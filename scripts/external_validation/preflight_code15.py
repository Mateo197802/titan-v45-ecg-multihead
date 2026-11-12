"""Seal publisher archives and describe signal coverage without using references or scores."""
from __future__ import annotations

import argparse
import csv
import json
import tempfile
from collections import Counter
from pathlib import Path

import h5py
import numpy as np
from code15_io import PROTOCOL, digest
from evaluate_code15 import selected, verified_hdf5

SHARDS = {f"exams_part{i}.zip" for i in range(18)}


def signal_summary(trace):
    if not np.isfinite(trace).all():
        return "nonfinite"
    nonzero = np.flatnonzero(np.any(trace != 0, axis=1))
    if not len(nonzero):
        return "all_zero"
    left, right = int(nonzero[0]), len(trace) - 1 - int(nonzero[-1])
    return f"{left}/{right}"


def join_index(path, names):
    by_shard = {Path(name).with_suffix(".hdf5").name: {} for name in names}
    seen = set()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            exam = int(row["exam_id"])
            patient = row["patient_id"].strip()
            if exam <= 0 or exam in seen or not patient or row["trace_file"] not in by_shard:
                raise ValueError("invalid publisher exam/patient membership")
            seen.add(exam)
            by_shard[row["trace_file"]][exam] = patient
    return by_shard


def inspect_shard(code, name, catalog, index, scratch):
    path = verified_hdf5(code, name, catalog, scratch)
    try:
        with h5py.File(path, "r") as h5:
            id_key, trace_key = next(pair for pair in (("exam_id", "tracings"), ("id_exam", "signal"))
                                     if set(pair) <= h5.keys())
            ids = np.asarray(h5[id_key]).reshape(-1)
            traces = h5[trace_key]
            shape = traces.shape
            actual = [int(exam) for exam in ids if int(exam)]
            if (shape != (len(ids), 4096, 12) or len(actual) != len(set(actual))
                    or set(actual) != index.keys()):
                raise ValueError(f"{name}: HDF5 and publisher index disagree")
            borders = Counter(signal_summary(traces[i]) for i, exam in enumerate(ids)
                              if int(exam) and selected(index[int(exam)]))
    finally:
        path.unlink()
    return {"source_ecgs": len(actual), "selected_ecgs": sum(borders.values()),
            "selected_zero_border_pairs": dict(borders), "hdf5_shape": list(shape),
            "placeholder_hdf5_rows": len(ids) - len(actual), "crc_verified": True}


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_bytes((json.dumps(value, sort_keys=True, indent=2) + "\n").encode())
    temporary.replace(path)


def run(code, scratch, available_only):
    protocol = json.loads(PROTOCOL.read_bytes())
    catalog_file, metadata = code / "record.json", code / "exams.csv"
    if digest(catalog_file) != protocol["catalog_sha256"] or digest(metadata) != protocol["metadata_sha256"]:
        raise ValueError("frozen publisher input mismatch")
    catalog = json.loads(catalog_file.read_bytes())
    entries = {a["key"]: a for a in catalog["files"] if a["key"].endswith(".zip")}
    if entries.keys() != SHARDS:
        raise ValueError("unexpected publisher archive set")
    index = join_index(metadata, SHARDS)
    checkpoint_dir = code / "preflight_checkpoints"
    checkpoint_dir.mkdir(mode=0o700, exist_ok=True)
    archives = {}
    for name in sorted(SHARDS):
        archive = code / name
        if not archive.exists() and available_only:
            continue
        sha = digest(archive)
        entry = entries[name]
        identity = {"sha256": sha, "bytes": archive.stat().st_size,
                    "publisher_md5": entry["checksum"].removeprefix("md5:"),
                    "metadata_sha256": protocol["metadata_sha256"], "catalog_sha256": protocol["catalog_sha256"]}
        receipt = checkpoint_dir / (name + ".json")
        if receipt.is_file():
            result = json.loads(receipt.read_bytes())
            if not result.get("crc_verified") or any(result.get(k) != v for k, v in identity.items()):
                raise ValueError(f"{name}: preflight checkpoint identity mismatch")
        else:
            with tempfile.TemporaryDirectory(dir=scratch) as working:
                result = {**identity, **inspect_shard(code, name, catalog,
                          index[Path(name).with_suffix(".hdf5").name], Path(working))}
            write_json(receipt, result)
        archives[name] = result
        print(json.dumps({"sealed_archive": name, "sha256": sha, "selected_ecgs": result["selected_ecgs"]}), flush=True)
    if archives.keys() != SHARDS:
        if available_only:
            return
        raise ValueError("all publisher archives required")
    all_patients = {p for shard in index.values() for p in shard.values()}
    selection_patients = sum(selected(p) for p in all_patients)
    total = {"protocol_sha256": digest(PROTOCOL), "archives": archives, "labels_used": False,
             "source_patients": len(all_patients), "selected_patients": selection_patients,
             "source_ecgs": sum(a["source_ecgs"] for a in archives.values()),
             "selected_ecgs": sum(a["selected_ecgs"] for a in archives.values())}
    write_json(code / "code15_preflight_receipt.json", total)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("code", type=Path)
    parser.add_argument("scratch", type=Path)
    parser.add_argument("--available-only", action="store_true")
    args = parser.parse_args()
    run(args.code, args.scratch, args.available_only)
