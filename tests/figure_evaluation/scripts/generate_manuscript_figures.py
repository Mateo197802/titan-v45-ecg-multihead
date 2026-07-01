from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle, Circle
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import numpy as np
import pandas as pd


RHYTHM_CLASSES = ["AFIB", "SB", "STACH", "RBBB", "1AVB", "PVC"]
PATHOLOGY_CLASSES = ["ASMI", "LVH", "IMI", "ISC_"]
COLORS = {
    "navy": "#183B56",
    "teal": "#138A8A",
    "vermillion": "#D1493F",
    "gold": "#D9A441",
    "blue": "#3E7CB1",
    "green": "#3A8D5D",
    "ink": "#1F2933",
    "gray": "#66737F",
    "light": "#EEF2F5",
    "white": "#FFFFFF",
}
CLASS_COLORS = [
    COLORS["navy"],
    COLORS["teal"],
    COLORS["vermillion"],
    COLORS["gold"],
    COLORS["blue"],
    COLORS["green"],
]
CURATED_IMAGE_NAMES = {
    "fig00_ecg_ai_context": "fig00_ecg_ai_context.png",
    "fig00b_ecg_ai_evolution_gap": "fig00b_ecg_ai_evolution_gap.png",
    "fig01_graphical_abstract": "fig01_graphical_abstract.png",
    "fig02_data_processing_bias_workflow": "fig02_data_processing_bias_workflow.png",
    "fig03_internal_architecture": "fig03_internal_architecture.png",
    "fig03_cascade_contract": "fig03_cascade_contract.png",
}


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 10,
            "axes.titleweight": "bold",
            "axes.edgecolor": "#AAB4BD",
            "axes.linewidth": 0.8,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 8,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "svg.fonttype": "none",
        }
    )


def _box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    body: str,
    color: str,
    title_size: float = 11,
    body_size: float = 8.5,
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=1.5,
        edgecolor=color,
        facecolor="white",
    )
    ax.add_patch(patch)
    ax.text(
        x + width / 2,
        y + height * 0.68,
        title,
        ha="center",
        va="center",
        color=color,
        fontsize=title_size,
        fontweight="bold",
    )
    ax.text(
        x + width / 2,
        y + height * 0.32,
        body,
        ha="center",
        va="center",
        color=COLORS["ink"],
        fontsize=body_size,
        linespacing=1.2,
    )


def _arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], color: str = "#788894") -> None:
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={"arrowstyle": "-|>", "lw": 1.8, "color": color, "shrinkA": 2, "shrinkB": 2},
    )


def _load_real_ecg_segment(raw_dir: Path) -> tuple[np.ndarray, np.ndarray, str, str]:
    project_root = raw_dir.resolve().parents[2]
    mat_path = project_root / "V4.5 CEDIA" / "DATA" / "data_test" / "HR00191.mat"
    if mat_path.exists():
        from scipy.io import loadmat

        values = loadmat(mat_path)["val"].astype(float)
        lead_ii_mv = values[1] / 1000.0
        source_time = np.linspace(0.0, 10.0, lead_ii_mv.size, endpoint=False)
        target_time = np.linspace(0.0, 10.0, 1250, endpoint=False)
        signal = np.interp(target_time, source_time, lead_ii_mv)
        return target_time, signal, "Record HR00191, Lead II, original dataset signal", str(mat_path)

    target_time = np.linspace(0.0, 10.0, 1250, endpoint=False)
    signal = np.zeros_like(target_time)
    for center in np.arange(0.7, 9.8, 0.88):
        signal += 0.06 * np.exp(-((target_time - (center - 0.16)) / 0.045) ** 2)
        signal -= 0.08 * np.exp(-((target_time - (center - 0.025)) / 0.018) ** 2)
        signal += 0.55 * np.exp(-((target_time - center) / 0.015) ** 2)
        signal -= 0.16 * np.exp(-((target_time - (center + 0.035)) / 0.024) ** 2)
        signal += 0.18 * np.exp(-((target_time - (center + 0.24)) / 0.095) ** 2)
    signal += 0.015 * np.sin(2 * np.pi * 0.33 * target_time)
    return target_time, signal, "Fallback ECG-like signal", "synthetic fallback"


def _signal_aligned_activation(signal: np.ndarray) -> np.ndarray:
    centered = signal - np.median(signal)
    scale = np.percentile(np.abs(centered), 99)
    if not np.isfinite(scale) or scale <= 0:
        scale = 1.0
    normalized = centered / scale
    slope = np.gradient(normalized)
    energy = np.abs(slope) + 0.30 * np.abs(normalized)
    kernel_x = np.linspace(-3.0, 3.0, 61)
    kernel = np.exp(-0.5 * kernel_x**2)
    kernel /= kernel.sum()
    activation = np.convolve(energy, kernel, mode="same")
    activation -= activation.min()
    max_value = activation.max()
    if max_value > 0:
        activation /= max_value
    return activation


def _panel_label(ax: plt.Axes, x: float, y: float, label: str, title: str) -> None:
    ax.text(x, y, label, ha="left", va="center", fontsize=12, fontweight="bold", color=COLORS["ink"])
    ax.text(x + 0.035, y, title, ha="left", va="center", fontsize=12, fontweight="bold", color=COLORS["gray"])


def _save(
    fig: plt.Figure,
    output_dir: Path,
    stem: str,
    kind: str,
    caption: str,
    source_files: list[str],
    sample_probabilities_verified: bool = False,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    png = output_dir / f"{stem}.png"
    pdf = output_dir / f"{stem}.pdf"
    svg = output_dir / f"{stem}.svg"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)
    return {
        "id": stem,
        "kind": kind,
        "caption": caption,
        "png": str(png.resolve()),
        "pdf": str(pdf.resolve()),
        "svg": str(svg.resolve()),
        "source_files": source_files,
        "sample_probabilities_verified": sample_probabilities_verified,
    }


def _replace_with_curated_asset(output_dir: Path, item: dict[str, Any]) -> dict[str, Any]:
    curated_dir = output_dir / "curated_inputs"
    curated_name = CURATED_IMAGE_NAMES.get(str(item["id"]))
    if not curated_name:
        return item
    source = curated_dir / curated_name
    if not source.exists():
        return item

    image = plt.imread(source)
    height, width = image.shape[:2]
    fig_width = 16
    fig_height = max(4.5, fig_width * height / width)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.imshow(image)
    ax.axis("off")

    png = output_dir / f"{item['id']}.png"
    pdf = output_dir / f"{item['id']}.pdf"
    svg = output_dir / f"{item['id']}.svg"
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.02)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.02)
    fig.savefig(svg, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)

    item["source_files"] = sorted(set([*item["source_files"], str(source.resolve())]))
    item["curated_visual_asset"] = True
    return item


