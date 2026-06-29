from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import tarfile
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.artifacts.manifest import sha256_file, verify_artifact_manifest
from titan_v45.contracts.profiles import CANONICAL_PROFILES
from titan_v45.evaluation.primary import evaluate_primary_predictions
from titan_v45.models.bundle import load_profile_bundle

PRIVATE_PATH = re.compile(r"(?:[A-Za-z]:[\\/]+Users[\\/]+|/" + r"home/[^/\s]+/)")
BACKBONE_PARAMETER_COUNT = 58_352_219


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_tar_zst(archive: Path, destination: Path) -> None:
    import zstandard as zstd

    destination.mkdir(parents=True, exist_ok=True)
    temporary_tar = destination / (archive.name + ".tmp.tar")
    try:
        with archive.open("rb") as src, temporary_tar.open("wb") as dst:
            zstd.ZstdDecompressor().copy_stream(src, dst)
        with tarfile.open(temporary_tar, mode="r") as handle:
            destination_resolved = destination.resolve()
            for member in handle.getmembers():
                target = (destination / member.name).resolve()
                if not target.is_relative_to(destination_resolved):
                    raise RuntimeError(f"archive member escapes destination: {member.name}")
            handle.extractall(destination)
    finally:
        temporary_tar.unlink(missing_ok=True)


def _dataset_package_report(root: Path) -> dict[str, Any]:
    package_manifests = sorted(root.rglob("package-manifest.json"))
    if len(package_manifests) != 1:
        raise RuntimeError(f"expected one package-manifest.json under {root}, found {len(package_manifests)}")
    payload = _read_json(package_manifests[0])
    scanned_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in package_manifests[0].parent.rglob("*")
        if path.is_file() and path.suffix.lower() in {".csv", ".json", ".md"}
    )
    if PRIVATE_PATH.search(scanned_text):
        raise RuntimeError(f"private path residue in extracted package: {root}")
    return {
        "rows": payload["rows"],
        "unique_records": payload["unique_records"],
        "file_count": len(payload["files"]),
        "licenses": payload.get("licenses", []),
        "package_manifest_sha256": sha256_file(package_manifests[0]),
    }


def _top1_from_csv(path: Path, profile_name: str, true_column: str, pred_column: str) -> dict[str, Any]:
    profile = CANONICAL_PROFILES[profile_name]
    rows = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
    index = {name: position for position, name in enumerate(profile.classes)}
    y_true = np.asarray([index[row[true_column]] for row in rows])
    y_pred = np.asarray([index[row[pred_column]] for row in rows])
    report = evaluate_primary_predictions(
        y_true=y_true,
        y_pred=y_pred,
        classes=profile.classes,
        scope="external_dev",
    )
    report["rows"] = len(rows)
    return report


def _p6_diagnostic_from_csv(root: Path) -> dict[str, Any]:
    path = root / "outputs/results/external_dev/evidence/rhythm_primary6_record_predictions.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
    correct_count = sum(str(row["correct"]).lower() == "true" for row in rows)
    canonical = _read_json(root / "outputs/results/external_dev/rhythm_primary6_metrics.json")
    accuracy = correct_count / len(rows)
    if abs(accuracy - float(canonical["top1_accuracy"])) > 1e-12:
        raise RuntimeError(
            f"Primary6 accuracy mismatch: recomputed {accuracy}, canonical {canonical['top1_accuracy']}"
        )
    return {
        "scope": "external_dev",
        "rows": len(rows),
        "correct": correct_count,
        "accuracy": accuracy,
        "macro_f1": canonical["binary_macro_f1"],
        "canonical_status": canonical["status"],
        "claim_boundary": "Diagnostic Primary6 without NSR/PAC; not a Primary8 result.",
    }


def _p8_from_csv(root: Path) -> dict[str, Any]:
    diagnostic = _top1_from_csv(
        root / "outputs/results/external_dev/evidence/rhythm_primary8_record_predictions.csv",
        "rhythm_primary8",
        "target_label",
        "predicted_label",
    )
    canonical = _read_json(root / "outputs/results/external_dev/rhythm_primary8_metrics.json")
    return {
        "scope": "external_dev",
        "records": canonical["records"],
        "top1_accepted_accuracy": canonical["top1_accepted_accuracy"],
        "binary_panel_macro_f1": canonical["binary_panel_macro_f1"],
        "canonical_status": canonical["status"],
        "diagnostic_single_target": {
            "accuracy": diagnostic["accuracy"],
            "macro_f1": diagnostic["macro_f1"],
            "rows": diagnostic["rows"],
        },
        "claim_boundary": "Primary8 does not pass its full accuracy gate.",
    }


