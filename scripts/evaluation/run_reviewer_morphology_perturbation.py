"""Zero the ten normalized morphology inputs while preserving released weights."""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from contextlib import contextmanager
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


@contextmanager
def perturb_preparation(owner, function, calls):
    """Wrap the argument to the pinned preparer without editing the loader."""
    original = getattr(owner, function)

    def prepare(record, morphology, *args, **kwargs):
        return original(record, neutralize(morphology, calls), *args, **kwargs)

    setattr(owner, function, prepare)
    try:
        yield
    finally:
        setattr(owner, function, original)


def p6_manifest_keys(repo, expected_sha256):
    import hashlib
    import io

    p = repo / "data/manifests/external_dev/rhythm_primary6_diagnostic_records.csv"
    raw = p.read_bytes()
    if hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != expected_sha256:
        raise ValueError("P6 manifest differs from producer receipt")
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")))
    keys = {(r["source"].casefold(), r["record_id"]) for r in rows}
    if len(keys) != len(rows) or not keys:
        raise ValueError("P6 manifest keys are not unique and nonempty")
    return keys


def keyed_ledger(path):
    result = {}
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            key = (row["source"].casefold(), row["record_id"])
            if key in result:
                raise ValueError("duplicate private replay key")
            result[key] = row
    return result


def compare(baseline, perturbed, profile, p6_keys=None):
    if baseline.keys() != perturbed.keys():
        raise ValueError("the perturbation changed the intended replay universe")
    profiles = ("P4",) if profile == "pathology_primary4" else ("P6", "P8")
    if "P6" in profiles and (not p6_keys or not p6_keys <= baseline.keys()):
        raise ValueError("invalid P6 eligibility manifest")
    result = {}
    for p in profiles:
        eligible = p6_keys if p == "P6" else baseline.keys()
        paired = changed = status_disagreement = 0
        by_class = {}
        for key in baseline:
            old = baseline[key]
            new = perturbed[key]
            if key not in eligible:
                if p in old or p in new:
                    raise ValueError("score outside P6 eligibility")
                continue
            if p == "P4":
                a, b = old.get("primary_scores"), new.get("primary_scores")
                old_decision, new_decision = old.get("pathology"), new.get("pathology")
            else:
                x, y = old.get(p, {}), new.get(p, {})
                a, b = x.get("scores"), y.get("scores")
                old_decision = (x.get("top1"), frozenset(x.get("labels", ())), x.get("used_fallback"))
                new_decision = (y.get("top1"), frozenset(y.get("labels", ())), y.get("used_fallback"))
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
            "intended_records": len(eligible), "ledger_universe_records": len(baseline), "paired_scored": paired,
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
        prepare = "prepare_p4_record"
    else:
        from titan_v45.cascade import run_rhythm
        owner, run = run_rhythm, run_rhythm.run_rhythm_release
        prepare = "prepare_rhythm_record"
    with perturb_preparation(owner, prepare, calls):
        original_report, ledger = run(a.repo, a.release, a.scratch, "cuda")
    if not calls[0]:
        raise ValueError("morphology intervention was never applied")
    p6_keys = None if a.profile == "pathology_primary4" else p6_manifest_keys(
        a.repo, original_report["manifest_sha256_lf"]["rhythm_primary6_diagnostic_records.csv"])
    summary = compare(keyed_ledger(a.baseline_ledger), ledger, a.profile, p6_keys)
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
