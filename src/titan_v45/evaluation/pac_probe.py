"""Exploratory patient-grouped PAC probes on frozen V3F embeddings."""
from __future__ import annotations

from collections import defaultdict

import numpy as np


def pool_v3f_tokens(token_embeddings):
    """Concatenate mean and max of one window's post-transformer tokens."""
    values = np.asarray(token_embeddings, dtype=np.float32)
    if (values.ndim != 3 or not values.shape[0] or not values.shape[1]
            or not values.shape[2] or not np.isfinite(values).all()):
        raise ValueError("expected finite [windows, tokens, features] V3F embeddings")
    return np.concatenate([values.mean(axis=1), values.max(axis=1)], axis=1)


def pool_record_windows(window_embeddings):
    """Average fixed-window mean+max embeddings into one vector per ECG."""
    values = np.asarray(window_embeddings, dtype=np.float32)
    if values.ndim != 2 or not len(values) or not values.shape[1] or not np.isfinite(values).all():
        raise ValueError("expected finite [windows, features] embeddings")
    return values.mean(axis=0, dtype=np.float64).astype(np.float32)


def patient_component_ids(patient_ids, signal_hashes=None):
    """Return stable component labels after joining patients with shared exact signals."""
    patients = np.asarray(patient_ids, dtype=str)
    if patients.ndim != 1 or not len(patients) or np.any(patients == ""):
        raise ValueError("patient IDs must be a nonempty one-dimensional array")
    parent = {patient: patient for patient in set(patients)}

    def find(patient):
        while parent[patient] != patient:
            parent[patient] = parent[parent[patient]]
            patient = parent[patient]
        return patient

    if signal_hashes is not None:
        hashes = np.asarray(signal_hashes, dtype=str)
        if hashes.ndim != 1 or len(hashes) != len(patients):
            raise ValueError("signal hashes and patient IDs must have the same length")
        patients_by_hash = defaultdict(set)
        for patient, digest in zip(patients, hashes, strict=True):
            if digest:
                patients_by_hash[digest].add(patient)
        for linked_patients in patients_by_hash.values():
            ordered = sorted(linked_patients)
            for patient in ordered[1:]:
                left, right = find(ordered[0]), find(patient)
                if left != right:
                    first, second = sorted((left, right))
                    parent[second] = first
    return np.asarray([find(patient) for patient in patients], dtype=str)


def patient_group_split(
    patient_ids,
    labels,
    *,
    signal_hashes=None,
    train_fraction=0.8,
    seed=20261109,
):
    """Create a deterministic patient-stratified split, joining exact-signal links first."""
    patients = np.asarray(patient_ids, dtype=str)
    target = np.asarray(labels)
    if patients.ndim != 1 or target.ndim != 1 or len(patients) != len(target):
        raise ValueError("patient IDs and labels must have the same length")
    if not len(patients) or np.any(patients == ""):
        raise ValueError("patient IDs must be nonempty")
    if not np.isin(target, [0, 1, False, True]).all():
        raise ValueError("PAC labels must be binary")
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between zero and one")

    if signal_hashes is not None:
        hashes = np.asarray(signal_hashes, dtype=str)
        if hashes.ndim != 1 or len(hashes) != len(patients):
            raise ValueError("signal hashes and patient IDs must have the same length")
    components = patient_component_ids(patients, signal_hashes)
    groups = defaultdict(list)
    for index, component in enumerate(components):
        groups[component].append(index)
    group_positive = {
        group: bool(np.asarray(target)[indices].astype(bool).any())
        for group, indices in groups.items()
    }
    rng = np.random.Generator(np.random.PCG64(seed))
    train_groups = set()
    for is_positive in (False, True):
        stratum = sorted(group for group, value in group_positive.items() if value is is_positive)
        if len(stratum) < 2:
            raise ValueError("each patient class stratum needs at least two patient components")
        shuffled = np.asarray(stratum, dtype=object)[rng.permutation(len(stratum))]
        count = int(round(len(stratum) * train_fraction))
        count = min(max(count, 1), len(stratum) - 1)
        train_groups.update(shuffled[:count].tolist())

    train_indices = np.asarray(
        [index for group, indices in groups.items() if group in train_groups for index in indices],
        dtype=np.int64,
    )
    holdout_indices = np.asarray(
        [index for group, indices in groups.items() if group not in train_groups for index in indices],
        dtype=np.int64,
    )
    return np.sort(train_indices), np.sort(holdout_indices)


