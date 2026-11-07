"""Measure numerical drift and decision margins on matched, sealed replays."""
from __future__ import annotations

import hashlib
import json

import numpy as np

from titan_v45.contracts.profiles import CANONICAL_PROFILES
from titan_v45.evaluation.revision_report import _load
from titan_v45.evaluation.waveform_reference import _read_private_ledger, _unique

HISTORICAL_ATOL = 1e-5
TOLERANCE_COUNTS = (HISTORICAL_ATOL, 1e-4, 1e-3)


def _probability_pair(archived, replayed):
    a, b = np.asarray(archived, dtype=float), np.asarray(replayed, dtype=float)
    if a.shape != b.shape or not a.size or any(
        not np.all((v >= 0) & (v <= 1)) for v in (a, b)
    ):
        raise ValueError("expected matched, finite probabilities")
    return a, b


def _drift(a, b):
    delta = b - a
    absolute = np.abs(delta)
    return {
        "pairs": int(delta.size),
        "mean_signed_difference": float(delta.mean()),
        "mean_absolute_difference": float(absolute.mean()),
        "median_absolute_difference": float(np.median(absolute)),
        "p95_absolute_difference": float(np.quantile(absolute, 0.95)),
        "p99_absolute_difference": float(np.quantile(absolute, 0.99)),
        "max_absolute_difference": float(absolute.max()),
        "above_historical_atol": int(np.count_nonzero(absolute > HISTORICAL_ATOL)),
        "counts_above_diagnostic_tolerances": {
            str(tol): int(np.count_nonzero(absolute > tol)) for tol in TOLERANCE_COUNTS
        },
    }


def binary_residuals(archived, replayed, threshold):
    a, b = _probability_pair(archived, replayed)
    if a.ndim != 1 or not 0 <= threshold <= 1:
        raise ValueError("invalid binary panel or threshold")
    score = _drift(a, b)
    return {
        "threshold": threshold,
        "score": score,
        "decision_changes": int(np.count_nonzero((a >= threshold) != (b >= threshold))),
        "minimum_archived_margin": float(np.min(np.abs(a - threshold))),
        "minimum_replayed_margin": float(np.min(np.abs(b - threshold))),
        "archived_margin_at_most_observed_max_error": int(
            np.count_nonzero(np.abs(a - threshold) <= score["max_absolute_difference"])
        ),
    }


def compare_pathology_replay_ledgers(archived, replayed, thresholds):
    if not archived or archived.keys() != replayed.keys() or any(
        row.get("primary_scores", {}).keys() != thresholds.keys()
        for ledger in (archived, replayed) for row in ledger.values()
    ):
        raise ValueError("pathology replay coverage or score classes differ")
    return {
        label: binary_residuals(
            [archived[key]["primary_scores"][label] for key in archived],
            [replayed[key]["primary_scores"][label] for key in archived],
            threshold,
        ) for label, threshold in thresholds.items()
    }


def ranking_residuals(archived, replayed, old_winner, new_winner):
    a, b = _probability_pair(archived, replayed)
    if a.ndim != 2 or a.shape[1] < 2:
        raise ValueError("ranking needs two or more classes")
    rows = np.arange(len(a))
    winners = [np.asarray(v, dtype=np.int64) for v in (old_winner, new_winner)]
    for scores, index in zip((a, b), winners, strict=True):
        if index.shape != rows.shape or np.any((index < 0) | (index >= a.shape[1])):
            raise ValueError("invalid winner indices")
        if np.any(scores[rows, index] != scores.max(axis=1)):
            raise ValueError("stored top-1 is not a score argmax")
    old, new = winners
    ordered = [np.argsort(-v, axis=1, kind="stable")[:, :2] for v in (a, b)]
    margin_a, margin_b = (v[rows, idx[:, 0]] - v[rows, idx[:, 1]]
                          for v, idx in zip((a, b), ordered, strict=True))
    changed = old != new
    stats = _drift(a, b)
    return {
        "records": len(a),
        "score": stats,
        "top1_changes": int(changed.sum()),
        "archived_top_ties": int(np.count_nonzero(margin_a == 0)),
        "replayed_top_ties": int(np.count_nonzero(margin_b == 0)),
        "archived_margin_at_most_twice_observed_max_error": int(
            np.count_nonzero(margin_a <= 2 * stats["max_absolute_difference"])
        ),
        "changes_with_same_top_two_candidates": int(np.count_nonzero(
            changed & np.all(np.sort(ordered[0], axis=1) == np.sort(ordered[1], axis=1), axis=1)
        )),
        "changed_rows": {
            "archived_winner_margin_min": float(margin_a[changed].min()),
            "archived_winner_margin_max": float(margin_a[changed].max()),
            "new_winner_margin_min": float(margin_b[changed].min()),
            "new_winner_margin_max": float(margin_b[changed].max()),
            "max_score_drift_on_changed_rows": float(np.abs(a[changed] - b[changed]).max()),
            "old_winner_minus_new_winner_after_replay_max": float(
                (b[rows, old] - b[rows, new])[changed].max()
            ),
        } if changed.any() else None,
    }


