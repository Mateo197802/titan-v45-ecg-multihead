from __future__ import annotations

import torch

from titan_v45.models.features import SpecialistFeatureLayout, compose_specialist_features


def test_specialist_feature_composition_has_explicit_stable_layout() -> None:
    layout = SpecialistFeatureLayout(
        rhythm_indices=(0, 2),
        specialist_rhythm_indices=(1,),
        pathology_indices=(0, 1),
        include_morphology=True,
        signal_event_feature_dim=2,
    )
    features = compose_specialist_features(
        backbone_features=torch.ones(3, 4),
        rhythm_probabilities=torch.arange(9, dtype=torch.float32).reshape(3, 3),
        pathology_probabilities=torch.ones(3, 2) * 2,
        layout=layout,
        morphology=torch.ones(3, 1) * 3,
        signal_event_features=torch.ones(3, 2) * 4,
    )
    assert features.shape == (3, 12)
    assert torch.isfinite(features).all()
    assert torch.all(features[:, -2:] == 4)
