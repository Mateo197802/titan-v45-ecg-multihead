"""Reconstructed release P4 waveform workflow and archival comparison."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import shutil
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory

import torch
import zstandard

from titan_v45.cascade.waveform import audit_pathology_waveforms, build_waveform_inventory
from titan_v45.data.reconstructed import prepare_p4_record
from titan_v45.models.frozen_pathology import (
    BACKBONE,
    DATASET,
    P4_CLASSES,
    SPECIALIST,
    FrozenPathology,
    verified_assets,
)

MORPHOLOGY_SHA = "2bd1c1822ed72d1531b1f62712d8007c7e2f21009056ad1a3ee905f37051fc3d"
P4_PACKAGE = "external-dev-pathology-ptbxl-fold10"


def _read_rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _extract_records(path, scratch):
    # Paths are constrained to the verified release's waveform tree.
    with path.open("rb") as compressed, zstandard.ZstdDecompressor().stream_reader(
        compressed
    ) as stream, tarfile.open(fileobj=stream, mode="r|") as archive:
        for member in archive:
            if not member.isfile():
                continue
            parts = Path(member.name).parts
            if parts[:2] != (P4_PACKAGE, "records"):
                continue
            target = (scratch / member.name).resolve()
            if not target.is_relative_to(scratch.resolve()) or target.suffix not in {".hea", ".dat"}:
                raise ValueError("unexpected path or suffix in release waveform tree")
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as destination, archive.extractfile(member) as source:
                shutil.copyfileobj(source, destination)


def _compare_saved(repo, ledger):
    differences, mismatch, missing = [], 0, 0
    for name in P4_CLASSES:
        table = repo / f"outputs/results/external_dev/evidence/pathology_primary4_{name}_record_predictions.csv"
        for row in _read_rows(table):
            key = row["source"].casefold(), row["record_id"]
            new = ledger.get(key, {})
            if "primary_scores" not in new:
                missing += 1
                continue
            differences.append(abs(new["primary_scores"][name] - float(row["probability"])))
            mismatch += new["pathology"][name] != bool(int(row["predicted"]))
    return {
        "compared_panel_pairs": len(differences), "missing_panel_pairs": missing,
        "decision_disagreements": mismatch,
        "max_absolute_probability_difference": max(differences, default=None),
        "mean_absolute_probability_difference": math.fsum(differences) / len(differences) if differences else None,
        "historical_atol": 1e-5,
        "meets_historical_tolerance_on_all_panel_pairs": (
            bool(differences) and not missing and max(differences) <= 1e-5
        ),
    }


def run_pathology_release(repo: Path, release: Path, scratch: Path, device: str):
    """Run the fixed P4 candidate with a manifest that contributes no labels."""
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    assets, digests = verified_assets(repo, release, {BACKBONE, SPECIALIST, DATASET})
    morph = repo / "scripts/cedia/recovery_candidates/morphology_features_v4.py"
    if hashlib.sha256(morph.read_bytes().replace(b"\r\n", b"\n")).hexdigest() != MORPHOLOGY_SHA:
        raise ValueError("unexpected candidate morphology hash")
    spec = importlib.util.spec_from_file_location("titan_reconstructed_morphology", morph)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest = repo / "data/manifests/external_dev/pathology_primary4_panels.csv"
    inventory = build_waveform_inventory(_read_rows(manifest))
    contract = json.loads((repo / "outputs/models/heads/global_head_contracts.json").read_text(encoding="utf-8"))
    scorer = FrozenPathology(assets, contract, device)
    with TemporaryDirectory(prefix="titan-p4-waveform-", dir=scratch) as work:
        work = Path(work)
        _extract_records(assets[DATASET], work)
        package = work / P4_PACKAGE
        report, ledger = audit_pathology_waveforms(
            inventory,
            lambda relative: prepare_p4_record(package / relative, module.normalized_morphology_features),
            scorer, scorer.thresholds, batch_size=32,
        )
    report.update({
        "schema": "TITAN_V45_RECONSTRUCTED_P4_WAVEFORM_CASCADE_V1",
        "scope": "frozen_selected_p4_waveforms_new_inference_not_historical_cascade",
        "batch_size": 32, "batching": "each_ecg_once_sorted_by_source_and_id",
        "thresholds": scorer.thresholds, "weights_or_thresholds_modified": False,
        "release_sha256": digests,
        "manifest_sha256_lf": hashlib.sha256(manifest.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "morphology_candidate_sha256_lf": MORPHOLOGY_SHA,
        "preprocessing": "declared_source_backed_p4_candidate_not_original_loader",
        "auxiliary_action": "no_frozen_policy",
        "saved_comparison": _compare_saved(repo, ledger),
        "independent_external_evaluation": False,
        "historical_preprocessing_certified": False,
        "torch": torch.__version__, "device": device,
    })
    return report, ledger
