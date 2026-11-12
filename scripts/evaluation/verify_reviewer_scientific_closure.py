"""Check closure evidence at its native CEDIA origin or as a sanitized export."""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from collections import Counter
from pathlib import Path

from score_reviewer_closure_ludb import ARCHIVE_SHA256, PROTOCOL_SHA256, write_new
from verify_reviewer_november_delivery import digest, protected_path, seal_entry, validate_public

JOBS = {
    "score": "33697", "evaluate": "33720", "morphology": "33704", "ptb_score": "33737", "ptb_evaluate": "33737",
    "ptbxl_rhythm_score": "33736", "ptbxl_rhythm_evaluate": "33736",
}
SUPERSEDED_EVALUATION = "33699"
FAILED_PTB_ADAPTER = "33718"
PUBLIC_NAMES = {
    "score": "ludb_scoring_receipt.json",
    "evaluate": "ludb_fixed_policy_and_reference_aggregate.json",
    "morphology": "morphology_robustness_aggregate.json",
    "sph": "sph_split_and_policy_audit.json",
    "ptb_score": "ptb_diagnostic_scoring_receipt.json",
    "ptb_evaluate": "ptb_diagnostic_transport_aggregate.json",
    "ptb_eligibility": "ptb_diagnostic_eligibility_verified_v2.json",
    "ptb_eligibility_superseded": "ptb_diagnostic_eligibility_superseded_v1.json",
    "ptbxl_support": "ptbxl_other_support_verified_v2.json",
    "ptbxl_rhythm_score": "ptbxl_cached_v3ag_rhythm_scoring_receipt.json",
    "ptbxl_rhythm_evaluate": "ptbxl_cached_v3ag_rhythm_aggregate.json",
}
SPH_SHA256 = "f133cec9ba402ff7fb19ccf5ecaba8daae66c4f492829e3d0f13caa356fbd2d7"
POLICY_SHA256 = "c9183320a4dd923f037a93fc014fc2db6bc64f223ff67b5d297e540eefb43ae6"
PTB_ELIGIBILITY_SHA256 = "fc179fe166b340c37b1372201243c4d48268d0270d691562a3187b706fa94eaf"
PTB_SUPERSEDED_SHA256 = "4e97e47839971f35f81333f46458ba6ab8ea01c1f3bf81c7b15fa58fc84547f9"
PTB_PROTOCOL_SHA256 = "3975bb5a8f2bcade7f559146d1c3f30a5553728b8ac94d84f40c4cec3c4d9db2"
PTBXL_SUPPORT_COMMIT = "e0feb79e372eafc98f4074b79df822c1e131f6fa"
PTBXL_SUPPORT_SHA256 = "1e758fcb0cc17e7cc15ff8be2fcb7911a6f102d4dd5d673cec440d409a187bcd"
SCORE_STATES = {"scored", "technical_unscored"}
ROUTES = {"accepted", "abstained", "technical_unscored"}


def number_equal(actual, n, d):
    return actual is None if not d else actual is not None and math.isclose(actual, n / d, abs_tol=1e-12)


