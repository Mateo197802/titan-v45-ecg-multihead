from __future__ import annotations

from collections.abc import Iterable

import torch


def _mean_epoch_loss(total_loss: float, examples: int) -> float:
    if examples == 0:
        raise ValueError("training loader produced no examples")
    return total_loss / examples


def train_binary_epoch(
    model: torch.nn.Module,
    loader: Iterable[tuple[torch.Tensor, torch.Tensor]],
    optimizer: torch.optim.Optimizer,
    *,
    device: str | torch.device,
    pos_weight: torch.Tensor | None = None,
) -> float:
    target_device = torch.device(device)
    model.train()
    total_loss = 0.0
    examples = 0
    criterion = torch.nn.BCEWithLogitsLoss(
        pos_weight=None if pos_weight is None else pos_weight.to(target_device)
    )
    for features, targets in loader:
        features = features.to(target_device).float()
        targets = targets.to(target_device).float()
        optimizer.zero_grad(set_to_none=True)
        loss = criterion(model(features), targets)
        loss.backward()
        optimizer.step()
        batch_size = int(features.shape[0])
        total_loss += float(loss.detach()) * batch_size
        examples += batch_size
    return _mean_epoch_loss(total_loss, examples)


def train_multiclass_epoch(
    model: torch.nn.Module,
    loader: Iterable[tuple[torch.Tensor, torch.Tensor]],
    optimizer: torch.optim.Optimizer,
    *,
    device: str | torch.device,
    class_weight: torch.Tensor | None = None,
) -> float:
    target_device = torch.device(device)
    model.train()
    total_loss = 0.0
    examples = 0
    criterion = torch.nn.CrossEntropyLoss(
        weight=None if class_weight is None else class_weight.to(target_device)
    )
    for features, targets in loader:
        features = features.to(target_device).float()
        targets = targets.to(target_device).long()
        optimizer.zero_grad(set_to_none=True)
        loss = criterion(model(features), targets)
        loss.backward()
        optimizer.step()
        batch_size = int(features.shape[0])
        total_loss += float(loss.detach()) * batch_size
        examples += batch_size
    return _mean_epoch_loss(total_loss, examples)
