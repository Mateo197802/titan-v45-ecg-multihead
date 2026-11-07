import ast
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.signal import butter, lfilter, resample_poly

from titan_v45.cascade.waveform import audit_pathology_waveforms, build_waveform_inventory
from titan_v45.data.preprocessing import CANONICAL_12_LEADS, extract_named_leads
from titan_v45.data.reconstructed import prepare_p4_record

ROOT = Path(__file__).resolve().parents[2]
P4 = ("ASMI", "LVH", "IMI", "ISC_")


def test_preprocessing_is_identical_to_preserved_replay():
    fs = 100
    rng = np.random.default_rng(2026)
    signal = rng.normal(size=(1000, 12))
    names = [name.upper() for name in CANONICAL_12_LEADS]
    wfdb = SimpleNamespace(
        rdheader=lambda _path: SimpleNamespace(fs=fs, sig_len=len(signal)),
        rdrecord=lambda _path, sampfrom, sampto: SimpleNamespace(
            p_signal=signal[sampfrom:sampto], sig_name=names,
        ),
    )
    morphology = SimpleNamespace(
        normalized_morphology_features=lambda values, fs: values[:10, :1].flatten()
    )
    source = (ROOT / "scripts/cedia/forensic_replay_primary4.py").read_text(encoding="utf-8")
    function = next(node for node in ast.parse(source).body
                    if isinstance(node, ast.FunctionDef) and node.name == "preprocess")
    namespace = dict(
        wfdb=wfdb, np=np, extract_named_leads=extract_named_leads, butter=butter,
        lfilter=lfilter, resample_poly=resample_poly, morphology=morphology,
        recovered_trainer_hash="known", leads=list(CANONICAL_12_LEADS),
        present_lead_counts=Counter(), present_leads_by_base={}, case_mapping_changed_bases=set(),
    )
    exec(compile(ast.Module(body=[function], type_ignores=[]), "<frozen replay>", "exec"), namespace)
    original = namespace["preprocess"]("synthetic")
    new = prepare_p4_record("synthetic", morphology.normalized_morphology_features, wfdb_module=wfdb)
    for expected, actual in zip(original, new, strict=True):
        np.testing.assert_array_equal(expected, actual)


def test_p4_inventory_does_not_use_panel_labels_and_rejects_conflicts():
    row = {"record_base": "records/a/a", "record_id": "a", "source": "x"}
    expected = build_waveform_inventory([row])
    assert build_waveform_inventory([{**row, "pathology": "LVH", "target": "0"},
                                     {**row, "pathology": "ASMI", "target": "1"}]) == expected
    with pytest.raises(ValueError, match="conflicting"):
        build_waveform_inventory([row, {**row, "record_base": "records/b/b"}])
    with pytest.raises(ValueError, match="unsafe"):
        build_waveform_inventory([{**row, "record_base": "../a"}])


def test_real_score_contract_keeps_all_outputs_and_failed_inputs():
    rows = [{"record_base": f"records/{k}/{k}", "record_id": k, "source": "x"}
            for k in ("a", "b", "c")]
    inventory = build_waveform_inventory(rows)

    def prepare(base):
        if base.endswith("/b"):
            raise FileNotFoundError("private path")
        return np.zeros((12, 1250)), np.ones(12, dtype=bool), np.zeros(10)

    def score(batch):
        p4 = dict(zip(P4, (0.67, 0.1, 0.8, 0.2), strict=True))
        auxiliary = {"ALMI": 0.1, "ILMI": 0.2, "LAE": 0.3}
        return [(p4, auxiliary)] * len(batch)

    report, ledger = audit_pathology_waveforms(
        inventory, prepare, score, dict(zip(P4, (0.67, 0.7, 0.635, 0.595), strict=True)),
        batch_size=2,
    )
    assert report["inputs"] == 3
    assert report["all_four_p4_scores_records"] == 2
    assert report["post_counts"] == {"no_scores": 1, "quarantine_not_assessed": 2}
    assert report["quarantine_rate_all_inputs"] is None
    assert report["auxiliary_score_support"] == {"ALMI": 2, "ILMI": 2, "LAE": 2}
    assert ledger[("x", "a")]["pathology"] == {"ASMI": True, "LVH": False, "IMI": True, "ISC_": False}
    assert ledger[("x", "b")]["error"] == "FileNotFoundError"
    assert ledger[("x", "c")]["auxiliary_action"] == "no_frozen_policy"
    assert "private path" not in str(ledger)
