import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_observed_baseline_diagnostic_is_aggregate_and_reconciles():
    path = ROOT / "outputs/results/benchmarkmax/sph_baseline_diagnostic_32726.json"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        "248b4857cbd4a92ad42bc96d78dab9f6431a0d572f9325684b520c31e27670c6"
    )
    text = path.read_text(encoding="utf-8")
    result = json.loads(text)
    assert result["source_records"] == 25770 and result["source_patients"] == 24666
    assert result["individual_records_exported"] is False
    assert not re.search(r'"A[0-9]{5}"|"(?:record_id|patient_id|ecg_id)"|/home/', text)
    assert set(result["endpoints"]) == {"P6:AFIB", "P8:PAC", "P4:ASMI", "P4:LVH", "P4:IMI"}
    for endpoint in result["endpoints"].values():
        bins = endpoint["score_bins_uniform_20"]
        counts = endpoint["frozen_decisions"]
        assert len(bins) == 20
        assert sum(item["positive"] for item in bins) == counts["tp"] + counts["fn"]
        assert sum(item["negative"] for item in bins) == counts["tn"] + counts["fp"]
        assert sum(counts.values()) == endpoint["records"] == 25770
        assert endpoint["statement_prevalence"] == endpoint["positive_statements"] / endpoint["records"]
        assert endpoint["average_precision_no_skill_baseline"] == endpoint["statement_prevalence"]
        assert len(endpoint["exploratory_binned_threshold_curve"]) == 20


def test_diagnostic_table_values_are_derived_from_the_aggregate():
    path = ROOT / "outputs/results/benchmarkmax/sph_baseline_diagnostic_32726.json"
    result = json.loads(path.read_text(encoding="utf-8"))
    document = (ROOT / "docs/benchmarkmax/OBSERVED_SPH_BASELINE.md").read_text(encoding="utf-8")
    for name, endpoint in result["endpoints"].items():
        counts = endpoint["frozen_decisions"]
        ppv = counts["tp"] / (counts["tp"] + counts["fp"])
        row = (f"| {name.replace(':', ' ')} | {endpoint['statement_prevalence']:.2%} | "
               f"{counts['tp']:,} | {counts['fp']:,} | {counts['fn']:,} | {ppv:.2%} | "
               f"{endpoint['frozen_auroc']:.4f} | {endpoint['frozen_average_precision']:.4f} | "
               f"{endpoint['frozen_brier']:.4f} | {endpoint['frozen_ece']:.4f} |")
        assert row in document
