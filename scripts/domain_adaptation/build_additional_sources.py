"""Materialize previously authorized development signals without touching CODE labels."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

import numpy as np
import wfdb
from build_code_development import PROTOCOL, ROOT, digest, stable, write_json
from evaluate_code15 import signature

from titan_v45.data.duration_aware_preprocessing import (
    normalize,
    observed_descriptors,
    prepare_observed,
)
from titan_v45.data.external_ecg import physical_mv

CROSS = ROOT / "docs/domain_adaptation/CROSS_SOURCE_PROTOCOL.json"


def code_signatures(bank):
    signatures = []
    for path in sorted(bank.glob("exams_part*/*-long_10.npz")):
        receipt = json.loads((path.parent / "receipt.json").read_bytes())
        if digest(path) != receipt["artifacts"][path.name]:
            raise ValueError("CODE waveform bank mismatch")
        with np.load(path, allow_pickle=False) as data:
            signatures.extend(signature(w) for w in normalize(data["wave"], "per_lead_zscore"))
    if not signatures:
        raise ValueError("no comparable CODE waveform signatures")
    return np.stack(signatures)


def read_source(raw, row, endpoints, source_roots=None):
    source = source_roots[row["source"]] if source_roots else (raw / row["source"]).resolve()
    relative = Path(row["relative_record"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("additional source path escaped source root")
    base = source / relative
    if not Path(f"{base}.hea").resolve(strict=True).is_relative_to(source):
        raise ValueError("source_path_escape")
    header = wfdb.rdheader(str(base))
    if header.fs != 500 or header.sig_len < 5000:
        raise ValueError("nonstandard_or_short_source_window")
    files = set(header.file_name)
    if len(files) != 1:
        raise ValueError("unexpected_waveform_components")
    name = next(iter(files))
    signal = base.parent / name
    if (Path(name).name != name or not signal.resolve(strict=True).is_relative_to(source)
            or digest(signal) != row["signal_sha256"]):
        raise ValueError("source_waveform_identity_mismatch")
    start = (header.sig_len - 5000) // 2
    trace = wfdb.rdrecord(str(base), sampfrom=start, sampto=start + 5000)
    mv = physical_mv(trace.p_signal, trace.sig_name, trace.units, 500)
    wave = prepare_observed(mv.T, 500)
    labels = [row["targets"][row["classes"].index(e)] if row["mask"][row["classes"].index(e)] else -1
              for e in endpoints]
    return wave, observed_descriptors(wave), labels


def read_candidate(raw, endpoints, row, *, source_roots=None):
    try:
        return read_source(raw, row, endpoints, source_roots), None
    except (ValueError, OSError) as exc:
        if str(exc) in {"source_waveform_identity_mismatch", "source_path_escape",
                        "additional source path escaped source root"}:
            raise
        return None, type(exc).__name__


def run(raw, preflight, code_bank, out):
    cfg, protocol = (json.loads(path.read_bytes()) for path in (CROSS, PROTOCOL))
    if (cfg["parent_protocol_sha256"] != digest(PROTOCOL)
            or digest(preflight / "private_inventory.json") != cfg["private_inventory_sha256"]
            or digest(preflight / "preflight_receipt.json") != cfg["inventory_receipt_sha256"]):
        raise ValueError("cross-source inventory or parent protocol mismatch")
    code = code_signatures(code_bank)
    inventory = json.loads((preflight / "private_inventory.json").read_bytes())["rows"]
    out.mkdir(mode=0o700, exist_ok=False)
    groups, matrix, mapping = defaultdict(list), [], []
    rejected = Counter()
    roots = {name: (raw / name).resolve(strict=True) for name in cfg["sources"]}
    if any(not root.is_relative_to(raw.resolve(strict=True)) for root in roots.values()):
        raise ValueError("additional source root escaped the approved input directory")
    worker = partial(read_candidate, raw, list(protocol["endpoints"]), source_roots=roots)
    workers = min(16, max(1, int(os.getenv("SLURM_CPUS_PER_TASK", "1"))))
    for source, splits in cfg["sources"].items():
        for split, cap in splits["caps"].items():
            if not cap:
                continue
            pool = [row for row in inventory if row["task"] == "rhythm" and row["source"] == source
                    and row["split"] == split and row["excluded_reason"] is None]
            pool.sort(key=lambda row: stable("titan-da-source-v1", row["identity_hash"]))
            with ThreadPoolExecutor(max_workers=workers) as readers:
                for index, (row, (result, error)) in enumerate(zip(pool[:cap], readers.map(worker, pool[:cap]), strict=True), 1):
                    if index % 250 == 0:
                        print(json.dumps({"source": source, "split": split, "checked": index}), flush=True)
                    if error:
                        rejected[f"{source}:{error}"] += 1
                        continue
                    wave, descriptors, labels = result
                    group = row["group_hash"] if source == "chapman_shaoxing" else None
                    if source == "chapman_shaoxing" and not group:
                        raise ValueError("missing Chapman subject proxy")
                    normalized = normalize(wave, "per_lead_zscore")
                    matrix.append(signature(normalized))
                    mapping.append((source, split, group, row["identity_hash"], row["signal_sha256"]))
                    groups[source, split].append((len(mapping) - 1, wave, descriptors, labels))
            print(json.dumps({"source": source, "split": split, "selected_records": len(pool[:cap])}), flush=True)
    signature_matrix = np.stack(matrix)
    removed = set()
    for start in range(0, len(matrix), 128):
        hits = signature_matrix[start:start + 128] @ code.T
        removed.update(start + i for i in np.flatnonzero(hits.max(axis=1) >= cfg["minimum_aligned_cosine"]))
    code_matches = len(removed)
    for start in range(0, len(matrix), 128):
        for i, j in zip(*np.nonzero(signature_matrix[start:start + 128] @ signature_matrix.T >=
                                    cfg["minimum_aligned_cosine"]), strict=True):
            if start + i < j:
                removed.update((start + int(i), int(j)))
    groups_by_subject, summary = defaultdict(set), {}
    for (source, split), values in groups.items():
        kept = [(idx, wave, desc, y) for idx, wave, desc, y in values if idx not in removed]
        if not kept:
            raise ValueError(f"no eligible source rows: {source}/{split}")
        ids, waves, desc, labels = zip(*kept, strict=True)
        people = [mapping[i][2] for i in ids]
        for person in people:
            if person is not None:
                groups_by_subject[person].add(split)
        private = [{"group": mapping[i][2], "identity": mapping[i][3], "waveform_sha256": mapping[i][4]} for i in ids]
        path = out / f"{source}-{split}.npz"
        manifest = out / f"private_{source}_{split}.json"
        np.savez(path, wave=np.stack(waves), descriptors=np.stack(desc), labels=np.asarray(labels, dtype=np.float32))
        write_json(manifest, private)
        y = np.asarray(labels)
        summary[f"{source}/{split}"] = {"ecgs": len(ids), "patients": len(set(people)) if all(people) else None,
            "endpoints": {e: {str(k): int((y[:, j] == k).sum()) for k in (-1, 0, 1)}
                          for j, e in enumerate(protocol["endpoints"])},
            "bank_sha256": digest(path), "private_manifest_sha256": digest(manifest)}
    if any(len(splits) != 1 for splits in groups_by_subject.values()):
        raise ValueError("Chapman subject proxies overlap partitions")
    result = {"scope": cfg["scope"], "protocol_sha256": digest(CROSS), "sources": summary,
              "code_waveform_signatures": len(code), "external_code_waveform_matches_excluded": code_matches,
              "total_aligned_exclusions": len(removed), "other_exclusions": dict(rejected),
              "code_label_files_read": False, "patient_independence_across_sources": "NOT_CERTIFIED",
              "reader_workers": workers, "slurm_job": os.getenv("SLURM_JOB_ID"),
              "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}
    write_json(out / "ADDITIONAL_SOURCE_RECEIPT.json", result)
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("raw", "preflight", "code_bank", "output"):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    run(args.raw, args.preflight, args.code_bank, args.output)
