from __future__ import annotations

import hashlib
import importlib.util
import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location(
    "audit_cedia_exclusive_revisions",
    ROOT / "scripts/evaluation/audit_cedia_exclusive_revisions.py",
)
audit_revisions = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(audit_revisions)


def _build_archive(tmp_path, name: str, payload: bytes) -> tuple:
    content = {
        "payload.py.txt": payload,
        "PROCEDENCIA_EXPORTACION.csv": b"archivo_zip,sha256_entrada,sha256_exportado,tipo\n",
        "CEDIA_RECOVERED_ORIGINALS.csv": (
            b"bytes,sha256,clasificacion\n1,,NOT_FOUND_IN_SEARCHED_CEDIA_SOURCES\n"
        ),
    }
    content["PROCEDENCIA_EXPORTACION.csv"] += (
        f"payload.py.txt,{'0' * 64},{hashlib.sha256(payload).hexdigest()},copia_saneada\n".encode()
    )
    checksums = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {member}\n"
        for member, data in content.items()
    ).encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        root = "fixture"
        for member, data in content.items():
            archive.writestr(f"{root}/{member}", data)
        archive.writestr(f"{root}/SHA256SUMS.txt", checksums)
    path = tmp_path / name
    path.write_bytes(buffer.getvalue())
    return path, content


def test_audit_revision_checks_crc_checksums_and_export_provenance(tmp_path, monkeypatch):
    archive, _ = _build_archive(tmp_path, "fixture.zip", b"safe source bytes")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    monkeypatch.setitem(audit_revisions.EXPECTED_ARCHIVE_SHA256, 3, digest)

    report, members = audit_revisions._audit_revision(archive, 3)

    assert report["valid"] is True
    assert report["crc_ok"] is True
    assert report["inventory_rows"] == 1
    assert report["exported_payload_hash_matches"] == 1
    assert "payload.py.txt" in members


def test_revision_comparison_counts_changed_and_added_members():
    left = {"same": "a" * 64, "changed": "b" * 64}
    right = {"same": "a" * 64, "changed": "c" * 64, "new": "d" * 64}

    assert audit_revisions._compare_revisions(left, right) == {
        "shared_member_paths": 2,
        "same_path_same_bytes": 1,
        "same_path_changed_bytes": 1,
        "added_members": 1,
        "removed_members": 0,
        "shared_content_hashes": 1,
    }


def test_git_comparison_reports_exact_bytes_without_claiming_source_provenance():
    payloads = {"codigo/TRAINING/example.py.txt": "a" * 64, "other.txt": "b" * 64}
    tracked = {"a" * 64: ["scripts/example.py"], "c" * 64: ["docs/other.txt"]}

    assert audit_revisions._compare_payloads_to_tracked_tree(payloads, tracked) == {
        "payload_member_count": 2,
        "exact_content_match_count": 1,
        "exact_relative_path_and_bytes_count": 0,
        "exact_content_matches": [
            {
                "archive_member": "codigo/TRAINING/example.py.txt",
                "tracked_paths": ["scripts/example.py"],
            }
        ],
    }


def test_audit_does_not_accept_private_or_unsafe_member_paths(tmp_path, monkeypatch):
    path, _ = _build_archive(tmp_path, "fixture.zip", b"safe")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("fixture/../escape", b"unsafe")
    path.write_bytes(buffer.getvalue())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setitem(audit_revisions.EXPECTED_ARCHIVE_SHA256, 3, digest)

    try:
        report, _ = audit_revisions._audit_revision(path, 3)
    except ValueError:
        return
    assert report["valid"] is False
