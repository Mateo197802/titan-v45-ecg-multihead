"""Load verified P4 checkpoints and score all primary and auxiliary outputs."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import torch

from titan_v45.cascade.policy import CASCADE_PATHOLOGIES
from titan_v45.models.factory import build_titan_v45_backbone
from titan_v45.models.features import (
    SpecialistFeatureLayout,
    compose_specialist_features,
    recovered_backbone_rhythm_probabilities,
)
from titan_v45.models.specialists import ClassWiseBinaryMLP

P4_CLASSES = ("ASMI", "LVH", "IMI", "ISC_")
BACKBONE = "backbone-v3ag-pathology.pt"
SPECIALIST = "specialists-v3ag-primary4-calibrated.pt"
DATASET = "external-dev-pathology-ptbxl-fold10.tar.zst"


def verified_assets(repo: Path, root: Path, names: set[str]):
    entries = json.loads((repo / "release-manifest.json").read_text(encoding="utf-8"))["assets"]
    paths, digests = {}, {}
    for entry in entries:
        name = entry["name"]
        if name not in names:
            continue
        path = (root / entry["path"]).resolve()
        if not path.is_relative_to(root.resolve()) or name in paths:
            raise ValueError("duplicate or unsafe release asset")
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest() if hasattr(
                hashlib, "file_digest"
            ) else _stream_digest(handle)
        if digest != entry["sha256"] or path.stat().st_size != entry["bytes"]:
            raise ValueError(f"release checksum or size mismatch: {name}")
        paths[name], digests[name] = path, digest
    if paths.keys() != names:
        raise ValueError("release is missing required assets")
    return paths, digests


def _stream_digest(handle):
    digest = hashlib.sha256()
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(block)
    return digest.hexdigest()


class FrozenPathology:
    def __init__(self, assets, contract, device):
        self.device = device
        rhythm = tuple(contract["heads"]["rhythm"]["classes"])
        pathology = tuple(contract["heads"]["pathology"]["classes"])
        if pathology != P4_CLASSES + CASCADE_PATHOLOGIES or len(set(rhythm)) != 14:
            raise ValueError("unexpected backbone output order")
        backbone = torch.load(assets[BACKBONE], map_location="cpu", weights_only=True)
        checkpoint = torch.load(assets[SPECIALIST], map_location="cpu", weights_only=True)
        if tuple(checkpoint["pathology4_classes"]) != P4_CLASSES:
            raise ValueError("unexpected P4 checkpoint classes")
        self.thresholds = dict(zip(P4_CLASSES, map(float, checkpoint["pathology4_thresholds"]),
                                   strict=True))
        if any(not math.isfinite(x) or not 0 <= x <= 1 for x in self.thresholds.values()):
            raise ValueError("invalid frozen thresholds")
        self.model = build_titan_v45_backbone()
        self.model.load_state_dict(backbone["state_dict"], strict=True)
        self.model.to(device).eval().requires_grad_(False)
        state = checkpoint["pathology4_specialist_state_dict"]
        if state["heads.0.0.weight"].numel() != 670:
            raise ValueError("unexpected P4 specialist feature width")
        self.head = ClassWiseBinaryMLP(670, 4, hidden_dim=state["heads.0.1.weight"].shape[0])
        self.head.load_state_dict(state, strict=True)
        self.head.to(device).eval().requires_grad_(False)
        self.layout = SpecialistFeatureLayout(
            rhythm_indices=tuple(rhythm.index(c) for c in checkpoint["primary8_classes"]),
            specialist_rhythm_indices=tuple(rhythm.index(c) for c in checkpoint["specialist_rhythm_classes"]),
            pathology_indices=tuple(pathology.index(c) for c in P4_CLASSES),
        )

    @torch.no_grad()
    def __call__(self, samples):
        x, mask, morph = (torch.as_tensor(np.stack(parts), device=self.device)
                          for parts in zip(*samples, strict=True))
        r, _, _, p, features = self.model(x, morphology_features=morph, lead_mask=mask, return_features=True)
        base = p.sigmoid()
        inputs = compose_specialist_features(
            backbone_features=features, rhythm_probabilities=recovered_backbone_rhythm_probabilities(r),
            pathology_probabilities=base, morphology=morph, layout=self.layout,
        )
        primary = self.head(inputs).sigmoid().cpu().tolist()
        auxiliary = base[:, 4:].cpu().tolist()
        return [(dict(zip(P4_CLASSES, a, strict=True)), dict(zip(CASCADE_PATHOLOGIES, b, strict=True)))
                for a, b in zip(primary, auxiliary, strict=True)]
