"""Join LUDB references only after verifying immutable score and route seals."""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from compare_reviewer_baseline import digest
from freeze_reviewer_selective_policy import components, jsonl
from score_reviewer_closure_ludb import (
    ARCHIVE_SHA256,
    PREFIX,
    PROFILES,
    PROTOCOL_SHA256,
    route,
    sha256,
    source_manifest,
    write_new,
)

POSITIVE_PATTERNS = {
    "RBBB": ("Conduction abnormalities", r"complete right bundle branch block"),
    "LBBB": ("Conduction abnormalities", r"complete left bundle branch block"),
    "1AVB": ("Conduction abnormalities", r"(?:i|first)[ -]degree av[ -]block"),
    "2AVB": ("Conduction abnormalities", r"(?:ii|second)[ -]degree av[ -]block"),
    "3AVB": ("Conduction abnormalities", r"(?:(?:iii|third)[ -]degree|complete) av[ -]block"),
    "PAC": ("Extrasystolies", r"(?:atrial extrasystoles?|single pac)"),
    "PVC": ("Extrasystolies", r"(?:ventricular extrasystoles?|single pvc|intercalary pvc)"),
    "Paced": ("Cardiac pacing", r"(?:(?:unipolar|bipolar) (?:atrial|ventricular)|biventricular) pacing"),
    "LVH": ("Hypertrophies", r"left ventricular hypertrophy"),
}
OTHER_MEMBERS = {
    "P6_Other_mapped": ("PAC", "Flutter", "LBBB", "2AVB", "3AVB"),
    "P8_Other_mapped": ("Flutter", "LBBB", "2AVB", "3AVB"),
    "Other_pathology_unvalidated": ("ALMI", "ILMI", "LAE"),
}
AUX_RHYTHM = {"Flutter": 0, "LBBB": 1, "2AVB": 2, "3AVB": 3, "LQTS": 4, "Paced": 5}
ROUTES = ("accepted", "abstained", "technical_unscored")
KNOWN = {"positive": 1, "negative": 0}
SPH_OTHER_MODEL_SHA256 = "ae8fab7cb5b54a89c38a7e21f99f8b1da10f5cc7d02fa3702283efd73ba129ba"
PUBLISHER_POSITIVE_COUNTS = {"AFIB": 15, "Flutter": 3, "1AVB": 10, "3AVB": 5, "LBBB": 4, "RBBB": 4, "LVH": 108}


def normalized(value):
    return " ".join(value.casefold().replace("\u2013", "-").replace("\u2011", "-").split())


def tokens(value):
    return tuple(normalized(t.strip(" []'\".")) for t in re.split(r"[\r\n;|]+", value) if t.strip(" []'\"."))


def reference_states(row, definitions):
    principal = definitions["principal_rhythm"]
    # This provider qualifier changes conduction, not the accompanying AF rhythm.
    categories = set(tokens(row["Rhythms"])) - {"aberrant conduction"}
    declared = {principal[t] for t in categories if t in principal}
    rhythm = next(iter(declared)) if len(declared) == 1 and categories <= principal.keys() else None
    labels = set(principal.values()) - {"other_specified_principal_rhythm"}
    states = {c: ("positive" if rhythm == c else "negative" if rhythm else "unknown") for c in labels}
    for label, (field, pattern) in POSITIVE_PATTERNS.items():
        states[label] = "positive" if any(
            re.match(pattern + r"(?:\b|$)", value) for value in tokens(row[field])
        ) else "unknown"
    states.update(dict.fromkeys(definitions["unmapped"], "unknown"))
    for endpoint, members in OTHER_MEMBERS.items():
        subset = [states[label] for label in members]
        states[endpoint] = "positive" if "positive" in subset else (
            "negative" if all(s == "negative" for s in subset) else "unknown")
    return states, rhythm


def read_references(archive, protocol, keys):
    with zipfile.ZipFile(archive) as z:
        checks = source_manifest(z.read(PREFIX + "SHA256SUMS.txt").decode("utf-8"))
        raw = z.read(PREFIX + "ludb.csv")
        if sha256(raw) != checks["ludb.csv"]:
            raise ValueError("publisher reference seal mismatch")
    result, rhythms = {}, {}
    for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")):
        key = "data/" + str(int(row["ID"]))
        if key in result:
            raise ValueError("duplicate publisher reference")
        result[key], rhythms[key] = reference_states(row, protocol["reference_rules"])
    if result.keys() != set(keys):
        raise ValueError("reference enrollment is not identical to scored enrollment")
    for label, count in PUBLISHER_POSITIVE_COUNTS.items():
        if sum(r[label] == "positive" for r in result.values()) != count:
            raise ValueError(f"LUDB parser does not reconcile publisher support: {label}")
    return result, rhythms, sha256(raw)


