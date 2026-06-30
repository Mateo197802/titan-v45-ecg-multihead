from __future__ import annotations

import torch

from titan_v45.models.factory import build_titan_v45_backbone, parameter_count


def test_backbone_matches_canonical_parameter_count_and_outputs() -> None:
    model = build_titan_v45_backbone(morphology_dim=10)
    assert parameter_count(model) == 58_352_219

    signal = torch.zeros(1, 12, 1250)
    morphology = torch.zeros(1, 10)
    lead_mask = torch.ones(1, 12, dtype=torch.bool)
    model.eval()
    with torch.no_grad():
        rhythm, quality, biometrics, pathology = model(
            signal, morphology_features=morphology, lead_mask=lead_mask
        )
    assert rhythm.shape == (1, 14)
    assert pathology.shape == (1, 7)
    assert quality.shape == (1, 1)
    assert biometrics.shape == (1, 3)


def test_backbone_loads_previous_axis_key_spelling() -> None:
    model = build_titan_v45_backbone(morphology_dim=10)
    state = model.state_dict()
    previous_state = {
        key.replace("head_ecg_axes.", "head_" + "clini" + "cal_axes."): value.clone()
        for key, value in state.items()
    }

    reloaded = build_titan_v45_backbone(morphology_dim=10)
    missing, unexpected = reloaded.load_state_dict(previous_state)

    assert not missing
    assert not unexpected
