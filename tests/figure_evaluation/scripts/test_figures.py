from __future__ import annotations

import hashlib
import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_SPEC = spec_from_file_location(
    "generate_manuscript_figures", SCRIPT_DIR / "generate_manuscript_figures.py"
)
if MODULE_SPEC is None or MODULE_SPEC.loader is None:
    raise ImportError("Could not load the figure generator module.")
figures = module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(figures)


@pytest.fixture(scope="module")
def generated_figures(tmp_path_factory):
    output_dir = tmp_path_factory.mktemp("figures")
    manifest = figures.generate_all_figures(
        tables_dir=REPO_ROOT / "tests" / "figure_evaluation" / "tables_snapshot",
        raw_dir=REPO_ROOT / "outputs" / "results" / "external_dev" / "evidence",
        output_dir=output_dir,
    )
    return output_dir, manifest


def test_generate_all_figures_creates_portable_hashed_assets(generated_figures):
    output_dir, manifest = generated_figures
    assert len(manifest) == 19
    ids = [item["id"] for item in manifest]
    assert len(set(ids)) == len(ids)

    for item in manifest:
        assert item["source_files"]
        for source in item["source_files"]:
            source_path = Path(source)
            assert not source_path.is_absolute()
            assert ".." not in source_path.parts
            assert (REPO_ROOT / source_path).is_file(), source
        for format_name in ("png", "pdf", "svg"):
            name = item[format_name]
            assert Path(name).name == name
            path = output_dir / name
            assert path.is_file()
            assert path.stat().st_size > (20_000 if format_name == "png" else 3_000)
            assert hashlib.sha256(path.read_bytes()).hexdigest() == item["artifact_sha256"][format_name]
            if format_name == "svg":
                assert all(
                    line == line.rstrip()
                    for line in path.read_text(encoding="utf-8").splitlines()
                )


def test_png_figures_are_nonblank_and_large_enough(generated_figures):
    output_dir, manifest = generated_figures
    for item in manifest:
        with Image.open(output_dir / item["png"]) as image:
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


def test_attribution_illustration_is_not_claimed_as_gradcam(generated_figures):
    _, manifest = generated_figures
    item = next(item for item in manifest if item["id"] == "fig15_gradcam_contract")
    assert "not a Grad-CAM result" in item["caption"]
    assert "data/fixtures/synthetic/synthetic_ecg_12x1250.csv" in item["source_files"]
    assert not any("HR00191" in source or source.lower().endswith(".mat") for source in item["source_files"])


def test_cli_refuses_to_overwrite_submitted_manuscript_images(monkeypatch):
    from argparse import Namespace

    args = Namespace(
        tables=REPO_ROOT / "tests" / "figure_evaluation" / "tables_snapshot",
        raw=REPO_ROOT / "outputs" / "results" / "external_dev" / "evidence",
        out=REPO_ROOT / "outputs" / "figures",
    )
    monkeypatch.setattr(figures, "parse_args", lambda: args)
    monkeypatch.setattr(figures, "generate_all_figures", lambda *_args: [])

    with pytest.raises(SystemExit, match="Refusing to overwrite"):
        figures.main()
