"""Rebuild all manuscript figures from pinned aggregate or archived development inputs.
Individual records are read locally only and never copied to the delivery.
"""

import collections
import csv
import hashlib
import json
import re
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[1]
FIG = HERE / "latex/figures"
FIG.mkdir(exist_ok=True, parents=True)
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.facecolor": "white",
        "axes.titlesize": 12,
        "axes.labelsize": 11.5,
    }
)
COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#A6761D", "#56B4E9", "#555555", "#8064A2"]
inventory = []


def save(fig, name, sources, kind="quantitative"):
    fig.savefig(FIG / (name + ".pdf"), bbox_inches="tight", pad_inches=0.10)
    fig.savefig(FIG / (name + ".png"), dpi=320, bbox_inches="tight", pad_inches=0.10)
    plt.close(fig)
    inventory.append(
        {
            "file": name,
            "kind": kind,
            "sources": sources,
            "creator": "Code-generated for this revision; no third-party artwork",
            "pdf_sha256": hashlib.sha256((FIG / (name + ".pdf")).read_bytes()).hexdigest(),
            "png_sha256": hashlib.sha256((FIG / (name + ".png")).read_bytes()).hexdigest(),
        }
    )


def box(ax, x, y, w, h, text, color="#EAF2F8", fontsize=10):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.012,rounding_size=.018",
            facecolor=color,
            edgecolor="#34556B",
            lw=1,
        )
    )
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize * 1.15,
        linespacing=1.35,
    )


