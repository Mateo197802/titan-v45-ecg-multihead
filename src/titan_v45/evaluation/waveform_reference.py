"""Score sealed waveform decisions against archived references after routing."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

import numpy as np

from titan_v45.contracts.profiles import CANONICAL_PROFILES
from titan_v45.evaluation.revision_report import BinaryPanel, binary_metrics, cluster_bootstrap
from titan_v45.evaluation.workflow import summarize_routes


def _key(row):
    return row["source"].casefold(), row["record_id"]


def _unique(rows):
    keys = [_key(row) for row in rows]
    if any(not all(key) for key in keys) or len(set(keys)) != len(keys):
        raise ValueError("empty or duplicate ECG reference key")
    return keys


def _flag(value):
    value = value.casefold()
    if value not in {"true", "false", "0", "1"}:
        raise ValueError("invalid reference or archived decision")
    return int(value in {"true", "1"})


def compare_binary_panel(archived, ledger, name):
    keys, truth, new, old, new_scores, old_scores = [], [], [], [], [], []
    for row, key in zip(archived, _unique(archived), strict=True):
        route = ledger.get(key, {})
        has_call = name in route.get("pathology", {})
        has_score = name in route.get("primary_scores", {})
        if has_call != has_score:
            raise ValueError("incomplete scored pathology row")
        if not has_score:
            continue
        keys.append(key)
        truth.append(_flag(row["target"]))
        new.append(int(route["pathology"][name]))
        old.append(_flag(row["predicted"]))
        new_scores.append(route["primary_scores"][name])
        old_scores.append(float(row["probability"]))
    return {
        "archived_reference_rows": len(archived),
        "missing_score_rows": len(archived) - len(keys),
        "new": binary_metrics(truth, new, new_scores),
        "archived_matched": binary_metrics(truth, old, old_scores),
    }, BinaryPanel(tuple(keys), np.array(truth), np.array(new))


def _compare_rhythm(archived, ledger, profile, classes, n_bootstrap):
    p8 = profile == "P8"
    ref, top, prefix = (
        ("accepted_labels", "predicted_label", "membership_prob_") if p8
        else ("true_labels", "pred_label", "prob_")
    )
    joined = []
    for row, key in zip(archived, _unique(archived), strict=True):
        current = ledger.get(key, {}).get(profile)
        if current is None:
            continue
        labels = set(row[ref].split("|"))
        historical = set(filter(None, row["predicted_labels"].split("|"))) if p8 else {
            c for c in classes if _flag(row["threshold_pass_" + c])
        }
        if (not labels or not labels <= set(classes) or not historical <= set(classes)
                or set(current["scores"]) != set(classes) or not set(current["labels"]) <= set(classes)
                or current["top1"] not in classes or row[top] not in classes):
            raise ValueError("invalid rhythm comparison classes")
        joined.append((key, labels, historical, row, current))
    keys = tuple(item[0] for item in joined)
    panels, metrics = {}, {}
    for name in classes:
        truth = [name in labels for _, labels, _, _, _ in joined]
        calls = [name in item["labels"] for _, _, _, _, item in joined]
        panels[name] = BinaryPanel(keys, np.array(truth), np.array(calls))
        metrics[name] = {
            "new": binary_metrics(truth, calls, [item["scores"][name] for *_, item in joined]),
            "archived_matched": binary_metrics(
                truth, [name in labels for _, _, labels, _, _ in joined],
                [row[prefix + name] for _, _, _, row, _ in joined],
            ),
        }
    return {
        "archived_reference_rows": len(archived), "matched_ecgs": len(joined),
        "missing_score_rows": len(archived) - len(joined),
        "matched_by_manifest_source": dict(sorted(Counter(k[0] for k in keys).items())),
        "accepted_top1_correct": {
            "new": sum(item["top1"] in labels for _, labels, _, _, item in joined),
            "archived_matched": sum(row[top] in labels for _, labels, _, row, _ in joined),
        },
        "classes": metrics,
        "bootstrap_new": cluster_bootstrap(panels, n_bootstrap=n_bootstrap) if joined else None,
    }


def _read_private_ledger(path: Path):
    raw = path.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    return dict(zip(_unique(rows), rows, strict=True)), hashlib.sha256(raw).hexdigest()


def summarize_selected_union(p4, rhythm):
    """Reconcile independently eligible release branches by exact key only."""
    routes = {}
    for key in p4.keys() | rhythm.keys():
        present = []
        for branch, ledger in (("pathology_only", p4), ("rhythm_only", rhythm)):
            if key not in ledger:
                continue
            row = ledger[key]
            if (row["pre"], row["post"]) == (branch, "quarantine_not_assessed"):
                present.append(branch)
            elif (row["pre"], row["post"]) != ("no_scores", "no_scores"):
                raise ValueError("unexpected state in a no-policy waveform ledger")
        pre = "both" if len(present) == 2 else present[0] if present else "no_scores"
        routes[key] = {"pre": pre, "post": "quarantine_not_assessed" if present else "no_scores"}
    return {
        **summarize_routes(routes), "unit": "source_and_record_id_not_verified_patient",
        "exact_key_overlap": len(p4.keys() & rhythm.keys()), "p4_keys": len(p4),
        "rhythm_keys": len(rhythm), "historical_parent_population_recovered": False,
    }


def build_waveform_reference_report(repo, *, pathology_ledger, rhythm_ledger, n_bootstrap=2000):
    if not isinstance(n_bootstrap, int) or n_bootstrap < 0:
        raise ValueError("bootstrap count must be a nonnegative integer")
    archived, manifests = {}, {}

    def read(name):
        raw = (repo / "outputs/results/external_dev/evidence" / name).read_bytes()
        normalized = raw.replace(b"\r\n", b"\n")
        archived[name] = hashlib.sha256(normalized).hexdigest()
        return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")))

    p4, p4_hash = _read_private_ledger(pathology_ledger)
    rhythm, rhythm_hash = _read_private_ledger(rhythm_ledger)

    def inventory(name):
        raw = (repo / "data/manifests/external_dev" / name).read_bytes()
        manifests[name] = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
        return {_key(row) for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))}

    p6_keys = inventory("rhythm_primary6_diagnostic_records.csv")
    if (p4.keys() != inventory("pathology_primary4_panels.csv")
            or rhythm.keys() != inventory("rhythm_primary8_records.csv")
            or not p6_keys <= rhythm.keys()
            or any(("P6" in row) != (key in p6_keys and "P8" in row)
                   for key, row in rhythm.items())):
        raise ValueError("private ledgers do not match the retained manifest inventories")
    panels, comparisons = {}, {}
    for name in CANONICAL_PROFILES["pathology_primary4"].classes:
        comparisons[name], panels[name] = compare_binary_panel(
            read(f"pathology_primary4_{name}_record_predictions.csv"), p4, name
        )
    return {
        "schema": "TITAN_V45_WAVEFORM_REFERENCE_COMPARISON_V1",
        "scope": "post_route_selected_development_references_not_independent_validation",
        "archived_reference_sha256_lf": archived,
        "manifest_sha256_lf": manifests,
        "private_ledger_sha256": {"P4": p4_hash, "rhythm": rhythm_hash},
        "selected_key_union": summarize_selected_union(p4, rhythm),
        "P4": {"classes": comparisons, "bootstrap_new": (
            cluster_bootstrap(panels, n_bootstrap=n_bootstrap)
            if all(panel.keys for panel in panels.values()) else None
        )},
        **{f"P{size}": _compare_rhythm(
            read(f"rhythm_primary{size}_record_predictions.csv"), rhythm, f"P{size}",
            CANONICAL_PROFILES[f"rhythm_primary{size}"].classes, n_bootstrap
        ) for size in (6, 8)},
    }