def loaded_ledger(directory, keys, policy):
    receipt = json.loads((directory / "scoring-receipt.json").read_bytes())
    ledger = directory / "private-scored-and-routed.jsonl"
    if (receipt["protocol_sha256"] != PROTOCOL_SHA256 or receipt["source_archive_sha256"] != ARCHIVE_SHA256
            or receipt["policy_sha256"] != digest(policy) or receipt["reference_values_used"] is not False
            or receipt["route_reference_values_used"] is not False
            or receipt["private_score_route_ledger_sha256"] != digest(ledger)):
        raise ValueError("immutable scoring receipt does not match source, protocol or ledger")
    rows = list(jsonl(ledger))
    if len(rows) != keys or len({r["key"] for r in rows}) != keys:
        raise ValueError("invalid one-row-per-ECG route ledger")
    frozen = json.loads(policy.read_bytes())
    observed = Counter()
    for item in rows:
        if item["route"] != route(item["profiles"], receipt["thresholds"], frozen):
            raise ValueError("sealed route violates the frozen policy")
        observed[item["route"]["state"]] += 1
    if observed != Counter(receipt["routes"]):
        raise ValueError("sealed route counts do not reconcile")
    return rows, receipt


def fraction(n, d):
    return float(n / d) if d else None


def confusion(truth, calls):
    return dict(zip(("tn", "fp", "fn", "tp"), map(int, np.bincount(
        2 * np.asarray(truth, dtype=int) + np.asarray(calls, dtype=int), minlength=4)), strict=True))


def endpoint_metrics(rows, refs, groups, label, decision, subsets, design, metrics, bootstrap):
    report = {}
    for name, condition in subsets.items():
        included = [r for r in rows if condition(r)]
        flow = Counter(refs[r["key"]][label] for r in included)
        unique = {k: len({groups[r["key"]] for r in included if refs[r["key"]][label] == k}) for k in flow}
        observations = [(refs[r["key"]][label], decision(r), groups[r["key"]]) for r in included]
        available = [(KNOWN[s], p, call, g) for s, (p, call), g in observations if s in KNOWN and p is not None]
        truth, values, calls, units = (list(x) for x in zip(*available, strict=True)) if available else ([], [], [], [])
        pos, neg = (len({g for y, g in zip(truth, units, strict=True) if y == k}) for k in (1, 0))
        stats = {"eligible_ecgs": len(included), "reference_states": dict(flow),
                 "reference_components": unique, "known_scored_ecgs": len(truth),
                 "positive_components_scored": pos, "negative_components_scored": neg,
                 "no_output": sum(p is None for _, (p, _), _ in observations)}
        if not truth:
            report[name] = {**stats, "status": "no_known_scored_references"}
            continue
        if all(c is not None for c in calls):
            c = confusion(truth, calls)
            stats["descriptive_confusion"] = c
            stats["positive_reference_sensitivity"] = fraction(c["tp"], c["tp"] + c["fn"])
        if not pos or not neg:
            report[name] = {**stats, "status": "one_reference_polarity_only"}
            continue
        enough = min(pos, neg) >= design["two_sided_minimum_clusters_per_polarity"]
        if any(c is None for c in calls):
            from audit_reviewer_auxiliary_support import rank_metrics

            ranking = rank_metrics(zip(values, truth, strict=True))
            ranking["compatible_reference_negatives"] = ranking.pop("explicit_normal_control")
            stats["ranking"] = ranking
            stats["status"] = "rank_only" if enough else "sparse_rank_only"
        else:
            m = metrics(truth, calls, values)
            m["npv"] = fraction(m["tn"], m["tn"] + m["fn"])
            stats["metrics"] = m
            stats["status"] = "evaluated" if enough else "sparse_descriptive"
            if enough:
                stats["cluster_intervals"] = bootstrap(
                    truth, calls, values, units, seed=design["seed"], n_bootstrap=design["replicates"],
                    confidence=design["confidence"])
        report[name] = stats
    return report


