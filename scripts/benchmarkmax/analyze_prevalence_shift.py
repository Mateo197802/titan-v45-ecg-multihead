"""Project statement-level PPV under illustrative prevalence-only shifts."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

SCENARIOS = (0.001, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20)
ENDPOINTS = ("P6:AFIB", "P8:PAC", "P4:ASMI", "P4:LVH", "P4:IMI")


def project_ppv(prevalence, sensitivity, specificity):
    if any(not math.isfinite(v) or not 0 <= v <= 1
           for v in (prevalence, sensitivity, specificity)):
        raise ValueError("probabilities must be finite and between zero and one")
    true_positive_rate = prevalence * sensitivity
    predicted_positive_rate = true_positive_rate + (1 - prevalence) * (1 - specificity)
    return true_positive_rate / predicted_positive_rate if predicted_positive_rate else None


def analyze(source):
    if source.get("schema") != "TITAN_V46_SPH_OBSERVED_BASELINE_DIAGNOSTIC_V1":
        raise ValueError("unexpected source schema")
    if set(source["endpoints"]) != set(ENDPOINTS):
        raise ValueError("unexpected endpoint set")
    results = {}
    for name in ENDPOINTS:
        data = source["endpoints"][name]
        counts = data["frozen_decisions"]
        tp, tn, fp, fn = (counts[key] for key in ("tp", "tn", "fp", "fn"))
        if (any(type(value) is not int or value < 0 for value in (tp, tn, fp, fn))
                or tp + tn + fp + fn != data["records"]
                or tp + fn != data["positive_statements"]
                or tn + fp != data["negative_statements"]
                or data["records"] != source["source_records"] or not tp + fn or not tn + fp):
            raise ValueError(f"inconsistent population: {name}")
        prevalence = (tp + fn) / data["records"]
        if not math.isclose(prevalence, data["statement_prevalence"], abs_tol=1e-12):
            raise ValueError(f"inconsistent prevalence: {name}")
        sensitivity = tp / (tp + fn)
        specificity = tn / (tn + fp)
        results[name] = {
            "observed_records": data["records"],
            "observed_statement_prevalence": prevalence,
            "frozen_sensitivity": sensitivity,
            "frozen_specificity": specificity,
            "observed_ppv": tp / (tp + fp) if tp + fp else None,
            "projected_ppv_at_observed_prevalence": project_ppv(prevalence, sensitivity, specificity),
            "scenarios": [{"hypothetical_statement_prevalence": value,
                           "projected_ppv": project_ppv(value, sensitivity, specificity)}
                          for value in SCENARIOS],
        }
    return {
        "schema": "TITAN_V46_SPH_PREVALENCE_ONLY_PROJECTION_V1",
        "scope": "Mathematical sensitivity analysis from previously observed SPH statements, not external validation or disease-risk prediction.",
        "assumptions": ["Conditional sensitivity and specificity remain fixed as prevalence changes.",
                        "The annotation process and population case mix remain comparable.",
                        "Absence of an ECG statement is not adjudicated disease absence.",
                        "No uncertainty intervals are estimated for these hypothetical projections."],
        "endpoints": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    report = analyze(json.loads(raw))
    report["source_sha256"] = hashlib.sha256(raw).hexdigest()
    report["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
