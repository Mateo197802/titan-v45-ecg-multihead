"""Label, split, and loss primitives for the new frozen-backbone pilot."""
from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping, Sequence

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from titan_v45.models.specialists import ClassWiseBinaryMLP

RHYTHM_CLASSES_P8 = ("AFIB", "SB", "STACH", "NSR", "RBBB", "PAC", "1AVB", "PVC")
RHYTHM_CLASSES_P6 = ("AFIB", "SB", "STACH", "RBBB", "1AVB", "PVC")
P4_CLASSES = ("ASMI", "LVH", "IMI", "ISC_")

CHALLENGE_2021_CODES = {
    "AFIB": frozenset({"164889003"}),
    "SB": frozenset({"426177001"}),
    "STACH": frozenset({"427084000"}),
    "NSR": frozenset({"426783006"}),
    "RBBB": frozenset({"59118001", "713427006", "713426002"}),
    "PAC": frozenset({"284470004", "63593006"}),
    "1AVB": frozenset({"270492004"}),
    "PVC": frozenset({"427172004", "17338001"}),
}

PTBXL_P4_CODES = {name: frozenset({name}) for name in P4_CLASSES}


def rhythm_targets(
    dx_codes: Iterable[str],
    classes: Sequence[str],
    *,
    supported_classes: Iterable[str],
) -> tuple[np.ndarray, np.ndarray]:
    """Map a complete Challenge Dx list; unsupported source labels remain masked."""
    supported = frozenset(supported_classes)
    if not classes or len(set(classes)) != len(classes) or not supported <= set(classes):
        raise ValueError("invalid rhythm class contract")
    codes = frozenset(str(code).strip() for code in dx_codes if str(code).strip())
    targets = np.zeros(len(classes), dtype=np.float32)
    mask = np.zeros(len(classes), dtype=bool)
    for index, name in enumerate(classes):
        if name not in CHALLENGE_2021_CODES:
            raise ValueError(f"unknown rhythm class: {name}")
        if name in supported:
            mask[index] = True
            targets[index] = float(bool(codes & CHALLENGE_2021_CODES[name]))
    return targets, mask


def ptbxl_p4_targets(scp_likelihoods: Mapping[str, float]) -> tuple[np.ndarray, np.ndarray]:
    """Return positives and explicit-NORM controls; unknown/unlabeled cells are masked."""
    values: dict[str, float] = {}
    for code, raw_value in scp_likelihoods.items():
        value = float(raw_value)
        if not np.isfinite(value) or value < 0:
            raise ValueError("PTB-XL SCP likelihoods must be finite and nonnegative")
        values[str(code)] = value

    positive = {name for name in P4_CLASSES if values.get(name, 0.0) > 0}
    has_unknown_target = any(name in values for name in P4_CLASSES if name not in positive)
    is_explicit_normal_control = values.get("NORM", 0.0) > 0 and not positive and not has_unknown_target
    targets = np.zeros(len(P4_CLASSES), dtype=np.float32)
    mask = np.zeros(len(P4_CLASSES), dtype=bool)
    for index, name in enumerate(P4_CLASSES):
        if name in positive:
            targets[index], mask[index] = 1.0, True
        elif is_explicit_normal_control:
            mask[index] = True
    return targets, mask


def stable_fraction(key: str, *, seed: int, namespace: str) -> float:
    if not key or seed < 0 or not namespace:
        raise ValueError("stable split inputs must be nonempty and seed nonnegative")
    payload = f"{namespace}\0{seed}\0{key}".encode()
    number = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return number / 2**64


def split_bucket(
    key: str,
    *,
    seed: int,
    namespace: str,
    train_fraction: float,
    validation_fraction: float,
) -> str:
    if not 0 < train_fraction < 1 or not 0 <= validation_fraction < 1:
        raise ValueError("split fractions are invalid")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("split fractions must leave a calibration bucket")
    fraction = stable_fraction(key, seed=seed, namespace=namespace)
    if fraction < train_fraction:
        return "train"
    if fraction < train_fraction + validation_fraction:
        return "validation"
    return "calibration"


