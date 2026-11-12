import importlib
import zipfile
from pathlib import Path

import pytest


@pytest.fixture
def packet(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts/evaluation"))
    return importlib.import_module("build_reviewer_scientific_closure_zip")


def test_zip_is_deterministic_and_refuses_unapproved_members(packet, tmp_path, monkeypatch):
    monkeypatch.setattr(packet, "ALLOWLIST", frozenset({"evidence.md"}))
    (tmp_path / "evidence.md").write_text("aggregate only", encoding="utf-8")
    a, b = tmp_path / "a.zip", tmp_path / "b.zip"
    assert packet.build(tmp_path, a) == packet.build(tmp_path, b)
    with zipfile.ZipFile(a, "a") as z:
        z.writestr("private.csv", "sample identifier")
    with pytest.raises(ValueError, match="unapproved"):
        packet.verify(a)
