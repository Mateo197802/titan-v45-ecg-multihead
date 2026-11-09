"""Independently verify the aggregate-only SPH post-dedup support report."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPLITS = {"train", "development", "exploratory_holdout"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_support(support: dict, expected_records: int, endpoint_names: set[str]) -> None:
    if support.get("individual_identifiers_exported") is not False:
        raise ValueError("support artifact declares individual identifiers")
    if support.get("record_denominator") != expected_records:
        raise ValueError("support artifact lacks an integer denominator")
    splits = support.get("splits")
    if not isinstance(splits, dict) or set(splits) != SPLITS:
        raise ValueError("support artifact has an invalid split set")
    if sum(item.get("records", -1) for item in splits.values()) != expected_records:
        raise ValueError("support split denominators do not reconcile")
    for item in splits.values():
        records = item.get("records")
        patients = item.get("patients")
        if (type(records) is not int or type(patients) is not int or records < 0
                or patients < 0 or patients > records):
            raise ValueError("support contains invalid record or patient counts")
        endpoints = item.get("endpoints")
        if not isinstance(endpoints, dict) or set(endpoints) != endpoint_names:
            raise ValueError("support endpoint set differs from frozen protocol")
        for values in endpoints.values():
            positive = values.get("positive_records")
            not_recorded = values.get("statement_not_recorded_records")
            positive_patients = values.get("positive_patients")
            if any(type(value) is not int or value < 0
                   for value in (positive, not_recorded, positive_patients)):
                raise ValueError("support contains invalid endpoint counts")
            if positive + not_recorded != records:
                raise ValueError("endpoint support does not reconcile to its split denominator")
            if positive_patients > patients or positive_patients > positive:
                raise ValueError("positive-patient support exceeds its denominator")


def verify_report(report: dict, config: dict) -> dict[str, object]:
    expected = config["expected_signal_audit"]
    endpoints = set(config["endpoints"])
    if report.get("schema") != "TITAN_V46_SPH_POSTDEDUP_SUPPORT_V1":
        raise ValueError("unexpected support report schema")
    if report.get("status") != "completed_aggregate_support_audit":
        raise ValueError("support report is not marked completed")
    if report.get("individual_identifiers_exported") is not False:
        raise ValueError("support report declares individual identifiers")
    if report.get("performance_metrics_computed") is not False:
        raise ValueError("support report must not contain model performance")
    if report.get("model_specific_preprocessing_assessed") is not False:
        raise ValueError("support report overstates model-specific preprocessing")
    if report.get("endpoints") != config["endpoints"]:
        raise ValueError("support endpoint contract differs from frozen configuration")
    if report.get("runtime") != config.get("runtime"):
        raise ValueError("support runtime differs from frozen configuration")

    source = report.get("source", {})
    if (source.get("records") != expected["records"]
            or source.get("patients") != expected["patients"]
            or source.get("input_sha256") != config["source"]["input_sha256"]
            or source.get("source_inventory_reference_sha256")
            != config["source"]["source_inventory_reference_sha256"]):
        raise ValueError("support source provenance differs from frozen configuration")

    signal = report.get("signal_audit", {})
    counts = signal.get("counts", {})
    for field in (
        "source_records", "valid_signal_records", "exact_duplicate_signal_groups",
        "exact_duplicate_signal_excess_records", "exact_duplicate_records_excluded",
        "unique_signal_records",
    ):
        expected_field = "records" if field == "source_records" else field
        if counts.get(field) != expected[expected_field]:
            raise ValueError(f"signal audit differs from frozen expectation: {field}")
    if signal.get("near_duplicate_detection") is not False:
        raise ValueError("support report overstates near-duplicate detection")
    if (counts["valid_signal_records"] - counts["exact_duplicate_records_excluded"]
            != counts["unique_signal_records"]):
        raise ValueError("unique-signal denominator does not reconcile")

    split = report.get("split", {})
    if split.get("labels_used_for_assignment") is not False:
        raise ValueError("split assignment was not label-blind")
    if split.get("patient_overlap_across_splits") != 0:
        raise ValueError("patient overlap is nonzero or unverified")
    before = report.get("support_before_signal_exclusions", {})
    after = report.get("support_after_signal_and_duplicate_exclusions", {})
    _validate_support(before, expected["records"], endpoints)
    _validate_support(after, expected["unique_signal_records"], endpoints)
    if (before["record_denominator"] != expected["records"]
            or after["record_denominator"] != expected["unique_signal_records"]):
        raise ValueError("support denominators do not match the frozen population")
    if sum(item["patients"] for item in before["splits"].values()) != expected["patients"]:
        raise ValueError("pre-exclusion patient split counts do not reconcile")
    for split_name in SPLITS:
        before_split = before["splits"][split_name]
        after_split = after["splits"][split_name]
        if (after_split["records"] > before_split["records"]
                or after_split["patients"] > before_split["patients"]):
            raise ValueError("post-dedup split support exceeds pre-exclusion support")
        for endpoint in endpoints:
            if (after_split["endpoints"][endpoint]["positive_records"]
                    > before_split["endpoints"][endpoint]["positive_records"]):
                raise ValueError(f"post-dedup split support exceeds source support: {endpoint}")
    for endpoint in endpoints:
        before_positive = sum(
            item["endpoints"][endpoint]["positive_records"]
            for item in before["splits"].values()
        )
        after_positive = sum(
            item["endpoints"][endpoint]["positive_records"]
            for item in after["splits"].values()
        )
        if before_positive != config["source"]["source_statement_counts_before_signal_exclusions"][endpoint]:
            raise ValueError(f"pre-exclusion endpoint support does not reconcile: {endpoint}")
        if after_positive > before_positive:
            raise ValueError(f"post-dedup support exceeds source support: {endpoint}")

    execution = report.get("execution", {})
    if (not re.fullmatch(r"[0-9a-f]{40}", execution.get("commit", ""))
            or not re.fullmatch(r"[0-9a-f]{64}", execution.get("script_sha256", ""))
            or not re.fullmatch(r"[0-9a-f]{64}", execution.get("config_sha256", ""))):
        raise ValueError("support report lacks valid execution provenance")
    return {
        "schema": "TITAN_V46_SPH_POSTDEDUP_SUPPORT_VERIFICATION_V1",
        "status": "passed",
        "commit": execution["commit"],
        "slurm_job_id": execution.get("slurm_job_id", "unknown"),
        "verified_checks": [
            "frozen_input_and_inventory_hashes",
            "source_population_and_exact_duplicate_counts",
            "post-dedup_split_denominators",
            "endpoint_support_reconciliation",
            "patient-level split totals",
            "aggregate-only output and non-performance scope",
        ],
        "individual_identifiers_exported": False,
    }


def _assert_outside(path: Path, roots: list[Path]) -> None:
    resolved = path.resolve()
    for root in roots:
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            continue
        raise ValueError("verification receipt must remain outside all Git checkouts")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-config-sha256", required=True)
    parser.add_argument("--forbidden-root", action="append", default=[], type=Path)
    args = parser.parse_args()
    roots = [ROOT, *(path.resolve() for path in args.forbidden_root)]
    _assert_outside(args.report, roots)
    _assert_outside(args.output, roots)
    if sha256_file(args.config) != args.expected_config_sha256:
        raise ValueError("frozen support configuration SHA-256 mismatch")
    report = json.loads(args.report.read_text(encoding="utf-8"))
    config = json.loads(args.config.read_text(encoding="utf-8"))
    receipt = verify_report(report, config)
    receipt["report_sha256"] = sha256_file(args.report)
    receipt["config_sha256"] = args.expected_config_sha256
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    os.chmod(args.output, 0o600)
    print(json.dumps({"output": str(args.output), "sha256": sha256_file(args.output)}, sort_keys=True))


if __name__ == "__main__":
    main()
