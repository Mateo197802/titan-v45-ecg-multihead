from __future__ import annotations

import csv
import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts/evaluation/verify_source_checksums.py"
MAT = hashlib.sha256(b"synthetic waveform").hexdigest()
HEA = hashlib.sha256(b"synthetic header").hexdigest()
OTHER = hashlib.sha256(b"different content").hexdigest()
OFFICIAL = "training/georgia/official-name.mat"


@pytest.fixture
def api():
    return importlib.import_module("titan_v45.evaluation.source_checksums")


def _record(record_id="renamed-local", **changes):
    return {
        "record_id": record_id,
        "mat_bytes": 101,
        "mat_sha256": MAT,
        "hea_bytes": 31,
        "hea_sha256": HEA,
        "header": {"demographics": "PRIVATE_HEADER_SENTINEL"},
        "patient_id": "PRIVATE_PATIENT_SENTINEL",
        **changes,
    }


def _inputs(tmp_path, records=None, checksums=None):
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps({"records": [_record()] if records is None else records}), encoding="utf-8")
    index = tmp_path / "SHA256SUMS.txt"
    index.write_text(
        f"{MAT}  {OFFICIAL}\n{HEA} *training/georgia/official-name.hea\n"
        if checksums is None else checksums,
        encoding="utf-8",
    )
    return inventory, index


def _audit(api, tmp_path, records=None, checksums=None):
    return api.audit_source_checksums(*_inputs(tmp_path, records, checksums))


def test_parses_both_gnu_modes_normalizes_dot_paths_and_idempotent_duplicates():
    try:
        api = importlib.import_module("titan_v45.evaluation.source_checksums")
    except ModuleNotFoundError:
        pytest.fail("offline source-checksum production helper is not implemented")
    index = api.parse_checksums(f"{MAT.upper()}  ./training/a file.mat\r\n\n{MAT} *training/a file.mat\n")
    assert index == {"training/a file.mat": MAT}


def test_parses_exact_physionet_challenge2020_first_line(api):
    line = "9a78e7f22742dde9f66ae235ec793ba2212019dc4d0ced75c4da09ced0b35fb2 LICENSE.txt"
    assert api.parse_checksums(line) == {
        "LICENSE.txt": "9a78e7f22742dde9f66ae235ec793ba2212019dc4d0ced75c4da09ced0b35fb2"}


@pytest.mark.parametrize("separator", [" ", "  ", "\t", " \t   ", " *", "  *", "\t*"])
def test_plain_whitespace_and_gnu_markers_do_not_become_path_prefixes(api, separator):
    assert api.parse_checksums(f"{MAT}{separator}training/a file.mat\r\n") == {
        "training/a file.mat": MAT}


@pytest.mark.parametrize("control", ["\x00", "\x1c", "\x7f", "\u0085", "\u200b", "\u2028", "\u2029", "\u202e", "\u2066"])
def test_unicode_controls_cannot_be_hidden_by_line_splitting_or_path_normalization(api, control):
    with pytest.raises(ValueError):
        api.parse_checksums(f"{MAT} training/a.mat{control}\n")


@pytest.mark.parametrize("tail", ["\u00a0a.mat", " * a.mat", "\t*\ta.mat", " * ../a.mat"])
def test_nonascii_separators_and_whitespace_after_binary_marker_are_rejected(api, tail):
    with pytest.raises(ValueError):
        api.parse_checksums(MAT + tail)


@pytest.mark.parametrize("text", [
    "not a checksum", f"{'g' * 64}  a.mat", f"{MAT[:-1]}  a.mat",
    f"{MAT}a.mat", f"{MAT}  ", f"{MAT}  a.mat\x00",
])
def test_rejects_malformed_checksum_lines(api, text):
    with pytest.raises(ValueError):
        api.parse_checksums(text)


@pytest.mark.parametrize("path", [
    "/absolute.mat", "../escape.mat", "training/../escape.mat", "C:/absolute.mat",
    "C:drive-relative.mat", "./C:/absolute.mat", "./C:drive-relative.mat",
    "\\\\server\\share\\a.mat", "training\\..\\a.mat", ".", "a.mat/", "a.mat/.",
])
def test_rejects_absolute_traversal_and_nonfile_paths(api, path):
    with pytest.raises(ValueError):
        api.parse_checksums(f"{MAT}  {path}\n")


def test_rejects_conflicting_duplicate_normalized_paths(api):
    with pytest.raises(ValueError, match="conflict"):
        api.parse_checksums(f"{MAT}  ./training/a.mat\n{OTHER} *training/a.mat\n")


