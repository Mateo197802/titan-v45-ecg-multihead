"""Audit cumulative CEDIA REV3-REV6 ZIP exports without extracting or executing them."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from scripts.evaluation.audit_cedia_recovery_bundle import _audit_inner

EXPECTED_ARCHIVE_SHA256 = {
    3: "1975a1bbc65a004b444676e7627349e43d9516898215a3b5ecbf242539c9c986",
    4: "3a87a980c76c1602f450e1aaab720245b566aee4807c21e3f779b73c0469b77a",
    5: "0e88146b007f68feba2ff643f6d98126d139f19d37fe395931bd640453005773",
    6: "4bf835059dfdf40f7fd4b0c1879d94b1175efcb091f6cf9065a5e482a3ad2b11",
}
_REVISION = re.compile(r"_REV([3-6])\.zip$", re.IGNORECASE)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _revision_number(path: Path) -> int:
    match = _REVISION.search(path.name)
    if not match:
        raise ValueError(f"archive filename must identify REV3-REV6: {path.name}")
    return int(match.group(1))


def _audit_revision(path: Path, revision: int) -> tuple[dict[str, Any], dict[str, str]]:
    data = path.read_bytes()
    digest = _sha256(data)
    try:
        with zipfile.ZipFile(path) as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise ValueError("ZIP CRC validation failed")
            inner, members = _audit_inner(data, EXPECTED_ARCHIVE_SHA256[revision])
            root = next(
                PurePosixPath(info.filename).parts[0]
                for info in archive.infolist()
                if not info.is_dir()
            )
            source_code_members = [
                {
                    "member": PurePosixPath(info.filename).relative_to(root).as_posix(),
                    "bytes": info.file_size,
                    "sha256": _sha256(archive.read(info)),
                }
                for info in archive.infolist()
                if not info.is_dir()
                and "/codigo_archivo_fuentes/" in info.filename
                and info.filename.lower().endswith(".py.txt")
            ]
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        raise ValueError(f"REV{revision} cannot be read ({type(exc).__name__})") from exc

    inventory = inner["source_inventory"]
    export = inner["export_provenance"]
    valid = bool(inner["valid"] and digest == EXPECTED_ARCHIVE_SHA256[revision])
    return (
        {
            "revision": revision,
            "archive_name": path.name,
            "archive_sha256": digest,
            "expected_sha256_match": digest == EXPECTED_ARCHIVE_SHA256[revision],
            "archive_bytes": len(data),
            "member_count": inner["member_count"],
            "checksum_entry_count": inner["checksum_entry_count"],
            "crc_ok": inner["zip_crc_ok"],
            "safe_member_names": inner["unsafe_member_count"] == 0,
            "duplicate_names": inner["duplicate_name_count"],
            "single_root": inner["single_root"],
            "inventory_rows": inventory.get("row_count"),
            "inventory_classification_counts": inventory.get("classification_counts", {}),
            "inventory_digest_nature_counts": inventory.get("digest_nature_counts", {}),
            "export_provenance_rows": export.get("row_count"),
            "identical_export_rows": export.get("identical_copy_count"),
            "sanitized_export_rows": export.get("sanitized_copy_count"),
            "exported_payload_hash_matches": export.get("payload_hash_match_count"),
            "export_source_hashes_recomputed": False,
            "source_code_members": source_code_members,
            "bounded_privacy_scan": inner["privacy_screening"],
            "valid": valid,
        },
        members,
    )


def _compare_revisions(left: dict[str, str], right: dict[str, str]) -> dict[str, int]:
    shared = set(left) & set(right)
    return {
        "shared_member_paths": len(shared),
        "same_path_same_bytes": sum(left[name] == right[name] for name in shared),
        "same_path_changed_bytes": sum(left[name] != right[name] for name in shared),
        "added_members": len(set(right) - set(left)),
        "removed_members": len(set(left) - set(right)),
        "shared_content_hashes": len(set(left.values()) & set(right.values())),
    }


def _compare_payloads_to_tracked_tree(
    payloads: dict[str, str], tracked: dict[str, list[str]]
) -> dict[str, Any]:
    matches = [
        {"archive_member": member, "tracked_paths": tracked[digest]}
        for member, digest in sorted(payloads.items())
        if digest in tracked
    ]
    return {
        "payload_member_count": len(payloads),
        "exact_content_match_count": len(matches),
        "exact_relative_path_and_bytes_count": sum(
            member in paths for member, paths in ((row["archive_member"], row["tracked_paths"]) for row in matches)
        ),
        "exact_content_matches": matches,
    }


def _tracked_tree_hashes(repository: Path) -> dict[str, list[str]]:
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=repository).decode().split("\0")
    tracked: dict[str, list[str]] = {}
    for name in names:
        if not name:
            continue
        path = repository / name
        try:
            digest = _sha256(path.read_bytes())
        except OSError:
            continue
        tracked.setdefault(digest, []).append(name.replace("\\", "/"))
    return tracked


def audit_revision_series(
    paths: list[Path], *, compare_git: dict[str, Path] | None = None
) -> dict[str, Any]:
    if len(paths) != 4:
        raise ValueError("exactly REV3, REV4, REV5 and REV6 are required")
    by_revision = {_revision_number(path): path for path in paths}
    if set(by_revision) != {3, 4, 5, 6}:
        raise ValueError("the revision series must contain REV3 through REV6 exactly once")

    reports: list[dict[str, Any]] = []
    member_maps: dict[int, dict[str, str]] = {}
    for revision in range(3, 7):
        report, members = _audit_revision(by_revision[revision], revision)
        reports.append(report)
        member_maps[revision] = members

    comparisons = {
        f"REV{revision}_to_REV{revision + 1}": _compare_revisions(
            member_maps[revision], member_maps[revision + 1]
        )
        for revision in range(3, 6)
    }
    git_comparisons = {}
    for label, repository in (compare_git or {}).items():
        tracked_hashes = _tracked_tree_hashes(repository)
        git_comparisons[label] = {
            "tracked_file_count": sum(len(paths) for paths in tracked_hashes.values()),
            "comparison": _compare_payloads_to_tracked_tree(
                member_maps[6], tracked_hashes
            ),
        }
    return {
        "schema": "TITAN_CEDIA_EXCLUSIVE_REVISION_AUDIT_V1",
        "revision_order": [3, 4, 5, 6],
        "packages": reports,
        "adjacent_revision_comparisons": comparisons,
        "git_tree_comparisons": git_comparisons,
        "raw_packages_published": False,
        "recovered_code_executed": False,
        "clinical_rows_or_identifiers_exported": False,
        "valid": all(report["valid"] for report in reports),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", nargs=4, type=Path, help="REV3, REV4, REV5 and REV6 ZIP files")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument(
        "--compare-git",
        action="append",
        default=[],
        metavar="LABEL=PATH",
        help="compare REV6 members with a tracked Git tree; may be repeated",
    )
    args = parser.parse_args()
    comparisons = {}
    for value in args.compare_git:
        if "=" not in value:
            parser.error("--compare-git must use LABEL=PATH")
        label, path = value.split("=", 1)
        if not label or label in comparisons:
            parser.error("--compare-git labels must be nonempty and unique")
        comparisons[label] = Path(path)
    result = audit_revision_series(args.archives, compare_git=comparisons)
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