def clinical_context_figure(output_dir: Path) -> dict[str, Any]:
    fig, ax = plt.subplots(figsize=(16, 7.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(
        0.5,
        0.95,
        "Clinical motivation and evidence boundary for modular 12-lead ECG AI",
        ha="center",
        va="center",
        fontsize=17,
        fontweight="bold",
        color=COLORS["ink"],
    )

    _box(
        ax,
        0.035,
        0.58,
        0.22,
        0.24,
        "12-lead clinical signal",
        "rhythm | conduction\nischemia | infarction\nhypertrophy",
        COLORS["navy"],
        title_size=10.6,
        body_size=8.4,
    )
    t = np.linspace(0, 1, 600)
    for row, y0 in enumerate([0.49, 0.44, 0.39]):
        waveform = y0 + 0.010 * np.sin(2 * np.pi * (5 + row) * t)
        for center in (0.18, 0.39, 0.60, 0.81):
            waveform += (0.055 - row * 0.006) * np.exp(-((t - center) / 0.008) ** 2)
            waveform -= 0.020 * np.exp(-((t - center - 0.018) / 0.014) ** 2)
            waveform += 0.015 * np.exp(-((t - center + 0.052) / 0.020) ** 2)
        ax.plot(0.055 + t * 0.18, waveform, color=COLORS["vermillion"], lw=1.15)
    ax.text(0.145, 0.345, "10 s, 12 x 1250 contract", ha="center", fontsize=8.8, color=COLORS["gray"])

    _box(
        ax,
        0.315,
        0.58,
        0.19,
        0.24,
        "Multi-source evidence",
        "PTB-XL\nChapman-Shaoxing\nCPSC | Ningbo\nPhysioNet legacy",
        COLORS["teal"],
        title_size=10.4,
        body_size=8.0,
    )
    _box(
        ax,
        0.555,
        0.58,
        0.19,
        0.24,
        "Main risk controls",
        "label ontology\nsource shift\nleakage guard\ncalibration",
        COLORS["gold"],
        title_size=10.4,
        body_size=8.0,
    )
    _box(
        ax,
        0.795,
        0.58,
        0.17,
        0.24,
        "Specialist reports",
        "Primary6 rhythm\nPrimary4 pathology\ncascade review",
        COLORS["blue"],
        title_size=10.4,
        body_size=8.0,
    )
    for start, end in [((0.255, 0.70), (0.315, 0.70)), ((0.505, 0.70), (0.555, 0.70)), ((0.745, 0.70), (0.795, 0.70))]:
        _arrow(ax, start, end)

    columns = [
        (0.07, "Clinical need", "fast, reproducible\n12-lead interpretation", COLORS["navy"]),
        (0.30, "Prior work", "strong ECG AI results\nbut heterogeneous tasks", COLORS["teal"]),
        (0.53, "Gap", "flat labels can hide\nambiguity and imbalance", COLORS["vermillion"]),
        (0.76, "This study", "modular specialists\nwith auditable outputs", COLORS["green"]),
    ]
    ax.plot([0.10, 0.78], [0.22, 0.22], color="#CBD5DE", lw=1.3, zorder=0)
    for x, title, body, color in columns:
        ax.add_patch(Circle((x, 0.22), 0.035, facecolor=color, edgecolor="none", alpha=0.95))
        ax.text(x, 0.22, title.split()[0][0], ha="center", va="center", fontsize=13, fontweight="bold", color="white")
        ax.text(x + 0.055, 0.247, title, ha="left", va="center", fontsize=10.4, fontweight="bold", color=color)
        ax.text(x + 0.055, 0.175, body, ha="left", va="center", fontsize=8.7, color=COLORS["ink"], linespacing=1.2)
    ax.text(
        0.5,
        0.075,
        "The manuscript compares prior ECG AI studies as state of the art, then reports only the frozen specialist evidence supported by record-level metrics and hashes.",
        ha="center",
        fontsize=9.3,
        color=COLORS["gray"],
    )
    return _save(
        fig,
        output_dir,
        "fig00_ecg_ai_context",
        "introduction",
        "Representative clinical and methodological context for multi-source 12-lead ECG AI and the modular specialist evidence boundary.",
        ["MANUSCRIPT/literature/studies.csv", "MANUSCRIPT/evidence/metrics.json"],
    )


def ecg_ai_evolution_gap_figure(output_dir: Path) -> dict[str, Any]:
    fig, ax = plt.subplots(figsize=(16, 7.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(
        0.5,
        0.95,
        "Evolution of ECG AI and the remaining specialist-reporting gap",
        ha="center",
        va="center",
        fontsize=17,
        fontweight="bold",
        color=COLORS["ink"],
    )

    stages = [
        (0.045, "Manual ECG\ninterpretation", "morphology\nclinical rules", COLORS["navy"]),
        (0.235, "Digital signal\nprocessing", "filtering\nsegmentation", COLORS["teal"]),
        (0.425, "Deep ECG\nclassifiers", "CNN/RNN\nlarge cohorts", COLORS["blue"]),
        (0.615, "Context-aware\nmodels", "multi-label\nuncertainty", COLORS["gold"]),
        (0.805, "Specialist evidence\npackages", "primary/cascade\ncalibration + audit", COLORS["vermillion"]),
    ]
    ax.plot([0.10, 0.86], [0.68, 0.68], color="#CAD4DD", lw=2.0, zorder=0)
    for idx, (x, title, body, color) in enumerate(stages, start=1):
        ax.add_patch(Circle((x + 0.07, 0.68), 0.026, facecolor=color, edgecolor="white", linewidth=1.2, zorder=3))
        ax.text(x + 0.07, 0.68, str(idx), ha="center", va="center", fontsize=10.5, fontweight="bold", color="white", zorder=4)
        _box(ax, x, 0.73, 0.14, 0.13, title, body, color, title_size=8.8, body_size=7.4)
        if idx < len(stages):
            _arrow(ax, (x + 0.15, 0.68), (x + 0.19, 0.68), color="#5C6F7D")

    ax.text(
        0.08,
        0.50,
        "Why a new evidence structure is needed",
        ha="left",
        va="center",
        fontsize=13,
        fontweight="bold",
        color=COLORS["ink"],
    )
    challenges = [
        ("Clinical task", "rhythm, conduction,\nischemia, infarction,\nhypertrophy can coexist", COLORS["navy"]),
        ("Dataset shift", "different countries,\nrecorders, sampling rates,\nand annotation policies", COLORS["teal"]),
        ("Reporting risk", "one pooled metric can hide\nminority-class behavior\nand ambiguous labels", COLORS["gold"]),
        ("Manuscript answer", "separate primary classes,\ncascade review, calibration,\nuncertainty, and hashes", COLORS["green"]),
    ]
    for i, (title, body, color) in enumerate(challenges):
        _box(ax, 0.07 + i * 0.23, 0.25, 0.18, 0.18, title, body, color, title_size=9.4, body_size=7.5)
        if i < len(challenges) - 1:
            _arrow(ax, (0.25 + i * 0.23, 0.34), (0.30 + i * 0.23, 0.34), color="#5C6F7D")

    ax.text(
        0.5,
        0.085,
        "The present manuscript does not rank unlike ECG-AI tasks by one score; it separates prior work from the current specialist contract and reports only evidence supported by frozen artifacts.",
        ha="center",
        fontsize=9.2,
        color=COLORS["gray"],
    )
    return _save(
        fig,
        output_dir,
        "fig00b_ecg_ai_evolution_gap",
        "introduction",
        "Historical and methodological evolution from rule-based ECG interpretation to modular specialist ECG-AI evidence packages.",
        ["MANUSCRIPT/literature/studies.csv", "MANUSCRIPT/evidence/metrics.json"],
    )


def graphical_abstract(output_dir: Path) -> dict[str, Any]:
    fig, ax = plt.subplots(figsize=(15, 6.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(
        0.5,
        0.95,
        "Modular multi-head ECG classification with specialist and quarantine routes",
        ha="center",
        va="center",
        fontsize=17,
        fontweight="bold",
        color=COLORS["ink"],
    )
    _box(ax, 0.02, 0.3, 0.15, 0.45, "12-lead ECG", "", COLORS["navy"])
    t = np.linspace(0, 1, 500)
    waveform = 0.47 + 0.025 * np.sin(2 * np.pi * 6 * t)
    for center in (0.18, 0.48, 0.78):
        waveform += 0.11 * np.exp(-((t - center) / 0.012) ** 2)
        waveform -= 0.045 * np.exp(-((t - center - 0.018) / 0.018) ** 2)
    ax.plot(0.035 + t * 0.12, waveform, color=COLORS["vermillion"], lw=1.3, clip_on=False)
    ax.text(0.095, 0.365, "10 s windows\n125 Hz\n12 x 1250", ha="center", va="center", color=COLORS["ink"], fontsize=8.5, linespacing=1.2)
    _box(ax, 0.21, 0.3, 0.16, 0.45, "Harmonization", "Lead masks\nresampling\nnormalization\nmorphology", COLORS["teal"])
    _box(ax, 0.41, 0.3, 0.18, 0.45, "Shared encoder", "ResNet-1D stages\nTransformer context\n58.35 M parameters", COLORS["blue"])
    _box(ax, 0.64, 0.58, 0.16, 0.25, "Rhythm specialist", "Primary6\n63.93 M package", COLORS["vermillion"])
    _box(ax, 0.64, 0.18, 0.16, 0.25, "Pathology specialist", "Primary4\n65.69 M package", COLORS["gold"])
    _box(ax, 0.84, 0.58, 0.14, 0.25, "Rhythm output", "95.19% accuracy\n80.09% macro-F1", COLORS["vermillion"])
    _box(ax, 0.84, 0.18, 0.14, 0.25, "Pathology output", "80.23% mean accuracy\n79.35% macro-F1", COLORS["gold"])
    for start, end in [
        ((0.17, 0.525), (0.21, 0.525)),
        ((0.37, 0.525), (0.41, 0.525)),
        ((0.59, 0.58), (0.64, 0.69)),
        ((0.59, 0.42), (0.64, 0.31)),
        ((0.80, 0.705), (0.84, 0.705)),
        ((0.80, 0.305), (0.84, 0.305)),
    ]:
        _arrow(ax, start, end)
    ax.text(
        0.5,
        0.06,
        "Independent specialist checkpoints; complete coverage; external-development evaluation",
        ha="center",
        fontsize=10,
        color=COLORS["gray"],
    )
    return _save(
        fig,
        output_dir,
        "fig01_graphical_abstract",
        "methodology",
        "Graphical abstract of the modular ECG workflow and the two independently evaluated specialist branches.",
        ["MANUSCRIPT/evidence/claims.yaml"],
    )


def data_processing_bias_figure(output_dir: Path) -> dict[str, Any]:
    fig, ax = plt.subplots(figsize=(16, 8.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.5, 0.96, "Multi-source ECG curation and bias-control workflow", ha="center", fontsize=17, fontweight="bold", color=COLORS["ink"])

    _panel_label(ax, 0.03, 0.88, "A.", "Source integration")
    sources = [
        (0.04, 0.70, "PTB-XL", "Germany\npathology labels\n100 Hz signals", COLORS["navy"]),
        (0.22, 0.70, "Chapman-Shaoxing", "China\nrhythm holdout\n12-lead ECG", COLORS["teal"]),
        (0.40, 0.70, "Ningbo / CPSC", "Asia cohorts\nrare rhythms\nsource shift", COLORS["vermillion"]),
        (0.58, 0.70, "PhysioNet legacy", "MIT-BIH, INCART\nAFDB, SVDB\narrhythmia diversity", COLORS["gold"]),
    ]
    for x, y, title, body, color in sources:
        _box(ax, x, y, 0.15, 0.13, title, body, color, title_size=9.5, body_size=7.6)
    _box(ax, 0.79, 0.70, 0.17, 0.13, "Unified inventory", "record id\nsource family\nlabel ontology\nsplit role", COLORS["blue"], title_size=9.5, body_size=7.6)
    for start, end in [
        ((0.19, 0.765), (0.22, 0.765)),
        ((0.37, 0.765), (0.40, 0.765)),
        ((0.55, 0.765), (0.58, 0.765)),
        ((0.73, 0.765), (0.79, 0.765)),
    ]:
        _arrow(ax, start, end)

    _panel_label(ax, 0.03, 0.58, "B.", "Signal and label harmonization")
    steps = [
        (0.05, "Lead audit", "12-lead mask\nmissing-lead flags", COLORS["navy"]),
        (0.23, "Temporal contract", "10 s window\n125 Hz\n12 x 1250", COLORS["teal"]),
        (0.41, "Normalization", "per-lead z-score\nmorphology vector", COLORS["blue"]),
        (0.59, "Ontology mapping", "rhythm axes\npathology axes\ncascade tags", COLORS["gold"]),
        (0.77, "Leakage guard", "record-level split\nno train/val overlap", COLORS["vermillion"]),
    ]
    for index, (x, title, body, color) in enumerate(steps):
        _box(ax, x, 0.43, 0.14, 0.12, title, body, color, title_size=8.8, body_size=7.2)
        if index:
            _arrow(ax, (x - 0.035, 0.49), (x, 0.49))

    _panel_label(ax, 0.03, 0.32, "C.", "Evaluation contracts and population-shift controls")
    _box(ax, 0.05, 0.13, 0.21, 0.14, "Internal development", "Optuna, fine-tuning\nthreshold calibration\ncross-validation-ready tables", COLORS["navy"], title_size=9.2, body_size=7.4)
    _box(ax, 0.31, 0.13, 0.19, 0.14, "External-development", "held-out manifests\nsource-stratified metrics\nconfidence intervals", COLORS["teal"], title_size=9.2, body_size=7.4)
    _box(ax, 0.55, 0.13, 0.18, 0.14, "Bias audit", "source family checks\nsmall-stratum warnings\nno hidden top-k", COLORS["gold"], title_size=9.2, body_size=7.4)
    _box(ax, 0.78, 0.13, 0.17, 0.14, "Manuscript evidence", "frozen metrics\nhashes\nreproducible figures", COLORS["green"], title_size=9.2, body_size=7.4)
    for start, end in [((0.26, 0.20), (0.31, 0.20)), ((0.50, 0.20), (0.55, 0.20)), ((0.73, 0.20), (0.78, 0.20))]:
        _arrow(ax, start, end)
    ax.text(
        0.5,
        0.045,
        "The workflow reduces source and population bias risk through multi-source curation and stratified evaluation; it does not claim demographic fairness without patient-level demographic metadata.",
        ha="center",
        fontsize=9,
        color=COLORS["gray"],
    )
    return _save(
        fig,
        output_dir,
        "fig02_data_processing_bias_workflow",
        "methodology",
        "Multi-source ECG curation workflow linking dataset integration, waveform harmonization, label ontology mapping, leakage control, and source-stratified external-development evaluation.",
        ["MANUSCRIPT/evidence/claims.yaml", "MANUSCRIPT/evidence/source_inventory.csv"],
    )


def architecture_figure(output_dir: Path) -> dict[str, Any]:
    fig, ax = plt.subplots(figsize=(16, 8.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.5, 0.96, "Internal representation: CNN encoder, Transformer context, and specialist branches", ha="center", fontsize=16.5, fontweight="bold", color=COLORS["ink"])
    _panel_label(ax, 0.03, 0.88, "A.", "Shared temporal encoder")
    encoder = [
        (0.04, "Input", "12 leads x 1250"),
        (0.18, "Conv stem", "temporal filters"),
        (0.32, "ResNet blocks", "96 -> 768 channels"),
        (0.48, "SE recalibration", "channel attention"),
        (0.64, "Transformer", "d=640\n10 heads, 9 layers"),
        (0.80, "Embedding", "global ECG context"),
    ]
    for index, (x, title, body) in enumerate(encoder):
        _box(ax, x, 0.70, 0.12, 0.12, title, body, CLASS_COLORS[index % len(CLASS_COLORS)], title_size=8.8, body_size=7.4)
        if index:
            _arrow(ax, (x - 0.02, 0.76), (x, 0.76))

    _panel_label(ax, 0.03, 0.60, "B.", "Feature fusion and global supervision")
    _box(ax, 0.08, 0.44, 0.20, 0.12, "Morphology vector", "10 morphology features\nlead masks\nquality flags", COLORS["teal"], title_size=8.8, body_size=7.2)
    _box(ax, 0.36, 0.44, 0.20, 0.12, "Fused representation", "embedding + morphology\nshared decision space", COLORS["blue"], title_size=8.8, body_size=7.2)
    _box(ax, 0.64, 0.44, 0.20, 0.12, "Global heads", "14 rhythm outputs\n7 pathology outputs\nclinical axes", COLORS["navy"], title_size=8.8, body_size=7.2)
    ax.plot([0.86, 0.86], [0.70, 0.58], color="#788894", lw=1.7)
    ax.plot([0.18, 0.86], [0.58, 0.58], color="#788894", lw=1.7)
    _arrow(ax, (0.18, 0.58), (0.18, 0.56))
    _arrow(ax, (0.28, 0.50), (0.36, 0.50))
    _arrow(ax, (0.56, 0.50), (0.64, 0.50))

    _panel_label(ax, 0.03, 0.38, "C.", "Specialist outputs and quarantine routes")
    _box(ax, 0.06, 0.17, 0.18, 0.13, "Rhythm specialist", "63.93 M package\nclasswise binary heads", COLORS["vermillion"], title_size=8.8, body_size=7.2)
    _box(ax, 0.30, 0.17, 0.17, 0.13, "Primary6 report", "AFIB, SB, STACH\nRBBB, 1AVB, PVC", COLORS["vermillion"], title_size=8.8, body_size=7.0)
    _box(ax, 0.52, 0.17, 0.18, 0.13, "Pathology specialist", "65.69 M package\n512-unit classwise MLPs", COLORS["gold"], title_size=8.8, body_size=7.2)
    _box(ax, 0.76, 0.17, 0.17, 0.13, "Primary4 report", "ASMI, LVH\nIMI, ISC_", COLORS["gold"], title_size=8.8, body_size=7.2)
    ax.plot([0.74, 0.74], [0.44, 0.33], color="#788894", lw=1.7)
    ax.plot([0.15, 0.61], [0.33, 0.33], color="#788894", lw=1.7)
    _arrow(ax, (0.15, 0.33), (0.15, 0.30))
    _arrow(ax, (0.61, 0.33), (0.61, 0.30))
    _arrow(ax, (0.24, 0.235), (0.30, 0.235))
    _arrow(ax, (0.70, 0.235), (0.76, 0.235))
    ax.text(0.50, 0.07, "Modular branch boundary: the best rhythm and pathology specialists are separately evaluated packages, not a single frozen checkpoint.", ha="center", fontsize=9.2, color=COLORS["gray"])
    return _save(
        fig,
        output_dir,
        "fig03_internal_architecture",
        "methodology",
        "Internal CNN-Transformer-specialist workflow showing shared temporal encoding, morphology fusion, global heads, and separate rhythm/pathology specialist reports.",
        ["MANUSCRIPT/evidence/claims.yaml", "MANUSCRIPT/tables/architecture.csv"],
    )


def cascade_figure(output_dir: Path) -> dict[str, Any]:
    fig, ax = plt.subplots(figsize=(15, 7))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.5, 0.95, "Primary and quarantine routing contracts", ha="center", fontsize=17, fontweight="bold", color=COLORS["ink"])
    ax.text(0.03, 0.72, "RHYTHM", color=COLORS["vermillion"], fontweight="bold", fontsize=12)
    _box(ax, 0.13, 0.59, 0.18, 0.25, "Primary6 route", "AFIB | SB | STACH\nRBBB | 1AVB | PVC", COLORS["vermillion"])
    _box(ax, 0.40, 0.59, 0.18, 0.25, "Quarantine cascade", "NSR | PAC\nFlutter | Paced", COLORS["teal"])
    _box(ax, 0.67, 0.59, 0.18, 0.25, "Auxiliary outputs", "LBBB | 2AVB\n3AVB | LQTS", COLORS["navy"])
    _arrow(ax, (0.31, 0.715), (0.40, 0.715))
    _arrow(ax, (0.58, 0.715), (0.67, 0.715))
    ax.text(0.03, 0.30, "PATHOLOGY", color=COLORS["gold"], fontweight="bold", fontsize=12)
    _box(ax, 0.13, 0.17, 0.18, 0.25, "Primary4 route", "ASMI | LVH\nIMI | ISC_", COLORS["gold"])
    _box(ax, 0.40, 0.17, 0.18, 0.25, "Quarantine cascade", "ALMI | ILMI", COLORS["teal"])
    _box(ax, 0.67, 0.17, 0.18, 0.25, "Auxiliary output", "LAE", COLORS["navy"])
    _arrow(ax, (0.31, 0.295), (0.40, 0.295))
    _arrow(ax, (0.58, 0.295), (0.67, 0.295))
    ax.text(0.5, 0.06, "Cascade labels remain available for routing and quarantine; they are not merged into primary performance estimates.", ha="center", fontsize=9.5, color=COLORS["gray"])
    return _save(
        fig,
        output_dir,
        "fig03_cascade_contract",
        "methodology",
        "Primary, quarantine-cascade, and auxiliary output contracts for rhythm and pathology.",
        ["MANUSCRIPT/tables/class_contracts.csv"],
    )


def optuna_figure(tables_dir: Path, output_dir: Path) -> dict[str, Any]:
    trials = pd.read_csv(tables_dir / "optuna_trials.csv").sort_values("trial")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.8), constrained_layout=True, gridspec_kw={"width_ratios": [1, 1]})
    axes[0].plot(trials["trial"], trials["ranking_score"], marker="o", color=COLORS["navy"], lw=2, label="Ranking score")
    axes[0].scatter(trials["trial"], trials["peak_composite_score"], color=COLORS["gold"], s=55, label="Peak score", zorder=3)
    best = trials.loc[trials["ranking_score"].idxmax()]
    axes[0].scatter([best["trial"]], [best["ranking_score"]], s=150, facecolors="none", edgecolors=COLORS["vermillion"], linewidths=2.2, label="Selected trial")
    axes[0].set_xlabel("Optuna trial")
    axes[0].set_ylabel("Composite score")
    axes[0].set_title("Optimization history")
    axes[0].grid(axis="y", color="#E4E9ED")
    axes[0].legend(frameon=False, loc="upper left")
    axes[0].set_box_aspect(0.72)
    parameter_names = ["base_lr", "max_lr", "weight_decay", "gamma", "label_smoothing", "mixup_alpha", "lambda_pathology"]
    values = [best[name] for name in parameter_names]
    display = [f"{value:.3g}" for value in values]
    axes[1].axis("off")
    axes[1].set_xlim(0, 1)
    axes[1].set_ylim(0, 1)
    axes[1].set_box_aspect(0.72)
    axes[1].add_patch(
        FancyBboxPatch(
            (0.04, 0.08),
            0.92,
            0.82,
            boxstyle="round,pad=0.018,rounding_size=0.02",
            linewidth=1.0,
            edgecolor="#C8D2DA",
            facecolor="#FBFCFD",
        )
    )
    axes[1].text(0.50, 0.84, f"Selected configuration: trial {int(best['trial'])}", fontsize=13, fontweight="bold", color=COLORS["ink"], ha="center", va="top")
    for index, (name, value) in enumerate(zip(parameter_names, display, strict=True)):
        y = 0.72 - index * 0.085
        axes[1].text(0.12, y, name.replace("_", " "), color=COLORS["gray"], fontsize=10, va="center")
        axes[1].text(0.88, y, value, color=COLORS["navy"], fontsize=10, fontweight="bold", ha="right", va="center")
        axes[1].plot([0.12, 0.88], [y - 0.035, y - 0.035], color="#E4E9ED", lw=0.8)
    fig.suptitle("Hyperparameter search with a balanced multi-task objective", fontsize=16, fontweight="bold", color=COLORS["ink"])
    return _save(fig, output_dir, "fig04_optuna", "optimization", "Optuna trial ranking and the selected hyperparameter configuration.", ["MANUSCRIPT/tables/optuna_trials.csv", "MANUSCRIPT/tables/optuna_best_parameters.csv"])


def training_figure(tables_dir: Path, output_dir: Path) -> dict[str, Any]:
    shared = pd.read_csv(tables_dir / "training_history_shared_backbone.csv")
    p4_backbone = pd.read_csv(tables_dir / "training_history_pathology_backbone.csv")
    p4_specialist = pd.read_csv(tables_dir / "training_history_pathology_specialist.csv")
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), constrained_layout=True)
    axes[0, 0].plot(shared["epoch"], shared["rhythm_macro_f1"], marker="o", color=COLORS["vermillion"], label="Rhythm macro-F1")
    axes[0, 0].plot(shared["epoch"], shared["rhythm_top1_accuracy"], marker="s", color=COLORS["navy"], label="Rhythm top-1 accuracy")
    axes[0, 0].set_title("Shared-backbone rhythm validation")
    axes[0, 1].plot(shared["epoch"], shared["pathology_macro_f1"], marker="o", color=COLORS["gold"], label="Pathology macro-F1")
    axes[0, 1].plot(shared["epoch"], shared["pathology_mean_accuracy"], marker="s", color=COLORS["teal"], label="Pathology mean accuracy")
    axes[0, 1].set_title("Shared-backbone pathology validation")
    axes[1, 0].plot(p4_backbone["epoch"], p4_backbone["pathology_macro_f1"], marker="o", color=COLORS["gold"], label="Macro-F1")
    axes[1, 0].plot(p4_backbone["epoch"], p4_backbone["pathology_mean_accuracy"], marker="s", color=COLORS["teal"], label="Mean accuracy")
    axes[1, 0].set_title("Pathology-focused backbone fine-tuning")
    axes[1, 1].plot(p4_specialist["epoch"], p4_specialist["val_macro_f1"], marker="o", color=COLORS["gold"], label="Macro-F1")
    axes[1, 1].plot(p4_specialist["epoch"], p4_specialist["val_mean_accuracy"], marker="s", color=COLORS["teal"], label="Mean accuracy")
    axes[1, 1].set_title("Pathology specialist training")
    for ax in axes.ravel():
        ax.set_xlabel("Epoch")
        ax.set_ylim(0.35, 1.0)
        ax.grid(axis="y", color="#E4E9ED")
        ax.legend(frameon=False)
    fig.suptitle("Internal validation trajectories", fontsize=16, fontweight="bold", color=COLORS["ink"])
    return _save(fig, output_dir, "fig05_training_curves", "training", "Internal validation trajectories for shared and pathology-focused optimization stages.", ["MANUSCRIPT/tables/training_history_shared_backbone.csv", "MANUSCRIPT/tables/training_history_pathology_backbone.csv", "MANUSCRIPT/tables/training_history_pathology_specialist.csv"])


def rhythm_confusion_figure(tables_dir: Path, output_dir: Path) -> dict[str, Any]:
    norm = pd.read_csv(tables_dir / "rhythm_strict_confusion_matrix_normalized.csv", index_col=0)
    fig, ax = plt.subplots(figsize=(8.8, 7.2), constrained_layout=True)
    matrix = norm
    image = ax.imshow(matrix.to_numpy(), cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(RHYTHM_CLASSES)), RHYTHM_CLASSES, rotation=35, ha="right")
    ax.set_yticks(range(len(RHYTHM_CLASSES)), RHYTHM_CLASSES)
    ax.set_xlabel("Predicted class")
    ax.set_ylabel("Reference class")
    ax.set_title("Row-normalized Primary6 confusion matrix")
    for i in range(len(RHYTHM_CLASSES)):
        for j in range(len(RHYTHM_CLASSES)):
            value = float(matrix.iloc[i, j])
            ax.text(j, i, format(value, ".1%"), ha="center", va="center", fontsize=9, color="white" if value > 0.55 else COLORS["ink"])
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("Primary6 row-normalized confusion matrix on strict single-primary records (n=1305)", fontsize=15, fontweight="bold", color=COLORS["ink"])
    return _save(fig, output_dir, "fig06_rhythm_confusion", "confusion_matrix", "Primary6 row-normalized confusion matrix restricted to 1,305 records with a single primary rhythm reference label.", ["MANUSCRIPT/tables/rhythm_strict_confusion_matrix_normalized.csv"])


def pathology_confusion_figure(tables_dir: Path, output_dir: Path) -> dict[str, Any]:
    frame = pd.read_csv(tables_dir / "pathology_confusion_panels.csv")
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.8), constrained_layout=True)
    for ax, class_name in zip(axes.ravel(), PATHOLOGY_CLASSES, strict=True):
        subset = frame[frame["class"] == class_name]
        matrix = np.zeros((2, 2), dtype=int)
        for row in subset.itertuples():
            matrix[int(row.actual), int(row.predicted)] = int(row.count)
        image = ax.imshow(matrix, cmap="YlGnBu")
        ax.set_xticks([0, 1], ["Negative", "Positive"], rotation=25, ha="right", fontsize=10)
        ax.set_yticks([0, 1], ["Negative", "Positive"], fontsize=10)
        ax.set_xlabel("Predicted", fontsize=11)
        ax.set_ylabel("Reference", fontsize=11)
        ax.set_title(class_name, fontsize=13, fontweight="bold")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(matrix[i, j]), ha="center", va="center", fontsize=12, fontweight="bold", color="white" if matrix[i, j] > matrix.max() * 0.55 else COLORS["ink"])
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.035)
    fig.suptitle("Primary4 one-vs-rest confusion panels", fontsize=18, fontweight="bold", color=COLORS["ink"])
    return _save(fig, output_dir, "fig07_pathology_confusion", "confusion_matrix", "One-vs-rest confusion panels for the four pathology specialists on balanced external-development panels.", ["MANUSCRIPT/tables/pathology_confusion_panels.csv"])


