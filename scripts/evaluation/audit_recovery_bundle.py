"""Validate a recovery ZIP without extracting or executing its contents."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import stat
import subprocess
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

_TEXT_SUFFIXES = {
    ".csv",
    ".json",
    ".log",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".tsv",
    ".txt",
    ".yaml",
    ".yml",
}
_IDENTIFIER_KEYS = {"ecgid", "patientid", "recordid", "subjectid"}
_SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA|EC|OPENSSH|DSA) PRIVATE KEY-----", re.IGNORECASE),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9_]{20,}"),
)
_INTERNAL_PATH_PATTERN = re.compile(
    rb"(?<![A-Za-z0-9/])/(?!/)[A-Za-z0-9_-]+/(?:[A-Za-z0-9_.-]+/)+|[A-Za-z]:[\\/](?:Users|home)[\\/]",
    re.IGNORECASE,
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _unsafe_member(info: zipfile.ZipInfo) -> bool:
    name = info.filename
    path = PurePosixPath(name)
    mode = info.external_attr >> 16
    return (
        not name
        or "\\" in name
        or path.is_absolute()
        or ".." in path.parts
        or bool(re.match(r"^[A-Za-z]:", name))
        or stat.S_ISLNK(mode)
        or bool(info.flag_bits & 0x1)
    )


def _identifier_values(value: object) -> int:
    if isinstance(value, dict):
        count = 0
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
            if normalized in _IDENTIFIER_KEYS:
                if isinstance(child, str) and child.strip():
                    count += 1
                elif isinstance(child, list):
                    count += sum(isinstance(item, str) and bool(item.strip()) for item in child)
            count += _identifier_values(child)
        return count
    if isinstance(value, list):
        return sum(_identifier_values(item) for item in value)
    return 0


def _contains_absolute_path(value: object) -> bool:
    if isinstance(value, dict):
        return any(_contains_absolute_path(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_absolute_path(child) for child in value)
    if isinstance(value, str):
        return (value.startswith("/") and not value.startswith("//")) or bool(
            re.match(r"^[A-Za-z]:[\\/]", value)
        )
    return False


def screen_archive_privacy(archive_path: Path, max_text_bytes: int = 32 * 1024 * 1024) -> dict:
    """Return aggregate-only static indicators; never return member names or values."""
    secret_markers = 0
    csv_identifier_headers = 0
    json_identifier_values = 0
    internal_paths = False
    scanned_text_members = 0
    skipped_large_text_members = 0
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            if info.is_dir() or Path(info.filename).suffix.lower() not in _TEXT_SUFFIXES:
                continue
            if info.file_size > max_text_bytes:
                skipped_large_text_members += 1
                continue
            raw = archive.read(info)
            scanned_text_members += 1
            secret_markers += sum(len(pattern.findall(raw)) for pattern in _SECRET_PATTERNS)
            internal_paths = internal_paths or bool(_INTERNAL_PATH_PATTERN.search(raw))
            suffix = Path(info.filename).suffix.lower()
            if suffix == ".csv":
                try:
                    header = next(
                        csv.reader(io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8-sig"))
                    )
                except (StopIteration, UnicodeDecodeError, csv.Error):
                    continue
                if any(
                    re.sub(r"[^a-z0-9]", "", field.lower()) in _IDENTIFIER_KEYS for field in header
                ):
                    csv_identifier_headers += 1
            elif suffix == ".json":
                try:
                    parsed = json.loads(raw)
                    json_identifier_values += _identifier_values(parsed)
                    internal_paths = internal_paths or _contains_absolute_path(parsed)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
    return {
        "common_private_key_or_token_markers": secret_markers,
        "csv_headers_with_record_or_patient_id_fields": csv_identifier_headers,
        "json_record_identifier_values_detected": json_identifier_values,
        "source_receipts_contain_internal_paths": internal_paths,
        "text_members_scanned": scanned_text_members,
        "oversize_text_members_not_scanned": skipped_large_text_members,
        "scope": "Static scan of bounded text members and selected identifier keys; not a universal privacy certification.",
    }


def summarize_git_comparison(
    payloads: list[tuple[str, str]], tracked_files: list[tuple[str, str]]
) -> dict:
    """Compare payload names/digests with tracked files without exposing paths."""
    tracked_digests = {digest for _, digest in tracked_files}
    tracked_by_basename: dict[str, set[str]] = {}
    tracked_by_path: dict[str, set[str]] = {}
    for path, digest in tracked_files:
        tracked_by_basename.setdefault(PurePosixPath(path).name.casefold(), set()).add(digest)
        tracked_by_path.setdefault(path.replace("\\", "/").casefold(), set()).add(digest)
    exact_content = sum(digest in tracked_digests for _, digest in payloads)
    exact_path = sum(
        digest in tracked_by_path.get(path.replace("\\", "/").casefold(), set())
        for path, digest in payloads
    )
    basename_conflicts = sum(
        PurePosixPath(path).name.casefold() in tracked_by_basename
        and digest not in tracked_by_basename[PurePosixPath(path).name.casefold()]
        for path, digest in payloads
    )
    return {
        "payload_count": len(payloads),
        "byte_identical_to_any_tracked_file_count": exact_content,
        "exact_relative_path_and_bytes_count": exact_path,
        "nonidentical_payload_count": len(payloads) - exact_content,
        "same_basename_different_bytes_count": basename_conflicts,
        "tracked_file_count": len(tracked_files),
    }


def _tracked_files(repo: Path, ref: str = "HEAD") -> list[tuple[str, str]]:
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-r", "-z", ref], check=True, capture_output=True
    )
    changed_result = subprocess.run(
        ["git", "-C", str(repo), "diff", "--name-only", "-z", ref],
        check=True,
        capture_output=True,
    )
    changed = {
        item.decode("utf-8", errors="surrogateescape")
        for item in changed_result.stdout.split(b"\0")
        if item
    }
    tracked = []
    for entry in result.stdout.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        if metadata.split(b" ", 1)[0] == b"120000":
            continue
        relative = raw_path.decode("utf-8", errors="surrogateescape")
        path = repo / relative
        if relative in changed:
            content = subprocess.run(
                ["git", "-C", str(repo), "show", f"{ref}:{relative}"],
                check=True,
                capture_output=True,
            ).stdout
            digest = hashlib.sha256(content).hexdigest()
            tracked.append((relative.replace("\\", "/"), digest))
        elif path.is_file() and not path.is_symlink():
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(block)
            tracked.append((relative.replace("\\", "/"), digest.hexdigest()))
    return tracked


def compare_bundle_to_git(
    archive_path: Path,
    repo_roots: list[Path],
    expected_sha256: str | None = None,
    refs: list[str] | None = None,
) -> dict:
    """Compare each ZIP payload to tracked repo files; report counts only."""
    integrity = audit_recovery_bundle(archive_path, expected_sha256)
    if not integrity["valid"]:
        raise ValueError("recovery bundle integrity checks failed")
    payloads = []
    with zipfile.ZipFile(archive_path) as archive:
        infos = [info for info in archive.infolist() if not info.is_dir()]
        root = infos[0].filename.split("/", 1)[0]
        excluded = {"INVENTARIO_COMPLETO.csv", "SHA256SUMS.txt"}
        for info in infos:
            if info.filename.rsplit("/", 1)[-1] in excluded:
                continue
            digest = hashlib.sha256(archive.read(info)).hexdigest()
            payloads.append((info.filename[len(root) + 1 :], digest))
    tracked = []
    selected_refs = refs or ["HEAD"] * len(repo_roots)
    if len(selected_refs) != len(repo_roots):
        raise ValueError("provide one Git ref per repository")
    for repo, ref in zip(repo_roots, selected_refs, strict=True):
        tracked.extend(_tracked_files(repo.resolve(), ref))
    return summarize_git_comparison(payloads, tracked)


def audit_recovery_bundle(archive_path: Path, expected_sha256: str | None = None) -> dict:
    """Verify ZIP integrity, safe names, the inventory and SHA256SUMS entries."""
    digest = hashlib.sha256()
    with archive_path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    archive_sha256 = digest.hexdigest()
    expected_match = None if expected_sha256 is None else archive_sha256 == expected_sha256.lower()

    counters = Counter()
    crc_ok = False
    manifest_ok = False
    inventory_rows = 0
    checksum_entries = 0
    inventory_file_count = 0
    inventory_type_counts = {}
    evidence_level_counts = {}
    file_count = 0
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        file_infos = [item for item in infos if not item.is_dir()]
        file_count = len(file_infos)
        counters["unsafe_member_count"] = sum(_unsafe_member(item) for item in infos)
        counters["duplicate_name_count"] = len(names) - len({name.casefold() for name in names})
        crc_ok = archive.testzip() is None

        inventory_matches = [name for name in names if name.endswith("/INVENTARIO_COMPLETO.csv")]
        sums_matches = [name for name in names if name.endswith("/SHA256SUMS.txt")]
        if len(inventory_matches) == len(sums_matches) == 1 and infos:
            inventory_name = inventory_matches[0]
            sums_name = sums_matches[0]
            root = names[0].split("/", 1)[0]
            inventory_data = archive.read(inventory_name)
            inventory_rows_data = list(
                csv.DictReader(io.TextIOWrapper(io.BytesIO(inventory_data), encoding="utf-8-sig"))
            )
            inventory_rows = len(inventory_rows_data)
            inventory_type_counts = dict(
                sorted(Counter(row.get("tipo", "") for row in inventory_rows_data).items())
            )
            evidence_level_counts = dict(
                sorted(
                    Counter(row.get("nivel_evidencia", "") for row in inventory_rows_data).items()
                )
            )
            inventory = {}
            for row in inventory_rows_data:
                relative = (row.get("ruta_relativa") or "").replace("\\", "/").lstrip("./")
                if not relative or relative in inventory:
                    counters["inventory_structure_error_count"] += 1
                    continue
                inventory[relative] = row

            expected_payload = {
                info.filename[len(root) + 1 :]
                for info in file_infos
                if info.filename.startswith(root + "/")
                and info.filename not in (inventory_name, sums_name)
            }
            inventory_file_count = len(inventory)
            if set(inventory) != expected_payload:
                counters["inventory_coverage_error_count"] += len(set(inventory) ^ expected_payload)
            for relative, row in inventory.items():
                name = root + "/" + relative
                if name not in names:
                    counters["inventory_missing_member_count"] += 1
                    continue
                content = archive.read(name)
                try:
                    expected_size = int(row.get("bytes", ""))
                except (TypeError, ValueError):
                    counters["inventory_size_error_count"] += 1
                else:
                    if expected_size != len(content):
                        counters["inventory_size_error_count"] += 1
                expected_hash = (row.get("sha256") or "").strip().lower()
                if (
                    not re.fullmatch(r"[0-9a-f]{64}", expected_hash)
                    or _sha256_bytes(content) != expected_hash
                ):
                    counters["inventory_hash_error_count"] += 1

            checksums = {}
            for line in archive.read(sums_name).decode("utf-8-sig").splitlines():
                match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?(.+)", line.strip())
                if not match:
                    counters["checksum_format_error_count"] += 1
                    continue
                relative = match.group(2).replace("\\", "/").lstrip("./")
                if relative in checksums:
                    counters["checksum_duplicate_entry_count"] += 1
                checksums[relative] = match.group(1).lower()
            checksum_entries = len(checksums)
            expected_checksums = {
                info.filename[len(root) + 1 :]
                for info in file_infos
                if info.filename.startswith(root + "/") and info.filename != sums_name
            }
            if set(checksums) != expected_checksums:
                counters["checksum_coverage_error_count"] += len(
                    set(checksums) ^ expected_checksums
                )
            for relative, expected_hash in checksums.items():
                name = root + "/" + relative
                if name not in names:
                    counters["checksum_missing_member_count"] += 1
                elif _sha256_bytes(archive.read(name)) != expected_hash:
                    counters["checksum_hash_error_count"] += 1

            manifest_ok = not any(
                counters[key]
                for key in counters
                if key.endswith("error_count") or key.endswith("entry_count")
            )

    valid = (
        crc_ok
        and manifest_ok
        and counters["unsafe_member_count"] == 0
        and counters["duplicate_name_count"] == 0
        and expected_match is not False
    )
    return {
        "schema": "TITAN_RECOVERY_ZIP_AUDIT_V1",
        "archive_sha256": archive_sha256,
        "expected_sha256_match": expected_match,
        "zip_crc_ok": crc_ok,
        "file_count": file_count,
        "inventory_rows": inventory_rows,
        "sha256sum_entries": checksum_entries,
        "inventory_row_count_matches": inventory_file_count == inventory_rows,
        "inventory_type_counts": inventory_type_counts,
        "evidence_level_counts": evidence_level_counts,
        "manifest_checks_ok": manifest_ok,
        "unsafe_member_count": counters["unsafe_member_count"],
        "duplicate_name_count": counters["duplicate_name_count"],
        "error_counts": {
            key: value
            for key, value in sorted(counters.items())
            if value
            and key.endswith("count")
            and key not in {"unsafe_member_count", "duplicate_name_count"}
        },
        "privacy_screening": screen_archive_privacy(archive_path),
        "valid": valid,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--repo", action="append", type=Path, default=[])
    parser.add_argument("--ref", action="append", default=[])
    args = parser.parse_args()
    try:
        report = audit_recovery_bundle(args.archive, args.expected_sha256)
        if args.repo:
            report["git_comparison"] = compare_bundle_to_git(
                args.archive, args.repo, args.expected_sha256, args.ref or None
            )
    except (
        OSError,
        zipfile.BadZipFile,
        UnicodeDecodeError,
        csv.Error,
        ValueError,
        subprocess.CalledProcessError,
    ) as exc:
        parser.error(f"archive could not be audited ({type(exc).__name__})")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
