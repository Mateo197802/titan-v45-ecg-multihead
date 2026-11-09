from __future__ import annotations

import csv
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
    for endpoint, values in sph["endpoints"].items():
        metrics = values["metrics"]
        table_row = (
            f"| {endpoint} | {metrics['positive_support']:,} / "
            f"{metrics['negative_support']:,} | "
            f"{100 * metrics['precision']:.2f}% | "
            f"{100 * metrics['f1']:.2f}% | "
            f"{100 * metrics['auroc']:.2f}% |"
        )
        assert table_row in report, endpoint

    assert rhythm["profiles"]["P6"]["inputs"] == 1643
    assert rhythm["profiles"]["P8"]["inputs"] == 2193
    assert rhythm["profiles"]["P8"]["fallback_count"] == 58
    assert pathology["inputs"] == 733
    assert pathology["saved_comparison"]["compared_panel_pairs"] == 962

    def record_ids(relative_path):
        with (ROOT / relative_path).open(encoding="utf-8", newline="") as stream:
            return {row["record_id"] for row in csv.DictReader(stream)}

    p8 = record_ids("data/manifests/external_dev/rhythm_primary8_records.csv")
    p6 = record_ids("data/manifests/external_dev/rhythm_primary6_diagnostic_records.csv")
    with (ROOT / "data/manifests/external_dev/pathology_primary4_panels.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        p4_rows = list(csv.DictReader(stream))
    p4 = {row["record_id"] for row in p4_rows}
    assert len(p8) == 2193
    assert len(p6) == 1643 and p6 <= p8
    assert len(p4_rows) == 962 and len(p4) == 733
    assert not (p8 & p4)
    assert len(p8 | p4) == 2926
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