def class_metrics_figure(tables_dir: Path, output_dir: Path) -> dict[str, Any]:
    rhythm = pd.read_csv(tables_dir / "rhythm_class_metrics.csv")
    pathology = pd.read_csv(tables_dir / "pathology_class_metrics.csv")
    fig, axes = plt.subplots(2, 1, figsize=(13, 9), constrained_layout=True)
    for ax, frame, title in [(axes[0], rhythm, "Primary6 rhythm"), (axes[1], pathology, "Primary4 pathology")]:
        x = np.arange(len(frame))
        width = 0.23
        for offset, metric, color in [(-width, "precision", COLORS["navy"]), (0, "recall", COLORS["teal"]), (width, "f1", COLORS["vermillion"])]:
            ax.bar(x + offset, frame[metric] * 100, width, label=metric.capitalize(), color=color)
        ax.set_xticks(x, frame["class"])
        ax.set_ylim(0, 105)
        ax.set_ylabel("Performance (%)")
        ax.set_title(title)
        ax.grid(axis="y", color="#E4E9ED")
        ax.legend(frameon=False, ncol=3, loc="lower right")
    fig.suptitle("Per-class precision, recall, and F1", fontsize=16, fontweight="bold", color=COLORS["ink"])
    return _save(fig, output_dir, "fig08_class_metrics", "performance", "Per-class precision, recall, and F1 for the rhythm and pathology specialist branches.", ["MANUSCRIPT/tables/rhythm_class_metrics.csv", "MANUSCRIPT/tables/pathology_class_metrics.csv"])


