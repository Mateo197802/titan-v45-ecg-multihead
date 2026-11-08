"""Endpoint-level SPH reporting from a sealed label-blind scoring ledger."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from titan_v45.data.sph import read_sph_dictionary, read_sph_metadata
from titan_v45.evaluation.revision_report import binary_metrics


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _clusters(private_index):
    rows = [json.loads(line) for line in Path(private_index).read_text().splitlines()]
    by_patient = {row["patient_id"]: row["patient_id"] for row in rows}

    def find(item):
        if by_patient[item] != item:
            by_patient[item] = find(by_patient[item])
        return by_patient[item]

    def union(left, right):
        left, right = find(left), find(right)
        if left != right:
            by_patient[max(left, right)] = min(left, right)

    by_signal = defaultdict(set)
    for row in rows:
        by_signal[row["signal_sha256_canonical_f64"]].add(row["patient_id"])
    for patients in by_signal.values():
        ordered = sorted(patients)
        for patient in ordered[1:]:
            union(ordered[0], patient)
    return {row["ecg_id"]: find(row["patient_id"]) for row in rows}


def _discordant_duplicate_records(private_index, metadata, codes):
    rows = [json.loads(line) for line in Path(private_index).read_text().splitlines()]
    by_signal = defaultdict(list)
    for row in rows:
        record_id = row["ecg_id"]
        if record_id not in metadata:
            raise ValueError("duplicate index contains an unknown ECG")
        by_signal[row["signal_sha256_canonical_f64"]].append(record_id)
    excluded = set()
    groups = 0
    for record_ids in by_signal.values():
        if len(record_ids) < 2:
            continue
        reference_values = {
            bool(codes & metadata[record_id].primary_codes) for record_id in record_ids
        }
        if len(reference_values) > 1:
            groups += 1
            excluded.update(record_ids)
    return excluded, groups


def _metric_values(truth, predicted, scores, weights, ece_bins):
    truth = np.asarray(truth, dtype=np.int8)
    predicted = np.asarray(predicted, dtype=np.int8)
    scores = np.asarray(scores, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.int64)
    counts = np.bincount(2 * truth + predicted, weights=weights, minlength=4)
    tn, fp, fn, tp = map(float, counts)
    total = tn + fp + fn + tp
    positives, negatives = tp + fn, tn + fp
    predicted_pos, predicted_neg = tp + fp, tn + fn
    vals = {
        "accuracy": (tp + tn) / total if total else None,
        "sensitivity": tp / positives if positives else None,
        "specificity": tn / negatives if negatives else None,
        "precision": tp / predicted_pos if predicted_pos else None,
        "npv": tn / predicted_neg if predicted_neg else None,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
        "brier_score": None,
        "ece": None,
        "auroc": None,
        "average_precision": None,
    }
    sw = float(weights.sum())
    if not sw:
        return vals
    vals["brier_score"] = float(np.dot(weights, (scores - truth) ** 2) / sw)
    bin_index = np.minimum((scores * ece_bins).astype(int), ece_bins - 1)
    ece = 0.0
    for index in range(ece_bins):
        w = weights * (bin_index == index)
        n = int(w.sum())
        if n:
            ece += n / sw * abs(np.dot(w, scores - truth) / n)
    vals["ece"] = float(ece)

    active = weights > 0
    scores, truth, weights = scores[active], truth[active], weights[active]
    order = np.argsort(scores, kind="stable")
    sorted_scores, sorted_truth, sorted_weights = scores[order], truth[order], weights[order]
    starts = np.r_[0, np.flatnonzero(np.diff(sorted_scores)) + 1]
    pos_by_score = np.add.reduceat(sorted_weights * sorted_truth, starts)
    neg_by_score = np.add.reduceat(sorted_weights * (1 - sorted_truth), starts)
    pos_total, neg_total = int(pos_by_score.sum()), int(neg_by_score.sum())
    if pos_total and neg_total:
        neg_below = np.cumsum(neg_by_score) - neg_by_score
        vals["auroc"] = float(
            np.sum(pos_by_score * (neg_below + 0.5 * neg_by_score))
            / (pos_total * neg_total)
        )
    tp_desc = np.cumsum(pos_by_score[::-1])
    fp_desc = np.cumsum(neg_by_score[::-1])
    if pos_total:
        vals["average_precision"] = float(
            np.sum(np.diff(np.r_[0, tp_desc]) / pos_total * tp_desc / (tp_desc + fp_desc))
        )
    return vals


def _cluster_bootstrap(truth, predicted, scores, cluster_ids, *, seed, replicates, ece_bins):
    unique = sorted(set(cluster_ids))
    lookup = {value: index for index, value in enumerate(unique)}
    cluster_index = np.fromiter((lookup[value] for value in cluster_ids), dtype=np.int32)
    rng = np.random.Generator(np.random.PCG64(seed))
    values = defaultdict(list)
    invalid = Counter()
    for _ in range(replicates):
        draw = rng.integers(0, len(unique), size=len(unique))
        cluster_weight = np.bincount(draw, minlength=len(unique))
        replicate = _metric_values(
            truth, predicted, scores, cluster_weight[cluster_index], ece_bins
        )
        for name, value in replicate.items():
            if value is None or not np.isfinite(value):
                invalid[name] += 1
            else:
                values[name].append(float(value))
    tail = 0.025
    return {
        name: {
            "low": float(np.quantile(samples, tail)) if samples else None,
            "high": float(np.quantile(samples, 1 - tail)) if samples else None,
            "valid_replicates": len(samples),
            "invalid_replicates": replicates - len(samples),
        }
        for name, samples in sorted(values.items())
    } | {
        "_design": {
            "unit": "connected_component_of_patient_ids_linked_by_exact_duplicate_waveforms",
            "method": "unstratified_cluster_percentile_bootstrap",
            "seed": seed,
            "replicates": replicates,
            "rng": "numpy.PCG64",
            "invalid_replicates_by_metric": dict(sorted(invalid.items())),
        }
    }


def evaluate_sph_ledger(
    *,
    source: Path,
    ledger: Path,
    scoring_receipt: Path,
    duplicate_index: Path,
    protocol: dict,
):
    receipt = json.loads(scoring_receipt.read_text(encoding="utf-8"))
    if receipt["ledger_sha256"] != _sha256(ledger):
        raise ValueError("scoring ledger hash does not match its sealed receipt")
    if receipt["stage"] != "full_population":
        raise ValueError("only the full-population scoring receipt is evaluable")
    frozen_controls = protocol["preperformance_controls"]
    duplicate_index_sha256 = _sha256(duplicate_index)
    if (duplicate_index_sha256 != frozen_controls["private_duplicate_index_sha256"]
            or duplicate_index_sha256 != receipt["private_duplicate_index_sha256"]):
        raise ValueError("private duplicate index hash differs from the frozen protocol")
    expected_control_hashes = {
        name: item["sha256"]
        for name, item in frozen_controls["aggregates"].items()
    }
    if receipt["preperformance_control_sha256"] != expected_control_hashes:
        raise ValueError("pre-performance control hashes differ from the scoring receipt")
    primary, modifier = read_sph_dictionary((source / "code.csv").read_text(encoding="utf-8-sig"))
    metadata = read_sph_metadata(
        (source / "metadata.csv").read_text(encoding="utf-8-sig"), primary, modifier
    )
    clusters = _clusters(duplicate_index)
    rows = {}
    for line in ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        key = row["record_id"]
        if key in rows:
            raise ValueError("duplicate ECG in scoring ledger")
        rows[key] = row
    if rows.keys() != metadata.keys():
        raise ValueError("scoring ledger does not cover the source metadata universe")
    if clusters.keys() != metadata.keys():
        raise ValueError("private duplicate index does not cover the source metadata universe")
    if len(rows) != protocol["expected_source_records"]:
        raise ValueError("source population differs from frozen protocol")
    endpoint_reports = {}
    for endpoint in protocol["endpoints"]:
        profile, name, codes = endpoint["profile"], endpoint["name"], set(endpoint["codes"])
        y, predicted, scores, cluster_ids = [], [], [], []
        conflicting_records, conflicting_groups = _discordant_duplicate_records(
            duplicate_index, metadata, codes
        )
        sensitivity_y, sensitivity_predicted, sensitivity_scores, sensitivity_clusters = [], [], [], []
        for record_id, metadata_row in metadata.items():
            row = rows[record_id]
            if row["status"] != "scored":
                continue
            if profile not in row["profiles"] or name not in row["profiles"][profile]["scores"]:
                continue
            y.append(int(bool(codes & metadata_row.primary_codes)))
            predicted.append(int(name in row["profiles"][profile]["labels"]))
            scores.append(float(row["profiles"][profile]["scores"][name]))
            cluster_ids.append(clusters[record_id])
            if record_id not in conflicting_records:
                sensitivity_y.append(y[-1])
                sensitivity_predicted.append(predicted[-1])
                sensitivity_scores.append(scores[-1])
                sensitivity_clusters.append(cluster_ids[-1])
        if not y:
            raise ValueError(f"endpoint has no scored rows: {name}")
        metrics = binary_metrics(y, predicted, scores, ece_bins=protocol["metrics"]["ece_bins"])
        bootstrap = _cluster_bootstrap(
            y,
            predicted,
            scores,
            cluster_ids,
            seed=protocol["bootstrap"]["seed"] + protocol["endpoints"].index(endpoint),
            replicates=protocol["bootstrap"]["replicates"],
            ece_bins=protocol["metrics"]["ece_bins"],
        )
        sensitivity_metrics = binary_metrics(
            sensitivity_y,
            sensitivity_predicted,
            sensitivity_scores,
            ece_bins=protocol["metrics"]["ece_bins"],
        ) if sensitivity_y else None
        sensitivity_bootstrap = _cluster_bootstrap(
            sensitivity_y,
            sensitivity_predicted,
            sensitivity_scores,
            sensitivity_clusters,
            seed=protocol["bootstrap"]["seed"] + protocol["endpoints"].index(endpoint),
            replicates=protocol["bootstrap"]["replicates"],
            ece_bins=protocol["metrics"]["ece_bins"],
        ) if sensitivity_y else None
        endpoint_reports[f"{profile}:{name}"] = {
            "reference": endpoint["reference"],
            "reference_semantics": "SPH documented ECG statement; not clinical diagnosis",
            "code_set": sorted(codes),
            "source_records": len(metadata),
            "source_statement_positive": sum(bool(codes & row.primary_codes) for row in metadata.values()),
            "source_statement_negative": len(metadata) - sum(
                bool(codes & row.primary_codes) for row in metadata.values()
            ),
            "scored_evaluable_records": len(y),
            "scored_positive": int(sum(y)),
            "scored_negative": len(y) - int(sum(y)),
            "unscored_source_records": len(metadata) - len(y),
            "metrics": metrics,
            "cluster_bootstrap_ci95": bootstrap,
            "patient_clusters_in_endpoint": len(set(cluster_ids)),
            "discordant_exact_duplicate_sensitivity": {
                "conflicting_duplicate_groups": conflicting_groups,
                "source_records_excluded": len(conflicting_records),
                "scored_records_retained": len(sensitivity_y),
                "metrics": sensitivity_metrics,
                "cluster_bootstrap_ci95": sensitivity_bootstrap,
                "definition": "exclude every member of an exact-signal group whose SPH statement reference disagrees for this endpoint; primary analysis retains all records",
            },
        }
    states = Counter(row["status"] for row in rows.values())
    profile_flow = {}
    for profile in ("P6", "P8", "P4"):
        profile_rows = [
            row for row in rows.values()
            if row["status"] == "scored" and profile in row.get("profiles", {})
        ]
        class_counts = Counter()
        top1_counts = Counter()
        empty_decisions = 0
        fallback_records = 0
        for row in profile_rows:
            decision = row["profiles"][profile]
            class_counts.update(decision["labels"])
            top1_counts.update([decision["top1"]])
            empty_decisions += not decision["labels"]
            fallback_records += bool(decision["used_fallback"])
        profile_flow[profile] = {
            "scored_records": len(profile_rows),
            "source_records": len(metadata),
            "coverage": len(profile_rows) / len(metadata),
            "rhythm_windows": sum(
                row.get("rhythm_windows", 0) for row in profile_rows
            ) if profile in {"P6", "P8"} else None,
            "predicted_label_records_by_class": dict(sorted(class_counts.items())),
            "top1_records_by_class": dict(sorted(top1_counts.items())),
            "empty_label_set_records": empty_decisions,
            "fallback_records": fallback_records,
        }
    technical_failure_reasons = Counter(
        row.get("reason", "unspecified") for row in rows.values()
        if row["status"] == "technical_exclusion"
    )
    return {
        "schema": "TITAN_V45_SPH_ENDPOINT_RESULTS_V1",
        "study_scope": "transfer_to_distinct_hospital_source_with_historical_traceability_limitations",
        "protocol_commit": receipt["protocol_commit"],
        "protocol_sha256": receipt["protocol_sha256"],
        "scoring_receipt_sha256": _sha256(scoring_receipt),
        "scoring_ledger_sha256": receipt["ledger_sha256"],
        "private_duplicate_index_sha256": _sha256(duplicate_index),
        "preperformance_control_sha256": receipt["preperformance_control_sha256"],
        "data_hashes": receipt["source_sha256"],
        "model_hashes": receipt["model_sha256"],
        "full_population_flow": {
            "source_metadata_records": len(metadata),
            "archive_records": receipt["flow"]["archive_records"],
            "scored_records": states.get("scored", 0),
            "technical_exclusions": states.get("technical_exclusion", 0),
            "missing_signal": states.get("missing_signal", 0),
            "no_metadata": states.get("no_metadata", 0),
            "status_counts": dict(sorted(states.items())),
            "technical_failure_reasons": dict(sorted(technical_failure_reasons.items())),
            "quarantine_assessed_records": 0,
            "quarantine_rate": None,
            "quarantine_reason": "no historically defined uncertainty or quarantine policy",
        },
        "profile_flow": profile_flow,
        "endpoints": endpoint_reports,
        "limitations": [
            "No overall Primary6, Primary8 or Primary4 clinical accuracy is defined across incompatible or proxy-only references.",
            "Scores are conditional on a documented SPH ECG statement and are not clinical disease labels.",
            "No external recalibration, threshold tuning, retraining or checkpoint selection was performed.",
            "Historical full training-data lineage is incomplete; complete independence is not certified.",
            "Exact duplicate-connected patient components are used for bootstrap; approximate duplicates are not assessed.",
        ],
    }
