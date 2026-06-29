from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch


@dataclass(frozen=True)
class MCDropoutResult:
    mean_probability: np.ndarray
    sample_probabilities: np.ndarray
    predictive_entropy: np.ndarray
    mutual_information: np.ndarray


def _entropy(probabilities: np.ndarray) -> np.ndarray:
    clipped = np.clip(probabilities, 1e-12, 1.0)
    return -(clipped * np.log(clipped)).sum(axis=-1)


def mc_dropout_predict(
    model: torch.nn.Module, inputs: torch.Tensor, *, passes: int = 25
) -> MCDropoutResult:
    if passes < 2:
        raise ValueError("MC Dropout requires at least two stochastic passes")
    was_training = model.training
    model.eval()
    for module in model.modules():
        if isinstance(module, torch.nn.modules.dropout._DropoutNd):
            module.train()
    samples: list[np.ndarray] = []
    with torch.no_grad():
        for _ in range(passes):
            probabilities = torch.softmax(model(inputs), dim=-1)
            samples.append(probabilities.detach().cpu().numpy())
    model.train(was_training)
    stacked = np.stack(samples, axis=0)
    mean_probability = stacked.mean(axis=0)
    predictive_entropy = _entropy(mean_probability)
    expected_entropy = _entropy(stacked).mean(axis=0)
    return MCDropoutResult(
        mean_probability=mean_probability,
        sample_probabilities=stacked,
        predictive_entropy=predictive_entropy,
        mutual_information=np.maximum(predictive_entropy - expected_entropy, 0.0),
    )
