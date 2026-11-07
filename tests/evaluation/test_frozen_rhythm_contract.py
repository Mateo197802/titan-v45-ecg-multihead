from pathlib import Path

import numpy as np
import pytest
import torch

from titan_v45.data.reconstructed import historical_window_starts
from titan_v45.models.frozen_rhythm import (
    P6_CLASSES,
    P8_CLASSES,
    aggregate_rhythm,
    build_frozen_rhythm_head,
    load_recorded_event_extractor,
)
from titan_v45.models.specialists import ClassWiseBinaryMLP

ROOT = Path(__file__).resolve().parents[2]


def test_rhythm_keeps_distinct_saved_aggregations_and_fallback():
    logits = np.full((2, 8), -5.0)
    logits[:, 0] = (-5.0, 9.0)
    logits[:, 1] = (1.0, 1.0)
    p6 = aggregate_rhythm(logits, {c: 0.99 for c in P6_CLASSES}, profile="P6")
    p8 = aggregate_rhythm(logits, {c: 0.99 for c in P8_CLASSES}, profile="P8")
    assert p6["top1"] == "AFIB"
    assert p6["labels"] == [] and not p6["used_fallback"]
    assert p8["top1"] == "SB"
    assert p8["labels"] == ["SB"] and p8["used_fallback"]
    with pytest.raises(ValueError):
        aggregate_rhythm(np.zeros((1, 6)), {c: 0.5 for c in P6_CLASSES}, profile="P6")


def test_source_backed_window_counts():
    assert historical_window_starts(1000, 100) == (0,)
    assert historical_window_starts(1200, 100) == (0, 250)
    assert historical_window_starts(1500, 100) == (0, 625)
    assert historical_window_starts(1600, 100) == (0, 625, 750)


def test_extractor_uses_pinned_trainer_and_twelve_outputs(tmp_path):
    archive = ROOT / "docs/provenance/recovered-original-sources-20261029.zip"
    extractor = load_recorded_event_extractor(archive)
    features = extractor(torch.zeros((2, 12, 1250)))
    assert features.shape == (2, 12) and torch.isfinite(features).all()
    assert features[0, 0] > 0  # Preserve the recorded flat-input behavior.
    corrupted = tmp_path / "invalid.zip"
    corrupted.write_bytes(b"invalid")
    with pytest.raises(ValueError, match="archive"):
        load_recorded_event_extractor(corrupted)


def test_frozen_rhythm_width_is_read_from_tensors_not_stale_metadata():
    state = ClassWiseBinaryMLP(681, 8, hidden_dim=17).state_dict()
    head, dimensions = build_frozen_rhythm_head({"rhythm_hidden_dim": 9,
                                                "rhythm_specialist_state_dict": state})
    assert dimensions == {"declared": 9, "stored": 17, "metadata_matches": False}
    assert head(torch.zeros((2, 681))).shape == (2, 8)
    assert all(torch.equal(v, state[k]) for k, v in head.state_dict().items())
