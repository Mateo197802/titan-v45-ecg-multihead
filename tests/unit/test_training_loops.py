from __future__ import annotations

import torch

from titan_v45.training.loops import train_binary_epoch, train_multiclass_epoch


def test_binary_training_epoch_updates_parameters_and_returns_finite_loss() -> None:
    model = torch.nn.Linear(3, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    features = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    targets = torch.tensor([[1.0, 0.0], [0.0, 1.0]])
    before = model.weight.detach().clone()
    loss = train_binary_epoch(model, [(features, targets)], optimizer, device="cpu")
    assert loss >= 0.0
    assert torch.isfinite(torch.tensor(loss))
    assert not torch.equal(before, model.weight.detach())


def test_multiclass_training_epoch_is_finite() -> None:
    model = torch.nn.Linear(2, 2)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss = train_multiclass_epoch(
        model,
        [(torch.eye(2), torch.tensor([0, 1]))],
        optimizer,
        device="cpu",
    )
    assert torch.isfinite(torch.tensor(loss))