def duplicate_balanced_sample_weights(labels, signal_hashes):
    """Weight exact waveform groups equally, then balance classes using train rows only."""
    target = np.asarray(labels, dtype=np.int64)
    hashes = np.asarray(signal_hashes, dtype=str)
    if target.ndim != 1 or hashes.ndim != 1 or len(target) != len(hashes) or not len(target):
        raise ValueError("labels and signal hashes must be nonempty one-dimensional arrays")
    if not np.isin(target, [0, 1]).all() or np.any(hashes == ""):
        raise ValueError("binary labels and nonempty signal hashes are required")
    _, inverse, counts = np.unique(hashes, return_inverse=True, return_counts=True)
    weights = 1.0 / counts[inverse].astype(np.float64)
    masses = np.asarray([weights[target == label].sum() for label in (0, 1)])
    if np.any(masses == 0):
        raise ValueError("training split must contain both PAC classes")
    weights *= weights.sum() / (2 * masses[target])
    return (weights * (len(weights) / weights.sum())).astype(np.float32)


def _standardize_fit(features):
    values = np.asarray(features, dtype=np.float64)
    if values.ndim != 2 or not len(values) or not np.isfinite(values).all():
        raise ValueError("training features must be a finite nonempty matrix")
    mean = values.mean(axis=0)
    scale = values.std(axis=0)
    scale[scale < 1e-12] = 1.0
    return mean.astype(np.float32), scale.astype(np.float32)


def fit_logistic_probe(features, labels, sample_weights, *, c=1.0, max_iter=500):
    """Fit an L2-regularized weighted logistic baseline with fixed settings."""
    from scipy.optimize import minimize

    x = np.asarray(features, dtype=np.float64)
    y = np.asarray(labels, dtype=np.float64)
    sample_weight = np.asarray(sample_weights, dtype=np.float64)
    if (x.ndim != 2 or y.shape != (len(x),) or sample_weight.shape != (len(x),)
            or not len(x) or not np.isfinite(x).all() or not np.isfinite(y).all()
            or not np.isfinite(sample_weight).all() or np.any(sample_weight <= 0)
            or set(np.unique(y)) != {0.0, 1.0} or c <= 0):
        raise ValueError("invalid logistic training arrays or settings")
    mean, scale = _standardize_fit(x)
    standardized = (x - mean) / scale
    sample_weight /= sample_weight.sum()

    def objective(parameters):
        coefficient, intercept = parameters[:-1], parameters[-1]
        logits = standardized @ coefficient + intercept
        probabilities = 1.0 / (1.0 + np.exp(-np.clip(logits, -50, 50)))
        loss = np.logaddexp(0.0, logits) - y * logits
        value = np.sum(sample_weight * loss) + 0.5 * np.dot(coefficient, coefficient) / c
        residual = sample_weight * (probabilities - y)
        gradient = np.concatenate([
            standardized.T @ residual + coefficient / c,
            np.asarray([residual.sum()]),
        ])
        return float(value), gradient

    result = minimize(objective, np.zeros(x.shape[1] + 1), method="L-BFGS-B", jac=True,
                      options={"maxiter": int(max_iter), "ftol": 1e-12, "gtol": 1e-8})
    if not result.success:
        raise RuntimeError(f"logistic optimization failed: {result.message}")
    return {
        "mean": mean,
        "scale": scale,
        "coefficient": result.x[:-1].astype(np.float32),
        "intercept": float(result.x[-1]),
        "optimizer_success": bool(result.success),
        "optimizer_status": int(result.status),
        "optimizer_message": str(result.message),
        "c": float(c),
    }


def predict_logistic_probe(features, fit):
    x = np.asarray(features, dtype=np.float64)
    logits = ((x - fit["mean"]) / fit["scale"]) @ fit["coefficient"] + fit["intercept"]
    return (1.0 / (1.0 + np.exp(-np.clip(logits, -50, 50)))).astype(np.float64)


