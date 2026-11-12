"""Fit and compare new mapped rhythm Other heads on sealed SPH scores."""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from compare_reviewer_baseline import digest, load_ledger
from freeze_reviewer_selective_policy import calibration_member, components, jsonl
from reviewer_morphology_retrained import fit_head, polarity, threshold
from reviewer_pathology_other import probabilities, write_new

P8 = ("AFIB", "SB", "STACH", "NSR", "RBBB", "PAC", "1AVB", "PVC")
P6 = tuple(c for c in P8 if c not in {"NSR", "PAC"})
KNOWN = ("positive", "control")


def partition(group, split):
    if calibration_member(group, split["seed"], split["train_fraction"]):
        return "train"
    if calibration_member(group, split["seed"], split["train_or_calibration_fraction"]):
        return "calibration"
    return "held"


def states_for(keys, refs, signals, targets):
    states, by_signal = {}, defaultdict(list)
    for key in keys:
        codes = refs[key].primary_codes
        if 1 in codes:
            states[key] = "control" if codes == {1} else "ambiguous"
        else:
            states[key] = "positive" if codes & targets else "unknown"
        by_signal[signals[key]].append(key)
    for items in by_signal.values():
        distinct = {states[k] for k in items}
        if len(distinct) > 1 and distinct.intersection(KNOWN):
            states.update(dict.fromkeys(items, "discordant_exact_signal"))
    return states


def feature_vector(row):
    p = row["profiles"]
    for profile, expected in (("P6", P6), ("P8", P8)):
        if set(p[profile]["scores"]) != set(expected):
            raise ValueError("published rhythm score class contract differs")
    aux = tuple(f"backbone_{i}" for i in range(6))
    a, b = p["P6"]["auxiliary_scores"], p["P8"]["auxiliary_scores"]
    if a != b or set(b) != set(aux):
        raise ValueError("expected same six frozen V3F auxiliary scores in both profiles")
    vector = [p[profile]["scores"][label] for profile, classes in (("P6", P6), ("P8", P8))
              for label in classes] + [b[k] for k in aux]
    if any(not 0 <= v <= 1 for v in vector):
        raise ValueError("score outside probability range")
    return vector


def matched(keys, states, splits, split):
    ix = np.asarray([i for i, k in enumerate(keys) if splits[k] == split and states[k] in KNOWN], dtype=int)
    return ix, np.asarray([states[keys[i]] == "positive" for i in ix], dtype=np.int8)


def fit_endpoint(x, base, keys, states, splits, policy):
    i, y = matched(keys, states, splits, "train")
    c, cy = matched(keys, states, splits, "calibration")
    result = {"train_controls_positives": [int(len(y) - y.sum()), int(y.sum())],
              "calibration_controls_positives": [int(len(cy) - cy.sum()), int(cy.sum())]}
    if polarity(y) < policy["minimum_training_per_polarity"] or polarity(cy) < policy["minimum_calibration_per_polarity"]:
        return {**result, "status": "insufficient_training_or_calibration_support"}
    model = fit_head(x[i], y, np.ones(len(y)), policy["l2"], policy["max_iterations"])
    if model is None:
        return {**result, "status": "nonconvergent"}
    return {**result, "status": "calibrated", "candidate": model,
            "candidate_threshold": threshold(cy, probabilities(model, x[c])),
            "comparator_threshold": threshold(cy, base[c])}


def evaluate_endpoint(x, base, keys, states, splits, groups, saved, policy, design, metric, intervals, paired):
    scored = set(keys)
    flow = defaultdict(Counter)
    for k, state in states.items():
        flow[splits[k]][f"{state}:{'scored' if k in scored else 'not_scored'}"] += 1
    result = {"status": saved["status"], "all_metadata_reference_scoring_flow": dict(flow)}
    if saved["status"] != "calibrated":
        return result
    held = np.asarray([i for i, k in enumerate(keys) if splits[k] == "held"], dtype=int)
    ix, y = matched(keys, states, splits, "held")
    candidate = probabilities(saved["candidate"], x[held])
    call_arrays = {
        "candidate": (candidate, saved["candidate_threshold"]),
        "released_auxiliary_comparator": (base[held], saved["comparator_threshold"]),
    }
    by_state = {}
    for name, (score, cut) in call_arrays.items():
        by_state[name] = dict(Counter(
            f"{states[keys[i]]}:{'positive' if decision else 'negative'}"
            for i, decision in zip(held, score >= cut, strict=True)))
    result["held_scored_calls_by_reference_state"] = by_state
    if polarity(y) < policy["minimum_held_per_polarity"]:
        return {**result, "status": "insufficient_held_support"}
    group_ids = [groups[keys[i]] for i in ix]
    stats = {"seed": design["seed"], "n_bootstrap": design["replicates"], "confidence": design["confidence"]}
    reports, comparisons = {}, {}
    for name, (score, cut) in call_arrays.items():
        values = score[np.searchsorted(held, ix)]
        calls = values >= cut
        reports[name] = {"calibration_threshold": cut, "metrics": metric(y, values, cut),
                         "intervals": intervals(y, calls, values, group_ids, **stats)}
        comparisons[name] = (calls, values)
    return {**result, "status": "evaluated", "matched_known_held_ecgs": len(ix), "known_statement_metrics": reports,
            "paired_candidate_minus_comparator": paired(
                y, *comparisons["released_auxiliary_comparator"], *comparisons["candidate"], group_ids, **stats)}


