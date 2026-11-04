import csv
import importlib.util
import json
from pathlib import Path

import pytest

from titan_v45.evaluation.workflow import route_record, summarize_routes
from titan_v45.uncertainty.quarantine import QuarantinePolicy

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/evaluation/audit_saved_workflow.py"
SPEC = importlib.util.spec_from_file_location("audit_saved_workflow", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_released_workflow_and_label_removal(tmp_path):
    expected, routes = MODULE.audit(ROOT)
    frozen = ROOT / "outputs/results/revision_20261029/saved_workflow_audit.json"
    assert json.loads(frozen.read_text(encoding="utf-8")) == expected
    assert expected["inputs"] == 2926
    assert expected["pre_counts"] == {"pathology_only": 733, "rhythm_only": 2193}
    assert expected["post_counts"] == {"quarantine_not_assessed": 2926}
    assert expected["quarantine_rate_all_inputs"] is None
    assert expected["p8_pre_top1_counts"]["NSR"] == 476
    assert expected["p8_empty_membership_fallbacks"] == 58
    assert expected["p4_scored_panel_pairs"] == 962
    assert expected["p4_records_with_all_four_scores"] == 5
    for relative in expected.pop("input_sha256_lf_normalized"):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix == ".json":
            data = json.loads(source.read_text(encoding="utf-8"))
            target.write_text(json.dumps({k: data[k] for k in ("classes", "thresholds")}))
            continue
        with source.open(encoding="utf-8", newline="") as src, target.open(
            "w", encoding="utf-8", newline=""
        ) as dst:
            reader = csv.DictReader(src)
            columns = [k for k in reader.fieldnames if k.startswith("membership_prob_")
                       or k in {"record_base", "pathology", "probability", "threshold"}]
            writer = csv.DictWriter(dst, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            for row in reader:
                # Compare saved outcomes here, not in the score-only router.
                decision = routes[row["record_base"]]
                if "membership_prob_NSR" in row:
                    assert decision["rhythm"]["top1"] == row["predicted_label"]
                    assert set(decision["rhythm"]["labels"]) == set(row["predicted_labels"].split("|"))
                if "probability" in row:
                    assert decision["pathology"][row["pathology"]] == bool(int(row["predicted"]))
                writer.writerow(row)
    stripped, stripped_routes = MODULE.audit(tmp_path)
    stripped.pop("input_sha256_lf_normalized")
    assert stripped == expected and stripped_routes == routes


def test_pre_post_denominators_keep_unknown_and_missing_separate():
    policy = QuarantinePolicy(0.5, 0.8, 0.2)
    scores, thresholds = {"NSR": 0.7}, {"NSR": 0.5}
    routed = {
        "unknown": route_record(scores, thresholds, {}),
        "missing": route_record({}, thresholds, {}),
        "retained": route_record(scores, thresholds, {}, uncertainty=(0.5, 0.8, 0.2), policy=policy),
        "quarantined": route_record({}, thresholds, {"LVH": (0.2, 0.5)},
                                    uncertainty=(0.4, 0.9, 0.1), policy=policy),
    }
    summary = summarize_routes(routed)
    assert summary["quarantine_assessed"] == 2
    assert summary["quarantine_rate_among_assessed"] == 0.5
    assert summary["quarantine_rate_all_inputs"] is None
    assert routed["quarantined"]["quarantine_reasons"] == ("low_confidence", "high_entropy")
    assert routed["missing"]["post"] == "no_scores"
    assert "ASMI" not in routed["quarantined"]["pathology"]
    with pytest.raises(ValueError, match="explicit policy"):
        route_record(scores, thresholds, {}, uncertainty=(0.1, 0.1, 0.1))
    with pytest.raises(ValueError, match="invalid uncertainty"):
        route_record(scores, thresholds, {}, uncertainty=(0.5, float("nan"), 0.1), policy=policy)
