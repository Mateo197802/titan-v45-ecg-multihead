import numpy as np

from titan_v45.data import sph_cross_source


def test_signature_comparison_uses_full_12_lead_windows(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "metadata.csv").write_text("ECG_ID,N\nA00001,5000\n", encoding="utf-8")
    release = tmp_path / "release"
    rhythm = release / "data/external_dev/extracted/rhythm/external-dev-rhythm-chapman-shaoxing/records"
    pathology = release / "data/external_dev/extracted/pathology/external-dev-pathology-ptbxl-fold10/records"
    rhythm.mkdir(parents=True)
    pathology.mkdir(parents=True)
    for directory in (rhythm, pathology):
        (directory / "sample.hea").touch()

    waveform = np.arange(12 * 1250, dtype=np.float32).reshape(12, 1250) / 1000
    monkeypatch.setattr(sph_cross_source, "open_sph_records", lambda _: iter([("A00001", b"h5")]))
    monkeypatch.setattr(sph_cross_source, "read_sph_signal", lambda *_: (np.zeros((12, 5000)), "<f8"))
    monkeypatch.setattr(
        sph_cross_source,
        "prepare_sph_waveform",
        lambda *_args, **_kwargs: [(waveform, np.ones(12), np.zeros(10))],
    )
    monkeypatch.setattr(sph_cross_source, "_record_bases", lambda root: [root / "sample"])
    monkeypatch.setattr(
        sph_cross_source,
        "prepare_p4_record",
        lambda *_args, **_kwargs: (waveform.copy(), np.ones(12), np.zeros(10)),
    )

    report, candidates = sph_cross_source.audit_cross_source_signatures(
        source, release
    )

    assert report["sph_records_compared"] == 1
    assert report["retained_source_records_compared"] == {
        "Chapman-Shaoxing-Ningbo": 1,
        "PTB-XL-fold10": 1,
    }
    assert report["candidate_signature_groups_crossing_sources"] == 1
    assert report["candidate_pairs_need_manual_signal_level_confirmation"] is True
    assert report["independence_certified"] is False
    assert "record_id" not in report
    assert len(candidates) == 1
    assert {row["source"] for row in candidates[0]["matches"]} == {
        "SPH", "Chapman-Shaoxing-Ningbo", "PTB-XL-fold10"
    }


def test_no_candidate_groups_do_not_require_manual_confirmation(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "metadata.csv").write_text("ECG_ID,N\nA00001,5000\n", encoding="utf-8")
    release = tmp_path / "release"
    rhythm = release / "data/external_dev/extracted/rhythm/external-dev-rhythm-chapman-shaoxing/records"
    pathology = release / "data/external_dev/extracted/pathology/external-dev-pathology-ptbxl-fold10/records"
    rhythm.mkdir(parents=True)
    pathology.mkdir(parents=True)
    (rhythm / "sample.hea").touch()
    (pathology / "sample.hea").touch()
    sph_waveform = np.zeros((12, 1250), dtype=np.float32)
    def retained_signal(base, _morphology, **_kwargs):
        value = 1 if "rhythm" in str(base) else 2
        return np.full((12, 1250), value, dtype=np.float32), np.ones(12), np.zeros(10)
    monkeypatch.setattr(sph_cross_source, "open_sph_records", lambda _: iter([("A00001", b"h5")]))
    monkeypatch.setattr(sph_cross_source, "read_sph_signal", lambda *_: (np.zeros((12, 5000)), "<f8"))
    monkeypatch.setattr(
        sph_cross_source,
        "prepare_sph_waveform",
        lambda *_args, **_kwargs: [(sph_waveform, np.ones(12), np.zeros(10))],
    )
    monkeypatch.setattr(sph_cross_source, "_record_bases", lambda root: [root / "sample"])
    monkeypatch.setattr(
        sph_cross_source,
        "prepare_p4_record",
        retained_signal,
    )

    report, candidates = sph_cross_source.audit_cross_source_signatures(source, release)

    assert report["candidate_signature_groups_crossing_sources"] == 0
    assert report["candidate_pairs_need_manual_signal_level_confirmation"] is False
    assert report["independence_certified"] is False
    assert candidates == []