def build_replay_diagnostics(repo, pathology_ledger, rhythm_ledger):
    """Rejoin exact retained rows; emit no identifiers, paths or row-level outputs."""
    baseline_path = repo / "outputs/results/revision_20261107/matched_reference_metrics.json"
    baseline_bytes = baseline_path.read_bytes()
    baseline = json.loads(baseline_bytes)
    p4, p4_sha = _read_private_ledger(pathology_ledger)
    rhythm, rhythm_sha = _read_private_ledger(rhythm_ledger)
    ledger_sha = {"P4": p4_sha, "rhythm": rhythm_sha}
    if baseline["private_ledger_sha256"] != ledger_sha:
        raise ValueError("private ledgers differ from the sealed native inputs")
    input_refs = {}

    def read(name):
        return _load(repo, name, input_refs)

    pathology = {}
    contract = CANONICAL_PROFILES["pathology_primary4"]
    for label, threshold in zip(contract.classes, contract.thresholds, strict=True):
        rows = read(f"pathology_primary4_{label}_record_predictions.csv")
        if any(abs(float(row["threshold"]) - threshold) > 1e-12 for row in rows):
            raise ValueError("archived P4 threshold differs from frozen contract")
        keys = _unique(rows)
        archived = [float(row["probability"]) for row in rows]
        replayed = [p4[key]["primary_scores"][label] for key in keys]
        if (any((x >= threshold) != bool(int(row["predicted"]))
                for x, row in zip(archived, rows, strict=True))
                or any((x >= threshold) != p4[key]["pathology"][label]
                       for x, key in zip(replayed, keys, strict=True))):
            raise ValueError("P4 decisions disagree with frozen thresholds")
        pathology[label] = binary_residuals(archived, replayed, threshold)
    rhythms = {}
    for name, number, top, prefix in (
        ("rhythm_primary6_diagnostic", 6, "pred_label", "prob_"),
        ("rhythm_primary8", 8, "predicted_label", "membership_prob_"),
    ):
        profile, classes = f"P{number}", CANONICAL_PROFILES[name].classes
        rows = read(f"rhythm_primary{number}_record_predictions.csv")
        replay = [rhythm[key][profile] for key in _unique(rows)]
        archived = [[float(row[prefix + c]) for c in classes] for row in rows]
        replayed = [[row["scores"][c] for c in classes] for row in replay]
        diagnostic = ranking_residuals(
            archived, replayed, [classes.index(row[top]) for row in rows],
            [classes.index(row["top1"]) for row in replay],
        )
        diagnostic["score_field"] = prefix.rstrip("_")
        diagnostic["by_class"] = {
            c: _drift(a, b) for c, a, b in zip(
                classes, np.asarray(archived).T, np.asarray(replayed).T, strict=True
            )
        }
        rhythms[profile] = diagnostic
    refs = {path.rsplit("/", 1)[-1]: meta["sha256_lf_normalized"] for path, meta in input_refs.items()}
    if refs != baseline["archived_reference_sha256_lf"]:
        raise ValueError("archived scores differ from the sealed comparison")
    return {
        "schema": "TITAN_V45_REPLAY_RESIDUAL_DIAGNOSTICS_V1",
        "scope": "paired_selected_development_outputs_only",
        "historical_atol": HISTORICAL_ATOL,
        "historical_pipeline_equivalence_claimed": False,
        "margins_are_descriptive_not_future_robustness_guarantees": True,
        "sealed_comparison_sha256": hashlib.sha256(baseline_bytes).hexdigest(),
        "private_ledger_sha256": ledger_sha,
        "archived_reference_sha256_lf": refs,
        "P4": pathology,
        **rhythms,
    }
