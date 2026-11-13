from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from titan_v45.data.mimic_ecg_waveform import (
    prepare_mimic_waveform,
    resolve_mimic_record_base,
)
from titan_v45.evaluation.mimic_concordance import summarize_mimic_pac_concordance

LEADS = ("I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6")


class FakeWfdb:
    def __init__(self, *, fs=500, samples=5000, leads=LEADS, units=None):
        self.header = SimpleNamespace(
            fs=fs, sig_len=samples, n_sig=len(leads), sig_name=list(leads),
            units=list(units or ["mV"] * len(leads)),
        )
        time = np.arange(samples, dtype=np.float32) / fs
        self.record = SimpleNamespace(
            p_signal=np.stack([np.sin(2 * np.pi * (1 + index / 4) * time)
                               for index in range(len(leads))], axis=1),
            sig_name=list(leads),
        )

    def rdheader(self, _):
        return self.header

    def rdrecord(self, _, *, sampfrom, sampto):
        return SimpleNamespace(
            p_signal=self.record.p_signal[sampfrom:sampto],
            sig_name=self.record.sig_name,
        )


def test_mimic_waveform_requires_canonical_12_lead_physical_contract():
    prepared = prepare_mimic_waveform("fixture", wfdb_module=FakeWfdb())

    assert len(prepared["windows"]) == 1
    signal, lead_mask, _ = prepared["windows"][0]
    assert signal.shape == (12, 1250)
    assert lead_mask.all()
    assert len(prepared["signal_sha256"]) == 64
    assert prepared["max_abs_mv"] == pytest.approx(1.0, abs=1e-5)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"fs": 250}, "500 Hz"),
        ({"samples": 4999}, "10-second"),
        ({"leads": (*LEADS[:-1], "RESP")}, "canonical 12-lead"),
        ({"units": ["uV"] * 12}, "mV units"),
    ],
)
def test_mimic_waveform_rejects_incompatible_source_contract(kwargs, message):
    with pytest.raises(ValueError, match=message):
        prepare_mimic_waveform("fixture", wfdb_module=FakeWfdb(**kwargs))


def test_mimic_record_path_resolution_rejects_traversal_and_symlinked_members(
    tmp_path, monkeypatch,
):
    root = tmp_path / "dataset"
    base = root / "files/p1000/p10000001/s40000001/40000001"
    base.parent.mkdir(parents=True)
    Path(f"{base}.hea").write_text("header", encoding="ascii")
    Path(f"{base}.dat").write_bytes(b"signal")
    assert resolve_mimic_record_base(
        root, "files/p1000/p10000001/s40000001/40000001"
    ) == base
    with pytest.raises(ValueError, match="unsafe MIMIC waveform path"):
        resolve_mimic_record_base(root, "../outside/record")

    target = Path(f"{base}.hea")
    original_is_symlink = Path.is_symlink
    monkeypatch.setattr(
        Path, "is_symlink", lambda path: path == target or original_is_symlink(path)
    )
    with pytest.raises(ValueError, match="missing or unsafe"):
        resolve_mimic_record_base(root, "files/p1000/p10000001/s40000001/40000001")


def test_mimic_machine_report_concordance_keeps_unmentioned_out_of_binary_metrics():
    report = summarize_mimic_pac_concordance(
        report_states=[
            "positive_mention", "explicit_negative_mention", "not_mentioned",
            "ambiguous_mention", "missing_report_text", "positive_mention",
        ],
        scores=[0.9, 0.1, 0.99, 0.01, 0.8, float("nan")],
        patient_ids=["p1", "p1", "p2", "p2", "p3", "p4"],
        signal_hashes=[f"{index:064x}" for index in range(1, 6)] + [""],
        waveform_statuses=["scored", "scored", "scored", "scored", "scored",
                           "failure:fixture"],
        replicates=20,
        seed=17,
    )

    assert report["record_count"] == 6
    assert report["report_state_counts"] == {
        "positive_mention": 2,
        "explicit_negative_mention": 1,
        "not_mentioned": 1,
        "ambiguous_mention": 1,
        "missing_report_text": 1,
    }
    assert report["binary_report_denominator"] == 3
    assert report["scored_binary_report_records"] == 2
    assert report["coverage_among_explicit_binary_reports"] == pytest.approx(2 / 3)
    assert report["metrics"]["n"] == 2
    assert report["metrics"]["accuracy"] == 1.0
    assert report["bootstrap"]["replicates_requested"] == 20
    assert report["identifiers_exported"] is False


def test_mimic_concordance_requires_status_score_and_identifier_contract():
    with pytest.raises(ValueError, match="scored rows require finite probabilities"):
        summarize_mimic_pac_concordance(
            report_states=["positive_mention"], scores=[float("nan")],
            patient_ids=["p1"], signal_hashes=["1" * 64], waveform_statuses=["scored"],
            replicates=2,
        )


def test_mimic_concordance_reports_cross_patient_conflict_and_sensitivity():
    shared_hash = "a" * 64
    report = summarize_mimic_pac_concordance(
        report_states=["positive_mention", "explicit_negative_mention"],
        scores=[0.8, 0.2],
        patient_ids=["p1", "p2"],
        signal_hashes=[shared_hash, shared_hash],
        waveform_statuses=["scored", "scored"],
        replicates=10,
        seed=23,
    )

    assert report["duplicate_audit"] == {
        "exact_duplicate_groups": 1,
        "cross_patient_exact_duplicate_groups": 1,
        "explicit_report_label_conflict_groups": 1,
        "discordant_duplicate_rows_excluded_in_sensitivity": 2,
    }
    assert report["metrics"]["n"] == 2
    assert report["discordant_duplicate_sensitivity"]["metrics"] is None
    assert report["discordant_duplicate_sensitivity"]["bootstrap"]["status"] == (
        "no_scored_binary_mentions"
    )
