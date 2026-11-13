"""Audit full-population prediction flow and a nested SPH restriction."""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from compare_reviewer_baseline import PROFILES, digest, load_ledger
from freeze_reviewer_selective_policy import components, jsonl

SCOPES = ("all_scored_reference_compatible", "restricted_has_any_profile_statement")


def stratum(codes, compatible, proxies, other, normal):
    if not codes:
        return "missing_primary_statement"
    if normal in codes:
        return "normal_only" if codes == {normal} else "ambiguous_normal_and_other_statement"
    if codes & compatible:
        return "mapped_plus_other_statement" if codes - compatible else "mapped_only"
    if codes & other:
        return "out_of_profile_observable_no_mapped_statement"
    if codes & proxies:
        return "proxy_present_no_mapped_statement"
    return "other_unmapped_no_profile_statement"


def observe(rows, refs, groups, profile, names, codes, config):
    union = set().union(*codes)
    proxy = set(config["proxy_codes"][profile])
    other = set(config["other_observable_codes"][profile])
    normal = config["normal_code"]
    flow, patients = defaultdict(Counter), defaultdict(set)
    calls, top1 = defaultdict(Counter), defaultdict(Counter)
    cluster, y, prediction, scores, mask = [], [], [], [], []
    for k, ref in refs.items():
        record = rows[k]
        primary = ref.primary_codes
        state = stratum(primary, union, proxy, other, normal)
        flow[state][record["status"]] += 1
        patients[state].add(ref.patient)
        if record["status"] != "scored":
            continue
        decision = record["profiles"][profile]
        emitted = decision["labels"]
        if set(emitted) - decision["scores"].keys() or decision["top1"] not in decision["scores"]:
            raise ValueError("inconsistent recorded decisions")
        calls[state].update(emitted)
        top1[state][decision["top1"]] += 1
        flow[state]["empty_label_set"] += not emitted
        flow[state]["fallback"] += decision["used_fallback"]
        if state in {"missing_primary_statement", "ambiguous_normal_and_other_statement"}:
            continue
        cluster.append(groups[k])
        y.append([bool(primary & e) for e in codes])
        prediction.append([e in emitted for e in names])
        scores.append([decision["scores"][e] for e in names])
        mask.append(bool(primary & union))
    population = {k: {
        "metadata_ecgs": sum(n for s, n in v.items() if s not in {"empty_label_set", "fallback"}),
        "unique_source_patients": len(patients[k]),
        "scoring_state": {s: n for s, n in v.items() if s not in {"empty_label_set", "fallback"}},
        "empty_label_set": v["empty_label_set"], "top1_fallback": v["fallback"],
        "released_calls": dict(calls[k]), "released_top1": dict(top1[k]),
    } for k, v in flow.items()}
    if sum(v["metadata_ecgs"] for v in population.values()) != len(rows) or not y:
        raise ValueError("population accounting failure or no matched records")
    arrays = (np.asarray(y, dtype=np.int8), np.asarray(prediction, dtype=np.int8),
              np.asarray(scores, dtype=float), np.asarray(mask, dtype=bool))
    if not np.isfinite(arrays[2]).all() or np.any((arrays[2] < 0) | (arrays[2] > 1)):
        raise ValueError("score outside finite probability range")
    return population, cluster, arrays


def point(y, pred, score, select, names, metrics):
    endpoints = {}
    for j, name in enumerate(names):
        ref, call, prob = y[select, j], pred[select, j], score[select, j]
        if not len(ref):
            endpoints[name] = {"n": 0, "metrics": None}
            continue
        values = metrics(ref, call, prob)
        n_negative_calls = values["tn"] + values["fn"]
        values["npv"] = values["tn"] / n_negative_calls if n_negative_calls else None
        endpoints[name] = {"n": len(ref), "statement_positive": int(ref.sum()), "metrics": values}
    defined = [e["metrics"] for e in endpoints.values() if e["metrics"] is not None]
    return {"n": int(select.sum()), "macro_f1_on_mapped_endpoints": float(
        np.mean([m["f1"] for m in defined])) if len(defined) == len(names) else None,
        "endpoint_macro_binary_accuracy": float(np.mean([m["accuracy"] for m in defined]))
        if len(defined) == len(names) else None, "endpoints": endpoints}