def test_content_hash_matches_even_when_local_id_and_filename_differ(api, tmp_path):
    report, details = _audit(api, tmp_path)
    row = details[0]
    assert row["status"] == "fully_verified"
    assert row["selected_match_path"] == OFFICIAL
    assert row["verified_source"] == "training/georgia"
    assert row["signal_status"] == row["header_status"] == "matched"
    assert row["matches"][0]["hea_path"] == "training/georgia/official-name.hea"
    assert report["unique_signal_source_counts"] == {"training/georgia": 1}
    assert report["fully_verified_source_counts"] == {"training/georgia": 1}
    assert report["all_records_fully_verified"] is True
    assert report["independent_validation"] is False


def test_filename_or_id_prefix_is_not_proof_and_hea_hash_cannot_match_signal(api, tmp_path):
    report, details = _audit(api, tmp_path, [_record("official-name", mat_sha256=OTHER)],
        f"{MAT}  {OFFICIAL}\n{OTHER}  training/georgia/official-name.hea\n")
    assert details[0]["status"] == "unresolved"
    assert details[0]["matches"] == []
    assert details[0]["verified_source"] is None
    assert report["all_records_fully_verified"] is False


def test_header_mismatch_prevents_full_verification_even_if_hash_exists_elsewhere(api, tmp_path):
    report, details = _audit(api, tmp_path, [_record(hea_sha256=OTHER)],
        f"{MAT}  {OFFICIAL}\n{HEA}  training/georgia/official-name.hea\n{OTHER}  unrelated.hea\n")
    row = details[0]
    assert row["signal_status"] == "matched"
    assert row["header_status"] == "mismatch"
    assert row["status"] == "signal_only"
    assert row["verified_source"] is None
    assert report["fully_verified_source_counts"] == {}
    assert report["all_records_fully_verified"] is False


@pytest.mark.parametrize("changes,index,header_status", [
    ({"hea_bytes": None, "hea_sha256": None}, None, "missing_local"),
    ({}, f"{MAT}  {OFFICIAL}\n", "missing_index"),
])
def test_missing_header_is_explicit_not_verified(api, tmp_path, changes, index, header_status):
    report, details = _audit(api, tmp_path, [_record(**changes)], index)
    assert details[0]["status"] == "signal_only"
    assert details[0]["header_status"] == header_status
    assert report["all_records_fully_verified"] is False


def test_all_ambiguous_paths_retained_and_header_match_does_not_silently_select(api, tmp_path):
    index = (f"{MAT}  training/georgia/a.mat\n{HEA}  training/georgia/a.hea\n"
             f"{MAT}  training/ptb-xl/b.mat\n{OTHER}  training/ptb-xl/b.hea\n")
    report, details = _audit(api, tmp_path, checksums=index)
    row = details[0]
    assert row["status"] == "ambiguous"
    assert row["selected_match_path"] is None and row["verified_source"] is None
    assert row["header_status"] == "not_selected"
    assert [m["mat_path"] for m in row["matches"]] == ["training/georgia/a.mat", "training/ptb-xl/b.mat"]
    assert [m["header_status"] for m in row["matches"]] == ["matched", "mismatch"]
    assert report["unique_signal_source_counts"] == {}
    assert report["all_records_fully_verified"] is False
    assert report["independent_validation"] is False


def test_missing_signal_and_empty_inputs_are_not_vacuously_verified(api, tmp_path):
    report, details = _audit(api, tmp_path, [_record(mat_bytes=None, mat_sha256=None)])
    assert details[0]["status"] == "missing_signal"
    assert details[0]["signal_status"] == "missing"
    assert report["all_records_fully_verified"] is False
    report, details = _audit(api, tmp_path, [], "")
    assert report["records_total"] == report["checksum_entries"] == 0
    assert report["record_status_counts"] == {} and details == []
    assert report["all_records_fully_verified"] is False


def test_duplicate_record_ids_fail_instead_of_double_counting(api, tmp_path):
    with pytest.raises(ValueError, match="duplicate"):
        _audit(api, tmp_path, [_record(), _record()])


@pytest.mark.parametrize("changes", [
    {"record_id": ""}, {"record_id": 12}, {"record_id": "line\nbreak"},
    {"mat_bytes": 0}, {"hea_bytes": -1}, {"mat_bytes": True}, {"hea_bytes": 1.5},
    {"mat_sha256": "invalid"}, {"hea_sha256": "g" * 64}, {"hea_sha256": 13},
    {"mat_sha256": hashlib.sha256(b"").hexdigest()}, {"hea_bytes": None},
    {"mat_sha256": None},
])
def test_invalid_record_sizes_hashes_ids_and_partial_pairs_fail(api, tmp_path, changes):
    with pytest.raises(ValueError):
        _audit(api, tmp_path, [_record(**changes)])


