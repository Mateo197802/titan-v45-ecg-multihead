from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA = "TITAN_V45_RECOMPUTED_RELEASE_EVIDENCE_V1"
TOLERANCE = 1e-12


def _json(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _csv(root: Path, relative: str) -> list[dict[str, str]]:
    with (root / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256_lf_normalized(path: Path) -> str:
    contents = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(contents).hexdigest()


def _close(actual: float, expected: float, description: str) -> None:
    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=TOLERANCE):
        raise ValueError(f"{description}: reported {expected:.16g}, recomputed {actual:.16g}")


def _bool(value: str, *, field: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"invalid boolean in {field}: {value!r}")
    return normalized == "true"


def _panel_counts(
    rows: list[dict[str, str]],
    classes: list[str],
    *,
    truth: str,
    predicted: str,
    multilabel_truth: bool = False,
    multilabel_predictions: bool = False,
) -> dict[str, dict[str, int | float]]:
    if not rows:
        raise ValueError("prediction evidence contains no rows")
    counts = {name: {key: 0 for key in ("tp", "tn", "fp", "fn")} for name in classes}
    for row in rows:
        if multilabel_truth:
            actual_labels = {label for label in row[truth].split("|") if label}
            unknown = actual_labels.difference(classes)
            if unknown:
                raise ValueError(f"unknown reference labels: {sorted(unknown)}")
        else:
            actual_label = row[truth]
            if actual_label not in classes:
                raise ValueError(f"unknown truth label {actual_label!r} in {truth}")
            actual_labels = {actual_label}

        if multilabel_predictions:
            predicted_labels = {label for label in row[predicted].split("|") if label}
        else:
            predicted_labels = {row[predicted]}
        unknown = predicted_labels.difference(classes)
        if unknown:
            raise ValueError(f"unknown predicted labels: {sorted(unknown)}")

        for label in classes:
            actual_positive = label in actual_labels
            predicted_positive = label in predicted_labels
            key = (
                "tp"
                if actual_positive and predicted_positive
                else "fn"
                if actual_positive
                else "fp"
                if predicted_positive
                else "tn"
            )
            counts[label][key] += 1

    for panel in counts.values():
        tp, tn, fp, fn = (int(panel[key]) for key in ("tp", "tn", "fp", "fn"))
        total = tp + tn + fp + fn
        panel["support"] = total
        panel["accuracy"] = (tp + tn) / total
        denominator = 2 * tp + fp + fn
        panel["f1"] = 2 * tp / denominator if denominator else 0.0
    return counts


def _boolean_panel_counts(
    rows: list[dict[str, str]], classes: list[str], truth_prefix: str, prediction_prefix: str
) -> dict[str, dict[str, int | float]]:
    counts: dict[str, dict[str, int | float]] = {}
    for label in classes:
        tp = tn = fp = fn = 0
        for row in rows:
            actual = _bool(row[f"{truth_prefix}{label}"], field=f"{truth_prefix}{label}")
            predicted = _bool(
                row[f"{prediction_prefix}{label}"], field=f"{prediction_prefix}{label}"
            )
            if actual and predicted:
                tp += 1
            elif actual:
                fn += 1
            elif predicted:
                fp += 1
            else:
                tn += 1
        total = tp + tn + fp + fn
        f1_denominator = 2 * tp + fp + fn
        counts[label] = {
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "support": total,
            "accuracy": (tp + tn) / total,
            "f1": 2 * tp / f1_denominator if f1_denominator else 0.0,
        }
    return counts


def _assert_panels(
    actual: dict[str, dict[str, int | float]],
    reported: dict[str, dict[str, Any]],
    profile: str,
) -> None:
    if list(actual) != list(reported):
        raise ValueError(f"{profile} panel order differs from its metric report")
    for label, panel in actual.items():
        report = reported[label]
        for key in ("tp", "tn", "fp", "fn"):
            if int(panel[key]) != int(report[key]):
                raise ValueError(f"{profile} {label} {key} differs from prediction evidence")
        if "f1" in report:
            _close(float(panel["f1"]), float(report["f1"]), f"{profile} {label} F1")
        if "accuracy" in report:
            _close(
                float(panel["accuracy"]),
                float(report["accuracy"]),
                f"{profile} {label} accuracy",
            )


def _assert_rows_match(
    left: list[dict[str, str]],
    right: list[dict[str, str]],
    fields: tuple[str, ...],
    description: str,
) -> None:
    left_rows = Counter(tuple(row[field] for field in fields) for row in left)
    right_rows = Counter(tuple(row[field] for field in fields) for row in right)
    if left_rows != right_rows:
        raise ValueError(f"{description} differs from its row-level evidence")


def _profile_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {profile["profile"]: profile for profile in payload["profiles"]}


def _verify_role_and_classes(
    profile: str,
    role: str,
    classes: list[str],
    canonical: dict[str, Any],
    metrics: dict[str, Any],
) -> None:
    expected = canonical[profile]
    if expected["release_role"] != role or metrics["release_role"] != role:
        raise ValueError(f"{profile} release role does not match canonical evidence")
    if expected["classes"] != classes or metrics["classes"] != classes:
        raise ValueError(f"{profile} class order does not match canonical evidence")


def verify_release_evidence(root: str | Path) -> dict[str, Any]:
    """Recompute published metrics from tracked record-level predictions and manifests."""
    root = Path(root).resolve()
    canonical = _profile_map(_json(root, "outputs/results/primary/canonical_profiles.json"))
    p8_metrics = _json(root, "outputs/results/external_dev/rhythm_primary8_metrics.json")
    p6_metrics = _json(root, "outputs/results/external_dev/rhythm_primary6_metrics.json")
    p4_metrics = _json(root, "outputs/results/external_dev/pathology_primary4_metrics.json")

    p8_classes = canonical["rhythm_primary8"]["classes"]
    p6_classes = canonical["rhythm_primary6_diagnostic"]["classes"]
    p4_classes = canonical["pathology_primary4"]["classes"]
    _verify_role_and_classes("rhythm_primary8", "primary8_candidate", p8_classes, canonical, p8_metrics)
    _verify_role_and_classes(
        "rhythm_primary6_diagnostic", "primary6_diagnostic", p6_classes, canonical, p6_metrics
    )
    _verify_role_and_classes("pathology_primary4", "primary4_pathology", p4_classes, canonical, p4_metrics)

    p8_path = "outputs/results/external_dev/evidence/rhythm_primary8_record_predictions.csv"
    p6_path = "outputs/results/external_dev/evidence/rhythm_primary6_record_predictions.csv"
    p8_rows = _csv(root, p8_path)
    p6_rows = _csv(root, p6_path)
    p8_manifest = _csv(root, "data/manifests/external_dev/rhythm_primary8_records.csv")
    p6_manifest = _csv(root, "data/manifests/external_dev/rhythm_primary6_diagnostic_records.csv")
    _assert_rows_match(
        p8_rows,
        p8_manifest,
        ("record_id", "record_base", "source", "target_label", "predicted_label", "window_count"),
        "Primary8 cohort manifest",
    )
    _assert_rows_match(
        [
            {
                **row,
                "predicted_label": row["pred_label"],
            }
            for row in p6_rows
        ],
        p6_manifest,
        ("record_id", "record_base", "source", "true_labels", "predicted_label", "correct", "window_count"),
        "Primary6 cohort manifest",
    )

    p8_panels = _panel_counts(
        p8_rows,
        p8_classes,
        truth="accepted_labels",
        predicted="predicted_labels",
        multilabel_truth=True,
        multilabel_predictions=True,
    )
    p8_accepted_correct = sum(
        row["predicted_label"] in {label for label in row["accepted_labels"].split("|") if label}
        for row in p8_rows
    )
    for row in p8_rows:
        if _bool(row["accepted_correct"], field="accepted_correct") != (
            row["predicted_label"] in {label for label in row["accepted_labels"].split("|") if label}
        ):
            raise ValueError("Primary8 accepted_correct flags disagree with reference labels")
        if _bool(row["single_label_correct"], field="single_label_correct") != (
            row["target_label"] == row["predicted_label"]
        ):
            raise ValueError("Primary8 single-label correctness flags disagree with labels")
    p8_accuracy = p8_accepted_correct / len(p8_rows)
    p8_macro_f1 = math.fsum(float(panel["f1"]) for panel in p8_panels.values()) / len(p8_panels)
    p8_single_label_accuracy = sum(
        row["target_label"] == row["predicted_label"] for row in p8_rows
    ) / len(p8_rows)
    if len(p8_rows) != int(p8_metrics["records"]):
        raise ValueError("Primary8 record count differs from its metric report")
    _assert_panels(p8_panels, p8_metrics["panels"], "Primary8")
    _close(p8_accuracy, float(p8_metrics["top1_accepted_accuracy"]), "Primary8 accepted accuracy")
    _close(p8_macro_f1, float(p8_metrics["binary_panel_macro_f1"]), "Primary8 macro-F1")
    _close(p8_accuracy, float(canonical["rhythm_primary8"]["accuracy"]), "Primary8 canonical accuracy")
    _close(p8_macro_f1, float(canonical["rhythm_primary8"]["macro_f1"]), "Primary8 canonical macro-F1")

    p6_panels = _boolean_panel_counts(p6_rows, p6_classes, "truth_", "threshold_pass_")
    p6_correct = sum(
        row["pred_label"] in {label for label in row["true_labels"].split("|") if label}
        for row in p6_rows
    )
    for row in p6_rows:
        if _bool(row["correct"], field="correct") != (
            row["pred_label"] in {label for label in row["true_labels"].split("|") if label}
        ):
            raise ValueError("Primary6 correctness flags disagree with labels")
    p6_accuracy = p6_correct / len(p6_rows)
    p6_macro_f1 = math.fsum(float(panel["f1"]) for panel in p6_panels.values()) / len(p6_panels)
    if len(p6_rows) != int(p6_metrics["records"]):
        raise ValueError("Primary6 record count differs from its metric report")
    if p6_correct != int(p6_metrics["correct"]):
        raise ValueError("Primary6 correct count differs from its metric report")
    _assert_panels(p6_panels, p6_metrics["panels"], "Primary6")
    _close(p6_accuracy, float(p6_metrics["top1_accuracy"]), "Primary6 top-1 accuracy")
    _close(p6_macro_f1, float(p6_metrics["binary_macro_f1"]), "Primary6 macro-F1")
    _close(p6_accuracy, float(canonical["rhythm_primary6_diagnostic"]["accuracy"]), "Primary6 canonical accuracy")
    _close(p6_macro_f1, float(canonical["rhythm_primary6_diagnostic"]["macro_f1"]), "Primary6 canonical macro-F1")

    p4_rows = [
        row
        for label in p4_classes
        for row in _csv(
            root,
            f"outputs/results/external_dev/evidence/pathology_primary4_{label}_record_predictions.csv",
        )
    ]
    p4_manifest = _csv(root, "data/manifests/external_dev/pathology_primary4_panels.csv")
    _assert_rows_match(
        p4_rows,
        p4_manifest,
        ("record_id", "record_base", "source", "pathology", "target", "predicted", "correct", "window_count"),
        "Primary4 cohort manifest",
    )
    if any(row["pathology"] not in p4_classes for row in p4_rows):
        raise ValueError("Primary4 prediction table contains an undeclared panel")
    if any(int(row["target"]) not in (0, 1) or int(row["predicted"]) not in (0, 1) for row in p4_rows):
        raise ValueError("Primary4 targets and predictions must be binary")
    p4_panels: dict[str, dict[str, int | float]] = {}
    for label in p4_classes:
        rows = [row for row in p4_rows if row["pathology"] == label]
        if not rows:
            raise ValueError(f"Primary4 panel {label} contains no rows")
        tp = tn = fp = fn = 0
        for row in rows:
            actual, predicted = int(row["target"]), int(row["predicted"])
            if _bool(row["correct"], field="correct") != (actual == predicted):
                raise ValueError(f"Primary4 {label} correctness flags disagree with labels")
            if actual and predicted:
                tp += 1
            elif actual:
                fn += 1
            elif predicted:
                fp += 1
            else:
                tn += 1
        total = tp + tn + fp + fn
        f1_denominator = 2 * tp + fp + fn
        p4_panels[label] = {
            "records": len(rows),
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "accuracy": (tp + tn) / total,
            "f1": 2 * tp / f1_denominator if f1_denominator else 0.0,
        }
    _assert_panels(p4_panels, p4_metrics["panels"], "Primary4")
    p4_accuracy = math.fsum(float(panel["accuracy"]) for panel in p4_panels.values()) / len(p4_panels)
    p4_macro_f1 = math.fsum(float(panel["f1"]) for panel in p4_panels.values()) / len(p4_panels)
    _close(p4_accuracy, float(p4_metrics["mean_accuracy"]), "Primary4 mean binary accuracy")
    _close(p4_macro_f1, float(p4_metrics["macro_f1"]), "Primary4 macro-F1")
    _close(p4_accuracy, float(canonical["pathology_primary4"]["accuracy"]), "Primary4 canonical accuracy")
    _close(p4_macro_f1, float(canonical["pathology_primary4"]["macro_f1"]), "Primary4 canonical macro-F1")

    rhythm_cohort = _json(root, "data/external_dev/rhythm/release_cohort_report.json")
    pathology_cohort = _json(root, "data/external_dev/pathology/release_cohort_report.json")
    if len(p8_rows) != int(rhythm_cohort["record_rows_primary8"]):
        raise ValueError("Primary8 prediction rows differ from the cohort report")
    if len(p6_rows) != int(rhythm_cohort["record_rows_primary6_diagnostic"]):
        raise ValueError("Primary6 prediction rows differ from the cohort report")
    if len(p4_rows) != int(pathology_cohort["panel_rows"]):
        raise ValueError("Primary4 panel rows differ from the cohort report")

    release = _json(root, "release-manifest.json")
    assets = {asset["name"]: asset["sha256"] for asset in release["assets"]}
    model_assets = {
        "rhythm_primary8": {
            "backbone": {"name": "backbone-v3f-original.pt", "sha256": assets["backbone-v3f-original.pt"]},
            "specialist": {
                "name": "specialists-v3q-primary8-best-candidate.pt",
                "sha256": assets["specialists-v3q-primary8-best-candidate.pt"],
            },
        },
        "rhythm_primary6_diagnostic": {
            "backbone": {"name": "backbone-v3f-original.pt", "sha256": assets["backbone-v3f-original.pt"]},
            "specialist": {
                "name": "specialists-v3p-e008-primary6-diagnostic.pt",
                "sha256": assets["specialists-v3p-e008-primary6-diagnostic.pt"],
            },
        },
        "pathology_primary4": {
            "backbone": {"name": "backbone-v3ag-pathology.pt", "sha256": assets["backbone-v3ag-pathology.pt"]},
            "specialist": {
                "name": "specialists-v3ag-primary4-calibrated.pt",
                "sha256": assets["specialists-v3ag-primary4-calibrated.pt"],
            },
        },
    }
    input_files = [
        p8_path,
        p6_path,
        "outputs/results/external_dev/evidence/pathology_primary4_ASMI_record_predictions.csv",
        "outputs/results/external_dev/evidence/pathology_primary4_LVH_record_predictions.csv",
        "outputs/results/external_dev/evidence/pathology_primary4_IMI_record_predictions.csv",
        "outputs/results/external_dev/evidence/pathology_primary4_ISC__record_predictions.csv",
        "data/manifests/external_dev/rhythm_primary8_records.csv",
        "data/manifests/external_dev/rhythm_primary6_diagnostic_records.csv",
        "data/manifests/external_dev/pathology_primary4_panels.csv",
        "outputs/results/primary/canonical_profiles.json",
        "outputs/results/external_dev/rhythm_primary8_metrics.json",
        "outputs/results/external_dev/rhythm_primary6_metrics.json",
        "outputs/results/external_dev/pathology_primary4_metrics.json",
        "data/external_dev/rhythm/release_cohort_report.json",
        "data/external_dev/pathology/release_cohort_report.json",
        "scripts/evaluation/verify_release_evidence.py",
        "src/titan_v45/evaluation/release_evidence.py",
        "release-manifest.json",
    ]
    return {
        "schema": SCHEMA,
        "verification": "passed",
        "scope": "Recomputes metrics from released record-level prediction tables; does not run ECG inference or retraining.",
        "release_tag": release["tag"],
        "profiles": {
            "rhythm_primary6_diagnostic": {
                "release_role": p6_metrics["release_role"],
                "records": len(p6_rows),
                "correct": p6_correct,
                "accuracy": p6_accuracy,
                "macro_f1": p6_macro_f1,
                "panels": p6_panels,
            },
            "pathology_primary4": {
                "release_role": p4_metrics["release_role"],
                "panel_rows": len(p4_rows),
                "mean_accuracy": p4_accuracy,
                "macro_f1": p4_macro_f1,
                "panels": p4_panels,
            },
            "rhythm_primary8": {
                "release_role": p8_metrics["release_role"],
                "records": len(p8_rows),
                "accepted_correct": p8_accepted_correct,
                "accepted_accuracy": p8_accuracy,
                "single_label_correct": sum(
                    row["target_label"] == row["predicted_label"] for row in p8_rows
                ),
                "single_label_accuracy": p8_single_label_accuracy,
                "macro_f1": p8_macro_f1,
                "panels": p8_panels,
            },
        },
        "model_assets": model_assets,
        "input_sha256_lf_normalized": {
            relative: _sha256_lf_normalized(root / relative) for relative in input_files
        },
    }
