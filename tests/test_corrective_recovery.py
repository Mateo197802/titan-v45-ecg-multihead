"""Test hard-example isolation and matched endpoint uncertainty."""
import sys
from pathlib import Path

import numpy as np
import torch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts" / "domain_adaptation"
sys.path.insert(0, str(SCRIPTS))
try:
    from corrective_evaluate import compare
    from corrective_fit import masks
finally:
    sys.path.remove(str(SCRIPTS))


def test_hard_examples_ignore_unlabeled_and_protected_outputs():
    y = torch.tensor([[1., 0., 1., 0., -1.], [0., 1., 0., 1., 1.]])
    p = torch.tensor([[.2, .9, .2, .9, .9], [.2, .8, .9, .2, .3]])
    hard, known = masks(y, p, {"hard_positive_probability_max": .45, "hard_negative_probability_min": .4})
    assert hard.tolist() == [[True, True, False, False, False], [False, False, False, False, True]]
    assert known.tolist() == [[True, True, True, True, False], [True, True, True, True, True]]


def test_small_support_prevents_fixed_denominator_macro_interval():
    y = np.tile(np.array([[0, -1, -1, 0, 0], [1, -1, -1, 1, 0]]), (10, 1))
    y[0, 4] = 1
    p = np.where(y == 1, .95, .01)
    data = {"labels": y, "p": p, "patients": np.arange(len(y))}
    policy = {"cuts": [.5] * 5, "maps": [{"kind": "identity"}] * 5}
    boot = {"replicates": 5, "seed": 12, "support_min_positive_and_negative_groups": 3}
    points, intervals = compare("cpsc", data, p, policy, boot, ["AFIB", "SB", "STACH", "RBBB", "1AVB"])
    assert {r["endpoint"] for r in points} == {"AFIB", "RBBB", "1AVB"}
    assert all(r["resampling_unit"] == "ecg_only" for r in intervals)
    assert all(r["ci_low"] is None for r in intervals if r["endpoint"] in {"macro", "1AVB"})
    afib = next(r for r in intervals if (r["endpoint"], r["arm"], r["metric"]) == ("AFIB", "C-A", "f1"))
    assert afib["ci_low"] == afib["ci_high"] == 0.
