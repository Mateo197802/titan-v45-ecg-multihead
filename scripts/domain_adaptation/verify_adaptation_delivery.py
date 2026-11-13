"""Rebuild and verify aggregate adaptation tables from sealed public evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev

RUN_FIELDS = ("mode", "normalization", "seed", "slurm_job", "best_epoch", "validation_macro_ap",
              "validation_macro_f1_at_half", "trainable_parameters", "code_commit", "checkpoint_sha256",
              "validation_source")
HEX = re.compile(r"[0-9a-f]{64}\Z")
PUBLIC_TYPES = {".csv", ".json", ".txt"}
PRIVATE_NAMES = {"exam", "patient", "ecg_id", "exam_id", "patient_id", "labels", "waveform", "identity"}
ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def assert_hash(path, expected):
    if not HEX.fullmatch(expected) or sha(path) != expected:
        raise ValueError(f"digest mismatch: {path.name}")


def ratio(a, b):
    return a / b if b else None


def verify_confusion(row, sensitivity, positive, negative):
    tp, tn, fp, fn = (int(row[key]) for key in ("tp", "tn", "fp", "fn"))
    if (min(tp, tn, fp, fn) < 0 or tp + fn != int(row[positive]) or tn + fp != int(row[negative])
            or not math.isclose(float(row["f1"]), ratio(2 * tp, 2 * tp + fp + fn) or 0, abs_tol=1e-12)
            or not math.isclose(float(row[sensitivity]), tp / (tp + fn), abs_tol=1e-12)
            or not math.isclose(float(row["specificity"]), tn / (tn + fp), abs_tol=1e-12)):
        raise ValueError("confusion counts or derived rates disagree")


def verify_cross_source(evidence):
    extra = evidence / "ADDITIONAL_SOURCE_RECEIPT.json"
    if not extra.is_file():
        return None
    receipt = json.loads(extra.read_bytes())
    protocol = ROOT / "docs/domain_adaptation/CROSS_SOURCE_PROTOCOL.json"
    assert_hash(protocol, receipt["protocol_sha256"])
    caps = json.loads(protocol.read_bytes())["sources"]
    sources = receipt["sources"]
    if (receipt["code_label_files_read"] or receipt["patient_independence_across_sources"] != "NOT_CERTIFIED"
            or set(sources) != {"chapman_shaoxing/train", "chapman_shaoxing/validation", "cpsc2018/train"}
            or sources["cpsc2018/train"]["patients"] is not None):
        raise ValueError("additional source receipt does not match its frozen scope")
    accounted = (sum(row["ecgs"] for row in sources.values()) + sum(receipt["other_exclusions"].values())
                 + receipt["total_aligned_exclusions"])
    if (accounted != sum(sum(row["caps"].values()) for row in caps.values())
            or not 0 <= receipt["external_code_waveform_matches_excluded"] <= receipt["total_aligned_exclusions"]):
        raise ValueError("additional source denominator or exclusions do not reconcile")
    for scope, row in sources.items():
        if scope.startswith("chapman_shaoxing/") and row["patients"] != row["ecgs"]:
            raise ValueError("Chapman source patient proxy does not match ECG units")
        for values in row["endpoints"].values():
            if set(values) != {"-1", "0", "1"} or min(values.values()) < 0 or sum(values.values()) != row["ecgs"]:
                raise ValueError("additional source reference supports do not reconcile")
    transfer = evidence / "SOURCE_GENERALIZATION_RECEIPT.json"
    if transfer.is_file():
        run = json.loads(transfer.read_bytes())
        table = evidence / "SOURCE_GENERALIZATION_MATRIX.csv"
        assert_hash(table, run["metrics_sha256"])
        rows = read_csv(table)
        if len(rows) != run["rows"] or run["code_evaluation_test_opened"] or run["independent_generalization"] != "NOT_EVALUATED":
            raise ValueError("invalid source transfer receipt")
        for row in rows:
            if row["estimable"] == "True":
                verify_confusion({**row, "negatives": int(row["ecgs"]) - int(row["positive_ecgs"])},
                                 "sensitivity", "positive_ecgs", "negatives")
    probe = evidence / "SOURCE_DESCRIPTOR_PROBE.json"
    if probe.is_file():
        data = json.loads(probe.read_bytes())
        if (data["test_opened"] or data["diagnostic_labels_used"] or data["additional_source_receipt_sha256"] != sha(extra)
                or data["ecg_duration_seconds"] != 10):
            raise ValueError("source recognition probe exceeded its scope")
    return sha(extra)


def verify(evidence, rebuild=False):
    qc = json.loads((evidence / "PATIENT_AND_SIGNAL_LEAKAGE_AUDIT.json").read_bytes())
    assert_hash(evidence / "EXTERNAL_DATA_MANIFESTS_SUMMARY.csv", qc["public_cohort_counts_sha256"])
    ref = json.loads((evidence / "VALIDATION_BASELINES_RECEIPT.json").read_bytes())
    base = evidence / "SIGNAL_PROCESSING_ABLATIONS.csv"
    assert_hash(base, ref["metrics_sha256"])
    rows = read_csv(base)
    keys = {(r["profile"], r["normalization"], r["duration"], r["endpoint"]) for r in rows}
    if len(rows) != len(keys) or len(rows) != ref["rows"] or ref["test_opened"]:
        raise ValueError("invalid baseline roster")
    for row in rows:
        verify_confusion(row, "recall", "positive_support", "negative_support")

    extra_hash = verify_cross_source(evidence)
    ssl = evidence / "mimic_ssl/SSL_TRAINING_RECEIPT.json"
    if ssl.is_file():
        ssl_data = json.loads(ssl.read_bytes())
        ssl_curves = ssl.with_name("SSL_LEARNING_CURVES.csv")
        assert_hash(ssl_curves, ssl_data["curves_sha256"])
        if (ssl_data["label_files_opened"] or ssl_data["heldout_waveforms_opened"]
                or ssl_data["ecgs"] != ssl_data["patients"] or not HEX.fullmatch(ssl_data["checkpoint_sha256"])
                or any(int(row["ecgs"]) != ssl_data["ecgs"] for row in read_csv(ssl_curves))):
            raise ValueError("masked waveform training receipt is not train-only and patient-consistent")

    experiments, learning, seen, receipts = [], [], set(), {}
    for receipt in sorted(evidence.glob("*/TRAINING_RECEIPT.json")):
        run = json.loads(receipt.read_bytes())
        key = tuple(run[k] for k in RUN_FIELDS[:3])
        curves = receipt.with_name("FINETUNING_LEARNING_CURVES.csv")
        assert_hash(curves, run["curves_sha256"])
        curve_rows = read_csv(curves)
        best = max(curve_rows, key=lambda row: float(row["validation_macro_ap"]))
        if (key in seen or run["calibration_or_test_opened"] or not HEX.fullmatch(run["checkpoint_sha256"])
                or run.get("additional_source_receipt_sha256") not in {None, extra_hash}
                or run["bank_receipt_sha256"] != qc["full_qc_receipt_sha256"] or int(best["epoch"]) != run["best_epoch"]
                or float(best["validation_macro_ap"]) != run["validation_macro_ap"]
                or float(best["validation_macro_f1_at_half"]) != run["validation_macro_f1_at_half"]):
            raise ValueError("invalid training receipt or best-epoch claim")
        seen.add(key)
        receipts[run["checkpoint_sha256"]] = sha(receipt)
        run.setdefault("validation_source", "code15")
        experiments.append({field: run[field] for field in RUN_FIELDS})
        learning.extend({"mode": key[0], "normalization": key[1], "seed": key[2], "slurm_job": run["slurm_job"], **row}
                        for row in curve_rows)
    transfer_path = evidence / "SOURCE_GENERALIZATION_RECEIPT.json"
    if transfer_path.is_file():
        linked = json.loads(transfer_path.read_bytes())["checkpoint_to_training_receipt_sha256"]
        if not linked or any(receipts.get(checkpoint) != receipt for checkpoint, receipt in linked.items()):
            raise ValueError("source-scoring checkpoint lacks a matching public training receipt")

    selection_path = evidence / "CANDIDATE_SELECTION_RECEIPT.json"
    if selection_path.is_file():
        selection = json.loads(selection_path.read_bytes())
        assert_hash(ROOT / "docs/domain_adaptation/SELECTION_PROTOCOL.json", selection["selection_protocol_sha256"])
        if (selection["selection_source"] != "validation_only"
                or receipts.get(selection["selected_checkpoint_sha256"]) != selection["selected_training_receipt_sha256"]):
            raise ValueError("selected checkpoint and validation receipt are not linked")
    if rebuild:
        write_csv(evidence / "TRAINING_EXPERIMENTS_COMPLETE.csv", RUN_FIELDS, experiments)
        if learning:
            write_csv(evidence / "FINETUNING_LEARNING_CURVES.csv", tuple(learning[0]), learning)
        groups = defaultdict(list)
        for run in experiments:
            groups[run["mode"], run["normalization"], run["validation_source"]].append(run)
        ablations = []
        for (mode, norm, source), group in sorted(groups.items()):
            ap = [r["validation_macro_ap"] for r in group]
            f1 = [r["validation_macro_f1_at_half"] for r in group]
            ablations.append({"mode": mode, "normalization": norm, "validation_source": source, "seeds": len(group),
                              "trainable_parameters": group[0]["trainable_parameters"], "macro_ap_mean": mean(ap),
                              "macro_ap_population_sd": pstdev(ap) if len(ap) > 1 else None,
                              "macro_f1_at_half_mean": mean(f1),
                              "macro_f1_at_half_population_sd": pstdev(f1) if len(f1) > 1 else None})
        if ablations:
            write_csv(evidence / "MODEL_ARCHITECTURE_ABLATIONS.csv", tuple(ablations[0]), ablations)
        with (evidence / "CHECKPOINT_SHA256SUMS.txt").open("w", encoding="utf-8", newline="\n") as stream:
            for run in experiments:
                stream.write(f"{run['checkpoint_sha256']}  {run['mode']}-{run['normalization']}-{run['seed']}/best.pt\n")
            if ssl.is_file():
                stream.write(f"{ssl_data['checkpoint_sha256']}  mimic-masked/masked_mimic_backbone.pt\n")

    final = evidence / "WITHIN_CODE_EVALUATION_RECEIPT.json"
    if final.is_file():
        test = json.loads(final.read_bytes())
        assert_hash(selection_path, test["selection_sha256"])
        assert_hash(evidence / "FROZEN_CANDIDATE_THRESHOLDS.json", test["threshold_file_sha256"])
        assert_hash(evidence / "WITHIN_CODE_SCORE_RECEIPT.json", test["score_receipt_sha256"])
        if (test["independent_generalization"] != "NOT_EVALUATED"
                or test["candidate_sha256"] != selection["selected_checkpoint_sha256"]):
            raise ValueError("within-CODE scope cannot certify another institution")
        readback = json.loads((evidence / "WITHIN_CODE_INDEPENDENT_READBACK.json").read_bytes())
        if (readback["status"] != "PASS" or readback["aggregate_receipt_sha256"] != sha(final)
                or readback["score_sha256"] != test["private_prediction_sha256"]
                or readback["ecgs"] != test["test_ecgs"] or readback["patients"] != test["test_patients"]
                or readback["point_comparisons"] <= 0 or readback["macro_ci_endpoint_comparisons"] <= 0
                or not 0 <= readback["max_abs_point_difference"] <= 1e-12
                or not 0 <= readback["max_abs_macro_ci_difference"] <= 1e-12):
            raise ValueError("private-score readback not verified for this evidence package")
        names = {"EXTERNAL_PER_CLASS_RESULTS.csv", "PATIENT_BOOTSTRAP_CONFIDENCE_INTERVALS.csv",
                 "EXTERNAL_MACRO_F1_COMPARISON.csv", "PRECISION_RECALL_CURVES.csv", "CALIBRATION_CURVES.csv",
                 "WITHIN_CODE_PROMOTION_DECISION.json"}
        if set(test["aggregates"]) != names:
            raise ValueError("unexpected public aggregate roster")
        for name, digest in test["aggregates"].items():
            assert_hash(evidence / name, digest)
        by_scope = defaultdict(dict)
        for row in read_csv(evidence / "EXTERNAL_PER_CLASS_RESULTS.csv"):
            if row["estimable"] == "True":
                verify_confusion(row, "sensitivity", "positive_ecgs", "negative_ecgs")
                by_scope[row["duration"], row["model"]][row["endpoint"]] = float(row["f1"])
        for row in read_csv(evidence / "EXTERNAL_MACRO_F1_COMPARISON.csv"):
            observed = by_scope[row["duration"], row["model"]]
            expected = row["endpoints"].split("|") if row["endpoints"] else []
            if (observed.keys() != set(expected) or observed and not math.isclose(
                    sum(observed.values()) / len(observed), float(row["macro_f1"]), abs_tol=1e-12)):
                raise ValueError("macro-F1 does not match all named endpoints")
    return {"baseline_rows": len(rows), "supervised_runs": len(experiments), "curve_rows": len(learning),
            "within_code_results_present": final.is_file()}


def privacy_and_manifest(evidence, rebuild=False):
    paths = {}
    manifest = evidence / "EXPERIMENT_REPRODUCIBILITY_MANIFEST.json"
    for file in sorted(evidence.rglob("*")):
        if file.is_symlink():
            raise ValueError("unexpected public symbolic link")
        if not file.is_file() or file == manifest:
            continue
        if file.suffix not in PUBLIC_TYPES or file.name.startswith("private_"):
            raise ValueError("unapproved public artifact type or name")
        if file.suffix == ".csv" and any(PRIVATE_NAMES.intersection(row) for row in read_csv(file)):
            raise ValueError("unexpected record-level CSV field")
        if file.suffix == ".json":
            def check(item):
                if isinstance(item, dict):
                    if PRIVATE_NAMES.intersection(item):
                        raise ValueError("unexpected record-level JSON field")
                    for value in item.values():
                        check(value)
                elif isinstance(item, list):
                    for value in item:
                        check(value)
            check(json.loads(file.read_bytes()))
        paths[file.relative_to(evidence).as_posix()] = {"sha256": sha(file), "bytes": file.stat().st_size}
    if rebuild:
        manifest.write_bytes((json.dumps({"scope": "PUBLIC_AGGREGATES_ONLY", "files": paths},
                                          sort_keys=True, indent=2) + "\n").encode())
    elif manifest.is_file() and paths != json.loads(manifest.read_bytes())["files"]:
        raise ValueError("public evidence manifest mismatch")
    return len(paths)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    summary = verify(args.evidence, args.rebuild)
    summary["public_files_verified"] = privacy_and_manifest(args.evidence, args.rebuild)
    print(json.dumps(summary, sort_keys=True))
