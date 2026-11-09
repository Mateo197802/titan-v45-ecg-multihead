from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import torch
from torch import Tensor

SPLIT_NAMESPACE = "TITAN-V46-SPH-DEV-SPLIT-V1:"
SPLIT_SEED = "197802"
PAC_AGGREGATE_SCHEMA = "TITAN_V46_SPH_PAC_HEAD_COMPARISON_V2"
_PRIVATE_KEYS = {
    "ecg_id", "ecg_ids", "record_id", "record_ids", "patient_id", "patient_ids",
    "identifiers", "ids", "scores", "row_scores", "record_level_scores", "logits",
    "embeddings", "raw_signal", "raw_signals", "waveform", "waveforms",
    "record_predictions", "per_record_predictions",
}


class PacMLP(torch.nn.Module):
    """Single-hidden-layer sensitivity model for the frozen V3F representation."""

    def __init__(self, *, input_dim: int, hidden_dim: int = 64, dropout: float = 0.2) -> None:
        super().__init__()
        if input_dim < 1 or hidden_dim < 1 or not 0 <= dropout < 1:
            raise ValueError("invalid PAC MLP dimensions or dropout")
        self.network = torch.nn.Sequential(
            torch.nn.Linear(input_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Dropout(dropout),
            torch.nn.Linear(hidden_dim, 1),
        )

    def forward(self, features: Tensor) -> Tensor:
        return self.network(features).squeeze(-1)


@dataclass(frozen=True)
class FeatureStandardizer:
    mean: np.ndarray
    scale: np.ndarray

    def transform(self, features: np.ndarray) -> np.ndarray:
        values = np.asarray(features, dtype=np.float64)
        if values.ndim != 2 or values.shape[1] != self.mean.size:
            raise ValueError("feature width differs from the fitted standardizer")
        if not np.isfinite(values).all():
            raise ValueError("features must be finite")
        return (values - self.mean) / self.scale


def fit_standardizer(training_features: np.ndarray) -> FeatureStandardizer:
    """Fit a population standardizer on training rows only."""
    values = np.asarray(training_features, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] == 0 or not np.isfinite(values).all():
        raise ValueError("training features must be a nonempty finite matrix")
    mean = values.mean(axis=0)
    scale = values.std(axis=0)
    scale[scale < 1e-12] = 1.0
    return FeatureStandardizer(mean=mean, scale=scale)


@dataclass(frozen=True)
class PacMLPFit:
    model: PacMLP
    epochs_trained: int
    best_dev_average_precision: float
    device: str

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        values = np.asarray(features, dtype=np.float32)
        if values.ndim != 2 or values.shape[1] != self.model.network[0].in_features:
            raise ValueError("feature width differs from the fitted PAC MLP")
        if not np.isfinite(values).all():
            raise ValueError("features must be finite")
        with torch.inference_mode():
            logits = self.model(torch.as_tensor(values, device=self.device))
            return torch.sigmoid(logits).cpu().numpy().astype(np.float64, copy=False)


def fit_pac_mlp(
    training_features: np.ndarray,
    training_labels: np.ndarray,
    development_features: np.ndarray,
    development_labels: np.ndarray,
    *,
    seed: int,
    max_epochs: int = 200,
    patience: int = 20,
    batch_size: int = 512,
    learning_rate: float = 1e-3,
    weight_decay: float = 1e-4,
    hidden_dim: int = 64,
    dropout: float = 0.2,
    device: str = "cpu",
) -> PacMLPFit:
    """Fit the prespecified single-hidden-layer sensitivity head.

    Training is unweighted binary cross-entropy. Development average precision
    controls early stopping; no evaluation/holdout rows are accepted here.
    """
    x_train = np.asarray(training_features, dtype=np.float32)
    y_train = np.asarray(training_labels, dtype=np.float32).reshape(-1)
    x_dev = np.asarray(development_features, dtype=np.float32)
    y_dev = np.asarray(development_labels, dtype=np.float32).reshape(-1)
    if (x_train.ndim != 2 or x_train.shape[0] != y_train.size or x_train.shape[0] == 0
            or x_dev.ndim != 2 or x_dev.shape[0] != y_dev.size or x_dev.shape[0] == 0
            or x_train.shape[1] != x_dev.shape[1] or x_train.shape[1] == 0):
        raise ValueError("training and development matrices are empty or misaligned")
    if (not np.isfinite(x_train).all() or not np.isfinite(x_dev).all()
            or not np.isin(y_train, (0, 1)).all() or not np.isin(y_dev, (0, 1)).all()):
        raise ValueError("training or development data are nonfinite or nonbinary")
    if (not (y_train == 0).any() or not (y_train == 1).any()
            or not (y_dev == 0).any() or not (y_dev == 1).any()):
        raise ValueError("training and development require both statement classes")
    if (seed < 0 or max_epochs < 1 or patience < 1 or batch_size < 1
            or learning_rate <= 0 or weight_decay < 0):
        raise ValueError("invalid PAC MLP training hyperparameter")
    selected_device = torch.device(device)
    if selected_device.type == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA was requested but is not available")

    torch.manual_seed(seed)
    if selected_device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
    model = PacMLP(input_dim=x_train.shape[1], hidden_dim=hidden_dim, dropout=dropout)
    model.to(selected_device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=learning_rate, weight_decay=weight_decay
    )
    loss_function = torch.nn.BCEWithLogitsLoss()
    train_x = torch.as_tensor(x_train, device=selected_device)
    train_y = torch.as_tensor(y_train, device=selected_device)
    dev_x = torch.as_tensor(x_dev, device=selected_device)
    generator = torch.Generator(device="cpu").manual_seed(seed)
    best_ap = -1.0
    best_state = None
    stale_epochs = 0
    epochs_trained = 0

    for epoch in range(1, max_epochs + 1):
        epochs_trained = epoch
        model.train()
        order = torch.randperm(train_x.shape[0], generator=generator)
        for start in range(0, train_x.shape[0], batch_size):
            indices = order[start : start + batch_size].to(selected_device)
            optimizer.zero_grad(set_to_none=True)
            loss = loss_function(model(train_x[indices]), train_y[indices])
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.inference_mode():
            dev_scores = torch.sigmoid(model(dev_x)).cpu().numpy().astype(np.float64)
        dev_ap = _average_precision(y_dev.astype(np.int8), dev_scores)
        if dev_ap is None:
            raise ValueError("development average precision is undefined")
        if dev_ap > best_ap + 1e-12:
            best_ap = float(dev_ap)
            best_state = {
                name: tensor.detach().cpu().clone()
                for name, tensor in model.state_dict().items()
            }
            stale_epochs = 0
        else:
            stale_epochs += 1
            if stale_epochs >= patience:
                break

    if best_state is None:
        raise AssertionError("PAC MLP did not produce a development checkpoint")
    model.load_state_dict(best_state, strict=True)
    model.eval()
    return PacMLPFit(
        model=model,
        epochs_trained=epochs_trained,
        best_dev_average_precision=best_ap,
        device=str(selected_device),
    )


def assign_patient_split(patient_id: str) -> str:
    """Reuse the label-blind patient assignment frozen in the feasibility audit."""
    patient_id = patient_id.strip()
    if not patient_id:
        raise ValueError("missing patient identifier")
    raw = f"{SPLIT_NAMESPACE}{SPLIT_SEED}:{patient_id}".encode()
    bucket = int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") % 100
    if bucket < 70:
        return "train"
    if bucket < 85:
        return "development"
    return "calibration"


def pool_v3f_meanmax(
    model: torch.nn.Module,
    windows: Tensor,
    lead_mask: Tensor | None = None,
) -> Tensor:
    """Create one record embedding from all windows using frozen V3F token pooling.

    The input is one record's ``[window, 12, 1250]`` tensor. The returned
    representation concatenates layer-normalized temporal mean and maximum
    pools, each with the model's lead-mask context. All windows for a record
    must have the same lead mask.
    """
    if model.training:
        raise ValueError("V3F encoder must be in evaluation mode")
    if windows.ndim != 3 or windows.shape[0] < 1:
        raise ValueError("windows must have shape [window, 12, time]")
    if windows.shape[1] != model.in_channels:
        raise ValueError("window lead count differs from the encoder contract")
    if lead_mask is None:
        lead_mask = torch.ones(
            (windows.shape[0], model.in_channels), dtype=torch.bool, device=windows.device
        )
    if lead_mask.shape != (windows.shape[0], model.in_channels):
        raise ValueError("lead mask must align with the windows")
    if not torch.equal(lead_mask, lead_mask[:1].expand_as(lead_mask)):
        raise ValueError("all windows for one record must share the same lead mask")

    tokens, mask_context = encode_v3f_token_sequences(model, windows, lead_mask)
    temporal_mean = tokens.mean(dim=(0, 1), keepdim=True)
    temporal_max = tokens.amax(dim=(0, 1), keepdim=True)
    mean_embedding = model.final_norm(temporal_mean.squeeze(0) + mask_context[:1])
    max_embedding = model.final_norm(temporal_max.squeeze(0) + mask_context[:1])
    return torch.cat((mean_embedding, max_embedding), dim=1)


def encode_v3f_token_sequences(
    model: torch.nn.Module,
    windows: Tensor,
    lead_mask: Tensor,
) -> tuple[Tensor, Tensor]:
    """Return frozen V3F transformer tokens and per-window lead-mask context."""
    if model.training:
        raise ValueError("V3F encoder must be in evaluation mode")
    if windows.ndim != 3 or windows.shape[0] < 1 or windows.shape[1] != model.in_channels:
        raise ValueError("windows must have shape [window, 12, time]")
    if lead_mask.shape != (windows.shape[0], model.in_channels):
        raise ValueError("lead mask must align with the windows")
    if not torch.isfinite(windows).all():
        raise ValueError("windows must be finite")

    mask = lead_mask.to(device=windows.device, dtype=windows.dtype)
    values = windows * mask.unsqueeze(-1)
    values = model.stem(values)
    values = model.res_layers(values)
    values = model.token_projection(values)
    tokens = model.position(values.transpose(1, 2))
    tokens = model.transformer(tokens)
    return tokens, model.lead_mask_projection(mask)


def select_f1_threshold(labels: np.ndarray, scores: np.ndarray) -> float:
    """Choose the highest development threshold attaining maximum binary F1."""
    labels = np.asarray(labels, dtype=np.int8).reshape(-1)
    scores = np.asarray(scores, dtype=np.float64).reshape(-1)
    if labels.size == 0 or labels.size != scores.size:
        raise ValueError("labels and scores must be nonempty and aligned")
    if not np.isin(labels, (0, 1)).all() or not np.isfinite(scores).all():
        raise ValueError("labels or scores are invalid")
    if not (labels == 1).any() or not (labels == 0).any():
        raise ValueError("threshold tuning requires both reference classes")

    best_f1 = -1.0
    best_threshold = -np.inf
    for threshold in np.unique(scores):
        predicted = scores >= threshold
        true_positive = int(np.count_nonzero(predicted & (labels == 1)))
        false_positive = int(np.count_nonzero(predicted & (labels == 0)))
        false_negative = int(np.count_nonzero(~predicted & (labels == 1)))
        denominator = 2 * true_positive + false_positive + false_negative
        f1 = 2 * true_positive / denominator if denominator else 0.0
        if f1 > best_f1 or (f1 == best_f1 and threshold > best_threshold):
            best_f1 = f1
            best_threshold = float(threshold)
    return best_threshold


@dataclass(frozen=True)
class L2LogisticModel:
    coefficients: np.ndarray
    intercept: float
    converged: bool
    iterations: int

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        from scipy.special import expit

        values = np.asarray(features, dtype=np.float64)
        if values.ndim != 2 or values.shape[1] != self.coefficients.size:
            raise ValueError("feature width differs from the fitted logistic model")
        return expit(values @ self.coefficients + self.intercept)


def fit_l2_logistic(
    features: np.ndarray,
    labels: np.ndarray,
    *,
    c_value: float = 1.0,
) -> L2LogisticModel:
    """Fit binary L2 logistic regression by average log loss and L-BFGS-B."""
    from scipy.optimize import minimize
    from scipy.special import expit

    values = np.asarray(features, dtype=np.float64)
    targets = np.asarray(labels, dtype=np.float64).reshape(-1)
    if (values.ndim != 2 or values.shape[0] != targets.size or values.shape[0] == 0
            or not np.isfinite(values).all() or not np.isin(targets, (0, 1)).all()):
        raise ValueError("logistic training data are empty, nonfinite or misaligned")
    if not np.isfinite(c_value) or c_value <= 0:
        raise ValueError("C must be finite and positive")
    if not (targets == 0).any() or not (targets == 1).any():
        raise ValueError("logistic training requires both reference classes")

    n_rows = values.shape[0]
    regularization = 1.0 / (c_value * n_rows)

    def objective(parameters: np.ndarray) -> tuple[float, np.ndarray]:
        weights, bias = parameters[:-1], parameters[-1]
        logits = values @ weights + bias
        loss = float(np.mean(np.logaddexp(0.0, logits) - targets * logits))
        loss += 0.5 * regularization * float(weights @ weights)
        residual = expit(logits) - targets
        gradient = np.empty_like(parameters)
        gradient[:-1] = values.T @ residual / n_rows + regularization * weights
        gradient[-1] = residual.mean()
        return loss, gradient

    result = minimize(
        objective,
        np.zeros(values.shape[1] + 1, dtype=np.float64),
        method="L-BFGS-B",
        jac=True,
        options={"maxiter": 1000, "ftol": 1e-12},
    )
    return L2LogisticModel(
        coefficients=np.asarray(result.x[:-1], dtype=np.float64),
        intercept=float(result.x[-1]),
        converged=bool(result.success),
        iterations=int(result.nit),
    )


def _auc(labels: np.ndarray, scores: np.ndarray) -> float | None:
    positives = int((labels == 1).sum())
    negatives = int((labels == 0).sum())
    if not positives or not negatives:
        return None
    order = np.argsort(scores, kind="mergesort")
    sorted_scores = scores[order]
    ranks = np.empty(scores.size, dtype=np.float64)
    start = 0
    while start < scores.size:
        stop = start + 1
        while stop < scores.size and sorted_scores[stop] == sorted_scores[start]:
            stop += 1
        ranks[order[start:stop]] = ((start + 1) + stop) / 2.0
        start = stop
    positive_rank_sum = float(ranks[labels == 1].sum())
    return (positive_rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def _average_precision(labels: np.ndarray, scores: np.ndarray) -> float | None:
    positives = int((labels == 1).sum())
    if not positives:
        return None
    average_precision = 0.0
    prior_recall = 0.0
    for threshold in np.unique(scores)[::-1]:
        selected = scores >= threshold
        true_positive = int(np.count_nonzero(selected & (labels == 1)))
        false_positive = int(np.count_nonzero(selected & (labels == 0)))
        recall = true_positive / positives
        precision = true_positive / (true_positive + false_positive)
        average_precision += (recall - prior_recall) * precision
        prior_recall = recall
    return average_precision


def binary_metrics(
    labels: np.ndarray,
    scores: np.ndarray,
    *,
    threshold: float,
    ece_bins: int = 10,
) -> dict[str, object]:
    labels = np.asarray(labels, dtype=np.int8).reshape(-1)
    scores = np.asarray(scores, dtype=np.float64).reshape(-1)
    if (labels.size == 0 or labels.size != scores.size or not np.isin(labels, (0, 1)).all()
            or not np.isfinite(scores).all() or np.any((scores < 0) | (scores > 1))):
        raise ValueError("binary metric inputs are empty, nonfinite or misaligned")
    if not np.isfinite(threshold) or not 0 <= threshold <= 1 or ece_bins < 1:
        raise ValueError("invalid threshold or ECE bin count")

    predicted = scores >= threshold
    positive = labels == 1
    negative = ~positive
    tp = int(np.count_nonzero(predicted & positive))
    fp = int(np.count_nonzero(predicted & negative))
    tn = int(np.count_nonzero(~predicted & negative))
    fn = int(np.count_nonzero(~predicted & positive))

    def ratio(numerator: int, denominator: int) -> float | None:
        return numerator / denominator if denominator else None

    bins = np.minimum((scores * ece_bins).astype(np.int64), ece_bins - 1)
    ece = 0.0
    for index in range(ece_bins):
        selected = bins == index
        if selected.any():
            ece += float(selected.mean()) * abs(float(scores[selected].mean()) - float(labels[selected].mean()))

    return {
        "records": int(labels.size),
        "positive_records": int(positive.sum()),
        "negative_records": int(negative.sum()),
        "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "accuracy": ratio(tp + tn, labels.size),
        "sensitivity": ratio(tp, tp + fn),
        "specificity": ratio(tn, tn + fp),
        "ppv": ratio(tp, tp + fp),
        "npv": ratio(tn, tn + fn),
        "f1": ratio(2 * tp, 2 * tp + fp + fn),
        "auroc": _auc(labels, scores),
        "average_precision": _average_precision(labels, scores),
        "brier": float(np.mean((scores - labels) ** 2)),
        "ece": ece,
        "threshold": float(threshold),
    }


def patient_cluster_bootstrap(
    labels: np.ndarray,
    scores_a: np.ndarray,
    scores_b: np.ndarray,
    patient_ids: np.ndarray,
    threshold_a: float,
    threshold_b: float,
    *,
    replicates: int,
    seed: int,
) -> dict[str, object]:
    """Paired percentile bootstrap, resampling whole patient clusters."""
    labels = np.asarray(labels, dtype=np.int8).reshape(-1)
    scores_a = np.asarray(scores_a, dtype=np.float64).reshape(-1)
    scores_b = np.asarray(scores_b, dtype=np.float64).reshape(-1)
    patient_ids = np.asarray(patient_ids).reshape(-1)
    if (labels.size == 0 or any(array.size != labels.size for array in (scores_a, scores_b, patient_ids))
            or replicates < 1):
        raise ValueError("bootstrap inputs are empty, misaligned or invalid")
    if not np.isfinite(scores_a).all() or not np.isfinite(scores_b).all():
        raise ValueError("bootstrap scores must be finite")

    patient_rows: dict[str, list[int]] = {}
    for row_index, patient_id in enumerate(patient_ids):
        key = str(patient_id)
        if not key.strip():
            raise ValueError("missing patient identifier in bootstrap inputs")
        patient_rows.setdefault(key, []).append(row_index)
    patients = sorted(patient_rows)
    row_indices = {key: np.asarray(value, dtype=np.int64) for key, value in patient_rows.items()}
    rng = np.random.Generator(np.random.PCG64(seed))
    point_a = binary_metrics(labels, scores_a, threshold=threshold_a)
    point_b = binary_metrics(labels, scores_b, threshold=threshold_b)
    metric_names = ("accuracy", "sensitivity", "specificity", "ppv", "npv", "f1", "auroc",
                    "average_precision", "brier", "ece")
    values_a = {name: [] for name in metric_names}
    values_b = {name: [] for name in metric_names}
    deltas = {name: [] for name in metric_names}
    invalid = 0
    for _ in range(replicates):
        sampled_patients = rng.choice(patients, size=len(patients), replace=True)
        indices = np.concatenate([row_indices[str(patient)] for patient in sampled_patients])
        if not (labels[indices] == 0).any() or not (labels[indices] == 1).any():
            invalid += 1
            continue
        metrics_a = binary_metrics(labels[indices], scores_a[indices], threshold=threshold_a)
        metrics_b = binary_metrics(labels[indices], scores_b[indices], threshold=threshold_b)
        for name in metric_names:
            a_value, b_value = metrics_a[name], metrics_b[name]
            if a_value is None or b_value is None:
                continue
            values_a[name].append(float(a_value))
            values_b[name].append(float(b_value))
            deltas[name].append(float(b_value) - float(a_value))

    def summarize(values: list[float]) -> list[float] | None:
        if not values:
            return None
        low, high = np.percentile(np.asarray(values, dtype=np.float64), [2.5, 97.5])
        return [float(low), float(high)]

    output = {}
    for name in metric_names:
        output[name] = {
            "point_a": point_a[name],
            "ci95_a": summarize(values_a[name]),
            "point_b": point_b[name],
            "ci95_b": summarize(values_b[name]),
            "delta_b_minus_a": (
                float(point_b[name]) - float(point_a[name])
                if point_a[name] is not None and point_b[name] is not None
                else None
            ),
            "delta_ci95": summarize(deltas[name]),
            "valid_replicates": len(deltas[name]),
        }
    return {
        "unit": "patient_id cluster; repeated ECGs sampled together",
        "method": "paired unstratified percentile bootstrap",
        "replicates": replicates,
        "seed": seed,
        "valid_replicates": replicates - invalid,
        "invalid_replicates": invalid,
        "metrics": output,
    }


def validate_pac_aggregate(report: dict[str, object]) -> None:
    """Reject incomplete, inconsistent, or record-level PAC result reports."""
    import re

    def reject_private(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                normalized = str(key).lower().replace("-", "_")
                if normalized in _PRIVATE_KEYS:
                    raise ValueError("aggregate contains private or record-level content")
                reject_private(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                reject_private(child)

    reject_private(report)
    if report.get("schema") != PAC_AGGREGATE_SCHEMA:
        raise ValueError("unexpected PAC aggregate schema")
    if "exploratory" not in str(report.get("scope", "")).lower():
        raise ValueError("PAC result scope must remain explicitly exploratory")

    inputs = report.get("inputs")
    if not isinstance(inputs, dict) or not inputs:
        raise ValueError("PAC aggregate input hashes are missing")
    for name, digest in inputs.items():
        if not isinstance(name, str) or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("PAC aggregate input hash is malformed")

    privacy = report.get("privacy")
    expected_privacy = {
        "individual_identifiers_exported": False,
        "record_level_scores_exported": False,
        "raw_signals_exported": False,
        "embeddings_exported": False,
    }
    if not isinstance(privacy, dict) or any(privacy.get(key) is not False for key in expected_privacy):
        raise ValueError("PAC aggregate privacy declarations are missing or unsafe")

    cohort = report.get("cohort")
    if not isinstance(cohort, dict):
        raise ValueError("PAC cohort summary is missing")

    def count(value: object, name: str, *, minimum: int = 0) -> int:
        if type(value) is not int or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")
        return value

    source_records = count(cohort.get("source_records"), "source_records", minimum=1)
    source_patients = count(cohort.get("source_patients"), "source_patients", minimum=1)
    eligible_records = count(cohort.get("eligible_records"), "eligible_records")
    if eligible_records > source_records or source_patients > source_records:
        raise ValueError("PAC cohort source denominators are inconsistent")
    if (cohort.get("patient_overlap_across_splits") != 0
            or cohort.get("labels_used_for_split_assignment") is not False):
        raise ValueError("PAC patient split independence or label-blind assignment is not certified")

    split_support = cohort.get("split_support")
    required_splits = ("train", "development", "exploratory_holdout")
    if not isinstance(split_support, dict) or set(split_support) != set(required_splits):
        raise ValueError("PAC split support must contain the three frozen patient partitions")
    total_records = total_patients = 0
    for split in required_splits:
        support = split_support[split]
        if not isinstance(support, dict):
            raise ValueError(f"{split} support is malformed")
        records = count(support.get("records"), f"{split}.records")
        patients = count(support.get("patients"), f"{split}.patients")
        positive_records = count(support.get("positive_records"), f"{split}.positive_records")
        positive_patients = count(support.get("positive_patients"), f"{split}.positive_patients")
        if (positive_records > records or positive_patients > patients
                or positive_patients > positive_records or patients > records):
            raise ValueError(f"{split} PAC supports are inconsistent")
        total_records += records
        total_patients += patients
    if total_records != eligible_records or total_patients > source_patients:
        raise ValueError("PAC partition denominators do not reconcile to the cohort")

    models = report.get("models")
    mlp_seeds = (197802, 197803, 197804, 197805, 197806)
    required_models = {
        "frozen_v45_p8_pac", "logistic_regression",
        *(f"mlp_seed_{seed}" for seed in mlp_seeds),
    }
    if not isinstance(models, dict) or set(models) != required_models:
        raise ValueError("PAC comparison must report P8, logistic, and all five frozen MLP seeds")
    baseline = report.get("p8_baseline")
    baseline_inputs = report.get("inputs", {})
    if (not isinstance(baseline, dict)
            or baseline.get("job_id") != "32668"
            or baseline.get("ledger_sha256") != baseline_inputs.get("v45_p8_score_ledger")
            or baseline.get("receipt_sha256") != baseline_inputs.get("v45_p8_scoring_receipt")
            or baseline.get("checkpoint_sha256") != baseline_inputs.get("p8_specialist")
            or baseline.get("threshold") != 0.45):
        raise ValueError("frozen V4.5 P8 baseline provenance or threshold is inconsistent")
    if (not isinstance(models, dict)
            or models.get("frozen_v45_p8_pac", {}).get("threshold") != baseline["threshold"]):
        raise ValueError("frozen V4.5 P8 model result does not use its original threshold")
    if (cohort.get("baseline_p8_scores_available_source_records") != source_records
            or cohort.get("baseline_p8_common_eligible_records") != eligible_records):
        raise ValueError("frozen P8 score coverage does not match the declared cohort")
    holdout = split_support["exploratory_holdout"]
    for name in sorted(required_models):
        model = models[name]
        if not isinstance(model, dict):
            raise ValueError(f"{name} result is malformed")
        threshold = model.get("threshold")
        if (not isinstance(threshold, (int, float)) or isinstance(threshold, bool)
                or not np.isfinite(threshold) or not 0 <= threshold <= 1):
            raise ValueError(f"{name} threshold is invalid")
        if name.startswith("mlp_seed_") and model.get("seed") != int(name.removeprefix("mlp_seed_")):
            raise ValueError(f"{name} model seed differs from its frozen identity")
        metrics = model.get("exploratory_holdout_metrics")
        if not isinstance(metrics, dict):
            raise ValueError(f"{name} holdout metrics are missing")
        records = count(metrics.get("records"), f"{name}.metrics.records")
        positives = count(metrics.get("positive_records"), f"{name}.metrics.positive_records")
        negatives = count(metrics.get("negative_records"), f"{name}.metrics.negative_records")
        if (records != holdout["records"] or positives != holdout["positive_records"]
                or negatives != records - positives):
            raise ValueError(f"{name} holdout metric denominator does not reconcile")
        if metrics.get("threshold") != threshold:
            raise ValueError(f"{name} holdout metric threshold differs from the reported frozen threshold")
        confusion = metrics.get("confusion")
        if not isinstance(confusion, dict) or set(confusion) != {"tp", "fp", "tn", "fn"}:
            raise ValueError(f"{name} confusion matrix is malformed")
        confusion_counts = [count(confusion[key], f"{name}.confusion.{key}")
                            for key in ("tp", "fp", "tn", "fn")]
        if sum(confusion_counts) != records:
            raise ValueError(f"{name} confusion denominator does not reconcile")
        if confusion["tp"] + confusion["fn"] != positives:
            raise ValueError(f"{name} positive support does not reconcile")
        if confusion["tn"] + confusion["fp"] != negatives:
            raise ValueError(f"{name} negative support does not reconcile")
        def ratio(numerator: int, denominator: int) -> float | None:
            return None if denominator == 0 else numerator / denominator

        derived = {
            "accuracy": ratio(confusion["tp"] + confusion["tn"], records),
            "sensitivity": ratio(confusion["tp"], confusion["tp"] + confusion["fn"]),
            "specificity": ratio(confusion["tn"], confusion["tn"] + confusion["fp"]),
            "ppv": ratio(confusion["tp"], confusion["tp"] + confusion["fp"]),
            "npv": ratio(confusion["tn"], confusion["tn"] + confusion["fn"]),
            "f1": ratio(2 * confusion["tp"], 2 * confusion["tp"] + confusion["fp"] + confusion["fn"]),
        }
        for metric, expected in derived.items():
            actual = metrics.get(metric)
            if expected is None:
                if actual is not None:
                    raise ValueError(f"{name}.{metric} does not reconcile with confusion")
            elif not isinstance(actual, (int, float)) or not np.isclose(
                actual, expected, rtol=1e-9, atol=1e-12
            ):
                raise ValueError(f"{name}.{metric} does not reconcile with confusion")
        for metric in ("auroc", "average_precision", "brier", "ece"):
            value = metrics.get(metric)
            if value is not None and (not isinstance(value, (int, float))
                                      or isinstance(value, bool) or not np.isfinite(value)
                                      or not 0 <= value <= 1):
                raise ValueError(f"{name}.{metric} is outside [0, 1]")

    bootstrap = report.get("paired_patient_cluster_bootstrap")
    if not isinstance(bootstrap, dict):
        raise ValueError("paired patient-cluster bootstrap is missing")
    replicates = count(bootstrap.get("replicates"), "bootstrap.replicates", minimum=1)
    if (bootstrap.get("unit") != "patient_id cluster; repeated ECGs sampled together"
            or bootstrap.get("method") != "paired unstratified percentile bootstrap"):
        raise ValueError("bootstrap sampling unit is inconsistent")
    comparisons = bootstrap.get("comparisons")
    expected_pairs = {"logistic_regression_minus_frozen_v45_p8_pac": (
        "frozen_v45_p8_pac", "logistic_regression",
    )}
    for seed in mlp_seeds:
        name = f"mlp_seed_{seed}"
        expected_pairs[f"{name}_minus_frozen_v45_p8_pac"] = ("frozen_v45_p8_pac", name)
        expected_pairs[f"{name}_minus_logistic_regression"] = ("logistic_regression", name)
    if not isinstance(comparisons, dict) or set(comparisons) != set(expected_pairs):
        raise ValueError("paired bootstrap must compare every new PAC head with P8 and each MLP with logistic")
    metric_names = (
        "accuracy", "sensitivity", "specificity", "ppv", "npv", "f1",
        "auroc", "average_precision", "brier", "ece",
    )
    for pair_name, (reference, candidate) in expected_pairs.items():
        pair = comparisons[pair_name]
        if (not isinstance(pair, dict)
                or pair.get("reference_model") != reference
                or pair.get("candidate_model") != candidate):
            raise ValueError(f"bootstrap comparison {pair_name} has incorrect model identities")
        valid = count(pair.get("valid_replicates"), f"{pair_name}.valid_replicates")
        invalid = count(pair.get("invalid_replicates"), f"{pair_name}.invalid_replicates")
        if valid + invalid != replicates:
            raise ValueError(f"bootstrap comparison {pair_name} replicate counts do not reconcile")
        bootstrap_metrics = pair.get("metrics")
        if not isinstance(bootstrap_metrics, dict) or set(bootstrap_metrics) != set(metric_names):
            raise ValueError(f"bootstrap comparison {pair_name} metric set differs from protocol")
        for metric in metric_names:
            interval = bootstrap_metrics[metric]
            if not isinstance(interval, dict):
                raise ValueError(f"bootstrap.{pair_name}.{metric} is malformed")
            for key, model_name in (("point_a", reference), ("point_b", candidate)):
                expected = models[model_name]["exploratory_holdout_metrics"].get(metric)
                actual = interval.get(key)
                if expected is None:
                    if actual is not None:
                        raise ValueError(f"bootstrap.{pair_name}.{metric}.{key} differs from holdout metrics")
                elif actual is None or not np.isclose(actual, expected, rtol=1e-9, atol=1e-12):
                    raise ValueError(f"bootstrap.{pair_name}.{metric}.{key} differs from holdout metrics")
            point_a, point_b = interval["point_a"], interval["point_b"]
            expected_delta = point_b - point_a if point_a is not None and point_b is not None else None
            if interval.get("delta_b_minus_a") is None:
                if expected_delta is not None:
                    raise ValueError(f"bootstrap.{pair_name}.{metric} delta is missing")
            elif expected_delta is None or not np.isclose(
                interval["delta_b_minus_a"], expected_delta, rtol=1e-9, atol=1e-12
            ):
                raise ValueError(f"bootstrap.{pair_name}.{metric} delta does not reconcile")
            metric_valid = count(interval.get("valid_replicates"), f"{pair_name}.{metric}.valid_replicates")
            if metric_valid > valid:
                raise ValueError(f"bootstrap.{pair_name}.{metric} has more valid draws than its pair")
            for key in ("ci95_a", "ci95_b", "delta_ci95"):
                bounds = interval.get(key)
                if bounds is not None and (
                    not isinstance(bounds, list) or len(bounds) != 2
                    or any(not isinstance(value, (int, float)) or not np.isfinite(value) for value in bounds)
                    or bounds[0] > bounds[1]
                ):
                    raise ValueError(f"bootstrap.{pair_name}.{metric}.{key} is malformed")
