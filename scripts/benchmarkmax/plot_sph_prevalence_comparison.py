"""Render aggregate-only paired error differences against the SPH prevalence baseline."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ENDPOINT_ORDER = ("P4:ASMI", "P4:IMI", "P4:LVH", "P6:PVC", "P6:RBBB", "P8:PAC")
METRICS = (
    ("brier", "Brier score"),
    ("ece", "10-bin ECE"),
    ("log_loss", "Log-loss"),
)
COMPARISONS = (
    ("raw_minus_prevalence", "Raw V4.5 - prevalence", "#1f6d88", "o"),
    ("platt_minus_prevalence", "Platt - prevalence", "#c96a2b", "s"),
)


def _plot_data(report_path: Path) -> tuple[dict, list[str], list[str]]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    endpoints = report.get("endpoints")
    if (
        report.get("schema") != "TITAN_V46_SPH_B1_PREVALENCE_COMPARISON_V1"
        or not isinstance(endpoints, dict)
        or set(endpoints) != set(ENDPOINT_ORDER)
    ):
        raise ValueError("renderer requires the complete aggregate-only prevalence comparison")

    labels = []
    for name in ENDPOINT_ORDER:
        endpoint = endpoints[name]
        support = endpoint.get("source_support", {})
        try:
            labels.append(
                f"{name.replace(':', ' ')}  (+{support['positive_records']:,} ECGs; "
                f"{support['positive_patients']:,} patients)"
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"aggregate endpoint support is incomplete for {name}") from error

        comparisons = endpoint.get("patient_cluster_bootstrap_deltas", {}).get("comparisons", {})
        for comparison, _, _, _ in COMPARISONS:
            metrics = comparisons.get(comparison, {})
            for metric, _ in METRICS:
                result = metrics.get(metric, {})
                interval = result.get("ci95")
                point = result.get("point_difference_first_minus_second")
                if (
                    not isinstance(interval, list)
                    or len(interval) != 2
                    or isinstance(point, bool)
                    or not isinstance(point, (int, float))
                ):
                    raise ValueError(f"aggregate {name} {comparison} {metric} CI95 is missing")
                values = [float(point), *(float(value) for value in interval)]
                if not all(math.isfinite(value) for value in values) or values[1] > values[2]:
                    raise ValueError(f"aggregate {name} {comparison} {metric} estimate is invalid")

    return report, labels, list(ENDPOINT_ORDER)


def render_figure(report_path: Path, output_dir: Path) -> tuple[str, str]:
    report, labels, ordered = _plot_data(report_path)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.ticker import MaxNLocator

    endpoints = report["endpoints"]
    positions = np.arange(len(ordered))
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5})
    figure, axes = plt.subplots(3, 2, figsize=(14.8, 10.5), sharey="row")

    for row, (metric, metric_title) in enumerate(METRICS):
        for column, (comparison, comparison_title, color, marker) in enumerate(COMPARISONS):
            axis = axes[row, column]
            points, lower, upper = [], [], []
            for name in ordered:
                result = endpoints[name]["patient_cluster_bootstrap_deltas"]["comparisons"][
                    comparison
                ][metric]
                points.append(float(result["point_difference_first_minus_second"]))
                low, high = (float(value) for value in result["ci95"])
                lower.append(low)
                upper.append(high)
            values = np.asarray(points)
            low_values = np.asarray(lower)
            high_values = np.asarray(upper)
            axis.errorbar(
                values,
                positions,
                xerr=np.vstack((values - low_values, high_values - values)),
                fmt=marker,
                markersize=5.2,
                color=color,
                ecolor=color,
                elinewidth=1.25,
                capsize=3.5,
                markeredgecolor="#263238",
                markeredgewidth=0.65,
                linestyle="none",
            )
            bounds = [*lower, *upper]
            span = max(bounds) - min(bounds)
            padding = max(span * 0.12, max(abs(value) for value in bounds) * 0.08, 1e-6)
            axis.set_xlim(min(0.0, min(bounds) - padding), max(0.0, max(bounds) + padding))
            axis.axvline(0, color="#49545a", linewidth=1.0, zorder=0)
            axis.set_title(f"{metric_title}: {comparison_title}", loc="left", weight="bold")
            axis.set_xlabel("Delta (method - prevalence); lower is better")
            axis.xaxis.set_major_locator(MaxNLocator(5))
            axis.grid(axis="x", color="#d7dde0", linewidth=0.7, alpha=0.8)
            axis.spines[["top", "right"]].set_visible(False)
            axis.spines[["left", "bottom"]].set_color("#647179")
            axis.set_yticks(positions, labels)
            if column == 1:
                axis.tick_params(labelleft=False)
        axes[row, 0].invert_yaxis()
    figure.suptitle(
        "SPH probability error versus a prevalence-only baseline",
        x=0.02,
        y=0.99,
        ha="left",
        fontsize=14,
        weight="bold",
    )
    figure.text(
        0.02,
        0.945,
        "Previously observed SPH; exploratory only. Each panel has its own x range; exact deltas and 95% patient-cluster CIs are tabulated.",
        fontsize=9,
        color="#34434a",
    )
    figure.text(
        0.02,
        0.025,
        "Negative deltas mean lower error than prevalence. Intervals condition on fixed fold estimates; no refit or multiple-comparison adjustment. Not independent or clinical validation.",
        fontsize=8.2,
        color="#34434a",
    )
    figure.subplots_adjust(left=0.245, right=0.99, top=0.90, bottom=0.12, wspace=0.25, hspace=0.38)

    output_dir.mkdir(parents=True, exist_ok=True)
    names = ("sph_b1_prevalence_comparison.png", "sph_b1_prevalence_comparison.pdf")
    figure.savefig(output_dir / names[0], dpi=220, facecolor="white")
    figure.savefig(output_dir / names[1], dpi=220, facecolor="white")
    plt.close(figure)
    return names


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    names = render_figure(args.report, args.output_dir)
    print(f"Rendered aggregate-only SPH prevalence figure: {', '.join(names)}")


if __name__ == "__main__":
    main()
