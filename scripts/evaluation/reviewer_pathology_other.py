"""Fit separate auxiliary and bounded Other heads using sealed Stage A P4 features."""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import os
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

import numpy as np
from compare_reviewer_baseline import digest
from reviewer_morphology_retrained import assign, audit_split, fit_head, polarity, threshold
from scipy.special import expit


def reference(codes, targets):
    present = codes.keys() & targets
    if present:
        if "NORM" in codes or not any(codes[c] > 0 for c in present):
            return "ambiguous"
        return "positive"
    if codes.get("NORM", 0) > 0 and codes.keys() <= {"NORM", "SR"}:
        return "control"
    return "unknown"


def identity(namespace, value):
    return hashlib.sha256(f"{namespace}\0{value}".encode()).hexdigest()


def read_references(path, metadata_count):
    refs, groups, folds = {}, {}, {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        row_count, reserved_rows = 0, 0
        for row in csv.DictReader(stream):
            row_count += 1
            fold = int(row["strat_fold"])
            if fold == 10:
                reserved_rows += 1
                continue
            if fold not in range(1, 10):
                raise ValueError("unexpected fold")
            key = identity("ptbxl", row["filename_lr"])
            patient_number = Decimal(row["patient_id"])
            if not patient_number.is_finite() or patient_number != patient_number.to_integral_value():
                raise ValueError("invalid patient identifier")
            patient = identity("ptbxl_patient", str(int(patient_number)))
            if key in refs or folds.setdefault(patient, fold) != fold:
                raise ValueError("duplicate reference or patient across official folds")
            codes = ast.literal_eval(row["scp_codes"])
            if not isinstance(codes, dict) or any(
                not isinstance(c, str) or not math.isfinite(v) or not 0 <= v <= 100
                for c, v in codes.items()
            ):
                raise ValueError("invalid SCP likelihoods")
            refs[key], groups[key] = codes, (fold, patient)
    if row_count != metadata_count or reserved_rows != row_count - len(refs):
        raise ValueError("reference denominator changed")
    return refs, groups, reserved_rows


def load_inputs(a, protocol):
    meta = json.loads((a.features / "private_feature_metadata.json").read_bytes())
    preflight_path = a.preflight / "preflight_receipt.json"
    preflight = json.loads(preflight_path.read_bytes())
    inventory_path = a.preflight / "private_inventory.json"
    cache = a.features / "private_frozen_features.npz"
    meta_path, dict_path = (a.source / name for name in ("ptbxl_database.csv", "scp_statements.csv"))
    for path, field, recorded in (
        (meta_path, "metadata_sha256", preflight["ptbxl"]["metadata_sha256"]),
        (dict_path, "dictionary_sha256", preflight["ptbxl"]["scp_statements_sha256"]),
        (cache, "feature_cache_sha256", meta["feature_cache_sha256"]),
        (preflight_path, "preflight_sha256", meta["preflight_receipt_sha256"]),
        (inventory_path, "inventory_sha256", meta["private_inventory_sha256"]),
    ):
        if path.is_symlink() or digest(path) != protocol[field] or recorded != protocol[field]:
            raise ValueError(f"input receipt mismatch: {field}")
    if (meta["git_commit"] != protocol["feature_commit"] or meta["performance_metrics_computed"]
            or preflight["ptbxl"]["fold10_accessed"] or preflight["fold10_used"]):
        raise ValueError("invalid extraction lineage")
    with dict_path.open(encoding="utf-8-sig", newline="") as stream:
        dictionary = {row[""]: row["description"] for row in csv.DictReader(stream)}
    if any(dictionary.get(k) != v for k, v in protocol["dictionary"].items()):
        raise ValueError("source statement description mismatch")
    refs, groups, reserved = read_references(
        meta_path, preflight["ptbxl"]["metadata_records_total_including_untouched_fold10"])
    inventory = json.loads(inventory_path.read_bytes())
    active = {r["identity_hash"]: r for r in inventory["rows"]
              if r["task"] == "pathology" and not r["excluded_reason"]}
    rows = meta["pathology_records"]
    if len(rows) != len(active) or {r["identity_hash"] for r in rows} != active.keys():
        raise ValueError("P4 feature inventory does not reconcile")
    for r in rows:
        k = r["identity_hash"]
        if groups.get(k) != (r["fold"], r["group_hash"]) or r["split"] != active[k]["split"]:
            raise ValueError("feature/reference identity or split mismatch")
    splits = [assign(r, "P4", {}) for r in rows]
    audit = audit_split(rows, splits, {k: r["signal_sha256"] for k, r in active.items()})
    with np.load(cache, allow_pickle=False) as arrays:
        wi, features = arrays["p4_record_index"], arrays["p4_features"].astype(np.float64)
    expected = np.flatnonzero([r["scored"] for r in rows])
    if (not np.array_equal(wi, expected) or features.shape != (len(wi), 670)
            or not np.isfinite(features).all()):
        raise ValueError("invalid one-window P4 feature contract")
    keys = [rows[i]["identity_hash"] for i in wi]
    counts = {"metadata_ecgs_folds_1_to_9": len(refs), "metadata_patients_folds_1_to_9": len({g for _, g in groups.values()}),
              "reserved_fold10_metadata_rows_count_only": reserved, "active_inventory_ecgs": len(rows),
              "scored_ecgs": len(wi), "active_by_split": audit, "cross_split_exact_signal_or_patient_overlap": 0}
    populations = {r["identity_hash"]: (split, r["scored"]) for r, split in zip(rows, splits, strict=True)}
    return refs, groups, populations, features, keys, counts


def probabilities(model, features):
    params = np.asarray(model["parameters"])
    return expit(((features - model["mean"]) / model["scale"]) @ params[:-1] + params[-1])


def matched_positions(keys, populations, states, split):
    ids = [i for i, k in enumerate(keys)
           if populations[k][0] == split and states[k] in {"positive", "control"}]
    return np.asarray(ids, dtype=int), np.asarray([states[keys[i]] == "positive" for i in ids], dtype=np.int8)


def endpoint_fit(x, keys, populations, states, recipe):
    i, y = matched_positions(keys, populations, states, "train")
    c, cy = matched_positions(keys, populations, states, "calibration")
    if (polarity(y) < recipe["minimum_training_per_polarity"]
            or polarity(cy) < recipe["minimum_calibration_per_polarity"]):
        return {"status": "insufficient_training_or_calibration_support"}
    model = fit_head(x[i], y, np.ones(len(y)), recipe["l2"], recipe["max_iterations"])
    if model is None:
        return {"status": "nonconvergent"}
    model["threshold"] = threshold(cy, probabilities(model, x[c]))
    return {"status": "calibrated", "model": model}


def endpoint_evaluate(x, keys, groups, populations, states, saved, protocol, metrics, bootstrap):
    flow = defaultdict(Counter)
    for key, state in states.items():
        split, scored = populations.get(key, ("outside_active_inventory", False))
        flow[split][f"{state}:{'scored' if scored else 'not_scored'}"] += 1
    out = {"status": saved["status"], "all_source_reference_and_scoring_flow": dict(flow)}
    if saved["status"] != "calibrated":
        return out
    held = np.asarray([i for i, k in enumerate(keys) if populations[k][0] == "held"], dtype=int)
    model = saved["model"]
    predictions = probabilities(model, x[held]) >= model["threshold"]
    out["held_calls_by_reference_state"] = dict(Counter(
        f"{states[keys[i]]}:{'positive' if p else 'negative'}" for i, p in zip(held, predictions, strict=True)))
    j, y = matched_positions(keys, populations, states, "held")
    if polarity(y) < protocol["training"]["minimum_held_per_polarity"]:
        out["status"] = "insufficient_held_support"
        return out
    scores = probabilities(model, x[j])
    out.update({"status": "evaluated", "threshold": model["threshold"],
                "known_statement_subset_metrics": metrics(y, scores, model["threshold"]),
                "known_statement_subset_intervals": bootstrap(
                    y, scores >= model["threshold"], scores, [groups[keys[i]][1] for i in j],
                    seed=protocol["statistics"]["seed"], n_bootstrap=protocol["statistics"]["replicates"],
                    confidence=protocol["statistics"]["confidence"])})
    return out


def write_new(path, content):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(content, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("fit", "evaluate"))
    for name in ("protocol", "source", "features", "preflight", "model", "output"):
        p.add_argument(f"--{name}", type=Path, required=True)
    p.add_argument("--expected-model-sha256")
    a = p.parse_args()
    protocol = json.loads(a.protocol.read_bytes())
    refs, groups, populations, x, keys, counts = load_inputs(a, protocol)
    binding = {"protocol_sha256": digest(a.protocol), "feature_metadata_sha256": digest(
        a.features / "private_feature_metadata.json")}
    endpoints = protocol["endpoints"]
    out = {"scope": protocol["scope"], "binding": binding, "job": os.environ.get("SLURM_JOB_ID"),
           "population": counts, "clinical_or_independent_validation": False, "record_identifiers_exported": False}
    if a.mode == "fit":
        # Do not compute reference states from held outcomes before sealing coefficients and thresholds.
        selected = (k for k in populations if populations[k][0] in {"train", "calibration"})
        training_refs = {k: refs[k] for k in selected}
        models = {
            name: endpoint_fit(x, keys, populations, {k: reference(v, set(codes)) for k, v in training_refs.items()},
                               protocol["training"])
            for name, codes in endpoints.items()
        }
        write_new(a.model, {"binding": binding, "endpoints": models})
        out.update({"held_outcomes_evaluated": False, "private_model_sha256": digest(a.model),
                    "endpoint_status": {name: model["status"] for name, model in models.items()}})
    else:
        from titan_v45.evaluation.specialist_heads import bootstrap_binary_metrics, class_metrics

        if not a.expected_model_sha256 or digest(a.model) != a.expected_model_sha256:
            raise ValueError("unsealed model")
        saved = json.loads(a.model.read_bytes())
        if saved["binding"] != binding or saved["endpoints"].keys() != endpoints.keys():
            raise ValueError("model input binding differs")
        out.update({"private_model_sha256": a.expected_model_sha256, "held_outcomes_evaluated": True,
                    "released_p4_has_no_matching_specialist_head_for_these_endpoints": True,
                    "endpoints": {name: endpoint_evaluate(
                        x, keys, groups, populations, {k: reference(v, set(codes)) for k, v in refs.items()},
                        saved["endpoints"][name], protocol, class_metrics, bootstrap_binary_metrics)
                        for name, codes in endpoints.items()}})
    write_new(a.output, out)


if __name__ == "__main__":
    main()
