"""Audit downloaded MIMIC ECGs and save a private, outcome-blind eligibility manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import wfdb
from acquire_mimic import atomic

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from titan_v45.data.external_ecg import physical_digest, physical_mv


def read_physical(base: Path):
    header = wfdb.rdheader(str(base))
    if set(header.file_name) != {base.name + ".dat"}:
        raise ValueError("unexpected_wfdb_component")
    if header.fs != 500 or header.sig_len != 5000 or any(
        not np.isfinite(gain) or gain <= 0 for gain in header.adc_gain
    ):
        raise ValueError("invalid_wfdb_header")
    record = wfdb.rdrecord(str(base), physical=True)
    values = physical_mv(record.p_signal, header.sig_name, header.units, 500)
    return values, header


def aligned_signature(values):
    # A narrow alignment-preserving screen; does not detect shifted or cropped copies.
    reduced = values.reshape(12, 250, 20).mean(axis=2)
    reduced -= reduced.mean(axis=1, keepdims=True)
    norm = np.linalg.norm(reduced, axis=1, keepdims=True)
    if np.any(norm <= 1e-8):
        raise ValueError("flat_signature")
    return (reduced / norm).reshape(-1).astype(np.float32) / np.sqrt(np.float32(12))


def aligned_near_pairs(signatures, threshold=0.995):
    if len(signatures) < 2:
        return
    matrix = np.asarray(signatures, dtype=np.float32)
    for start in range(0, len(matrix), 128):
        similarities = matrix[start:start + 128] @ matrix.T
        for i, j in zip(*np.nonzero(similarities >= threshold), strict=True):
            if start + i < j:
                yield int(start + i), int(j)


def run(study: Path, history_path: Path):
    acquisition = study / "private_mimic_acquisition.jsonl"
    content = acquisition.read_bytes()
    rows = [json.loads(line) for line in content.splitlines()]
    selection = [json.loads(line) for line in (study / "private_mimic_selection.jsonl").read_bytes().splitlines()]
    keys = ("subject_id", "study_id", "split", "path")
    if [{key: r[key] for key in keys} for r in rows] != selection or not rows:
        raise ValueError("acquisition rows do not match frozen selection")
    history = json.loads(history_path.read_text(encoding="utf-8"))
    historical_hashes = {
        row["signal_sha256"] for row in history["rows"]
        if row.get("signal_sha256")
    }
    if not historical_hashes:
        raise ValueError("historical hash comparison has no input")
    patient_splits = defaultdict(set)
    for row in rows:
        patient_splits[row["subject_id"]].add(row["split"])
    if any(len(splits) != 1 for splits in patient_splits.values()):
        raise ValueError("patient partition collision")

    def check(row):
        if row["status"] != "verified":
            return {**row, "qc": "acquisition_failed"}, None
        base = study / "mimic" / row["path"]
        try:
            for suffix in (".hea", ".dat"):
                data = base.with_suffix(suffix).read_bytes()
                expected = row["components"][suffix]
                if len(data) != expected["bytes"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
                    raise ValueError("waveform_component_mismatch")
            values, header = read_physical(base)
            return {
                **row, "qc": "physical_valid", "fs": 500, "duration_seconds": 10,
                "leads": header.sig_name, "gain": header.adc_gain, "units": header.units,
                "peak_absolute_mv": float(np.max(np.abs(values))),
                "physical_digest": physical_digest(values, 500),
                "stage_a_raw_byte_match": row["components"][".dat"]["sha256"] in historical_hashes,
            }, aligned_signature(values)
        except (ValueError, OSError, RuntimeError):
            return {**row, "qc": "physical_or_integrity_failed"}, None

    with ThreadPoolExecutor(max_workers=4) as pool:
        checked = list(pool.map(check, rows))
    eligible_indices = [idx for idx, (_, signature) in enumerate(checked) if signature is not None]
    exact_groups = defaultdict(list)
    for idx in eligible_indices:
        exact_groups[checked[idx][0]["physical_digest"]].append(idx)
    exact = {idx for group in exact_groups.values() if len(group) > 1 for idx in group}
    near = set()
    near_pairs = 0
    cross_split_near_pairs = 0
    for a, b in aligned_near_pairs([checked[idx][1] for idx in eligible_indices]):
        i, j = eligible_indices[a], eligible_indices[b]
        near.update((i, j))
        near_pairs += 1
        cross_split_near_pairs += checked[i][0]["split"] != checked[j][0]["split"]
    counts = defaultdict(Counter)
    for idx, (row, _) in enumerate(checked):
        row["analysis_status"] = (
            row["qc"] if row["qc"] != "physical_valid" else
            "stage_a_raw_match" if row["stage_a_raw_byte_match"] else
            "exact_duplicate" if idx in exact else
            "aligned_near_duplicate" if idx in near else "waveform_eligible"
        )
        counts[row["split"]][row["analysis_status"]] += 1
    manifest = b"".join(json.dumps(row, sort_keys=True).encode() + b"\n" for row, _ in checked)
    atomic(study / "private_mimic_waveform_eligibility.jsonl", manifest)
    receipt = {
        "scope": "WAVEFORM_QC_NO_REFERENCE_OR_PERFORMANCE",
        "input_acquisition_sha256": hashlib.sha256(content).hexdigest(),
        "eligibility_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        "source_patient_split_overlap": 0,
        "counts_by_split": counts,
        "stage_a_raw_hashes_compared": len(historical_hashes),
        "stage_a_raw_matches": sum(bool(row.get("stage_a_raw_byte_match")) for row, _ in checked),
        "within_source_exact_duplicate_records": len(exact),
        "within_source_aligned_near_pairs": near_pairs,
        "within_source_aligned_cross_split_pairs": cross_split_near_pairs,
        "historical_physical_or_near_duplicate_comparison": "NOT_RUN",
        "patient_independence_from_historical_backbones": "NOT_CERTIFIED",
        "performance_computed": False,
    }
    output = (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode()
    atomic(study / "mimic_waveform_qc_receipt.json", output)
    print(output.decode(), end="")


if __name__ == "__main__":
    import os

    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", type=Path)
    parser.add_argument("stage_a_inventory", type=Path)
    args = parser.parse_args()
    run(args.study, args.stage_a_inventory)
