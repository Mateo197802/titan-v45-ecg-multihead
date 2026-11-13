import json
from pathlib import Path

import pytest

from scripts.benchmarkmax.plot_sph_baseline import render

ROOT = Path(__file__).resolve().parents[2]


def test_benchmark_figures_are_generated_only_from_aggregate(tmp_path):
    pytest.importorskip("matplotlib")
    report = json.loads((ROOT / "outputs/results/benchmarkmax/sph_baseline_diagnostic_32726.json")
                        .read_text(encoding="utf-8"))
    names = render(report, tmp_path)
    assert set(names) == {f"sph_baseline_{stem}.{suffix}"
                          for stem in ("roc", "pr", "calibration", "score_distributions")
                          for suffix in ("png", "pdf")}
    assert all((tmp_path / name).stat().st_size > 1000 for name in names)
    with pytest.raises(ValueError, match="aggregate"):
        render({"schema": "individual-ledger"}, tmp_path)
