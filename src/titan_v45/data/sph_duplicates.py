"""Private identity-aware duplicate and amplitude audit for native SPH."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from titan_v45.data.sph import (
    inspect_sph_signal_metadata,
    open_sph_records,
    read_sph_dictionary,
    read_sph_metadata,
)


def _union_find():
    parent = {}

    def find(item):
        parent.setdefault(item, item)
        if parent[item] != item:
            parent[item] = find(parent[item])
        return parent[item]

    def union(left, right):
        left, right = find(left), find(right)
        if left != right:
            parent[max(left, right)] = min(left, right)

    return parent, find, union


def audit_sph_duplicates(directory: Path, private_index: Path | None = None):
    """Summarize exact signal links, patient/label conflicts and unit metadata.

    The optional row-level identity map is private and must stay outside Git.
    This exact-array comparison does not claim near-duplicate detection.
    """
    primary, modifier = read_sph_dictionary(
        (directory / "code.csv").read_text(encoding="utf-8-sig")
    )
    metadata = read_sph_metadata(
        (directory / "metadata.csv").read_text(encoding="utf-8-sig"),
        primary,
        modifier,
    )
    hashes = defaultdict(list)
    attrs = Counter()
    attr_values = defaultdict(Counter)
    raw_ranges = []
    dtypes = Counter()
    seen = set()
    for key, content in open_sph_records(directory / "records.tar.gz"):
        if key in seen:
            raise ValueError("duplicate archive ECG ID")
        seen.add(key)
        if key not in metadata:
            continue
        info = inspect_sph_signal_metadata(content, metadata[key].samples)
        values = info.pop("attributes")
        dtypes[info["dtype"]] += 1
        for name, value in values.items():
            attrs[name] += 1
            canonical = json.dumps(value, sort_keys=True, ensure_ascii=True, default=str)
            attr_values[name][canonical] += 1
        digest = info["signal_sha256_canonical_f64"]
        hashes[digest].append(key)
        raw_ranges.append([
            info["raw_min"], info["raw_max"], *info["raw_abs_quantiles"],
            info["lead_std_median"],
        ])

    exact_groups = [keys for keys in hashes.values() if len(keys) > 1]
    duplicate_cross_patient = 0
    label_conflict_groups = 0
    duplicate_records = set()
    parent, find, union = _union_find()
    for patient in {row.patient for row in metadata.values()}:
        find(patient)
    private_rows = []
    for digest, keys in sorted(hashes.items()):
        patients = sorted({metadata[key].patient for key in keys})
        code_sets = {key: tuple(sorted(metadata[key].primary_codes)) for key in keys}
        conflicts = len(set(code_sets.values())) > 1
        if len(keys) > 1:
            duplicate_records.update(keys)
            for patient in patients[1:]:
                union(patients[0], patient)
            duplicate_cross_patient += len(patients) > 1
            label_conflict_groups += conflicts
        representative = min(keys)
        for key in keys:
            private_rows.append({
                "ecg_id": key,
                "patient_id": metadata[key].patient,
                "signal_sha256_canonical_f64": digest,
                "duplicate_representative": representative,
                "duplicate_group_size": len(keys),
                "primary_codes": list(code_sets[key]),
                "duplicate_group_label_conflict": conflicts,
            })

    components = Counter(find(patient) for patient in parent)
    roots = Counter(components.values())
    matrix = np.asarray(raw_ranges, dtype=np.float64)
    report = {
        "schema": "TITAN_V45_SPH_DUPLICATE_AMPLITUDE_AUDIT_V1",
        "scope": "exact decoded arrays and source metadata; no model performance",
        "records_hashed": sum(map(len, hashes.values())),
        "exact_duplicate_groups": len(exact_groups),
        "exact_duplicate_excess_records": sum(len(keys) - 1 for keys in exact_groups),
        "groups_crossing_patient_ids": duplicate_cross_patient,
        "groups_with_primary_code_set_conflicts": label_conflict_groups,
        "records_in_exact_duplicate_groups": len(duplicate_records),
        "patient_components_linked_by_exact_duplicates": {
            "patient_count": len(components),
            "count": len(roots),
            "component_size_distribution": {str(k): v for k, v in sorted(roots.items())},
            "unit_for_cluster_bootstrap": "connected_component_of_source_patient_ids",
        },
        "hdf5_attribute_presence_counts": dict(sorted(attrs.items())),
        "hdf5_attribute_values": {
            name: dict(sorted(counter.items())) for name, counter in sorted(attr_values.items())
        },
        "raw_signal_scale": {
            "interpretation": "native stored values only; physical units not inferred",
            "dtype_counts": dict(sorted(dtypes.items())),
            "global_min": float(matrix[:, 0].min()),
            "global_max": float(matrix[:, 1].max()),
            "abs_value_quantiles_by_record": {
                str(q): float(np.quantile(matrix[:, column], q))
                for q, column in ((0.5, 2), (0.95, 3), (0.999, 4))
            },
            "median_of_record_median_lead_std": float(np.median(matrix[:, 5])),
            "normalization_test": "per-lead z-score after source-backed filter/resampling",
        },
        "source_inventory_sha256": hashlib.sha256(
            (directory / "metadata.csv").read_bytes()
        ).hexdigest(),
        "record_or_patient_identifiers_exported": False,
        "near_duplicate_analysis": "not performed",
        "historical_cross_source_independence": "not certified; source patient IDs are not linkable",
    }
    if private_index is not None:
        private_index.parent.mkdir(parents=True, exist_ok=True)
        with private_index.open("x", encoding="utf-8", newline="\n") as stream:
            for row in sorted(private_rows, key=lambda item: item["ecg_id"]):
                stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return report
