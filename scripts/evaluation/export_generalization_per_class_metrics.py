from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

METRIC_FIELDS = (
    "accuracy",
    "precision",
    "recall",
    "specificity",
    "f1",
    "auroc",
    "average_precision",
    "brier_score",
    "ece",
)
CONFUSION_FIELDS = ("tp", "tn", "fp", "fn")


def export_metrics(source_path: Path, as_of: str) -> dict[str, Any]:
    source_path = source_path.resolve()
    source_relative = source_path.relative_to(ROOT).as_posix()
    source_bytes = source_path.read_bytes()
    source = json.loads(source_bytes)
    endpoints = []
    for name, row in source["endpoints"].items():
        metrics = row["metrics"]
        intervals = {
            metric: {
                field: interval[field]
                for field in ("low", "high", "valid_replicates", "invalid_replicates")
                if field in interval
            }
            for metric, interval in row.get("cluster_bootstrap_ci95", {}).items()
            if metric != "_design"
        }
        duplicate = row.get("discordant_exact_duplicate_sensitivity", {})
        duplicate_metrics = duplicate.get("metrics", {})
        endpoints.append(
            {
                "endpoint": name,
                "profile": name.split(":", 1)[0],
                "label": name.split(":", 1)[1],
                "reference_semantics": row["reference_semantics"],
                "n": metrics["rows"],
                "source_records": row["source_records"],
                "positive_support": metrics["positive_support"],
                "negative_support": metrics["negative_support"],
                "patient_clusters": row["patient_clusters_in_endpoint"],
                "confusion": {field: metrics[field] for field in CONFUSION_FIELDS},
                "metrics": {field: metrics[field] for field in METRIC_FIELDS if field in metrics},
                "patient_cluster_bootstrap_95ci": intervals,
                "discordant_exact_duplicate_sensitivity": {
                    "conflicting_duplicate_groups": duplicate.get("conflicting_duplicate_groups"),
                    "source_records_excluded": duplicate.get("source_records_excluded"),
                    "scored_records_retained": duplicate.get("scored_records_retained"),
                    "metrics": {
                        field: duplicate_metrics[field]
                        for field in (*CONFUSION_FIELDS, *METRIC_FIELDS)
                        if field in duplicate_metrics
                    },
                },
            }
        )

    return {
        "schema": "TITAN_V45_GENERALIZATION_PER_CLASS_METRICS_V1",
        "as_of": as_of,
        "source_path": source_relative,
        "source_sha256": sha256(source_bytes).hexdigest(),
        "source_schema": source["schema"],
        "protocol_commit": source["protocol_commit"],
        "protocol_sha256": source["protocol_sha256"],
        "scoring_receipt_sha256": source["scoring_receipt_sha256"],
        "scoring_ledger_sha256": source["scoring_ledger_sha256"],
        "evaluation_scope": {
            "study_scope": source["study_scope"],
            "source_records": source["full_population_flow"]["source_metadata_records"],
            "scored_records_per_profile": source["full_population_flow"]["scored_records"],
            "patient_clusters_for_interval_design": next(iter(source["endpoints"].values()))[
                "patient_clusters_in_endpoint"
            ],
            "profiles": ["P6", "P8", "P4"],
            "compatible_statement_endpoints": len(endpoints),
            "independent_test": False,
            "clinical_adjudication": False,
            "quarantine_assessed": False,
            "interpretation": "Existing SPH ECG-statement transfer results only; not a new independent validation experiment or clinical diagnosis study.",
        },
        "endpoints": endpoints,
        "limitations": source["limitations"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export aggregate SPH endpoint metrics without record-level fields.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    args = parser.parse_args()
    result = export_metrics(args.source, args.as_of)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