def source_balanced_element_weights(
    source_ids: Sequence[str],
    mask: torch.Tensor,
    *,
    window_weights: torch.Tensor | None = None,
) -> torch.Tensor:
    """Equalize active source contribution per class without changing labels."""
    if mask.ndim != 2 or len(source_ids) != mask.shape[0] or any(not source for source in source_ids):
        raise ValueError("source IDs and label mask must be aligned")
    device = mask.device
    active = mask.to(dtype=torch.bool)
    base = torch.ones(mask.shape[0], dtype=torch.float32, device=device)
    if window_weights is not None:
        if window_weights.shape != (mask.shape[0],) or not torch.isfinite(window_weights).all():
            raise ValueError("window weights must be finite and row-aligned")
        if torch.any(window_weights < 0):
            raise ValueError("window weights must be nonnegative")
        base = window_weights.to(device=device, dtype=torch.float32)

    weights = torch.zeros(mask.shape, dtype=torch.float32, device=device)
    unique_sources = tuple(sorted(set(source_ids)))
    source_index = {name: index for index, name in enumerate(unique_sources)}
    row_sources = torch.tensor([source_index[name] for name in source_ids], device=device)
    for class_index in range(mask.shape[1]):
        present = active[:, class_index]
        contributing = []
        for index in range(len(unique_sources)):
            source_rows = row_sources == index
            total = base[source_rows & present].sum()
            if float(total) > 0:
                contributing.append((source_rows, total))
        if not contributing:
            continue
        for source_rows, total in contributing:
            selected = source_rows & present
            weights[selected, class_index] = base[selected] / total / len(contributing)
    return weights


def masked_binary_cross_entropy(
    logits: torch.Tensor,
    targets: torch.Tensor,
    mask: torch.Tensor,
    *,
    pos_weight: torch.Tensor | None = None,
    element_weights: torch.Tensor | None = None,
) -> torch.Tensor:
    if logits.ndim != 2 or targets.shape != logits.shape or mask.shape != logits.shape:
        raise ValueError("logits, targets, and mask must be aligned matrices")
    active = mask.to(device=logits.device, dtype=torch.bool)
    if not torch.any(active):
        raise ValueError("masked BCE has no observed labels")
    target_values = targets.to(device=logits.device, dtype=logits.dtype)
    if not torch.isfinite(target_values[active]).all() or torch.any(
        (target_values[active] != 0) & (target_values[active] != 1)
    ):
        raise ValueError("observed targets must be finite and binary")
    clean_targets = torch.where(active, target_values, torch.zeros_like(target_values))
    loss = F.binary_cross_entropy_with_logits(
        logits,
        clean_targets,
        pos_weight=None if pos_weight is None else pos_weight.to(logits.device, logits.dtype),
        reduction="none",
    )
    weights = active.to(dtype=loss.dtype)
    if element_weights is not None:
        if element_weights.shape != logits.shape or not torch.isfinite(element_weights).all():
            raise ValueError("element weights must be finite and aligned")
        if torch.any(element_weights < 0):
            raise ValueError("element weights must be nonnegative")
        weights = weights * element_weights.to(device=logits.device, dtype=loss.dtype)
    denominator = weights.sum()
    if float(denominator) <= 0:
        raise ValueError("masked BCE has zero total weight")
    return (loss * weights).sum() / denominator


def classwise_positive_weights(
    targets: torch.Tensor,
    mask: torch.Tensor,
    element_weights: torch.Tensor,
    *,
    maximum: float = 10.0,
) -> torch.Tensor:
    if targets.ndim != 2 or mask.shape != targets.shape or element_weights.shape != targets.shape:
        raise ValueError("targets, mask, and element weights must be aligned matrices")
    if not np.isfinite(maximum) or maximum < 1:
        raise ValueError("maximum positive weight must be finite and at least one")
    active = mask.to(dtype=torch.bool)
    values = targets.to(dtype=torch.float32)
    weights = element_weights.to(device=targets.device, dtype=torch.float32) * active
    positive = (weights * values).sum(dim=0)
    negative = (weights * (1 - values)).sum(dim=0)
    if torch.any(positive <= 0) or torch.any(negative <= 0):
        raise ValueError("each trained class requires observed positive and negative examples")
    return (negative / positive).clamp(min=1.0, max=float(maximum))


