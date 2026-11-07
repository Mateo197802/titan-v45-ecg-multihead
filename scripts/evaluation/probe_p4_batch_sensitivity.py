"""Hold prepared ECG tensors fixed and isolate batch-size effects in P4 inference."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import torch

from titan_v45.cascade.run_pathology import (
    MORPHOLOGY_SHA,
    P4_PACKAGE,
    _compare_saved,
    _extract_records,
    _load_morphology,
    _read_rows,
)
from titan_v45.cascade.waveform import audit_pathology_waveforms, build_waveform_inventory
from titan_v45.data.reconstructed import prepare_p4_record
from titan_v45.evaluation.replay_diagnostics import compare_pathology_replay_ledgers
from titan_v45.evaluation.waveform_reference import _read_private_ledger
from titan_v45.models.frozen_pathology import (
    BACKBONE,
    DATASET,
    SPECIALIST,
    FrozenPathology,
    verified_assets,
)


def run(release, scratch, sealed_ledger):
    if not torch.cuda.is_available():
        raise RuntimeError("this CEDIA probe requires CUDA")
    assets, hashes = verified_assets(ROOT, release, {BACKBONE, DATASET, SPECIALIST})
    reference, digest = _read_private_ledger(sealed_ledger)
    sealed = json.loads(
        (ROOT / "outputs/results/revision_20261107/matched_reference_metrics.json").read_bytes()
    )
    if digest != sealed["private_ledger_sha256"]["P4"]:
        raise ValueError("sealed P4 ledger hash mismatch")
    contract = json.loads((ROOT / "outputs/models/heads/global_head_contracts.json").read_bytes())
    model = FrozenPathology(assets, contract, "cuda")
    morphology = _load_morphology(ROOT)
    manifest = ROOT / "data/manifests/external_dev/pathology_primary4_panels.csv"
    inventory = build_waveform_inventory(_read_rows(manifest))
    with TemporaryDirectory(prefix="titan-p4-fixed-batch-", dir=scratch) as location:
        work = Path(location)
        _extract_records(assets[DATASET], work)
        inputs = {p: prepare_p4_record(work / P4_PACKAGE / p, morphology)
                  for p in inventory.values()}
    variants = {}
    for name, size in (("batch32", 32), ("batch32_repeat", 32), ("batch1", 1)):
        _, variants[name] = audit_pathology_waveforms(
            inventory, inputs.__getitem__, model, model.thresholds, batch_size=size,
        )
    reference_comparisons = {name: _compare_saved(ROOT, ledger) for name, ledger in variants.items()}
    return {
        "schema": "TITAN_V45_P4_FIXED_INPUT_BATCH_PROBE_V1",
        "scope": "same_selected_ECGs_same_prepared_tensors_not_historical_loader_recovery",
        "torch": torch.__version__,
        "cuda_device": torch.cuda.get_device_name(),
        "records": len(inputs),
        "weights_or_thresholds_modified": False,
        "batch_sizes": {"batch32": 32, "batch32_repeat": 32, "batch1": 1},
        "release_sha256": hashes,
        "morphology_candidate_sha256_lf": MORPHOLOGY_SHA,
        "sealed_ledger_sha256": digest,
        "against_archived_panel_probabilities": reference_comparisons,
        "comparisons_all_four_scores": {
            "same_batch_repeat": compare_pathology_replay_ledgers(
                variants["batch32"], variants["batch32_repeat"], model.thresholds
            ),
            "batch32_vs_batch1": compare_pathology_replay_ledgers(
                variants["batch32"], variants["batch1"], model.thresholds
            ),
            "previous_native_batch32_vs_current": compare_pathology_replay_ledgers(
                reference, variants["batch32"], model.thresholds
            ),
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", required=True, type=Path)
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--sealed-pathology-ledger", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.sealed_pathology_ledger.resolve().is_relative_to(ROOT.resolve()):
        parser.error("private ledgers must remain outside the checkout")
    result = run(args.release_root, args.scratch, args.sealed_pathology_ledger)
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
