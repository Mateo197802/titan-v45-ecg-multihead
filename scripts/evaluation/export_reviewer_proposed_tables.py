"""Render sanitized reviewer tables from canonical public aggregate files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SPH_PATH = "outputs/results/external_sph/sph_aggregate_normalized_32669.json"
CANONICAL_PATH = "outputs/results/primary/canonical_profiles.json"
P4_METRICS_PATH = "outputs/results/external_dev/pathology_primary4_metrics.json"
P4_COHORT_PATH = "data/external_dev/pathology/release_cohort_report.json"
OUTPUT_PATH = "docs/reviewer_closure/REVIEWER_PROPOSED_TABLES.md"
EXPECTED_ENDPOINTS = {
    "P6:AFIB",
    "P6:SB",
    "P6:STACH",
    "P6:RBBB",
    "P6:PVC",
    "P8:AFIB",
    "P8:SB",
    "P8:STACH",
    "P8:RBBB",
    "P8:PAC",
    "P8:PVC",
    "P4:ASMI",
    "P4:LVH",
    "P4:IMI",
}
BOOTSTRAP_METRICS = (
    "accuracy",
    "sensitivity",
    "specificity",
    "precision",
    "npv",
    "f1",
    "auroc",
    "average_precision",
    "brier_score",
    "ece",
)


def _read_json(root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((root / relative_path).read_text(encoding="utf-8"))


def load_inputs(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        _read_json(root, SPH_PATH),
        _read_json(root, CANONICAL_PATH),
        _read_json(root, P4_METRICS_PATH),
        _read_json(root, P4_COHORT_PATH),
    )


def _validate_sph(sph: dict[str, Any]) -> None:
    endpoints = sph.get("endpoints", {})
    if set(endpoints) != EXPECTED_ENDPOINTS:
        raise ValueError("SPH aggregate must contain exactly the 14 compatible endpoints")

    for endpoint, row in endpoints.items():
        metrics = row["metrics"]
        n = row["source_records"]
        if n != 25_770 or row["scored_evaluable_records"] != n or row["unscored_source_records"] != 0:
            raise ValueError(f"{endpoint} does not have the complete 25,770-record denominator")
        if metrics["rows"] != n or metrics["positive_support"] + metrics["negative_support"] != n:
            raise ValueError(f"{endpoint} support does not match its denominator")
        if metrics["tp"] + metrics["fn"] != metrics["positive_support"]:
            raise ValueError(f"{endpoint} positive confusion counts are inconsistent")
        if metrics["tn"] + metrics["fp"] != metrics["negative_support"]:
            raise ValueError(f"{endpoint} negative confusion counts are inconsistent")
        intervals = row["cluster_bootstrap_ci95"]
        if any(intervals[name]["valid_replicates"] != 2_000 for name in BOOTSTRAP_METRICS):
            raise ValueError(f"{endpoint} is missing the expected 2,000 valid bootstrap draws")


def _validate_canonical(
    canonical: dict[str, Any], p4_metrics: dict[str, Any], p4_cohort: dict[str, Any]
) -> None:
    profiles = {row["profile"]: row for row in canonical.get("profiles", [])}
    expected = {"rhythm_primary6_diagnostic", "rhythm_primary8", "pathology_primary4"}
    if set(profiles) != expected:
        raise ValueError("canonical profile file must contain P6, P8 and P4")
    p4_rows = sum(p4_cohort["panel_counts"].values())
    if p4_rows != p4_cohort["panel_rows"] or p4_rows != 962:
        raise ValueError("P4 panel rows disagree between canonical evidence sources")
    for name in expected:
        profile = profiles[name]
        if profile["coverage"] != 1.0 or profile["hidden_abstention"]:
            raise ValueError(f"{name} does not match the canonical coverage contract")
    p4 = profiles["pathology_primary4"]
    if p4["accuracy_definition"] != "mean_binary_panel_accuracy":
        raise ValueError("P4 accuracy must retain the mean binary-panel definition")
    if profiles["rhythm_primary6_diagnostic"]["accuracy_definition"] != "record_top1":
        raise ValueError("P6 accuracy must retain the record-level top-1 definition")
    if profiles["rhythm_primary8"]["accuracy_definition"] != "record_top1_accepted_labels":
        raise ValueError("P8 accuracy must retain the accepted-label top-1 definition")
    if any(profiles[name]["macro_f1_definition"] != "binary_panel_macro_f1" for name in expected):
        raise ValueError("profile macro-F1 must retain the binary-panel definition")
    if abs(p4["accuracy"] - p4_metrics["mean_accuracy"]) > 1e-12:
        raise ValueError("P4 canonical accuracy disagrees with its panel metric report")
    if abs(p4["macro_f1"] - p4_metrics["macro_f1"]) > 1e-12:
        raise ValueError("P4 canonical macro-F1 disagrees with its panel metric report")


def _percentage(value: float) -> str:
    return f"{value * 100:.2f}%"


def _metric_ci(row: dict[str, Any], metric: str, *, percentage: bool) -> str:
    value = row["metrics"][metric]
    interval = row["cluster_bootstrap_ci95"][metric]
    render = _percentage if percentage else lambda x: f"{x:.4f}"
    return f"{render(value)} ({render(interval['low'])}-{render(interval['high'])})"


def render_tables(
    sph: dict[str, Any],
    canonical: dict[str, Any],
    p4_metrics: dict[str, Any],
    p4_cohort: dict[str, Any],
) -> str:
    _validate_sph(sph)
    _validate_canonical(canonical, p4_metrics, p4_cohort)
    lines = [
        "# Reviewer-Proposed Tables",
        "",
        "**For author review only.** These tables are not inserted into the submitted manuscript. Values are read from the linked aggregate JSON files; no patient/ECG rows or identifiers are used.",
        "",
        "## SPH ECG-statement endpoints",
        "",
        "Each endpoint has 25,770 scored ECG records (24,666 source patients overall), with no unscored records in the frozen receipt. A positive/negative statement is a source-code presence/absence label, not an adjudicated clinical diagnosis. `TP/FP/TN/FN` are ordered as written. Values in parentheses are 95% percentile intervals from 2,000 unstratified bootstrap replicates over connected components of patient IDs linked by exact-waveform duplicates; they are not intervals over independent institutions.",
        "",
        "| Endpoint | Source code(s) | Positive / negative | TP / FP / TN / FN | Accuracy (95% CI) | Sensitivity (95% CI) | Specificity (95% CI) | PPV (95% CI) | NPV (95% CI) | F1 (95% CI) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    endpoints = sph["endpoints"]
    for endpoint in sorted(endpoints):
        row = endpoints[endpoint]
        metrics = row["metrics"]
        codes = ", ".join(str(code) for code in row["code_set"])
        confusion = f"{metrics['tp']} / {metrics['fp']} / {metrics['tn']} / {metrics['fn']}"
        values = [
            endpoint,
            codes,
            f"{metrics['positive_support']} / {metrics['negative_support']}",
            confusion,
            _metric_ci(row, "accuracy", percentage=True),
            _metric_ci(row, "sensitivity", percentage=True),
            _metric_ci(row, "specificity", percentage=True),
            _metric_ci(row, "precision", percentage=True),
            _metric_ci(row, "npv", percentage=True),
            _metric_ci(row, "f1", percentage=True),
        ]
        lines.append("| " + " | ".join(values) + " |")

    lines.extend(
        [
            "",
            "### Ranking and calibration metrics",
            "",
            "| Endpoint | AUROC (95% CI) | Average precision (95% CI) | Brier score (95% CI) | ECE (95% CI) |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for endpoint in sorted(endpoints):
        row = endpoints[endpoint]
        values = [
            endpoint,
            _metric_ci(row, "auroc", percentage=False),
            _metric_ci(row, "average_precision", percentage=False),
            _metric_ci(row, "brier_score", percentage=False),
            _metric_ci(row, "ece", percentage=False),
        ]
        lines.append("| " + " | ".join(values) + " |")

    profiles = {row["profile"]: row for row in canonical["profiles"]}
    p6 = profiles["rhythm_primary6_diagnostic"]
    p8 = profiles["rhythm_primary8"]
    p4 = profiles["pathology_primary4"]
    p6_correct = round(p6["records"] * p6["accuracy"])
    p8_correct = round(p8["records"] * p8["accuracy"])
    if abs(p6_correct / p6["records"] - p6["accuracy"]) > 1e-12:
        raise ValueError("P6 accuracy is inconsistent with its integer correct count")
    if abs(p8_correct / p8["records"] - p8["accuracy"]) > 1e-12:
        raise ValueError("P8 accuracy is inconsistent with its integer correct count")
    p4_rows = p4_cohort["panel_rows"]
    lines.extend(
        [
            "",
            "## Historical selected-profile comparison",
            "",
            "| Profile | Evaluation unit and denominator | Decision policy | Accuracy (definition) | Macro-F1 | Disposition and limit |",
            "| --- | --- | --- | ---: | ---: | --- |",
            f"| Primary6 (P6) | {p6['records']:,} selected ECG | Record-level top-1; thresholded membership sets reported separately. | {p6_correct:,}/{p6['records']:,} = {_percentage(p6['accuracy'])} (record-level top-1) | {_percentage(p6['macro_f1'])} (binary-panel macro-F1) | Diagnostic profile; V3H informed model selection, so not an untouched test. |",
            f"| Primary8 (P8) | {p8['records']:,} selected ECG, including the P6 cohort | Record-level top-1; forced fallback if the threshold set is empty (58 selected-cohort cases). | {p8_correct:,}/{p8['records']:,} = {_percentage(p8['accuracy'])} (record-level top-1) | {_percentage(p8['macro_f1'])} (binary-panel macro-F1) | Candidate; does not pass the complete project gate. |",
            f"| Primary4 (P4) | {p4_rows:,} selected binary-panel observations across 733 ECG / 676 linked patients | Per-class checkpoint thresholds; binary panel observations are the unit. | {_percentage(p4['accuracy'])} (mean binary-panel accuracy) | {_percentage(p4['macro_f1'])} (binary-panel macro-F1) | Selected high-confidence panels; accepted by project decision, not independent clinical validation. |",
            "",
            "The P8 denominator overlaps P6 and must not be summed with it. P4 observations are not unique ECGs or patients. The reported canonical metrics are not proof of patient-disjoint training or exact historical loader reproduction; see [checkpoint-to-patient lineage](CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md) and [replay disposition](HISTORICAL_LOADER_IDENTITY_AND_REPLAY.md).",
            "",
            "## Sources and reproduction",
            "",
            f"- SPH endpoint data: [`{SPH_PATH}`](../../{SPH_PATH})",
            "- SPH endpoint definitions: [`docs/external_validation/sph_label_harmonization.md`](../external_validation/sph_label_harmonization.md)",
            f"- Rhythm profile results: [`{CANONICAL_PATH}`](../../{CANONICAL_PATH})",
            f"- P4 panel metrics: [`{P4_METRICS_PATH}`](../../{P4_METRICS_PATH})",
            f"- P4 panel denominator: [`{P4_COHORT_PATH}`](../../{P4_COHORT_PATH})",
            "- Rebuild this proposal with `python scripts/evaluation/export_reviewer_proposed_tables.py`.",
            "- The SPH target represents a recorded ECG statement; no code does not mean clinical absence. Quarantine was not assessed. The SPH transfer does not establish full historical source independence.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, help="Output Markdown path; defaults to the reviewer-closure document.")
    args = parser.parse_args()
    sph, canonical, p4_metrics, p4_cohort = load_inputs(args.root)
    rendered = render_tables(sph, canonical, p4_metrics, p4_cohort)
    output = args.output or args.root / OUTPUT_PATH
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"Wrote sanitized reviewer table proposal to {output}")


if __name__ == "__main__":
    main()