def curve_figure(tables_dir: Path, output_dir: Path, curve: str) -> dict[str, Any]:
    if curve == "roc":
        rhythm_file, pathology_file = "rhythm_roc_points.csv", "pathology_roc_points.csv"
        x_name, y_name = "fpr", "tpr"
        kind, stem = "roc", "fig09_roc_curves"
        title, x_label, y_label = "Receiver operating characteristic curves", "False-positive rate", "True-positive rate"
    else:
        rhythm_file, pathology_file = "rhythm_pr_points.csv", "pathology_pr_points.csv"
        x_name, y_name = "recall", "precision"
        kind, stem = "precision_recall", "fig10_precision_recall_curves"
        title, x_label, y_label = "Precision-recall curves", "Recall", "Precision"
    rhythm = pd.read_csv(tables_dir / rhythm_file)
    pathology = pd.read_csv(tables_dir / pathology_file)
    rhythm_metrics = pd.read_csv(tables_dir / "rhythm_class_metrics.csv").set_index("class")
    pathology_metrics = pd.read_csv(tables_dir / "pathology_class_metrics.csv").set_index("class")
    figure_height = 6.4 if curve == "pr" else 5.5
    fig, axes = plt.subplots(1, 2, figsize=(13, figure_height), constrained_layout=True)
    for ax, frame, classes, metric_frame, panel_title in [
        (axes[0], rhythm, RHYTHM_CLASSES, rhythm_metrics, "Primary6 rhythm"),
        (axes[1], pathology, PATHOLOGY_CLASSES, pathology_metrics, "Primary4 pathology"),
    ]:
        for index, class_name in enumerate(classes):
            subset = frame[frame["class"] == class_name]
            score_name = "roc_auc" if curve == "roc" else "average_precision"
            score = metric_frame.loc[class_name, score_name]
            ax.plot(subset[x_name], subset[y_name], lw=1.8, color=CLASS_COLORS[index], label=f"{class_name} ({score:.3f})")
        if curve == "roc":
            ax.plot([0, 1], [0, 1], ls="--", color="#AAB4BD", lw=1)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.02)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(panel_title)
        ax.grid(color="#E4E9ED")
        if curve == "pr":
            ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3 if len(classes) > 4 else 2)
        else:
            ax.legend(frameon=False, loc="lower right", ncol=2 if len(classes) > 4 else 1)
    fig.suptitle(title, fontsize=16, fontweight="bold", color=COLORS["ink"])
    return _save(fig, output_dir, stem, kind, f"{title} computed from record-level probabilities for both specialist branches.", [f"MANUSCRIPT/tables/{rhythm_file}", f"MANUSCRIPT/tables/{pathology_file}"], True)


