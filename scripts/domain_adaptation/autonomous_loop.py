"""Run one crash-recoverable autonomous cycle in a preallocated SLURM slot."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
from pathlib import Path
from statistics import mean

import numpy as np
from autonomous_worker import PROTOCOL, SCOPES, Runner, read_fit, settings
from corrective_audit import cfg as corrective_settings
from corrective_evaluate import compare
from recovery_inputs import audit_splits, config
from recovery_reporting import source_audit
from train_duration_aware import digest, write_json

JOB = re.compile(r"[0-9]+\Z")
INITIAL = "published_development_incumbent"


def load(path):
    return json.loads(path.read_bytes())


def guards(r, initial):
    source = {s: r["sources"][s] - initial[s] for s in ("chapman", "cpsc")}
    return (all(g["pass"] for g in r["guards"].values()), r["calibration_guard"],
            all(d >= -.03 for d in source.values()), min(source.values()), mean(source.values()),
            r["summary"]["f1"], r["summary"]["average_precision"], -r["summary"]["brier_score"], -r["summary"]["ece"])


def ranked(records, initial):
    return sorted(records, key=lambda r: (guards(r, initial), r["arm"]), reverse=True)


def qualifies(records, initial, baseline_f1, seeds):
    return ({r["seed"] for r in records} == set(seeds)
            and all(all(guards(r, initial)[:3]) and r["summary"]["f1"] > baseline_f1 for r in records))


def next_phase(state, c):
    index = len(state["cycles"])
    phase = c["phases"][index]
    seen = {(r["endpoint"], r["arm"], r["anchor"]) for r in state["screens"]}
    anchor = state["working"]
    arms = [a for a in phase["arms"] if (phase["endpoint"], a, anchor) not in seen]
    return {"number": index + 1, "endpoint": phase["endpoint"], "arms": arms, "anchor": anchor}


def anchor_for(root, runner, name):
    if name == INITIAL:
        return {"scores": {k: v["p"] for k, v in runner.data.items()}, "policy": runner.policy,
                "chapman_policy": runner.policy,
                "checkpoint_sha256": config()["parent_checkpoints"][str(settings()["reference_seed"])]}
    path = root / "fits" / name
    r = read_fit(path)
    with np.load(path / "private_scores.npz", allow_pickle=False) as z:
        return {**r, "scores": dict(z)}


def result_id(phase, arm, seed):
    return f"{phase['number']:02d}-{phase['endpoint']}-{arm}-{seed}"


def run_fit(root, state_file, state, runner, phase, anchor, arm, seed, job):
    c = settings()
    fit_id = result_id(phase, arm, seed)
    target = root / "fits" / fit_id
    if target.is_dir():
        return read_fit(target)
    attempts = [a for a in state["attempts"] if a["fit"] == fit_id]
    if len(attempts) > c["limits"]["transient_retries"]:
        return None
    if len(state["attempts"]) >= c["limits"]["fit_attempts"]:
        return None
    stage = root / "attempts" / f"{fit_id}-{len(attempts) + 1}"
    if attempts:
        prior = attempts[-1]
        prior_dir = root / "attempts" / prior["stage"]
        if (prior_dir / "fit.json").is_file():
            record = read_fit(prior_dir)
            prior_dir.rename(target)
            return record
        # A terminal attempt with an explicit permanent error is never retried.
        if prior["outcome"] == "PERMANENT_ERROR":
            raise ValueError("prior fit terminated on integrity failure")
        prior["outcome"] = "INTERRUPTED"
    attempt = {"fit": fit_id, "job": job, "stage": stage.name, "outcome": "STARTED"}
    state["attempts"].append(attempt)
    write_json(state_file, state)
    stage.mkdir()
    try:
        r = runner.fit(stage, phase["endpoint"], arm, seed, anchor, job)
        read_fit(stage)
        stage.rename(target)
    except (ValueError, FloatingPointError) as e:
        attempt["outcome"] = "PERMANENT_ERROR"
        attempt["error_class"] = type(e).__name__
        write_json(state_file, state)
        raise
    attempt["outcome"] = "VERIFIED"
    write_json(state_file, state)
    return r


def paired(root, runner, fit):
    r = read_fit(root / "fits" / fit)
    with np.load(root / "fits" / fit / "private_scores.npz", allow_pickle=False) as z:
        blocks = {}
        for scope in SCOPES:
            policy = r["chapman_policy"] if scope == "chapman" else r["policy"]
            _, intervals = compare(scope, runner.data[scope], z[scope], policy,
                                   corrective_settings()["paired_bootstrap"], config()["endpoints"])
            blocks[scope] = intervals
    return blocks


def execute(previous, archive, root, job):
    if not JOB.fullmatch(job):
        raise ValueError("numeric SLURM allocation required")
    c = settings()
    root.mkdir(mode=0o700, exist_ok=True)
    for name in ("fits", "attempts"):
        (root / name).mkdir(exist_ok=True)
    with (root / "controller.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state_file = root / "state.json"
        state = load(state_file) if state_file.exists() else {
            "protocol_sha256": digest(PROTOCOL), "cycles": [], "attempts": [], "screens": [],
            "working": INITIAL, "incumbent": INITIAL, "stagnant": 0, "stop": None, "jobs": [],
        }
        if state["protocol_sha256"] != digest(PROTOCOL):
            raise ValueError("controller protocol changed")
        if state["stop"] and (root / "final.json").exists():
            return
        if job not in state["jobs"]:
            state["jobs"].append(job)
        if len(state["jobs"]) * c["limits"]["job_minutes"] * 60 > c["limits"]["gpu_seconds"]:
            state["stop"] = "GPU_BUDGET"
        write_json(state_file, state)
        runner = Runner(previous, archive)
        if "integrity" not in state:
            state["integrity"] = {"code": audit_splits(previous / "code-bank"),
                                  "sources": source_audit(previous / "additional-sources-v2")}
            first = anchor_for(root, runner, INITIAL)
            initial = {}
            for scope in SCOPES:
                data = runner.data[scope]
                initial[scope] = mean(score_for(data, j, first["policy"]) for j in range(5)
                                      if set(data["labels"][data["labels"][:, j] >= 0, j]) == {0, 1})
            state["initial"] = initial
            write_json(state_file, state)
        if not state["stop"]:
            phase = state.get("current") or next_phase(state, c)
            state["current"] = phase
            write_json(state_file, state)
            anchor = anchor_for(root, runner, phase["anchor"])
            results = []
            try:
                for arm in phase["arms"]:
                    r = run_fit(root, state_file, state, runner, phase, anchor, arm, c["reference_seed"], job)
                    if r is not None:
                        results.append(r)
                if results:
                    lead = ranked(results, state["initial"])[0]
                    family = [lead]
                    for seed in c["seeds"][1:]:
                        r = run_fit(root, state_file, state, runner, phase, anchor, lead["arm"], seed, job)
                        if r is not None:
                            family.append(r)
                    decide(state, phase, results, family, c, root, runner)
                else:
                    state["stagnant"] += 1
                    state["cycles"].append({**phase, "decision": "NO_UNTESTED_OR_COMPLETED_HYPOTHESIS"})
                state.pop("current")
            except (ValueError, FloatingPointError):
                state["stop"] = "INTEGRITY_OR_NUMERICAL_FAILURE"
                write_json(state_file, state)
                raise
            if not state["stop"]:
                if len(state["attempts"]) >= c["limits"]["fit_attempts"]:
                    state["stop"] = "FIT_BUDGET"
                elif state["stagnant"] >= c["limits"]["stagnant_cycles"]:
                    state["stop"] = "THREE_STAGNANT_CYCLES"
                elif len(state["cycles"]) >= c["limits"]["cycles"]:
                    state["stop"] = "CYCLE_BUDGET"
            write_json(state_file, state)
        if state["stop"]:
            finalist = state["incumbent"] if state["incumbent"] != INITIAL else state["working"]
            if finalist == INITIAL:
                eligible = [r for cycle in state["cycles"] for r in cycle.get("family", [])]
                if eligible:
                    finalist = max(eligible, key=lambda r: tuple(r["rank"]))["representative"]
            verified = {}
            for path in sorted((root / "fits").iterdir()):
                verified[path.name] = read_fit(path)
            intervals = paired(root, runner, finalist) if finalist != INITIAL else {}
            write_json(root / "final.json", {
                "state": state, "finalist": finalist, "fits": verified, "intervals": intervals,
                "historical_test_opened": False, "independent_generalization": "NOT_EVALUATED",
                "promotion": "NOT_AUTHORIZED"})


def score_for(data, j, policy):
    from autonomous_worker import score_anchor

    return score_anchor(data, j, policy)["f1"]


def decide(state, phase, screens, family, c, root, runner):
    initial = state["initial"]
    for r in screens:
        state["screens"].append({"endpoint": r["endpoint"], "arm": r["arm"], "anchor": phase["anchor"]})
    record = {**phase, "screened": [r["arm"] for r in screens], "family": [], "decision": "NO_REPRODUCIBLE_ADVANCE"}
    state["stagnant"] += 1
    if len(family) == len(c["seeds"]):
        ordered = sorted(family, key=lambda r: (r["summary"]["f1"], r["seed"]))
        mid = ordered[len(ordered) // 2]
        fit = result_id(phase, mid["arm"], mid["seed"])
        ranks = [guards(r, initial) for r in family]
        rank = [min(r[i] for r in ranks) if i < 3 else mean(r[i] for r in ranks) for i in range(len(ranks[0]))]
        record["family"] = [{"representative": fit, "rank": rank,
                             "members": [result_id(phase, r["arm"], r["seed"]) for r in family]}]
        prior = state.get("working_rank")
        if prior is None or tuple(rank) > tuple(prior):
            state["working"], state["working_rank"], state["stagnant"] = fit, rank, 0
            record["decision"] = "EXPERIMENTAL_ANCHOR_ONLY"
        base_f1 = (initial["validation"] if state["incumbent"] == INITIAL else
                   read_fit(root / "fits" / state["incumbent"])["summary"]["f1"])
        if qualifies(family, initial, base_f1, c["seeds"]):
            state["incumbent"] = fit
            record["decision"] = "DEVELOPMENT_INCUMBENT_ADVANCE"
            if mid["summary"]["f1"] >= .70:
                ci = next(r for r in paired(root, runner, fit)["validation"] if
                          (r["endpoint"], r["arm"], r["metric"]) == ("macro", "C-A", "f1"))
                if ci["ci_low"] is not None and ci["ci_low"] > 0:
                    state["stop"] = "DEVELOPMENT_TARGET_MET"
    state["cycles"].append(record)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("previous", "archive", "root"):
        parser.add_argument(field, type=Path)
    args = vars(parser.parse_args())
    execute(**args, job=os.environ["SLURM_JOB_ID"])
