import importlib.util
import sys
from pathlib import Path

import pytest

scripts = Path(__file__).resolve().parents[2] / "scripts/evaluation"
sys.path.insert(0, str(scripts))
try:
    spec = importlib.util.spec_from_file_location(
        "freeze_policy", scripts / "freeze_reviewer_selective_policy.py",
    )
    policy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(policy)
finally:
    sys.path.remove(str(scripts))


def test_exact_signal_links_patients_transitively():
    rows = [dict(record_id=k, patient_id=p, signal_sha256_canonical_f64=h)
            for k, p, h in (("1", "p1", "a"), ("2", "p2", "a"),
                            ("3", "p2", "b"), ("4", "p3", "b"))]
    assert len(set(policy.components(rows).values())) == 1


def test_cutoff_ties_and_contract():
    assert policy.cutoff(list(range(10)), .9) == 1
    assert policy.cutoff([0, 0, 1, 2], .75) == 0
    assert policy.confidence({"a": .75, "b": .51}, {"a": .5, "b": .5}) == pytest.approx(.01)
    with pytest.raises(ValueError, match="contracts"):
        policy.confidence({"a": .75}, {"b": .5})


def test_held_rows_do_not_need_score_or_reference_fields():
    recipe = {"split_seed": "demo", "calibration_fraction": .5, "target_scored_coverage": .9}
    ids = [str(i) for i in range(40)]
    groups = {k: k for k in ids}
    rows = [
        {"record_id": k, "status": "scored", "profiles": {
            p: {"scores": {"a": .8}} for p in policy.PROFILES
        }} if policy.calibration_member(k, "demo", .5) else {"record_id": k}
        for k in ids
    ]
    result = policy.freeze(rows, groups, {p: {"a": .5} for p in policy.PROFILES}, recipe)
    assert result["counts"]["held_records"] > 0
    assert result["shared_components"] == 0 and not result["reference_labels_used"]
