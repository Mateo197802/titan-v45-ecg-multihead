"""Zero the ten normalized morphology inputs while preserving released weights."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

import numpy as np
from compare_reviewer_baseline import digest


def neutralize(original, calls):
    def zero(signal, *args, **kwargs):
        value = np.asarray(original(signal, *args, **kwargs))
        if value.shape != (10,) or not np.isfinite(value).all():
            raise ValueError("unexpected normalized morphology contract")
        calls[0] += 1
        return np.zeros_like(value)
    return zero


def keyed_ledger(path):
    result = {}
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            key = (row["source"], row["record_id"])
            if key in result:
                raise ValueError("duplicate private replay key")
            result[key] = row
    return result


def compare(baseline, perturbed, profile):
    if baseline.keys() != perturbed.keys():
        raise ValueError("the perturbation changed the intended replay universe")
    profiles = ("P4",) if profile == "pathology_primary4" else ("P6", "P8")
    result = {}
    for p in profiles:
        paired = changed = status_disagreement = 0
        by_class = {}
        for key, old in baseline.items():
            new = perturbed[key]
            if p == "P4":
                a, b = old.get("primary_scores"), new.get("primary_scores")
                old_decision, new_decision = old.get("pathology"), new.get("pathology")
            else:
                x, y = old.get(p, {}), new.get(p, {})
                a, b = x.get("scores"), y.get("scores")
                old_decision = (x.get("top1"), x.get("labels"))
                new_decision = (y.get("top1"), y.get("labels"))
            if a is None or b is None:
                status_disagreement += (a is None) != (b is None)
                continue
            if a.keys() != b.keys() or not a:
                raise ValueError("score contract differs")
            paired += 1
            changed += old_decision != new_decision
            for name, a_score in a.items():
                delta = abs(a_score - b[name])
                if not np.isfinite(delta):
                    raise ValueError("nonfinite paired score delta")
                entry = by_class.setdefault(name, {"sum_abs": 0.0, "max_abs": 0.0})
                entry["sum_abs"] += delta
                entry["max_abs"] = max(entry["max_abs"], delta)
        result[p] = {
            "intended_records": len(baseline), "paired_scored": paired,
            "decision_changes": changed, "scoring_status_disagreements": status_disagreement,
            "by_class": {k: {"mean_absolute_delta": v["sum_abs"]/paired,
                             "max_absolute_delta": v["max_abs"]} for k, v in by_class.items()},
        }
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "release", "scratch", "baseline-ledger", "private-ledger", "output"):
        p.add_argument(f"--{name}", type=Path, required=True)
    p.add_argument("--profile", choices=("pathology_primary4", "rhythm"), required=True)
    p.add_argument("--baseline-sha256", required=True)
    p.add_argument("--source-commit", required=True)
    a = p.parse_args()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=a.repo, text=True).strip()
    if commit != a.source_commit or digest(a.baseline_ledger) != a.baseline_sha256:
        raise ValueError("replay baseline does not match the sealed source")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=a.repo).strip():
        raise ValueError("perturbation requires an unchanged replay tree")
    from titan_v45.cascade import run_pathology

    calls = [0]
    if a.profile == "pathology_primary4":
        owner, run = run_pathology, run_pathology.run_pathology_release
    else:
        from titan_v45.cascade import run_rhythm
        owner, run = run_rhythm, run_rhythm.run_rhythm_release
    load = owner._load_morphology
    owner._load_morphology = lambda repo: neutralize(load(repo), calls)
    try:
        original_report, ledger = run(a.repo, a.release, a.scratch, "cuda")
    finally:
        owner._load_morphology = load
    if not calls[0]:
        raise ValueError("morphology intervention was never applied")
    summary = compare(keyed_ledger(a.baseline_ledger), ledger, a.profile)
    with a.private_ledger.open("x", encoding="utf-8") as stream:
        for (source, key), row in ledger.items():
            stream.write(json.dumps({"source": source, "record_id": key, **row}, allow_nan=False)+"\n")
    report = {
        "scope": "paired zero-input sensitivity on selected historical replay; not a retrained ablation",
        "intervention": "replace the complete normalized morphology vector by zero at preprocessing output",
        "unchanged": ["waveforms", "published weights", "lead masks", "event features", "thresholds"],
        "source_commit": commit, "job": os.environ.get("SLURM_JOB_ID"),
        "baseline_ledger_sha256": a.baseline_sha256, "private_perturbed_ledger_sha256": digest(a.private_ledger),
        "release_sha256": original_report["release_sha256"], "window_calls": calls[0],
        "profiles": summary, "identifiers_exported": False,
    }
    with a.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, allow_nan=False, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
