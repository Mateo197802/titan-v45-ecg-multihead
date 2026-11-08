"""Validate the public-safe hash chain for a completed SPH aggregation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_receipts(config_path, score_path, aggregate_path, aggregation_path,
                      correction_path, wrapper_path):
    config = json.loads(config_path.read_text(encoding="utf-8"))
    score = json.loads(score_path.read_text(encoding="utf-8"))
    aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
    aggregation = json.loads(aggregation_path.read_text(encoding="utf-8"))
    correction = json.loads(correction_path.read_text(encoding="utf-8"))
    config_hash, score_hash, aggregate_hash = map(digest, (config_path, score_path, aggregate_path))
    checks = {
        "score_protocol_hash": score["protocol_sha256"] == config_hash,
        "score_source_hashes": score["source_sha256"] == config["source_sha256"],
        "score_model_hashes": score["model_sha256"] == config["model_sha256"],
        "score_label_blind": score["labels_used_for_inference_or_routing"] is False,
        "score_population": score["flow"]["metadata_records"] == config["expected_source_records"],
        "aggregate_protocol_hash": aggregate["protocol_sha256"] == config_hash,
        "aggregate_commit": aggregate["protocol_commit"] == score["protocol_commit"],
        "aggregate_score_receipt": aggregate["scoring_receipt_sha256"] == score_hash,
        "aggregate_ledger_hash": aggregate["scoring_ledger_sha256"] == score["ledger_sha256"],
        "aggregation_protocol_hash": aggregation["protocol_sha256"] == config_hash,
        "aggregation_commit": aggregation["commit"] == score["protocol_commit"],
        "aggregation_score_receipt": aggregation["inputs"]["scoring_receipt_sha256"] == score_hash,
        "aggregation_ledger_hash": aggregation["inputs"]["ledger_sha256"] == score["ledger_sha256"],
        "aggregation_output": aggregation["aggregate_sha256"] == aggregate_hash,
        "correction_output": correction["aggregate_sha256"] == aggregate_hash,
        "correction_aggregation_receipt": correction["frozen_evaluator_receipt_sha256"] == digest(aggregation_path),
        "correction_wrapper": correction["wrapper_sha256"] == digest(wrapper_path),
        "correction_frozen_evaluator": correction["frozen_evaluator_sha256"]
        == config["implementation_sha256"]["scripts/external_validation/evaluate_sph_ledger.py"],
        "correction_scope": correction["other_bootstrap_metrics_modified"] is False,
    }
    failed = [name for name, valid in checks.items() if not valid]
    if failed:
        raise ValueError("receipt chain failed: " + ", ".join(failed))
    return {"checks_passed": len(checks), "protocol_sha256": config_hash,
            "aggregate_sha256": aggregate_hash, "scoring_job_id": score["job_id"],
            "aggregation_job_id": aggregation["job_id"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("config", "score", "aggregate", "aggregation", "correction", "wrapper"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(validate_receipts(args.config, args.score, args.aggregate, args.aggregation,
                                       args.correction, args.wrapper), sort_keys=True))


if __name__ == "__main__":
    main()