def classwise_focal_alpha(
    targets: torch.Tensor, mask: torch.Tensor, element_weights: torch.Tensor
) -> torch.Tensor:
    if targets.ndim != 2 or mask.shape != targets.shape or element_weights.shape != targets.shape:
        raise ValueError("targets, mask, and element weights must be aligned matrices")
    active = mask.to(dtype=torch.bool)
    values = targets.to(dtype=torch.float32)
    weights = element_weights.to(device=targets.device, dtype=torch.float32) * active
    positive = (weights * values).sum(dim=0)
    negative = (weights * (1 - values)).sum(dim=0)
    total = positive + negative
    if torch.any(positive <= 0) or torch.any(negative <= 0):
        raise ValueError("each trained class requires observed positive and negative examples")
    return negative / total


def masked_binary_focal_loss(
    logits: torch.Tensor,
    targets: torch.Tensor,
    mask: torch.Tensor,
    *,
    alpha_positive: torch.Tensor,
    gamma: float = 2.0,
    element_weights: torch.Tensor | None = None,
) -> torch.Tensor:
    if logits.ndim != 2 or targets.shape != logits.shape or mask.shape != logits.shape:
        raise ValueError("logits, targets, and mask must be aligned matrices")
    if alpha_positive.shape != (logits.shape[1],) or not torch.isfinite(alpha_positive).all():
        raise ValueError("focal alpha must be a finite per-class vector")
    if torch.any((alpha_positive <= 0) | (alpha_positive >= 1)) or not np.isfinite(gamma) or gamma < 0:
        raise ValueError("focal alpha and gamma are outside their valid ranges")
    active = mask.to(device=logits.device, dtype=torch.bool)
    target_values = targets.to(device=logits.device, dtype=logits.dtype)
    if not torch.isfinite(target_values[active]).all() or torch.any(
        (target_values[active] != 0) & (target_values[active] != 1)
    ):
        raise ValueError("observed targets must be finite and binary")
    clean_targets = torch.where(active, target_values, torch.zeros_like(target_values))
    probability = torch.sigmoid(logits)
    probability_of_target = probability * clean_targets + (1 - probability) * (1 - clean_targets)
    alpha = alpha_positive.to(device=logits.device, dtype=logits.dtype).unsqueeze(0)
    alpha_of_target = alpha * clean_targets + (1 - alpha) * (1 - clean_targets)
    cells = F.binary_cross_entropy_with_logits(logits, clean_targets, reduction="none")
    cells = cells * alpha_of_target * (1 - probability_of_target).pow(gamma)
    weights = active.to(dtype=cells.dtype)
    if element_weights is not None:
        if element_weights.shape != logits.shape or not torch.isfinite(element_weights).all():
            raise ValueError("element weights must be finite and aligned")
        if torch.any(element_weights < 0):
            raise ValueError("element weights must be nonnegative")
        weights = weights * element_weights.to(device=logits.device, dtype=cells.dtype)
    denominator = weights.sum()
    if float(denominator) <= 0:
        raise ValueError("masked focal loss has zero total weight")
    return (cells * weights).sum() / denominator


def _mean_observed_class_loss(
    logits: torch.Tensor, targets: torch.Tensor, mask: torch.Tensor
) -> torch.Tensor:
    active = mask.to(device=logits.device, dtype=torch.bool)
    clean_targets = torch.where(active, targets.to(logits.device, logits.dtype), 0.0)
    cells = F.binary_cross_entropy_with_logits(logits, clean_targets, reduction="none")
    counts = active.sum(dim=0)
    present_classes = counts > 0
    if not torch.any(present_classes):
        raise ValueError("validation has no observed labels")
    per_class = (cells * active).sum(dim=0) / counts.clamp(min=1)
    return per_class[present_classes].mean()