def check_scientific(score, evaluated, morph, sph, score_hash):
    if (score["source_archive_sha256"] != ARCHIVE_SHA256
            or score["protocol_sha256"] != PROTOCOL_SHA256 or score["policy_sha256"] != POLICY_SHA256
            or score["eligible_ecgs"] != 200 or score["publisher_verified_waveform_files"] != 400
            or score["reference_values_used"] is not False or score["route_reference_values_used"] is not False
            or evaluated["scoring_receipt_sha256"] != score_hash
            or evaluated["frozen_protocol_sha256"] != PROTOCOL_SHA256
            or evaluated["frozen_policy_sha256"] != POLICY_SHA256
            or evaluated["historical_quarantine"] != "WITHDRAW_HISTORICAL_CLAIM"
            or evaluated["second_stage_or_human_review"] is not False):
        raise ValueError("LUDB provenance, source eligibility, or policy separation differs")
    n = score["eligible_ecgs"]
    for p in ("P6", "P8", "P4"):
        if (set(score["scored_by_profile"][p]) - SCORE_STATES
                or sum(score["scored_by_profile"][p].values()) != n):
            raise ValueError("invalid profile scoring counts")
    joint = evaluated["joint_selective"]
    if (joint["routes"] != score["routes"] or set(joint["routes"]) - ROUTES
            or sum(joint["routes"].values()) != n or joint["denominator_all_eligible"] != n):
        raise ValueError("one-route-per-ECG denominator fails")
    routed = joint["routes"]
    a, q = routed.get("accepted", 0), routed.get("abstained", 0)
    if (joint["denominator_scored_jointly"] != a + q
            or not number_equal(joint["coverage_all_eligible"], a, n)
            or not number_equal(joint["abstention_all_eligible"], q, n)):
        raise ValueError("coverage and abstention do not reconcile")
    denominators = joint["opportunity_denominators"]
    errors = joint["wrong_opportunities"]
    for d in (denominators, errors):
        if d["baseline"] != d["accepted"] + d["abstained_counterfactual"]:
            raise ValueError("accepted and counterfactual opportunities do not partition baseline")
    for name, k in (("risk_baseline", "baseline"), ("risk_accepted", "accepted"),
                    ("risk_abstained_counterfactual", "abstained_counterfactual")):
        if errors[k] > denominators[k] or not number_equal(joint[name], errors[k], denominators[k]):
            raise ValueError("risk uses the wrong known-reference denominator")
    for endpoint in evaluated["endpoints"].values():
        estimates = endpoint["estimates"]
        if estimates["all_eligible"]["eligible_ecgs"] != n:
            raise ValueError("primary reference flow lacks the full source denominator")
        for sample in estimates.values():
            if (sum(sample["reference_states"].values()) != sample["eligible_ecgs"]
                    or sample["known_scored_ecgs"] > sum(sample["reference_states"].get(s, 0)
                                                       for s in ("positive", "negative"))):
                raise ValueError("unknown references cannot enter an endpoint confusion table")
            if "descriptive_confusion" in sample and sum(sample["descriptive_confusion"].values()) != sample["known_scored_ecgs"]:
                raise ValueError("endpoint confusion denominator does not match known scored ECGs")
        d = endpoint.get("joint_positive_disposition")
        if d is not None and (d["all_reference_positives"] != sum(d.get(k, 0) for k in (
            "emitted_tp", "emitted_fn", "abstained_positive_no_output", "technical_unscored_positive_no_output"
        )) or d["all_reference_positives"] != estimates["all_eligible"]["reference_states"].get("positive", 0)):
            raise ValueError("emitted errors and withheld reference positives do not reconcile")
    if (sph["eligible_ecgs"] != 25770 or sum(sph["ecg_by_split"].values()) != 25770
            or sph["overlap_calibration_held"] != {"patient": 0, "signal": 0, "component": 0}
            or sph["joint_policy_sha256"] != POLICY_SHA256 or sph["exact_calibration_recipe_rederived"] is not True):
        raise ValueError("SPH calibration isolation or cutoff reproduction is not verified")
    if morph["fit_or_feature_extraction_performed"] is not False or set(morph["profiles"]) != {"P6", "P8", "P4"}:
        raise ValueError("morphology audit must reuse the three original fitted arms")
    ordered = sorted(morph["profiles"].values(), key=lambda p: p["two_sided_monte_carlo_p"])
    holm = 0.0
    for i, p in enumerate(ordered):
        holm = min(1.0, max(holm, (len(ordered) - i) * p["two_sided_monte_carlo_p"]))
        if (not number_equal(p["two_sided_monte_carlo_p"], p["absolute_null_extremes"] + 1, p["permutations"] + 1)
                or not math.isclose(p["holm_adjusted_p"], holm, abs_tol=1e-12)
                or not math.isclose(p["observed_delta_macro_f1"],
                                    p["original_bootstrap_rederived"]["with_minus_without"], abs_tol=1e-12)):
            raise ValueError("morphology robustness calculations do not reconcile")


