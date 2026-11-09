"""Render a concise statement-level SPH table from the verified aggregate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def pct(value):
    return "NA" if value is None else f"{100 * value:.2f}%"


def render(report):
    if report.get("schema") != "TITAN_V45_SPH_ENDPOINT_RESULTS_V1":
        raise ValueError("expected SPH aggregate")
    flow = report["full_population_flow"]
    lines = [
        "# SPH statement-level transfer results",
        "",
        "These are ECG-statement comparisons, not clinical diagnoses or incident disease.",
        "An absent statement is not adjudicated absence of disease. Historical training",
        "lineage is incomplete, so full independence is not certified.",
        "",
        f"Scored ECG: {flow['scored_records']:,} / {flow['source_metadata_records']:,}; "
        f"technical exclusions: {flow['technical_exclusions']}; inference failures: {flow['inference_failures']}.",
        "Quarantine was not assessed. Patient-component percentile intervals use 2,000 replicates.",
        "",
        "| Endpoint | Positive / negative statements | Sensitivity | Specificity | F1 | F1 95% CI | AUROC |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, endpoint in report["endpoints"].items():
        metric = endpoint["metrics"]
        interval = endpoint["cluster_bootstrap_ci95"].get("f1", {})
        ci = f"{pct(interval.get('low'))} to {pct(interval.get('high'))}"
        lines.append(f"| {name} | {endpoint['scored_positive']:,} / {endpoint['scored_negative']:,} | "
                     f"{pct(metric['sensitivity'])} | {pct(metric['specificity'])} | {pct(metric['f1'])} | "
                     f"{ci} | {pct(metric['auroc'])} |")
    lines.extend([
        "",
        "P4 F1 and P8 PAC results must not be hidden or compared directly with",
        "historical balanced panels. NSR, 1AVB and ISC_ have no primary compatible",
        "SPH reference in this protocol; no pooled full-profile accuracy is reported.",
        "The [full aggregate](../../outputs/results/external_sph/sph_aggregate_normalized_32669.json)",
        "contains confusion counts, predictive values, calibration metrics, valid",
        "and invalid bootstrap draws, and duplicate-sensitivity analyses. The",
        "[independent point check](../../outputs/results/external_sph/sph_independent_points_32672.json)",
        "recomputes point metrics from restricted inputs. A separate",
        "[bootstrap check](../../outputs/results/external_sph/sph_independent_bootstrap_32677.json)",
        "reproduces six binary-metric intervals, including F1. The separate",
        "[score-interval check](../../outputs/results/external_sph/sph_independent_score_bootstrap_32728.json)",
        "reproduces AUROC, average precision, Brier and ECE intervals for all",
        "14 endpoints, including duplicate sensitivity. Both checks reuse the same",
        "seeded draws and are computational checks, not new independent cohorts.",
        "",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.write_text(render(json.loads(args.input.read_text(encoding="utf-8"))), encoding="utf-8")


if __name__ == "__main__":
    main()