def main():
    from specialist_heads import (
        bootstrap_binary_metrics,
        class_metrics,
        paired_bootstrap_metric_differences,
    )
    from titan_v45.data.sph import read_sph_dictionary, read_sph_metadata

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("fit", "evaluate"))
    for n in ("phase", "protocol", "source", "ledger", "receipt", "duplicate-index", "model", "output"):
        p.add_argument(f"--{n}", type=Path, required=True)
    p.add_argument("--expected-model-sha256")
    a = p.parse_args()
    phase, protocol = (json.loads(path.read_bytes()) for path in (a.phase, a.protocol))
    rows, receipt = load_ledger(a.ledger, a.receipt, phase)
    if digest(a.duplicate_index) != receipt["private_duplicate_index_sha256"]:
        raise ValueError("duplicate-index seal mismatch")
    for n in ("metadata.csv", "code.csv"):
        if digest(a.source / n) != receipt["source_sha256"][n]:
            raise ValueError("source seal mismatch")
    primary, modifiers = read_sph_dictionary((a.source / "code.csv").read_text(encoding="utf-8-sig"))
    if any(primary.get(int(k)) != v for k, v in protocol["dictionary"].items()):
        raise ValueError("source label contract differs")
    refs = read_sph_metadata((a.source / "metadata.csv").read_text(encoding="utf-8-sig"), primary, modifiers)
    index = list(jsonl(a.duplicate_index))
    groups = components(index)
    signals = {r["ecg_id"]: r["signal_sha256_canonical_f64"] for r in index}
    if rows.keys() != groups.keys() or rows.keys() != refs.keys() or any(
        r["patient_id"] != refs[r["ecg_id"]].patient for r in index
    ):
        raise ValueError("metadata, ledger and patient/signal index differ")
    components_by_split = {g: partition(g, protocol["split"]) for g in set(groups.values())}
    splits = {k: components_by_split[g] for k, g in groups.items()}
    keys = [k for k, r in rows.items() if r["status"] == "scored" and (a.mode != "fit" or splits[k] != "held")]
    x = np.asarray([feature_vector(rows[k]) for k in keys], dtype=float)
    chosen = [k for k in rows if a.mode != "fit" or splits[k] != "held"]
    binding = {"protocol_sha256": digest(a.protocol), "scoring_receipt_sha256": digest(a.receipt),
               "private_duplicate_index_sha256": receipt["private_duplicate_index_sha256"]}
    report = {"scope": protocol["scope"], "binding": binding, "job": os.environ.get("SLURM_JOB_ID"),
              "split_ecgs": dict(Counter(splits.values())), "split_components": dict(Counter(components_by_split.values())),
              "cross_split_patient_or_exact_signal_components": 0,
              "unique_ecgs": len(refs), "unique_patients": len({r.patient for r in refs.values()}),
              "record_identifiers_exported": False, "non_evaluable": protocol["non_evaluable"]}
    if a.mode == "evaluate":
        if not a.expected_model_sha256 or digest(a.model) != a.expected_model_sha256:
            raise ValueError("unsealed head checkpoint")
        saved = json.loads(a.model.read_bytes())
        if saved["binding"] != binding or saved["endpoints"].keys() != protocol["endpoints"].keys():
            raise ValueError("checkpoint inputs changed")
    endpoints = {}
    for name, spec in protocol["endpoints"].items():
        states = states_for(chosen, refs, signals, set(spec["codes"]))
        base = x[:, [len(P6) + len(P8) + i for i in spec["auxiliary"]]].max(axis=1)
        if a.mode == "fit":
            endpoints[name] = fit_endpoint(x, base, keys, states, splits, protocol["training"])
        else:
            endpoints[name] = evaluate_endpoint(
                x, base, keys, states, splits, groups, saved["endpoints"][name], protocol["training"],
                protocol["statistics"], class_metrics, bootstrap_binary_metrics, paired_bootstrap_metric_differences)
    if a.mode == "fit":
        write_new(a.model, {"binding": binding, "endpoints": endpoints})
        report["endpoint_status"] = {name: value["status"] for name, value in endpoints.items()}
    else:
        report.update({"endpoints": endpoints, "candidate": protocol["candidate"], "comparator": protocol["comparator"]})
    report.update({"held_outcomes_evaluated": a.mode == "evaluate", "private_model_sha256": digest(a.model)})
    write_new(a.output, report)


if __name__ == "__main__":
    main()
