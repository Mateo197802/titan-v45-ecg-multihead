"""Check public loop receipts, budgets and privacy without restricted inputs."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from verify_adaptation_delivery import assert_hash
from verify_recovery_delivery import check_counts, json_value, rows

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/performance_recovery/AUTONOMOUS_LOOP_PROTOCOL.json"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
FIT_ID = re.compile(r"[0-9]{2}-(?:SB|AFIB|1AVB)-[a-z_]+-[0-9]{8}\Z")
FILES = {
    "AUTONOMOUS_LOOP_EXECUTION_LEDGER.csv", "ITERATION_HYPOTHESES_AND_DECISIONS.json",
    "CLASSWISE_ERROR_EVOLUTION.csv", "TRAINING_CHECKPOINT_SHA256SUMS.txt", "BEST_DEVELOPMENT_MODEL.json",
    "THREE_SEED_STABILITY.csv", "MULTISOURCE_GENERALIZATION_RESULTS.csv", "FINAL_PERFORMANCE_COMPARISON.csv",
    "REMAINING_TECHNICAL_BLOCKERS.md",
}


def verify(folder):
    name = "MODEL_PROMOTION_DECISION.json"
    receipt = json.loads((folder / name).read_bytes())
    json_value(receipt)
    assert_hash(PROTOCOL, receipt["protocol_sha256"])
    limit = json.loads(PROTOCOL.read_bytes())["limits"]
    if (receipt["promotion"] != "NOT_AUTHORIZED" or receipt["independent_generalization"] != "NOT_EVALUATED"
            or receipt["historical_test_opened"] or not receipt["selection_reuse"]
            or set(receipt["files"]) != FILES or {p.name for p in folder.iterdir()} != FILES | {name}):
        raise ValueError("incorrect scope or aggregate roster")
    for name, sha in receipt["files"].items():
        path = folder / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("unsafe delivery path")
        assert_hash(path, sha)
        if path.suffix == ".json":
            json_value(json.loads(path.read_bytes()))
        elif path.suffix == ".csv":
            rows(path)
    history = json.loads((folder / "ITERATION_HYPOTHESES_AND_DECISIONS.json").read_bytes())
    fits = history["verified_fits"]
    if (len(fits) != receipt["verified_fits"] or len(history["cycles"]) != receipt["cycles"] <= limit["cycles"]
            or len(history["attempts"]) != receipt["attempts"] <= limit["fit_attempts"]
            or history["readback"]["max_absolute_error"] > 1e-7):
        raise ValueError("invalid execution counts or readback")
    jobs = rows(folder / "AUTONOMOUS_LOOP_EXECUTION_LEDGER.csv")
    if (sum(int(r["verified_fits"]) for r in jobs) != len(fits)
            or sum(int(r["attempts"]) for r in jobs) != len(history["attempts"])
            or sum(int(r["ElapsedRaw"]) for r in jobs if "gres/gpu" in r["AllocTRES"])
            != receipt["allocated_gpu_seconds"] <= limit["gpu_seconds"]):
        raise ValueError("invalid SLURM accounting")
    detail = rows(folder / "CLASSWISE_ERROR_EVOLUTION.csv")
    if len(detail) != history["readback"]["rows"] or {r["fit"] for r in detail} != set(fits):
        raise ValueError("incomplete independent recalculation")
    for row in detail:
        check_counts(row)
    selected = json.loads((folder / "BEST_DEVELOPMENT_MODEL.json").read_bytes())
    if selected["finalist"] != receipt["finalist"] or not set(selected["predecessor_chain"]) <= set(fits):
        raise ValueError("invalid finalized ancestry")
    hashes = {}
    for line in (folder / "TRAINING_CHECKPOINT_SHA256SUMS.txt").read_text(encoding="ascii").splitlines():
        sha, name = line.split("  ", 1)
        fit = name.removesuffix("/best.pt")
        if not SHA256.fullmatch(sha) or not FIT_ID.fullmatch(fit) or fit in hashes or name == fit:
            raise ValueError("invalid checkpoint roster")
        hashes[fit] = sha
    if set(hashes) != set(fits) or hashes.get(selected["finalist"]) != selected["fit"]["checkpoint_sha256"]:
        raise ValueError("checkpoint SHA roster disagrees with the finalist")
    for child, parent in zip(selected["predecessor_chain"], selected["predecessor_chain"][1:], strict=False):
        if fits[child]["anchor_sha256"] != hashes[parent]:
            raise ValueError("checkpoint ancestry is not hash-linked")
    stable = rows(folder / "THREE_SEED_STABILITY.csv")
    for cycle in history["cycles"]:
        for family in cycle.get("family", []):
            roster = family["members"]
            if len(roster) != 3 or len(set(roster)) != 3 or not set(roster) <= set(fits):
                raise ValueError("unstable finalist roster")
            if sum(int(row["cycle"]) == cycle["number"] for row in stable) != len(roster):
                raise ValueError("missing per-seed metrics")
    replay = json.loads((folder.parent / "AUTONOMOUS_CHECKPOINT_REPLAY.json").read_bytes())
    interval = json.loads((folder.parent / "AUTONOMOUS_INTERVAL_READBACK.json").read_bytes())
    for audit in (replay, interval):
        json_value(audit)
        assert_hash(PROTOCOL, audit["protocol_sha256"])
        if audit["test_opened"]:
            raise ValueError("final audit opened historical test")
    if (replay["finalist"] != selected["finalist"] or replay["chain"] != selected["predecessor_chain"]
            or replay["max_absolute_probability_error"] > 1e-5
            or set(replay["sample_counts"]) != {"validation", "chapman", "cpsc"}
            or min(replay["sample_counts"].values()) < 1 or interval["max_absolute_error"] > 1e-12
            or interval["scope"] != "CODE_SELECTION_ONLY" or interval["valid_replicates"] != 1000):
        raise ValueError("checkpoint replay or independent interval readback failed")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("folder", type=Path)
    verify(cli.parse_args().folder)
    print("Autonomous loop public evidence verified")
