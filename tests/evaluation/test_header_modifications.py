import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from titan_v45.evaluation.source_checksums import describe_header_changes

UPSTREAM = b"example 1 500 100\nexample.mat 16+24 1000/mV 16 0 1 2 0 I\n#Age: 70\n#Dx: 123\n"


def test_reports_byte_identity_without_clinical_equivalence():
    result = describe_header_changes(UPSTREAM, UPSTREAM)
    assert result["byte_identical"]
    assert result["changed_signal_token_columns"] == []
    assert result["changed_comment_fields"] == []
    assert result["clinical_equivalence_certified"] is False


def test_documents_format_changes_without_exporting_values():
    local = UPSTREAM.replace(b"\n", b"\r\n").replace(b"#Age:", b"# Age:")
    local = local.replace(b"16+24 1000/mV", b"16x1+24 1000.0(0)/mV")
    result = describe_header_changes(local, UPSTREAM)
    assert not result["byte_identical"]
    assert result["local_newline_style"] == "CRLF"
    assert result["upstream_newline_style"] == "LF"
    assert result["changed_signal_token_columns"] == [1, 2]
    assert result["changed_comment_fields"] == []
    assert "123" not in json.dumps(result)
    assert "example" not in json.dumps(result)


def test_distinguishes_only_newlines_from_other_format_changes():
    only_newlines = describe_header_changes(UPSTREAM.replace(b"\n", b"\r\n"), UPSTREAM)
    also_spacing = describe_header_changes(UPSTREAM.replace(b"#Age", b"# Age"), UPSTREAM)
    assert only_newlines["identical_after_newline_normalization"] is True
    assert also_spacing["identical_after_newline_normalization"] is False


def test_changed_and_missing_comments_are_not_hidden():
    local = UPSTREAM.replace(b"#Dx: 123", b"#Dx: 456").replace(b"#Age: 70\n", b"")
    result = describe_header_changes(local, UPSTREAM)
    assert result["changed_comment_fields"] == ["age", "dx"]
    assert "456" not in json.dumps(result)
    assert "70" not in json.dumps(result)


def test_unknown_comment_names_are_not_exported():
    result = describe_header_changes(UPSTREAM + b"#PatientName: private\n", UPSTREAM)
    assert result["changed_comment_fields"] == ["other"]
    assert "PatientName" not in json.dumps(result)
    assert "private" not in json.dumps(result)


@pytest.mark.parametrize("invalid", [b"", b"\xff", b"example x 500 100\n", b"example 2 500 100\n"])
def test_rejects_empty_undecodable_or_incomplete_headers(invalid):
    with pytest.raises(ValueError):
        describe_header_changes(invalid, UPSTREAM)


def test_rejects_duplicate_comment_keys_instead_of_masking_them():
    with pytest.raises(ValueError, match="duplicate"):
        describe_header_changes(UPSTREAM + b"# dx: 456\n", UPSTREAM)


def test_changed_record_header_is_not_silently_ignored():
    result = describe_header_changes(UPSTREAM.replace(b"500 100", b"250 100"), UPSTREAM)
    assert result["record_line_tokens_equal"] is False


def test_different_lead_counts_remain_visible():
    other = b"example 2 500 100\nfile.mat 16 1/mV 16 0 0 0 0 I\nfile.mat 16 1/mV 16 0 0 0 0 II\n"
    result = describe_header_changes(other, UPSTREAM)
    assert result["signal_line_count_equal"] is False


@pytest.mark.parametrize("damage", [None, "local_hash", "upstream_hash", "path", "empty", "output_alias"])
def test_cli_fingerprints_inputs_and_does_not_export_identifiers(tmp_path, damage):
    root = Path(__file__).resolve().parents[2]
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    (upstream / "example.hea").write_bytes(UPSTREAM)
    inventory = tmp_path / "inventory.json"
    index = tmp_path / "index.txt"
    output = tmp_path / "report.json"
    digest = hashlib.sha256(UPSTREAM).hexdigest()
    row = {"record_id": "example", "header": UPSTREAM.decode(), "hea_bytes": len(UPSTREAM),
           "hea_sha256": digest, "mat_bytes": 12, "mat_sha256": "a" * 64}
    if damage == "local_hash":
        row["hea_sha256"] = "b" * 64
    if damage == "upstream_hash":
        (upstream / "example.hea").write_bytes(UPSTREAM + b"\n")
    if damage == "path":
        row["record_id"] = "../example"
    index.write_text(f"{'a' * 64}  training/source/example.mat\n{digest}  training/source/example.hea\n")
    inventory.write_text(json.dumps({"records": [] if damage == "empty" else [row]}))
    before = inventory.read_bytes()
    result = subprocess.run([sys.executable, str(root / "scripts/evaluation/audit_header_modifications.py"),
                             "--inventory", str(inventory), "--checksums", str(index),
                             "--upstream-headers", str(upstream),
                             "--output", str(inventory if damage == "output_alias" else output)],
                            capture_output=True, text=True, cwd=root)
    assert inventory.read_bytes() == before
    if damage:
        assert result.returncode != 0
        assert not output.exists()
    else:
        assert result.returncode == 0, result.stderr
        report = json.loads(output.read_text())
        assert report["records"] == 1
        assert report["byte_identical_headers"] == 1
        assert report["distribution_hold_lifted"] is False
        assert "example" not in output.read_text()
        assert "#Age" not in output.read_text()
