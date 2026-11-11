"""Train frozen-backbone specialist heads and write privacy-safe evaluations."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.evaluation.revision_report import binary_metrics  # noqa: E402
from titan_v45.evaluation.specialist_heads import (  # noqa: E402
    bootstrap_binary_metrics,
    class_metrics,
    paired_bootstrap_metric_differences,
    select_f1_threshold,
)
from titan_v45.models.frozen_rhythm import aggregate_rhythm  # noqa: E402
from titan_v45.training.specialist_heads import (  # noqa: E402
    P4_CLASSES,
    RHYTHM_CLASSES_P6,
    RHYTHM_CLASSES_P8,
    fit_classwise_binary_head,
    source_balanced_element_weights,
)

CONFIG = ROOT / "configs/specialist_heads/study_20261111_v2.json"
BOOTSTRAP_REPLICATES = 2000
BOOTSTRAP_SEED = 20261111


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_revision(repo: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, suffix=".json",
                            delete=False) as temp:
        temp_path = Path(temp.name)
        json.dump(payload, temp, sort_keys=True, indent=2)
        temp.write("\n")
        temp.flush()
        os.fsync(temp.fileno())
    os.chmod(temp_path, 0o600)
    temp_path.replace(path)


def _atomic_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0]) if rows else []
    with NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=path.parent,
                            suffix=".csv", delete=False) as temp:
        temp_path = Path(temp.name)
        writer = csv.DictWriter(temp, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        temp.flush()
        os.fsync(temp.fileno())
    os.chmod(temp_path, 0o600)
    temp_path.replace(path)


def _metadata_classes(records: list[dict[str, Any]], task: str) -> tuple[str, ...]:
    expected = P4_CLASSES if task == "pathology" else RHYTHM_CLASSES_P8
    if any(tuple(row["classes"]) != expected for row in records):
        raise ValueError(f"unexpected {task} class order in private feature metadata")
    return expected


def _selected_window_rows(record_index: np.ndarray, selected_records: set[int]) -> np.ndarray:
    return np.flatnonzero(np.isin(record_index, np.fromiter(selected_records, dtype=np.int32)))


def _targets_by_index(records: list[dict[str, Any]], indices: np.ndarray, columns: list[int]):
    targets, masks, sources, groups, window_weights = [], [], [], [], []
    counts = Counter(indices.tolist())
    for record_index in indices.tolist():
        row = records[record_index]
        targets.append([row["targets"][column] for column in columns])
        masks.append([row["mask"][column] for column in columns])
        sources.append(row["source"])
        groups.append(row["identity_hash"])
        window_weights.append(1.0 / counts[record_index])
    return (np.asarray(targets, dtype=np.float32), np.asarray(masks, dtype=bool),
            sources, groups, np.asarray(window_weights, dtype=np.float32))


def _train_rhythm_variant(
    profile: str,
    loss_name: str,
    seed: int,
    records: list[dict[str, Any]],
    feature_matrix: np.ndarray,
    window_records: np.ndarray,
    *,
    device: str,
    settings: dict[str, Any],
    loso_train: bool = False,
):
    classes = RHYTHM_CLASSES_P6 if profile == "P6" else RHYTHM_CLASSES_P8
    columns = [RHYTHM_CLASSES_P8.index(name) for name in classes]
    train_splits = {"train", "source_holdout"} if loso_train else {"train"}
    train_records = {
        i for i, row in enumerate(records)
        if row["scored"] and row["split"] in train_splits
        and (not loso_train or row["source"] in {"chapman_shaoxing", "georgia"})
    }
    validation_records = {
        i for i, row in enumerate(records)
        if row["scored"] and row["split"] == "validation" and row["source"] == "chapman_shaoxing"
    }
    train_windows = _selected_window_rows(window_records, train_records)
    validation_windows = _selected_window_rows(window_records, validation_records)
    if not len(train_windows) or not len(validation_windows):
        raise ValueError("rhythm training or Chapman validation windows are absent")
    train_record_ids = window_records[train_windows]
    val_record_ids = window_records[validation_windows]
    train_targets, train_masks, train_sources, _, record_weights = _targets_by_index(
        records, train_record_ids, columns
    )
    element_weights = source_balanced_element_weights(
        train_sources, torch.as_tensor(train_masks),
        window_weights=torch.as_tensor(record_weights),
    ).numpy()
    val_targets = np.asarray(
        [[records[i]["targets"][c] for c in columns] for i in val_record_ids], dtype=np.float32
    )
    val_masks = np.asarray(
        [[records[i]["mask"][c] for c in columns] for i in val_record_ids], dtype=bool
    )
    validation_groups = [records[i]["identity_hash"] for i in val_record_ids]
    aggregation = "mean_logits" if profile == "P6" else "mean_probabilities"
    model, receipt = fit_classwise_binary_head(
        feature_matrix[train_windows], train_targets, train_masks, element_weights,
        feature_matrix[validation_windows], val_targets, val_masks,
        loss_name=loss_name,
        focal_gamma=float(settings["focal_gamma"]),
        positive_weight_max=float(settings["positive_weight_clip"][1]),
        validation_group_ids=validation_groups,
        validation_aggregation=aggregation,
        hidden_dim=int(settings["hidden_dim"]), dropout=float(settings["dropout"]),
        learning_rate=float(settings["learning_rate"]), batch_size=int(settings["batch_size"]),
        max_epochs=int(settings["max_epochs"]), patience=int(settings["early_stopping_patience"]),
        seed=seed, device=device,
    )
    receipt.update({
        "profile": profile,
        "trainable_parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "train_records": len(train_records),
        "train_windows": len(train_windows),
        "validation_records": len(validation_records),
        "validation_windows": len(validation_windows),
        "training_sources": sorted({records[i]["source"] for i in train_records}),
        "loso_cpsc_sensitivity_model": loso_train,
    })
    return model, receipt, classes


def _candidate_record_scores(
    model: torch.nn.Module, features: np.ndarray, window_records: np.ndarray,
    records: list[dict[str, Any]], profile: str, device: str,
) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        window_logits = model(torch.as_tensor(features, dtype=torch.float32, device=device)).cpu().numpy()
    scores = np.full((len(records), len(RHYTHM_CLASSES_P6 if profile == "P6" else RHYTHM_CLASSES_P8),),
                     np.nan, dtype=np.float64)
    for index, row in enumerate(records):
        if not row["scored"]:
            continue
        logits = window_logits[window_records == index]
        if not len(logits):
            continue
        if profile == "P6":
            mean_logits = logits.mean(axis=0, dtype=np.float64)
            scores[index] = 1 / (1 + np.exp(-np.clip(mean_logits, -50, 50)))
        else:
            clipped = np.clip(logits, -50, 50)
            scores[index] = (1 / (1 + np.exp(-clipped))).mean(axis=0, dtype=np.float64)
    return scores


def _baseline_rhythm_scores(
    logits: np.ndarray, window_records: np.ndarray, records: list[dict[str, Any]],
    profile: str, thresholds: dict[str, float],
) -> np.ndarray:
    classes = RHYTHM_CLASSES_P6 if profile == "P6" else RHYTHM_CLASSES_P8
    scores = np.full((len(records), len(classes)), np.nan, dtype=np.float64)
    for index, row in enumerate(records):
        if not row["scored"]:
            continue
        values = logits[window_records == index]
        if len(values):
            result = aggregate_rhythm(values, thresholds, profile=profile)
            scores[index] = [result["scores"][name] for name in classes]
    return scores


def _calibrate_thresholds(records, scores, classes, split: str) -> dict[str, float | None]:
    if scores.ndim != 2 or scores.shape[0] != len(records) or scores.shape[1] != len(classes):
        raise ValueError("calibration scores must align with records and class order")
    result: dict[str, float | None] = {}
    for column, name in enumerate(classes):
        indices = [i for i, row in enumerate(records)
                   if row["scored"] and np.isfinite(scores[i, column])
                   and row["split"] == split and row["source"] == (
                       "ptbxl" if split == "calibration" and tuple(classes) == P4_CLASSES
                       else "chapman_shaoxing"
                   ) and row["mask"][P4_CLASSES.index(name) if name in P4_CLASSES else
                                      RHYTHM_CLASSES_P8.index(name)]]
        truth = [records[i]["targets"][P4_CLASSES.index(name) if name in P4_CLASSES else
                                     RHYTHM_CLASSES_P8.index(name)] for i in indices]
        probabilities = [scores[i, column] for i in indices]
        try:
            result[name] = select_f1_threshold(truth, probabilities)
        except ValueError:
            result[name] = None
    return result


def _p4_candidate(model, features, device):
    model.eval()
    with torch.no_grad():
        logits = model(torch.as_tensor(features, dtype=torch.float32, device=device)).cpu().numpy()
    return (1 / (1 + np.exp(-np.clip(logits, -50, 50)))).astype(np.float64)


def _bootstrap_macro_f1_delta(y, mask, baseline_calls, candidate_calls, groups, classes, seed):
    y, mask = np.asarray(y, dtype=np.int8), np.asarray(mask, dtype=bool)
    old, new = np.asarray(baseline_calls, dtype=np.int8), np.asarray(candidate_calls, dtype=np.int8)
    group_values = np.asarray(groups, dtype=str)
    eligible = []
    for column in range(y.shape[1]):
        values = y[mask[:, column], column]
        if len(values) and values.min() == 0 and values.max() == 1:
            eligible.append(column)
    if not eligible:
        return {"low": None, "high": None, "valid_replicates": 0, "classes": []}
    unique = np.unique(group_values)
    rows_by_group = [np.flatnonzero(group_values == group) for group in unique]
    rng = np.random.Generator(np.random.PCG64(seed))
    deltas = []
    for _ in range(BOOTSTRAP_REPLICATES):
        sampled = rng.integers(0, len(unique), size=len(unique))
        indices = np.concatenate([rows_by_group[index] for index in sampled])
        old_f1, new_f1 = [], []
        for column in eligible:
            selected = indices[mask[indices, column]]
            if not len(selected):
                old_f1.append(0.0)
                new_f1.append(0.0)
                continue
            old_metrics = binary_metrics(y[selected, column], old[selected, column])
            new_metrics = binary_metrics(y[selected, column], new[selected, column])
            old_f1.append(float(old_metrics["f1"]))
            new_f1.append(float(new_metrics["f1"]))
        deltas.append(float(np.mean(new_f1) - np.mean(old_f1)))
    low, high = np.quantile(deltas, [0.025, 0.975], method="linear")
    return {"low": float(low), "high": float(high), "valid_replicates": len(deltas),
            "classes": [classes[column] for column in eligible]}


def _macro_delta_ci(
    records, eligible_indices, classes, baseline_scores, baseline_thresholds,
    candidate_scores, candidate_thresholds, seed,
):
    source_classes = P4_CLASSES if tuple(classes) == P4_CLASSES else RHYTHM_CLASSES_P8
    columns = [source_classes.index(name) for name in classes]
    y, mask = [], []
    baseline_calls, candidate_calls, groups = [], [], []
    for record_index in eligible_indices:
        row = records[record_index]
        y.append([row["targets"][column] for column in columns])
        mask.append([row["mask"][column] for column in columns])
        baseline_calls.append([
            int(baseline_scores[record_index, class_column] >= baseline_thresholds[name])
            for class_column, name in enumerate(classes)
        ])
        candidate_calls.append([
            int(candidate_scores[record_index, class_column] >= candidate_thresholds[name])
            for class_column, name in enumerate(classes)
        ])
        groups.append(row["group_hash"] or row["identity_hash"])
    return _bootstrap_macro_f1_delta(
        y, mask, baseline_calls, candidate_calls, groups, classes, seed
    )


def _metric_rows(
    *, profile: str, scope: str, source: str, records, eligible_indices: list[int],
    classes: tuple[str, ...], baseline_scores, baseline_thresholds, candidate_models,
    group_unit: str, output_rows: list[dict[str, Any]],
):
    candidate_outputs = []
    for model_name, (scores, thresholds, is_primary) in candidate_models.items():
        candidate_outputs.append((model_name, scores, thresholds, is_primary))
    for column, name in enumerate(classes):
        selected = [i for i in eligible_indices if records[i]["mask"][
            (P4_CLASSES if profile == "P4" else RHYTHM_CLASSES_P8).index(name)
        ] and np.isfinite(baseline_scores[i, column])]
        truth = np.asarray([
            records[i]["targets"][(P4_CLASSES if profile == "P4" else RHYTHM_CLASSES_P8).index(name)]
            for i in selected
        ], dtype=np.int64)
        groups = [records[i]["group_hash"] or records[i]["identity_hash"] for i in selected]
        group_count = len(set(groups))
        has_both = len(truth) > 0 and truth.min() == 0 and truth.max() == 1
        systems = [("published_baseline", baseline_scores, baseline_thresholds, True)] + candidate_outputs
        per_system = {}
        for model_name, scores_matrix, thresholds, is_primary in systems:
            threshold = thresholds.get(name)
            probabilities = np.asarray([scores_matrix[i, column] for i in selected], dtype=np.float64)
            if threshold is None or not has_both:
                metrics = {key: None for key in (
                    "accuracy", "precision", "recall", "specificity", "negative_predictive_value",
                    "f1", "auroc",
                    "average_precision", "brier_score", "ece",
                )}
                calls = np.zeros(len(selected), dtype=np.int64)
            else:
                metrics = class_metrics(truth, probabilities, float(threshold))
                calls = (probabilities >= float(threshold)).astype(np.int64)
            per_system[model_name] = (metrics, calls, probabilities, threshold, is_primary)
            row = {
                "profile": profile,
                "scope": scope,
                "source": source,
                "model": model_name,
                "endpoint": name,
                "n_ecg": len(selected),
                "n_groups": group_count,
                "group_unit": group_unit,
                "n_patients": group_count if group_unit == "patient" else None,
                "positive_support": int(truth.sum()),
                "negative_support": int(len(truth) - truth.sum()),
                "threshold": threshold,
                "estimable": has_both and threshold is not None,
                **metrics,
                "f1_ci_low": None,
                "f1_ci_high": None,
                "delta_f1_vs_baseline": None,
                "paired_delta_f1_ci_low": None,
                "paired_delta_f1_ci_high": None,
            }
            for metric_name in ("accuracy", "precision", "recall", "specificity",
                                "negative_predictive_value", "f1", "auroc",
                                "average_precision", "brier_score", "ece"):
                row[f"{metric_name}_ci_low"] = None
                row[f"{metric_name}_ci_high"] = None
                row[f"paired_delta_{metric_name}_ci_low"] = None
                row[f"paired_delta_{metric_name}_ci_high"] = None
            if row["estimable"]:
                interval = bootstrap_binary_metrics(
                    truth, calls, probabilities, groups,
                    seed=BOOTSTRAP_SEED + column + len(scope), n_bootstrap=BOOTSTRAP_REPLICATES,
                )
                for metric_name, bounds in interval["intervals"].items():
                    row[f"{metric_name}_ci_low"] = bounds["low"]
                    row[f"{metric_name}_ci_high"] = bounds["high"]
            output_rows.append(row)
        baseline_metrics, baseline_calls, baseline_probabilities, _, _ = per_system["published_baseline"]
        for model_name, (metrics, calls, probabilities, _, is_primary) in per_system.items():
            if model_name == "published_baseline" or metrics["f1"] is None:
                continue
            target_row = next(row for row in reversed(output_rows)
                              if row["profile"] == profile and row["scope"] == scope
                              and row["source"] == source and row["model"] == model_name
                              and row["endpoint"] == name)
            target_row["delta_f1_vs_baseline"] = float(metrics["f1"]) - float(baseline_metrics["f1"])
            if is_primary:
                paired = paired_bootstrap_metric_differences(
                    truth, baseline_calls, baseline_probabilities, calls, probabilities, groups,
                    seed=BOOTSTRAP_SEED + 10 + column + len(scope),
                    n_bootstrap=BOOTSTRAP_REPLICATES,
                )
                for metric_name, bounds in paired["intervals"].items():
                    target_row[f"paired_delta_{metric_name}_ci_low"] = bounds["low"]
                    target_row[f"paired_delta_{metric_name}_ci_high"] = bounds["high"]


def _summary_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for row in metric_rows:
        if row["estimable"]:
            key = (row["profile"], row["scope"], row["source"], row["model"])
            groups.setdefault(key, []).append(row)
    summaries = []
    for (profile, scope, source, model), rows in sorted(groups.items()):
        baseline_rows = groups.get((profile, scope, source, "published_baseline"), [])
        baseline_by_endpoint = {item["endpoint"]: item for item in baseline_rows}
        model_by_endpoint = {item["endpoint"]: item for item in rows}
        common_endpoints = sorted(set(model_by_endpoint) & set(baseline_by_endpoint))
        mean_f1 = (
            float(np.mean([model_by_endpoint[name]["f1"] for name in common_endpoints]))
            if common_endpoints else None
        )
        baseline_macro = (
            float(np.mean([baseline_by_endpoint[name]["f1"] for name in common_endpoints]))
            if common_endpoints else None
        )
        summaries.append({
            "profile": profile,
            "scope": scope,
            "source": source,
            "model": model,
            "evaluable_endpoints": len(common_endpoints),
            "model_evaluable_endpoints": len(rows),
            "comparison_endpoints": common_endpoints,
            "macro_f1": mean_f1,
            "baseline_macro_f1": baseline_macro,
            "delta_macro_f1_vs_baseline": (
                None if baseline_macro is None or mean_f1 is None else mean_f1 - baseline_macro
            ),
            "selection_from_holdout_prohibited": model != "published_baseline",
            "paired_delta_macro_f1_ci_low": None,
            "paired_delta_macro_f1_ci_high": None,
        })
    return summaries


def _dataset_split_summary(metadata: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": "TITAN_SPECIALIST_DATASET_SPLITS_V1",
        "study_id": metadata["study_id"],
        "fold10_used": False,
        "sp_h_or_v3h_used": False,
        "individual_records_or_ids_included": False,
        "preflight_support_and_signal_specs": metadata["preflight_aggregates"],
        "preprocessing_errors_by_source_and_type": metadata["preprocessing_errors_by_source_and_type"],
        "tasks": {},
    }
    for task, records in (("rhythm", metadata["rhythm_records"]),
                          ("pathology", metadata["pathology_records"])):
        task_data = {}
        for source in sorted({row["source"] for row in records}):
            source_rows = [row for row in records if row["source"] == source]
            split_data = {}
            for split in sorted({row["split"] for row in source_rows}):
                selected = [row for row in source_rows if row["split"] == split]
                scored = [row for row in selected if row["scored"]]
                class_names = selected[0]["classes"]
                support = {}
                for column, name in enumerate(class_names):
                    observed = [row for row in scored if row["mask"][column]]
                    support[name] = {
                        "observed": len(observed),
                        "positive": sum(row["targets"][column] for row in observed),
                        "negative_or_control": len(observed) - sum(
                            row["targets"][column] for row in observed
                        ),
                    }
                split_data[split] = {
                    "inventory_records": len(selected),
                    "feature_scored_records": len(scored),
                    "feature_failures": len(selected) - len(scored),
                    "class_support": support,
                }
            task_data[source] = split_data
        result["tasks"][task] = task_data
    return result


def _metrics_for_rhythm_scope(
    profile, scope, source, records, classes, candidate_scores, baseline_scores,
    baseline_thresholds, group_unit, metric_rows,
    primary_model="weighted_bce_seed_20261111",
):
    indices = [i for i, row in enumerate(records) if row["scored"] and row["source"] == source]
    candidate_models = {
        name: (scores, thresholds, name == primary_model)
        for name, scores, thresholds in candidate_scores
    }
    _metric_rows(
        profile=profile, scope=scope, source=source, records=records, eligible_indices=indices,
        classes=classes, baseline_scores=baseline_scores, baseline_thresholds=baseline_thresholds,
        candidate_models=candidate_models, group_unit=group_unit, output_rows=metric_rows,
    )


def _save_private_checkpoint(path, model, payload):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    temporary = path.with_suffix(path.suffix + ".tmp")
    torch.save({**payload, "state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()}},
               temporary)
    os.chmod(temporary, 0o600)
    temporary.replace(path)
    return {"name": path.name, "bytes": path.stat().st_size, "sha256": _sha256(path)}


def run(feature_dir: Path, output_dir: Path, device: str):
    global BOOTSTRAP_REPLICATES, BOOTSTRAP_SEED
    feature_dir, output_dir = feature_dir.resolve(), output_dir.resolve()
    if feature_dir == output_dir or output_dir.is_relative_to(feature_dir):
        raise ValueError("training outputs must not overwrite the feature cache")
    output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output_dir, 0o700)
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    training_settings = config["candidate_training"]
    loss_names = tuple(training_settings["loss_comparison"])
    seeds = tuple(int(value) for value in training_settings["seeds"])
    primary_candidate = str(training_settings["primary_candidate"])
    BOOTSTRAP_REPLICATES = int(config["statistics"]["bootstrap_replicates"])
    BOOTSTRAP_SEED = int(config["statistics"]["seed"])
    if (not seeds or primary_candidate != f"weighted_bce_seed_{seeds[0]}"
            or float(config["statistics"]["confidence"]) != 0.95):
        raise ValueError("frozen primary candidate, seed order, or confidence level is inconsistent")
    metadata_path = feature_dir / "private_feature_metadata.json"
    feature_path = feature_dir / "private_frozen_features.npz"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("schema") != "TITAN_PRIVATE_SPECIALIST_FEATURE_CACHE_V1":
        raise ValueError("unexpected private feature cache schema")
    if metadata.get("feature_cache_sha256") != _sha256(feature_path):
        raise ValueError("feature cache hash mismatch")
    if metadata.get("config_sha256") != _sha256(CONFIG):
        raise ValueError("frozen study configuration changed after feature extraction")
    if metadata.get("git_commit") != _git_revision(ROOT):
        raise ValueError("feature cache was extracted from a different code commit")
    with np.load(feature_path, allow_pickle=False) as loaded:
        arrays = {name: loaded[name] for name in loaded.files}
    rhythm_records = metadata["rhythm_records"]
    p4_records = metadata["pathology_records"]
    _metadata_classes(rhythm_records, "rhythm")
    _metadata_classes(p4_records, "pathology")
    thresholds = metadata["baseline_thresholds"]
    metric_rows, training_runs, private_checkpoints = [], [], []

    baseline_rhythm = {
        "P6": _baseline_rhythm_scores(
            arrays["p6_baseline_logits"], arrays["rhythm_record_index"], rhythm_records,
            "P6", thresholds["P6"],
        ),
        "P8": _baseline_rhythm_scores(
            arrays["p8_baseline_logits"], arrays["rhythm_record_index"], rhythm_records,
            "P8", thresholds["P8"],
        ),
    }

    rhythm_candidates = {}
    for profile in ("P6", "P8"):
        feature_key = "p6_features" if profile == "P6" else "p8_features"
        profile_candidates = []
        for loss_name in loss_names:
            for seed in seeds:
                name = f"{loss_name}_seed_{seed}"
                model, receipt, classes = _train_rhythm_variant(
                    profile, loss_name, seed, rhythm_records, arrays[feature_key],
                    arrays["rhythm_record_index"], device=device, settings=training_settings,
                )
                scores = _candidate_record_scores(
                    model, arrays[feature_key], arrays["rhythm_record_index"],
                    rhythm_records, profile, device,
                )
                candidate_thresholds = _calibrate_thresholds(
                    rhythm_records, scores, classes, "calibration"
                )
                checkpoint = _save_private_checkpoint(
                    output_dir / "checkpoints" / f"{profile.lower()}-{name}.pt", model,
                    {"schema": "TITAN_NEW_SPECIALIST_HEAD_CHECKPOINT_V1", "profile": profile,
                     "classes": list(classes), "input_dim": int(arrays[feature_key].shape[1]),
                     "thresholds": candidate_thresholds, "training_receipt": receipt,
                     "config_sha256": _sha256(CONFIG),
                     "feature_cache_sha256": metadata["feature_cache_sha256"],
                     "frozen_backbone_hashes": metadata["baseline_asset_hashes"]},
                )
                private_checkpoints.append(checkpoint)
                training_runs.append({**receipt, "name": name, "profile": profile,
                                      "candidate_thresholds": candidate_thresholds,
                                      "checkpoint": checkpoint})
                profile_candidates.append((name, scores, candidate_thresholds))
        rhythm_candidates[profile] = profile_candidates
        classes = RHYTHM_CLASSES_P6 if profile == "P6" else RHYTHM_CLASSES_P8
        _metrics_for_rhythm_scope(
            profile, "chapman_plus_cpsc_train_to_georgia_holdout", "georgia", rhythm_records,
            classes, profile_candidates, baseline_rhythm[profile], thresholds[profile],
            "record_not_patient", metric_rows,
            primary_model=primary_candidate,
        )

    # One predeclared complementary leave-one-source-out rhythm comparison.
    loso_models = {}
    for profile in ("P6", "P8"):
        feature_key = "p6_features" if profile == "P6" else "p8_features"
        loso_model_name = f"loso_cpsc_weighted_bce_seed_{seeds[0]}"
        model, receipt, classes = _train_rhythm_variant(
            profile, "weighted_bce", seeds[0], rhythm_records, arrays[feature_key],
            arrays["rhythm_record_index"], device=device, settings=training_settings,
            loso_train=True,
        )
        scores = _candidate_record_scores(
            model, arrays[feature_key], arrays["rhythm_record_index"], rhythm_records, profile, device
        )
        candidate_thresholds = _calibrate_thresholds(rhythm_records, scores, classes, "calibration")
        checkpoint = _save_private_checkpoint(
            output_dir / "checkpoints" / f"{profile.lower()}-{loso_model_name}.pt",
            model, {"schema": "TITAN_NEW_SPECIALIST_HEAD_CHECKPOINT_V1", "profile": profile,
                    "classes": list(classes), "thresholds": candidate_thresholds,
                    "training_receipt": receipt, "config_sha256": _sha256(CONFIG),
                    "feature_cache_sha256": metadata["feature_cache_sha256"],
                    "frozen_backbone_hashes": metadata["baseline_asset_hashes"]},
        )
        private_checkpoints.append(checkpoint)
        training_runs.append({**receipt, "name": loso_model_name,
                              "profile": profile, "candidate_thresholds": candidate_thresholds,
                              "checkpoint": checkpoint})
        loso_scores = _candidate_record_scores(
            model, arrays[feature_key], arrays["rhythm_record_index"], rhythm_records, profile, device
        )
        loso_models[profile] = [(loso_model_name, loso_scores,
                                 candidate_thresholds)]
        _metrics_for_rhythm_scope(
            profile, "chapman_plus_georgia_train_to_cpsc_holdout", "cpsc2018", rhythm_records,
            classes, loso_models[profile], baseline_rhythm[profile], thresholds[profile],
            "record_not_patient", metric_rows,
            primary_model=loso_model_name,
        )

    p4_features = arrays["p4_features"]
    p4_row_indices = arrays["p4_record_index"].astype(int)
    p4_scored_records = [p4_records[i] for i in p4_row_indices]
    p4_baseline_scores = arrays["p4_baseline_scores"].astype(np.float64)
    p4_candidates = []
    for loss_name in loss_names:
        for seed in seeds:
            name = f"{loss_name}_seed_{seed}"
            train_ids = [j for j, row in enumerate(p4_scored_records)
                         if row["split"] == "train" and any(row["mask"])]
            validation_ids = [j for j, row in enumerate(p4_scored_records)
                              if row["split"] == "validation" and any(row["mask"])]
            calibration_ids = [j for j, row in enumerate(p4_scored_records) if row["split"] == "calibration"]
            internal_ids = [j for j, row in enumerate(p4_scored_records)
                            if row["split"] == "internal_evaluation"]
            if not train_ids or not validation_ids or not calibration_ids or not internal_ids:
                raise ValueError("PTB-XL train/validation/calibration/internal evaluation partition is empty")
            train_y = np.asarray([p4_scored_records[i]["targets"] for i in train_ids], dtype=np.float32)
            train_m = np.asarray([p4_scored_records[i]["mask"] for i in train_ids], dtype=bool)
            train_w = source_balanced_element_weights(
                ["ptbxl"] * len(train_ids), torch.as_tensor(train_m)
            ).numpy()
            val_y = np.asarray([p4_scored_records[i]["targets"] for i in validation_ids], dtype=np.float32)
            val_m = np.asarray([p4_scored_records[i]["mask"] for i in validation_ids], dtype=bool)
            val_groups = [p4_scored_records[i]["identity_hash"] for i in validation_ids]
            model, receipt = fit_classwise_binary_head(
                p4_features[train_ids], train_y, train_m, train_w,
                p4_features[validation_ids], val_y, val_m,
                loss_name=loss_name,
                focal_gamma=float(training_settings["focal_gamma"]),
                positive_weight_max=float(training_settings["positive_weight_clip"][1]),
                validation_group_ids=val_groups,
                validation_aggregation="mean_logits",
                hidden_dim=int(training_settings["hidden_dim"]),
                dropout=float(training_settings["dropout"]),
                learning_rate=float(training_settings["learning_rate"]),
                batch_size=int(training_settings["batch_size"]),
                max_epochs=int(training_settings["max_epochs"]),
                patience=int(training_settings["early_stopping_patience"]),
                seed=seed, device=device,
            )
            receipt["trainable_parameter_count"] = sum(
                parameter.numel() for parameter in model.parameters()
            )
            scores = _p4_candidate(model, p4_features, device)
            thresholds_candidate = _calibrate_thresholds(
                p4_scored_records, scores, P4_CLASSES, "calibration"
            )
            checkpoint = _save_private_checkpoint(
                output_dir / "checkpoints" / f"p4-{name}.pt", model,
                {"schema": "TITAN_NEW_SPECIALIST_HEAD_CHECKPOINT_V1", "profile": "P4",
                 "classes": list(P4_CLASSES), "input_dim": int(p4_features.shape[1]),
                 "thresholds": thresholds_candidate,
                 "training_receipt": {**receipt, "train_records": len(train_ids),
                                      "validation_records": len(validation_ids),
                                      "calibration_records": len(calibration_ids),
                                      "internal_evaluation_records": len(internal_ids)},
                 "config_sha256": _sha256(CONFIG),
                 "feature_cache_sha256": metadata["feature_cache_sha256"],
                 "frozen_backbone_hashes": metadata["baseline_asset_hashes"]},
            )
            private_checkpoints.append(checkpoint)
            training_runs.append({**receipt, "name": name, "profile": "P4",
                                  "candidate_thresholds": thresholds_candidate,
                                  "checkpoint": checkpoint})
            p4_candidates.append((name, scores, thresholds_candidate,
                                  name == primary_candidate))
    _metric_rows(
        profile="P4", scope="ptbxl_folds_1_7_train_fold8_validation_fold9_internal_eval",
        source="ptbxl", records=p4_scored_records,
        eligible_indices=[i for i, row in enumerate(p4_scored_records)
                          if row["split"] == "internal_evaluation"],
        classes=P4_CLASSES, baseline_scores=p4_baseline_scores,
        baseline_thresholds=thresholds["P4"],
        candidate_models={name: (scores, th, primary) for name, scores, th, primary in p4_candidates},
        group_unit="patient", output_rows=metric_rows,
    )

    summaries = _summary_rows(metric_rows)
    for row in summaries:
        profile, scope, source, model_name = (
            row["profile"], row["scope"], row["source"], row["model"]
        )
        if model_name == "published_baseline":
            continue
        if profile == "P4":
            selected = next((item for item in p4_candidates if item[0] == model_name), None)
            records = p4_scored_records
            classes = P4_CLASSES
            baseline_scores = p4_baseline_scores
            baseline_thresholds = thresholds["P4"]
            eligible_indices = [i for i, item in enumerate(records)
                                if item["split"] == "internal_evaluation"]
        elif scope == "chapman_plus_cpsc_train_to_georgia_holdout":
            selected = next((item for item in rhythm_candidates[profile]
                             if item[0] == model_name), None)
            records = rhythm_records
            classes = RHYTHM_CLASSES_P6 if profile == "P6" else RHYTHM_CLASSES_P8
            baseline_scores = baseline_rhythm[profile]
            baseline_thresholds = thresholds[profile]
            eligible_indices = [i for i, item in enumerate(records)
                                if item["scored"] and item["source"] == source]
        else:
            selected = next((item for item in loso_models[profile]
                             if item[0] == model_name), None)
            records = rhythm_records
            classes = RHYTHM_CLASSES_P6 if profile == "P6" else RHYTHM_CLASSES_P8
            baseline_scores = baseline_rhythm[profile]
            baseline_thresholds = thresholds[profile]
            eligible_indices = [i for i, item in enumerate(records)
                                if item["scored"] and item["source"] == source]
        if selected is None:
            continue
        _, candidate_scores, candidate_thresholds, *rest = selected
        primary = profile == "P4" and model_name == primary_candidate or (
            profile in {"P6", "P8"} and model_name in {
                primary_candidate, f"loso_cpsc_weighted_bce_seed_{seeds[0]}"
            }
        )
        if not primary or any(candidate_thresholds.get(name) is None for name in classes):
            continue
        ci = _macro_delta_ci(
            records, eligible_indices, classes, baseline_scores, baseline_thresholds,
            candidate_scores, candidate_thresholds, BOOTSTRAP_SEED + 20 + len(scope) + len(profile),
        )
        row["paired_delta_macro_f1_ci_low"] = ci["low"]
        row["paired_delta_macro_f1_ci_high"] = ci["high"]
        row["macro_f1_bootstrap_classes"] = ci["classes"]

    public_metric_rows = [{key: value for key, value in row.items()
                           if not key.startswith("_private")}
                          for row in metric_rows]
    _atomic_csv(output_dir / "SPECIALIST_PER_CLASS_RESULTS.csv", public_metric_rows)
    _atomic_csv(output_dir / "SPECIALIST_MODEL_COMPARISON.csv", summaries)
    _atomic_json(output_dir / "SPECIALIST_DATASET_SPLITS.json", _dataset_split_summary(metadata))
    receipt = {
        "schema": "TITAN_SPECIALIST_TRAINING_EVALUATION_RECEIPT_V1",
        "study_id": config["study_id"],
        "config_sha256": _sha256(CONFIG),
        "feature_cache_sha256": metadata["feature_cache_sha256"],
        "private_feature_metadata_sha256": _sha256(metadata_path),
        "baseline_asset_hashes": metadata["baseline_asset_hashes"],
        "private_checkpoint_manifest": private_checkpoints,
        "training_runs": training_runs,
        "metrics_artifacts": {
            "SPECIALIST_PER_CLASS_RESULTS.csv": _sha256(output_dir / "SPECIALIST_PER_CLASS_RESULTS.csv"),
            "SPECIALIST_MODEL_COMPARISON.csv": _sha256(output_dir / "SPECIALIST_MODEL_COMPARISON.csv"),
            "SPECIALIST_DATASET_SPLITS.json": _sha256(output_dir / "SPECIALIST_DATASET_SPLITS.json"),
        },
        "n_bootstrap": BOOTSTRAP_REPLICATES,
        "independent_external_validation": "NOT_RUN",
        "sp_h_or_v3h_used": False,
        "fold10_used": False,
        "historical_weights_or_thresholds_modified": False,
        "row_level_data_or_predictions_public": False,
        "device": device,
        "torch_version": torch.__version__,
    }
    _atomic_json(output_dir / "SPECIALIST_TRAINING_RECEIPT.json", receipt)
    public_manifest = {
        "schema": "TITAN_SPECIALIST_REPRODUCIBILITY_MANIFEST_V1",
        "study_id": receipt["study_id"],
        "created_utc": datetime.now(UTC).isoformat(),
        "git_commit": _git_revision(ROOT),
        "config_sha256": receipt["config_sha256"],
        "code_sha256": {
            "audit_inputs.py": _sha256(ROOT / "scripts/specialist_experiments/audit_inputs.py"),
            "extract_features.py": _sha256(ROOT / "scripts/specialist_experiments/extract_features.py"),
            "train_evaluate.py": _sha256(Path(__file__).resolve()),
            "training_primitives.py": _sha256(ROOT / "src/titan_v45/training/specialist_heads.py"),
            "evaluation_primitives.py": _sha256(ROOT / "src/titan_v45/evaluation/specialist_heads.py"),
        },
        "baseline_assets": receipt["baseline_asset_hashes"],
        "private_candidate_checkpoints": private_checkpoints,
        "aggregate_result_artifacts": receipt["metrics_artifacts"],
        "runtime": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "cudnn": torch.backends.cudnn.version(),
            "device": device,
            "device_name": torch.cuda.get_device_name(0) if device == "cuda" else platform.processor(),
            "preprocessing_runtime": {
                "numpy": metadata["numpy_version"],
                "scipy": metadata["scipy_version"],
                "wfdb": metadata["wfdb_version"],
                "feature_extraction_torch": metadata["torch_version"],
            },
        },
        "data_handling": {
            "row_level_data_or_predictions_public": False,
            "candidate_weights_public": False,
            "fold10_used": False,
            "sp_h_or_v3h_used": False,
            "independent_external_validation": "NOT_RUN",
        },
    }
    _atomic_json(output_dir / "SPECIALIST_REPRODUCIBILITY_MANIFEST.json", public_manifest)
    print(json.dumps({
        "schema": receipt["schema"], "study_id": receipt["study_id"],
        "training_run_count": len(training_runs), "checkpoint_count": len(private_checkpoints),
        "summary_rows": len(summaries), "per_class_rows": len(public_metric_rows),
        "independent_external_validation": "NOT_RUN",
        "metric_artifact_hashes": receipt["metrics_artifacts"],
        "reproducibility_manifest_sha256": _sha256(
            output_dir / "SPECIALIST_REPRODUCIBILITY_MANIFEST.json"
        ),
    }, sort_keys=True))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    args = parser.parse_args()
    run(args.feature_dir, args.output_dir, args.device)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
