import importlib
from pathlib import Path

import pytest


@pytest.fixture
def audit(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts/evaluation"))
    return importlib.import_module("audit_reviewer_ptbxl_other_support")


@pytest.mark.parametrize(("endpoint", "codes", "marker", "expected"), [
    ("Paced", {"PACE": 0}, "pacemaker", "concordant_marker_unknown_scp_likelihood"),
    ("Paced", {"PACE": 100}, "pacemaker", "positive"),
    ("Paced", {"PACE": 100}, "", "ambiguous_pacing_reference"),
    ("Paced", {"NORM": 100}, "pacemaker", "ambiguous_pacing_reference"),
    ("Paced", {"NORM": 100, "SR": 0}, "", "explicit_normal_control"),
    ("LQTS", {"LNGQT": 100}, "", "non_equivalent_proxy"),
    ("LAE", {"LAO/LAE": 100}, "", "non_equivalent_proxy"),
    ("NSR", {"SR": 0}, "", "non_equivalent_proxy"),
    ("3AVB", {"NORM": 100}, "", "explicit_normal_control"),
    ("3AVB", {"3AVB": 100}, "", "positive"),
    ("2AVB", {"1AVB": 100}, "", "unknown"),
    ("LBBB", {"ILBBB": 100}, "", "unknown"),
    ("LBBB", {"CLBBB": 100}, "", "positive"),
    ("Flutter", {"AFLT": 0}, "", "ambiguous"),
    ("ALMI", {"ALMI": 100, "NORM": 100}, "", "ambiguous"),
    ("PAC", {}, "", "unknown"),
])
def test_no_silent_proxy_or_negative(audit, endpoint, codes, marker, expected):
    assert audit.disposition(endpoint, codes, marker) == expected
