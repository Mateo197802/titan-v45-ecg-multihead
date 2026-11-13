"""Explain observed controller decisions without changing the frozen search."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def diagnose(folder):
    state = json.loads((folder / "ITERATION_HYPOTHESES_AND_DECISIONS.json").read_bytes())
    with (folder / "CLASSWISE_ERROR_EVOLUTION.csv").open(newline="", encoding="utf-8") as stream:
        points = defaultdict(list)
        for row in csv.DictReader(stream):
            points[row["fit"]].append(row)
    for cycle in state["cycles"]:
        n = cycle["number"]
        prefix = f"{n:02d}-"
        fits = {k: r for k, r in state["verified_fits"].items() if k.startswith(prefix)}
        arms = {}
        for k, r in fits.items():
            failed = [e for e, g in r["guards"].items() if not g["pass"]]
            endpoint = {x["scope"]: {key: x[key] for key in ("recall", "precision", "average_precision", "fp", "fn")}
                        for x in points[k] if x["endpoint"] == cycle["endpoint"]}
            arms[k] = {"failed_code_guards": failed, "endpoint_by_scope": endpoint,
                       "code_f1": r["summary"]["f1"], "code_ap": r["summary"]["average_precision"]}
        yield {"cycle": n, "endpoint": cycle["endpoint"], "anchor": cycle["anchor"],
               "decision": cycle["decision"], "fit_diagnostics": arms}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder", type=Path)
    print(json.dumps(list(diagnose(p.parse_args().folder)), indent=2))