def check_ptb(score, result, eligibility, score_hash):
    if (score["protocol_sha256"] != PTB_PROTOCOL_SHA256 or score["reference_labels_used_for_scoring"] is not False
            or result["fit_or_calibration_performed"] is not False or result["historical_independence_certified"]
            or result["score_receipt_sha256"] != score_hash
            or result["reference_eligibility_sha256"] != PTB_ELIGIBILITY_SHA256
            or result["private_reference_manifest_sha256"] != eligibility["reference_manifest_sha256"]
            or not (score["all_source_records"] == result["all_source_ecgs"] == eligibility["verified_headers"] == 549)
            or result["source_subjects"] != 290 or result["scored_flow"] != score["flow"]
            or sum(result["scored_flow"].values()) != 549):
        raise ValueError("PTB clinical comparison lineage, scope or denominator differs")
    if set(result["endpoints"]) != {"ASMI", "IMI", "ALMI", "ILMI"}:
        raise ValueError("PTB clinical territory contract differs")
    for label, endpoints in result["endpoints"].items():
        prior = eligibility["endpoints"][label]
        if not prior["eligible_for_territory_control_comparison"]:
            raise ValueError("PTB endpoint did not pass the source-reference support gate")
        for e in endpoints.values():
            known = e["reference_states"].get("positive", 0) + e["reference_states"].get("negative", 0)
            if (e["eligible_ecgs"] != 549 or sum(e["reference_states"].values()) != 549
                    or e["known_scored_ecgs"] > known
                    or e["reference_states"].get("negative", 0) > prior["record_states"]["explicit_control"]
                    or e["reference_states"].get("positive", 0) > prior["record_states"]["positive"]):
                raise ValueError("PTB endpoint reference flow does not reconcile")


def check_ludb_detail(score, result):
    audit = result["partition_audit"]
    if (audit["eligible_records"] != score["eligible_ecgs"]
            or audit["source_unique_subjects_per_publisher"] != 200 or audit["distinct_physical_waveforms"] != 200
            or audit["exact_duplicate_groups"] != 0 or audit["prior_stage_a_distinct_raw_signal_digests"] != 19217
            or audit["lu_db_raw_signal_matches_to_stage_a"] != 0 or audit["historical_independence_certified"]
            or audit["lu_db_train_or_calibration_records"] != 0):
        raise ValueError("LUDB source population, exact signal check or exposure scope differs")
    by_rhythm = result["routing_by_principal_rhythm"]
    routes = Counter()
    for counts in by_rhythm.values():
        routes.update(counts)
    if (routes != score["routes"]
            or {k: sum(v.values()) for k, v in by_rhythm.items()} != result["reference_principal_rhythm_counts"]):
        raise ValueError("LUDB routes by reference group do not reconcile")
    endpoints = result["endpoints"]
    primary = {p: [f"{p}:{c}" for c in classes] for p, classes in score["thresholds"].items()}
    if set(endpoints) != {k for keys in primary.values() for k in keys}:
        raise ValueError("LUDB output endpoint coverage differs from released profiles")
    tests = [(keys, result["matched_restricted_contrast"][p], "all_eligible", "restricted_known_positive_profile")
             for p, keys in primary.items()]
    tests.append((primary["P8"] + primary["P4"], result["matched_selective_contrast"],
                  "jointly_scored_baseline", "accepted"))
    for keys, contrast, a, b in tests:
        matched = [k for k in keys if all(endpoints[k]["estimates"][s]["status"] == "evaluated" for s in (a, b))]
        if contrast["matched_endpoints"] != matched or set(contrast["means"]) != {a, b}:
            raise ValueError("LUDB matched contrast includes incompatible endpoint estimates")
        for subset, metrics in contrast["means"].items():
            if any(not number_equal(value, sum(endpoints[k]["estimates"][subset]["metrics"][m] for k in matched),
                                    len(matched)) for m, value in metrics.items()):
                raise ValueError("LUDB matched contrast arithmetic differs")
    for e in endpoints.values():
        d = e.get("joint_positive_disposition", {})
        if d.get("abstained_baseline_counterfactual_fn", 0) > d.get("abstained_positive_no_output", 0):
            raise ValueError("LUDB counterfactual misses exceed withheld positives")
    for endpoint, positive in {"P8:AFIB": 15, "P8:1AVB": 10, "P8:RBBB": 4, "P4:LVH": 108}.items():
        if endpoints[endpoint]["estimates"]["all_eligible"]["reference_states"].get("positive", 0) != positive:
            raise ValueError("LUDB compatible references do not match published support")


