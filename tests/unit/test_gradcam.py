from __future__ import annotations

import numpy as np
import torch

from titan_v45.explainability.gradcam import gradcam_1d


class TinyEcgModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.conv = torch.nn.Conv1d(12, 8, kernel_size=3, padding=1)
        self.relu = torch.nn.ReLU()
        self.pool = torch.nn.AdaptiveAvgPool1d(1)
        self.head = torch.nn.Linear(8, 4)

    def forward(self, signal: torch.Tensor) -> torch.Tensor:
        features = self.relu(self.conv(signal))
        return self.head(self.pool(features).squeeze(-1))


def test_gradcam_returns_time_and_lead_attribution() -> None:
    torch.manual_seed(197802)
    signal = torch.randn(1, 12, 125)
    result = gradcam_1d(TinyEcgModel(), signal, target_index=2, target_layer="conv")

    assert result.time_attribution.shape == (125,)
    assert result.lead_attribution.shape == (12,)
    assert np.isfinite(result.time_attribution).all()
    assert np.isfinite(result.lead_attribution).all()
    assert (result.time_attribution >= 0).all()
