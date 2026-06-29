from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import tarfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from titan_v45.artifacts.manifest import sha256_file

PRIVATE_COLUMNS = {"record", "source_manifest"}
ABSOLUTE_PATH = re.compile(r"^(?:[A-Za-z]:[\\/]|/" + r"home/|/Users/)")


@dataclass(frozen=True)
class DatasetPackageReport:
    manifests: int
    rows: int
    unique_records: int
    files: int


def _slug(value: str, *, fallback: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._").lower()
    return normalized or fallback


def _safe_record_id(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return normalized or "record"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _companion_files(record_base: Path) -> tuple[Path, ...]:
    header = record_base.with_suffix(".hea")
    candidates = {path.resolve() for path in record_base.parent.glob(record_base.name + ".*")}
    if header.is_file():
        candidates.add(header.resolve())
        for line in header.read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
            token = line.split(maxsplit=1)[0] if line.strip() else ""
            if token and not token.startswith("#"):
                referenced = (header.parent / token).resolve()
                if referenced.is_file():
                    candidates.add(referenced)
    files = tuple(sorted((path for path in candidates if path.is_file()), key=lambda item: item.name))
    if header.resolve() not in files:
        raise FileNotFoundError(f"WFDB header is missing for record: {record_base}")
    return files


def _public_row(row: dict[str, str], public_base: PurePosixPath) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in row.items():
        if key in PRIVATE_COLUMNS or (key.endswith("_path") and key != "header_path"):
            continue
        result[key] = "" if ABSOLUTE_PATH.search(str(value)) else str(value)
    result["record_base"] = str(public_base)
    result["header_path"] = str(public_base) + ".hea"
    return result


def _write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError(f"manifest contains no records: {path.name}")
    fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _inventory(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path.name == "package-manifest.json":
            continue
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return rows


def _copy_license_files(root: Path, license_files: Iterable[str | Path] | None) -> list[str]:
    copied: list[str] = []
    if license_files is None:
        return copied
    license_root = root / "licenses"
    license_root.mkdir(parents=True, exist_ok=True)
    for source in license_files:
        source_path = Path(source).resolve()
        if not source_path.is_file():
            raise FileNotFoundError(f"license file is missing: {source_path}")
        destination = license_root / source_path.name
        shutil.copy2(source_path, destination)
        copied.append(destination.relative_to(root).as_posix())
    return sorted(copied)


def materialize_external_development_package(
    manifests: Iterable[str | Path],
    output_dir: str | Path,
    *,
    license_files: Iterable[str | Path] | None = None,
) -> DatasetPackageReport:
    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    manifest_paths = [Path(path).resolve() for path in manifests]
    if not manifest_paths:
        raise ValueError("at least one source manifest is required")
    copied: dict[tuple[str, str], Path] = {}
    row_count = 0
    for manifest in manifest_paths:
        public_rows: list[dict[str, str]] = []
        for row in _read_rows(manifest):
            record_id = str(row.get("record_id", "")).strip()
            record_base = str(row.get("record_base", "")).strip()
            if not record_id or not record_base:
                raise ValueError(f"manifest row lacks record_id or record_base: {manifest.name}")
            source = _slug(
                str(row.get("source_family") or row.get("source") or "unknown"),
                fallback="unknown",
            )
            safe_record_id = _safe_record_id(record_id)
            source_base = Path(record_base).resolve()
            key = (source, safe_record_id)
            prior = copied.get(key)
            if prior is not None and prior != source_base:
                raise ValueError(f"public record collision for {source}/{safe_record_id}")
            public_directory = root / "records" / source / safe_record_id
            public_directory.mkdir(parents=True, exist_ok=True)
            for companion in _companion_files(source_base):
                destination = public_directory / companion.name
                if not destination.exists() or sha256_file(destination) != sha256_file(companion):
                    shutil.copy2(companion, destination)
            copied[key] = source_base
            public_base = PurePosixPath("records", source, safe_record_id, source_base.name)
            public_rows.append(_public_row(row, public_base))
            row_count += 1
        _write_manifest(root / "manifests" / manifest.name, public_rows)
    licenses = _copy_license_files(root, license_files)
    inventory = _inventory(root)
    payload = {
        "protocol": "TITAN_V45_EXTERNAL_DEVELOPMENT_PACKAGE_V1",
        "manifests": [path.name for path in manifest_paths],
        "licenses": licenses,
        "rows": row_count,
        "unique_records": len(copied),
        "files": inventory,
    }
    (root / "package-manifest.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return DatasetPackageReport(len(manifest_paths), row_count, len(copied), len(inventory))


def _create_deterministic_tar(source: Path, tar_path: Path) -> None:
    with tarfile.open(tar_path, mode="w") as handle:
        for path in sorted(source.rglob("*"), key=lambda item: item.relative_to(source).as_posix()):
            arcname = Path(source.name) / path.relative_to(source)
            info = handle.gettarinfo(str(path), arcname.as_posix())
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            if path.is_file():
                with path.open("rb") as file_handle:
                    handle.addfile(info, file_handle)
            else:
                handle.addfile(info)


def _create_tar_zst_with_python(source: Path, destination: Path) -> None:
    try:
        import zstandard as zstd
    except ImportError as exc:  # pragma: no cover - exercised only on missing optional dependency
        raise RuntimeError(
            "tar --zstd is unavailable and Python package 'zstandard' is not installed"
        ) from exc
    temporary_tar = destination.with_suffix(destination.suffix + ".tmp.tar")
    try:
        _create_deterministic_tar(source, temporary_tar)
        compressor = zstd.ZstdCompressor(level=19, threads=0)
        with temporary_tar.open("rb") as src, destination.open("wb") as dst:
            compressor.copy_stream(src, dst)
    finally:
        temporary_tar.unlink(missing_ok=True)


def create_reproducible_tar_zst(source_dir: str | Path, archive: str | Path) -> None:
    source = Path(source_dir).resolve()
    destination = Path(archive).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "tar",
        "--sort=name",
        "--mtime=@0",
        "--owner=0",
        "--group=0",
        "--numeric-owner",
        "--zstd",
        "-cf",
        str(destination),
        "-C",
        str(source.parent),
        source.name,
    ]
    try:
        subprocess.run(command, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        _create_tar_zst_with_python(source, destination)
