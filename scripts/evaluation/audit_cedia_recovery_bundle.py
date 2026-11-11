"""Audit nested CEDIA recovery ZIPs without extracting or executing their contents."""

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

from scripts.evaluation.audit_recovery_bundle import (
    _tracked_files,
    audit_recovery_bundle,
    summarize_git_comparison,
)

_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_CHECKSUM_LINE = re.compile(r"^([0-9a-fA-F]{64})\s+\*?(.+)$")
_TEXT_SUFFIXES = {".csv", ".json", ".md", ".py", ".sh", ".txt", ".yaml", ".yml"}
_IDENTIFIER_KEYS = {"ecgid", "patientid", "recordid", "subjectid"}
_MAX_MEMBER_UNCOMPRESSED_BYTES = 64 * 1024 * 1024
_MAX_TOTAL_UNCOMPRESSED_BYTES = 256 * 1024 * 1024
_SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA|EC|OPENSSH|DSA) PRIVATE KEY-----", re.IGNORECASE),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9_]{20,}"),
)
_INTERNAL_PATH = re.compile(
    rb"(?<![A-Za-z0-9/])/(?!/)[A-Za-z0-9_-]+/(?:[A-Za-z0-9_.-]+/)+|"
    rb"[A-Za-z]:[\\/](?:Users|home)[\\/]",
    re.IGNORECASE,
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _unsafe_name(name: str, mode: int, flags: int) -> bool:
    path = PurePosixPath(name)
    return (
        not name
        or "\\" in name
        or path.is_absolute()
        or ".." in path.parts
        or bool(re.match(r"^[A-Za-z]:", name))
        or stat.S_ISLNK(mode)
        or bool(flags & 0x1)
    )


def _relative_members(archive: zipfile.ZipFile) -> tuple[dict[str, bytes], int, int, bool]:
    infos = [info for info in archive.infolist() if not info.is_dir()]
    if any(info.file_size > _MAX_MEMBER_UNCOMPRESSED_BYTES for info in infos) or sum(
        info.file_size for info in infos
    ) > _MAX_TOTAL_UNCOMPRESSED_BYTES:
        raise ValueError("archive exceeds static scan bounds")
    names = [info.filename for info in archive.infolist()]
    duplicate_count = len(names) - len({name.casefold() for name in names})
    unsafe_count = sum(
        _unsafe_name(info.filename, info.external_attr >> 16, info.flag_bits)
        for info in archive.infolist()
    )
    roots = {PurePosixPath(info.filename).parts[0] for info in infos}
    root = next(iter(roots)) if len(roots) == 1 else ""
    members: dict[str, bytes] = {}
    for info in infos:
        parts = PurePosixPath(info.filename).parts
        relative = PurePosixPath(*parts[1:]).as_posix() if root and parts[0] == root else info.filename
        members[relative] = archive.read(info)
    return members, duplicate_count, unsafe_count, len(roots) == 1


def _count_json_identifiers(value: object) -> int:
    if isinstance(value, dict):
        found = 0
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
            if normalized in _IDENTIFIER_KEYS:
                if isinstance(child, str) and child.strip():
                    found += 1
                elif isinstance(child, list):
                    found += sum(isinstance(item, str) and bool(item.strip()) for item in child)
            found += _count_json_identifiers(child)
        return found
    if isinstance(value, list):
        return sum(_count_json_identifiers(item) for item in value)
    return 0


def _privacy_summary(members: dict[str, bytes]) -> dict:
    secret_markers = 0
    csv_id_headers = 0
    json_id_values = 0
    internal_paths = False
    scanned = 0
    skipped = 0
    for name, data in members.items():
        suffix = PurePosixPath(name).suffix.lower()
        if suffix not in _TEXT_SUFFIXES:
            continue
        if len(data) > 32 * 1024 * 1024:
            skipped += 1
            continue
        scanned += 1
        secret_markers += sum(len(pattern.findall(data)) for pattern in _SECRET_PATTERNS)
        internal_paths = internal_paths or bool(_INTERNAL_PATH.search(data))
        if suffix == ".csv":
            try:
                header = next(csv.reader(io.StringIO(data.decode("utf-8-sig"))))
            except (StopIteration, UnicodeDecodeError, csv.Error):
                continue
            csv_id_headers += int(
                any(re.sub(r"[^a-z0-9]", "", field.lower()) in _IDENTIFIER_KEYS for field in header)
            )
        elif suffix == ".json":
            try:
                parsed = json.loads(data)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            json_id_values += _count_json_identifiers(parsed)
            internal_paths = internal_paths or _contains_absolute_json_path(parsed)
    return {
        "common_private_key_or_token_markers": secret_markers,
        "csv_headers_with_record_or_patient_id_fields": csv_id_headers,
        "json_record_identifier_values_detected": json_id_values,
        "source_receipts_contain_internal_paths": internal_paths,
        "text_members_scanned": scanned,
        "oversize_text_members_not_scanned": skipped,
        "scope": "Static bounded text scan only; not a universal privacy or licensing certification.",
    }


def _contains_absolute_json_path(value: object) -> bool:
    if isinstance(value, dict):
        return any(_contains_absolute_json_path(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_absolute_json_path(child) for child in value)
    if isinstance(value, str):
        return (value.startswith("/") and not value.startswith("//")) or bool(
            re.match(r"^[A-Za-z]:[\\/]", value)
        )
    return False


def _parse_sha_manifest(members: dict[str, bytes]) -> tuple[dict[str, str], int]:
    candidates = [name for name in members if PurePosixPath(name).name == "SHA256SUMS.txt"]
    if len(candidates) != 1:
        return {}, 1
    parsed: dict[str, str] = {}
    errors = 0
    for line in members[candidates[0]].decode("utf-8-sig", errors="replace").splitlines():
        match = _CHECKSUM_LINE.fullmatch(line.strip())
        if not match:
            errors += 1
            continue
        relative = match.group(2).replace("\\", "/").removeprefix("./")
        path = PurePosixPath(relative)
        if not relative or path.is_absolute() or ".." in path.parts or relative in parsed:
            errors += 1
            continue
        parsed[path.as_posix()] = match.group(1).lower()
    return parsed, errors


def _audit_export_provenance(members: dict[str, bytes]) -> dict:
    candidates = [name for name in members if PurePosixPath(name).name == "PROCEDENCIA_EXPORTACION.csv"]
    if len(candidates) != 1:
        return {
            "row_count": 0,
            "identical_copy_count": 0,
            "sanitized_copy_count": 0,
            "payload_hash_match_count": 0,
            "identity_claim_errors": 1,
            "valid": False,
        }
    try:
        rows = list(
            csv.DictReader(io.StringIO(members[candidates[0]].decode("utf-8-sig", errors="strict")))
        )
    except (UnicodeDecodeError, csv.Error):
        rows = []
    required = {"archivo_zip", "sha256_entrada", "sha256_exportado", "tipo"}
    if not rows or not required <= set(rows[0]):
        return {
            "row_count": len(rows),
            "identical_copy_count": 0,
            "sanitized_copy_count": 0,
            "payload_hash_match_count": 0,
            "identity_claim_errors": 1,
            "valid": False,
        }

    member_digests = {name: _sha256(data) for name, data in members.items()}
    counts = Counter()
    payload_matches = 0
    errors = 0
    for row in rows:
        relative = (row.get("archivo_zip") or "").replace("\\", "/")
        relpath = PurePosixPath(relative)
        if not relative or relpath.is_absolute() or ".." in relpath.parts:
            errors += 1
            continue
        relative = relpath.as_posix()
        source_hash = (row.get("sha256_entrada") or "").lower()
        exported_hash = (row.get("sha256_exportado") or "").lower()
        identity = row.get("tipo") or ""
        if not _SHA256.fullmatch(source_hash) or not _SHA256.fullmatch(exported_hash):
            errors += 1
            continue
        if relative not in member_digests or member_digests[relative] != exported_hash:
            errors += 1
            continue
        payload_matches += 1
        if identity == "identico":
            counts[identity] += 1
            errors += int(source_hash != exported_hash)
        elif identity == "copia_saneada":
            counts[identity] += 1
        else:
            errors += 1
    return {
        "row_count": len(rows),
        "identical_copy_count": counts["identico"],
        "sanitized_copy_count": counts["copia_saneada"],
        "payload_hash_match_count": payload_matches,
        "identity_claim_errors": errors,
        "source_hashes_independently_recomputed": False,
        "valid": errors == 0 and payload_matches == len(rows),
    }


def _audit_originals_inventory(members: dict[str, bytes]) -> dict:
    candidates = [name for name in members if PurePosixPath(name).name == "CEDIA_RECOVERED_ORIGINALS.csv"]
    if len(candidates) != 1:
        return {"row_count": 0, "schema_ok": False, "valid_digest_fields": False}
    try:
        rows = list(
            csv.DictReader(io.StringIO(members[candidates[0]].decode("utf-8-sig", errors="strict")))
        )
    except (UnicodeDecodeError, csv.Error):
        rows = []
    required = {"bytes", "sha256", "clasificacion"}
    if not rows or not required <= set(rows[0]):
        return {"row_count": len(rows), "schema_ok": False, "valid_digest_fields": False}
    classes = Counter(row.get("clasificacion") or "" for row in rows)
    nature_field_available = "naturaleza_sha256" in rows[0]
    nature = (
        Counter(row.get("naturaleza_sha256") or "" for row in rows)
        if nature_field_available
        else Counter({"NOT_PRESENT_IN_REV1_SCHEMA": len(rows)})
    )
    digests = []
    digest_error_count = 0
    for row in rows:
        value = (row.get("sha256") or "").lower()
        if value:
            if _SHA256.fullmatch(value):
                digests.append(value)
            else:
                digest_error_count += 1
    digest_counts = Counter(digests)
    duplicate_groups = sum(count > 1 for count in digest_counts.values())
    duplicate_extra_rows = sum(count - 1 for count in digest_counts.values() if count > 1)
    return {
        "row_count": len(rows),
        "schema_ok": True,
        "digest_nature_field_available": nature_field_available,
        "classification_counts": dict(sorted(classes.items())),
        "digest_nature_counts": dict(sorted(nature.items())),
        "hash_field_count": len(digests),
        "unique_hash_count": len(digest_counts),
        "duplicate_hash_group_count": duplicate_groups,
        "duplicate_content_extra_row_count": duplicate_extra_rows,
        "digest_field_errors": digest_error_count,
        "source_file_bytes_recomputed_here": False,
        "valid_digest_fields": digest_error_count == 0,
    }


def _audit_inner(data: bytes, expected_sha256: str | None) -> tuple[dict, dict[str, str]]:
    archive_sha = _sha256(data)
    expected_match = None if expected_sha256 is None else archive_sha == expected_sha256.lower()
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            crc_ok = archive.testzip() is None
            members, duplicate_count, unsafe_count, single_root = _relative_members(archive)
    except ValueError:
        return (
            {
                "archive_sha256": archive_sha,
                "expected_sha256_match": expected_match,
                "zip_crc_ok": False,
                "member_count": 0,
                "duplicate_name_count": 0,
                "unsafe_member_count": 0,
                "single_root": False,
                "scan_bound_exceeded": True,
                "checksum_manifest_ok": False,
                "checksum_entry_count": 0,
                "checksum_error_count": 1,
                "export_provenance": {"valid": False},
                "source_inventory": {"schema_ok": False},
                "privacy_screening": {},
                "valid": False,
            },
            {},
        )
    except (OSError, zipfile.BadZipFile, RuntimeError):
        return (
            {
                "archive_sha256": archive_sha,
                "expected_sha256_match": expected_match,
                "zip_crc_ok": False,
                "member_count": 0,
                "duplicate_name_count": 0,
                "unsafe_member_count": 0,
                "single_root": False,
                "scan_bound_exceeded": False,
                "checksum_manifest_ok": False,
                "checksum_entry_count": 0,
                "checksum_error_count": 1,
                "export_provenance": {"valid": False},
                "source_inventory": {"schema_ok": False},
                "privacy_screening": {},
                "valid": False,
            },
            {},
        )
    checksums, checksum_errors = _parse_sha_manifest(members)
    checksum_file = next(
        (name for name in members if PurePosixPath(name).name == "SHA256SUMS.txt"), None
    )
    payload_names = set(members) - ({checksum_file} if checksum_file else set())
    checksum_errors += len(payload_names.symmetric_difference(checksums))
    for relative, expected in checksums.items():
        if relative not in members or _sha256(members[relative]) != expected:
            checksum_errors += 1
    export = _audit_export_provenance(members)
    inventory = _audit_originals_inventory(members)
    member_digests = {name: _sha256(value) for name, value in members.items() if name != checksum_file}
    valid = (
        crc_ok
        and duplicate_count == 0
        and unsafe_count == 0
        and single_root
        and checksum_errors == 0
        and export.get("valid", False)
        and inventory.get("schema_ok", False)
        and inventory.get("valid_digest_fields", False)
        and expected_match is not False
    )
    return (
        {
            "archive_sha256": archive_sha,
            "expected_sha256_match": expected_match,
            "zip_crc_ok": crc_ok,
            "member_count": len(members),
            "duplicate_name_count": duplicate_count,
            "unsafe_member_count": unsafe_count,
            "single_root": single_root,
            "checksum_manifest_ok": checksum_errors == 0,
            "checksum_entry_count": len(checksums),
            "checksum_error_count": checksum_errors,
            "export_provenance": export,
            "source_inventory": inventory,
            "privacy_screening": _privacy_summary(members),
            "valid": valid,
        },
        member_digests,
    )


def _payload_digests(archive_path: Path) -> list[tuple[str, str]]:
    with zipfile.ZipFile(archive_path) as archive:
        result = []
        for info in archive.infolist():
            if info.is_dir():
                continue
            basename = PurePosixPath(info.filename).name.upper()
            if basename == "SHA256SUMS.TXT" or basename.startswith("INVENTARIO_"):
                continue
            result.append((info.filename, _sha256(archive.read(info))))
        return result


def _compare_revisions(first: dict[str, str], second: dict[str, str]) -> dict:
    shared = set(first) & set(second)
    return {
        "shared_member_path_count": len(shared),
        "same_path_same_content_count": sum(first[name] == second[name] for name in shared),
        "same_path_changed_content_count": sum(first[name] != second[name] for name in shared),
        "rev2_added_member_count": len(set(second) - set(first)),
        "rev2_removed_member_count": len(set(first) - set(second)),
        "shared_content_digest_count": len(set(first.values()) & set(second.values())),
    }


def audit_cedia_recovery_bundle(
    outer_path: Path,
    *,
    expected_outer_sha256: str | None = None,
    expected_inner_sha256: dict[str, str] | None = None,
    compare_bundles: list[Path] | None = None,
    git_repo: Path | None = None,
    git_refs: list[str] | None = None,
) -> dict:
    """Verify REV1/REV2 packages in memory; output only digests and aggregate counts."""
    digest = hashlib.sha256()
    with outer_path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    outer_hash = digest.hexdigest()
    outer_match = None if expected_outer_sha256 is None else outer_hash == expected_outer_sha256.lower()
    expected_inner_sha256 = expected_inner_sha256 or {}
    try:
        with zipfile.ZipFile(outer_path) as outer:
            infos = outer.infolist()
            if sum(info.file_size for info in infos if not info.is_dir()) > _MAX_TOTAL_UNCOMPRESSED_BYTES:
                raise ValueError("outer archive exceeds static scan bounds")
            crc_ok = outer.testzip() is None
            names = [info.filename for info in infos]
            outer_duplicates = len(names) - len({name.casefold() for name in names})
            outer_unsafe = sum(
                _unsafe_name(info.filename, info.external_attr >> 16, info.flag_bits)
                for info in infos
            )
            zip_infos = [info for info in infos if not info.is_dir() and info.filename.lower().endswith(".zip")]
            roles = {
                "REV2" if info.filename.upper().endswith("_REV2.ZIP") else "REV1": info
                for info in zip_infos
            }
            role_shape_ok = len(zip_infos) == 2 and set(roles) == {"REV1", "REV2"}
            revisions: dict[str, dict] = {}
            member_maps: dict[str, dict[str, str]] = {}
            for role, info in roles.items():
                report, member_hashes = _audit_inner(
                    outer.read(info), expected_inner_sha256.get(role)
                )
                revisions[role] = report
                member_maps[role] = member_hashes
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        raise ValueError(f"outer CEDIA recovery bundle cannot be read ({type(exc).__name__})") from exc

    comparisons: dict[str, dict] = {}
    if role_shape_ok:
        comparisons["revision_comparison"] = _compare_revisions(
            member_maps.get("REV1", {}), member_maps.get("REV2", {})
        )
    if compare_bundles:
        cedia_payloads = list(member_maps.get("REV2", {}).items())
        for index, prior_path in enumerate(compare_bundles, start=1):
            prior_audit = audit_recovery_bundle(prior_path)
            if not prior_audit["valid"]:
                comparisons[f"prior_bundle_{index}"] = {"valid": False}
                continue
            prior_payloads = _payload_digests(prior_path)
            prior_hashes = {value for _, value in prior_payloads}
            cedia_hashes = {value for _, value in cedia_payloads}
            comparisons[f"prior_bundle_{index}"] = {
                "valid": True,
                "archive_sha256": prior_audit["archive_sha256"],
                "payload_count": len(prior_payloads),
                "cedia_rev2_member_count": len(cedia_payloads),
                "shared_content_digest_count": len(prior_hashes & cedia_hashes),
            }
    if git_repo is not None and git_refs:
        cedia_payloads = list(member_maps.get("REV2", {}).items())
        tracked_files: list[tuple[str, str]] = []
        for ref in git_refs:
            tracked_files.extend(_tracked_files(git_repo.resolve(), ref))
        comparisons["git_refs"] = {
            "ref_count": len(git_refs),
            "refs": git_refs,
            "tracked_file_count": len(tracked_files),
            "comparison": summarize_git_comparison(cedia_payloads, tracked_files),
        }

    all_inner_valid = role_shape_ok and all(value.get("valid", False) for value in revisions.values())
    return {
        "schema": "TITAN_CEDIA_NESTED_RECOVERY_AUDIT_V1",
        "outer": {
            "archive_sha256": outer_hash,
            "expected_sha256_match": outer_match,
            "zip_crc_ok": crc_ok,
            "member_count": len(infos),
            "nested_zip_count": len(zip_infos),
            "duplicate_name_count": outer_duplicates,
            "unsafe_member_count": outer_unsafe,
            "valid": crc_ok and outer_duplicates == 0 and outer_unsafe == 0 and outer_match is not False,
        },
        "revisions": revisions,
        **comparisons,
        "valid": (
            crc_ok
            and outer_duplicates == 0
            and outer_unsafe == 0
            and outer_match is not False
            and all_inner_valid
        ),
        "interpretation": [
            "Archive hashes establish byte identity only; they do not independently authenticate historical origin.",
            "CEDIA inventory hashes are validated as recorded fields, not recomputed against original CEDIA files absent from this transfer.",
            "Exported payload hashes and inner checksum manifests are recomputed from ZIP bytes.",
            "Static privacy screening is bounded and does not certify licensing or authorize publication of source contents.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("outer_zip", type=Path)
    parser.add_argument("--expected-outer-sha256")
    parser.add_argument("--expected-inner-sha256", action="append", default=[], metavar="REV=SHA256")
    parser.add_argument("--compare-bundle", action="append", type=Path, default=[])
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--git-ref", action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        inner_hashes = {}
        for value in args.expected_inner_sha256:
            role, separator, digest = value.partition("=")
            if not separator or role not in {"REV1", "REV2"} or not _SHA256.fullmatch(digest):
                parser.error("expected inner hashes must use REV1= or REV2= followed by a SHA-256 digest")
            inner_hashes[role] = digest
        report = audit_cedia_recovery_bundle(
            args.outer_zip,
            expected_outer_sha256=args.expected_outer_sha256,
            expected_inner_sha256=inner_hashes,
            compare_bundles=args.compare_bundle,
            git_repo=args.repo,
            git_refs=args.git_ref,
        )
    except (OSError, ValueError, zipfile.BadZipFile, csv.Error, UnicodeDecodeError, subprocess.CalledProcessError) as exc:
        parser.error(f"CEDIA recovery bundle could not be audited ({type(exc).__name__})")
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
