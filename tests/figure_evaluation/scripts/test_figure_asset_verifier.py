from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify_figure_assets.py")
SPEC = importlib.util.spec_from_file_location("verify_figure_assets", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise ImportError("Could not load the figure asset verifier.")
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


def test_manuscript_media_inventory_is_scoped_to_the_figure_directory(tmp_path: Path) -> None:
    figures = tmp_path / "outputs" / "figures"
    figures.mkdir(parents=True)
    (figures / "paper.png").write_bytes(b"png")
    report_figures = figures / "external_sph"
    report_figures.mkdir()
    (report_figures / "report.png").write_bytes(b"png")

    assert verifier.manuscript_media_names(figures) == {
        "paper.png",
    }


def test_manuscript_media_inventory_detects_extra_top_level_images(tmp_path: Path) -> None:
    figures = tmp_path / "outputs" / "figures"
    figures.mkdir(parents=True)
    (figures / "paper.png").write_bytes(b"png")
    (figures / "unexpected.svg").write_text("svg", encoding="utf-8")

    assert verifier.manuscript_media_names(figures) == {
        "paper.png",
        "unexpected.svg",
    }
