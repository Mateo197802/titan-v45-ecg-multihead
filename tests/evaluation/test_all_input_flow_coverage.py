from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_coverage_report_matches_frozen_sph_and_selected_replay():
    report = (ROOT / "docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md").read_text(
        encoding="utf-8"
    )
    sph = load("outputs/results/external_sph/sph_aggregate_32669.json")
    rhythm = load("outputs/results/revision_20261107/rhythm_waveform.json")
    pathology = load("outputs/results/revision_20261107/pathology_waveform.json")

    flow = sph["full_population_flow"]
    assert flow["source_metadata_records"] == flow["scored_records"] == 25770
    assert flow["technical_exclusions"] == flow["inference_failures"] == 0
    assert flow["quarantine_assessed_records"] == 0
    assert len(sph["endpoints"]) == 14
    assert sph["profile_flow"]["P6"]["empty_label_set_records"] == 16785
    assert sph["profile_flow"]["P8"]["fallback_records"] == 801
    assert sph["profile_flow"]["P4"]["empty_label_set_records"] == 8343

    assert rhythm["profiles"]["P6"]["inputs"] == 1643
    assert rhythm["profiles"]["P8"]["inputs"] == 2193
    assert rhythm["profiles"]["P8"]["fallback_count"] == 58
    assert pathology["inputs"] == 733
    assert pathology["saved_comparison"]["compared_panel_pairs"] == 962
    for phrase in (
        "801",
        "16,785",
        "8,343",
        "not_assessed",
        "not adjudicated disease absence",
        "0.0006194115",
    ):
        assert phrase in report


def test_coverage_report_links_all_local_source_artifacts():
    path = ROOT / "docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md"
    report = path.read_text(encoding="utf-8")
    links = [
        token.split(")", 1)[0]
        for token in report.split("](")[1:]
        if not token.startswith("http")
    ]
    assert links
    for link in links:
        assert (path.parent / link).is_file(), link
