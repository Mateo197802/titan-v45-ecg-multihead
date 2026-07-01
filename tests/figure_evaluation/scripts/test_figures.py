from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image
import pytest

import figures


@pytest.fixture(scope="module")
def generated_figures(tmp_path_factory, raw_dir):
    manuscript_root = raw_dir.parents[1]
    output_dir = tmp_path_factory.mktemp("figures")
    manifest = figures.generate_all_figures(
        tables_dir=manuscript_root / "tables",
        raw_dir=raw_dir,
        output_dir=output_dir,
    )
    return output_dir, manifest


def test_generate_all_figures_creates_publication_assets(generated_figures):
    _, manifest = generated_figures
    assert len(manifest) >= 12
    for item in manifest:
        for format_name in ("png", "pdf", "svg"):
            path = Path(item[format_name])
            assert path.exists()
            assert path.stat().st_size > (20_000 if format_name == "png" else 3_000)


def test_png_figures_are_nonblank_and_large_enough(generated_figures):
    _, manifest = generated_figures
    for item in manifest:
        with Image.open(item["png"]) as image:
            assert image.width >= 1800
            assert image.height >= 900
            pixels = np.asarray(image.convert("RGB"))
            assert float(pixels.std()) > 8.0


def test_probability_figures_are_evidence_gated(generated_figures):
    output_dir, _ = generated_figures
    manifest = json.loads((output_dir / "figure_manifest.json").read_text(encoding="utf-8"))
    probability_kinds = {"roc", "precision_recall", "calibration"}
    for item in manifest:
        if item["kind"] in probability_kinds:
            assert item["sample_probabilities_verified"] is True
            assert item["source_files"]