def opportunities(r, refs, contracts):
    errors, denominator = 0, 0
    for p in ("P8", "P4"):
        for label in contracts[p]:
            state = refs[r["key"]][label]
            if state in KNOWN:
                denominator += 1
                errors += int(KNOWN[state] != int(label in r["profiles"][p]["labels"]))
    return errors, denominator


def risk_curve(margins, errors, opportunities_count, weights):
    order = np.argsort(-margins, kind="stable")
    if not len(order) or not weights.sum():
        return [], [], None
    ends = np.r_[np.flatnonzero(np.diff(margins[order])), len(order) - 1]
    ranked_weights = weights[order]
    count = np.cumsum(ranked_weights)[ends]
    coverage = count / count[-1]
    den = np.cumsum(ranked_weights * opportunities_count[order])[ends]
    err = np.cumsum(ranked_weights * errors[order])[ends]
    covered = count > 0
    risk = [fraction(n, d) for n, d in zip(err[covered], den[covered], strict=True)]
    coverage = coverage[covered]
    area = None if any(x is None for x in risk) else float(np.dot(np.diff(np.r_[0, coverage]), risk))
    return coverage.tolist(), risk, area


def selective(rows, refs, groups, contracts, design):
    scored = np.asarray([r["route"]["state"] != "technical_unscored" for r in rows])
    accept = np.asarray([r["route"]["state"] == "accepted" for r in rows])
    reject = scored & ~accept
    margin = np.asarray([r["route"]["signed_margin"] for r in rows if r["route"]["state"] != "technical_unscored"])
    errors, den = np.asarray([opportunities(r, refs, contracts) if ok else (0, 0)
                             for r, ok in zip(rows, scored, strict=True)]).T
    _, ix = np.unique([groups[r["key"]] for r in rows], return_inverse=True)
    n = int(ix.max()) + 1
    rng = np.random.default_rng(design["seed"])

    def estimates(weights):
        cov, risk, area = risk_curve(margin, errors[scored], den[scored], weights[scored])
        results = {
            "coverage_all_eligible": fraction(weights[accept].sum(), weights.sum()),
            "abstention_all_eligible": fraction(weights[reject].sum(), weights.sum()),
            "risk_baseline": fraction(weights @ errors, weights @ den),
            "risk_accepted": fraction(weights[accept] @ errors[accept], weights[accept] @ den[accept]),
            "risk_abstained_counterfactual": fraction(
                weights[reject] @ errors[reject], weights[reject] @ den[reject]),
            "aurc_scored": area,
        }
        return results, cov, risk

    point, cov, risk = estimates(np.ones(len(rows), dtype=int))
    boot = defaultdict(list)
    for _ in range(design["replicates"]):
        weights = np.bincount(rng.integers(n, size=n), minlength=n)[ix]
        sample = estimates(weights)[0]
        for k, v in sample.items():
            if v is not None:
                boot[k].append(v)
    tail = (1 - design["confidence"]) / 2
    intervals = {k: {"bounds": np.quantile(boot[k], [tail, 1-tail]).tolist() if boot[k] else None,
                     "valid": len(boot[k]), "invalid": design["replicates"] - len(boot[k])} for k in point}
    grid = np.arange(1, 11) / 10
    indices = np.searchsorted(cov, grid, side="left") if cov else []
    return {
        "routes": dict(Counter(r["route"]["state"] for r in rows)),
        "denominator_all_eligible": len(rows), "denominator_scored_jointly": int(scored.sum()),
        "opportunity_denominators": {"baseline": int(den.sum()), "accepted": int(den[accept].sum()),
                                     "abstained_counterfactual": int(den[reject].sum())},
        "wrong_opportunities": {"baseline": int(errors.sum()), "accepted": int(errors[accept].sum()),
                                "abstained_counterfactual": int(errors[reject].sum())},
        **point, "cluster_intervals": intervals, "risk_coverage_grid": {
            "attained_coverage": [cov[i] for i in indices], "risk": [risk[i] for i in indices],
        },
    }


def disposition(rows, refs, profile, label):
    result = Counter()
    for r in rows:
        if refs[r["key"]][label] != "positive":
            continue
        status = r["route"]["state"]
        r_scores = r["profiles"][profile]
        hit = label in r_scores.get("labels", ())
        if status == "accepted":
            result["emitted_tp" if hit else "emitted_fn"] += 1
        else:
            result[status + "_positive_no_output"] += 1
            if status == "abstained" and not hit:
                result["abstained_baseline_counterfactual_fn"] += 1
    result["all_reference_positives"] = sum(v for k, v in result.items() if k != "abstained_baseline_counterfactual_fn")
    return dict(result)


