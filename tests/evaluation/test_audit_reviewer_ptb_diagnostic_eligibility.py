import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def audit(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts/evaluation"))
    return importlib.import_module("audit_reviewer_ptb_diagnostic_eligibility")


def test_territory_contract_never_relabels_other_diseases_as_control(audit):
    config = json.loads((ROOT / "configs/reviewer_experiments/ptb_diagnostic_eligibility_v1.json").read_bytes())
    assert audit.source_references(
        b"# Reason for admission: Myocardial infarction\n# Acute infarction (localization): infero-lateral", config,
    ) == {"ASMI": "unknown", "IMI": "unknown", "ALMI": "unknown", "ILMI": "positive"}
    assert set(audit.source_references(
        b"# Reason for admission: Cardiomyopathy", config,
    ).values()) == {"unknown"}
    assert set(audit.source_references(
        b"# Reason for admission: Healthy control\n# Acute infarction (localization): n/a", config,
    ).values()) == {"explicit_control"}
    assert set(audit.source_references(
        b"# Reason for admission: Healthy control\n# Reason for admission: Myocardial infarction", config,
    ).values()) == {"discordant_header"}


def test_eligibility_uses_subjects_instead_of_repeated_ecgs(audit):
    refs = [{"source_subject": "A", "references": {"ASMI": "positive"}}] * 6
    refs.extend({"source_subject": str(i), "references": {"ASMI": "explicit_control"}} for i in range(5))
    e = audit.summarize(refs, ["ASMI"])["ASMI"]
    assert e["record_states"]["positive"] == 6 and e["subject_states"]["positive"] == 1
    assert not e["eligible_for_territory_control_comparison"]


def test_amendment_accepts_explicit_control_no_but_not_other_disease(audit):
    v2 = json.loads((ROOT / "configs/reviewer_experiments/ptb_diagnostic_eligibility_v2.json").read_bytes())
    no = b"\n# Acute infarction (localization): no"
    assert set(audit.source_references(b"# Reason for admission: Healthy control" + no, v2).values()) == {
        "explicit_control",
    }
    assert set(audit.source_references(b"# Reason for admission: Dysrhythmia" + no, v2).values()) == {"unknown"}
