"""Stage only the retained WFDB waveform members on node-local scratch."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tarfile
from collections import Counter
from pathlib import Path, PurePosixPath

import zstandard

PACKAGES = {
    "Chapman-Shaoxing-Ningbo": (
        "external-dev-rhythm-chapman-shaoxing",
        Path("data/external_dev/rhythm/external-dev-rhythm-chapman-shaoxing.tar.zst"),
        Path("data/external_dev/extracted/rhythm"),
    ),
    "PTB-XL-fold10": (
        "external-dev-pathology-ptbxl-fold10",
        Path("data/external_dev/pathology/external-dev-pathology-ptbxl-fold10.tar.zst"),
        Path("data/external_dev/extracted/pathology"),
    ),
}
SUPPORTED_SUFFIXES = {".hea", ".dat", ".mat"}


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _extract(archive_path: Path, destination_root: Path, package: str):
    counts = Counter()
    headers, data = set(), set()
    with archive_path.open("rb") as compressed, zstandard.ZstdDecompressor().stream_reader(
        compressed
    ) as stream, tarfile.open(fileobj=stream, mode="r|") as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            if (path.is_absolute() or ".." in path.parts or "\\" in member.name):
                raise ValueError("unsafe member path in retained waveform package")
            if path.parts[:2] != (package, "records") or member.isdir():
                continue
            if not member.isfile():
                raise ValueError("non-regular record member in retained waveform package")
            suffix = path.suffix.lower()
            if suffix not in SUPPORTED_SUFFIXES:
                counts["ignored_non_waveform_members"] += 1
                continue
            if member.size > 32 * 1024 * 1024:
                raise ValueError("unexpectedly large WFDB member")
            target = (destination_root / Path(*path.parts)).resolve()
            if not target.is_relative_to(destination_root.resolve()):
                raise ValueError("waveform member escapes the scratch destination")
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as output, archive.extractfile(member) as source:
                shutil.copyfileobj(source, output)
            counts[suffix] += 1
            base = path.with_suffix("").as_posix()
            (headers if suffix == ".hea" else data).add(base)
    if not headers or headers - data:
        raise ValueError("retained WFDB package has a header without a data file")
    counts["records_with_header_and_data"] = len(headers)
    return dict(sorted(counts.items()))


def stage(release_root: Path, output_root: Path):
    reports = {}
    for label, (package, relative_archive, relative_destination) in PACKAGES.items():
        archive = release_root / relative_archive
        reports[label] = {
            "archive_bytes": archive.stat().st_size,
            "archive_sha256": _sha256(archive),
            "members": _extract(
                archive,
                output_root / relative_destination,
                package,
            ),
        }
    return {
        "schema": "TITAN_V45_RETAINED_WFDB_SCRATCH_STAGE_V1",
        "source_release_manifest_sha256": _sha256(release_root / "release-manifest.json"),
        "packages": reports,
        "only_supported_wfdb_members_staged": True,
        "record_identifiers_in_receipt": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    report = stage(args.release_root, args.output_root)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with args.receipt.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    os.chmod(args.receipt, 0o600)


if __name__ == "__main__":
    main()
