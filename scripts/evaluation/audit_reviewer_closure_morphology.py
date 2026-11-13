"""Re-derive the sealed morphology effect and test paired robustness without training."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

import numpy as np
from compare_reviewer_baseline import digest
from reviewer_morphology_retrained import (
    ARMS,
    load_features,
    paired_macro,
    record_scores,
    select_profiles,
    selected,
)
from score_reviewer_closure_ludb import write_new


def paired_counts(trials, groups):
    relevant = np.unique(np.concatenate([x[0] for x in trials]))
    _, inverse = np.unique(np.asarray(groups)[relevant], return_inverse=True)
    n = int(inverse.max()) + 1
    table = np.zeros((n, len(trials), 2, 3), dtype=np.int64)
    for index, (ids, truth, *calls) in enumerate(trials):
        cluster = inverse[np.searchsorted(relevant, ids)]
        for arm, call in enumerate(calls):
            for cell, condition in enumerate(((truth == 1) & (call == 1),
                                              (truth == 0) & (call == 1),
                                              (truth == 1) & (call == 0))):
                table[:, index, arm, cell] = np.bincount(cluster[condition], minlength=n)
    return table


def macro_f1(cells):
    tp, fp, fn = np.moveaxis(cells, -1, 0)
    den = 2 * tp + fp + fn
    if np.any(den == 0):
        raise ValueError("permutation metric lacks support")
    return (2 * tp / den).mean(axis=-1)


def arm_swap(table, count, seed):
    observed = table.sum(axis=0)
    point = float(macro_f1(observed[:, 0, :]) - macro_f1(observed[:, 1, :]))
    pool = observed.sum(axis=1)
    delta = (table[:, :, 0, :] - table[:, :, 1, :]).reshape(len(table), -1).astype(float)
    rng = np.random.default_rng(seed)
    hits = 0
    for start in range(0, count, 128):
        size = min(128, count - start)
        swaps = rng.choice((-1., 1.), size=(size, len(table)))
        signed = (swaps @ delta).reshape(size, *pool.shape)
        stat = macro_f1((pool + signed) / 2) - macro_f1((pool - signed) / 2)
        hits += int(np.sum(np.abs(stat) >= abs(point) - 1e-12))
    return {
        "observed_delta_macro_f1": point, "exchangeability_units": len(table),
        "absolute_null_extremes": hits, "permutations": count,
        "two_sided_monte_carlo_p": (1 + hits) / (count + 1),
    }


def holm(p_values):
    ordered = sorted(p_values, key=p_values.get)
    previous, adjusted = 0.0, {}
    for index, key in enumerate(ordered):
        previous = max(previous, min(1.0, (len(ordered) - index) * p_values[key]))
        adjusted[key] = previous
    return adjusted


def verify_bootstrap(current, prior):
    if (current["valid_replicates"], current["invalid_replicates"]) != (
        prior["valid_replicates"], prior["invalid_replicates"]
    ) or not math.isclose(current["with_minus_without"], prior["with_minus_without"], abs_tol=1e-12):
        raise ValueError("original paired point or resampling counts do not rederive")
    if not np.allclose(current["bounds"], prior["bounds"], atol=1e-12, rtol=0):
        raise ValueError("original paired percentile interval does not rederive")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("robustness", "original-protocol", "prior-aggregate", "model", "features", "inventory", "output"):
        p.add_argument(f"--{name}", type=Path, required=True)
    a = p.parse_args()
    config = json.loads(a.robustness.read_bytes())
    if digest(a.prior_aggregate) != config["evaluation_aggregate_sha256"] or digest(a.model) != config["model_sha256"]:
        raise ValueError("prior result or fitted model digest differs")
    original = json.loads(a.prior_aggregate.read_bytes())
    saved = json.loads(a.model.read_bytes())
    proto, arrays, meta, signals, extraction = load_features(a.original_protocol, a.features, a.inventory)
    binding = {"protocol_sha256": digest(a.original_protocol), "extraction_receipt_sha256": extraction,
               "inventory_sha256": digest(a.inventory)}
    if saved["binding"] != binding or original["binding"] != binding:
        raise ValueError("held input lineage differs")
    result = {}
    for profile, rows, wi, labels, columns, xs, splits, counts in select_profiles(proto, arrays, meta, signals):
        if counts != original["profiles"][profile]["split_counts"]:
            raise ValueError("held split does not match the original evaluation")
        prior = original["profiles"][profile]
        groups = [r["group_hash"] or r["identity_hash"] for r in rows]
        trials = []
        for label, col in zip(labels, columns, strict=True):
            endpoint = prior["endpoints"][label]
            if endpoint["status"] != "evaluated":
                continue
            ids = selected(rows, splits, "held", col)
            truth = np.array([rows[i]["targets"][col] for i in ids], dtype=np.int8)
            endpoint_models = saved["profiles"][profile]["endpoints"][label]["models"]
            calls = []
            for arm in ARMS:
                model = endpoint_models[arm]
                scores = record_scores(model, xs[arm], wi, ids, profile)
                call = (scores >= model["threshold"]).astype(np.int8)
                table = np.bincount(2 * truth + call, minlength=4)
                if table.tolist() != [endpoint["metrics"][arm][k] for k in ("tn", "fp", "fn", "tp")]:
                    raise ValueError("sealed held confusion table did not rederive")
                calls.append(call)
            trials.append((ids, truth, *calls))
        rebuilt = paired_macro(trials, groups, proto["statistics"])
        verify_bootstrap(rebuilt, prior["paired_endpoint_macro_f1"])
        diagnostic = arm_swap(paired_counts(trials, groups), config["permutations"], config["seed"])
        if not math.isclose(diagnostic["observed_delta_macro_f1"], rebuilt["with_minus_without"], abs_tol=1e-12):
            raise ValueError("sensitivity statistic differs from the original estimand")
        result[profile] = {"evaluated_endpoints": len(trials), "original_bootstrap_rederived": rebuilt, **diagnostic}
    if list(result) != config["profiles"]:
        raise ValueError("post hoc profile family differs from frozen config")
    adjusted = holm({key: r["two_sided_monte_carlo_p"] for key, r in result.items()})
    for key, value in adjusted.items():
        result[key]["holm_adjusted_p"] = value
    write_new(a.output, {
        "schema": config["schema"], "job": os.environ.get("SLURM_JOB_ID"), "scope": config["scope"],
        "analysis_contract": config["statistic"], "interpretation_limit": config["inference"],
        "config_sha256": digest(a.robustness), "original_aggregate_sha256": digest(a.prior_aggregate),
        "original_model_sha256": digest(a.model), "binding": binding, "profiles": result,
        "fit_or_feature_extraction_performed": False, "no_individual_records_exported": True,
    })


if __name__ == "__main__":
    main()