def arrow(ax, start, end, label=None):
    ax.add_patch(
        FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=12, lw=1.2, color="#34556B")
    )
    if label:
        ax.text(
            (start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.02, label, ha="center", fontsize=9
        )


def canvas(w=7.0, h=3.4):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    return fig, ax


fig, ax = canvas()
for x, t in [
    (0.02, "Multi-source ECG\n12 named leads\nSource-specific labels"),
    (0.36, "Signal harmonization\n10 s at 125 Hz\nLead mask retained"),
    (0.70, "Separate profiles\nRhythm statements\nPathology panels"),
]:
    box(ax, x, 0.38, 0.28, 0.40, t)
arrow(ax, (0.30, 0.58), (0.36, 0.58))
arrow(ax, (0.64, 0.58), (0.70, 0.58))
ax.text(
    0.5,
    0.15,
    "Evaluation unit and eligibility must accompany every performance estimate.",
    ha="center",
    fontsize=10,
)
save(
    fig,
    "fig00_ecg_ai_context",
    ["Study schematic; Methods input and reporting contracts"],
    "schematic",
)
fig, ax = canvas(h=3.0)
for x, t in [
    (0.02, "Beat-level endpoint\nTiming annotations\nEvent matching"),
    (0.36, "ECG-level endpoint\nStatement labels\nTITAN evaluation"),
    (0.70, "Longitudinal endpoint\nHistory and follow-up\nIncident diagnosis"),
]:
    box(ax, x, 0.26, 0.28, 0.55, t, "#EAF2F8" if x != 0.36 else "#D8EDE5", 9.5)
ax.text(
    0.5,
    0.07,
    "Different reference units require different studies; these boxes are not a performance ranking.",
    ha="center",
    fontsize=9,
)
save(fig, "fig00b_ecg_ai_evolution_gap", ["Endpoint scope schematic"], "schematic")
fig, ax = canvas(h=3.8)
box(ax, 0.02, 0.39, 0.23, 0.24, "12 × 1250 waveform\n+ 12-lead mask", fontsize=9)
box(ax, 0.34, 0.65, 0.28, 0.24, "V3F fitted backbone\n+ P6 / P8 specialist")
box(ax, 0.34, 0.17, 0.28, 0.24, "V3AG fitted backbone\n+ P4 specialist")
box(ax, 0.72, 0.65, 0.25, 0.24, "Selected rhythm\nP6: 1643; P8: 2193", fontsize=9)
box(ax, 0.72, 0.17, 0.25, 0.24, "Four binary panels\n962 rows / 733 ECGs", fontsize=9)
for a, b in [
    ((0.25, 0.55), (0.34, 0.76)),
    ((0.25, 0.46), (0.34, 0.29)),
    ((0.62, 0.77), (0.72, 0.77)),
    ((0.62, 0.29), (0.72, 0.29)),
]:
    arrow(ax, a, b)
ax.text(
    0.50,
    0.02,
    "Same architecture design; two separately fitted backbone files.",
    ha="center",
    fontsize=10,
)
save(
    fig,
    "fig01_graphical_abstract",
    ["Verified checkpoint and selected-profile contracts"],
    "schematic",
)
fig, ax = canvas(h=4.3)
for y, t in [
    (0.78, "Physical waveform + named leads"),
    (0.55, "Reconstructed filter / resample / central 10 s / standardize"),
    (0.32, "Waveform 12 × 1250 + lead mask + morphology proxies"),
]:
    box(ax, 0.07, y, 0.86, 0.15, t, fontsize=9.5)
arrow(ax, (0.5, 0.78), (0.5, 0.70))
arrow(ax, (0.5, 0.55), (0.5, 0.47))
for x, t in [
    (0.02, "Historical selected\ndevelopment evaluation"),
    (0.36, "Later retrospective\ntransfer / policy studies"),
    (0.70, "Independent study\nIn progress; no results"),
]:
    box(ax, x, 0.03, 0.28, 0.20, t, fontsize=9)
for x in [0.16, 0.50, 0.84]:
    arrow(ax, (x, 0.32), (x, 0.23))
save(
    fig,
    "fig02_data_processing_bias_workflow",
    ["Reconstructed preprocessing; evidence-stage distinction"],
    "schematic",
)
fig, ax = canvas(w=7.1, h=5.3)
box(
    ax,
    0.03,
    0.84,
    0.94,
    0.13,
    "Waveform + lead mask → ResNet-1D / SE → Transformer\n640-dimensional waveform/mask embedding",
    fontsize=10,
)
rows = [
    (0.65, "640 embedding + 10 morphology = 650", "Global rhythm\n14 outputs"),
    (0.47, "640 embedding only", "Global pathology\n7 outputs"),
    (
        0.29,
        "640 embedding + 10 morphology\n+ 31 score / event context = 681",
        "P6 / P8 specialist\nHidden width 512",
    ),
    (
        0.11,
        "640 embedding + 10 morphology\n+ 20 score context = 670",
        "P4 specialist\nHidden width 512",
    ),
]
for y, inp, consumer in rows:
    box(ax, 0.03, y, 0.61, 0.125, inp, fontsize=9.5)
    box(ax, 0.73, y, 0.24, 0.125, consumer, fontsize=9)
    arrow(ax, (0.64, y + 0.0625), (0.73, y + 0.0625))
ax.text(
    0.5,
    0.018,
    "Specialist morphology occupies indices 640–649; arrows denote actual input tensors.",
    ha="center",
    fontsize=9,
)
save(
    fig,
    "fig03_internal_architecture",
    ["docs/reviewer_two_comment_rigorous/R2_3F_MORPHOLOGY_FINAL_VALIDATION.md"],
    "schematic",
)
fig, ax = canvas(h=4.2)
box(
    ax,
    0.02,
    0.53,
    0.45,
    0.37,
    "Released rhythm reporting\nP6: AFIB, SB, STACH,\nRBBB, 1AVB, PVC\nP8 additionally: NSR, PAC",
    fontsize=9.5,
)
box(
    ax,
    0.53,
    0.53,
    0.45,
    0.37,
    "Released pathology reporting\nP4: ASMI, LVH, IMI, ISC_\nFour separate binary panels",
    fontsize=9.5,
)
box(
    ax,
    0.02,
    0.04,
    0.45,
    0.35,
    "Other declared rhythm outputs\nFlutter, paced, LBBB, 2AVB, 3AVB, LQTS\nExposure ≠ verified supervision",
    color="#F7EFE2",
    fontsize=9,
)
box(
    ax,
    0.53,
    0.04,
    0.45,
    0.35,
    "Other declared pathology outputs\nALMI, ILMI, LAE\nNo released residual Other class",
    color="#F7EFE2",
    fontsize=9,
)
save(fig, "fig03_cascade_contract", ["Verified output ontology; no dispatch inferred"], "schematic")

E = REPO / "outputs/results/external_dev/evidence"


def read(p):
    with open(p, newline="") as handle:
        return list(csv.DictReader(handle))


def split(v):
    return re.split("[|;,]", v)


rhythm = read(E / "rhythm_primary6_record_predictions.csv")
p8 = read(E / "rhythm_primary8_record_predictions.csv")
P6 = ["AFIB", "SB", "STACH", "RBBB", "1AVB", "PVC"]
P4 = ["ASMI", "LVH", "IMI", "ISC_"]
profiles = {"P6": {}, "P4": {}, "P8": {}}
raw = {"P6": {}, "P4": {}, "P8": {}}


def curve(y, p):
    order = np.argsort(-p, kind="stable")
    ys = y[order]
    ps = p[order]
    ends = np.r_[np.flatnonzero(np.diff(ps)), len(ps) - 1]
    tp = np.cumsum(ys)[ends]
    fp = (ends + 1) - tp
    rec = tp / y.sum()
    fpr = fp / (len(y) - y.sum())
    prec = tp / (tp + fp)
    auroc = np.trapezoid(np.r_[0, rec], np.r_[0, fpr])
    ap = np.sum(np.diff(np.r_[0, rec]) * prec)
    return np.r_[0, fpr], np.r_[0, rec], np.r_[1, prec], float(auroc), float(ap)


def metrics(y, p, d):
    tp = int((y & d).sum())
    tn = int((~y & ~d).sum())
    fp = int((~y & d).sum())
    fn = int((y & ~d).sum())
    n = len(y)
    x, r, pr, auc, ap = curve(y, p)
    rng = np.random.default_rng(4620846)
    draws = rng.multinomial(n, np.array([tp, tn, fp, fn]) / n, size=1000)
    f = 2 * draws[:, 0] / np.maximum(2 * draws[:, 0] + draws[:, 2] + draws[:, 3], 1)
    bins = np.minimum((p * 10).astype(int), 9)
    cal = []
    ece = 0
    for b in range(10):
        m = bins == b
        if m.any():
            cal.append([float(p[m].mean()), float(y[m].mean()), int(m.sum())])
            ece += m.mean() * abs(p[m].mean() - y[m].mean())
    return {
        "n": n,
        "positive": int(y.sum()),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": tp / (tp + fp),
        "recall": tp / (tp + fn),
        "specificity": tn / (tn + fp),
        "npv": tn / (tn + fn),
        "f1": 2 * tp / (2 * tp + fp + fn),
        "accuracy": (tp + tn) / n,
        "auroc": auc,
        "ap": ap,
        "brier": float(np.mean((p - y) ** 2)),
        "ece": float(ece),
        "f1_ci": np.quantile(f, [0.025, 0.975]).tolist(),
        "calibration": cal,
    }


for prof, rows, cs in [
    ("P6", rhythm, P6),
    ("P8", p8, ["AFIB", "SB", "STACH", "NSR", "RBBB", "PAC", "1AVB", "PVC"]),
]:
    for c in cs:
        if prof == "P6":
            y = np.array([r["truth_" + c].lower() == "true" for r in rows])
            p = np.array([float(r["prob_" + c]) for r in rows])
            d = np.array([r["threshold_pass_" + c].lower() == "true" for r in rows])
        else:
            y = np.array([c in split(r["accepted_labels"]) for r in rows])
            p = np.array([float(r["membership_prob_" + c]) for r in rows])
            d = np.array([c in split(r["predicted_labels"]) for r in rows])
        raw[prof][c] = (y, p, d)
        profiles[prof][c] = metrics(y, p, d)
for c in P4:
    rows = read(E / f"pathology_primary4_{c}_record_predictions.csv")
    y = np.array([r["target"] == "1" for r in rows])
    p = np.array([float(r["probability"]) for r in rows])
    d = np.array([r["predicted"] == "1" for r in rows])
    raw["P4"][c] = (y, p, d)
    profiles["P4"][c] = metrics(y, p, d)
single = []
cm = np.zeros((6, 6), int)
for r in rhythm:
    labs = [
        v for v in re.split("[|;,]", r["accepted_primary_labels"] or r["true_labels"]) if v in P6
    ]
    if len(labs) == 1:
        single.append(r)
        cm[P6.index(labs[0]), P6.index(r["pred_label"])] += 1
fig, ax = plt.subplots(figsize=(6.4, 4.7))
norm = cm / cm.sum(1)[:, None] * 100
im = ax.imshow(norm, cmap="Blues", vmin=0, vmax=100)
for i in range(6):
    for j in range(6):
        ax.text(
            j,
            i,
            f"{norm[i, j]:.1f}%\n({cm[i, j]})",
            ha="center",
            va="center",
            color="white" if norm[i, j] > 55 else "#222222",
            fontsize=10.5,
        )
ax.set(
    xticks=range(6),
    yticks=range(6),
    xticklabels=P6,
    yticklabels=P6,
    xlabel="Top-1 prediction",
    ylabel="Single accepted reference",
)
ax.set_title(f"P6 single-reference subset: {len(single)} ECGs")
fig.colorbar(im, ax=ax, label="Row percentage", fraction=0.045)
save(
    fig, "fig06_rhythm_confusion", ["Archived P6 record-level predictions; single-reference subset"]
)


def bars(prof, cs, name):
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    x = np.arange(len(cs))
    w = 0.25
    for off, key, color in [
        (-w, "precision", COLORS[0]),
        (0, "recall", COLORS[1]),
        (w, "f1", COLORS[2]),
    ]:
        vals = np.array([profiles[prof][c][key] for c in cs])
        kw = {}
        if key == "f1":
            ci = np.array([profiles[prof][c]["f1_ci"] for c in cs]).T
            kw = {"yerr": np.abs(ci - vals), "capsize": 3, "error_kw": {"lw": 1}}
        ax.bar(x + off, vals, w, label=key.capitalize(), color=color, **kw)
    ax.set(xticks=x, xticklabels=cs, ylim=(0, 1.13), ylabel="Fraction")
    ax.legend(ncols=3, loc="upper right", frameon=False, fontsize=11)
    ax.set_title(prof + " thresholded binary decisions")
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save(
        fig,
        name,
        [
            "Archived "
            + prof
            + " predictions; 1000 confusion-multinomial bootstrap replicates, seed 4620846"
        ],
    )


bars("P6", P6, "fig08_class_metrics")
bars("P4", P4, "fig08b_pathology_class_metrics")
fig, axs = plt.subplots(2, 2, figsize=(6.8, 5.1))
for ax, c in zip(axs.flat, P4, strict=True):
    m = profiles["P4"][c]
    a = np.array([[m["tn"], m["fp"]], [m["fn"], m["tp"]]])
    n = a / a.sum(1)[:, None] * 100
    ax.imshow(n, cmap="Blues", vmin=0, vmax=100)
    for i in range(2):
        for j in range(2):
            ax.text(
                j,
                i,
                f"{n[i, j]:.1f}%\n({a[i, j]})",
                ha="center",
                va="center",
                fontsize=10.5,
                color="white" if n[i, j] > 55 else "#222222",
            )
    ax.set(
        xticks=[0, 1],
        yticks=[0, 1],
        xticklabels=["Negative", "Positive"],
        yticklabels=["Negative", "Positive"],
        xlabel="Prediction",
        ylabel="Reference",
    )
    ax.set_title(f"{c}: n = {m['n']}")
fig.tight_layout()
save(
    fig, "fig07_pathology_confusion", ["Archived P4 panel predictions; panel-specific denominators"]
)
for typ, name in [("roc", "fig09_roc_curves"), ("pr", "fig10_precision_recall_curves")]:
    fig, axs = plt.subplots(1, 2, figsize=(9, 5.2))
    for ax, prof, cs in zip(axs, ["P6", "P4"], [P6, P4], strict=True):
        for c, color in zip(cs, COLORS, strict=False):
            y, p, _ = raw[prof][c]
            x, r, pr, auc, ap = curve(y, p)
            ax.plot(
                x if typ == "roc" else r,
                r if typ == "roc" else pr,
                color=color,
                lw=1.6,
                label=f"{c}: {auc if typ == 'roc' else ap:.3f}",
            )
        if typ == "roc":
            ax.plot([0, 1], [0, 1], ls="--", color="#777777", lw=1)
        ax.set(
            xlim=(-0.02, 1.02),
            ylim=(-0.02, 1.03),
            xlabel="False-positive rate" if typ == "roc" else "Recall",
            ylabel="Sensitivity" if typ == "roc" else "Precision",
        )
        ax.set_title(prof + (" AUROC" if typ == "roc" else " average precision"), fontsize=15)
        ax.legend(fontsize=14, frameon=False, loc="lower right" if typ == "roc" else "lower left")
        ax.grid(alpha=0.18)
        ax.tick_params(labelsize=14)
        ax.xaxis.label.set_fontsize(15)
        ax.yaxis.label.set_fontsize(15)
    fig.tight_layout()
    save(
        fig,
        name,
        [
            "Archived P6/P4 probabilities; grouped distinct score thresholds; AP uses recall-weighted sum"
        ],
    )
fig, axs = plt.subplots(1, 2, figsize=(9, 5.2))
for ax, prof, cs in zip(axs, ["P6", "P4"], [P6, P4], strict=True):
    ax.plot([0, 1], [0, 1], ls="--", color="#777777")
    for c, color in zip(cs, COLORS, strict=False):
        a = np.array(profiles[prof][c]["calibration"])
        ax.plot(a[:, 0], a[:, 1], marker="o", ms=3, lw=1.25, color=color, label=c)
    ax.set(
        xlim=(0, 1),
        ylim=(0, 1),
        xlabel="Mean predicted probability",
        ylabel="Reference-positive fraction",
    )
    ax.set_title(prof + " reliability (10 bins)", fontsize=15)
    ax.legend(fontsize=14, frameon=False, loc="upper left")
    ax.grid(alpha=0.18)
    ax.tick_params(labelsize=14)
    ax.xaxis.label.set_fontsize(15)
    ax.yaxis.label.set_fontsize(15)
fig.tight_layout()
save(
    fig,
    "fig11_calibration",
    ["Archived binary probabilities; 10 equal-width bins; nonempty bins only"],
)


def wilson(k, n):
    p = k / n
    z = 1.96
    cen = (p + z * z / (2 * n)) / (1 + z * z / n)
    rad = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return cen - rad, cen + rad


groups = collections.defaultdict(list)
for r in rhythm:
    groups[r["source"]].append(r)
source_rows = []
for source, rs in sorted(groups.items(), key=lambda x: -len(x[1])):
    n = len(rs)
    k = sum(r["correct"].lower() == "true" for r in rs)
    lo, hi = wilson(k, n)
    source_rows.append(
        {"source": source, "n": n, "correct": k, "accuracy": k / n, "lo": lo, "hi": hi}
    )
names = {
    "chapman_shaoxing": "Chapman–Shaoxing",
    "codetest_zenodo_3765780": "CODE test",
    "data_test": "Mixed local",
    "CPSC2018": "CPSC2018",
    "CPSC2018_Extra": "CPSC Extra",
    "Georgia": "Georgia",
    "Ningbo": "Ningbo",
    "PTBXL": "PTB-XL",
    "training/ptb-xl": "PTB-XL alias",
    "training/ningbo": "Ningbo",
    "training/cpsc_2018_extra": "CPSC Extra",
    "training/georgia": "Georgia",
    "training/cpsc_2018": "CPSC2018",
}
fig, ax = plt.subplots(figsize=(7, 4))
pos = np.arange(len(source_rows))
v = np.array([r["accuracy"] for r in source_rows])
lo = np.array([r["lo"] for r in source_rows])
hi = np.array([r["hi"] for r in source_rows])
labels = [names.get(r["source"], r["source"]) + f" ({r['correct']}/{r['n']})" for r in source_rows]
ax.errorbar(v, pos, xerr=[v - lo, hi - v], fmt="o", color=COLORS[0], capsize=3)
ax.set(
    yticks=pos, yticklabels=labels, xlim=(0, 1.04), xlabel="Top-1 accuracy with Wilson 95% interval"
)
ax.invert_yaxis()
ax.grid(axis="x", alpha=0.2)
fig.tight_layout()
save(
    fig,
    "fig12_source_performance",
    ["Archived P6 source aliases and correctness; Wilson ECG intervals"],
)
errors = collections.Counter()
for i, a in enumerate(P6):
    for j, b in enumerate(P6):
        if i != j and cm[i, j]:
            errors[(a, b)] = int(cm[i, j])
e = errors.most_common(10)
fig, ax = plt.subplots(figsize=(6.8, 4))
y = np.arange(len(e))
ax.barh(y, [v for _, v in e], color=COLORS[1])
ax.set(
    yticks=y,
    yticklabels=[a + " → " + b for (a, b), v in e],
    xlabel="Misclassified ECGs (single-reference subset)",
)
ax.invert_yaxis()
ax.xaxis.get_major_locator().set_params(integer=True)
for i, (_, v) in enumerate(e):
    ax.text(v + 0.25, i, str(v), va="center")
ax.set_xlim(0, max(v for _, v in e) * 1.15)
ax.grid(axis="x", alpha=0.15)
ax.set_axisbelow(True)
fig.tight_layout()
save(
    fig,
    "fig13_error_flows",
    ["Archived P6 single-reference top-1 confusions; ten largest observed counts"],
)
rows = read(HERE / "supplementary/JOB_16768_AGGREGATE_EPOCHS.csv")
fig, axs = plt.subplots(1, 2, figsize=(8.5, 3.6))
epochs = [int(r["epoch"]) for r in rows]
for key, col, lab in [
    ("p8_macro_f1", COLORS[0], "P8 macro-F1"),
    ("p4_macro_f1", COLORS[1], "P4 macro-F1"),
    ("composite", COLORS[2], "Logged composite"),
]:
    axs[0].plot(epochs, [float(r[key]) for r in rows], label=lab, color=col)
for key, col, lab in [("train_loss", COLORS[0], "Train"), ("val_loss", COLORS[1], "Validation")]:
    axs[1].plot(epochs, [float(r[key]) for r in rows], label=lab, color=col)
axs[0].set(xlabel="Epoch", ylabel="Internal score", ylim=(0, 1))
axs[1].set(xlabel="Epoch", ylabel="Logged loss")
for ax in axs:
    ax.legend(frameon=False, fontsize=12)
    ax.grid(alpha=0.2)
    ax.tick_params(labelsize=12)
    ax.xaxis.label.set_fontsize(13)
    ax.yaxis.label.set_fontsize(13)
fig.tight_layout()
save(
    fig,
    "fig16768_internal_history",
    ["supplementary/JOB_16768_AGGREGATE_EPOCHS.csv; historical internal run only"],
)
summary = {
    "profiles": profiles,
    "P6_top1": sum(r["correct"].lower() == "true" for r in rhythm) / len(rhythm),
    "single_reference_n": len(single),
    "P6_confusion": cm.tolist(),
    "source_rows": source_rows,
    "P4_distinct_ecg": len(
        {
            r["record_base"]
            for c in P4
            for r in read(E / f"pathology_primary4_{c}_record_predictions.csv")
        }
    ),
    "inputs_sha256": {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [
            E / "rhythm_primary6_record_predictions.csv",
            E / "rhythm_primary8_record_predictions.csv",
        ]
        + [E / f"pathology_primary4_{c}_record_predictions.csv" for c in P4]
    },
}
assert len(rhythm) == 1643 and sum(r["correct"].lower() == "true" for r in rhythm) == 1564
assert summary["P4_distinct_ecg"] == 733
assert abs(np.mean([v["f1"] for v in profiles["P6"].values()]) - 0.8009383239876123) < 1e-10
assert abs(np.mean([v["f1"] for v in profiles["P4"].values()]) - 0.7934563704) < 1e-8
(HERE / "supplementary/INDEPENDENT_AGGREGATE_RECALCULATION.json").write_text(
    json.dumps(summary, indent=2)
)
# Retain the authenticated CODE plots alongside the regenerated release plots.
# These public package figures have their own source and checksums.
for source, target in (
    ("figure_03_sensitivity_ppv", "fig_code_sensitivity_ppv"),
    ("figure_05_observed_precision_recall", "fig_code_observed_pr"),
):
    for ext in ("pdf", "png"):
        data = (REPO / "docs/external_evidence/figures" / f"{source}.{ext}").read_bytes()
        (FIG / f"{target}.{ext}").write_bytes(data)
    inventory.append({
        "file": target,
        "kind": "authenticated aggregate result",
        "sources": [f"docs/external_evidence/figures/{source}.pdf",
                    "PR10 source commit 63c74b3fde2c51f7f8cde4ad396d77a1bd16cb29"],
        "creator": "Supplied public evidence package; copied byte-for-byte",
        "pdf_sha256": hashlib.sha256((FIG / f"{target}.pdf").read_bytes()).hexdigest(),
        "png_sha256": hashlib.sha256((FIG / f"{target}.png").read_bytes()).hexdigest(),
    })
(HERE / "audit/FIGURE_MANIFEST.json").write_text(json.dumps(inventory, indent=2))
(FIG / "figure_manifest.json").write_text(
    json.dumps(
        {
            "schema": "TITAN_LIFE_REVISION_DRAFT_FIGURES_V1",
            "files": {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(FIG.iterdir())
                if p.suffix in {".pdf", ".png"}
            },
        },
        indent=2,
    )
)
print(
    json.dumps(
        {
            "figures": len(inventory),
            "single_reference_n": len(single),
            "P4_unique": summary["P4_distinct_ecg"],
            "macro_ap": {k: np.mean([m["ap"] for m in v.values()]) for k, v in profiles.items()},
        },
        indent=2,
    )
)
