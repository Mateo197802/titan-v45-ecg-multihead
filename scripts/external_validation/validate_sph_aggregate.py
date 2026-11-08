"""Validate aggregate SPH denominators, confusion metrics, and bootstrap metadata."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def _equal(actual, expected, name):
    if expected is None:
        if actual is not None:
            raise ValueError(f"{name}: expected undefined")
    elif actual is None or not math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12):
        raise ValueError(f"{name}: inconsistent value")


def _check_bootstrap(intervals, replicates, name):
    if intervals["_design"]["replicates"] != replicates:
        raise ValueError(f"{name}: incorrect bootstrap replicate count")
    for metric, interval in intervals.items():
        if metric == "_design":
            continue
        if interval["valid_replicates"] + interval["invalid_replicates"] != replicates:
            raise ValueError(f"{name}: {metric} bootstrap count mismatch")
        low, high = interval["low"], interval["high"]
        if low is not None and (high is None or not 0 <= low <= high <= 1):
            raise ValueError(f"{name}: {metric} interval invalid")


def validate_report(report, protocol):
    if report.get("schema") != "TITAN_V45_SPH_ENDPOINT_RESULTS_V1":
        raise ValueError("unexpected aggregate schema")
    flow = report["full_population_flow"]
    source = protocol["expected_source_records"]
    if flow["source_metadata_records"] != source or sum(flow["status_counts"].values()) != source:
        raise ValueError("population flow does not reconcile")
    if flow["scored_records"] != flow["status_counts"].get("scored", 0):
        raise ValueError("scored count does not match status counts")
    expected = {f"{row['profile']}:{row['name']}" for row in protocol["endpoints"]}
    if set(report["endpoints"]) != expected:
        raise ValueError("endpoint set does not match frozen protocol")
    for profile, values in report["profile_flow"].items():
        if values["source_records"] != source or values["scored_records"] > flow["scored_records"]:
            raise ValueError(f"{profile}: invalid coverage denominator")
        _equal(values["coverage"], values["scored_records"] / source, f"{profile} coverage")
    if set(report["profile_flow"]) != set(protocol["classes"]):
        raise ValueError("profile set does not match frozen protocol")
    for name, endpoint in report["endpoints"].items():
        if endpoint["source_records"] != source:
            raise ValueError(f"{name}: incorrect source count")
        if endpoint["source_statement_positive"] + endpoint["source_statement_negative"] != source:
            raise ValueError(f"{name}: source supports do not reconcile")
        if endpoint["scored_evaluable_records"] + endpoint["unscored_source_records"] != source:
            raise ValueError(f"{name}: scored and unscored counts do not reconcile")
        metrics = endpoint["metrics"]
        tp, tn, fp, fn = (metrics[key] for key in ("tp", "tn", "fp", "fn"))
        if any(not isinstance(value, int) or value < 0 for value in (tp, tn, fp, fn)):
            raise ValueError(f"{name}: invalid confusion counts")
        n = tp + tn + fp + fn
        if n != endpoint["scored_evaluable_records"] or n != metrics["rows"]:
            raise ValueError(f"{name}: confusion denominator mismatch")
        if tp + fn != endpoint["scored_positive"] or tn + fp != endpoint["scored_negative"]:
            raise ValueError(f"{name}: scored supports do not reconcile")
        for metric, numerator, denominator in (
            ("accuracy", tp + tn, n), ("precision", tp, tp + fp),
            ("recall", tp, tp + fn), ("specificity", tn, tn + fp),
        ):
            _equal(metrics[metric], numerator / denominator if denominator else None, f"{name} {metric}")
        denominator = 2 * tp + fp + fn
        _equal(metrics["f1"], 2 * tp / denominator if denominator else 0.0, f"{name} f1")
        for metric in ("auroc", "average_precision", "brier_score", "ece"):
            value = metrics[metric]
            if value is not None and not 0 <= value <= 1:
                raise ValueError(f"{name}: {metric} outside [0,1]")
        replicates = protocol["bootstrap"]["replicates"]
        _check_bootstrap(endpoint["cluster_bootstrap_ci95"], replicates, name)
        sensitivity = endpoint["discordant_exact_duplicate_sensitivity"]
        retained = sensitivity["scored_records_retained"]
        if not 0 <= retained <= n or not 0 <= sensitivity["source_records_excluded"] <= source:
            raise ValueError(f"{name}: invalid duplicate-sensitivity denominator")
        alternate = sensitivity["metrics"]
        intervals = sensitivity["cluster_bootstrap_ci95"]
        if retained == 0:
            if alternate is not None or intervals is not None:
                raise ValueError(f"{name}: empty sensitivity analysis must be undefined")
        else:
            if alternate["rows"] != retained or sum(alternate[key] for key in ("tp", "tn", "fp", "fn")) != retained:
                raise ValueError(f"{name}: duplicate-sensitivity confusion count mismatch")
            _check_bootstrap(intervals, replicates, f"{name} duplicate sensitivity")
    return {"source_records": source, "endpoints_checked": len(expected), "profiles_checked": len(report["profile_flow"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aggregate", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    args = parser.parse_args()
    result = validate_report(json.loads(args.aggregate.read_text(encoding="utf-8")),
                             json.loads(args.protocol.read_text(encoding="utf-8")))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
