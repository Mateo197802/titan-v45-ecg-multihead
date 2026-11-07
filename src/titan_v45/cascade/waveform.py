"""Label-free inventory and transition accounting for frozen waveform inference."""
from __future__ import annotations

import math
from collections import Counter
from pathlib import PurePosixPath

from titan_v45.cascade.policy import CASCADE_PATHOLOGIES
from titan_v45.evaluation.workflow import route_record, summarize_routes


def packaged_rhythm_path(key, path):
    """Apply the audited CODE-test archive directory alias, not an ID search."""
    source = "codetest_zenodo_3765780"
    prefix = f"records/{source}/"
    if key[0] == source and path.startswith(prefix):
        return "records/codetest/" + path[len(prefix):]
    return path


def build_waveform_inventory(rows):
    """Project an inventory to source, identity and relative signal path only."""
    inventory = {}
    for row in rows:
        key = row["source"].casefold(), row["record_id"]
        path = row["record_base"]
        p = PurePosixPath(path)
        if not all(key) or p.is_absolute() or ".." in p.parts or "\\" in path or ":" in path:
            raise ValueError("empty identity or unsafe waveform path")
        if p.parts[:1] != ("records",) or p.as_posix() != path:
            raise ValueError("unsafe or noncanonical waveform path")
        if key in inventory and inventory[key] != path:
            raise ValueError("conflicting waveform paths for one identity")
        inventory[key] = path
    if not inventory:
        raise ValueError("empty waveform inventory")
    if len(set(inventory.values())) != len(inventory):
        raise ValueError("one waveform path has multiple identities")
    return dict(sorted(inventory.items()))


def audit_pathology_waveforms(inventory, prepare, score, thresholds, *, batch_size=32):
    """Apply P4 decisions and expose auxiliary scores without an invented policy."""
    if batch_size < 1:
        raise ValueError("batch size must be positive")
    ledger = {}
    lead_support = Counter()
    errors = Counter()
    positives = Counter()
    auxiliary_support = Counter()
    entries = list(inventory.items())
    for start in range(0, len(entries), batch_size):
        keys, prepared = [], []
        for key, record_base in entries[start : start + batch_size]:
            try:
                sample = prepare(record_base)
            except (OSError, ValueError) as exc:
                errors[type(exc).__name__] += 1
                ledger[key] = {**route_record({}, {}, {}), "error": type(exc).__name__}
                continue
            keys.append(key)
            prepared.append(sample)
            lead_support[int(sample[1].sum())] += 1
        if not keys:
            continue
        for key, (primary, auxiliary) in zip(keys, score(prepared), strict=True):
            if primary.keys() != thresholds.keys():
                raise ValueError("score classes differ from frozen P4 thresholds")
            if set(auxiliary) != set(CASCADE_PATHOLOGIES) or any(
                not math.isfinite(x) or not 0 <= x <= 1 for x in auxiliary.values()
            ):
                raise ValueError("invalid auxiliary pathology score contract")
            row = route_record({}, {}, {c: (p, thresholds[c]) for c, p in primary.items()})
            positives.update(c for c, flag in row["pathology"].items() if flag)
            auxiliary_support.update(auxiliary.keys())
            ledger[key] = {**row, "primary_scores": primary, "auxiliary_scores": auxiliary,
                           "auxiliary_action": "no_frozen_policy"}
    return {
        **summarize_routes(ledger),
        "all_four_p4_scores_records": sum("primary_scores" in row for row in ledger.values()),
        "primary_positive_counts": {c: positives[c] for c in thresholds},
        "auxiliary_score_support": dict(sorted(auxiliary_support.items())),
        "present_lead_counts": {str(k): v for k, v in sorted(lead_support.items())},
        "input_error_counts": dict(sorted(errors.items())),
        "reference_labels_used_for_routing": False,
    }, ledger