def fit_mlp_probe(
    features,
    labels,
    sample_weights,
    *,
    seed=20261109,
    epochs=100,
    batch_size=256,
    learning_rate=0.001,
    weight_decay=0.0001,
    dropout=0.2,
):
    """Fit the prespecified MLP sensitivity head on CPU using fixed epochs."""
    import torch
    from torch import nn

    x = np.asarray(features, dtype=np.float32)
    y = np.asarray(labels, dtype=np.float32)
    weights = np.asarray(sample_weights, dtype=np.float32)
    if (x.ndim != 2 or y.shape != (len(x),) or weights.shape != (len(x),)
            or not len(x) or not np.isfinite(x).all() or not np.isfinite(y).all()
            or not np.isfinite(weights).all() or np.any(weights <= 0)
            or set(np.unique(y)) != {0.0, 1.0} or epochs < 1 or batch_size < 1):
        raise ValueError("invalid MLP training arrays or settings")
    torch.manual_seed(seed)
    torch.set_num_threads(2)
    mean, scale = _standardize_fit(x)
    standardized = ((x - mean) / scale).astype(np.float32)

    class PACProbeMLP(nn.Module):
        def __init__(self, input_dim):
            super().__init__()
            self.layers = nn.Sequential(
                nn.Linear(input_dim, 256), nn.ReLU(), nn.Dropout(dropout),
                nn.Linear(256, 64), nn.ReLU(), nn.Dropout(dropout), nn.Linear(64, 1),
            )

        def forward(self, values):
            return self.layers(values).squeeze(-1)

    model = PACProbeMLP(x.shape[1]).cpu()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    criterion = nn.BCEWithLogitsLoss(reduction="none")
    train_x = torch.from_numpy(standardized)
    train_y = torch.from_numpy(y)
    train_weights = torch.from_numpy(weights / weights.mean())
    generator = torch.Generator(device="cpu").manual_seed(seed)
    for _ in range(epochs):
        model.train()
        order = torch.randperm(len(train_x), generator=generator)
        for start in range(0, len(order), batch_size):
            batch = order[start:start + batch_size]
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(train_x[batch]), train_y[batch])
            loss = (loss * train_weights[batch]).mean()
            loss.backward()
            optimizer.step()
    model.eval()
    return {"mean": mean, "scale": scale, "state_dict": model.state_dict(),
            "input_dim": int(x.shape[1]), "seed": int(seed), "epochs": int(epochs),
            "batch_size": int(batch_size), "learning_rate": float(learning_rate),
            "weight_decay": float(weight_decay), "dropout": float(dropout)}


def predict_mlp_probe(features, fit):
    import torch
    from torch import nn

    class PACProbeMLP(nn.Module):
        def __init__(self, input_dim):
            super().__init__()
            self.layers = nn.Sequential(
                nn.Linear(input_dim, 256), nn.ReLU(), nn.Dropout(fit["dropout"]),
                nn.Linear(256, 64), nn.ReLU(), nn.Dropout(fit["dropout"]), nn.Linear(64, 1),
            )

        def forward(self, values):
            return self.layers(values).squeeze(-1)

    model = PACProbeMLP(fit["input_dim"]).cpu()
    model.load_state_dict(fit["state_dict"], strict=True)
    model.eval()
    x = ((np.asarray(features, dtype=np.float32) - fit["mean"]) / fit["scale"]).astype(np.float32)
    with torch.inference_mode():
        logits = model(torch.from_numpy(x)).numpy()
    return (1.0 / (1.0 + np.exp(-np.clip(logits, -50, 50)))).astype(np.float64)