def macro_contrast(endpoints, names, baseline, comparator):
    common = [name for name in names if all(
        endpoints[name]["estimates"][split]["status"] == "evaluated"
        for split in (baseline, comparator))]
    means = {}
    for split in (baseline, comparator):
        means[split] = {metric: (
            float(np.mean([endpoints[name]["estimates"][split]["metrics"][metric] for name in common]))
            if common else None) for metric in ("f1", "accuracy")}
    return {"matched_endpoints": common, "means": means}


def analyze(rows, refs, rhythms, groups, receipt, protocol, morphology_model):
    from reviewer_pathology_other import probabilities
    from reviewer_rhythm_other import feature_vector
    from titan_v45.evaluation.specialist_heads import bootstrap_binary_metrics

    from titan_v45.evaluation.revision_report import binary_metrics

    design = protocol["analysis"]["uncertainty"]
    contracts = receipt["thresholds"]
    endpoints = {}
    for p in PROFILES:
        labels = contracts[p]
        for label in labels:
            def decision(row, profile=p, target=label):
                scores = row["profiles"][profile]
                return scores.get("scores", {}).get(target), int(target in scores.get("labels", ()))

            subsets = {"all_eligible": lambda _: True,
                       "restricted_known_positive_profile": lambda r, classes=labels: any(
                           refs[r["key"]][c] == "positive" for c in classes)}
            if p in ("P8", "P4"):
                subsets.update({status: lambda r, s=status: r["route"]["state"] == s for status in ROUTES})
                subsets["jointly_scored_baseline"] = lambda r: r["route"]["state"] != "technical_unscored"
            report = endpoint_metrics(rows, refs, groups, label, decision, subsets, design,
                                      binary_metrics, bootstrap_binary_metrics)
            endpoints[f"{p}:{label}"] = {"estimates": report}
            if p in ("P8", "P4"):
                endpoints[f"{p}:{label}"]["joint_positive_disposition"] = disposition(rows, refs, p, label)
                endpoints[f"{p}:{label}"]["route_scope_note"] = (
                    "For abstained and technical routes, per-profile baseline decisions are counterfactual only.")
    auxiliary = {}
    candidate = {r["key"]: np.asarray(feature_vector(r)) for r in rows
                 if all(r["profiles"][p]["status"] == "scored" for p in ("P6", "P8"))}
    model = morphology_model["endpoints"]
    for label in sorted(set(AUX_RHYTHM) | set(OTHER_MEMBERS) | {"ALMI", "ILMI", "LAE", "NSR", "PAC"}):
        routes = {"all_eligible": lambda _: True}
        profile = "P8" if label in AUX_RHYTHM else "P4"
        key = f"backbone_{AUX_RHYTHM[label]}" if label in AUX_RHYTHM else label
        def score(row, p=profile, name=key):
            return row["profiles"][p].get("auxiliary_scores", {}).get(name), None

        spec = model.get(label, {})
        entry = {"released_auxiliary": endpoint_metrics(
            rows, refs, groups, label, score, routes, design, binary_metrics, bootstrap_binary_metrics)}
        if spec.get("status") == "calibrated":
            def candidate_call(r, model_spec=spec):
                features = candidate.get(r["key"])
                if features is None:
                    return None, None
                value = float(probabilities(model_spec["candidate"], features))
                return value, int(value >= model_spec["candidate_threshold"])

            entry["separately_trained_sph_head"] = endpoint_metrics(
                rows, refs, groups, label, candidate_call, routes, design, binary_metrics, bootstrap_binary_metrics)
        else:
            entry["candidate_status"] = spec.get("status", "no_compatible_calibrated_head")
        auxiliary[label] = entry
    return {
        "endpoints": endpoints, "auxiliary_and_other": auxiliary,
        "matched_restricted_contrast": {p: macro_contrast(
            endpoints, [f"{p}:{label}" for label in contracts[p]], "all_eligible",
            "restricted_known_positive_profile") for p in PROFILES},
        "matched_selective_contrast": macro_contrast(
            endpoints, [f"{p}:{label}" for p in ("P8", "P4") for label in contracts[p]],
            "jointly_scored_baseline", "accepted"),
        "reference_principal_rhythm_counts": dict(Counter(x or "unknown" for x in rhythms.values())),
        "joint_selective": selective(rows, refs, groups, contracts, design),
        "routing_by_principal_rhythm": {k: dict(Counter(
            r["route"]["state"] for r in rows if (rhythms[r["key"]] or "unknown") == k))
            for k in sorted({v or "unknown" for v in rhythms.values()})},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "protocol", "policy", "scored", "output", "other-model",
                 "other-fit-receipt", "stage-a-inventory"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    if digest(args.archive) != ARCHIVE_SHA256 or digest(args.protocol) != PROTOCOL_SHA256:
        raise ValueError("frozen source or protocol differs")
    protocol = json.loads(args.protocol.read_bytes())
    rows, receipt = loaded_ledger(args.scored, protocol["source"]["records"], args.policy)
    model_hash = digest(args.other_model)
    fit = json.loads(args.other_fit_receipt.read_bytes())
    if (model_hash != SPH_OTHER_MODEL_SHA256 or fit["private_model_sha256"] != model_hash
            or fit["held_outcomes_evaluated"] is not False
            or str(fit["job"]) != "33396"):
        raise ValueError("expected the sealed November SPH fit, without target-cohort calibration")
    model = json.loads(args.other_model.read_bytes())
    if model["binding"] != fit["binding"]:
        raise ValueError("Other fit provenance differs")
    keys = [r["key"] for r in rows]
    refs, rhythms, reference_hash = read_references(args.archive, protocol, keys)
    groups = components({"ecg_id": r["key"], "patient_id": r["key"],
                         "signal_sha256_canonical_f64": r["physical_waveform_digest"] or "unavailable:" + r["key"]}
                        for r in rows)
    seen = defaultdict(list)
    for r in rows:
        if r["physical_waveform_digest"] is not None:
            seen[r["physical_waveform_digest"]].append(r["key"])
    for same_signal in seen.values():
        for label in refs[same_signal[0]]:
            if len({refs[k][label] for k in same_signal}) > 1:
                for k in same_signal:
                    refs[k][label] = "discordant_exact_waveform"
    prior = json.loads(args.stage_a_inventory.read_bytes())
    hashes = {r["signal_sha256"] for r in prior["rows"] if r.get("signal_sha256")}
    overlap = sum(r["raw_waveform_digest"] in hashes for r in rows)
    args.output.mkdir(mode=0o700)
    linked = args.output / "private-reference-route-ledger.jsonl"
    with linked.open("x", encoding="utf-8") as stream:
        for r in rows:
            k = r["key"]
            stream.write(json.dumps({**r, "references": refs[k], "component": groups[k]}, allow_nan=False) + "\n")
    split = {
        "source_unique_subjects_per_publisher": protocol["source"]["source_subjects"],
        "eligible_records": len(rows), "physical_waveforms_verified": sum(map(len, seen.values())),
        "distinct_physical_waveforms": len(seen), "subject_signal_components": len(set(groups.values())),
        "exact_duplicate_groups": sum(len(s) > 1 for s in seen.values()),
        "prior_stage_a_distinct_raw_signal_digests": len(hashes), "lu_db_raw_signal_matches_to_stage_a": overlap,
        "prior_stage_a_inventory_sha256": digest(args.stage_a_inventory),
        "raw_overlap_limit": "Same byte encoding only; no cross-provider patient key or complete June training manifest.",
        "lu_db_train_or_calibration_records": 0,
        "historical_independence_certified": False,
    }
    result = analyze(rows, refs, rhythms, groups, receipt, protocol, model)
    write_new(args.output / "aggregate.json", {
        "schema": "TITAN_V45_CLOSURE_LUDB_EVALUATION_V1", "job": os.environ.get("SLURM_JOB_ID"),
        "score_job": receipt["job"], "scoring_receipt_sha256": digest(args.scored / "scoring-receipt.json"),
        "frozen_protocol_sha256": PROTOCOL_SHA256, "frozen_policy_sha256": digest(args.policy),
        "source_reference_sha256": reference_hash, "frozen_sph_other_head_sha256": model_hash,
        "private_reference_route_ledger_sha256": digest(linked), "partition_audit": split,
        "independence": "new source transport; no target fitting; original historical patient exposure not certified",
        "historical_quarantine": "WITHDRAW_HISTORICAL_CLAIM", "second_stage_or_human_review": False,
        "no_individual_records_exported": True, **result,
    })


if __name__ == "__main__":
    main()
