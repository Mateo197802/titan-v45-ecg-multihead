import importlib
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts" / "evaluation"


@pytest.fixture
def bridge(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    return importlib.import_module("reviewer_ptbxl_reference_bridge")


def test_enrollment_excludes_fold10_before_path_access_and_ignores_label(bridge, tmp_path):
    file = tmp_path / "meta.csv"
    file.write_text("strat_fold,filename_lr,scp_codes\n"
                    "1,records100/00000/00001_lr,not decoded\n"
                    "9,records100/01000/01002_lr,not decoded\n"
                    "10,forbidden,not decoded\n")
    cohort = bridge.enrollment(file, 2)
    assert list(cohort.values()) == [("records100/00000/00001_lr", 1), ("records100/01000/01002_lr", 9)]
    k = next(iter(cohort))
    original = {"task": "pathology", "source": "ptbxl", "fold": 1, "relative_record": cohort[k][0], "identity_hash": k}
    assert bridge.inventory_rows({"rows": [original]}, cohort) == {k: original}
    with pytest.raises(ValueError, match="forbidden"):
        bridge.inventory_rows({"rows": [{**original, "fold": 10}]}, cohort)


def test_missing_and_unknown_likelihood_kept_out_of_metrics(bridge):
    refs = {"a": {"ISC_": 42}, "b": {"NORM": 100, "SR": 0}, "c": {"ISC_": 0},
            "d": {"ALMI": 100}, "e": {"ISC_": 55}}

    def scored(p):
        return {"P4": {"status": "scored", "scores": {"ISC_": p}, "labels": ["ISC_"] if p > 0.5 else []}}

    rows = dict(zip(refs, [scored(0.8), scored(0.1), scored(0.9), scored(0.8),
                           {"P4": {"status": "not_in_authorized_preflight"}}], strict=True))

    def metric(y, calls, probs):
        assert y == calls == [1, 0]
        assert probs == [0.8, 0.1]
        return {"tn": 1, "fn": 0}

    result = bridge.observe_endpoint(
        rows, refs, dict(zip(refs, refs, strict=True)), "P4", "ISC_", "ISC_", False,
        {"seed": 10, "replicates": 10, "confidence": 0.95}, metric,
        lambda *a, **k: {}, None, 0.5)
    assert result["known_scored"] == 2
    assert result["reference_and_scoring_flow"] == {"positive:scored": 1, "control:scored": 1,
                                                    "ambiguous:scored": 1, "unknown:scored": 1,
                                                    "positive:not_in_authorized_preflight": 1}
