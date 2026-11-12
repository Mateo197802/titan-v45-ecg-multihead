import importlib
import zipfile
from pathlib import Path

import pytest


@pytest.fixture
def transport(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts/evaluation"))
    return importlib.import_module("reviewer_closure_ptb_diagnostic_transport")


def test_verified_provider_record_extracts_only_checked_header_and_signals(transport, tmp_path):
    record = "patient001/source"
    archive = tmp_path / "source.zip"
    header = b"source 15 1000 5\n" + b"source.dat 16 1000/mV 16 0 0 0 0 I\n" * 15
    files = {record + ".hea": header, record + ".dat": b"signal"}
    with zipfile.ZipFile(archive, "w") as zipped:
        for k, v in files.items():
            zipped.writestr("data/" + k, v)
    checks = {k: transport.sha256(v) for k, v in files.items()}
    with zipfile.ZipFile(archive) as zipped:
        paths, file_hash = transport.verified_record(zipped, "data/", record, checks, tmp_path)
        assert {p.read_bytes() for p in paths} == set(files.values())
        assert len(file_hash) == 64
        checks[record + ".dat"] = "0" * 64
        with pytest.raises(ValueError, match="signal digest"):
            transport.verified_record(zipped, "data/", record, checks, tmp_path)
