"""Check public loop receipts, budgets and privacy without restricted inputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from verify_adaptation_delivery import assert_hash
from verify_recovery_delivery import check_counts, json_value, rows

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/performance_recovery/AUTONOMOUS_LOOP_PROTOCOL.json"
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


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("folder", type=Path)
    verify(cli.parse_args().folder)
    print("Autonomous loop public evidence verified")