@pytest.mark.parametrize("value", [[], {}, {"records": {}}, {"records": ["not an object"]}])
def test_invalid_inventory_schema_fails(api, tmp_path, value):
    inventory, index = _inputs(tmp_path)
    inventory.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError):
        api.audit_source_checksums(inventory, index)


def test_exact_byte_receipts_reproducibility_and_no_private_metadata_leak(api, tmp_path):
    inventory, index = _inputs(tmp_path)
    index.write_bytes(index.read_bytes().replace(b"\r\n", b"\n"))
    first = api.audit_source_checksums(inventory, index)
    assert first == api.audit_source_checksums(inventory, index)
    report, details = first
    for key, path in (("inventory", inventory), ("checksums", index)):
        assert report["receipt"][key] == {
            "bytes": len(path.read_bytes()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    serialized = json.dumps(report)
    assert "renamed-local" not in serialized and "record_id" not in serialized
    assert "PRIVATE_" not in json.dumps(first) and '"patient_id"' not in json.dumps(first)
    assert '"header"' not in json.dumps(details)
    index.write_bytes(index.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    second_report, second_details = api.audit_source_checksums(inventory, index)
    assert second_details == details
    assert second_report["receipt"]["checksums"] != report["receipt"]["checksums"]


def _run_cli(*args):
    return subprocess.run([sys.executable, "-B", str(CLI), *map(str, args)], cwd=ROOT,
                          capture_output=True, text=True, check=False)


@pytest.mark.parametrize("extension", [None, "json", "csv"])
def test_cli_defaults_to_aggregate_and_details_are_explicit_opt_in(api, tmp_path, extension):
    inventory, index = _inputs(tmp_path)
    output = tmp_path / "output.json"
    details = tmp_path / f"details.{extension}"
    args = ["--inventory", inventory, "--checksums", index, "--output", output]
    if extension:
        args += ["--details", details]
    before = (inventory.read_bytes(), index.read_bytes())
    result = _run_cli(*args)
    assert result.returncode == 0, result.stderr
    assert json.loads(output.read_text(encoding="utf-8"))["records_total"] == 1
    assert "renamed-local" not in output.read_text(encoding="utf-8")
    assert "PRIVATE_" not in output.read_text(encoding="utf-8")
    if extension:
        text = details.read_text(encoding="utf-8")
        assert "renamed-local" in text and "PRIVATE_" not in text
        parsed = json.loads(text) if extension == "json" else list(csv.DictReader(text.splitlines()))
        assert parsed[0]["record_id"] == "renamed-local"
    else:
        assert not details.exists()
    assert before == (inventory.read_bytes(), index.read_bytes())


def test_cli_validation_failure_does_not_write_or_overwrite_outputs(api, tmp_path):
    inventory, index = _inputs(tmp_path, [_record(mat_bytes=0)])
    output = tmp_path / "output.json"
    output.write_text("preserve-existing", encoding="utf-8")
    result = _run_cli("--inventory", inventory, "--checksums", index, "--output", output)
    assert result.returncode == 1 and "failed" in result.stderr.lower()
    assert output.read_text(encoding="utf-8") == "preserve-existing"
    assert "PRIVATE_" not in result.stderr


@pytest.mark.parametrize("collision", ["inventory", "checksums", "details", "bad_extension"])
def test_cli_refuses_input_overwrites_output_collisions_and_invalid_detail_format(api, tmp_path, collision):
    inventory, index = _inputs(tmp_path)
    output = inventory if collision == "inventory" else index if collision == "checksums" else tmp_path / "out.json"
    details = output if collision == "details" else tmp_path / "details.txt"
    args = ["--inventory", inventory, "--checksums", index, "--output", output]
    if collision in {"details", "bad_extension"}:
        args += ["--details", details]
    before = (inventory.read_bytes(), index.read_bytes())
    result = _run_cli(*args)
    assert result.returncode == 1
    assert before == (inventory.read_bytes(), index.read_bytes())
    if output not in (inventory, index):
        assert not output.exists()


@pytest.mark.parametrize("target", ["inventory", "checksums", "output"])
def test_cli_refuses_hardlink_aliases_before_overwriting_any_input_or_output(api, tmp_path, target):
    inventory, index = _inputs(tmp_path)
    output = tmp_path / "out.json"
    output.write_text("existing output", encoding="utf-8")
    alias = tmp_path / "alias.json"
    source = {"inventory": inventory, "checksums": index, "output": output}[target]
    alias.hardlink_to(source)
    before = [p.read_bytes() for p in (inventory, index, output)]
    args = ["--inventory", inventory, "--checksums", index, "--output", alias]
    if target == "output":
        args = ["--inventory", inventory, "--checksums", index, "--output", output, "--details", alias]
    result = _run_cli(*args)
    assert result.returncode == 1
    assert [p.read_bytes() for p in (inventory, index, output)] == before