def paired_contrast(y, pred, restricted, clusters, design):
    _, ix = np.unique(clusters, return_inverse=True)
    n = int(ix.max()) + 1
    m = y.shape[1]
    # One weighted bincount produces every endpoint's four cells.
    cells = (4*np.arange(m) + 2*y + pred).ravel()
    rng = np.random.default_rng(design["seed"])

    def metrics(w):
        tn, fp, fn, tp = np.bincount(cells, weights=np.repeat(w, m), minlength=4*m).reshape(m, 4).T
        den = 2*tp + fp + fn
        f = np.divide(2*tp, den, out=np.zeros(m), where=den > 0) if w.sum() else np.full(m, np.nan)
        a = (tn+tp) / w.sum() if w.sum() else np.full(m, np.nan)
        sens = np.divide(tp, tp+fn, out=np.full(m, np.nan), where=(tp+fn) > 0)
        spec = np.divide(tn, tn+fp, out=np.full(m, np.nan), where=(tn+fp) > 0)
        return np.r_[f.mean(), a.mean(), sens, spec]

    def difference(w):
        return metrics(w*restricted) - metrics(w)

    delta = difference(np.ones(len(y)))
    samples = np.asarray([difference(np.bincount(rng.integers(n, size=n), minlength=n)[ix])
                          for _ in range(design["replicates"])])
    a = (1-design["level"])/2
    out = []
    for d, v in zip(delta, samples.T, strict=True):
        valid = v[np.isfinite(v)]
        out.append({"restricted_minus_all": float(d) if np.isfinite(d) else None,
                    "interval": np.quantile(valid, [a, 1-a]).tolist() if len(valid) else None,
                    "valid_replicates": len(valid), "invalid_replicates": len(v)-len(valid)})
    return out


def report_profiles(rows, refs, groups, frozen, protocol, metrics):
    profiles = {}
    for p in PROFILES:
        end = [e for e in frozen["endpoints"] if e["profile"] == p]
        names, codes = [e["name"] for e in end], [set(e["codes"]) for e in end]
        if set(names).intersection(protocol["reference_missing_outputs"][p]) or (
            set(names) | set(protocol["reference_missing_outputs"][p]) != set(frozen["profiles"][p]["classes"])
        ):
            raise ValueError("reference map does not account for every released output")
        population, cluster, (y, pred, score, restricted) = observe(rows, refs, groups, p, names, codes, protocol)
        contrasts = paired_contrast(y, pred, restricted, cluster, protocol["bootstrap"])
        profiles[p] = {
            "reference_strata": population, "outputs_without_validated_reference": protocol["reference_missing_outputs"][p],
            "metrics": {scope: point(y, pred, score, mask, names, metrics)
                        for scope, mask in zip(SCOPES, (np.ones(len(y), dtype=bool), restricted), strict=True)},
            "paired_denominator_differences": {
                "macro_f1": contrasts[0], "endpoint_macro_binary_accuracy": contrasts[1],
                "sensitivity": dict(zip(names, contrasts[2:2+len(names)], strict=True)),
                "specificity": dict(zip(names, contrasts[2+len(names):], strict=True)),
            },
        }
    return profiles


def main():
    from titan_v45.data.sph import read_sph_dictionary, read_sph_metadata
    from titan_v45.evaluation.revision_report import binary_metrics

    p = argparse.ArgumentParser(description=__doc__)
    for n in ("phase", "protocol", "frozen", "source", "ledger", "receipt", "duplicate-index", "output"):
        p.add_argument(f"--{n}", type=Path, required=True)
    a = p.parse_args()
    phase, protocol, frozen = (json.loads(path.read_bytes()) for path in (a.phase, a.protocol, a.frozen))
    rows, receipt = load_ledger(a.ledger, a.receipt, phase)
    if digest(a.frozen) != receipt["protocol_sha256"] or digest(
        a.duplicate_index
    ) != receipt["private_duplicate_index_sha256"]:
        raise ValueError("frozen protocol or duplicate index differs")
    for n in ("metadata.csv", "code.csv"):
        if digest(a.source/n) != receipt["source_sha256"][n]:
            raise ValueError("source hash mismatch")
    dictionary, modifiers = read_sph_dictionary((a.source/"code.csv").read_text(encoding="utf-8-sig"))
    refs = read_sph_metadata((a.source/"metadata.csv").read_text(encoding="utf-8-sig"), dictionary, modifiers)
    index = list(jsonl(a.duplicate_index))
    groups = components(index)
    if rows.keys() != refs.keys() or rows.keys() != groups.keys() or any(
        r["patient_id"] != refs[r["ecg_id"]].patient for r in index
    ):
        raise ValueError("ledger, metadata and signal grouping differ")
    counts = Counter(code for ref in refs.values() for code in ref.primary_codes)
    report = {"schema": protocol["schema"], "scope": protocol["scope"], "job": os.environ.get("SLURM_JOB_ID"),
              "baseline_receipt_sha256": digest(a.receipt), "analysis_protocol_sha256": digest(a.protocol),
              "source_population": {"source": frozen["source_population"]["dataset"], "metadata_ecgs": len(refs),
                                    "unique_source_patients": len({ref.patient for ref in refs.values()}),
                                    "distinct_exact_signal_signatures_in_sealed_index": len({
                                        r["signal_sha256_canonical_f64"] for r in index}),
                                    "patient_exact_signal_components": len(set(groups.values())), "status": receipt["flow"]},
              "statement_prevalence_before_exclusions": {str(code): {
                  "statement": name, "ecgs": counts[code], "fraction": counts[code]/len(refs),
              } for code, name in dictionary.items()},
              "denominator_definition": protocol["denominator"], "restricted_definition": protocol["restriction"],
              "routing": protocol["routing"], "reference_semantics": protocol["reference"],
              "record_identifiers_exported": False, "independent_validation": False,
              "profiles": report_profiles(rows, refs, groups, frozen, protocol, binary_metrics)}
    with a.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