def _grouped_validation_loss(
    model: ClassWiseBinaryMLP,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    mask: torch.Tensor,
    group_ids: Sequence[str] | None,
    aggregation: str,
) -> torch.Tensor:
    if aggregation not in {"mean_logits", "mean_probabilities"}:
        raise ValueError("validation aggregation must be mean_logits or mean_probabilities")
    groups: dict[str, list[int]] = {}
    for index, group in enumerate(group_ids if group_ids is not None else map(str, range(len(inputs)))):
        groups.setdefault(str(group), []).append(index)
    record_logits, record_targets, record_masks = [], [], []
    model.eval()
    with torch.no_grad():
        window_logits = model(inputs)
        for indices in groups.values():
            selected = torch.as_tensor(indices, dtype=torch.long, device=inputs.device)
            group_targets = targets.index_select(0, selected)
            group_mask = mask.index_select(0, selected)
            if not torch.equal(group_targets, group_targets[0].expand_as(group_targets)) or not torch.equal(
                group_mask, group_mask[0].expand_as(group_mask)
            ):
                raise ValueError("windows in a validation group must share labels and masks")
            group_logits = window_logits.index_select(0, selected)
            if aggregation == "mean_probabilities":
                record_logits.append(torch.sigmoid(group_logits).mean(dim=0))
            else:
                record_logits.append(group_logits.mean(dim=0))
            record_targets.append(group_targets[0])
            record_masks.append(group_mask[0])
        predictions = torch.stack(record_logits)
        truth = torch.stack(record_targets)
        observed = torch.stack(record_masks).to(dtype=torch.bool)
        if aggregation == "mean_probabilities":
            losses = F.binary_cross_entropy(
                predictions.clamp(min=1e-7, max=1 - 1e-7), truth, reduction="none"
            )
            counts = observed.sum(dim=0)
            per_class = (losses * observed).sum(dim=0) / counts.clamp(min=1)
            present = counts > 0
            if not torch.any(present):
                raise ValueError("validation has no observed labels")
            return per_class[present].mean()
        return _mean_observed_class_loss(predictions, truth, observed)