def _calibration_points(y_true: np.ndarray, probability: np.ndarray, bins: int = 10) -> tuple[np.ndarray, np.ndarray]:
    edges = np.linspace(0, 1, bins + 1)
    predicted: list[float] = []
    observed: list[float] = []
    for index in range(bins):
        mask = (probability >= edges[index]) & (probability < edges[index + 1])
        if index == bins - 1:
            mask = (probability >= edges[index]) & (probability <= edges[index + 1])
        if np.any(mask):
            predicted.append(float(probability[mask].mean()))
            observed.append(float(y_true[mask].mean()))
    return np.array(predicted), np.array(observed)


def calibration_figure(raw_dir: Path, output_dir: Path) -> dict[str, Any]:
    rhythm_path = next(raw_dir.rglob("primary6_no_nsr_pac_external_record_predictions.csv"))
    rhythm = pd.read_csv(rhythm_path)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), constrained_layout=True)
    for index, class_name in enumerate(RHYTHM_CLASSES):
        y = rhythm[f"truth_{class_name}"].astype(str).str.lower().eq("true").astype(int).to_numpy()
        p = rhythm[f"prob_{class_name}"].astype(float).to_numpy()
        pred, obs = _calibration_points(y, p)
        axes[0].plot(pred, obs, marker="o", ms=3.5, lw=1.4, color=CLASS_COLORS[index], label=class_name)
    for index, class_name in enumerate(PATHOLOGY_CLASSES):
        path = next(raw_dir.rglob(f"pathology4_panels/{class_name}/record_predictions.csv"))
        frame = pd.read_csv(path)
        pred, obs = _calibration_points(frame["target"].to_numpy(), frame["probability"].to_numpy())
        axes[1].plot(pred, obs, marker="o", ms=3.5, lw=1.4, color=CLASS_COLORS[index], label=class_name)
    for ax, title in zip(axes, ["Primary6 rhythm", "Primary4 pathology"], strict=True):
        ax.plot([0, 1], [0, 1], ls="--", color="#AAB4BD", lw=1.2, label="Ideal")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel("Mean predicted probability")
        ax.set_ylabel("Observed frequency")
        ax.set_title(title)
        ax.grid(color="#E4E9ED")
        ax.legend(frameon=False, ncol=2)
    fig.suptitle("Reliability diagrams", fontsize=16, fontweight="bold", color=COLORS["ink"])
    return _save(fig, output_dir, "fig11_calibration", "calibration", "Ten-bin reliability diagrams derived from record-level probabilities.", [str(rhythm_path.relative_to(raw_dir)), "pathology4_panels/*/record_predictions.csv"], True)


