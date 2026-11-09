from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from titan_v45.cascade.policy import CASCADE_PATHOLOGIES, CASCADE_RHYTHMS
from titan_v45.models.frozen_rhythm import P6_CLASSES, P8_CLASSES, aggregate_rhythm

ROOT = Path(__file__).resolve().parents[2]


def test_no_threshold_crossed_differs_between_profiles():
    logits = np.full((1, 8), -10.0)
    p6 = aggregate_rhythm(logits, dict.fromkeys(P6_CLASSES, 0.9), profile="P6")
    p8 = aggregate_rhythm(logits, dict.fromkeys(P8_CLASSES, 0.9), profile="P8")
    assert p6["labels"] == []
    assert p6["top1"] in P6_CLASSES
    assert p6["used_fallback"] is False
    assert p8["labels"] == [p8["top1"]]
    assert p8["used_fallback"] is True


def test_contract_and_selected_replay_remain_separate():
    contract = json.loads((ROOT / "outputs/models/heads/global_head_contracts.json").read_text())
    assert tuple(contract["heads"]["rhythm"]["classes"]) == P8_CLASSES + CASCADE_RHYTHMS
    assert tuple(contract["heads"]["pathology"]["classes"][-3:]) == CASCADE_PATHOLOGIES
    assert {"NSR", "PAC"}.issubset(P8_CLASSES)
    assert not {"NSR", "PAC"}.intersection(P6_CLASSES)
    rhythm = json.loads((ROOT / "outputs/results/revision_20261107/rhythm_waveform.json").read_text())
    pathology = json.loads((ROOT / "outputs/results/revision_20261107/pathology_waveform.json").read_text())
    assert rhythm["profiles"]["P8"]["fallback_count"] == 58
    assert rhythm["profiles"]["P8"]["top1_counts"]["NSR"] == 476
    assert rhythm["auxiliary_action"] == pathology["auxiliary_action"] == "no_frozen_policy"
    assert rhythm["profiles"]["P8"]["quarantine_rate"] is None
    assert pathology["quarantine_rate_all_inputs"] is None
