"""Aggregate-only comparison of frozen PAC probes with machine report mentions."""
from __future__ import annotations

import re
from collections import Counter, defaultdict

import numpy as np

from titan_v45.evaluation.pac_probe import (
    binary_metrics,
    patient_cluster_bootstrap,
    patient_component_ids,
)

REPORT_STATES = (
    "positive_mention",
    "explicit_negative_mention",
    "not_mentioned",
    "ambiguous_mention",
    "missing_report_text",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _metric_bundle(labels, scores, patients, signal_hashes, *, threshold, ece_bins,
                   replicates, seed):
    if not len(labels):
        return {"metrics": None, "bootstrap": {"status": "no_scored_binary_mentions"}}
    components = patient_component_ids(patients, signal_hashes)
    return {
        "metrics": binary_metrics(labels, scores, threshold=threshold, ece_bins=ece_bins),
        "bootstrap": patient_cluster_bootstrap(
            labels, scores, components, replicates=replicates, seed=seed
        ),
    }


def summarize_mimic_pac_concordance(
    report_states,
    scores,
    patient_ids,
    signal_hashes,
    waveform_statuses,
    *,
    threshold=0.5,
    ece_bins=10,
    replicates=2000,
    seed=20261109,
):
    """Summarize explicit automated-report concordance without emitting row data."""
    states = np.asarray(report_states, dtype=str)
    probability = np.asarray(scores, dtype=np.float64)
    patients = np.asarray(patient_ids, dtype=str)
    hashes = np.asarray(signal_hashes, dtype=str)
    statuses = np.asarray(waveform_statuses, dtype=str)
    if (states.ndim != 1 or not len(states) or any(
            values.shape != states.shape for values in (probability, patients, hashes, statuses))):
        raise ValueError("MIMIC states, scores, identifiers and statuses must align")
    failure_status = np.char.startswith(statuses, "failure:")
    if (not set(states).issubset(REPORT_STATES) or np.any(patients == "")
            or np.any(~((statuses == "scored") | failure_status))):
        raise ValueError("invalid MIMIC report state, patient or waveform status")
    scored = statuses == "scored"
    if (np.any(~np.isfinite(probability[scored]))
            or np.any((probability[scored] < 0) | (probability[scored] > 1))
            or np.any(np.isfinite(probability[~scored])) or np.any(hashes[~scored] != "")):
        raise ValueError("scored rows require finite probabilities and failed rows must be missing")
    if any(not _SHA256_RE.fullmatch(value) for value in hashes[scored]):
        raise ValueError("scored rows require canonical waveform SHA-256 values")
    if not 0 <= threshold <= 1 or ece_bins < 1 or replicates < 1:
        raise ValueError("invalid metric settings")

    state_counts = Counter(states.tolist())
    state_counts = {name: int(state_counts.get(name, 0)) for name in REPORT_STATES}
    status_counts = {name: int(count) for name, count in sorted(Counter(statuses).items())}
    explicit = np.isin(states, ["positive_mention", "explicit_negative_mention"])
    metric_rows = explicit & scored
    labels = (states[metric_rows] == "positive_mention").astype(np.int8)
    metric_scores = probability[metric_rows]
    metric_patients = patients[metric_rows]
    metric_hashes = hashes[metric_rows]
    primary = _metric_bundle(
        labels, metric_scores, metric_patients, metric_hashes,
        threshold=threshold, ece_bins=ece_bins, replicates=replicates, seed=seed,
    )

    hashes_to_rows = defaultdict(list)
    for index in np.flatnonzero(scored):
        hashes_to_rows[hashes[index]].append(int(index))
    duplicate_groups = [rows for rows in hashes_to_rows.values() if len(rows) > 1]
    cross_patient_groups = sum(
        len(set(patients[rows])) > 1 for rows in duplicate_groups
    )
    labels_by_hash = defaultdict(set)
    for row in np.flatnonzero(metric_rows):
        labels_by_hash[hashes[row]].add(int(states[row] == "positive_mention"))
    discordant_hashes = {
        digest for digest, values in labels_by_hash.items() if len(values) > 1
    }
    sensitivity_rows = metric_rows & ~np.isin(hashes, list(discordant_hashes))
    sensitivity = _metric_bundle(
        (states[sensitivity_rows] == "positive_mention").astype(np.int8),
        probability[sensitivity_rows], patients[sensitivity_rows], hashes[sensitivity_rows],
        threshold=threshold, ece_bins=ece_bins, replicates=replicates, seed=seed,
    )
    binary_denominator = int(explicit.sum())
    scored_binary = int(metric_rows.sum())
    return {
        "schema": "TITAN_V45_MIMIC_PAC_MACHINE_REPORT_CONCORDANCE_V1",
        "status": "exploratory_automatic_report_concordance",
        "record_count": int(len(states)),
        "patient_count": int(len(set(patients))),
        "report_state_counts": state_counts,
        "waveform_status_counts": status_counts,
        "binary_report_denominator": binary_denominator,
        "scored_binary_report_records": scored_binary,
        "coverage_among_explicit_binary_reports": (
            scored_binary / binary_denominator if binary_denominator else None
        ),
        "threshold": float(threshold),
        "metrics": primary["metrics"],
        "bootstrap": primary["bootstrap"],
        "duplicate_audit": {
            "exact_duplicate_groups": len(duplicate_groups),
            "cross_patient_exact_duplicate_groups": int(cross_patient_groups),
            "explicit_report_label_conflict_groups": len(discordant_hashes),
            "discordant_duplicate_rows_excluded_in_sensitivity": int(
                (metric_rows & ~sensitivity_rows).sum()
            ),
        },
        "discordant_duplicate_sensitivity": sensitivity,
        "reference_scope": "machine-generated report mention only; not a clinical reference",
        "identifiers_exported": False,
        "waveform_hashes_exported": False,
        "row_level_scores_exported": False,
        "report_text_exported": False,
    }
