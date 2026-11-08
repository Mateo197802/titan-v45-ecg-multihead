import json
from pathlib import Path

from scripts.external_validation.render_sph_results import render

ROOT = Path(__file__).resolve().parents[2]


def test_results_table_matches_published_aggregate():
    report = json.loads((ROOT / "outputs/results/external_sph/sph_aggregate_normalized_32669.json")
                        .read_text(encoding="utf-8"))
    expected = render(report)
    assert (ROOT / "docs/external_validation/sph_results.md").read_text(encoding="utf-8") == expected
    for endpoint in report["endpoints"]:
        assert f"| {endpoint} |" in expected
    assert "25,770 / 25,770" in expected
    assert "not adjudicated absence of disease" in expected
