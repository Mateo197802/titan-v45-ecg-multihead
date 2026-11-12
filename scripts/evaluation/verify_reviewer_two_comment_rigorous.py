"""Read-only arithmetic checks, and build or verify the allowlisted public ZIP."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

RESULTS = {
    "R2_3F_ABLATION_CONFIRMATORY_RESULTS.json", "R2_4K_COVERAGE_RISK_AND_FALSE_NEGATIVES.json",
    "EXPERIMENTAL_PROTOCOLS_AND_SPLITS.json", "RUNTIME_AND_CASCADE_AGGREGATE.json",
    "CEDIA_EXECUTION_RECEIPTS.json",
}
DOCS = {
    "R2_3F_MORPHOLOGY_FINAL_VALIDATION.md", "R2_3F_HISTORICAL_REPLAY_ROOT_CAUSE.md",
    "R2_4K_SELECTIVE_PREDICTION_FINAL_VALIDATION.md", "R2_4K_CASCADE_EXPERIMENT.md",
    "SCIENTIFIC_CLAIM_VERIFICATION_MATRIX.csv", "FINAL_TWO_COMMENT_SCIENTIFIC_VERDICT.md",
    "EXPERIMENT_DESIGN_AND_REPRODUCTION.md",
}
REPRODUCTION = {
    "configs/reviewer_experiments/two_comment_rigorous_v1.json",
    "configs/reviewer_experiments/two_comment_gpu_v1.json",
    "configs/reviewer_experiments/november_morphology_retrained.json",
    "scripts/cedia/reviewer_two_comment.sbatch",
    "scripts/cedia/reviewer_private_scratch.sh",
    "scripts/evaluation/reviewer_selective_utility.py",
    "scripts/evaluation/reviewer_morphology_multiseed.py",
    "scripts/evaluation/reviewer_morphology_runtime.py",
    "scripts/evaluation/verify_reviewer_two_comment_rigorous.py",
    "scripts/evaluation/seal_reviewer_two_comment_native.py",
    "scripts/evaluation/render_reviewer_two_comment_reports.py",
    "scripts/evaluation/compare_reviewer_baseline.py",
    "scripts/evaluation/evaluate_reviewer_closure_ludb.py",
    "scripts/evaluation/freeze_reviewer_selective_policy.py",
    "scripts/evaluation/reviewer_morphology_retrained.py",
    "scripts/evaluation/score_reviewer_closure_ludb.py",
}


def require(check, text):
    if not check:
        raise ValueError(text)


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-8, abs_tol=1e-8)


def load(path):
    return json.loads(path.read_bytes())


def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def check_selective(result):
    source = {"SPH": (12869, 2478), "LUDB": (200, 48)}
    for name, (enrolled, withheld) in source.items():
        data = result["cohorts"][name]
        rules = data["rules"]
        all_ = rules["no_abstention"]
        frozen = rules["frozen_joint"]
        random = rules["random_equal_coverage"]
        require(data["full_ecgs"] == enrolled and data["scored_ecgs"] + data["technical_unscored"] == enrolled,
                f"{name} enrollment")
        require(close(all_["accepted"] - frozen["accepted"], withheld), f"{name} frozen denominator")
        require(close(random["accepted_risk"], all_["accepted_risk"]), f"{name} random expectation")
        for policy, r in rules.items():
            if policy != "no_abstention":
                require(close(r["accepted"], frozen["accepted"]), f"{name} matched coverage")
            endpoints = list(r["endpoints"].values())
            known = sum(sum(e[k] for k in ("tp", "tn", "fp", "fn_emitted")) for e in endpoints)
            err = sum(e["fp"] + e["fn_emitted"] for e in endpoints)
            require(close(known, r["known_emitted"]) and close(err, r["emitted_errors"]),
                    f"{name} emitted accounting")
            for e in endpoints:
                require(close(e["positive_total"], e["tp"]+e["fn_emitted"]+e["positive_withheld"]),
                        f"{name} class positive accounting")
            require(close(r["accepted_risk"], err/known), f"{name} accepted risk")
            require(close(r["known_emitted"]+r["known_withheld"], data["known_scored_opportunities"]),
                    f"{name} reference denominator")
            require(close(err+r["withheld_errors"], all_["emitted_errors"]), f"{name} error accounting")
            require(close(r["withheld_positive"], sum(e["positive_withheld"] for e in endpoints)),
                    f"{name} withheld positive accounting")
            for k, v in r["full_scored_cost"].items():
                require(close(v, (err+float(k)*r["known_withheld"])/data["known_scored_opportunities"]),
                        f"{name} full-denominator cost")
        delta = data["paired_risk_difference_vs_no_abstention_and_random_expected"]
        require(close(delta["difference"], frozen["accepted_risk"]-all_["accepted_risk"]), f"{name} paired delta")
    lu = result["cohorts"]["LUDB"]["rules"]
    require(lu["no_abstention"]["emitted_errors"] == 192 and lu["frozen_joint"]["emitted_errors"] == 139
            and lu["no_abstention"]["known_emitted"] == 924 and lu["frozen_joint"]["known_emitted"] == 697,
            "LUDB original risk accounting did not reproduce")


def check_ablation(abl):
    require(abl["seeds"] == [1978, 1983, 2026, 4501, 4502], "paired seeds differ")
    for name, profile in abl["profiles"].items():
        expected = []
        for s in abl["seeds"]:
            score = profile["seed_macro_f1"][str(s)]
            means = []
            for arm in ("with_morphology", "without_morphology"):
                rows = [x["seeds"][str(s)][arm] for x in profile["endpoints"].values() if x["status"] == "evaluated"]
                for x in rows:
                    require(x["rows"] == x["tp"]+x["fp"]+x["tn"]+x["fn"], f"{name} binary denominator")
                    d = 2*x["tp"]+x["fp"]+x["fn"]
                    require(close(x["f1"], 2*x["tp"]/d if d else 0), f"{name} binary F1")
                require(rows and close(score[arm], sum(x["f1"] for x in rows)/len(rows)), f"{name} macro")
                means.append(score[arm])
            expected.append(means[0]-means[1])
        require(close(profile["contrast"]["with_minus_without"], sum(expected)/len(expected)), f"{name} delta")
        c = profile["contrast"]
        require(c["valid_replicates"] + c["invalid_replicates"] == 2000, f"{name} bootstrap accounting")


def check_runtime(runtime):
    fixtures = runtime["fixture"]
    require(len(fixtures["expected"]) == len(fixtures["observed"]) == 10, "missing descriptor fixture")
    require(all(close(x, fixtures["observed"][k]) for k, x in fixtures["expected"].items()), "descriptor mismatch")
    require(fixtures["flat_line_artifact"]["peaks"] == 36, "flat-line finding not reproduced")
    require(runtime["identical_fixed_batch_repetition"] and runtime["traced_ecgs"] == 16, "runtime audit incomplete")
    c = runtime["fallback"]
    t = c["totals"]
    require(c["full_ecgs"] == 200 and c["routes"]["accepted"] == 152 and c["routes"]["abstained"] == 48,
            "cascade denominator")
    require(t["known_emitted"] + t["known_unresolved"] + t.get("technical_unscored", 0) == t["known_total"] == 924,
            "cascade endpoint denominator")
    require(t["baseline_errors"] == 192 and sum(x.get("final_errors", 0) for x in c["endpoint_accounting"].values())
            == t["final_errors"], "cascade errors")
    fb_before = t["final_errors"] - 139 - t["introduced"] + t["corrected"]
    require(t["known_emitted"] - t["fallback_known"] == 697 and 0 <= fb_before <= 53,
            "cascade fallback accounting")


def verify_directory(results, docs):
    files = {f"results/{name}": (results/name).read_bytes() for name in sorted(RESULTS)}
    files.update({f"docs/{name}": (docs/name).read_bytes() for name in sorted(DOCS)})
    root = Path(__file__).resolve().parents[2]
    files.update({name: (root/name).read_bytes() for name in sorted(REPRODUCTION)})
    s, m, r = (load(results / n) for n in ("R2_4K_COVERAGE_RISK_AND_FALSE_NEGATIVES.json",
                                          "R2_3F_ABLATION_CONFIRMATORY_RESULTS.json",
                                          "RUNTIME_AND_CASCADE_AGGREGATE.json"))
    check_selective(s)
    check_ablation(m)
    check_runtime(r)
    receipts = load(results / "CEDIA_EXECUTION_RECEIPTS.json")
    protocols = load(results / "EXPERIMENTAL_PROTOCOLS_AND_SPLITS.json")
    for name, aggregate in (("selective", s), ("morphology", m), ("runtime", r)):
        receipt = receipts["experiments"][name]
        require(receipt["job"] == aggregate["job"] and receipt["state"] == "COMPLETED" and receipt["exit"] == "0:0",
                f"{name} native execution did not complete")
        require(receipt["aggregate_sha256"] == hash_bytes(files["results/"+receipt["aggregate_filename"]]),
                f"{name} native aggregate hash differs")
        require(aggregate["protocol_sha256"] == protocols["frozen_protocol_sha256"][name],
                f"{name} protocol hash mismatch")
        require(aggregate["individual_data_exported"] is False, "individual data present")
    return files


def main():
    p = argparse.ArgumentParser()
    for name in ("results", "docs", "zip"):
        p.add_argument(f"--{name}", type=Path, required=True)
    p.add_argument("--build", action="store_true")
    a = p.parse_args()
    files = verify_directory(a.results, a.docs)
    files["SHA256SUMS"] = "".join(f"{hash_bytes(b)}  {n}\n" for n, b in files.items()).encode()
    if a.build:
        with ZipFile(a.zip, "x") as z:
            for name, b in sorted(files.items()):
                item = ZipInfo(name)
                item.compress_type = ZIP_DEFLATED
                z.writestr(item, b)
    with ZipFile(a.zip) as z:
        require(len(z.namelist()) == len(files) and set(z.namelist()) == set(files), "ZIP member mismatch")
        require(all(z.read(n) == b for n, b in files.items()), "ZIP byte mismatch")
    print(json.dumps({"zip_sha256": hash_bytes(a.zip.read_bytes()), "members": len(files),
                      "arithmetic_recomputed": True, "individual_data_exported": False}))


if __name__ == "__main__":
    main()
