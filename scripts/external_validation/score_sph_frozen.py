"""Run frozen TITAN V4.5 profiles over all eligible SPH waveforms."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.cascade.run_pathology import _load_morphology
from titan_v45.data.sph import open_sph_records, read_sph_signal, read_sph_signal_index
from titan_v45.data.sph_waveform import prepare_sph_waveform
from titan_v45.evaluation.sph_scoring import summarize_sph_record
from titan_v45.models.frozen_pathology import (
    BACKBONE as P4_BACKBONE,
)
from titan_v45.models.frozen_pathology import (
    SPECIALIST as P4_SPECIALIST,
)
from titan_v45.models.frozen_pathology import (
    FrozenPathology,
    verified_assets,
)
from titan_v45.models.frozen_rhythm import (
    BACKBONE as RHYTHM_BACKBONE,
)
from titan_v45.models.frozen_rhythm import (
    HEADS,
    FrozenRhythm,
    load_recorded_event_extractor,
)


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_signal_index(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"ECG_ID", "N"}.issubset(reader.fieldnames or ()):
            raise ValueError("metadata lacks ECG_ID or N")
        rows = []
        for row in reader:
            rows.append((row["ECG_ID"], row["N"]))
    return read_sph_signal_index(
        "ECG_ID,N\n" + "".join(f"{record},{samples}\n" for record, samples in rows)
    )


def _protocol(repo, args):
    config_path = repo / "configs/external_validation/sph_frozen.json"
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if commit != args.expected_commit or not commit:
        raise ValueError("working tree commit does not match frozen protocol commit")
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if status:
        raise ValueError("protocol source tree must be clean")
    config_hash = _sha256(config_path)
    if config_hash != args.expected_config_sha256:
        raise ValueError("frozen protocol configuration hash mismatch")
    return json.loads(config_path.read_text(encoding="utf-8")), config_hash, commit


def _score_batch(records, rhythm_scorer, pathology_scorer, thresholds, writer):
    rhythm_windows = []
    offsets = {}
    pathology_samples = []
    for row in records:
        offsets[row["record_id"]] = (len(rhythm_windows), len(row["rhythm_samples"]))
        rhythm_windows.extend(row["rhythm_samples"])
        pathology_samples.append(row["pathology_sample"])
    rhythm_logits, rhythm_aux = rhythm_scorer(rhythm_windows)
    pathology_outputs = pathology_scorer(pathology_samples)
    if len(pathology_outputs) != len(records):
        raise ValueError("P4 scorer output count mismatch")
    for row, (primary, auxiliary) in zip(records, pathology_outputs, strict=True):
        offset, count = offsets[row["record_id"]]
        logits = {name: values[offset:offset + count] for name, values in rhythm_logits.items()}
        aux = rhythm_aux[offset:offset + count]
        summary = summarize_sph_record(
            logits, aux, primary, auxiliary, thresholds, count, pathology_scorer.thresholds
        )
        output = {"record_id": row["record_id"], "status": "scored", **summary}
        writer.write(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n")


def run(args):
    import h5py
    import numpy as np
    import scipy
    import wfdb
    import zstandard

    repo, source, release = args.repo.resolve(), args.source.resolve(), args.release_root.resolve()
    duplicate_index = args.duplicate_index.resolve()
    if (source.is_relative_to(repo) or args.ledger.resolve().is_relative_to(repo)
            or duplicate_index.is_relative_to(repo)):
        raise ValueError("SPH source and per-record ledger must stay outside Git")
    if args.output.resolve().is_relative_to(repo):
        raise ValueError("execution receipt must stay outside Git")
    protocol, config_hash, commit = _protocol(repo, args)
    implementation_hashes = {}
    for relative_path, expected_hash in protocol["implementation_sha256"].items():
        path = (repo / relative_path).resolve()
        if not path.is_relative_to(repo) or _sha256(path) != expected_hash:
            raise ValueError(f"frozen implementation digest mismatch: {relative_path}")
        implementation_hashes[relative_path] = expected_hash
    control_hashes = {}
    for name, item in protocol["preperformance_controls"]["aggregates"].items():
        path = (repo / item["path"]).resolve()
        if not path.is_relative_to(repo) or _sha256(path) != item["sha256"]:
            raise ValueError(f"pre-performance control aggregate mismatch: {name}")
        control_hashes[name] = item["sha256"]
        if name == "cross_source_signature":
            audit = json.loads(path.read_text(encoding="utf-8"))
            if audit.get("independence_certified") is not False:
                raise ValueError("cross-source screen must not certify historical independence")
    duplicate_index_sha256 = _sha256(duplicate_index)
    if duplicate_index_sha256 != protocol["preperformance_controls"]["private_duplicate_index_sha256"]:
        raise ValueError("private SPH duplicate index hash mismatch")
    for name, expected in protocol["source_sha256"].items():
        if _sha256(source / name) != expected:
            raise ValueError(f"SPH input digest mismatch: {name}")
    if protocol["stage"] != "full_population":
        raise ValueError("only the preregistered full-population stage may score")
    contract = json.loads(
        (repo / "outputs/models/heads/global_head_contracts.json").read_text(encoding="utf-8")
    )
    names = {P4_BACKBONE, P4_SPECIALIST, RHYTHM_BACKBONE, *HEADS.values()}
    assets, digests = verified_assets(repo, release, names)
    if digests != protocol["model_sha256"]:
        raise ValueError("frozen model digests differ from preregistration")
    morphology = _load_morphology(repo)
    event_archive = repo / "docs/provenance/recovered-original-sources-20261029.zip"
    event_extractor = load_recorded_event_extractor(event_archive)
    rhythm_scorer = FrozenRhythm(assets, contract, event_extractor, "cuda")
    pathology_scorer = FrozenPathology(assets, contract, "cuda")
    thresholds = protocol["thresholds"]
    p4_thresholds = {key: float(value) for key, value in pathology_scorer.thresholds.items()}
    if thresholds["P4"] != p4_thresholds:
        raise ValueError("P4 checkpoint threshold mismatch")
    p6_lineage = json.loads(
        (repo / "outputs/results/revision_20261029/p6_calibration_lineage_summary.json")
        .read_text(encoding="utf-8")
    )
    p8_metrics = json.loads(
        (repo / "outputs/results/external_dev/rhythm_primary8_metrics.json")
        .read_text(encoding="utf-8")
    )
    if (tuple(p6_lineage["classes"]) != tuple(protocol["classes"]["P6"])
            or p6_lineage["biases"] != [0] * 6
            or p6_lineage["aggregation"] != "mean_logits"
            or p6_lineage["thresholds"] != list(thresholds["P6"].values())):
        raise ValueError("P6 threshold or aggregation contract mismatch")
    if (tuple(p8_metrics["classes"]) != tuple(protocol["classes"]["P8"])
            or p8_metrics["thresholds"] != list(thresholds["P8"].values())):
        raise ValueError("P8 threshold contract mismatch")
    expected_rhythm = {
        "P6": tuple(protocol["classes"]["P6"]),
        "P8": tuple(protocol["classes"]["P8"]),
    }
    for profile in ("P6", "P8"):
        if tuple(thresholds[profile]) != expected_rhythm[profile]:
            raise ValueError("rhythm class/threshold contract mismatch")
    index = _read_signal_index(source / "metadata.csv")
    if len(index) != protocol["expected_source_records"]:
        raise ValueError("source record count differs from preregistration")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the frozen SPH scoring job")
    torch.set_num_threads(2)
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    status_counts = {}
    pending = []
    batch_size = int(protocol["inference"]["records_per_batch"])
    seen, archive_records = set(), 0
    with args.ledger.open("x", encoding="utf-8", newline="\n") as ledger:
        for record_id, content in open_sph_records(source / "records.tar.gz"):
            archive_records += 1
            if record_id in seen:
                raise ValueError("duplicate record in source archive")
            seen.add(record_id)
            samples = index.get(record_id)
            if samples is None:
                row = {"record_id": record_id, "status": "no_metadata"}
            else:
                try:
                    signal, _ = read_sph_signal(content, samples)
                    rhythm = prepare_sph_waveform(signal, morphology, branch="rhythm")
                    pathology = prepare_sph_waveform(signal, morphology, branch="P4")
                    pending.append({
                        "record_id": record_id,
                        "rhythm_samples": rhythm,
                        "pathology_sample": pathology[0],
                    })
                    if len(pending) >= batch_size:
                        _score_batch(pending, rhythm_scorer, pathology_scorer,
                                     thresholds, ledger)
                        status_counts["scored"] = status_counts.get("scored", 0) + len(pending)
                        pending.clear()
                    continue
                except (ValueError, OSError) as exc:
                    row = {
                        "record_id": record_id,
                        "status": "technical_exclusion",
                        "reason": type(exc).__name__,
                    }
            ledger.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
        if pending:
            _score_batch(pending, rhythm_scorer, pathology_scorer,
                         thresholds, ledger)
            status_counts["scored"] = status_counts.get("scored", 0) + len(pending)
        for record_id in sorted(index.keys() - seen):
            row = {"record_id": record_id, "status": "missing_signal"}
            ledger.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    ledger_hash = _sha256(args.ledger)
    if sum(status_counts.values()) != len(index):
        raise ValueError("flow denominator does not reconcile with source metadata")
    receipt = {
        "schema": "TITAN_V45_SPH_SCORING_RECEIPT_V1",
        "stage": "full_population",
        "protocol_commit": commit,
        "protocol_sha256": config_hash,
        "source_sha256": protocol["source_sha256"],
        "model_sha256": digests,
        "implementation_sha256": implementation_hashes,
        "preperformance_control_sha256": control_hashes,
        "private_duplicate_index_sha256": duplicate_index_sha256,
        "ledger_sha256": ledger_hash,
        "job_id": os.environ.get("SLURM_JOB_ID", "not_slurm"),
        "runtime_seconds": time.monotonic() - started,
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "device": torch.cuda.get_device_name(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "h5py": h5py.__version__,
            "wfdb": wfdb.__version__,
            "zstandard": zstandard.__version__,
        },
        "preprocessing_code_sha256_lf": _sha256(
            repo / "src/titan_v45/data/reconstructed.py"
        ),
        "morphology_candidate_sha256_lf": _sha256(
            repo / "scripts/cedia/recovery_candidates/morphology_features_v4.py"
        ),
        "event_trainer_archive_sha256": _sha256(event_archive),
        "flow": {
            "metadata_records": len(index),
            "archive_records": archive_records,
            "status_counts": dict(sorted(status_counts.items())),
            "scored_records": status_counts.get("scored", 0),
        },
        "labels_used_for_inference_or_routing": False,
        "patient_or_record_level_data_in_repository": False,
        "quarantine_policy": "not_assessed_no_historical_policy_frozen",
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(receipt, output, indent=2, allow_nan=False)
        output.write("\n")
    os.chmod(args.ledger, 0o600)
    os.chmod(args.output, 0o600)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--release-root", type=Path, required=True)
    parser.add_argument("--duplicate-index", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-config-sha256", required=True)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
