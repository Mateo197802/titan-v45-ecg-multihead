"""Revision analyses of saved predictions, never ECG inference or test tuning.

CLI: python scripts/evaluation/build_revision_report.py --output-dir <directory>
All denominators refer to the supplied external-development CSV rows. An ECG
cluster is (source, record_id), not a patient or a verified waveform identity.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from titan_v45.contracts.profiles import CANONICAL_PROFILES

SCHEMA = "TITAN_V45_REVISION_REPORT_V1"
EVIDENCE = Path("outputs/results/external_dev/evidence")
ECGKey = tuple[str, str]


@dataclass(frozen=True)
class BinaryPanel:
    """One binary decision per ECG in a panel; ECGs may recur in other panels."""

    keys: tuple[ECGKey, ...]
    truth: np.ndarray
    predicted: np.ndarray


def _binary(values: Sequence[Any] | np.ndarray) -> np.ndarray:
    try:
        result = np.asarray(values, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("targets and decisions must be non-null binary values") from exc
    if result.ndim != 1 or not np.all(np.isin(result, [0, 1])):
        raise ValueError("targets and decisions must be non-null binary values")
    return result.astype(np.int64)


def _probabilities(values: Sequence[Any] | None, count: int) -> np.ndarray:
    if values is None:
        return np.full(count, np.nan)
    result = []
    for value in values:
        if value is None or (
            isinstance(value, str) and value.strip().lower() in {"", "null", "nan", "na"}
        ):
            result.append(float("nan"))
            continue
        try:
            result.append(float(value))
        except (ValueError, TypeError) as exc:
            raise ValueError("invalid probability") from exc
    array = np.asarray(result, dtype=float)
    if array.shape != (count,) or np.any(np.isinf(array)) or np.any((array < 0) | (array > 1)):
        raise ValueError("probabilities must have matching length and lie in [0, 1] or be null")
    return array


def _counts(truth: np.ndarray, predicted: np.ndarray) -> np.ndarray:
    return np.array(
        [
            np.sum((truth == 1) & (predicted == 1)),
            np.sum((truth == 0) & (predicted == 0)),
            np.sum((truth == 0) & (predicted == 1)),
            np.sum((truth == 1) & (predicted == 0)),
        ],
        dtype=np.int64,
    )


def binary_metrics(
    truth: Sequence[Any] | np.ndarray,
    predicted: Sequence[Any] | np.ndarray,
    probabilities: Sequence[Any] | None = None,
    *,
    ece_bins: int = 10,
) -> dict[str, Any]:
    """Binary metrics with explicit missing-score and undefined-metric support.

    AUROC integrates the empirical ROC; AP is the non-interpolated step integral
    of precision over recall. Equal scores enter together, independent of row
    order. ECE weights equal-width bins by available-score count, not all rows.
    F1 with zero denominator is 0, matching the existing fixed-class macro rule.
    """
    if not isinstance(ece_bins, int) or ece_bins < 1:
        raise ValueError("ece_bins must be a positive integer")
    y, pred = _binary(truth), _binary(predicted)
    if y.shape != pred.shape:
        raise ValueError("binary targets and predictions must have matching shapes")
    p = _probabilities(probabilities, len(y))
    tp, tn, fp, fn = map(int, _counts(y, pred))
    undefined: dict[str, str] = {}

    def ratio(name: str, numerator: int, denominator: int) -> float | None:
        if denominator:
            return numerator / denominator
        undefined[name] = "zero_denominator"
        return None

    result: dict[str, Any] = {
        "rows": len(y),
        "positive_support": tp + fn,
        "negative_support": tn + fp,
        "predicted_positive_support": tp + fp,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": ratio("accuracy", tp + tn, len(y)),
        "precision": ratio("precision", tp, tp + fp),
        "recall": ratio("recall", tp, tp + fn),
        "specificity": ratio("specificity", tn, tn + fp),
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
    }
    if not 2 * tp + fp + fn:
        undefined["f1"] = "zero_denominator_reported_as_zero"
    mask = ~np.isnan(p)
    scores, reference = p[mask], y[mask]
    positive, negative = int(reference.sum()), int(len(reference) - reference.sum())
    result.update(
        {
            "probability_rows": len(scores),
            "missing_probability_rows": int((~mask).sum()),
            "probability_positive_support": positive,
            "probability_negative_support": negative,
            "auroc": None,
            "average_precision": None,
            "brier_score": None,
            "ece": None,
        }
    )
    if len(scores):
        result["brier_score"] = float(np.mean((scores - reference) ** 2))
        edges = np.linspace(0.0, 1.0, ece_bins + 1)
        bin_index = np.minimum(np.searchsorted(edges, scores, side="right") - 1, ece_bins - 1)
        ece = 0.0
        for index in range(ece_bins):
            selected = bin_index == index
            if np.any(selected):
                ece += float(
                    np.sum(selected)
                    / len(scores)
                    * abs(scores[selected].mean() - reference[selected].mean())
                )
        result["ece"] = ece
        order = np.argsort(-scores, kind="stable")
        sorted_scores, sorted_y = scores[order], reference[order]
        ends = np.r_[np.flatnonzero(np.diff(sorted_scores) != 0), len(scores) - 1]
        cumulative_tp = np.cumsum(sorted_y)[ends]
        cumulative_fp = ends + 1 - cumulative_tp
        if positive:
            delta_recall = np.diff(np.r_[0, cumulative_tp]) / positive
            result["average_precision"] = float(np.sum(delta_recall * cumulative_tp / (ends + 1)))
        else:
            undefined["average_precision"] = "no_positive_probability_rows"
        if positive and negative:
            tpr, fpr = np.r_[0, cumulative_tp / positive], np.r_[0, cumulative_fp / negative]
            result["auroc"] = float(np.sum(np.diff(fpr) * (tpr[1:] + tpr[:-1]) / 2))
        else:
            undefined["auroc"] = (
                "no_positive_probability_rows" if not positive else "no_negative_probability_rows"
            )
    else:
        undefined.update(
            dict.fromkeys(
                ("auroc", "average_precision", "brier_score", "ece"), "no_probability_rows"
            )
        )
    result["undefined"] = undefined
    return result


def _validate_panel(panel: BinaryPanel) -> tuple[np.ndarray, np.ndarray]:
    truth, predicted = _binary(panel.truth), _binary(panel.predicted)
    if len(truth) != len(panel.keys) or truth.shape != predicted.shape or not len(truth):
        raise ValueError("each panel must have nonempty, matching ECG keys and binary arrays")
    if any(len(key) != 2 or not all(key) for key in panel.keys):
        raise ValueError("each ECG key must contain source and record_id")
    if len(set(panel.keys)) != len(panel.keys):
        raise ValueError("duplicate ECG within a panel")
    return truth, predicted


def cluster_bootstrap(
    panels: Mapping[str, BinaryPanel],
    *,
    seed: int = 2026,
    n_bootstrap: int = 2000,
    confidence: float = 0.95,
    cluster_ids: Mapping[ECGKey, str] | None = None,
) -> dict[str, Any]:
    """Resample the union of ECGs, carrying all their panel rows together.

    A draw absent from any declared panel is invalid for both macro statistics.
    Missing-positive classes in a present panel keep F1=0, never leave the macro.
    """
    if not isinstance(seed, int) or seed < 0 or not isinstance(n_bootstrap, int) or n_bootstrap < 0:
        raise ValueError("seed and n_bootstrap must be nonnegative integers")
    if not 0 < confidence < 1 or not panels:
        raise ValueError("confidence must be between 0 and 1 and panels must be nonempty")
    validated = [_validate_panel(panel) for panel in panels.values()]
    ecg_keys = {key for panel in panels.values() for key in panel.keys}
    if cluster_ids is not None:
        if any(key not in cluster_ids or not cluster_ids[key] for key in ecg_keys):
            raise ValueError("cluster_ids must identify every ECG with a nonempty cluster ID")
        if any(not isinstance(cluster_ids[key], str) for key in ecg_keys):
            raise ValueError("cluster IDs must be strings")
    grouped = {
        key: ("patient", cluster_ids[key]) if cluster_ids is not None else key
        for key in ecg_keys
    }
    keys = sorted(set(grouped.values()))
    positions = {key: index for index, key in enumerate(keys)}
    # Per-cluster sufficient statistics retain multiplicities across panels.
    contributions = np.zeros((len(keys), len(panels), 4), dtype=np.int64)
    for j, (panel, (truth, predicted)) in enumerate(zip(panels.values(), validated, strict=True)):
        for key, y, pred in zip(panel.keys, truth, predicted, strict=True):
            index = 0 if y and pred else 3 if y else 2 if pred else 1
            contributions[positions[grouped[key]], j, index] += 1
    rng = np.random.Generator(np.random.PCG64(seed))
    f1_values, accuracy_values = [], []
    for _ in range(n_bootstrap):
        weights = np.bincount(rng.integers(0, len(keys), size=len(keys)), minlength=len(keys))
        counts = np.einsum("i,ijk->jk", weights, contributions)
        sizes = counts.sum(axis=1)
        if np.any(sizes == 0):
            continue
        tp, tn, fp, fn = counts.T
        denominator = 2 * tp + fp + fn
        f1_values.append(
            float(
                np.mean(
                    np.divide(
                        2 * tp, denominator, out=np.zeros(len(panels)), where=denominator != 0
                    )
                )
            )
        )
        accuracy_values.append(float(np.mean((tp + tn) / sizes)))

    def interval(values: list[float]) -> dict[str, Any]:
        tail = (1 - confidence) / 2
        low, high = (
            np.quantile(values, [tail, 1 - tail], method="linear") if values else (None, None)
        )
        return {
            "low": float(low) if low is not None else None,
            "high": float(high) if high is not None else None,
            "valid_replicates": len(values),
            "invalid_replicates": n_bootstrap - len(values),
            "status": "ok" if values else "disabled" if not n_bootstrap else "no_valid_replicates",
        }

    return {
        "unit": "supplied_patient_id" if cluster_ids is not None else "ECG_source_record_id",
        "n_clusters": len(keys),
        "method": "unstratified_cluster_percentile",
        "confidence": confidence,
        "seed": seed,
        "n_bootstrap": n_bootstrap,
        "rng": "numpy.PCG64",
        "macro_f1": interval(f1_values),
        "mean_panel_accuracy": interval(accuracy_values),
    }


def _bool(value: str | None) -> int:
    if value is None or value.strip().lower() not in {"true", "false", "0", "1"}:
        raise ValueError("missing or invalid binary decision/correctness flag")
    return int(value.strip().lower() in {"true", "1"})


def _labels(value: str | None, classes: Sequence[str], *, allow_empty: bool = False) -> set[str]:
    if value is None:
        raise ValueError("missing label set column")
    labels = set(value.split("|")) if value else set()
    if (not labels and not allow_empty) or labels.difference(classes):
        raise ValueError("missing or unknown labels in saved prediction evidence")
    return labels


def _keys(rows: list[dict[str, str]]) -> tuple[ECGKey, ...]:
    result = []
    for row in rows:
        source, record_id = row.get("source", ""), row.get("record_id", "")
        # Only public source identifiers are exported, never arbitrary paths.
        if (
            not source
            or not re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", source)
            or any(part in {".", ".."} for part in source.split("/"))
        ):
            raise ValueError("source must be a public source identifier, not a private path")
        if not record_id or record_id != record_id.strip():
            raise ValueError("missing or invalid record_id; no fallback to row/patient identity")
        result.append((source, record_id))
    return tuple(result)


def _supports(keys: Sequence[ECGKey]) -> dict[str, int]:
    return {
        "rows": len(keys),
        "unique_record_ids": len({key[1] for key in keys}),
        "unique_ecgs": len(set(keys)),
    }


def _fingerprint(data: bytes) -> dict[str, Any]:
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return {
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "sha256_lf_normalized": hashlib.sha256(normalized).hexdigest(),
    }


def _load(root: Path, name: str, inputs: dict[str, Any]) -> list[dict[str, str]]:
    relative = EVIDENCE / name
    data = (root / relative).read_bytes()
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""))
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError(f"missing or duplicate CSV headers in {name}")
    rows = list(reader)
    if not rows or any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError(f"empty or structurally incomplete CSV: {name}")
    inputs[relative.as_posix()] = {**_fingerprint(data), "rows": len(rows)}
    return rows


def _panel_report(
    panel: BinaryPanel,
    probabilities: Sequence[Any] | None,
    *,
    score_field: str | None,
    threshold: float | None,
    ece_bins: int,
) -> dict[str, Any]:
    truth, predicted = _validate_panel(panel)
    return {
        **binary_metrics(truth, predicted, probabilities, ece_bins=ece_bins),
        "unique_ecgs": len(set(panel.keys)),
        "probability_field": score_field,
        "threshold": threshold,
    }


def _aggregate(classes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = list(classes.values())
    rows = sum(panel["rows"] for panel in values)
    tp, tn, fp, fn = (sum(panel[key] for panel in values) for key in ("tp", "tn", "fp", "fn"))
    return {
        "classes": classes,
        "panel_observations": rows,
        "macro_f1": float(np.mean([panel["f1"] for panel in values])),
        "mean_panel_accuracy": float(np.mean([panel["accuracy"] for panel in values])),
        "pooled_accuracy": (tp + tn) / rows,
        "pooled_f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
        "no_positive_classes": [
            label for label, panel in classes.items() if not panel["positive_support"]
        ],
    }


def _source_supports(keys: Sequence[ECGKey], panels: Mapping[str, BinaryPanel]) -> dict[str, Any]:
    sources = {}
    for source in sorted({key[0] for key in keys}):
        class_supports = {}
        for label, panel in panels.items():
            mask = np.array([key[0] == source for key in panel.keys])
            selected_keys = [key for key in panel.keys if key[0] == source]
            positive = int(panel.truth[mask].sum())
            class_supports[label] = {
                **_supports(selected_keys),
                "positive_support": positive,
                "negative_support": len(selected_keys) - positive,
            }
        sources[source] = {
            **_supports([key for key in keys if key[0] == source]),
            "classes": class_supports,
            "no_positive_classes": [
                label for label, counts in class_supports.items() if not counts["positive_support"]
            ],
        }
    return sources


def _score_column(rows: list[dict[str, str]], name: str) -> Sequence[Any] | None:
    return [row[name] for row in rows] if name in rows[0] else None


def _rhythm(
    root: Path,
    profile_name: str,
    inputs: dict[str, Any],
    *,
    seed: int,
    n_bootstrap: int,
    confidence: float,
    ece_bins: int,
) -> dict[str, Any]:
    p8 = profile_name == "rhythm_primary8"
    profile = CANONICAL_PROFILES[profile_name]
    rows = _load(root, f"rhythm_primary{8 if p8 else 6}_record_predictions.csv", inputs)
    keys = _keys(rows)
    truth_field, pred_field = (
        ("accepted_labels", "predicted_label") if p8 else ("true_labels", "pred_label")
    )
    references = [_labels(row[truth_field], profile.classes) for row in rows]
    predictions = [row[pred_field] for row in rows]
    if any(pred not in profile.classes for pred in predictions):
        raise ValueError("unknown top-1 prediction")
    correct = [pred in labels for pred, labels in zip(predictions, references, strict=True)]
    flag = "accepted_correct" if p8 else "correct"
    if any(_bool(row[flag]) != ok for row, ok in zip(rows, correct, strict=True)):
        raise ValueError("accepted-label correctness flags disagree with saved labels")
    predicted_sets = (
        [_labels(row["predicted_labels"], profile.classes, allow_empty=True) for row in rows]
        if p8
        else []
    )
    panels, metrics = {}, {}
    for label, threshold in zip(profile.classes, profile.thresholds, strict=True):
        truth = np.array([label in labels for labels in references], dtype=np.int64)
        if p8:
            pred = np.array([label in labels for labels in predicted_sets], dtype=np.int64)
        else:
            saved_truth = np.array([_bool(row[f"truth_{label}"]) for row in rows])
            if not np.array_equal(saved_truth, truth):
                raise ValueError("Primary6 truth columns disagree with true_labels")
            pred = np.array([_bool(row[f"threshold_pass_{label}"]) for row in rows])
        panels[label] = BinaryPanel(keys, truth, pred)
        field = f"{'membership_prob' if p8 else 'prob'}_{label}"
        metrics[label] = _panel_report(
            panels[label],
            _score_column(rows, field),
            score_field=field,
            threshold=threshold,
            ece_bins=ece_bins,
        )
    result: dict[str, Any] = {
        "supports": _supports(keys),
        "accepted_label": {
            "rows": len(rows),
            "correct": sum(correct),
            "accuracy": sum(correct) / len(rows),
            "rule": f"{pred_field} in {truth_field}",
        },
        "binary_panels": _aggregate(metrics),
        "sources": _source_supports(keys, panels),
        "bootstrap": cluster_bootstrap(
            panels, seed=seed, n_bootstrap=n_bootstrap, confidence=confidence
        ),
    }
    for source, counts in result["sources"].items():
        successes = sum(ok for key, ok in zip(keys, correct, strict=True) if key[0] == source)
        counts["accepted_correct"] = successes
        counts["accepted_accuracy"] = successes / counts["rows"]
    if p8:
        targets = [row["target_label"] for row in rows]
        if any(target not in labels for target, labels in zip(targets, references, strict=True)):
            raise ValueError("Primary8 target_label must belong to accepted_labels")
        target_correct = [target == pred for target, pred in zip(targets, predictions, strict=True)]
        if any(
            _bool(row["single_label_correct"]) != ok
            for row, ok in zip(rows, target_correct, strict=True)
        ):
            raise ValueError("Primary8 single-target correctness flags disagree with labels")
        target_panels, target_metrics = {}, {}
        matrix = np.zeros((len(profile.classes), len(profile.classes)), dtype=np.int64)
        for target, pred in zip(targets, predictions, strict=True):
            matrix[profile.classes.index(target), profile.classes.index(pred)] += 1
        for label in profile.classes:
            panel = BinaryPanel(
                keys,
                np.array([target == label for target in targets], dtype=np.int64),
                np.array([pred == label for pred in predictions], dtype=np.int64),
            )
            target_panels[label] = panel
            field = f"prob_{label}"
            target_metrics[label] = _panel_report(
                panel,
                _score_column(rows, field),
                score_field=field,
                threshold=None,
                ece_bins=ece_bins,
            )
        result["single_target"] = {
            "rows": len(rows),
            "correct": sum(target_correct),
            "accuracy": sum(target_correct) / len(rows),
            "rule": "target_label == predicted_label on all rows; not a strict-single-reference subset",
            "classes": target_metrics,
            "macro_f1": float(np.mean([p["f1"] for p in target_metrics.values()])),
            "confusion_matrix": {
                "labels": list(profile.classes),
                "rows": "target_label",
                "columns": "predicted_label",
                "values": matrix.tolist(),
            },
            "bootstrap": cluster_bootstrap(
                target_panels, seed=seed, n_bootstrap=n_bootstrap, confidence=confidence
            ),
        }
    # This diagnostic is not a replacement decision rule and never tunes scores.
    audit: dict[str, Any] = {"threshold_disagreements": {}}
    for label, panel in panels.items():
        field = f"{'membership_prob' if p8 else 'prob'}_{label}"
        probability = _probabilities(_score_column(rows, field), len(rows))
        valid = ~np.isnan(probability)
        threshold = profile.thresholds[profile.classes.index(label)]
        audit["threshold_disagreements"][label] = {
            "evaluable_rows": int(valid.sum()),
            "disagreements": int(
                np.sum((probability[valid] >= threshold) != panel.predicted[valid])
            ),
        }
    if p8:
        probability_matrix = np.column_stack(
            [
                _probabilities(_score_column(rows, f"prob_{label}"), len(rows))
                for label in profile.classes
            ]
        )
        valid = ~np.any(np.isnan(probability_matrix), axis=1)
        argmax_labels = np.array(profile.classes)[np.argmax(probability_matrix[valid], axis=1)]
        audit["prob_argmax_evaluable_rows"] = int(valid.sum())
        audit["prob_argmax_disagreements"] = int(
            np.sum(argmax_labels != np.array(predictions)[valid])
        )
    result["probability_decision_audit"] = audit
    return result


def _pathology(
    root: Path,
    inputs: dict[str, Any],
    *,
    seed: int,
    n_bootstrap: int,
    confidence: float,
    ece_bins: int,
) -> dict[str, Any]:
    panels, metrics, all_keys = {}, {}, []
    profile = CANONICAL_PROFILES["pathology_primary4"]
    for label, declared_threshold in zip(profile.classes, profile.thresholds, strict=True):
        rows = _load(root, f"pathology_primary4_{label}_record_predictions.csv", inputs)
        keys = _keys(rows)
        if any(row["pathology"] != label for row in rows):
            raise ValueError("pathology label disagrees with CSV panel")
        truth = np.array([_bool(row["target"]) for row in rows])
        predicted = np.array([_bool(row["predicted"]) for row in rows])
        if any(
            _bool(row["correct"]) != (y == pred)
            for row, y, pred in zip(rows, truth, predicted, strict=True)
        ):
            raise ValueError("Primary4 correctness flags disagree with binary targets/decisions")
        thresholds = _probabilities([row["threshold"] for row in rows], len(rows))
        if np.any(np.isnan(thresholds)) or not np.allclose(
            thresholds, declared_threshold, rtol=0, atol=1e-12
        ):
            raise ValueError("Primary4 CSV thresholds disagree with frozen model contract")
        probability = _probabilities(_score_column(rows, "probability"), len(rows))
        valid = ~np.isnan(probability)
        if np.any((probability[valid] >= thresholds[valid]) != predicted[valid]):
            raise ValueError("Primary4 saved predictions disagree with their saved thresholds")
        panel = BinaryPanel(keys, truth, predicted)
        panels[label] = panel
        metrics[label] = _panel_report(
            panel,
            probability,
            score_field="probability",
            threshold=declared_threshold,
            ece_bins=ece_bins,
        )
        all_keys.extend(keys)
    return {
        "supports": _supports(all_keys),
        "binary_panels": _aggregate(metrics),
        "sources": _source_supports(all_keys, panels),
        "bootstrap": cluster_bootstrap(
            panels, seed=seed, n_bootstrap=n_bootstrap, confidence=confidence
        ),
    }


def _git_revision(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = result.stdout.strip()
    return value if result.returncode == 0 and re.fullmatch(r"[0-9a-f]{40,64}", value) else None


def build_revision_report(
    root: str | Path,
    *,
    seed: int = 2026,
    n_bootstrap: int = 2000,
    confidence: float = 0.95,
    ece_bins: int = 10,
) -> dict[str, Any]:
    """Read only six saved-prediction CSVs; export no record paths or identifiers."""
    root = Path(root).resolve()
    inputs: dict[str, Any] = {}
    settings = {
        "seed": seed,
        "n_bootstrap": n_bootstrap,
        "confidence": confidence,
        "ece_bins": ece_bins,
    }
    profiles = {
        name: _rhythm(root, name, inputs, **settings)
        for name in ("rhythm_primary6_diagnostic", "rhythm_primary8")
    }
    profiles["pathology_primary4"] = _pathology(root, inputs, **settings)
    for name, result in profiles.items():
        contract = CANONICAL_PROFILES[name]
        result["model_contract"] = {
            "release_role": contract.release_role,
            "classes": list(contract.classes),
            "backbone_sha256": contract.backbone_sha256,
            "specialist_sha256": contract.specialist_sha256,
            "status": "declared_release_contract_not_weight_or_inference_verification",
        }
    implementation_root = Path(__file__).resolve().parents[3]
    code_paths = [
        "src/titan_v45/evaluation/revision_report.py",
        "scripts/evaluation/build_revision_report.py",
        "src/titan_v45/contracts/profiles.py",
    ]
    code = {name: _fingerprint((implementation_root / name).read_bytes()) for name in code_paths}
    return {
        "schema": SCHEMA,
        "scope": "saved_predictions",
        "evaluation_scope": "external_dev",
        "evidence_classification": "repeated_external_development",
        "configuration": settings,
        "definitions": {
            "ecg_identity": "(source, record_id); not a patient or independently verified waveform identity",
            "supports": "rows are observations; positive_support is tp+fn; negative_support is tn+fp; multilabel supports may sum above record count",
            "macro_f1": "unweighted mean binary F1 over the fixed declared classes; F1 zero denominator is 0",
            "mean_panel_accuracy": "unweighted arithmetic mean of panel accuracies; not pooled accuracy or top-1 accuracy",
            "pooled_accuracy": "sum(tp+tn)/sum(panel rows); P4 ECGs may contribute multiple panel observations",
            "probability_metrics": "classwise one-versus-rest, available scores only; Brier=mean((p-y)^2); ECE=sum(bin_n/score_n * abs(mean(p)-mean(y)))",
            "probability_columns": "P6 prob_<class> vs truth_<class>; P8 membership_prob_<class> vs accepted_labels and separately prob_<class> vs target_label; P4 probability vs target",
            "ece_bins": "equal width on [0,1]; left inclusive, right exclusive except last includes 1",
            "auroc_ap": "empirical ROC trapezoids; non-interpolated average precision; tied scores processed together",
            "null_policy": "no target/decision/identity rows dropped; missing scores excluded only from probability metrics with denominators disclosed; undefined metrics JSON null with reasons",
            "bootstrap": "sorted union of source/record_id ECGs; unstratified draws with replacement; all panels share cluster multiplicity; absent-panel replicates invalid; fixed-class zero F1 policy; linear percentile CI",
            "bootstrap_streams": "each profile and target view restarts PCG64(seed); no paired cross-profile comparison",
        },
        "limitations": [
            "Saved predictions only: no waveform inference, retraining, threshold selection or test tuning.",
            "Repeated external-dev evaluation, not untouched external-final or clinical validation; CIs do not correct selection or domain bias.",
            "No validated patient identifiers used; ECG bootstrap is not patient-level uncertainty and cannot exclude dependence between ECGs from one person.",
            "Primary4 panels are selected high-confidence binary cohorts, not a prevalence-representative all-ECG multiclass cohort.",
            "Primary6 and Primary4 have different declared backbones; these results do not validate a single joint checkpoint.",
            "Probability metrics describe named saved score columns only; P8 columns do not consistently reconstruct saved decisions. No decisions are replaced with argmax or retuned thresholds.",
            "Input and code hashes verify bytes, not source-data rights, clinical labels, waveform identity or actual model execution provenance.",
            "Manuscript tables are not inputs: class F1 and panel supports are recomputed, not a verification or edit of manuscript Table 9.",
        ],
        "profiles": profiles,
        "integrity": {
            "inputs": inputs,
            "implementation": code,
            "git_revision": _git_revision(root),
            "runtime": {"python": sys.version.split()[0], "numpy": np.__version__},
            "weights_verified": False,
            "hash_policy": "sha256 is exact bytes; sha256_lf_normalized normalizes CRLF/CR to LF",
            "git_revision_note": "base revision only; implementation hashes include uncommitted generator code",
        },
    }


def _serialized(report: Any) -> str:
    return json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _flatten(value: Any, prefix: str = ""):
    if isinstance(value, dict) and value:
        for key in sorted(value):
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            yield from _flatten(value[key], f"{prefix}/{escaped}")
    else:
        yield prefix, json.dumps(value, sort_keys=True, allow_nan=False)


def _write_table(path: Path, records: list[dict[str, Any]]) -> None:
    fields = list(dict.fromkeys(key for record in records for key in record))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, restval="null", lineterminator="\n")
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    key: "null"
                    if value is None
                    else json.dumps(value, sort_keys=True)
                    if isinstance(value, dict)
                    else value
                    for key, value in record.items()
                }
            )


def _write_figures(report: dict[str, Any], destination: Path) -> tuple[list[str], str]:
    try:
        import matplotlib
    except ImportError as exc:
        raise ValueError(
            "--figures requires matplotlib from the existing dev dependencies"
        ) from exc

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    profiles = report["profiles"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), layout="constrained")
    views = [
        ("P6 diagnostic / binary", profiles["rhythm_primary6_diagnostic"], "binary_panels"),
        ("P8 candidate / binary", profiles["rhythm_primary8"], "binary_panels"),
        ("P8 single target", profiles["rhythm_primary8"], "single_target"),
        ("P4 binary panels", profiles["pathology_primary4"], "binary_panels"),
    ]
    for index, (_, profile, view) in enumerate(views):
        payload = profile[view]
        bootstrap = payload["bootstrap"] if view == "single_target" else profile["bootstrap"]
        interval = bootstrap["macro_f1"]
        if interval["low"] is not None:
            axes[0].hlines(index, interval["low"], interval["high"], color="#157866", linewidth=2)
        axes[0].plot(payload["macro_f1"], index, "o", color="#157866")
        axes[0].annotate(
            f"{payload['macro_f1']:.4f}",
            (payload["macro_f1"], index),
            xytext=(0, 9),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )
    axes[0].set_yticks(range(len(views)), [view[0] for view in views])
    axes[0].set_title("Fixed-class macro-F1")
    axes[0].set_ylim(3.6, -0.6)
    p4 = profiles["pathology_primary4"]
    panel_metrics = p4["binary_panels"]
    interval = p4["bootstrap"]["mean_panel_accuracy"]
    if interval["low"] is not None:
        axes[1].hlines(0, interval["low"], interval["high"], color="#157866", linewidth=2)
    for index, metric in enumerate(("mean_panel_accuracy", "pooled_accuracy")):
        value = panel_metrics[metric]
        axes[1].plot(value, index, "o", color="#157866" if index == 0 else "#bd4935")
        axes[1].annotate(
            f"{value:.4f}",
            (value, index),
            xytext=(0, 9),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )
    axes[1].set_yticks([0, 1], ["Unweighted mean", "Pooled panel rows (no CI)"])
    axes[1].set_title("P4 accuracy denominators")
    axes[1].set_ylim(1.6, -0.6)
    for axis in axes:
        axis.set_xlim(0, 1)
        axis.set_xlabel("Score (0-1)")
        axis.grid(axis="x", alpha=0.2)
        axis.spines[["top", "right"]].set_visible(False)
    config = report["configuration"]
    fig.suptitle("TITAN V4.5 / saved predictions / repeated external-dev", fontsize=13)
    fig.supxlabel(
        f"{config['confidence']:.0%} ECG-cluster percentile CI; seed={config['seed']}; B={config['n_bootstrap']}\n"
        f"P4: {p4['supports']['rows']} panel rows / {p4['supports']['unique_ecgs']} ECGs; not patients",
        fontsize=9,
    )
    names = ["revision_metrics.png", "revision_metrics.pdf"]
    fig.savefig(destination / names[0], dpi=200)
    fig.savefig(
        destination / names[1], metadata={"Creator": SCHEMA, "CreationDate": None, "ModDate": None}
    )
    plt.close(fig)
    return names, matplotlib.__version__


def write_revision_report(
    report: dict[str, Any],
    output_dir: str | Path,
    *,
    figures: bool = False,
) -> dict[str, Any]:
    """Write deterministic JSON, lossless long-form CSV, class CSV and hashes."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    with (destination / "revision_report.json").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(_serialized(report))
    with (destination / "revision_report.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["field", "value_json"])
        writer.writerows(_flatten(report))
    records, summaries, sources = [], [], []
    for name, profile in report["profiles"].items():
        views = {"binary_panels": profile["binary_panels"]}
        if "single_target" in profile:
            views["single_target"] = profile["single_target"]
        for view, payload in views.items():
            for label, metrics in payload["classes"].items():
                records.append({"profile": name, "view": view, "class": label, **metrics})
            bootstrap = payload["bootstrap"] if view == "single_target" else profile["bootstrap"]
            summary = {
                "profile": name,
                "view": view,
                "scope": report["scope"],
                **profile["supports"],
                "macro_f1": payload["macro_f1"],
                "macro_f1_ci_low": bootstrap["macro_f1"]["low"],
                "macro_f1_ci_high": bootstrap["macro_f1"]["high"],
                "bootstrap_valid_replicates": bootstrap["macro_f1"]["valid_replicates"],
                "bootstrap_invalid_replicates": bootstrap["macro_f1"]["invalid_replicates"],
            }
            if view == "single_target":
                summary.update(
                    single_target_correct=payload["correct"],
                    single_target_accuracy=payload["accuracy"],
                )
            else:
                summary.update(
                    {
                        key: payload[key]
                        for key in (
                            "panel_observations",
                            "mean_panel_accuracy",
                            "pooled_accuracy",
                            "pooled_f1",
                        )
                    }
                )
                summary.update(
                    mean_panel_accuracy_ci_low=bootstrap["mean_panel_accuracy"]["low"],
                    mean_panel_accuracy_ci_high=bootstrap["mean_panel_accuracy"]["high"],
                )
                if "accepted_label" in profile:
                    summary.update(
                        accepted_correct=profile["accepted_label"]["correct"],
                        accepted_accuracy=profile["accepted_label"]["accuracy"],
                    )
            summaries.append(summary)
        for source, supports in profile["sources"].items():
            for label, counts in supports["classes"].items():
                sources.append({"profile": name, "source": source, "class": label, **counts})
    _write_table(destination / "class_metrics.csv", records)
    _write_table(destination / "summary.csv", summaries)
    _write_table(destination / "source_supports.csv", sources)
    names = [
        "revision_report.json",
        "revision_report.csv",
        "class_metrics.csv",
        "summary.csv",
        "source_supports.csv",
    ]
    figure_runtime = {}
    if figures:
        figure_names, version = _write_figures(report, destination)
        names.extend(figure_names)
        figure_runtime["matplotlib"] = version
    manifest = {
        "schema": SCHEMA,
        "scope": "saved_predictions",
        "figure_runtime": figure_runtime,
        "output_sha256": {
            name: hashlib.sha256((destination / name).read_bytes()).hexdigest() for name in names
        },
    }
    with (destination / "integrity.json").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(_serialized(manifest))
    return manifest