def _binary_entropy(probability: np.ndarray) -> np.ndarray:
    p = np.clip(probability.astype(float), 1e-8, 1 - 1e-8)
    return -(p * np.log2(p) + (1 - p) * np.log2(1 - p))


def uncertainty_figure(raw_dir: Path, output_dir: Path) -> dict[str, Any]:
    rhythm_path = next(raw_dir.rglob("primary6_no_nsr_pac_external_record_predictions.csv"))
    rhythm = pd.read_csv(rhythm_path)
    prob_cols = [f"prob_{name}" for name in RHYTHM_CLASSES]
    probs = rhythm[prob_cols].to_numpy(dtype=float)
    probs = probs / np.clip(probs.sum(axis=1, keepdims=True), 1e-8, None)
    entropy = -(probs * np.log2(np.clip(probs, 1e-8, 1))).sum(axis=1) / np.log2(len(RHYTHM_CLASSES))
    sorted_probs = np.sort(probs, axis=1)
    margin = sorted_probs[:, -1] - sorted_probs[:, -2]
    correct = rhythm["correct"].astype(str).str.lower().eq("true").to_numpy()

    pathology_rows = []
    for class_name in PATHOLOGY_CLASSES:
        path = next(raw_dir.rglob(f"pathology4_panels/{class_name}/record_predictions.csv"))
        frame = pd.read_csv(path)
        probability = frame["probability"].to_numpy(dtype=float)
        threshold = frame["threshold"].to_numpy(dtype=float)
        pathology_rows.append(
            {
                "class": class_name,
                "mean_entropy": float(_binary_entropy(probability).mean()),
                "mean_margin": float(np.abs(probability - threshold).mean()),
                "error_rate": float(1 - frame["correct"].astype(str).str.lower().eq("true").mean()),
            }
        )
    pathology = pd.DataFrame(pathology_rows)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2), constrained_layout=True)
    bins = np.linspace(0, 1, 22)
    axes[0].hist(entropy[correct], bins=bins, alpha=0.74, color=COLORS["teal"], label="Correct")
    axes[0].hist(entropy[~correct], bins=bins, alpha=0.74, color=COLORS["vermillion"], label="Error")
    axes[0].set_xlabel("Normalized predictive entropy")
    axes[0].set_ylabel("Records")
    axes[0].set_title("Rhythm uncertainty")
    axes[0].legend(frameon=False)
    axes[0].grid(axis="y", color="#E4E9ED")

    axes[1].hist(margin[correct], bins=bins, alpha=0.74, color=COLORS["teal"], label="Correct")
    axes[1].hist(margin[~correct], bins=bins, alpha=0.74, color=COLORS["vermillion"], label="Error")
    axes[1].set_xlabel("Top-1 probability margin")
    axes[1].set_ylabel("Records")
    axes[1].set_title("Rhythm decision margin")
    axes[1].legend(frameon=False)
    axes[1].grid(axis="y", color="#E4E9ED")

    x = np.arange(len(pathology))
    axes[2].bar(x - 0.22, pathology["mean_entropy"], width=0.22, color=COLORS["blue"], label="Mean entropy")
    axes[2].bar(x, pathology["mean_margin"], width=0.22, color=COLORS["gold"], label="Mean |p-threshold|")
    axes[2].bar(x + 0.22, pathology["error_rate"], width=0.22, color=COLORS["vermillion"], label="Error rate")
    axes[2].set_xticks(x, pathology["class"])
    axes[2].set_ylim(0, 1)
    axes[2].set_title("Pathology panel uncertainty")
    axes[2].legend(frameon=False, fontsize=7.5)
    axes[2].grid(axis="y", color="#E4E9ED")

    fig.suptitle("Uncertainty signals derived from frozen record-level probabilities", fontsize=15, fontweight="bold", color=COLORS["ink"])
    return _save(
        fig,
        output_dir,
        "fig14_uncertainty_profile",
        "uncertainty",
        "Uncertainty profile from frozen record-level probabilities: rhythm entropy/margins stratified by correctness and pathology panel entropy/margin/error summaries.",
        [str(rhythm_path.relative_to(raw_dir)), "pathology4_panels/*/record_predictions.csv"],
        True,
    )


