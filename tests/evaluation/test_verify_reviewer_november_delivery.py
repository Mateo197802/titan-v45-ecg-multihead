import importlib
import json
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts" / "evaluation"


@pytest.fixture
def delivery(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    return importlib.import_module("verify_reviewer_november_delivery")


def test_wait_never_invents_results_and_native_failures_remain_visible(delivery, tmp_path):
    states = delivery.accounting("33355|PENDING|0:0|00:00:00|\n33373|PENDING|0:0|00:00:00|\n"
                                 "33365|FAILED|1:0|00:00:01|\n")
    report = delivery.verify({"phase": tmp_path, "history": tmp_path}, states)
    assert report["verified_jobs"] == 0
    assert report["jobs"]["33365"]["scheduler"]["exit_code"] == "1:0"
    assert report["superseded_jobs_not_used"]["33373"]["state"] == "PENDING"


def test_native_completion_requires_valid_public_sealed_bytes(delivery, tmp_path):
    out = tmp_path / "sph-frozen-33355"
    out.mkdir()
    p = out / "scoring-receipt.json"
    ledger = out / "private-predictions.jsonl"
    ledger.write_text("synthetic")
    result = {"stage": "full_population", "job_id": 33355, "labels_used_for_inference_or_routing": False,
              "ledger_sha256": delivery.digest(ledger),
              "flow": {"metadata_records": 25770, "scored_records": 25768,
                       "status_counts": {"scored": 25768, "missing_signal": 2}}}
    p.write_text(json.dumps(result))
    seal = out / "SHA256SUMS"
    seal.write_text(f"{delivery.digest(p)}  {p}\n")
    states = delivery.accounting("33355|COMPLETED|0:0|00:01:00|\n")
    roots = {"phase": tmp_path, "history": tmp_path}
    assert delivery.verify(roots, states)["verified_jobs"] == 1
    p.write_text(json.dumps({**result, "new_field": 1}))
    assert delivery.verify(roots, states)["verified_jobs"] == 0
    p.write_text(json.dumps({**result, "patient_id": "fake"}))
    seal.write_text(f"{delivery.digest(p)}  scoring-receipt.json\n")
    assert delivery.verify(roots, states)["verified_jobs"] == 0


def test_selective_arithmetic_checks_both_denominators_and_confusion(delivery):
    stats = {"held_records": 5, "scored_records": 4, "accepted": 3, "abstained": 1,
             "technical_unscored": 1, "abstention_all_held": 0.2, "abstention_scored": 0.25,
             "coverage_all_held": 0.6, "coverage_scored": 0.75,
             "endpoints": {"A": {"routes": {
                 "baseline": {"n": 4, "tp": 1, "tn": 2, "fp": 0, "fn": 1},
                 "accepted": {"n": 3, "tp": 1, "tn": 2, "fp": 0, "fn": 0},
                 "abstained": {"n": 1, "tp": 0, "tn": 0, "fp": 0, "fn": 1},
             }}}}
    delivery.check_selective(stats)
    stats["coverage_all_held"] = 0.75
    with pytest.raises(ValueError, match="denominator"):
        delivery.check_selective(stats)
