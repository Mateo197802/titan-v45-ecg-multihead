"""Verify a completed locked CODE evaluation and export aggregate artifacts only."""
from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from pathlib import Path

import numpy as np
from code15_io import PROTOCOL, ROOT, digest
from verify_code15_evaluation import verify

SHARDS = {f"exams_part{i}.zip" for i in range(18)}
FIRST = "exams_part10.zip"
EVALUATION_RECEIPT = "code15_evaluation_receipt.json"
PINNED_FIRST = ROOT / "outputs/results/external_validation_20261111/code15-first" / EVALUATION_RECEIPT
AGGREGATES = {"EXTERNAL_CODE15_RESULTS.csv", "EXTERNAL_PER_CLASS_CONFUSION.csv",
              "EXTERNAL_CODE15_MACRO.csv", "EXTERNAL_CODE15_CALIBRATION.csv"}
COMMON_BORDERS = {"581/581", "0/0", "48/48", "648/648", "nonfinite", "all_zero"}
PRIVATE_FIELDS = {"exam", "exam_id", "patient", "patient_id", "record_id", "subject_id", "statement"}


def read(path):
    return json.loads(path.read_bytes())


def require(condition, error):
    if not condition:
        raise ValueError(error)


def duration_distribution(preflight, padding):
    by_archive = padding["per_archive_boundary_counts"]
    require(set(by_archive) == set(preflight), "padding and preflight archive sets differ")
    distribution = {}
    for name, groups in by_archive.items():
        selected, scored = Counter(), Counter()
        for row in groups:
            status = row["status"]
            key = f"{row['zero_left']}/{row['zero_right']}" if status == "finite_nonzero" else status
            require(type(row["n_ecg"]) is int and row["n_ecg"] > 0
                    and type(row["scored"]) is bool, "invalid padding group")
            selected[key] += row["n_ecg"]
            if row["scored"]:
                scored[key] += row["n_ecg"]
        require(selected == preflight[name]["selected_zero_border_pairs"],
                f"{name}: preflight and post-inference signal counts differ")

        def summarize(counts):
            return {key: counts[key] for key in sorted(COMMON_BORDERS)} | {
                "other_border_pairs": sum(n for key, n in counts.items() if key not in COMMON_BORDERS)}

        distribution[name] = {"selected": summarize(selected), "scored": summarize(scored)}
    return distribution


def verify_first_reuse(first, final, expected_rows):
    with np.load(first, allow_pickle=False) as cached, np.load(final, allow_pickle=False) as scored:
        lookup = {int(exam): i for i, exam in enumerate(cached["exams"])}
        pairs = [(lookup[int(exam)], i) for i, exam in enumerate(scored["exams"]) if int(exam) in lookup]
        require(len(pairs) == expected_rows, "first shard retained row count differs from signal audit")
        left = np.asarray([pair[0] for pair in pairs], dtype=int)
        right = np.asarray([pair[1] for pair in pairs], dtype=int)
        for field in ("labels", "patients", "baseline_P6", "candidate_P6", "baseline_P8", "candidate_P8"):
            require(np.array_equal(cached[field][left], scored[field][right]),
                    f"first-archive reuse mismatch: {field}")
    return len(pairs)


def gate(result, protocol):
    if not result["macro_f1_classes"]:
        return "NOT_EVALUABLE"
    limits = protocol["evaluation"]
    passed = (
        result["macro_f1_classes"] == list(protocol["reference"])
        and result["macro_f1_delta"] >= limits["promotion_macro_f1_gain_min"]
        and result["delta_ci95"][0] is not None
        and result["delta_ci95"][0] > 0
        and result["minimum_sensitivity_change"] >= -limits["promotion_max_sensitivity_drop"]
        and result["macro_brier_delta"] <= limits["promotion_max_macro_brier_increase"]
        and result["five_endpoint_empty_set_delta"] <= limits["promotion_max_empty_set_rate_increase"]
    )
    require(passed == result["observed_metric_gate_pass"], "frozen promotion gate mismatch")
    return "PASS" if passed else "FAIL"


