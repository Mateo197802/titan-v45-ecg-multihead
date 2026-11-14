"""Recompute shareable tables and figures from archived decisions, never from ECGs."""
import hashlib
import json
import re
from zipfile import ZipFile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reviewer_map import REPO, ROOT
from sklearn.metrics import (
    average_precision_score,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)

EVIDENCE = REPO / "outputs/results/external_dev"
RELEASE = REPO / "outputs/models/release_weight_manifest.json"
FIGURES = ROOT / "latex/figures"
GENERATED = ROOT / "latex/tables"


def sha(path):
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()


def pct(value):
    return rf"{100 * value:.2f}\%"


def tex(value):
    return str(value).replace("_", r"\_").replace("&", r"\&")


def table(caption, label, columns, rows, layout=None):
    layout = layout or ("l" + "r" * (len(columns) - 1))
    return "\n".join([
        r"\begin{table}[htbp]", rf"\caption{{{caption}\label{{{label}}}}}",
        r"\centering\small", rf"\begin{{tabular}}{{{layout}}}", r"\toprule",
        " & ".join(columns) + r" \\", r"\midrule",
        *(" & ".join(map(str, row)) + r" \\" for row in rows),
        r"\bottomrule", r"\end{tabular}", r"\end{table}",
    ])


def save(fig, name):
    fig.savefig(FIGURES / (name + ".pdf"), bbox_inches="tight", metadata={"CreationDate": None})
    fig.savefig(FIGURES / (name + ".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)


def binary(y, decision, score):
    tp, tn = np.sum(y & decision), np.sum(~y & ~decision)
    fp, fn = np.sum(~y & decision), np.sum(y & ~decision)
    return dict(tp=int(tp), tn=int(tn), fp=int(fp), fn=int(fn),
                precision=tp / (tp + fp), recall=tp / (tp + fn), specificity=tn / (tn + fp),
                f1=2 * tp / (2 * tp + fp + fn), accuracy=(tp + tn) / len(y),
                auroc=roc_auc_score(y, score), ap=average_precision_score(y, score),
                brier=np.mean((score - y) ** 2), n=len(y))


def wilson(k, n):
    z = 1.95996398454
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2*n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z*z / (4*n*n)) / den
    return center - half, center + half


def ci_f1(metric, rng):
    # Row bootstrap conditional on the observed panel; not a patient-level interval.
    n = metric["n"]
    a = rng.multinomial(n, [metric[k] / n for k in ("tp", "tn", "fp", "fn")], 1000)
    d = 2*a[:, 0] + a[:, 2] + a[:, 3]
    return np.quantile(np.divide(2*a[:, 0], d, out=np.zeros(len(d)), where=d > 0), [.025, .975])


def historic_training():
    archive = REPO.parent / "TITAN_V45_FINAL_EVIDENCE_20261111_SHAREABLE.zip"
    member = "RECOVERED_ORIGINALS/slurm-16768.out"
    with ZipFile(archive) as package:
        raw = package.read(member)
    pat = r"^Epoch (\d+)/50: score=(\d+\.\d+) p8_f1=(\d+\.\d+) path4_f1=(\d+\.\d+).*?train_loss=(\d+\.\d+) val_loss=(\d+\.\d+)"
    rows = re.findall(pat, raw.decode(), re.M)
    assert [int(r[0]) for r in rows] == list(range(1,51))
    trace = np.asarray(rows, dtype=float)
    fig, axes = plt.subplots(2, 1, figsize=(7.1, 5.1), sharex=True, layout="constrained")
    for ax, keys, ylabel in [(axes[0], ("Composite", "P8 macro-F1", "P4 macro-F1"), "Validation score"),
                             (axes[1], ("Train loss", "Validation loss"), "Recorded loss")]:
        start = 1 if ax is axes[0] else 4
        for idx, key in enumerate(keys, start):
            ax.plot(trace[:,0], trace[:,idx], lw=1.6, label=key)
        ax.set(ylabel=ylabel, xlim=(1,50))
        ax.legend(ncol=len(keys), loc="best", frameon=False)
    axes[1].set(xlabel="Epoch")
    save(fig, "fig16768_internal_history")
    (ROOT / "JOB_16768_AGGREGATE_EPOCHS.csv").write_text(
        "epoch,composite,p8_macro_f1,p4_macro_f1,train_loss,val_loss\n"+
        "\n".join(",".join(r) for r in rows)+"\n", encoding="ascii")
    return {"archive": archive.name, "archive_sha256": sha(archive), "member": member,
            "member_sha256": hashlib.sha256(raw).hexdigest(), "epochs": len(rows)}


def class_plot(metrics, name, rng):
    fig, ax = plt.subplots(figsize=(7.3, 3.1), layout="constrained")
    x = np.arange(len(metrics))
    for j, (key, color) in enumerate([("precision", "#2c5282"), ("recall", "#19796c"), ("f1", "#b56836")]):
        values = [m[key] for m in metrics.values()]
        err = np.abs(np.asarray([ci_f1(m, rng) for m in metrics.values()]).T - values) if key == "f1" else None
        ax.bar(x + (j-1)*.24, values, .23, color=color, label=key.capitalize(), yerr=err, capsize=3)
    ax.set(xticks=x, xticklabels=list(metrics), ylim=(0, 1.10), ylabel="Score")
    ax.legend(ncol=3, loc="lower center", bbox_to_anchor=(.5, 1.01), frameon=False)
    save(fig, name)


def matrix(ax, values, ticks, title):
    m = values / values.sum(axis=1, keepdims=True).clip(1)
    ax.imshow(m, vmin=0, vmax=1, cmap="Blues")
    for (i, j), v in np.ndenumerate(m):
        ax.text(j, i, f"{100*v:.0f}%", ha="center", va="center", color="white" if v > .55 else "#15222d")
    ax.set(xticks=range(len(ticks)), yticks=range(len(ticks)), xticklabels=ticks, yticklabels=ticks,
           title=title, xlabel="Predicted", ylabel="Reference")


def build_data():
    FIGURES.mkdir(parents=True, exist_ok=True)
    GENERATED.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(4620846)
    inputs = [RELEASE]
    profiles = {}
    vectors = {}
    metrics = {}
    for p in (6, 8):
        config = EVIDENCE / f"rhythm_primary{p}_metrics.json"
        pred = EVIDENCE / f"evidence/rhythm_primary{p}_record_predictions.csv"
        inputs += [config, pred]
        cfg, frame = json.loads(config.read_text()), pd.read_csv(pred)
        classes = cfg["classes"]
        profiles[p] = cfg, frame
        vectors[p] = {}
        metrics[p] = {}
        for c, t in zip(classes, cfg["thresholds"], strict=True):
            y = (frame[f"truth_{c}"].to_numpy(dtype=bool) if p == 6 else
                 frame.accepted_labels.str.split("|", regex=False).map(lambda labels, c=c: c in labels).to_numpy())
            s = frame[f"{'membership_' if p == 8 else ''}prob_{c}"].to_numpy()
            d = s >= t
            vectors[p][c] = (y, s)
            metrics[p][c] = binary(y, d, s)
            if p == 6:
                assert np.array_equal(d, frame[f"threshold_pass_{c}"].to_numpy(dtype=bool))
            else:
                d = frame.predicted_labels.str.split("|", regex=False).map(lambda labels, c=c: c in labels).to_numpy()
                metrics[p][c] = binary(y, d, s)
            assert np.isclose(metrics[p][c]["f1"], cfg["panels"][c]["f1"])
        empty = ~np.column_stack([
            vectors[p][c][1] >= t for c, t in zip(classes, cfg["thresholds"], strict=True)
        ]).any(axis=1)
        correct = frame["correct" if p == 6 else "accepted_correct"]
        assert (int(empty.sum()), int(correct[empty].sum())) == {6:(79,64), 8:(58,22)}[p]
        assert len(frame) == cfg["records"]
        assert np.isclose(correct.mean(), cfg.get("top1_accuracy", cfg.get("top1_accepted_accuracy")))

    config = EVIDENCE / "pathology_primary4_metrics.json"
    inputs.append(config)
    cfg4 = json.loads(config.read_text())
    union = set()
    vectors[4], metrics[4] = {}, {}
    sources4 = {}
    for c, t in zip(cfg4["classes"], cfg4["thresholds"], strict=True):
        pred = EVIDENCE / f"evidence/pathology_primary4_{c}_record_predictions.csv"
        inputs.append(pred)
        frame = pd.read_csv(pred)
        union.update(frame.record_base)
        y, s = frame.target.to_numpy(dtype=bool), frame.probability.to_numpy()
        vectors[4][c] = (y, s)
        assert np.array_equal(s >= t, frame.predicted.to_numpy(dtype=bool))
        metrics[4][c] = binary(y, s >= t, s)
        assert np.isclose(metrics[4][c]["f1"], cfg4["panels"][c]["f1"])
        for src, part in frame.groupby("source"):
            n, k = sources4.get(src, (0, 0))
            sources4[src] = n + len(part), k + int(part.correct.sum())
    assert sum(m["n"] for m in metrics[4].values()) == 962 and len(union) == 733
    assert np.isclose(np.mean([m["accuracy"] for m in metrics[4].values()]), cfg4["mean_accuracy"])

    for p, cfg in [(6, profiles[6][0]), (8, profiles[8][0]), (4, cfg4)]:
        rows = [[tex(c), m["tp"] + m["fn"], m["n"], *[pct(m[k]) for k in
                ("precision", "recall", "specificity", "f1")], f"{t:.3f}"]
                for (c, m), t in zip(metrics[p].items(), cfg["thresholds"], strict=True)]
        (GENERATED / f"classes_p{p}.tex").write_text(table(
            f"P{p} statement-level decisions at the released thresholds. Positives are reference statements.",
            {6:"tab:rhythmclass",4:"tab:pathclass",8:"tab:p8class"}[p],
            ["Class", "Positive", "Total", "Precision", "Recall", "Specificity", "F1", "Cutoff"], rows), encoding="ascii")

    cfg6, p6 = profiles[6]
    src = [(tex(s), len(g), int(g.correct.sum())) for s, g in p6.groupby("source_family")]
    (GENERATED / "p6_sources.tex").write_text(table(
        "P6 selected ECGs by retained source family. Wilson intervals use ECGs, not patients.",
        "tab:app_source_primary6", ["Source family", "ECGs", "Correct", "Top-1", "Wilson 95\\% CI"],
        [[s, n, k, pct(k/n), " to ".join(map(pct, wilson(k,n)))] for s,n,k in src]), encoding="ascii")
    (GENERATED / "p4_sources.tex").write_text(table(
        "P4 retained source alias. Pooled observation accuracy is not the mean of the four panel accuracies.",
        "tab:app_source_primary4", ["Source alias", "Observations", "Correct", "Pooled accuracy"],
        [[tex(s), n, k, pct(k/n)] for s,(n,k) in sorted(sources4.items())]), encoding="ascii")

    classes = cfg6["classes"]
    multi = p6.true_labels.str.contains(r"[|;,]", regex=True).sum()
    cmat = np.array([[int(((p6.true_labels == a) & (p6.pred_label == b)).sum()) for b in classes] for a in classes])
    fig, ax = plt.subplots(figsize=(5.9, 4.0), layout="constrained")
    matrix(ax, cmat, classes, f"P6 top-1: {cmat.sum():,} single-reference ECGs")
    save(fig, "fig06_rhythm_confusion")
    fig, axs = plt.subplots(1, 4, figsize=(8.7, 2.6), layout="constrained")
    for ax, (c, m) in zip(axs, metrics[4].items(), strict=True):
        matrix(ax, np.array([[m["tn"],m["fp"]],[m["fn"],m["tp"]]]), ["Neg.", "Pos."], f"{c} (n={m['n']})")
    save(fig, "fig07_pathology_confusion")
    class_plot(metrics[6], "fig08_class_metrics", rng)
    class_plot(metrics[4], "fig08b_pathology_class_metrics", rng)

    for kind, name in [("roc", "fig09_roc_curves"), ("pr", "fig10_precision_recall_curves"), ("cal", "fig11_calibration")]:
        fig, axs = plt.subplots(1, 2, figsize=(8.1, 3.5), layout="constrained")
        for ax, p in zip(axs, (6, 4), strict=True):
            for c, (y, s) in vectors[p].items():
                if kind == "roc":
                    x, v, _ = roc_curve(y, s)
                elif kind == "pr":
                    v, x, _ = precision_recall_curve(y, s)
                else:
                    bins = np.minimum(np.floor(s * 10).astype(int), 9)
                    x = [s[bins == b].mean() for b in np.unique(bins)]
                    v = [y[bins == b].mean() for b in np.unique(bins)]
                ax.plot(x, v, label=c, lw=1.45, marker="o" if kind == "cal" else None, ms=3)
            if kind in ("roc", "cal"):
                ax.plot([0,1], [0,1], "--", lw=.8, color="gray")
            labels = {"roc":("False-positive rate", "True-positive rate"), "pr":("Recall", "Precision"),
                      "cal":("Mean predicted probability", "Observed positive frequency")}
            ax.set(title=f"Primary{p}", xlim=(0,1), ylim=(0,1.02), xlabel=labels[kind][0], ylabel=labels[kind][1])
            if kind == "cal":
                ax.set(xticks=np.linspace(0,1,11), yticks=np.linspace(0,1,11))
                ax.tick_params(labelsize=7)
            ax.legend(frameon=False, fontsize=8, loc="best")
        save(fig, name)
    fig, ax = plt.subplots(figsize=(7.7, 3.6), layout="constrained")
    for i, (_, n, k) in enumerate(src):
        a,b = wilson(k,n)
        ax.errorbar(k/n, i, xerr=[[k/n-a],[b-k/n]], fmt="o", color="#245785", capsize=3)
    ax.set(yticks=range(len(src)), yticklabels=[f"{s.replace(chr(92),'')} (n={n})" for s,n,_ in src],
           xlim=(-.025,1.025), xlabel="Top-1 accuracy with Wilson 95% interval")
    save(fig, "fig12_source_performance")
    err = sorted([(int(cmat[i,j]), f"{a} → {b}") for i,a in enumerate(classes) for j,b in enumerate(classes)
                  if i != j and cmat[i,j]], reverse=True)[:10][::-1]
    fig, ax = plt.subplots(figsize=(7.4, 3.4), layout="constrained")
    ax.barh([e[1] for e in err], [e[0] for e in err], color="#367b76")
    ax.set(xlabel="Single-reference ECGs", ylabel="Reference → top-1 output")
    save(fig, "fig13_error_flows")
    weights = json.loads(RELEASE.read_text())["weights"]
    (GENERATED / "release_hashes.tex").write_text(table(
        "Verified release v0.1.0 artifacts. Each digest covers the named file only.",
        "tab:app_hashes", ["File", "Bytes", "SHA-256"],
        [[r"\path{" + w["name"] + "}", f"{w['bytes']:,}", r"\path{" + w["sha256"] + "}"] for w in weights],
        r"@{}p{.33\linewidth}rp{.45\linewidth}@{}"), encoding="ascii")
    summary = {f"P{p}": {**m, "macro_f1": float(np.mean([v["f1"] for v in m.values()])),
                         "macro_auroc": float(np.mean([v["auroc"] for v in m.values()])),
                         "macro_ap": float(np.mean([v["ap"] for v in m.values()]))} for p,m in metrics.items()}
    summary["p6_confusion_n"] = int(cmat.sum())
    summary["p6_non_single_label_indicator_count"] = int(multi)
    sph = REPO / "outputs/results/external_sph/sph_aggregate_32669.json"
    inputs.append(sph)
    rows = []
    for endpoint, result in json.loads(sph.read_text())["endpoints"].items():
        if not result["scored_evaluable_records"]:
            continue
        m = result["metrics"]
        ci = result["cluster_bootstrap_ci95"]["f1"]
        rows.append([tex(endpoint), f"{m['positive_support']:,}", pct(m["precision"]),
                     pct(m["recall"]), pct(m["tn"]/(m["tn"]+m["fn"])), pct(m["f1"]),
                     f"{pct(ci['low'])}--{pct(ci['high'])}"])
    (GENERATED / "sph_endpoints.tex").write_text(table(
        "Retrospective SPH full-denominator mapped endpoints. Each row contains 25,770 ECG statements. "
        "F1 intervals use 2,000 patient and duplicate component bootstrap draws. Unmapped endpoints are omitted.",
        "tab:sph_endpoints", ["Endpoint", "Positive", "PPV", "Recall", "NPV", "F1", "F1 95\\% CI"], rows), encoding="ascii")
    summary["source_hashes"] = {str(p.relative_to(REPO)).replace(chr(92),"/"): sha(p) for p in inputs}
    summary["job_16768"] = historic_training()
    (ROOT / "RELEASE_RECALCULATION.json").write_text(json.dumps(summary, indent=2, default=lambda v: v.item())+"\n")
    return summary


if __name__ == "__main__":
    build_data()
