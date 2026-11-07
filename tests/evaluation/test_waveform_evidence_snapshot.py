import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "outputs/results/revision_20261107"


def _read(name):
    return json.loads((EVIDENCE / name).read_bytes())


def test_native_aggregate_hashes_and_boundaries_match_receipt():
    outputs = _read("execution.json")["outputs"]
    assert {item["job"] for item in outputs.values()} == {32448, 32461, 32464}
    for name, item in outputs.items():
        assert hashlib.sha256((EVIDENCE / name).read_bytes()).hexdigest() == item["sha256"]
        assert (item["state"], item["exit_code"]) == ("COMPLETED", "0:0")
    release = {row["name"]: row["sha256"] for row in json.loads(
        (ROOT / "release-manifest.json").read_bytes()
    )["assets"]}
    for name in ("pathology_waveform.json", "rhythm_waveform.json"):
        report = _read(name)
        assert all(release[asset] == sha for asset, sha in report["release_sha256"].items())
        assert report["weights_or_thresholds_modified"] is False
        assert report["historical_preprocessing_certified"] is False
        assert report["reference_labels_used_for_routing"] is False
        assert report["independent_external_evaluation"] is False


def test_native_aggregate_denominators_and_matched_reference_consistency():
    p4, rhythm, metrics = map(_read, (
        "pathology_waveform.json", "rhythm_waveform.json", "matched_reference_metrics.json",
    ))
    assert p4["all_four_p4_scores_records"] == 733
    pairs = p4["saved_comparison"]
    assert (pairs["compared_panel_pairs"], pairs["decision_disagreements"]) == (962, 0)
    assert pairs["max_absolute_probability_difference"] > pairs["historical_atol"]
    assert pairs["meets_historical_tolerance_on_all_panel_pairs"] is False
    assert rhythm["codetest_archive_alias_records"] == 167
    for name, size in (("P6", 1643), ("P8", 2193)):
        profile = rhythm["profiles"][name]
        assert profile["inputs"] == profile["scored_records"] == metrics[name]["matched_ecgs"] == size
        assert profile["binary_set_disagreements"] == 0
        assert profile["quarantine_rate"] is None
    assert rhythm["profiles"]["P6"]["top1_disagreements"] == 1
    assert rhythm["profiles"]["P8"]["top1_disagreements"] == 0
    assert rhythm["profiles"]["P8"]["fallback_count"] == 58
    assert metrics["P6"]["accepted_top1_correct"] == {"new": 1563, "archived_matched": 1564}
    union = metrics["selected_key_union"]
    assert union["inputs"] == 2926 and union["exact_key_overlap"] == 0
    assert union["quarantine_assessed"] == 0 and union["quarantine_rate_all_inputs"] is None
    assert union["historical_parent_population_recovered"] is False
    assert metrics["manifest_sha256_lf"] == {
        "pathology_primary4_panels.csv": p4["manifest_sha256_lf"], **rhythm["manifest_sha256_lf"],
    }
