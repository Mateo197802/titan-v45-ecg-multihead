import importlib
import io
import tarfile

import pytest

zstandard = pytest.importorskip("zstandard")
_extract = importlib.import_module(
    "scripts.external_validation.stage_retained_wfdb_archives"
)._extract


def _write_archive(path, names):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as archive:
        for name in names:
            payload = name.encode()
            member = tarfile.TarInfo(name)
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))
    path.write_bytes(zstandard.ZstdCompressor().compress(raw.getvalue()))


def test_stage_retained_wfdb_archive_selects_supported_files_and_checks_pairs(tmp_path):
    package = "external-dev-rhythm-chapman-shaoxing"
    archive = tmp_path / "retained.tar.zst"
    _write_archive(archive, [
        f"{package}/records/sub/record.hea",
        f"{package}/records/sub/record.mat",
        f"{package}/records/sub/record.atr",
    ])

    counts = _extract(archive, tmp_path / "scratch", package)

    assert counts == {
        ".hea": 1,
        ".mat": 1,
        "ignored_non_waveform_members": 1,
        "records_with_header_and_data": 1,
    }
    assert (tmp_path / "scratch" / package / "records/sub/record.hea").is_file()
    assert not (tmp_path / "scratch" / package / "records/sub/record.atr").exists()


def test_stage_retained_wfdb_archive_rejects_unsafe_paths(tmp_path):
    archive = tmp_path / "unsafe.tar.zst"
    _write_archive(archive, ["external-dev/records/../escape.hea"])

    with pytest.raises(ValueError, match="unsafe member path"):
        _extract(archive, tmp_path / "scratch", "external-dev")
