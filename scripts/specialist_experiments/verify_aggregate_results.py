"""Validate sanitized specialist result tables without row-level data."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

IDENTIFIER_TOKENS = (
    "patient_id",
    "record_id",
    "ecg_id",
    "signal_id",
    "group_hash",
    "identity_hash",
    "waveform_path",
    "file_path",
)

CLASS_FIELDS = {
    "profile",
    "scope",
    "source",
    "model",
    "endpoint",
    "estimable",
    "rows",
    "n_ecg",
    "n_groups",
    "positive_support",
    "negative_support",
    "predicted_positive_support",
    "tp",
    "tn",
    "fp",
    "fn",
    "accuracy",
    "precision",
    "recall",
    "specificity",
    "f1",
    "negative_predictive_value",
}

SUMMARY_FIELDS = {
    "profile",
    "scope",
    "source",
    "model",
    "evaluable_endpoints",
    "model_evaluable_endpoints",
    "comparison_endpoints",
    "macro_f1",
    "baseline_macro_f1",
    "delta_macro_f1_vs_baseline",
}


def _number(row: dict[str, str], field: str) -> float | None:
    value = row.get(field, "").strip()
    if not value:
        return None
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"non-finite {field}")
    return number


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _close(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return left is right
    return math.isclose(left, right, rel_tol=2e-10, abs_tol=2e-10)


def verify_aggregate_results(per_class_path: Path, comparison_path: Path) -> dict[str, Any]:
    with per_class_path.open(newline="", encoding="utf-8-sig") as source:
        class_reader = csv.DictReader(source)
        class_fields = set(class_reader.fieldnames or ())
        class_rows = list(class_reader)
    with comparison_path.open(newline="", encoding="utf-8-sig") as source:
        summary_reader = csv.DictReader(source)
        summary_fields = set(summary_reader.fieldnames or ())
        summaries = list(summary_reader)

    if missing := CLASS_FIELDS - class_fields:
        raise ValueError(f"per-class table missing required columns: {sorted(missing)}")
    if missing := SUMMARY_FIELDS - summary_fields:
        raise ValueError(f"comparison table missing required columns: {sorted(missing)}")

    private_columns = sorted(
        field
        for field in class_fields | summary_fields
        if any(token in field.lower() for token in IDENTIFIER_TOKENS)
    )
    if private_columns:
        raise ValueError(f"identifier-like columns are not publishable: {private_columns}")

    formula_checks = 0
    class_index: dict[tuple[str, str, str, str], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in class_rows:
        key = (row["profile"], row["scope"], row["source"], row["model"])
        endpoint = row["endpoint"]
        if endpoint in class_index[key]:
            raise ValueError(f"duplicate per-class row for {key}/{endpoint}")
        class_index[key][endpoint] = row
        if row["estimable"].strip().lower() != "true":
            continue

        tp, tn, fp, fn = (int(row[field]) for field in ("tp", "tn", "fp", "fn"))
        n = int(row["rows"])
        positive, negative = int(row["positive_support"]), int(row["negative_support"])
        if n != tp + tn + fp + fn:
            raise ValueError(f"confusion counts do not sum to rows for {key}/{endpoint}")
        if positive != tp + fn or negative != tn + fp:
            raise ValueError(f"class supports disagree with confusion counts for {key}/{endpoint}")
        if int(row["predicted_positive_support"]) != tp + fp:
            raise ValueError(f"predicted-positive support disagrees for {key}/{endpoint}")

        expected = {
            "accuracy": (tp + tn) / n if n else None,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / positive if positive else None,
            "specificity": tn / negative if negative else None,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
            "negative_predictive_value": tn / (tn + fn) if tn + fn else None,
        }
        for field, value in expected.items():
            if not _close(_number(row, field), value):
                raise ValueError(f"{field} disagrees with confusion counts for {key}/{endpoint}")
        formula_checks += 1

    summary_index: dict[tuple[str, str, str, str], dict[str, str]] = {}
    macro_checks = 0
    delta_checks = 0
    for row in summaries:
        key = (row["profile"], row["scope"], row["source"], row["model"])
        if key in summary_index:
            raise ValueError(f"duplicate comparison summary for {key}")
        summary_index[key] = row
        try:
            endpoints = ast.literal_eval(row["comparison_endpoints"])
        except (SyntaxError, ValueError) as error:
            raise ValueError(f"invalid comparison_endpoints for {key}") from error
        if not isinstance(endpoints, list) or not endpoints or not all(
            isinstance(endpoint, str) for endpoint in endpoints
        ):
            raise ValueError(f"comparison_endpoints must be a nonempty string list for {key}")
        rows = class_index.get(key, {})
        selected = [rows[endpoint] for endpoint in endpoints if endpoint in rows]
        if len(selected) != len(endpoints) or any(
            item["estimable"].strip().lower() != "true" for item in selected
        ):
            raise ValueError(f"comparison summary references unavailable endpoints for {key}")
        if int(row["evaluable_endpoints"]) != len(endpoints):
            raise ValueError(f"evaluable endpoint count disagrees for {key}")
        macro = sum(float(item["f1"]) for item in selected) / len(selected)
        if not _close(_number(row, "macro_f1"), macro):
            raise ValueError(f"macro-F1 disagrees with per-class rows for {key}")
        macro_checks += 1

    for key, row in summary_index.items():
        if key[3] == "published_baseline":
            continue
        baseline_key = (*key[:3], "published_baseline")
        baseline = summary_index.get(baseline_key)
        if baseline is None:
            raise ValueError(f"missing published baseline summary for {key}")
        if not _close(_number(row, "baseline_macro_f1"), _number(baseline, "macro_f1")):
            raise ValueError(f"baseline macro-F1 disagrees for {key}")
        delta = _number(row, "macro_f1") - _number(baseline, "macro_f1")
        if not _close(_number(row, "delta_macro_f1_vs_baseline"), delta):
            raise ValueError(f"macro-F1 delta disagrees for {key}")
        delta_checks += 1

    return {
        "schema": "TITAN_SPECIALIST_AGGREGATE_AUDIT_V1",
        "status": "PASS",
        "per_class_rows": len(class_rows),
        "comparison_rows": len(summaries),
        "confusion_metric_rows_verified": formula_checks,
        "macro_f1_rows_verified": macro_checks,
        "baseline_delta_rows_verified": delta_checks,
        "identifier_like_columns": [],
        "inputs": {
            per_class_path.name: {"sha256": _sha256(per_class_path), "bytes": per_class_path.stat().st_size},
            comparison_path.name: {"sha256": _sha256(comparison_path), "bytes": comparison_path.stat().st_size},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-class", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    receipt = verify_aggregate_results(args.per_class, args.comparison)
    serialized = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_bytes(serialized.encode("utf-8"))
    print(serialized, end="")


if __name__ == "__main__":
    main()