def binary_metrics(labels, scores, *, threshold=0.5, ece_bins=10):
    """Calculate binary record-level metrics with explicit undefined denominators."""
    y = np.asarray(labels, dtype=np.int8)
    probability = np.asarray(scores, dtype=np.float64)
    if (y.ndim != 1 or probability.shape != y.shape or not len(y)
            or not np.isin(y, [0, 1]).all() or not np.isfinite(probability).all()
            or np.any((probability < 0) | (probability > 1)) or not 0 <= threshold <= 1
            or ece_bins < 1):
        raise ValueError("invalid labels, probabilities or metric settings")
    predicted = probability >= threshold
    positive = y == 1
    negative = ~positive
    tp = int(np.count_nonzero(predicted & positive))
    fp = int(np.count_nonzero(predicted & negative))
    tn = int(np.count_nonzero(~predicted & negative))
    fn = int(np.count_nonzero(~predicted & positive))

    def ratio(numerator, denominator):
        return float(numerator / denominator) if denominator else None

    sensitivity = ratio(tp, tp + fn)
    specificity = ratio(tn, tn + fp)
    precision = ratio(tp, tp + fp)
    recall = sensitivity
    f1 = ratio(2 * tp, 2 * tp + fp + fn)
    auroc = None
    average_precision = None
    if positive.any() and negative.any():
        order = np.argsort(probability, kind="mergesort")
        sorted_scores = probability[order]
        ranks = np.empty(len(y), dtype=np.float64)
        start = 0
        while start < len(y):
            end = start + 1
            while end < len(y) and sorted_scores[end] == sorted_scores[start]:
                end += 1
            ranks[order[start:end]] = (start + 1 + end) / 2.0
            start = end
        positives = int(positive.sum())
        negatives = int(negative.sum())
        auroc = float((ranks[positive].sum() - positives * (positives + 1) / 2)
                      / (positives * negatives))

        descending = np.argsort(-probability, kind="mergesort")
        ordered_scores, ordered_y = probability[descending], y[descending]
        tp_cumulative = fp_cumulative = 0
        previous_recall = 0.0
        average_precision = 0.0
        start = 0
        while start < len(y):
            end = start + 1
            while end < len(y) and ordered_scores[end] == ordered_scores[start]:
                end += 1
            tp_cumulative += int(ordered_y[start:end].sum())
            fp_cumulative += int(end - start - ordered_y[start:end].sum())
            current_recall = tp_cumulative / positives
            current_precision = tp_cumulative / (tp_cumulative + fp_cumulative)
            average_precision += (current_recall - previous_recall) * current_precision
            previous_recall = current_recall
            start = end

    bins = np.minimum((probability * ece_bins).astype(np.int64), ece_bins - 1)
    ece = 0.0
    for bin_index in range(ece_bins):
        selected = bins == bin_index
        if selected.any():
            ece += float(selected.mean() * abs(y[selected].mean() - probability[selected].mean()))
    return {
        "n": int(len(y)),
        "support": {"positive": int(positive.sum()), "negative": int(negative.sum())},
        "threshold": float(threshold),
        "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "accuracy": float((tp + tn) / len(y)),
        "sensitivity": sensitivity,
        "specificity": specificity,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "auroc": auroc,
        "average_precision": average_precision,
        "brier_score": float(np.mean((probability - y) ** 2)),
        "ece": float(ece),
        "ece_bins": int(ece_bins),
    }


def patient_cluster_bootstrap(labels, scores, patient_components, *, replicates=2000, seed=20261109):
    """Bootstrap record metrics by patient/exact-waveform connected component."""
    y = np.asarray(labels, dtype=np.int8)
    probability = np.asarray(scores, dtype=np.float64)
    components = np.asarray(patient_components, dtype=str)
    if y.ndim != 1 or probability.shape != y.shape or components.shape != y.shape:
        raise ValueError("labels, scores and patient components must have equal lengths")
    if not len(y) or np.any(components == "") or replicates < 1:
        raise ValueError("nonempty patient components and positive replicates are required")
    order = np.argsort(components, kind="mergesort")
    ordered_components = components[order]
    starts = np.concatenate(([0], np.flatnonzero(
        ordered_components[1:] != ordered_components[:-1]
    ) + 1))
    ends = np.concatenate((starts[1:], [len(order)]))
    rows_by_component = {
        str(ordered_components[start]): order[start:end]
        for start, end in zip(starts, ends, strict=True)
    }
    component_ids = np.asarray(sorted(rows_by_component), dtype=object)
    rng = np.random.Generator(np.random.PCG64(seed))
    metric_names = ("accuracy", "sensitivity", "specificity", "precision", "recall", "f1",
                    "auroc", "average_precision", "brier_score", "ece")
    samples = {name: [] for name in metric_names}
    for _ in range(replicates):
        sampled = rng.choice(component_ids, size=len(component_ids), replace=True)
        indices = np.concatenate([rows_by_component[key] for key in sampled])
        report = binary_metrics(y[indices], probability[indices])
        for name in metric_names:
            if report[name] is not None and np.isfinite(report[name]):
                samples[name].append(float(report[name]))
    return {
        "unit": "patient/exact-waveform connected component",
        "method": "unstratified percentile bootstrap",
        "replicates_requested": int(replicates),
        "seed": int(seed),
        "confidence_level": 0.95,
        "intervals": {
            name: {
                "valid_replicates": len(values),
                "invalid_replicates": replicates - len(values),
                "lower": float(np.quantile(values, 0.025)) if values else None,
                "upper": float(np.quantile(values, 0.975)) if values else None,
            }
            for name, values in samples.items()
        },
    }