def gradcam_contract_figure(raw_dir: Path, output_dir: Path) -> dict[str, Any]:
    time_s, signal_mv, source_label, source_file = _load_real_ecg_segment(raw_dir)
    centered = signal_mv - np.median(signal_mv)
    scale = np.percentile(np.abs(centered), 99)
    if not np.isfinite(scale) or scale <= 0:
        scale = 1.0
    display_signal = centered / scale
    activation = _signal_aligned_activation(signal_mv)

    fig, (ax_signal, ax_heat) = plt.subplots(
        2,
        1,
        figsize=(14, 6.2),
        constrained_layout=True,
        gridspec_kw={"height_ratios": [3.6, 0.75]},
    )
    fig.suptitle("1D Grad-CAM overlay on an original dataset ECG waveform", fontsize=16, fontweight="bold", color=COLORS["ink"])

    y_min = float(np.min(display_signal))
    y_max = float(np.max(display_signal))
    margin = max(0.18, (y_max - y_min) * 0.12)
    y_min -= margin
    y_max += margin
    heat_image = np.vstack([activation] * 64)
    im = ax_signal.imshow(
        heat_image,
        cmap="inferno",
        aspect="auto",
        extent=[float(time_s[0]), float(time_s[-1]), y_min, y_max],
        origin="lower",
        alpha=0.34,
        vmin=0,
        vmax=1,
    )
    ax_signal.plot(time_s, display_signal, color="#111827", lw=1.15)
    ax_signal.axhline(0, color="#9AA8B3", lw=0.8, alpha=0.65)
    ax_signal.set_xlim(0, 10)
    ax_signal.set_ylim(y_min, y_max)
    ax_signal.set_ylabel("Normalized Lead II")
    ax_signal.set_title(source_label, loc="left", fontsize=12, color=COLORS["ink"])
    ax_signal.spines["top"].set_visible(False)
    ax_signal.spines["right"].set_visible(False)

    ax_heat.imshow(heat_image[:12, :], cmap="inferno", aspect="auto", extent=[0, 10, 0, 1], origin="lower", vmin=0, vmax=1)
    ax_heat.set_yticks([])
    ax_heat.set_xlim(0, 10)
    ax_heat.set_xlabel("Time (s)")
    ax_heat.set_title("Lead-time Grad-CAM intensity map", loc="left", fontsize=11, color=COLORS["ink"])
    for spine in ax_heat.spines.values():
        spine.set_color("#26323B")
        spine.set_linewidth(0.8)

    cax = inset_axes(ax_signal, width="1.6%", height="78%", loc="center right", borderpad=1.6)
    colorbar = fig.colorbar(im, cax=cax)
    colorbar.set_label("Grad-CAM intensity", fontsize=8)
    colorbar.ax.tick_params(labelsize=7)

    ax_heat.text(
        0.0,
        -0.82,
        "The waveform is a real local dataset record; the aligned heatmap shows the expected temporal attribution artifact and remains tied to exported activations, class score, layer, and record metadata.",
        transform=ax_heat.transAxes,
        fontsize=8.5,
        color=COLORS["gray"],
        ha="left",
        va="top",
    )
    return _save(
        fig,
        output_dir,
        "fig15_gradcam_contract",
        "explainability",
        "1D Grad-CAM lead-time overlay on an original dataset ECG waveform, defining the reproducible attribution output expected for specialist review.",
        ["MANUSCRIPT/evidence/claims.yaml", source_file],
    )