def check_ptbxl_support(audit, receipt_hash):
    if (receipt_hash != PTBXL_SUPPORT_SHA256 or audit["metadata_ecgs"] != 19601
            or audit["source_subjects"] != 16965 or audit["cached_records"] != 6205
            or audit["cached_exact_signal_groups_crossing_folds_1_9"] != 0
            or audit["fold10_reference_parsed"] or audit["fold10_waveforms_accessed"]
            or audit["historical_independence_certified"] or audit["inference_or_performance_estimation"]):
        raise ValueError("PTB-XL support receipt does not preserve scope or source seal")
    targets = {"NSR", "PAC", "Flutter", "Paced", "LBBB", "2AVB", "3AVB", "LQTS", "ALMI", "ILMI", "LAE"}
    support = audit["endpoint_support"]
    denominators = {"all_folds_1_9": 19601, **{f"{p}_scoreable": 6205 for p in ("P6", "P8", "P4")}}
    if set(support) != targets or any(set(parts) != set(denominators) for parts in support.values()):
        raise ValueError("PTB-XL audit does not account for all requested classes and profiles")
    for endpoint, parts in support.items():
        for split, part in parts.items():
            counts, subjects = part["ECGs"], part["source_subjects"]
            if (sum(counts.values()) != denominators[split] or set(counts) != set(subjects)
                    or any(not 0 < subjects[k] <= n for k, n in counts.items())
                    or (endpoint in {"NSR", "LQTS", "LAE"} and set(counts) - {"unknown", "non_equivalent_proxy"})):
                raise ValueError("PTB-XL support counts or diagnostic proxy boundary differ")


def check_ptbxl_rhythm(score, result, audit, score_hash):
    if (score["scored"] != 6205 or score["source_reference_values_used"] or score["waveform_inference"]
            or score["archived_probability_columns_checked"] != 16
            or not 0 <= score["max_absolute_archived_score_error"] <= 1e-5
            or result["score_receipt_sha256"] != score_hash or result["reference_support_sha256"] != PTBXL_SUPPORT_SHA256
            or result["all_metadata_ecgs"] != 19601 or result["cached_scored_ecgs"] != 6205
            or result["outside_authorized_scoreable_cache"] != 13396
            or result["historical_independence_certified"] or result["fold10_references_or_waveforms_used"]
            or result["weights_changed"] or result["calibration_and_held_subject_overlap"] != 0
            or result["exact_signal_groups_crossing_folds"] != 0):
        raise ValueError("PTB-XL cached readout changed source, replay tolerance or split boundary")
    if set(result["endpoints"]) != {"Paced", "2AVB", "3AVB"}:
        raise ValueError("PTB-XL cached readout endpoint set differs")
    for endpoint, entry in result["endpoints"].items():
        c, h = entry["calibration_folds_1_8"], entry["held_fold_9"]
        pooled = entry["pooled_descriptive_rank"]
        expected = audit["endpoint_support"][endpoint]["P4_scoreable"]["ECGs"]
        if (entry["released_operating_point_exists"] or pooled["reference_states"] != expected
                or sum(s["eligible_cache_ecgs"] for s in (c, h)) != 6205
                or any(sum(s["reference_states"].values()) != s["eligible_cache_ecgs"] for s in (c, h))
                or any(sum(s["reference_states"].get(k, 0) for s in (c, h)) != n for k, n in expected.items())
                or (c["reference_states"].keys() | h["reference_states"].keys()) != expected.keys()):
            raise ValueError("PTB-XL cached endpoint denominator does not reconcile")
        threshold = entry["new_operating_point"]
        enough = min(s[k] for s in (c, h) for k in ("positive_subjects", "control_subjects")) >= 5
        if (threshold is not None) != enough or ("metrics" in h) != enough:
            raise ValueError("PTB-XL operating point or held estimate bypasses the support screen")
        if enough:
            m = h["metrics"]
            if (m["tp"] + m["fn"] != h["reference_states"]["positive"]
                    or m["tn"] + m["fp"] != h["reference_states"]["explicit_normal_control"]
                    or not number_equal(m["npv"], m["tn"], m["tn"] + m["fn"])):
                raise ValueError("PTB-XL held confusion counts differ from known references")


