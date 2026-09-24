from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath

EXPECTED_MANUSCRIPT_IMAGES = (
    "fig00_ecg_ai_context.png",
    "fig00b_ecg_ai_evolution_gap.png",
    "fig01_graphical_abstract.png",
    "fig02_data_processing_bias_workflow.png",
    "fig03_cascade_contract.png",
    "fig03_internal_architecture.png",
    "fig06_rhythm_confusion.png",
    "fig07_pathology_confusion.png",
    "fig08_class_metrics.png",
    "fig09_roc_curves.png",
    "fig10_precision_recall_curves.png",
    "fig11_calibration.png",
    "fig12_source_performance.png",
    "fig13_error_flows.png",
)
MEDIA_SUFFIXES = {".bmp", ".eps", ".gif", ".jpeg", ".jpg", ".pdf", ".png", ".svg", ".tif", ".tiff", ".webp"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if not header.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"{path} is not a PNG file")
    width, height = struct.unpack(">II", header[16:24])
    if width == 0 or height == 0:
        raise ValueError(f"{path} has invalid dimensions")
    return width, height


def portable_filename(value: object) -> str:
    name = str(value)
    if (
        Path(name).is_absolute()
        or PureWindowsPath(name).is_absolute()
        or PurePosixPath(name).name != name
        or "\\" in name
    ):
        raise ValueError(f"Expected a portable filename, got {name!r}")
    return name


def verify_source_archive(manifest: dict[str, object], archive_path: Path) -> None:
    expected_archive_hash = manifest.get("source_archive_sha256")
    if not isinstance(expected_archive_hash, str) or sha256_file(archive_path) != expected_archive_hash:
        raise SystemExit("Source archive SHA-256 does not match the figure manifest.")

    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        source_tex = str(manifest.get("source_tex", ""))
        if source_tex not in names:
            raise SystemExit(f"Manuscript source is missing from archive: {source_tex}")
        tex = archive.read(source_tex).decode("utf-8")
        references = tuple(
            dict.fromkeys(
                PurePosixPath(match).name
                for match in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex)
            )
        )
        if set(references) != set(EXPECTED_MANUSCRIPT_IMAGES):
            raise SystemExit("Manuscript figure references differ from the expected image list.")
        for item in manifest["assets"]:
            source = str(item["source"])
            path = PurePosixPath(source)
            if path.is_absolute() or ".." in path.parts or "\\" in source:
                raise SystemExit(f"Unsafe source archive path: {source!r}")
            if source not in names:
                raise SystemExit(f"Figure is missing from source archive: {source}")
            if sha256_bytes(archive.read(source)) != item["sha256"]:
                raise SystemExit(f"Figure differs from source archive: {source}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the manuscript image set and hashes.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--figures", type=Path, required=True)
    parser.add_argument("--root", type=Path, help="Repository root used to check tracked media.")
    parser.add_argument("--source-archive", type=Path, help="Optional original ZIP for byte-level comparison.")
    args = parser.parse_args()

    figures_dir = args.figures.resolve()
    manifest_path = args.manifest.resolve()
    repository_root = (args.root or manifest_path.parents[1]).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "TITAN_V45_MANUSCRIPT_IMAGE_MANIFEST_V1":
        raise SystemExit("Unsupported manuscript image manifest schema.")

    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise SystemExit("Manifest assets must be a list.")
    filenames = [portable_filename(item.get("file")) for item in assets]
    if tuple(filenames) != EXPECTED_MANUSCRIPT_IMAGES:
        raise SystemExit("Manifest image list differs from the manuscript references.")

    actual_media = {
        path.name
        for path in figures_dir.iterdir()
        if path.is_file() and path.suffix.lower() in MEDIA_SUFFIXES
    }
    if actual_media != set(EXPECTED_MANUSCRIPT_IMAGES):
        raise SystemExit(
            "Figure directory must contain only the manuscript PNGs; "
            f"missing={sorted(set(EXPECTED_MANUSCRIPT_IMAGES) - actual_media)}, "
            f"extra={sorted(actual_media - set(EXPECTED_MANUSCRIPT_IMAGES))}"
        )

    failures: list[str] = []
    for item in assets:
        name = portable_filename(item.get("file"))
        path = figures_dir / name
        expected_hash = item.get("sha256")
        if not isinstance(expected_hash, str) or sha256_file(path) != expected_hash:
            failures.append(f"{name}: SHA-256 missing or mismatched")
        try:
            png_size(path)
        except (OSError, ValueError) as exc:
            failures.append(f"{name}: {exc}")

    if failures:
        raise SystemExit("\n".join(failures))
    if args.source_archive:
        verify_source_archive(manifest, args.source_archive.resolve())

    print(f"Verified {len(assets)} manuscript PNGs and their SHA-256 hashes.")
    if args.source_archive:
        print("All PNG bytes also match the supplied manuscript archive.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
