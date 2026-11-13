"""Fit and evaluate identical masked logistic heads on paired morphology features."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

import numpy as np
from compare_reviewer_baseline import digest
from scipy.optimize import minimize
from scipy.special import expit

ARMS = ("with_morphology", "without_morphology")
P6 = ("AFIB", "SB", "STACH", "RBBB", "1AVB", "PVC")


def assign(record, profile, protocol):
    if profile == "P4":
        fold = int(record["fold"])
        if fold == 10:
            raise ValueError("forbidden fold 10")
        if not record["group_hash"]:
            raise ValueError("P4 patient key is missing")
        if 1 <= fold <= 7 and record["split"] == "train":
            return "train"
        if fold == 8 and record["split"] == "validation":
            return "unused"
        if fold == 9 and record["split"] in {"calibration", "internal_evaluation"}:
            return "calibration" if record["split"] == "calibration" else "held"
        raise ValueError("inconsistent P4 fold/split")
    if record["source"] != "chapman_shaoxing":
        return "unused"
    recipe = protocol["rhythm_split"]
    group = record["group_hash"]
    if not group:
        raise ValueError("Chapman record-as-patient proxy missing")
    token = json.dumps([recipe["seed"], group], separators=(",", ":")).encode()
    fraction = int.from_bytes(hashlib.sha256(token).digest()[:8], "big") / 2**64
    if fraction < recipe["train_cut"]:
        return "train"
    return "calibration" if fraction < recipe["calibration_cut"] else "held"


def audit_split(records, splits, signals):
    ownership = {}
    for row, split in zip(records, splits, strict=True):
        if split == "unused":
            continue
        for kind, value in (("group", row["group_hash"]), ("signal", signals[row["identity_hash"]])):
            if not value or ownership.setdefault((kind, value), split) != split:
                raise ValueError("missing grouping key or group/signal overlap")
    return dict(Counter(splits))


def fit_head(x, y, w, l2, iterations):
    total = w.sum()
    w = w / total
    mean = w @ x
    scale = np.sqrt(w @ (x-mean)**2)
    scale = np.where(scale > 1e-8, scale, 1.0)
    z = (x-mean)/scale

    def loss(parameters):
        coef, intercept = parameters[:-1], parameters[-1]
        logits = z @ coef + intercept
        obj = w @ (np.logaddexp(0, logits) - y*logits) + l2/2 * (coef @ coef)
        error = w * (expit(logits)-y)
        return obj, np.r_[z.T @ error + l2*coef, error.sum()]

    result = minimize(loss, np.zeros(x.shape[1]+1), method="L-BFGS-B", jac=True,
                      options={"maxiter": iterations, "ftol": 1e-10, "gtol": 1e-6})
    if not result.success or not np.isfinite(result.x).all():
        return None
    return {"mean": mean.tolist(), "scale": scale.tolist(), "parameters": result.x.tolist(),
            "iterations": int(result.nit)}


def record_scores(model, x, wi, record_ids, profile):
    select = np.isin(wi, record_ids)
    idx = np.searchsorted(record_ids, wi[select])
    w = np.asarray(model["parameters"])
    values = ((x[select]-model["mean"])/model["scale"]) @ w[:-1] + w[-1]
    counts = np.bincount(idx, minlength=len(record_ids))
    if not len(counts) or np.any(counts == 0):
        raise ValueError("selected scored ECG lacks a feature window")
    if profile != "P6":
        values = expit(values)
    output = np.bincount(idx, weights=values, minlength=len(counts))/counts
    return expit(output) if profile == "P6" else output


def threshold(y, scores):
    order = np.argsort(-scores, kind="stable")
    s = scores[order]
    ends = np.r_[np.flatnonzero(np.diff(s)), len(s)-1]
    tp = np.cumsum(y[order])[ends]
    # Candidates are in descending order, so argmax deterministically keeps the highest tie.
    return float(s[ends[np.argmax(2*tp/(y.sum()+ends+1))]])


def load_features(protocol_path, root, inventory_path):
    proto = json.loads(protocol_path.read_bytes())
    receipt_path = root / "extraction-receipt.json"
    receipt = json.loads(receipt_path.read_bytes())
    if (receipt["protocol_sha256"] != digest(protocol_path)
            or receipt["source_commit"] != proto["upstream_feature_commit"]
            or receipt["performance_metrics_computed"] is not False):
        raise ValueError("wrong extraction receipt")
    arrays, metadatas = {}, {}
    inventory_hash = digest(inventory_path)
    inventory = json.loads(inventory_path.read_bytes())
    for arm in ARMS:
        directory = root / arm
        meta_path = directory / "private_feature_metadata.json"
        cache = directory / "private_frozen_features.npz"
        seal = receipt["arms"][arm]
        if digest(meta_path) != seal["metadata_sha256"] or digest(cache) != seal["feature_sha256"]:
            raise ValueError("feature cache seal mismatch")
        m = json.loads(meta_path.read_bytes())
        if (m["private_inventory_sha256"] != inventory_hash
                or m["baseline_asset_hashes"] != seal["asset_hashes"]
                or m["git_commit"] != proto["upstream_feature_commit"]
                or m["performance_metrics_computed"] is not False):
            raise ValueError("feature metadata provenance mismatch")
        arrays[arm] = np.load(cache, allow_pickle=False)
        metadatas[arm] = m
    a, b = (metadatas[k] for k in ARMS)
    for key in ("rhythm_records", "pathology_records", "baseline_asset_hashes", "baseline_thresholds"):
        if a[key] != b[key]:
            raise ValueError("arm inventory or release configuration differs")
    signals = {r["identity_hash"]: r["signal_sha256"] for r in inventory["rows"]
               if not r["excluded_reason"]}
    return proto, arrays, a, signals, digest(receipt_path)


def select_profiles(protocol, arrays, meta, signals):
    for profile in protocol["profiles"]:
        rhythm = profile != "P4"
        rows = meta["rhythm_records" if rhythm else "pathology_records"]
        index = "rhythm_record_index" if rhythm else "p4_record_index"
        wi = arrays[ARMS[0]][index]
        if not np.array_equal(wi, arrays[ARMS[1]][index]):
            raise ValueError("arms differ in feature window membership/order")
        classes = tuple(rows[0]["classes"])
        if any(tuple(r["classes"]) != classes for r in rows):
            raise ValueError("class order differs by ECG")
        labels = P6 if profile == "P6" else classes
        x = {arm: arrays[arm][profile.lower()+"_features"].astype(np.float64) for arm in ARMS}
        if x[ARMS[0]].shape != x[ARMS[1]].shape or any(
            len(a) != len(wi) or not np.isfinite(a).all() for a in x.values()
        ):
            raise ValueError("feature contract or finiteness differs")
        splits = [assign(row, profile, protocol) for row in rows]
        counts = audit_split(rows, splits, signals)
        yield profile, rows, wi, labels, [classes.index(c) for c in labels], x, splits, counts


def selected(rows, splits, name, col):
    return np.array([i for i, row in enumerate(rows)
                     if splits[i] == name and row["scored"] and row["mask"][col]], dtype=np.int32)


def polarity(y):
    if not np.isin(y, (0, 1)).all():
        raise ValueError("observed reference is not binary")
    return min(int(y.sum()), int(len(y)-y.sum()))


def fit(protocol, profiles):
    recipe = protocol["training"]
    output = {}
    for p, rows, wi, labels, columns, xs, splits, counts in profiles:
        results = {}
        for label, col in zip(labels, columns, strict=True):
            train = selected(rows, splits, "train", col)
            cal = selected(rows, splits, "calibration", col)
            ty, cy = (np.array([rows[i]["targets"][col] for i in ids], dtype=np.int8) for ids in (train, cal))
            if (polarity(ty) < recipe["minimum_training_records_per_polarity"]
                    or polarity(cy) < recipe["minimum_calibration_records_per_polarity"]):
                results[label] = {"status": "insufficient_train_or_calibration_support"}
                continue
            mask = np.isin(wi, train)
            row_positions = np.searchsorted(train, wi[mask])
            per_record_counts = np.bincount(row_positions, minlength=len(train))
            if np.any(per_record_counts == 0):
                raise ValueError("missing training windows")
            weights = 1 / per_record_counts[row_positions]
            arm_models = {
                arm: fit_head(x[mask], ty[row_positions], weights, recipe["l2"], recipe["max_iterations"])
                for arm, x in xs.items()
            }
            if any(model is None for model in arm_models.values()):
                results[label] = {"status": "nonconvergence_in_at_least_one_arm"}
                continue
            for arm, model in arm_models.items():
                model["threshold"] = threshold(cy, record_scores(model, xs[arm], wi, cal, p))
            results[label] = {"status": "calibrated", "train_n": len(train), "calibration_n": len(cal),
                              "models": arm_models}
        output[p] = {"split_counts": counts, "endpoints": results}
    return output


def paired_macro(trials, groups, design):
    if not trials:
        return None
    selected_ids = np.unique(np.concatenate([ids for ids, *_ in trials]))
    groups = [groups[i] for i in selected_ids]
    trials = [(np.searchsorted(selected_ids, ids), y, a, b) for ids, y, a, b in trials]
    _, inverse = np.unique(groups, return_inverse=True)
    n = len(set(groups))
    rng = np.random.default_rng(design["seed"])

    def macro_delta(w):
        values = []
        for ids, y, a, b in trials:
            v = w[ids]
            if not v[y == 1].sum() or not v[y == 0].sum():
                return None
            scores = []
            for decisions in (a, b):
                _, fp, fn, tp = np.bincount(2*y+decisions, weights=v, minlength=4)
                scores.append(2*tp/(2*tp+fp+fn))
            values.append(scores[0]-scores[1])
        return float(np.mean(values))

    point = macro_delta(np.ones(len(groups)))
    samples = []
    for _ in range(design["replicates"]):
        w = np.bincount(rng.integers(n, size=n), minlength=n)[inverse]
        v = macro_delta(w)
        if v is not None:
            samples.append(v)
    alpha = (1-design["level"])/2
    return {"with_minus_without": point, "bounds": np.quantile(samples, [alpha, 1-alpha]).tolist() if samples else None,
            "valid_replicates": len(samples), "invalid_replicates": design["replicates"]-len(samples)}


def released_decisions(profile, arrays, wi, ids, labels, thresholds):
    selected = np.isin(wi, ids)
    ix = np.searchsorted(ids, wi[selected])
    counts = np.bincount(ix, minlength=len(ids))
    if np.any(counts == 0):
        raise ValueError("released baseline missing held score")
    ordered_thresholds = {label: thresholds[label] for label in labels}
    order = np.argsort(ix, kind="stable")
    if profile == "P4":
        scores = arrays["p4_baseline_scores"][selected][order]
        if not np.all(counts == 1) or scores.shape != (len(ids), len(labels)):
            raise ValueError("released P4 score contract differs from the held ECGs")
        return scores, scores >= list(ordered_thresholds.values())

    from titan_v45.models.frozen_rhythm import aggregate_rhythm

    # Both released rhythm heads emit eight logits, including the P6 checkpoint.
    logits = arrays[profile.lower()+"_baseline_logits"][selected][order]
    scores, calls = [], []
    for group in np.split(logits, np.cumsum(counts)[:-1]):
        result = aggregate_rhythm(group, ordered_thresholds, profile=profile)
        scores.append([result["scores"][label] for label in labels])
        calls.append([label in result["labels"] for label in labels])
    return np.asarray(scores), np.asarray(calls)


def evaluate(protocol, profiles, models, arrays, released_thresholds, metric, paired_intervals):
    results = {}
    design = protocol["statistics"]
    for p, rows, wi, labels, columns, xs, splits, counts in profiles:
        if counts != models[p]["split_counts"]:
            raise ValueError("split changed since fit")
        groups = [r["group_hash"] or r["identity_hash"] for r in rows]
        endpoints, trials = {}, []
        for position, (label, col) in enumerate(zip(labels, columns, strict=True)):
            prior = models[p]["endpoints"][label]
            ids = selected(rows, splits, "held", col)
            y = np.array([rows[i]["targets"][col] for i in ids], dtype=np.int8)
            if prior["status"] != "calibrated" or polarity(y) == 0:
                endpoints[label] = {"status": prior["status"] if prior["status"] != "calibrated"
                                    else "insufficient_held_support", "held_known_n": len(ids)}
                continue
            scores, decisions, metrics = {}, {}, {}
            for arm in ARMS:
                model = prior["models"][arm]
                s = record_scores(model, xs[arm], wi, ids, p)
                scores[arm], decisions[arm] = s, (s >= model["threshold"]).astype(np.int8)
                metrics[arm] = metric(y, decisions[arm], s)
            baseline, calls = released_decisions(p, arrays, wi, ids, labels, released_thresholds[p])
            metrics["released_baseline"] = metric(y, calls[:, position], baseline[:, position])
            a, b = ARMS
            trials.append((ids, y, decisions[a], decisions[b]))
            endpoints[label] = {
                "status": "evaluated", "held_known_n": len(ids), "metrics": metrics,
                "paired_intervals_with_minus_without": paired_intervals(
                    y, decisions[b], scores[b], decisions[a], scores[a], [groups[i] for i in ids],
                    seed=design["seed"], n_bootstrap=design["replicates"],
                ),
            }
        evaluated = [x["metrics"] for x in endpoints.values() if x["status"] == "evaluated"]
        results[p] = {"split_counts": counts, "endpoints": endpoints,
                      "macro_f1_on_common_supported_endpoints": {
                          arm: float(np.mean([e[arm]["f1"] for e in evaluated])) if evaluated else None
                          for arm in (*ARMS, "released_baseline")
                      },
                      "paired_endpoint_macro_f1": paired_macro(trials, groups, design)}
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("fit", "evaluate"))
    for name in ("protocol", "features", "inventory", "model", "output"):
        p.add_argument(f"--{name}", type=Path, required=True)
    p.add_argument("--expected-model-sha256")
    a = p.parse_args()
    proto, arrays, meta, signals, extraction_sha = load_features(a.protocol, a.features, a.inventory)
    profiles = select_profiles(proto, arrays, meta, signals)
    binding = {"protocol_sha256": digest(a.protocol), "extraction_receipt_sha256": extraction_sha,
               "inventory_sha256": digest(a.inventory)}
    if a.mode == "fit":
        fitted = fit(proto, profiles)
        with a.model.open("x", encoding="utf-8") as stream:
            json.dump({"binding": binding, "profiles": fitted}, stream, allow_nan=False)
        output = {"binding": binding, "model_sha256": digest(a.model), "held_outcomes_evaluated": False,
                  "profiles": {name: {"split_counts": val["split_counts"],
                                      "endpoint_status": {k: v["status"] for k,v in val["endpoints"].items()}}
                               for name, val in fitted.items()}}
    else:
        if not a.expected_model_sha256 or digest(a.model) != a.expected_model_sha256:
            raise ValueError("model is not sealed")
        saved = json.loads(a.model.read_bytes())
        if saved["binding"] != binding:
            raise ValueError("model inputs changed after fit")
        from titan_v45.evaluation.revision_report import binary_metrics
        from titan_v45.evaluation.specialist_heads import paired_bootstrap_metric_differences
        output = {"binding": binding, "model_sha256": a.expected_model_sha256,
                  "scope": proto["scope"], "bootstrap": proto["statistics"],
                  "profiles": evaluate(proto, profiles, saved["profiles"], arrays[ARMS[0]],
                                       meta["baseline_thresholds"], binary_metrics,
                                       paired_bootstrap_metric_differences)}
    output.update({"job": os.environ.get("SLURM_JOB_ID"), "identifiers_exported": False})
    with a.output.open("x", encoding="utf-8") as stream:
        json.dump(output, stream, indent=2, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