def run(code, first, evaluation, destination):
    protocol = read(PROTOCOL)
    transport_path, preflight_path = (code / name for name in ("range_all_receipt.json",
                                                               "code15_preflight_receipt.json"))
    transport, preflight = read(transport_path), read(preflight_path)
    acquisition = {item["archive"]: item for item in transport["archives"]}
    require(transport["scope"] == "all" and transport["labels_read"] is False
            and len(transport["archives"]) == len(SHARDS) and acquisition.keys() == SHARDS,
            "18-archive transfer receipt required")
    seals = preflight["archives"]
    require(seals.keys() == SHARDS and preflight["protocol_sha256"] == digest(PROTOCOL)
            and preflight["labels_used"] is False, "18-archive label-blind integrity receipt required")
    for name, seal in seals.items():
        require(seal["crc_verified"] is True and all(seal[field] == acquisition[name][field]
                for field in ("sha256", "bytes", "publisher_md5")), f"{name}: acquisition identity mismatch")

    receipt_path = evaluation / EVALUATION_RECEIPT
    receipt = read(receipt_path)
    require(receipt["complete_archive_coverage"] is True and receipt["reused_verified_first_archive"] is True
            and receipt["protocol_sha256"] == digest(PROTOCOL)
            and receipt["preflight_receipt_sha256"] == digest(preflight_path)
            and receipt["archive_sha256"] == {name: seal["sha256"] for name, seal in seals.items()},
            "full frozen evaluation is not linked to the input seals")
    first_receipt_path = first / EVALUATION_RECEIPT
    require(digest(first_receipt_path) == digest(PINNED_FIRST), "first receipt differs from the committed receipt")
    first_receipt = read(first_receipt_path)
    require(first_receipt["archive_sha256"] == {FIRST: receipt["archive_sha256"][FIRST]}
            and all(first_receipt[key] == receipt[key] for key in ("candidate_receipt_sha256", "baseline_hashes")),
            "first archive and full evaluation disagree on frozen inputs")
    first_cache = first / "private_shard_cache.npz"
    final_scores = evaluation / "private_scores.npz"
    ledger = evaluation / "private_selection.json"
    require(digest(first_cache) == first_receipt["private_shard_cache_sha256"]
            and digest(final_scores) == receipt["private_scores_sha256"]
            and digest(ledger) == receipt["private_selection_sha256"], "private provenance hashes mismatch")
    flow = receipt["cohort_flow"]
    ledger_rows = read(ledger)
    require(len(ledger_rows["excluded_before_scoring"]) == flow["ecgs_excluded_before_scoring"]
            and len(ledger_rows["aligned_duplicate_exams"]) == flow["ecgs_excluded_as_aligned_duplicates"]
            and len(ledger_rows["eligible_exams"]) == flow["final_paired_ecgs"] == receipt["n_ecg"]
            and flow["selected_ecgs"] == preflight["selected_ecgs"] == sum(
                flow[key] for key in ("ecgs_excluded_before_scoring", "ecgs_excluded_as_aligned_duplicates",
                                     "final_paired_ecgs"))
            and flow["selected_patients"] == preflight["selected_patients"] == (
                flow["patients_with_no_scored_ecgs"] + flow["patients_with_scored_ecgs"])
            and flow["patients_with_scored_ecgs"] == receipt["n_patients"], "cohort denominators do not conserve")

    padding_path = evaluation / "padding_audit.json"
    padding = read(padding_path)
    require(padding["evaluation_receipt_sha256"] == digest(receipt_path)
            and padding["n_scored_verified"] == receipt["n_ecg"]
            and padding["labels_or_probabilities_loaded"] is False, "completed signal audit required")
    duration = duration_distribution(seals, padding)
    require(sum(sum(row["scored"].values()) for row in duration.values()) == receipt["n_ecg"],
            "scored signal denominator does not conserve")
    reused = verify_first_reuse(first_cache, final_scores, sum(duration[FIRST]["scored"].values()))
    metrics = verify(evaluation)
    original = receipt["point_estimates_independently_verified"]
    require(original["status"] == "PASS" and original["patient_bootstrap_replayed"] is True
            and metrics["aggregate_csv_sha256"] == original["aggregate_csv_sha256"] == receipt["aggregate_csv_sha256"]
            and metrics["metric_rows_verified"] == original["metric_rows_verified"],
            "point estimates or paired bootstrap not verified")
    decisions = {profile: gate(result, protocol) for profile, result in receipt["promotion"].items()}
    require(decisions.keys() == set(protocol["evaluation"]["profiles"])
            and all(receipt["promotion"][profile]["decision"] == decision for profile, decision in decisions.items()),
            "profile promotion result disagrees with the frozen criteria")

    aggregates = receipt["aggregate_views_sha256"]
    require(set(aggregates) <= AGGREGATES and (AGGREGATES - {"EXTERNAL_CODE15_CALIBRATION.csv"}) <= set(aggregates),
            "unexpected aggregate export names")
    for name, expected in {**aggregates, "CODE15_PER_CLASS.csv": receipt["aggregate_csv_sha256"]}.items():
        require(digest(evaluation / name) == expected, f"{name}: aggregate hash mismatch")
        with (evaluation / name).open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            require(reader.fieldnames and PRIVATE_FIELDS.isdisjoint(reader.fieldnames), f"{name}: private columns")
    destination.mkdir(mode=0o700, exist_ok=False)
    for name in sorted({*aggregates, "CODE15_PER_CLASS.csv", EVALUATION_RECEIPT}):
        shutil.copyfile(evaluation / name, destination / name)
    public_archives = {name: {key: entry[key] for key in ("sha256", "bytes", "publisher_md5")}
                       for name, entry in acquisition.items()}
    public = {"scope": "FULL_FROZEN_SAMPLE_OPERATIONAL_BENCHMARK", "archives": public_archives,
              "crc_verified_archives": len(seals), "duration_distribution": duration, "cohort_flow": flow,
              "promotion_gates": decisions, "p4": "NOT_EVALUABLE",
              "historical_patient_independence": receipt["historical_patient_independence"],
              "duration_contract_10_seconds": "LIMITED",
              "first_archive_bit_exact_rows_retained": reused, "independent_metric_verification": metrics,
              "paired_bootstrap_verified_in_evaluation": True,
              "source_receipt_sha256": {"transport": digest(transport_path), "preflight": digest(preflight_path),
                                         "evaluation": digest(receipt_path), "padding": digest(padding_path)}}
    output = destination / "CODE15_FULL_DELIVERY_RECEIPT.json"
    output.write_bytes((json.dumps(public, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps({"archives": len(seals), "n_ecg": receipt["n_ecg"], "gates": decisions,
                      "delivery_receipt_sha256": digest(output)}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("code", "first", "evaluation", "destination"):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    run(args.code, args.first, args.evaluation, args.destination)
