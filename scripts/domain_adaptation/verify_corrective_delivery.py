"""Validate the corrective public delivery against its frozen protocol."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from verify_adaptation_delivery import assert_hash
from verify_recovery_delivery import check_counts, json_value, rows

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/performance_recovery/CORRECTIVE_PROTOCOL.json"
REPORTS = {"CORRECTIVE_SELECTION.json", "CORRECTIVE_FITS.json", "CORRECTIVE_METRICS.csv",
           "CORRECTIVE_PAIRED_INTERVALS.csv"}
EXTRAS = {"CORRECTIVE_DECISION.json", "CORRECTIVE_DIAGNOSIS.json", "CORRECTIVE_SLURM.csv",
          "CORRECTIVE_REPRESENTATION_PROBE.csv", "CORRECTIVE_REPRESENTATION_RECEIPT.json",
          "CORRECTIVE_PRIVATE_READBACK.json"}


def verify(folder):
    decision = json.loads((folder / "CORRECTIVE_DECISION.json").read_bytes())
    if (decision["test_opened"] or decision["promotion"] != "NOT_AUTHORIZED"
            or decision["independent_generalization"] != "NOT_EVALUATED"
            or decision["development_success"] != all(decision["guards"].values())):
        raise ValueError("incorrect promotion or access claim")
    assert_hash(PROTOCOL, decision["protocol_sha256"])
    protocol = json.loads(PROTOCOL.read_bytes())
    if ({p.name for p in folder.iterdir()} != REPORTS | EXTRAS or set(decision["public_sha256"]) != REPORTS
            or any(p.is_symlink() or not p.is_file() for p in folder.iterdir())):
        raise ValueError("unexpected corrective artifact roster")
    for p in folder.iterdir():
        if p.name in REPORTS:
            assert_hash(p, decision["public_sha256"][p.name])
        if p.suffix == ".json":
            json_value(json.loads(p.read_bytes()))
        else:
            rows(p)
    selection = json.loads((folder / "CORRECTIVE_SELECTION.json").read_bytes())
    diagnostic = folder / "CORRECTIVE_DIAGNOSIS.json"
    assert_hash(diagnostic, selection["audit_sha256"])
    audit = json.loads(diagnostic.read_bytes())
    fits = json.loads((folder / "CORRECTIVE_FITS.json").read_bytes())
    if (not audit["diagnostic_pass"] or audit["test_opened"] or audit["max_probability_replay_error"] > 1e-5
            or not audit["masked_gradient_zero"] or selection["test_opened"]):
        raise ValueError("development diagnostics not satisfied")
    jobs = {row["JobIDRaw"]: row for row in rows(folder / "CORRECTIVE_SLURM.csv")}
    probe = json.loads((folder / "CORRECTIVE_REPRESENTATION_RECEIPT.json").read_bytes())
    readback = json.loads((folder / "CORRECTIVE_PRIVATE_READBACK.json").read_bytes())
    assert_hash(folder / "CORRECTIVE_REPRESENTATION_PROBE.csv", probe["results_sha256"])
    assert_hash(folder / "CORRECTIVE_DECISION.json", readback["source_decision_sha256"])
    if any(r["test_opened"] or r["protocol_sha256"] != decision["protocol_sha256"] for r in (probe, readback)):
        raise ValueError("probe or readback protocol mismatch")
    if len(probe["published_weights"]) != 5 or readback["max_absolute_error"] > 1e-7:
        raise ValueError("physical model hashes or readback incomplete")
    release = {r["name"]: r["sha256"] for r in json.loads((ROOT / "release-manifest.json").read_bytes())["assets"]}
    if any(release.get(name) != sha for name, sha in probe["published_weights"].items()):
        raise ValueError("physical checkpoint hashes differ from release")
    relevant = {audit["slurm_job"], decision["slurm_job"], probe["slurm_job"], readback["slurm_job"],
                *[r["slurm_job"] for r in fits]}
    if any(jobs[j]["State"] != "COMPLETED" or jobs[j]["ExitCode"] != "0:0" for j in relevant):
        raise ValueError("published evidence is not backed by completed jobs")
    if sum(int(j["ElapsedRaw"]) for j in jobs.values() if "gres/gpu" in j["AllocTRES"]) > protocol["gpu_allocation_hours_max"] * 3600:
        raise ValueError("corrective GPU budget exceeded")
    keys = {(r["arm"], r["seed"]) for r in fits}
    if len(keys) != len(fits) or len(fits) > protocol["max_fits"] or selection["selected"] not in fits:
        raise ValueError("invalid corrective fit roster")
    for r in fits:
        assert_hash(diagnostic, r["audit_sha256"])
        if (r["epoch"] not in r["history"] or r["calibration_opened"] or r["test_opened"]
                or len(r["checkpoint_sha256"]) != 64):
            raise ValueError("invalid corrective fit receipt")
        chosen_epoch = min(r["history"], key=lambda h: (
            *h["selection"][:2], *[-v for v in h["selection"][2:]]))
        if r["epoch"] != chosen_epoch:
            raise ValueError("corrective epoch differs from frozen selection rule")
    metrics = rows(folder / "CORRECTIVE_METRICS.csv")
    if len(metrics) != readback["rows_verified"]:
        raise ValueError("not all metrics independently verified")
    for row in metrics:
        check_counts(row)
        tn, fn = int(row["tn"]), int(row["fn"])
        if tn + fn and abs(float(row["npv"]) - tn / (tn + fn)) > 1e-12:
            raise ValueError("invalid NPV")
    intervals = rows(folder / "CORRECTIVE_PAIRED_INTERVALS.csv")
    point = {(r["scope"], r["arm"], r["endpoint"], r["metric"]): float(r["value"]) for r in intervals}
    for r in intervals:
        if r["scope"] == "cpsc" and r["resampling_unit"] != "ecg_only":
            raise ValueError("CPSC patient grouping is not certified")
        if not 0 <= int(r["valid_replicates"]) <= protocol["paired_bootstrap"]["replicates"]:
            raise ValueError("invalid bootstrap support")
        if r["arm"] == "C-A":
            key = (r["scope"], r["endpoint"], r["metric"])
            a, c = (point[(key[0], arm, *key[1:])] for arm in ("A", "C"))
            if not math.isclose(c - a, float(r["value"]), abs_tol=1e-12):
                raise ValueError("paired point estimate differs from matched point metrics")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    verify(parser.parse_args().folder)
    print("Corrective development evidence verified")
