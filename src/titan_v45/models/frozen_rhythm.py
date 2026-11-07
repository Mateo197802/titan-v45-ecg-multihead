"""Frozen rhythm heads with profile-specific, source-backed aggregation."""
from __future__ import annotations

import ast
import hashlib
import math
import zipfile

import numpy as np
import torch

from titan_v45.cascade.policy import CASCADE_RHYTHMS
from titan_v45.evaluation.decision_policy import membership_decision
from titan_v45.models.factory import build_titan_v45_backbone
from titan_v45.models.features import (
    SpecialistFeatureLayout,
    compose_specialist_features,
    recovered_backbone_rhythm_probabilities,
)
from titan_v45.models.specialists import ClassWiseBinaryMLP

P8_CLASSES = ("AFIB", "SB", "STACH", "NSR", "RBBB", "PAC", "1AVB", "PVC")
P6_CLASSES = tuple(c for c in P8_CLASSES if c not in {"NSR", "PAC"})
BACKBONE = "backbone-v3f-original.pt"
HEADS = {"P6": "specialists-v3p-e008-primary6-diagnostic.pt",
         "P8": "specialists-v3q-primary8-best-candidate.pt"}
DATASET = "external-dev-rhythm-chapman-shaoxing.tar.zst"
TRAINER_SHA = "8e8d59889a0458c47a90f9735ff6ba017c7e1a79582d11529a608e1816e671fe"


def load_recorded_event_extractor(archive):
    """Bind only two pure feature functions from the hash-pinned trainer."""
    try:
        with zipfile.ZipFile(archive) as source:
            data = source.read("TRAINING/train_v3d_specialists_hpc.py")
    except (OSError, KeyError, zipfile.BadZipFile) as exc:
        raise ValueError("invalid recovered trainer archive") from exc
    if hashlib.sha256(data).hexdigest() != TRAINER_SHA:
        raise ValueError("recovered trainer hash mismatch")
    names = {"_select_event_peaks_1d", "_signal_event_features_from_batch"}
    nodes = [node for node in ast.parse(data).body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in nodes} != names or len(nodes) != 2:
        raise ValueError("unexpected recorded feature definitions")
    namespace = {"np": np, "torch": torch, "SIGNAL_EVENT_FEATURE_DIM": 12}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<pinned trainer feature functions>", "exec"),
         namespace)
    return namespace["_signal_event_features_from_batch"]


def aggregate_rhythm(logits, thresholds, *, profile):
    classes = {"P6": P6_CLASSES, "P8": P8_CLASSES}[profile]
    values = np.asarray(logits)
    if values.ndim != 2 or values.shape[1] != 8 or not len(values) or not np.isfinite(values).all():
        raise ValueError("expected finite nonempty eight-class window logits")
    if tuple(thresholds) != classes or any(not math.isfinite(x) or not 0 <= x <= 1
                                           for x in thresholds.values()):
        raise ValueError("invalid profile thresholds")
    if profile == "P6":
        mean = values[:, [P8_CLASSES.index(c) for c in classes]].mean(axis=0, dtype=np.float64)
        scores = dict(zip(classes, (1 / (1 + np.exp(-np.clip(mean, -50, 50)))).tolist(), strict=True))
        return {"top1": classes[int(np.argmax(mean))],
                "labels": [c for c in classes if scores[c] >= thresholds[c]],
                "used_fallback": False, "scores": scores}
    probability = torch.as_tensor(values, dtype=torch.float32).sigmoid().numpy()
    scores = dict(zip(classes, probability.mean(axis=0, dtype=np.float64).tolist(), strict=True))
    return {**membership_decision(scores, thresholds), "scores": scores}


def build_frozen_rhythm_head(checkpoint):
    """Use the actual tensors when the redundant width metadata is stale."""
    state = checkpoint["rhythm_specialist_state_dict"]
    width, inputs = state["heads.0.1.weight"].shape
    if inputs != 681:
        raise ValueError("stored rhythm feature width is not 681")
    declared = int(checkpoint["rhythm_hidden_dim"])
    head = ClassWiseBinaryMLP(inputs, len(P8_CLASSES), hidden_dim=width)
    head.load_state_dict(state, strict=True)
    return head, {"declared": declared, "stored": width, "metadata_matches": width == declared}


class FrozenRhythm:
    def __init__(self, assets, contract, event_extractor, device):
        self.device = device
        self.event_extractor = event_extractor
        rhythm = tuple(contract["heads"]["rhythm"]["classes"])
        pathology = tuple(contract["heads"]["pathology"]["classes"])
        if rhythm != P8_CLASSES + CASCADE_RHYTHMS or pathology[:4] != ("ASMI", "LVH", "IMI", "ISC_"):
            raise ValueError("unexpected backbone output order")
        self.model = build_titan_v45_backbone()
        weights = torch.load(assets[BACKBONE], map_location="cpu", weights_only=True)
        self.model.load_state_dict(weights["state_dict"], strict=True)
        self.model.to(device).eval().requires_grad_(False)
        self.heads, self.layouts, self.biases, self.widths = {}, {}, {}, {}
        for profile, name in HEADS.items():
            checkpoint = torch.load(assets[name], map_location="cpu", weights_only=True)
            if (tuple(checkpoint["primary8_classes"]) != P8_CLASSES
                    or checkpoint["signal_event_feature_dim"] != 12
                    or checkpoint["input_dim"] != 681
                    or not checkpoint["classwise_rhythm_heads"]
                    or checkpoint["rhythm_mode"] != "multilabel"):
                raise ValueError("unexpected rhythm specialist checkpoint contract")
            head, self.widths[profile] = build_frozen_rhythm_head(checkpoint)
            self.heads[profile] = head.to(device).eval().requires_grad_(False)
            self.layouts[profile] = SpecialistFeatureLayout(
                rhythm_indices=tuple(rhythm.index(c) for c in P8_CLASSES),
                specialist_rhythm_indices=tuple(rhythm.index(c) for c in checkpoint["specialist_rhythm_classes"]),
                pathology_indices=tuple(pathology.index(c) for c in checkpoint["pathology4_classes"]),
                signal_event_feature_dim=12,
            )
            bias = checkpoint.get("rhythm_logit_biases") if profile == "P8" else None
            if bias is not None:
                if len(bias) != 8 or not all(math.isfinite(x) for x in bias):
                    raise ValueError("invalid P8 checkpoint logit biases")
                self.biases[profile] = torch.tensor(bias, dtype=torch.float32, device=device)

    @torch.no_grad()
    def __call__(self, samples):
        x, mask, morph = (torch.as_tensor(np.stack(parts), device=self.device)
                          for parts in zip(*samples, strict=True))
        r, _, _, p, features = self.model(x, morphology_features=morph, lead_mask=mask, return_features=True)
        rhythm = recovered_backbone_rhythm_probabilities(r)
        pathology = p.sigmoid()
        events = self.event_extractor(x)
        logits = {}
        for profile, head in self.heads.items():
            inputs = compose_specialist_features(
                backbone_features=features, rhythm_probabilities=rhythm, pathology_probabilities=pathology,
                morphology=morph, signal_event_features=events, layout=self.layouts[profile],
            )
            output = head(inputs).float()
            if profile in self.biases:
                output = output + self.biases[profile]
            logits[profile] = output.cpu().numpy()
        return logits, rhythm[:, 8:].cpu().numpy()
