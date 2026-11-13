"""Render aggregate-only SPH PAC-head metrics and paired patient bootstrap intervals."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.benchmarkmax.pac import validate_pac_aggregate  # noqa: E402

METRICS = ("average_precision", "sensitivity")
COLORS = {
    "frozen_v45_p8_pac": "#355C7D",
    "logistic_regression": "#C46D25",
    "mlp": "#2A7F62",
}
MARKERS = {"frozen_v45_p8_pac": "o", "logistic_regression": "s", "mlp": "D"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _finite_interval(value: object, *, metric: str, model: str) -> tuple[float, float]:
    if (not isinstance(value, list) or len(value) != 2
            or any(type(item) not in (int, float) or not math.isfinite(item) for item in value)):
        raise ValueError(f"missing or invalid patient-cluster interval for {model} {metric}")
    low, high = float(value[0]), float(value[1])
    if low > high:
        raise ValueError(f"reversed patient-cluster interval for {model} {metric}")
    return low, high


def _comparison_for_model(
    report: dict[str, object], model_name: str
) -> tuple[dict[str, object], str]:
    comparison_key = (
        "logistic_regression_minus_frozen_v45_p8_pac"
        if model_name == "frozen_v45_p8_pac"
        else f"{model_name}_minus_frozen_v45_p8_pac"
    )
    try:
        comparison = report["paired_patient_cluster_bootstrap"]["comparisons"][comparison_key]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"aggregate lacks paired P8 comparison for {model_name}") from exc
    side = "ci95_a" if model_name == "frozen_v45_p8_pac" else "ci95_b"
    return comparison, side


def _figure_rows(report: dict[str, object]) -> list[dict[str, object]]:
    models = report.get("models")
    if not isinstance(models, dict) or not {
        "frozen_v45_p8_pac", "logistic_regression",
    }.issubset(models):
        raise ValueError("aggregate lacks the frozen P8 or logistic comparison model")
    mlp_names = sorted(
        (name for name in models if name.startswith("mlp_seed_")),
        key=lambda value: int(value.removeprefix("mlp_seed_")),
    )
    if len(mlp_names) != 5:
        raise ValueError("aggregate must report all five prespecified MLP seeds")
    ordered_names = ["frozen_v45_p8_pac", "logistic_regression", *mlp_names]
    rows = []
    for name in ordered_names:
        model = models[name]
        metrics = model.get("exploratory_holdout_metrics")
        if not isinstance(metrics, dict):
            raise ValueError(f"aggregate lacks holdout metrics for {name}")
        comparison, ci_side = _comparison_for_model(report, name)
        comparison_metrics = comparison.get("metrics")
        if not isinstance(comparison_metrics, dict):
            raise ValueError(f"aggregate lacks paired metrics for {name}")
        row: dict[str, object] = {
            "name": name,
            "label": (
                "Frozen V4.5 P8"
                if name == "frozen_v45_p8_pac"
                else "L2 logistic regression"
                if name == "logistic_regression"
                else f"MLP seed {name.removeprefix('mlp_seed_')}"
            ),
            "group": (
                name if name in COLORS else "mlp"
            ),
            "metrics": {},
        }
        for metric in METRICS:
            if metric not in metrics or metric not in comparison_metrics:
                raise ValueError(f"aggregate lacks {metric} for {name}")
            point = metrics[metric]
            if type(point) not in (int, float) or not math.isfinite(point):
                raise ValueError(f"invalid {metric} point estimate for {name}")
            interval = _finite_interval(
                comparison_metrics[metric].get(ci_side), metric=metric, model=name
            )
            if not interval[0] <= float(point) <= interval[1]:
                raise ValueError(f"point estimate falls outside its interval for {name} {metric}")
            row["metrics"][metric] = {"point": float(point), "ci95": interval}
        rows.append(row)
    return rows


def render_figure(report_path: Path, output_dir: Path) -> dict[str, str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.lines import Line2D
    from matplotlib.ticker import MultipleLocator

    report = json.loads(report_path.read_text(encoding="utf-8"))
    validate_pac_aggregate(report)
    rows = _figure_rows(report)
    cohort = report["cohort"]
    split = cohort["split_support"]["exploratory_holdout"]
    bootstrap = report["paired_patient_cluster_bootstrap"]
    if (split["records"] < 1 or split["positive_records"] < 1
            or bootstrap.get("method") != "paired unstratified percentile bootstrap"
            or bootstrap.get("unit") != "patient_id cluster; repeated ECGs sampled together"
            or bootstrap.get("replicates") != 2000):
        raise ValueError("aggregate has incompatible holdout or bootstrap context")
    job_id = str(report.get("execution", {}).get("slurm_job_id", ""))
    if not re.fullmatch(r"\d+", job_id):
        raise ValueError("aggregate lacks a numeric CEDIA SLURM job ID")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    figure, axes = plt.subplots(1, 2, figsize=(13.4, 6.2), sharey=True)
    y = np.arange(len(rows))
    titles = {"average_precision": "Average precision", "sensitivity": "Sensitivity"}
    for axis, metric in zip(axes, METRICS, strict=True):
        for index, row in enumerate(rows):
            values = row["metrics"][metric]
            point = values["point"]
            lower, upper = values["ci95"]
            group = row["group"]
            axis.errorbar(
                point,
                index,
                xerr=np.asarray([[point - lower], [upper - point]]),
                fmt=MARKERS[group],
                color=COLORS[group],
                ecolor=COLORS[group],
                markersize=5.5,
                markeredgecolor="#26343b",
                markeredgewidth=0.55,
                elinewidth=1.3,
                capsize=3,
                zorder=3,
            )
        axis.set_xlim(0.0, 1.0)
        axis.set_title(titles[metric], loc="left", weight="bold")
        axis.set_xlabel("Score")
        axis.xaxis.set_major_locator(MultipleLocator(0.2))
        axis.grid(axis="x", color="#d7dde0", linewidth=0.7, alpha=0.85)
        axis.spines[["top", "right"]].set_visible(False)
        axis.spines[["left", "bottom"]].set_color("#647179")
        axis.set_axisbelow(True)

    axes[0].set_yticks(y, [row["label"] for row in rows])
    axes[0].invert_yaxis()
    axes[1].tick_params(labelleft=False)
    legend = [
        Line2D([0], [0], marker=MARKERS[key], color="none", markerfacecolor=color,
               markeredgecolor="#26343b", markersize=6, label=label)
        for key, color, label in (
            ("frozen_v45_p8_pac", COLORS["frozen_v45_p8_pac"], "Frozen V4.5 P8"),
            ("logistic_regression", COLORS["logistic_regression"], "L2 logistic"),
            ("mlp", COLORS["mlp"], "Prespecified MLP seeds"),
        )
    ]
    figure.legend(
        handles=legend,
        loc="upper left",
        frameon=False,
        ncol=3,
        bbox_to_anchor=(0.17, 0.87),
    )
    figure.suptitle(
        "SPH PAC statement scores: frozen baseline and exploratory heads",
        x=0.17, y=0.97, ha="left", fontsize=14, weight="bold",
    )
    figure.text(
        0.17, 0.91,
        f"Previously observed SPH; {split['positive_records']} code-30 statements / "
        f"{split['records']:,} exploratory-holdout ECGs. Absence means statement not recorded.",
        fontsize=9, color="#34434a",
    )
    figure.text(
        0.17, 0.035,
        "Points and 95% patient-cluster percentile intervals (2,000 paired draws), "
        "conditional on fitted models. Not independent, clinical, or external validation.",
        fontsize=8.5, color="#34434a",
    )
    figure.subplots_adjust(left=0.21, right=0.98, top=0.79, bottom=0.13, wspace=0.25)

    output_dir.mkdir(parents=True, exist_ok=True)
    base = f"sph_pac_head_comparison_{job_id}"
    png_path = output_dir / f"{base}.png"
    pdf_path = output_dir / f"{base}.pdf"
    manifest_path = output_dir / f"{base}.figure_manifest.json"
    figure.savefig(
        png_path,
        dpi=220,
        facecolor="white",
        metadata={"Title": "SPH PAC head comparison", "Description": report["scope"]},
    )
    figure.savefig(
        pdf_path,
        facecolor="white",
        metadata={
            "Title": "SPH PAC head comparison",
            "Subject": report["scope"],
            "CreationDate": None,
            "ModDate": None,
        },
    )
    plt.close(figure)

    manifest = {
        "schema": "TITAN_V46_SPH_PAC_HEAD_FIGURE_V1",
        "source_aggregate": report_path.name,
        "source_aggregate_sha256": sha256_file(report_path),
        "renderer_sha256": sha256_file(Path(__file__).resolve()),
        "protocol_sha256": report["protocol"]["protocol_sha256"],
        "execution_commit": report["protocol"]["git_commit"],
        "cedia_slurm_job_id": job_id,
        "metrics": list(METRICS),
        "interval": {
            "confidence_level": 0.95,
            "method": bootstrap["method"],
            "unit": bootstrap["unit"],
            "replicates": bootstrap["replicates"],
        },
        "holdout_records": split["records"],
        "holdout_positive_records": split["positive_records"],
        "scope": report["scope"],
        "individual_records_exported": False,
        "record_level_scores_exported": False,
        "files": {
            png_path.name: sha256_file(png_path),
            pdf_path.name: sha256_file(pdf_path),
        },
    }
    with manifest_path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return {
        png_path.name: str(png_path),
        pdf_path.name: str(pdf_path),
        manifest_path.name: str(manifest_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    outputs = render_figure(args.report.resolve(), args.output_dir.resolve())
    print(json.dumps(outputs, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
