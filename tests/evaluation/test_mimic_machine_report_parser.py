from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path

import pytest

MODULE = "titan_v45.benchmarkmax.mimic_reports"
TEMPLATE = Path(__file__).resolve().parents[2] / "configs/benchmarkmax/mimic_pac_report_mapping.template.json"


def _api():
    assert importlib.util.find_spec(MODULE) is not None, "MIMIC PAC report parser is not implemented"
    return importlib.import_module(MODULE)


def approved_mapping() -> dict[str, object]:
    return {
        "schema": "TITAN_V46_MIMIC_PAC_REPORT_MAPPING_V1",
        "mapping_id": "synthetic-unit-test-only",
        "status": "approved_by_corresponding_author",
        "approval": {"approved_by": "Synthetic test fixture", "approved_on": "2026-11-09"},
        "phrases": {
            "explicit_positive": ["PAC", "PACs", "atrial premature complex"],
            "explicit_negative": ["no PAC", "no PACs", "without PACs"],
            "uncertain_or_qualified": ["possible PAC", "cannot exclude PAC"],
        },
    }


def write_mapping(tmp_path: Path, mapping: dict[str, object]) -> Path:
    path = tmp_path / "mapping.json"
    path.write_text(json.dumps(mapping), encoding="utf-8")
    return path


def test_template_is_not_loadable_as_an_approved_mapping() -> None:
    api = _api()

    with pytest.raises(ValueError, match="author approval"):
        api.load_approved_pac_mapping(TEMPLATE)


def test_approved_mapping_cannot_be_constructed_without_the_validating_loader() -> None:
    api = _api()

    with pytest.raises(ValueError, match="load_approved_pac_mapping"):
        api.ApprovedPACPhraseMapping(
            mapping_id="unapproved",
            explicit_positive=(("pac",),),
            explicit_negative=(),
            uncertain_or_qualified=(("possible", "pac"),),
        )


def test_report_slots_preserve_blank_columns_and_require_all_18_fields() -> None:
    api = _api()
    row = {f"report_{index}": "" for index in range(18)}
    row["report_0"] = "First line"
    row["report_2"] = "Third line"

    lines = api.report_lines_from_row(row)

    assert len(lines) == 18
    assert lines[0] == "First line"
    assert lines[1] == ""
    assert lines[2] == "Third line"
    del row["report_17"]
    with pytest.raises(ValueError, match="report_0..report_17"):
        api.report_lines_from_row(row)


def test_matcher_distinguishes_explicit_states_and_never_infers_negative_from_silence(
    tmp_path: Path,
) -> None:
    api = _api()
    mapping = api.load_approved_pac_mapping(write_mapping(tmp_path, approved_mapping()))

    assert api.classify_report_lines(["ＰＡＣ."], mapping) == "explicit_positive"
    assert api.classify_report_lines(["No PAC"], mapping) == "explicit_negative"
    assert api.classify_report_lines(["Possible PAC"], mapping) == "uncertain_or_qualified"
    assert api.classify_report_lines(["Normal sinus rhythm"], mapping) == (
        "not_mentioned_or_report_missing"
    )
    assert api.classify_report_lines([None, ""], mapping) == "not_mentioned_or_report_missing"


def test_specific_negation_and_qualifier_override_their_positive_subphrase(
    tmp_path: Path,
) -> None:
    api = _api()
    mapping = api.load_approved_pac_mapping(write_mapping(tmp_path, approved_mapping()))

    assert api.classify_report_lines(["No PACs detected"], mapping) == "explicit_negative"
    assert api.classify_report_lines(["Cannot exclude PAC"], mapping) == (
        "uncertain_or_qualified"
    )


def test_conflicting_report_lines_are_uncertain_not_positive_or_negative(
    tmp_path: Path,
) -> None:
    api = _api()
    mapping = api.load_approved_pac_mapping(write_mapping(tmp_path, approved_mapping()))

    assert api.classify_report_lines(["PAC", "No PAC"], mapping) == (
        "uncertain_or_qualified"
    )


def test_measurement_row_returns_only_the_report_state(tmp_path: Path) -> None:
    api = _api()
    mapping = api.load_approved_pac_mapping(write_mapping(tmp_path, approved_mapping()))
    row: dict[str, object] = {f"report_{index}": "" for index in range(18)}
    row.update({"subject_id": "private-subject", "study_id": "private-study"})
    row["report_1"] = "PAC"

    result = api.classify_measurement_row(row, mapping)

    assert result == "explicit_positive"
    assert isinstance(result, str)


def test_duplicate_phrase_across_classes_is_rejected(tmp_path: Path) -> None:
    api = _api()
    data = approved_mapping()
    data["phrases"]["explicit_negative"] = ["PAC"]

    with pytest.raises(ValueError, match="multiple classes"):
        api.load_approved_pac_mapping(write_mapping(tmp_path, data))


def test_mapping_approval_date_requires_exact_iso_calendar_format(tmp_path: Path) -> None:
    api = _api()
    data = approved_mapping()
    data["approval"]["approved_on"] = "20261109"

    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        api.load_approved_pac_mapping(write_mapping(tmp_path, data))
