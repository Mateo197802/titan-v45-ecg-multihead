"""Render fixed, aggregate-only figures from the SPH endpoint report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROFILE_COLORS = {"P6": "#147d73", "P8": "#d45545", "P4": "#bd8a16"}
ENDPOINT_ORDER = ("P6", "P8", "P4")


def _save(fig, directory, stem):
    png = directory / f"{stem}.png"
    pdf = directory / f"{stem}.pdf"
    fig.savefig(png, dpi=200, metadata={"Software": "TITAN V4.5 SPH aggregate report"})
    fig.savefig(
        pdf,
        metadata={"Creator": "TITAN V4.5 SPH aggregate report", "CreationDate": None, "ModDate": None},
    )
    plt.close(fig)
    return [png.name, pdf.name]


def _ordered_endpoints(report):
    rows = []
    for profile in ENDPOINT_ORDER:
        rows.extend(
            (profile, name, endpoint)
            for key, endpoint in report["endpoints"].items()
            for found_profile, name in [key.split(":", 1)]
            if found_profile == profile
        )
    return rows


def _plot_coverage(report, directory):
    flow = report["full_population_flow"]
    profiles = report["profile_flow"]
    fig, axis = plt.subplots(figsize=(8.5, 3.7), layout="constrained")
    names = list(ENDPOINT_ORDER)
    coverage = [profiles[name]["coverage"] for name in names]
    axis.barh(names, coverage, color=[PROFILE_COLORS[name] for name in names], height=0.56)
    for y, profile in enumerate(names):
        count = profiles[profile]["scored_records"]
        axis.text(coverage[y] + 0.012, y, f"{count:,} / {profiles[profile]['source_records']:,}",
                  va="center", fontsize=9)
    axis.set_xlim(0, 1.16)
    axis.set_xlabel("ECGs with scores / full metadata population")
    axis.set_title("SPH profile coverage")
    axis.grid(axis="x", alpha=0.2)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.tick_params(axis="y", length=0)
    footer = (
        f"Metadata {flow['source_metadata_records']:,} | archive {flow['archive_records']:,} | "
        f"technical exclusions {flow['technical_exclusions']:,} | "
        f"inference failures {flow['inference_failures']:,} | "
        f"missing signals {flow['missing_signal']:,} | quarantine not assessed"
    )
    fig.text(0.01, 0.01, footer, fontsize=8, ha="left")
    return _save(fig, directory, "sph_profile_coverage")


def _plot_endpoint_metrics(report, directory):
    endpoints = _ordered_endpoints(report)
    metrics = ("sensitivity", "specificity", "auroc")
    labels = [
        f"{profile}:{name}  (+{endpoint['scored_positive']:,}/-{endpoint['scored_negative']:,})"
        for profile, name, endpoint in endpoints
    ]
    fig, axes = plt.subplots(1, 3, figsize=(15, max(6, 0.42 * len(endpoints) + 2)),
                             sharey=True, layout="constrained")
    y_positions = list(range(len(endpoints)))
    for axis, metric in zip(axes, metrics, strict=True):
        for y, (profile, _name, endpoint) in enumerate(endpoints):
            value = endpoint["metrics"].get(metric)
            if value is None:
                continue
            interval = endpoint["cluster_bootstrap_ci95"].get(metric, {})
            low, high = interval.get("low"), interval.get("high")
            xerr = None if low is None or high is None else [[value - low], [high - value]]
            axis.errorbar(value, y, xerr=xerr, fmt="o", color=PROFILE_COLORS[profile],
                          markersize=4, capsize=2, linewidth=1)
        axis.set_xlim(0, 1)
        axis.set_xlabel(metric.replace("_", " ").title())
        axis.grid(axis="x", alpha=0.2)
        axis.spines[["top", "right"]].set_visible(False)
        axis.set_yticks(y_positions, labels if axis is axes[0] else [])
        axis.invert_yaxis()
    fig.suptitle("SPH statement-level endpoint metrics")
    fig.supxlabel("Point estimate and 95% patient-component bootstrap interval; no pooled profile score")
    return _save(fig, directory, "sph_endpoint_metrics")


def _plot_duplicate_sensitivity(report, directory):
    endpoints = _ordered_endpoints(report)
    fig, axis = plt.subplots(figsize=(9, max(5.5, 0.36 * len(endpoints) + 1.5)),
                             layout="constrained")
    y_positions = list(range(len(endpoints)))
    for y, (_profile, _name, endpoint) in enumerate(endpoints):
        primary = endpoint["metrics"].get("f1")
        sensitivity = endpoint["discordant_exact_duplicate_sensitivity"]
        alternate = (sensitivity.get("metrics") or {}).get("f1")
        for offset, value, interval, color, marker in (
            (-0.12, primary, endpoint["cluster_bootstrap_ci95"].get("f1", {}), "#147d73", "o"),
            (0.12, alternate, (sensitivity.get("cluster_bootstrap_ci95") or {}).get("f1", {}),
             "#d45545", "s"),
        ):
            if value is None:
                continue
            low, high = interval.get("low"), interval.get("high")
            xerr = None if low is None or high is None else [[value - low], [high - value]]
            axis.errorbar(value, y + offset, xerr=xerr, fmt=marker, color=color,
                          markersize=4, capsize=2, linewidth=1)
    axis.set_xlim(0, 1)
    axis.set_yticks(y_positions, [f"{profile}:{name}" for profile, name, _ in endpoints])
    axis.invert_yaxis()
    axis.set_xlabel("F1 and 95% patient-component bootstrap interval")
    axis.set_title("Endpoint-discordant exact-duplicate sensitivity")
    axis.grid(axis="x", alpha=0.2)
    axis.spines[["top", "right"]].set_visible(False)
    axis.plot([], [], "o", color="#147d73", label="Primary: all rows retained")
    axis.plot([], [], "s", color="#d45545", label="Sensitivity: discordant exact groups excluded")
    axis.legend(frameon=False, loc="lower right", fontsize=8)
    axis.text(0.01, -0.09,
              "Endpoint-specific exclusion counts and denominators are in the aggregate JSON.",
              transform=axis.transAxes, fontsize=8)
    return _save(fig, directory, "sph_duplicate_sensitivity")


def plot_sph_aggregate(report, output_dir):
    if report.get("schema") != "TITAN_V45_SPH_ENDPOINT_RESULTS_V1":
        raise ValueError("unexpected SPH aggregate report schema")
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    names = []
    names.extend(_plot_coverage(report, directory))
    names.extend(_plot_endpoint_metrics(report, directory))
    names.extend(_plot_duplicate_sensitivity(report, directory))
    return {"files": names, "matplotlib_version": matplotlib.__version__}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    report = json.loads(args.input.read_text(encoding="utf-8"))
    result = plot_sph_aggregate(report, args.output_dir)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
