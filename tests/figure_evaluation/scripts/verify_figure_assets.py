from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


EXPECTED_RESULT_FIGURES = {
    "fig04_optuna",
    "fig05_training_curves",
    "fig06_rhythm_confusion",
    "fig07_pathology_confusion",
    "fig08_class_metrics",
    "fig09_roc_curves",
    "fig10_precision_recall_curves",
    "fig11_calibration",
    "fig12_source_performance",
    "fig13_error_flows",
    "fig14_uncertainty_profile",
    "fig15_gradcam_contract",
}

EXPECTED_METHOD_FIGURES = {
    "fig00_ecg_ai_context",
    "fig00b_ecg_ai_evolution_gap",
    "fig01_graphical_abstract",
    "fig02_data_processing_bias_workflow",
    "fig03_internal_architecture",
    "fig03_cascade_contract",
}


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if not header.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"{path} is not a PNG file")
    return struct.unpack(">II", header[16:24])


def path_from_manifest(figures_dir: Path, item: dict[str, object], key: str) -> Path:
    value = Path(str(item[key]))
    return figures_dir / value.name


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify manuscript figure assets.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--figures", type=Path, required=True)
    parser.add_argument("--min-width", type=int, default=1200)
    parser.add_argument("--min-height", type=int, default=600)
    args = parser.parse_args()

    figures_dir = args.figures.resolve()
    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    ids = {str(item["id"]) for item in manifest}

    missing_expected = (EXPECTED_RESULT_FIGURES | EXPECTED_METHOD_FIGURES) - ids
    if missing_expected:
        raise SystemExit(f"Missing expected figure ids: {sorted(missing_expected)}")

    failures: list[str] = []
    for item in manifest:
        figure_id = str(item["id"])
        for key in ("png", "pdf", "svg"):
            path = path_from_manifest(figures_dir, item, key)
            if not path.exists():
                failures.append(f"{figure_id}: missing {key} asset {path.name}")
                continue
            minimum_size = 20_000 if key == "png" else 3_000
            if path.stat().st_size < minimum_size:
                failures.append(f"{figure_id}: {key} asset is too small")

        png_path = path_from_manifest(figures_dir, item, "png")
        if png_path.exists():
            width, height = png_size(png_path)
            if width < args.min_width or height < args.min_height:
                failures.append(
                    f"{figure_id}: PNG dimensions {width}x{height} below "
                    f"{args.min_width}x{args.min_height}"
                )

    if failures:
        raise SystemExit("\n".join(failures))

    print(
        f"Verified {len(manifest)} manuscript figure assets in {figures_dir} "
        f"against {manifest_path.name}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
