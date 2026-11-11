"""Recompute bounded V4 May confusion and error-subset routing totals."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.evaluation.audit_recovery_bundle import audit_recovery_bundle


def _unique_member(archive: zipfile.ZipFile, basename: str) -> str:
    matches = [name for name in archive.namelist() if name.endswith("/" + basename)]
    if len(matches) != 1:
        raise ValueError("required aggregate member is absent or ambiguous")
    return matches[0]


def _metrics_from_confusion(matrix: list[list[int]]) -> tuple[int, int, float, float]:
    size = len(matrix)
    if size != 9 or any(len(row) != size or any(value < 0 for value in row) for row in matrix):
        raise ValueError("expected a nonnegative 9-by-9 confusion matrix")
    total = sum(map(sum, matrix))
    correct = sum(matrix[index][index] for index in range(size))
    f1_values = []
    for index in range(size):
        true_positive = matrix[index][index]
        support = sum(matrix[index])
        predicted = sum(matrix[row][index] for row in range(size))
        denominator = support + predicted
        f1_values.append(2 * true_positive / denominator if denominator else 0.0)
    return total, correct, correct / total, sum(f1_values) / size


def recompute_legacy_v4_quarantine(archive_path: Path, expected_sha256: str | None = None) -> dict:
    integrity = audit_recovery_bundle(archive_path, expected_sha256)
    if not integrity["valid"]:
        raise ValueError("recovery bundle integrity checks failed")

    with zipfile.ZipFile(archive_path) as archive:
        matrix_name = _unique_member(archive, "primary9_confusion_matrix.csv")
        report_name = _unique_member(archive, "primary9_external_report.json")
        cascade_name = _unique_member(archive, "cascade_ood_v1_report.json")
        matrix_rows = list(csv.reader(io.StringIO(archive.read(matrix_name).decode("utf-8-sig"))))
        if len(matrix_rows) != 10 or len(matrix_rows[0]) != 10:
            raise ValueError("unexpected aggregate confusion table shape")
        class_names = matrix_rows[0][1:]
        if len(set(class_names)) != 9:
            raise ValueError("confusion table class labels are not unique")
        if [row[0] for row in matrix_rows[1:]] != class_names:
            raise ValueError("confusion table row and column labels differ")
        matrix = [[int(value) for value in row[1:]] for row in matrix_rows[1:]]
        total, correct, accuracy, macro_f1 = _metrics_from_confusion(matrix)

        external = json.loads(archive.read(report_name))
        if external.get("confusion_matrix") != matrix:
            raise ValueError("CSV and JSON confusion matrices disagree")
        if external.get("class_names") != class_names:
            raise ValueError("CSV and JSON class order disagrees")
        if external.get("total_evaluated") != total:
            raise ValueError("reported evaluation denominator disagrees")
        if not math.isclose(
            accuracy, external.get("accuracy", math.nan), rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValueError("reported accuracy disagrees with the confusion matrix")
        if not math.isclose(
            macro_f1, external.get("macro_f1", math.nan), rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValueError("reported macro-F1 disagrees with the confusion matrix")

        cascade = json.loads(archive.read(cascade_name))
        actions = cascade.get("action_counts", {})
        error_count = total - correct
        accepted = int(actions.get("accepted_prediction", 0))
        boundary = int(actions.get("quarantine_known_boundary", 0))
        rare = int(actions.get("quarantine_rare_rhythm", 0))
        pathology = int(actions.get("quarantine_pathology", 0))
        ood = int(actions.get("ood_real", 0))
        action_total = accepted + boundary + rare + pathology + ood
        if cascade.get("total_records") != error_count or action_total != error_count:
            raise ValueError("legacy cascade is not an exact partition of the confusion errors")
        coverage = accepted / error_count
        nonacceptance = (boundary + rare + pathology + ood) / error_count
        if not math.isclose(
            coverage, cascade.get("coverage", math.nan), rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValueError("reported cascade coverage uses a different numerator or denominator")
        if not math.isclose(
            nonacceptance, cascade.get("quarantine_rate", math.nan), rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValueError("reported error-subset nonacceptance fraction disagrees")

        return {
            "schema": "TITAN_V4_LEGACY_ERROR_SUBSET_RECOMPUTATION_V1",
            "source_scope": "V4 May 2026 legacy Primary-9 diagnostic; not V4.5 June",
            "primary9": {
                "classes": 9,
                "records": total,
                "correct_diagonal": correct,
                "off_diagonal_errors": error_count,
                "accuracy_recomputed": accuracy,
                "macro_f1_recomputed": macro_f1,
                "csv_matches_report_matrix": True,
                "reported_metrics_match": True,
            },
            "routing_on_error_subset_only": {
                "records": error_count,
                "accepted_prediction": accepted,
                "known_boundary": boundary,
                "rare_rhythm_quarantine": rare,
                "pathology_quarantine": pathology,
                "ood_real_label": ood,
                "action_sum": action_total,
                "coverage_fraction": coverage,
                "nonacceptance_fraction": nonacceptance,
                "full_672_record_quarantine_rate": None,
            },
            "aggregate_source_sha256": {
                "confusion_matrix_csv": hashlib.sha256(archive.read(matrix_name)).hexdigest(),
                "error_subset_routing_json": hashlib.sha256(archive.read(cascade_name)).hexdigest(),
            },
            "limits": [
                "The routing counts apply only to the 211-error subset, not all 672 records.",
                "ood_real is an archived algorithmic label, not clinical adjudication.",
                "No June 2026 V4.5 quarantine policy, ledger, checkpoint or job is established here.",
                "No post-routing outcomes, human review or corrected predictions are measured.",
            ],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    args = parser.parse_args()
    try:
        report = recompute_legacy_v4_quarantine(args.archive, args.expected_sha256)
    except (OSError, zipfile.BadZipFile, UnicodeDecodeError, csv.Error, ValueError) as exc:
        parser.error(f"legacy aggregate verification failed ({type(exc).__name__})")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