def fit_classwise_binary_head(
    train_inputs: np.ndarray,
    train_targets: np.ndarray,
    train_mask: np.ndarray,
    train_element_weights: np.ndarray,
    validation_inputs: np.ndarray,
    validation_targets: np.ndarray,
    validation_mask: np.ndarray,
    *,
    loss_name: str = "weighted_bce",
    focal_gamma: float = 2.0,
    positive_weight_max: float = 10.0,
    validation_group_ids: Sequence[str] | None = None,
    validation_aggregation: str = "mean_logits",
    hidden_dim: int = 192,
    dropout: float = 0.25,
    learning_rate: float = 1e-3,
    batch_size: int = 256,
    max_epochs: int = 40,
    patience: int = 6,
    seed: int = 20261111,
    device: str = "cuda",
) -> tuple[ClassWiseBinaryMLP, dict[str, object]]:
    """Fit only a class-wise head, selecting an epoch using masked validation BCE."""
    if train_inputs.ndim != 2 or validation_inputs.ndim != 2:
        raise ValueError("features must be two-dimensional arrays")
    if train_inputs.shape[1] != validation_inputs.shape[1] or not train_inputs.shape[0]:
        raise ValueError("training and validation feature dimensions must match and train be nonempty")
    if train_targets.shape != train_mask.shape or train_targets.shape[0] != train_inputs.shape[0]:
        raise ValueError("training labels must be aligned with feature rows")
    if validation_targets.shape != validation_mask.shape or validation_targets.shape[0] != len(
        validation_inputs
    ):
        raise ValueError("validation labels must be aligned with feature rows")
    if train_targets.shape[1] != validation_targets.shape[1] or train_targets.shape[1] == 0:
        raise ValueError("training and validation class counts must match and be nonzero")
    if train_element_weights.shape != train_targets.shape:
        raise ValueError("training element weights must match the training label matrix")
    if loss_name not in {"weighted_bce", "source_balanced_bce", "focal"}:
        raise ValueError("unsupported loss_name")
    if not np.isfinite(focal_gamma) or focal_gamma < 0 or not np.isfinite(positive_weight_max):
        raise ValueError("focal gamma or positive-weight maximum is invalid")
    if validation_group_ids is not None and len(validation_group_ids) != len(validation_inputs):
        raise ValueError("validation group IDs must align with validation windows")
    if batch_size < 1 or max_epochs < 1 or patience < 1 or seed < 0:
        raise ValueError("batch size, epochs, patience, and seed must be valid")
    if not np.isfinite(train_inputs).all() or not np.isfinite(validation_inputs).all():
        raise ValueError("feature matrices must be finite")

    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.use_deterministic_algorithms(True)
    target_device = torch.device(device)
    model = ClassWiseBinaryMLP(
        int(train_inputs.shape[1]), int(train_targets.shape[1]),
        hidden_dim=hidden_dim, dropout=dropout,
    ).to(target_device)
    x_train = torch.as_tensor(train_inputs, dtype=torch.float32)
    y_train = torch.as_tensor(train_targets, dtype=torch.float32)
    m_train = torch.as_tensor(train_mask, dtype=torch.bool)
    w_train = torch.as_tensor(train_element_weights, dtype=torch.float32)
    if loss_name == "weighted_bce":
        pos_weight = classwise_positive_weights(
            y_train, m_train, w_train, maximum=positive_weight_max
        )
    else:
        pos_weight = torch.ones(train_targets.shape[1], dtype=torch.float32)
    focal_alpha = classwise_focal_alpha(y_train, m_train, w_train) if loss_name == "focal" else None
    generator = torch.Generator().manual_seed(seed)
    loader = DataLoader(
        TensorDataset(x_train, y_train, m_train, w_train),
        batch_size=batch_size,
        shuffle=True,
        generator=generator,
    )
    x_val = torch.as_tensor(validation_inputs, dtype=torch.float32, device=target_device)
    y_val = torch.as_tensor(validation_targets, dtype=torch.float32, device=target_device)
    m_val = torch.as_tensor(validation_mask, dtype=torch.bool, device=target_device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    best_state = None
    best_loss = float("inf")
    best_epoch = 0
    stale_epochs = 0
    history: list[dict[str, float | int]] = []

    for epoch in range(1, max_epochs + 1):
        model.train()
        total_loss, total_weight = 0.0, 0.0
        for batch_x, batch_y, batch_mask, batch_weight in loader:
            batch_x = batch_x.to(target_device)
            batch_y = batch_y.to(target_device)
            batch_mask = batch_mask.to(target_device)
            batch_weight = batch_weight.to(target_device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(batch_x)
            if loss_name == "focal":
                loss = masked_binary_focal_loss(
                    logits, batch_y, batch_mask, alpha_positive=focal_alpha,
                    gamma=focal_gamma,
                    element_weights=batch_weight,
                )
            else:
                loss = masked_binary_cross_entropy(
                    logits, batch_y, batch_mask, pos_weight=pos_weight,
                    element_weights=batch_weight,
                )
            loss.backward()
            optimizer.step()
            weight_sum = float((batch_weight * batch_mask).sum().detach())
            total_loss += float(loss.detach()) * weight_sum
            total_weight += weight_sum
        model.eval()
        validation_loss = float(_grouped_validation_loss(
            model, x_val, y_val, m_val, validation_group_ids, validation_aggregation
        ))
        train_loss = total_loss / total_weight if total_weight else float("nan")
        history.append({"epoch": epoch, "train_masked_loss": train_loss,
                        "validation_macro_bce": validation_loss})
        if validation_loss < best_loss - 1e-7:
            best_loss, best_epoch, stale_epochs = validation_loss, epoch, 0
            best_state = {name: value.detach().cpu().clone()
                          for name, value in model.state_dict().items()}
        else:
            stale_epochs += 1
            if stale_epochs >= patience:
                break

    if best_state is None:
        raise RuntimeError("training did not produce a finite validation checkpoint")
    model.load_state_dict(best_state, strict=True)
    model.to(target_device).eval()
    return model, {
        "best_epoch": best_epoch,
        "best_validation_macro_bce": best_loss,
        "epochs_run": len(history),
        "early_stopped": len(history) < max_epochs,
        "positive_weights": pos_weight.detach().cpu().tolist(),
        "focal_alpha_positive": None if focal_alpha is None else focal_alpha.detach().cpu().tolist(),
        "focal_gamma": focal_gamma if loss_name == "focal" else None,
        "positive_weight_max": positive_weight_max if loss_name == "weighted_bce" else None,
        "loss_name": loss_name,
        "history": history,
    }
