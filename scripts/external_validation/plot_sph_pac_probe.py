"""Validate and render aggregate-only figures for the exploratory SPH PAC probe."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

METRICS = (
    "accuracy",
    "sensitivity",
    "specificity",
    "precision",
    "recall",
    "f1",
    "auroc",
    "average_precision",
    "brier_score",
    "ece",
)
MODELS = {
    "weighted_l2_logistic": ("Weighted L2 logistic", "#126782", "o", -0.11),
    "fixed_mlp_sensitivity": ("Fixed MLP (sensitivity analysis)", "#C44735", "s", 0.11),
}
IDENTIFIER_KEYS = {"record_id", "patient_id", "ecg_id", "subject_id", "study_id"}
SPH_RECORD_ID = re.compile(r"(?<![A-Za-z0-9])A[0-9]{5}(?![A-Za-z0-9])")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _reject_nonfinite(value: str):
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _read_json(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    value = json.loads(raw, parse_constant=_reject_nonfinite)
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path.name}")
    return value, raw


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _metric_close(observed: float, expected: float) -> bool:
    return math.isclose(float(observed), float(expected), rel_tol=0, abs_tol=1e-9)


def _inspect_identifiers(value) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in IDENTIFIER_KEYS or SPH_RECORD_ID.search(str(key)):
                raise ValueError("individual identifier field found in public JSON")
            _inspect_identifiers(child)
    elif isinstance(value, list):
        for child in value:
            _inspect_identifiers(child)
    elif isinstance(value, str) and SPH_RECORD_ID.search(value):
        raise ValueError("individual SPH record identifier found in public JSON")


def _validate_confusion_and_metrics(package: dict, expected_config: dict) -> None:
    points = package.get("point_estimates")
    bootstrap = package.get("patient_cluster_bootstrap")
    _require(isinstance(points, dict), "missing point estimates")
    _require(isinstance(bootstrap, dict), "missing patient-cluster bootstrap")

    n = points.get("n")
    support = points.get("support")
    confusion = points.get("confusion")
    _require(_is_int(n) and n > 0, "invalid scored-record denominator")
    _require(isinstance(support, dict), "missing endpoint support")
    _require(isinstance(confusion, dict), "missing confusion counts")
    for name in ("positive", "negative"):
        _require(_is_int(support.get(name)) and support[name] >= 0, "invalid class support")
    for name in ("tp", "fp", "tn", "fn"):
        _require(_is_int(confusion.get(name)) and confusion[name] >= 0,
                 "invalid confusion count")

    tp, fp, tn, fn = (confusion[name] for name in ("tp", "fp", "tn", "fn"))
    positives = tp + fn
    negatives = tn + fp
    _require(n == positives + negatives, "confusion counts do not match denominator")
    _require(support["positive"] == positives and support["negative"] == negatives,
             "support does not match confusion counts")

    denominators = {
        "accuracy": (tp + tn, n),
        "sensitivity": (tp, positives),
        "specificity": (tn, negatives),
        "precision": (tp, tp + fp),
        "recall": (tp, positives),
        "f1": (2 * tp, 2 * tp + fp + fn),
    }
    for metric, (numerator, denominator) in denominators.items():
        _require(denominator > 0, f"cannot verify {metric} with zero support")
        _require(_metric_close(points.get(metric), numerator / denominator),
                 f"{metric} does not reconcile with confusion counts")
    for metric in METRICS:
        value = points.get(metric)
        _require(isinstance(value, (float, int)) and not isinstance(value, bool)
                 and math.isfinite(value) and 0 <= value <= 1,
                 f"invalid point estimate for {metric}")

    _require(bootstrap.get("unit") == expected_config["unit"],
             "bootstrap unit differs from frozen protocol")
    _require(bootstrap.get("method") == expected_config["method"],
             "bootstrap method differs from frozen protocol")
    _require(bootstrap.get("replicates_requested") == expected_config["replicates"],
             "bootstrap replicate count differs from frozen protocol")
    _require(bootstrap.get("seed") == expected_config["seed"],
             "bootstrap seed differs from frozen protocol")
    _require(bootstrap.get("confidence_level") == expected_config["confidence_level"],
             "bootstrap confidence level differs from frozen protocol")

    intervals = bootstrap.get("intervals")
    _require(isinstance(intervals, dict), "missing bootstrap intervals")
    for metric in METRICS:
        interval = intervals.get(metric)
        _require(isinstance(interval, dict), f"missing bootstrap interval for {metric}")
        low, high = interval.get("lower"), interval.get("upper")
        valid, invalid = interval.get("valid_replicates"), interval.get("invalid_replicates")
        _require(all(isinstance(item, (int, float)) and math.isfinite(item)
                     for item in (low, high)), f"invalid bootstrap limits for {metric}")
        _require(0 <= low <= high <= 1, f"out-of-range bootstrap limits for {metric}")
        _require(_is_int(valid) and _is_int(invalid)
                 and valid + invalid == expected_config["replicates"] and valid > 0,
                 f"bootstrap replicate accounting failed for {metric}")


def validate_public_pac_artifacts(
    aggregate_path: Path,
    receipt_path: Path,
    protocol_config_path: Path,
) -> dict:
    """Validate receipt hashes, frozen protocol links, aggregate counts and metrics."""
    aggregate_path = Path(aggregate_path)
    receipt_path = Path(receipt_path)
    protocol_config_path = Path(protocol_config_path)
    aggregate, aggregate_bytes = _read_json(aggregate_path)
    receipt, receipt_bytes = _read_json(receipt_path)
    config, _config_bytes = _read_json(protocol_config_path)
    aggregate_sha256 = _sha256_bytes(aggregate_bytes)
    receipt_sha256 = _sha256_bytes(receipt_bytes)
    config_sha256 = _sha256_file(protocol_config_path)

    _require(aggregate.get("schema") == "TITAN_V45_SPH_PAC_PROBE_AGGREGATE_V1",
             "unexpected aggregate schema")
    _require(receipt.get("schema") == "TITAN_V45_SPH_PAC_PROBE_RECEIPT_V1",
             "unexpected execution receipt schema")
    _require(receipt.get("public_aggregate_sha256") == aggregate_sha256,
             "aggregate SHA-256 does not match execution receipt")
    _require(receipt.get("protocol_config_sha256") == config_sha256,
             "protocol configuration SHA-256 does not match execution receipt")
    _require(re.fullmatch(r"[0-9a-f]{40}", str(receipt.get("protocol_commit", ""))) is not None,
             "invalid frozen protocol commit")
    _require(receipt.get("v3f_checkpoint_sha256") == config["model"]["sha256"],
             "checkpoint hash does not match frozen protocol")
    _require(receipt.get("source_sha256") == config["source"]["sha256"],
             "SPH source hashes do not match frozen protocol")
    _require(receipt.get("dependency_archive_sha256")
             == {"python_deps": config["environment"]["dependency_archive_sha256"]["python_deps"]},
             "dependency archive hash does not match frozen protocol")
    for key, expected in config["environment"]["versions"].items():
        if key in receipt.get("runtime", {}):
            _require(receipt["runtime"][key] == expected,
                     f"runtime {key} does not match frozen protocol")
    _require(receipt.get("mimic_data_consulted") is False,
             "MIMIC data must not be represented as consulted")
    _require(receipt.get("threshold_or_model_tuning_on_holdout") is False,
             "holdout tuning is prohibited by the frozen protocol")
    _require(receipt.get("row_level_data_in_repository") is False,
             "row-level data must remain outside the public repository")
    _require(receipt.get("labels_used_for_head_fitting") is True,
             "receipt must disclose training-label use for probe fitting")

    _inspect_identifiers(aggregate)
    _inspect_identifiers(receipt)
    _require(aggregate.get("status") == "exploratory_patient_split_holdout",
             "aggregate status must remain exploratory")
    _require(aggregate.get("patient_or_record_identifiers_present") is False
             and aggregate.get("row_level_predictions_present") is False
             and aggregate.get("probe_weights_present") is False,
             "aggregate privacy declarations are not safe")
    _require(aggregate.get("target") == (
        "SPH primary code 30; code 31 excluded; ECG statement, not clinical adjudication"
    ), "unexpected target definition")

    source = aggregate.get("source", {})
    split = aggregate.get("split", {})
    expected_records = config["source"]["expected_records"]
    for field in ("metadata_records", "embedding_eligible_records", "embedding_rows"):
        _require(source.get(field) == expected_records, "source record counts do not reconcile")
    _require(source.get("technical_status_counts") == {"embedded": expected_records},
             "technical embedding statuses do not reconcile")
    _require(source.get("unique_source_patients_in_eligible_rows")
             == config["source"]["expected_patients"], "unique patient count differs from protocol")
    _require(_is_int(source.get("window_count_total")) and source["window_count_total"] > 0,
             "invalid total window count")
    _require(split.get("train_records", 0) + split.get("holdout_records", 0) == expected_records,
             "train and holdout records do not reconcile to source population")
    _require(split.get("train_patient_count", 0) + split.get("holdout_patient_count", 0)
             == source["unique_source_patients_in_eligible_rows"],
             "train and holdout patient counts do not reconcile")
    _require(split.get("seed") == config["split"]["seed"]
             and split.get("train_fraction") == config["split"]["train_fraction"],
             "split parameters differ from frozen protocol")
    _require(split.get("train_positive", 0) + split.get("train_negative", 0)
             == split.get("train_records")
             and split.get("holdout_positive", 0) + split.get("holdout_negative", 0)
             == split.get("holdout_records"), "split class supports do not reconcile")
    _require(split.get("holdout_positive") > 0 and split.get("holdout_negative") > 0,
             "both endpoint classes must occur in holdout")

    duplicates = aggregate.get("duplicate_audit", {})
    duplicate_config = config["duplicate_policy"]
    _require(duplicates.get("exact_duplicate_groups")
             == duplicate_config["expected_exact_duplicate_groups"]
             and duplicates.get("cross_patient_exact_duplicate_groups")
             == duplicate_config["expected_cross_patient_exact_groups"]
             and duplicates.get("groups_with_pac_label_conflict")
             == duplicate_config["expected_pac_discordant_exact_groups"],
             "duplicate audit differs from frozen pre-performance controls")

    models = aggregate.get("models", {})
    _require(set(models) == set(MODELS), "unexpected PAC probe model set")
    interval_config = config["metrics"]["intervals"]
    for name, report in models.items():
        _require(set(report) == {
            "holdout", "holdout_without_pac_discordant_exact_duplicate_groups"
        }, f"unexpected report scopes for {name}")
        for scope_name, package in report.items():
            expected_config = {
                "unit": interval_config["unit"],
                "method": interval_config["method"],
                "replicates": interval_config["replicates"],
                "seed": interval_config["seed"],
                "confidence_level": interval_config["confidence_level"],
            }
            _validate_confusion_and_metrics(package, expected_config)
            if scope_name == "holdout":
                points = package["point_estimates"]
                _require(points["n"] == split["holdout_records"]
                         and points["support"]["positive"] == split["holdout_positive"]
                         and points["support"]["negative"] == split["holdout_negative"],
                         f"{name} holdout denominator or support mismatch")
            else:
                _require(package["point_estimates"]["n"]
                         == split["holdout_records"]
                         - duplicates["holdout_rows_excluded_in_sensitivity"],
                         f"{name} duplicate-sensitivity denominator mismatch")

    return {
        "aggregate": aggregate,
        "receipt": receipt,
        "aggregate_sha256": aggregate_sha256,
        "execution_receipt_sha256": receipt_sha256,
        "protocol_config_sha256": config_sha256,
    }


def _draw_metric_panel(axis, models: dict, metric_names: tuple[str, ...], title: str) -> None:
    y_positions = list(range(len(metric_names)))
    for model_name, (display, color, marker, offset) in MODELS.items():
        package = models[model_name]["holdout"]
        points = package["point_estimates"]
        intervals = package["patient_cluster_bootstrap"]["intervals"]
        for index, metric in enumerate(metric_names):
            value = points[metric]
            interval = intervals[metric]
            low, high = interval["lower"], interval["upper"]
            y = index + offset
            axis.hlines(y, low, high, color=color, linewidth=1.6, zorder=2)
            axis.vlines((low, high), y - 0.055, y + 0.055, color=color, linewidth=1.2, zorder=2)
            axis.plot(value, y, marker=marker, color=color, markersize=6,
                      linestyle="none", label=display if index == 0 else None, zorder=3)

    axis.set_xlim(0, 1.03)
    axis.set_ylim(-0.42, len(metric_names) - 0.58)
    axis.set_yticks(y_positions, [name.replace("_", " ").title() for name in metric_names])
    axis.invert_yaxis()
    axis.set_xlabel("Estimate and 95% patient-component bootstrap interval")
    axis.set_title(title)
    axis.grid(axis="x", color="#D9E0E3", linewidth=0.8, alpha=0.8)
    axis.set_axisbelow(True)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.tick_params(axis="y", length=0, pad=8)
    axis.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1.0))


def _render_figure(aggregate: dict, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    points = aggregate["models"]["weighted_l2_logistic"]["holdout"]["point_estimates"]
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.4))
    _draw_metric_panel(axes[0], aggregate["models"], ("auroc", "average_precision"),
                       "Discrimination")
    _draw_metric_panel(axes[1], aggregate["models"],
                       ("sensitivity", "specificity", "precision", "f1"),
                       "Operating point (threshold = 0.50)")
    fig.suptitle("SPH primary-code 30 PAC statement probe", fontsize=14, y=0.97)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.91),
               ncol=2, frameon=False)
    fig.text(0.5, 0.105,
             f"Exploratory holdout: n={points['n']:,} ECG statements; "
             f"{points['support']['positive']:,} positive, {points['support']['negative']:,} negative",
             ha="center", fontsize=9)
    fig.text(0.5, 0.055,
             "Not clinical adjudication or independent external validation; "
             "PAC target was previously inspected.",
             ha="center", fontsize=8.5, color="#40484C")
    fig.subplots_adjust(left=0.13, right=0.98, top=0.79, bottom=0.23, wspace=0.34)

    outputs = [output_dir / "sph_pac_probe_exploratory.png",
               output_dir / "sph_pac_probe_exploratory.pdf"]
    fig.savefig(outputs[0], dpi=240, bbox_inches="tight",
                metadata={"Software": "TITAN V4.5 PAC aggregate postprocessor",
                          "Title": "Exploratory SPH PAC probe"})
    fig.savefig(outputs[1], bbox_inches="tight",
                metadata={"Creator": "TITAN V4.5 PAC aggregate postprocessor",
                          "Title": "Exploratory SPH PAC probe",
                          "CreationDate": None, "ModDate": None})
    plt.close(fig)
    return outputs


def generate_report(
    aggregate_path: Path,
    receipt_path: Path,
    protocol_config_path: Path,
    output_dir: Path,
) -> dict:
    checked = validate_public_pac_artifacts(aggregate_path, receipt_path, protocol_config_path)
    output_dir = Path(output_dir)
    outputs = _render_figure(checked["aggregate"], output_dir)
    figures = {
        path.name: {"bytes": path.stat().st_size, "sha256": _sha256_file(path)}
        for path in outputs
    }
    generator_path = Path(__file__).resolve()
    manifest = {
        "schema": "TITAN_V45_SPH_PAC_FIGURE_MANIFEST_V1",
        "status": "exploratory_aggregate_only_postprocessing",
        "inputs": {
            "aggregate_sha256": checked["aggregate_sha256"],
            "execution_receipt_sha256": checked["execution_receipt_sha256"],
            "protocol_config_sha256": checked["protocol_config_sha256"],
            "protocol_commit": checked["receipt"]["protocol_commit"],
            "embedding_archive_sha256": checked["receipt"]["embedding_archive_sha256"],
            "embedding_receipt_sha256": checked["receipt"]["embedding_receipt_sha256"],
            "v3f_checkpoint_sha256": checked["receipt"]["v3f_checkpoint_sha256"],
            "cedia_fit_job_id": checked["receipt"]["slurm_job_id"],
        },
        "generator": {
            "path": "scripts/external_validation/plot_sph_pac_probe.py",
            "sha256": _sha256_file(generator_path),
            "python": platform.python_version(),
            "matplotlib": matplotlib.__version__,
        },
        "figures": figures,
        "privacy": {
            "individual_identifiers_present": False,
            "row_level_predictions_present": False,
            "probe_weights_present": False,
            "mimic_data_consulted": False,
        },
        "interpretation": (
            "Exploratory SPH primary-code 30 statement endpoint; not clinical adjudication "
            "or independent external validation."
        ),
    }
    manifest_path = output_dir / "pac_probe_figure_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aggregate", type=Path,
                        default=root / "outputs/results/external_sph_pac/pac_probe_aggregate.json")
    parser.add_argument("--receipt", type=Path,
                        default=root / "outputs/results/external_sph_pac/pac_probe_receipt.json")
    parser.add_argument("--protocol-config", type=Path,
                        default=root / "configs/external_validation/pac_v3f_embedding_probe.json")
    parser.add_argument("--output-dir", type=Path,
                        default=root / "outputs/figures/external_sph_pac")
    args = parser.parse_args()
    result = generate_report(args.aggregate, args.receipt, args.protocol_config, args.output_dir)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
