import io
import tarfile

import h5py
import numpy as np
import pytest

from titan_v45.data.sph import open_sph_records, parse_aha, read_sph_metadata, read_sph_signal


def test_primary_and_modifiers_do_not_become_interchangeable():
    assert parse_aha("50+346;161+332", {50, 161}, {346, 332}) == {
        50: (346,), 161: (332,),
    }
    with pytest.raises(ValueError):
        parse_aha("346+50", {50}, {346})
    with pytest.raises(ValueError):
        parse_aha("50;50+346", {50}, {346})
    with pytest.raises(ValueError):
        parse_aha("50+346+346", {50}, {346})


def test_metadata_is_record_unique_but_patient_can_repeat():
    header = "ECG_ID,AHA_Code,Patient_ID,Age,Sex,N,Date\n"
    one = "A00001,50,P1,21,F,5000,2019-01-01\n"
    two = "A00002,50,P1,21,F,5500,2019-01-01\n"
    valid = read_sph_metadata(header + one + two, {50}, set())
    assert len(valid) == 2 and valid["A00001"].patient == valid["A00002"].patient
    with pytest.raises(ValueError, match="duplicate"):
        read_sph_metadata(header + one + one, {50}, set())


def test_tar_format_is_probed_and_paths_are_not_extracted(tmp_path):
    data = io.BytesIO()
    with h5py.File(data, "w") as handle:
        handle["ecg"] = np.zeros((12, 5000), dtype=np.int16)
    raw = data.getvalue()
    archive = tmp_path / "records.tar.gz"
    with tarfile.open(archive, "w") as handle:
        member = tarfile.TarInfo("records/A00001.h5")
        member.size = len(raw)
        handle.addfile(member, io.BytesIO(raw))
    [(name, content)] = list(open_sph_records(archive))
    assert name == "A00001"
    assert read_sph_signal(content, 5000)[0].shape == (12, 5000)
    with pytest.raises(ValueError, match="shape"):
        read_sph_signal(content, 5001)
    with tarfile.open(archive, "w") as handle:
        member = tarfile.TarInfo("../A00001.h5")
        member.size = len(raw)
        handle.addfile(member, io.BytesIO(raw))
    with pytest.raises(ValueError, match="path"):
        list(open_sph_records(archive))
