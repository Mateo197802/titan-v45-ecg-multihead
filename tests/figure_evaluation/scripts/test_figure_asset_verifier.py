from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify_figure_assets.py")
SPEC = importlib.util.spec_from_file_location("verify_figure_assets", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise ImportError("Could not load the figure asset verifier.")
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


def test_repository_media_inventory_includes_assets_outside_figures(tmp_path: Path) -> None:
    figures = tmp_path / "outputs" / "figures"
    figures.mkdir(parents=True)
    (figures / "paper.png").write_bytes(b"png")
    (tmp_path / "other" / "diagram.svg").parent.mkdir()
    (tmp_path / "other" / "diagram.svg").write_text("svg", encoding="utf-8")

    assert verifier.repository_media_paths(tmp_path) == {
        "outputs/figures/paper.png",
        "other/diagram.svg",
    }
