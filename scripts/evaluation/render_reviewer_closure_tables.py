"""Render deterministic tables from native-hash-matched closure aggregates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from verify_reviewer_november_delivery import protected_path
from verify_reviewer_scientific_closure import JOBS, PUBLIC_NAMES

TABLES = "VERIFIED_ENDPOINT_AND_ROUTE_TABLES.md"
ENDPOINTS = ("NSR", "PAC", "Flutter", "Paced", "LBBB", "2AVB", "3AVB", "LQTS", "ALMI", "ILMI", "LAE")
METRIC_COLUMNS = ("Sens", "Spec", "PPV", "NPV", "F1", "AUROC", "AP")


def table(header, rows):
    def row(values):
        return "| " + " | ".join(str(v).replace("|", r"\|") for v in values) + " |"

    return "\n".join([row(header), row(["---"] * len(header)), *(row(r) for r in rows)])


def fmt(value):
    return "NA" if value is None else f"{value:.4f}"


def interval(bounds):
    return "NA" if bounds is None else "[" + ", ".join(map(fmt, bounds)) + "]"


def states(counts):
    return "; ".join(f"{k}: {counts[k]}" for k in sorted(counts)) or "none"


def metrics(d):
    return tuple(fmt(d.get(k)) for k in ("recall", "specificity", "precision", "npv", "f1", "auroc", "average_precision"))


def confusion(d):
    return "/".join(str(d[k]) for k in ("tp", "fn", "fp", "tn")) if d else "NA"


def estimates(r):
    values = {"recall": r.get("positive_reference_sensitivity"), **r.get("metrics", {}), **r.get("ranking", {})}
    return (r["eligible_ecgs"], states(r["reference_states"]), r["known_scored_ecgs"],
            confusion(r.get("descriptive_confusion")), *metrics(values), r["status"])


def render_ludb(ludb):
    joint = ludb["joint_selective"]
    count = joint["routes"]
    n = joint["denominator_all_eligible"]
    denom, errors = joint["opportunity_denominators"], joint["wrong_opportunities"]
    cis = joint["cluster_intervals"]
    rows = []
    for name, key in (("Coverage", "coverage_all_eligible"), ("Abstention", "abstention_all_eligible"),
                      ("Baseline error", "risk_baseline"), ("Accepted error", "risk_accepted"),
                      ("Abstained baseline counterfactual error", "risk_abstained_counterfactual"),
                      ("AURC, jointly scored", "aurc_scored")):
        if key.startswith("risk_"):
            route = key.removeprefix("risk_")
            nd = f"{errors[route]} / {denom[route]} endpoint opportunities"
        elif key == "aurc_scored":
            nd = f'{joint["denominator_scored_jointly"]} ECGs in curve'
        else:
            route = "accepted" if key.startswith("coverage_") else "abstained"
            nd = f"{count.get(route, 0)} / {n} ECGs"
        rows.append((name, nd, fmt(joint[key]), interval(cis[key]["bounds"]), cis[key]["valid"]))
    yield "## LUDB: actual joint routes and risk"
    yield table(("Measure", "Denominator", "Estimate", "Cluster 95% interval", "Valid draws"), rows)
    yield f"Technical non-scoring: {count.get('technical_unscored', 0)}/{n}. No referral or human review."
    yield table(("Reference principal rhythm", "Eligible", "Accepted", "Abstained", "Technical", "Abstention fraction"),
                ((r, sum(c.values()), c.get("accepted", 0), c.get("abstained", 0), c.get("technical_unscored", 0),
                  fmt(c.get("abstained", 0) / sum(c.values())))
                 for r, c in sorted(ludb["routing_by_principal_rhythm"].items())))
    disposition = ("all_reference_positives", "emitted_tp", "emitted_fn", "abstained_positive_no_output",
                   "abstained_baseline_counterfactual_fn", "technical_unscored_positive_no_output")
    yield table(("P8/P4 endpoint", "Positive refs", "Emitted TP", "Emitted FN", "Withheld positive",
                 "Withheld baseline FN", "Technical positive"),
                ((k, *(e["joint_positive_disposition"].get(f, 0) for f in disposition))
                 for k, e in sorted(ludb["endpoints"].items()) if "joint_positive_disposition" in e))
    yield "## LUDB: matched contrasts and per-endpoint operating points"
    contrasts = [*sorted(ludb["matched_restricted_contrast"].items()),
                 ("P8/P4 selective", ludb["matched_selective_contrast"])]
    yield table(("Contrast", "Common evaluated endpoints", "Subset", "Macro-F1", "Mean binary accuracy"),
                ((name, ", ".join(c["matched_endpoints"]) or "none", subset, fmt(m["f1"]), fmt(m["accuracy"]))
                 for name, c in contrasts for subset, m in c["means"].items()))
    yield (
        "Rows in abstained or technical strata describe baseline counterfactual calls, not predictions emitted by "
        "the joint policy. Sensitivity with only positive references is descriptive."
    )
    columns = ("Endpoint", "Subset", "ECGs", "Reference states", "Known scored", "TP/FN/FP/TN", *METRIC_COLUMNS, "Status")
    yield table(columns, ((name, subset, *estimates(r)) for name, e in sorted(ludb["endpoints"].items())
                          for subset, r in e["estimates"].items()))


def render_other(ludb, ptbxl, ptb, readout):
    yield "## Reference coverage and supplementary results"
    yield (
        "PTB-XL source and cached references do not imply clinical ground truth. Subject counts per state are unique "
        "within state and must not be summed across states. Unmapped and proxy labels do not count as negatives."
    )
    yield table(("Endpoint", "LUDB references (200 ECGs)", "PTB-XL cached references (6,205 ECGs)",
                 "PTB-XL cached source subjects by state"),
                ((e, states(ludb["auxiliary_and_other"][e]["released_auxiliary"]["all_eligible"]["reference_states"]),
                  states(ptbxl["endpoint_support"][e]["P4_scoreable"]["ECGs"]),
                  states(ptbxl["endpoint_support"][e]["P4_scoreable"]["source_subjects"])) for e in ENDPOINTS))
    yield (
        "PTB Diagnostic compares exact clinical territory with explicit healthy controls. PPV and NPV apply only "
        "to the enriched reference subset. Rank-only rows have no operational call."
    )
    yield table(("Territory", "Score source", "ECGs", "Reference states", "Known scored", "TP/FN/FP/TN",
                 *METRIC_COLUMNS, "Status"),
                ((e, model, *estimates(r)) for e, methods in sorted(ptb["endpoints"].items()) for model, r in methods.items()))
    yield (
        "PTB-XL cached V3AG rhythm: pooled rank estimates are descriptive. Held operating-point estimates appear "
        "only when both split supports passed. None of these operating points belongs to the published specialists."
    )
    rows = []
    for e, r in sorted(readout["endpoints"].items()):
        h, threshold = r["held_fold_9"], r["new_operating_point"]
        p = r["pooled_descriptive_rank"].get("rank_metrics", {})
        m = h.get("metrics", {})
        rows.append((e, states(h["reference_states"]), f'{h["positive_subjects"]} / {h["control_subjects"]}',
                     ("NA" if threshold is None else f"{threshold:.8g}"), confusion(m), *metrics(m),
                     fmt(p.get("auroc")), fmt(p.get("average_precision"))))
    yield table(("Endpoint", "Held references", "Held positive / control subjects", "New threshold",
                 "Held TP/FN/FP/TN", *METRIC_COLUMNS, "Pooled AUROC", "Pooled AP"), rows)


def render(content):
    sections = [
        "# Verified endpoint and route tables",
        ("Generated from the sealed CEDIA aggregates. NA means undefined, unassessed, or no applicable operating "
         "point, not zero. See the aggregates for full precision, cluster intervals where estimable, and calibration. "
         "No individual records are reproduced here."),
        *render_ludb(content["evaluate"]),
        *render_other(content["evaluate"], content["ptbxl_support"], content["ptb_evaluate"],
                      content["ptbxl_rhythm_evaluate"]),
    ]
    return ("\n\n".join(sections) + "\n").encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = args.data_dir.resolve()
    receipt = json.loads(protected_path(root, "native_closure_verification.json").read_bytes())
    if (not receipt["science_consistency_verified"] or receipt["record_level_export_performed"]
            or receipt["public_files"] != PUBLIC_NAMES
            or any((receipt["scheduler"][j]["state"], receipt["scheduler"][j]["exit_code"]) != ("COMPLETED", "0:0")
                   for j in JOBS.values())):
        raise ValueError("native verification is incomplete")
    content = {}
    for key, filename in PUBLIC_NAMES.items():
        data = protected_path(root, filename).read_bytes()
        if hashlib.sha256(data).hexdigest() != receipt["public_sha256"][key]:
            raise ValueError(f"input differs from the native seal: {filename}")
        content[key] = json.loads(data)
    rendered = render(content)
    with args.output.open("xb") as stream:
        stream.write(rendered)


if __name__ == "__main__":
    main()
