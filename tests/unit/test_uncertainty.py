from __future__ import annotations

import numpy as np
import torch

from titan_v45.uncertainty.mc_dropout import mc_dropout_predict
from titan_v45.uncertainty.quarantine import QuarantinePolicy, quarantine_decision


class DropoutClassifier(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.dropout = torch.nn.Dropout(p=0.5)
        self.linear = torch.nn.Linear(4, 3)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(self.dropout(x))


def test_mc_dropout_returns_finite_predictive_uncertainty() -> None:
    torch.manual_seed(197802)
    result = mc_dropout_predict(DropoutClassifier(), torch.ones(2, 4), passes=12)

    assert result.mean_probability.shape == (2, 3)
    assert result.sample_probabilities.shape == (12, 2, 3)
    assert np.isfinite(result.predictive_entropy).all()
    assert np.isfinite(result.mutual_information).all()
    assert (result.mutual_information >= -1e-8).all()
    assert np.std(result.sample_probabilities, axis=0).max() > 0


def test_quarantine_policy_abstains_on_high_uncertainty() -> None:
    decision = quarantine_decision(
        max_probability=0.55,
        predictive_entropy=0.80,
        mutual_information=0.20,
        policy=QuarantinePolicy(
            min_confidence=0.70,
            max_predictive_entropy=0.65,
            max_mutual_information=0.10,
        ),
    )
    assert decision.quarantined is True
    assert set(decision.reasons) == {"low_confidence", "high_entropy", "high_mutual_information"}