def native_files(root):
    out = subprocess.check_output([
        "sacct", "-S", "2026-11-12", "-X", "-j",
        ",".join(sorted(set(JOBS.values()) | {SUPERSEDED_EVALUATION, FAILED_PTB_ADAPTER})),
        "-P", "-n",
        "-o", "JobIDRaw,State,ExitCode,Elapsed",
    ], text=True)
    states = {}
    for line in out.splitlines():
        job, state, code, elapsed = line.rstrip("|").split("|")
        if job in states:
            raise ValueError("duplicate accounting rows")
        states[job] = {"state": state.split()[0], "exit_code": code, "elapsed": elapsed}
    for job in JOBS.values():
        state = states.get(job)
        if not state or (state["state"], state["exit_code"]) != ("COMPLETED", "0:0"):
            raise ValueError(f"authoritative job {job} is not a successful result")
    if states.get(FAILED_PTB_ADAPTER, {}).get("state") != "FAILED":
        raise ValueError("PTB adapter failure not preserved in native accounting")
    roots = {
        "score": root / f"ludb-score-{JOBS['score']}",
        "evaluate": root / f"ludb-eval-{JOBS['evaluate']}",
        "morphology": root / f"morphology-audit-{JOBS['morphology']}",
        "ptb_score": root / f"ptb-transport-{JOBS['ptb_score']}",
        "ptb_evaluate": root / f"ptb-transport-{JOBS['ptb_evaluate']}",
        "ptbxl_rhythm_score": root / f"ptbxl-cached-rhythm-{JOBS['ptbxl_rhythm_score']}",
        "ptbxl_rhythm_evaluate": root / f"ptbxl-cached-rhythm-{JOBS['ptbxl_rhythm_evaluate']}",
    }
    paths = {k: protected_path(r, "scoring-receipt.json" if k.endswith("score") else "aggregate.json")
             for k, r in roots.items()}
    checks = {k: seal_entry(roots[k], p) for k, p in paths.items()}
    for k, file, field in (
        ("score", "private-scored-and-routed.jsonl", "private_score_route_ledger_sha256"),
        ("evaluate", "private-reference-route-ledger.jsonl", "private_reference_route_ledger_sha256"),
        ("ptb_score", "private-scores.jsonl", "private_scores_sha256"),
        ("ptbxl_rhythm_score", "private-readout.json", "private_score_sha256"),
    ):
        if seal_entry(roots[k], protected_path(roots[k], file)) != json.loads(paths[k].read_bytes())[field]:
            raise ValueError("native private ledger does not match public summary")
    paths["sph"] = protected_path(root, "sph-split-audit-baceb368a08352b6ea74798f1c77159ef1ec139a.json")
    checks["sph"] = digest(paths["sph"])
    if checks["sph"] != SPH_SHA256:
        raise ValueError("native SPH audit bytes differ")
    for k, tag, expected in (
        ("ptb_eligibility", "fc0f1d7bd9fca80cb159277fab17961dbb028cb9", PTB_ELIGIBILITY_SHA256),
        ("ptb_eligibility_superseded", "f6781067bc18860f1224060e61a3141151cbe293", PTB_SUPERSEDED_SHA256),
    ):
        directory = root / f"ptb-diagnostic-source-audit-{tag}"
        paths[k] = protected_path(directory, "aggregate.json")
        checks[k] = seal_entry(directory, paths[k])
        if checks[k] != expected:
            raise ValueError("native PTB source audit bytes differ")
        aggregate = json.loads(paths[k].read_bytes())
        ref = protected_path(directory, "private-reference-manifest.jsonl")
        if seal_entry(directory, ref) != aggregate["reference_manifest_sha256"]:
            raise ValueError("PTB private reference bytes differ")
    directory = root / f"ptbxl-other-support-{PTBXL_SUPPORT_COMMIT}"
    paths["ptbxl_support"] = protected_path(directory, "aggregate.json")
    checks["ptbxl_support"] = seal_entry(directory, paths["ptbxl_support"])
    return paths, checks, states


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--cedia-root", type=Path)
    group.add_argument("--public-dir", type=Path)
    parser.add_argument("--native-receipt", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.cedia_root:
        paths, checks, states = native_files(args.cedia_root.resolve())
    else:
        if not args.native_receipt:
            parser.error("--public-dir requires --native-receipt")
        source = json.loads(args.native_receipt.read_bytes())
        states, checks = source["scheduler"], source["public_sha256"]
        if (set(checks) != set(PUBLIC_NAMES)
                or any(not re.fullmatch(r"[0-9a-f]{64}", h) for h in checks.values())
                or checks["sph"] != SPH_SHA256
                or any((states[j]["state"], states[j]["exit_code"]) != ("COMPLETED", "0:0") for j in JOBS.values())):
            raise ValueError("invalid native export receipt")
        paths = {k: protected_path(args.public_dir.resolve(), name) for k, name in PUBLIC_NAMES.items()}
    content = {}
    for k, path in paths.items():
        if digest(path) != checks[k]:
            raise ValueError("published artifact differs from its native seal")
        content[k] = json.loads(path.read_bytes())
        validate_public(content[k])
        if k in JOBS and str(content[k]["job"]) != JOBS[k]:
            raise ValueError("producer job does not match native accounting")
    check_scientific(content["score"], content["evaluate"], content["morphology"], content["sph"], checks["score"])
    check_ludb_detail(content["score"], content["evaluate"])
    check_ptb(content["ptb_score"], content["ptb_evaluate"], content["ptb_eligibility"], checks["ptb_score"])
    check_ptbxl_support(content["ptbxl_support"], checks["ptbxl_support"])
    check_ptbxl_rhythm(content["ptbxl_rhythm_score"], content["ptbxl_rhythm_evaluate"],
                     content["ptbxl_support"], checks["ptbxl_rhythm_score"])
    if checks["ptb_eligibility_superseded"] != PTB_SUPERSEDED_SHA256:
        raise ValueError("superseded PTB reference audit bytes differ")
    result = {"schema": "TITAN_V45_SCIENTIFIC_CLOSURE_VERIFICATION_V1",
              "scheduler": states, "public_sha256": checks, "public_files": PUBLIC_NAMES,
              "superseded_evaluations_not_used": {
                  SUPERSEDED_EVALUATION: "multiline source grammar corrected",
                  FAILED_PTB_ADAPTER: "wrong sealed model threshold key; no rows or receipt produced",
              },
              "science_consistency_verified": True, "record_level_export_performed": False}
    if args.output:
        write_new(args.output, result)
    else:
        print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
