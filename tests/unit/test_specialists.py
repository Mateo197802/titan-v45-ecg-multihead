from __future__ import annotations

import torch

from titan_v45.models.specialists import ClassWiseBinaryMLP, parameter_count


def test_rhythm_specialist_matches_canonical_parameter_count() -> None:
    model = ClassWiseBinaryMLP(input_dim=681, output_dim=8, hidden_dim=512)
    assert parameter_count(model) == 4_909_720
    assert model(torch.zeros(2, 681)).shape == (2, 8)


def test_v3ag_pathology_specialist_matches_canonical_parameter_count() -> None:
    model = ClassWiseBinaryMLP(input_dim=670, output_dim=4, hidden_dim=512)
    assert parameter_count(model) == 2_432_244
    assert model(torch.zeros(2, 670)).shape == (2, 4)
