import hashlib
import json

import pytest

from scripts.external_validation.validate_sph_receipts import validate_receipts


def test_receipt_chain_detects_aggregate_tampering(tmp_path):
    def write(name, value):
        path = tmp_path / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    wrapper = tmp_path / "wrapper.py"
    wrapper.write_text("# synthetic", encoding="utf-8")
    source, models, commit, ledger = {"metadata.csv": "a"}, {"model": "b"}, "c" * 40, "d" * 64
    config = write("config.json", {"source_sha256": source, "model_sha256": models,
                                   "expected_source_records": 4,
                                   "implementation_sha256": {"scripts/external_validation/evaluate_sph_ledger.py": "e"}})
    score = write("score.json", {"protocol_sha256": sha(config), "protocol_commit": commit,
                                  "source_sha256": source, "model_sha256": models,
                                  "labels_used_for_inference_or_routing": False,
                                  "flow": {"metadata_records": 4}, "ledger_sha256": ledger, "job_id": "1"})
    aggregate = write("aggregate.json", {"protocol_sha256": sha(config), "protocol_commit": commit,
                                          "scoring_receipt_sha256": sha(score), "scoring_ledger_sha256": ledger})
    aggregation = write("aggregation.json", {"protocol_sha256": sha(config), "commit": commit,
                        "inputs": {"scoring_receipt_sha256": sha(score), "ledger_sha256": ledger},
                        "aggregate_sha256": sha(aggregate), "job_id": "2"})
    correction = write("correction.json", {"aggregate_sha256": sha(aggregate),
                       "frozen_evaluator_receipt_sha256": sha(aggregation), "wrapper_sha256": sha(wrapper),
                       "frozen_evaluator_sha256": "e", "other_bootstrap_metrics_modified": False})
    paths = (config, score, aggregate, aggregation, correction, wrapper)
    assert validate_receipts(*paths)["checks_passed"] == 19
    aggregate.write_text("{}", encoding="utf-8")
    with pytest.raises((ValueError, KeyError)):
        validate_receipts(*paths)
