"""Check closure evidence at its native CEDIA origin or as a sanitized export."""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from pathlib import Path

from score_reviewer_closure_ludb import ARCHIVE_SHA256, PROTOCOL_SHA256, write_new
from verify_reviewer_november_delivery import digest, protected_path, seal_entry, validate_public

JOBS = {"score": "33697", "evaluate": "33699", "morphology": "33704"}
PUBLIC_NAMES = {
    "score": "ludb_scoring_receipt.json",
    "evaluate": "ludb_fixed_policy_and_reference_aggregate.json",
    "morphology": "morphology_robustness_aggregate.json",
    "sph": "sph_split_and_policy_audit.json",
}
SPH_SHA256 = "f133cec9ba402ff7fb19ccf5ecaba8daae66c4f492829e3d0f13caa356fbd2d7"
POLICY_SHA256 = "c9183320a4dd923f037a93fc014fc2db6bc64f223ff67b5d297e540eefb43ae6"
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
    for p in morph["profiles"].values():
        if (not number_equal(p["two_sided_monte_carlo_p"], p["absolute_null_extremes"] + 1, p["permutations"] + 1)
                or p["holm_adjusted_p"] < p["two_sided_monte_carlo_p"]
                or not math.isclose(p["observed_delta_macro_f1"],
                                    p["original_bootstrap_rederived"]["with_minus_without"], abs_tol=1e-12)):
            raise ValueError("morphology robustness calculations do not reconcile")


def native_files(root):
    out = subprocess.check_output([
        "sacct", "-S", "2026-11-12", "-X", "-j", ",".join(JOBS.values()), "-P", "-n",
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
    roots = {
        "score": root / f"ludb-score-{JOBS['score']}",
        "evaluate": root / f"ludb-eval-{JOBS['evaluate']}",
        "morphology": root / f"morphology-audit-{JOBS['morphology']}",
    }
    paths = {k: protected_path(r, "scoring-receipt.json" if k == "score" else "aggregate.json")
             for k, r in roots.items()}
    checks = {k: seal_entry(roots[k], p) for k, p in paths.items()}
    for k, file, field in (
        ("score", "private-scored-and-routed.jsonl", "private_score_route_ledger_sha256"),
        ("evaluate", "private-reference-route-ledger.jsonl", "private_reference_route_ledger_sha256"),
    ):
        if seal_entry(roots[k], protected_path(roots[k], file)) != json.loads(paths[k].read_bytes())[field]:
            raise ValueError("native private ledger does not match public summary")
    paths["sph"] = protected_path(root, "sph-split-audit-baceb368a08352b6ea74798f1c77159ef1ec139a.json")
    checks["sph"] = digest(paths["sph"])
    if checks["sph"] != SPH_SHA256:
        raise ValueError("native SPH audit bytes differ")
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
    result = {"schema": "TITAN_V45_SCIENTIFIC_CLOSURE_VERIFICATION_V1",
              "scheduler": states, "public_sha256": checks, "public_files": PUBLIC_NAMES,
              "science_consistency_verified": True, "record_level_export_performed": False}
    if args.output:
        write_new(args.output, result)
    else:
        print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