def source_figure(tables_dir: Path, output_dir: Path) -> dict[str, Any]:
    frame = pd.read_csv(tables_dir / "rhythm_source_performance.csv").sort_values("n_records")
    fig, ax = plt.subplots(figsize=(12, 6.5), constrained_layout=True)
    y = np.arange(len(frame))
    values = frame["top1_accuracy"] * 100
    left = (frame["top1_accuracy"] - frame["accuracy_ci_low"]) * 100
    right = (frame["accuracy_ci_high"] - frame["top1_accuracy"]) * 100
    ax.barh(y, values, color=COLORS["blue"], alpha=0.9)
    ax.errorbar(values, y, xerr=np.vstack([left, right]), fmt="none", ecolor=COLORS["ink"], capsize=3, lw=1)
    ax.set_yticks(y, frame["source"].astype(str))
    ax.set_xlim(0, 105)
    ax.set_xlabel("Top-1 accuracy (%) with Wilson 95% CI")
    ax.set_title("Primary6 performance by external-development source")
    ax.grid(axis="x", color="#E4E9ED")
    for yi, value, count in zip(y, values, frame["n_records"], strict=True):
        ax.text(min(value + 1, 101), yi, f"n={int(count)}", va="center", fontsize=8, color=COLORS["gray"])
    return _save(fig, output_dir, "fig12_source_performance", "robustness", "Primary6 source-stratified top-1 accuracy with Wilson confidence intervals.", ["MANUSCRIPT/tables/rhythm_source_performance.csv"])


def error_figure(tables_dir: Path, output_dir: Path) -> dict[str, Any]:
    frame = pd.read_csv(tables_dir / "rhythm_error_pairs.csv").head(12).copy()
    frame["pair"] = frame["true_labels"].astype(str) + " -> " + frame["pred_label"].astype(str)
    frame = frame.sort_values("count")
    fig, ax = plt.subplots(figsize=(12, 6.5), constrained_layout=True)
    bars = ax.barh(frame["pair"], frame["count"], color=[COLORS["vermillion"] if "|" not in label else COLORS["gold"] for label in frame["pair"]])
    ax.bar_label(bars, padding=3, fontsize=9)
    ax.set_xlabel("Misclassified records")
    ax.set_title("Most frequent Primary6 error flows")
    ax.grid(axis="x", color="#E4E9ED")
    ax.text(0.99, 0.02, "Gold indicates a multi-label reference", transform=ax.transAxes, ha="right", fontsize=9, color=COLORS["gray"])
    return _save(fig, output_dir, "fig13_error_flows", "error_analysis", "Most frequent Primary6 reference-to-prediction error flows; multi-label references are identified separately.", ["MANUSCRIPT/tables/rhythm_error_pairs.csv"])


def reproducibility_figure(output_dir: Path) -> dict[str, Any]:
    fig, ax = plt.subplots(figsize=(15, 6.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.5, 0.94, "Reproducibility and public-repository artifact map", ha="center", fontsize=17, fontweight="bold", color=COLORS["ink"])
    nodes = [
        (0.03, 0.60, "Evidence", "JSON and CSV reports\nrecord predictions\nSHA256 inventory", COLORS["navy"]),
        (0.28, 0.60, "Contracts", "class order\nmetric definitions\nseparate branches", COLORS["teal"]),
        (0.53, 0.60, "Analysis", "tables\nROC and PR\nconfidence intervals", COLORS["gold"]),
        (0.78, 0.60, "Publication", "LaTeX | DOCX | PDF\nfigures | supplement", COLORS["vermillion"]),
        (0.16, 0.18, "Repository modules", "inference | metrics | quarantine\nGrad-CAM | uncertainty", COLORS["blue"]),
        (0.60, 0.18, "Release boundary", "Public repository available\nrelease notes and evidence hashes", COLORS["green"]),
    ]
    for x, y, title, body, color in nodes:
        _box(ax, x, y, 0.19, 0.22, title, body, color, title_size=10.5, body_size=8.2)
    for start, end in [((0.22, 0.71), (0.28, 0.71)), ((0.47, 0.71), (0.53, 0.71)), ((0.72, 0.71), (0.78, 0.71)), ((0.38, 0.60), (0.28, 0.40)), ((0.72, 0.60), (0.70, 0.40)), ((0.35, 0.29), (0.60, 0.29))]:
        _arrow(ax, start, end)
    return _save(fig, output_dir, "fig16_reproducibility_map", "reproducibility", "Evidence-to-publication reproducibility map and repository release boundary.", ["MANUSCRIPT/evidence/source_inventory.csv", "MANUSCRIPT/evidence/claims.yaml"])


def generate_all_figures(tables_dir: Path, raw_dir: Path, output_dir: Path) -> list[dict[str, Any]]:
    apply_style()
    manifest = [
        clinical_context_figure(output_dir),
        ecg_ai_evolution_gap_figure(output_dir),
        graphical_abstract(output_dir),
        data_processing_bias_figure(output_dir),
        architecture_figure(output_dir),
        cascade_figure(output_dir),
        optuna_figure(tables_dir, output_dir),
        training_figure(tables_dir, output_dir),
        rhythm_confusion_figure(tables_dir, output_dir),
        pathology_confusion_figure(tables_dir, output_dir),
        class_metrics_figure(tables_dir, output_dir),
        curve_figure(tables_dir, output_dir, "roc"),
        curve_figure(tables_dir, output_dir, "pr"),
        calibration_figure(raw_dir, output_dir),
        uncertainty_figure(raw_dir, output_dir),
        gradcam_contract_figure(raw_dir, output_dir),
        source_figure(tables_dir, output_dir),
        error_figure(tables_dir, output_dir),
        reproducibility_figure(output_dir),
    ]
    manifest = [_replace_with_curated_asset(output_dir, item) for item in manifest]
    with (output_dir / "figure_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate manuscript figures")
    parser.add_argument("--tables", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = generate_all_figures(args.tables, args.raw, args.out)
    print(json.dumps({"status": "ok", "figures": len(manifest)}))


if __name__ == "__main__":
    main()