def _load_bundles(root: Path) -> dict[str, Any]:
    paths = {
        "v3f": root / "outputs/models/backbones/backbone-v3f-original.pt",
        "p6": root / "outputs/models/specialists/rhythm/specialists-v3p-e008-primary6-diagnostic.pt",
        "p8": root / "outputs/models/specialists/rhythm/specialists-v3q-primary8-best-candidate.pt",
        "v3ag": root / "outputs/models/backbones/backbone-v3ag-pathology.pt",
        "p4": root / "outputs/models/specialists/pathology/specialists-v3ag-primary4-calibrated.pt",
    }
    contracts = {
        name: {
            "profile": profile.name,
            "task": profile.task,
            "classes": list(profile.classes),
            "artifact_classes": list(profile.artifact_classes),
            "backbone_rhythm_classes": list(profile.backbone_rhythm_classes),
            "backbone_pathology_classes": list(profile.backbone_pathology_classes),
            "thresholds": list(profile.thresholds),
            "backbone_sha256": profile.backbone_sha256,
            "specialist_sha256": profile.specialist_sha256,
            "backbone_parameter_count": BACKBONE_PARAMETER_COUNT,
        }
        for name, profile in CANONICAL_PROFILES.items()
    }
    loaded = {}
    loaded["rhythm_primary8"] = load_profile_bundle(
        CANONICAL_PROFILES["rhythm_primary8"],
        paths["v3f"],
        paths["p8"],
        contracts["rhythm_primary8"],
    ).specialist_architecture.__dict__
    loaded["rhythm_primary6_diagnostic"] = load_profile_bundle(
        CANONICAL_PROFILES["rhythm_primary6_diagnostic"],
        paths["v3f"],
        paths["p6"],
        contracts["rhythm_primary6_diagnostic"],
    ).specialist_architecture.__dict__
    loaded["pathology_primary4"] = load_profile_bundle(
        CANONICAL_PROFILES["pathology_primary4"],
        paths["v3ag"],
        paths["p4"],
        contracts["pathology_primary4"],
    ).specialist_architecture.__dict__
    return loaded


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CEDIA release reproducibility verification.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--extract-root", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = _read_json(root / "release-manifest.json")
    verify_artifact_manifest(root, manifest["artifacts"])
    extract_root = (args.extract_root or root / "data/external_dev/extracted").resolve()
    rhythm_extract = extract_root / "rhythm"
    pathology_extract = extract_root / "pathology"
    _extract_tar_zst(
        root / "data/external_dev/rhythm/external-dev-rhythm-chapman-shaoxing.tar.zst",
        rhythm_extract,
    )
    _extract_tar_zst(
        root / "data/external_dev/pathology/external-dev-pathology-ptbxl-fold10.tar.zst",
        pathology_extract,
    )
    p8 = _p8_from_csv(root)
    p6 = _p6_diagnostic_from_csv(root)
    payload = {
        "schema": "TITAN_V45_CEDIA_REPRODUCIBILITY_REPORT_V1",
        "status": "passed",
        "execution_root": "release_checkout",
        "release_tag": manifest["tag"],
        "release_assets": {
            asset["name"]: {"bytes": asset["bytes"], "sha256": asset["sha256"]}
            for asset in manifest["assets"]
        },
        "loaded_bundles": _load_bundles(root),
        "datasets": {
            "rhythm": _dataset_package_report(rhythm_extract),
            "pathology": _dataset_package_report(pathology_extract),
        },
        "metrics": {
            "rhythm_primary8": p8,
            "rhythm_primary6_diagnostic": p6,
            "pathology_primary4": _read_json(
                root / "outputs/results/external_dev/pathology_primary4_metrics.json"
            ),
        },
        "claim_boundary": "External-development verification; not an untouched external-final claim.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
