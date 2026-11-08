import pytest

from scripts.external_validation.normalize_sph_aggregate import normalize_report
from scripts.external_validation.plot_sph_aggregate import plot_sph_aggregate
from scripts.external_validation.plot_sph_aggregate_corrected import plot_corrected


def _metric(value):
    return value, {"low": value - 0.1, "high": value + 0.1}


def _report():
    endpoints = {}
    profiles = {name: {"coverage": 0.75, "scored_records": 3, "source_records": 4}
                for name in ("P6", "P8", "P4")}
    for profile in ("P6", "P8", "P4"):
        point, ci = _metric(0.8)
        endpoints[f"{profile}:TEST"] = {
            "scored_positive": 1,
            "scored_negative": 2,
            "metrics": {"sensitivity": point, "specificity": point, "auroc": point, "f1": point},
            "cluster_bootstrap_ci95": {
                "sensitivity": ci, "specificity": ci, "auroc": ci, "f1": ci,
            },
            "discordant_exact_duplicate_sensitivity": {
                "metrics": {"f1": 0.7},
                "cluster_bootstrap_ci95": {"f1": {"low": 0.6, "high": 0.8}},
            },
        }
    return {
        "schema": "TITAN_V45_SPH_ENDPOINT_RESULTS_V1",
        "full_population_flow": {
            "source_metadata_records": 4,
            "archive_records": 4,
            "technical_exclusions": 0,
            "inference_failures": 1,
            "missing_signal": 0,
        },
        "profile_flow": profiles,
        "endpoints": endpoints,
    }


def test_aggregate_plotter_writes_fixed_privacy_safe_figures(tmp_path):
    pytest.importorskip("matplotlib")
    result = plot_sph_aggregate(_report(), tmp_path)

    assert result["matplotlib_version"]
    assert set(result["files"]) == {
        "sph_profile_coverage.png", "sph_profile_coverage.pdf",
        "sph_endpoint_metrics.png", "sph_endpoint_metrics.pdf",
        "sph_duplicate_sensitivity.png", "sph_duplicate_sensitivity.pdf",
    }
    assert all((tmp_path / name).stat().st_size > 0 for name in result["files"])


def test_aggregate_plotter_rejects_nonaggregate_input(tmp_path):
    with pytest.raises(ValueError, match="schema"):
        plot_sph_aggregate({"schema": "private-ledger"}, tmp_path)


def test_frozen_aggregate_metric_names_normalize_before_plotting(tmp_path):
    pytest.importorskip("matplotlib")
    report = _report()
    for endpoint in report["endpoints"].values():
        endpoint["metrics"].pop("sensitivity")
        endpoint["metrics"].update({"tn": 8, "fp": 2, "fn": 3, "tp": 7, "recall": 0.7})
        endpoint["discordant_exact_duplicate_sensitivity"]["metrics"].update(
            {"tn": 8, "fp": 2, "fn": 3, "tp": 7, "recall": 0.7}
        )
    normalized = normalize_report(report, "a" * 64)
    assert normalized["endpoints"]["P6:TEST"]["metrics"]["sensitivity"] == 0.7
    assert len(plot_corrected(normalized, tmp_path)["files"]) == 6


def test_corrected_plot_preserves_interval_excluding_point(tmp_path, monkeypatch):
    pytest.importorskip("matplotlib")
    report = _report()
    for endpoint in report["endpoints"].values():
        endpoint["cluster_bootstrap_ci95"]["sensitivity"] = {"low": 0.85, "high": 0.95}
    from matplotlib.axes import Axes

    intervals = []
    original = Axes.hlines

    def capture(axis, y, xmin, xmax, *args, **kwargs):
        intervals.append((xmin, xmax))
        return original(axis, y, xmin, xmax, *args, **kwargs)

    monkeypatch.setattr(Axes, "hlines", capture)
    plot_corrected(report, tmp_path)
    assert any(low == pytest.approx(0.85) and high == pytest.approx(0.95) for low, high in intervals)


def test_corrected_plot_preserves_endpoint_labels_on_shared_axes(tmp_path, monkeypatch):
    plt = pytest.importorskip("matplotlib.pyplot")
    figures = []
    with monkeypatch.context() as context:
        context.setattr(plt, "close", lambda figure: figures.append(figure))
        plot_corrected(_report(), tmp_path)
    endpoint_figure = figures[1]
    labels = [label.get_text() for label in endpoint_figure.axes[0].get_yticklabels()]
    assert labels == ["P6:TEST  (+1/-2)", "P8:TEST  (+1/-2)", "P4:TEST  (+1/-2)"]
    for figure in figures:
        plt.close(figure)


def test_corrected_plot_notes_and_legend_do_not_overlap_axes(tmp_path, monkeypatch):
    plt = pytest.importorskip("matplotlib.pyplot")
    figures = []
    with monkeypatch.context() as context:
        context.setattr(plt, "close", lambda figure: figures.append(figure))
        plot_corrected(_report(), tmp_path)
    coverage, duplicate = figures[0], figures[2]
    assert "Metadata" in coverage.axes[0].get_xlabel()
    assert not coverage.texts
    axis = duplicate.axes[0]
    assert "Endpoint-specific exclusion" in axis.get_xlabel()
    renderer = duplicate.canvas.get_renderer()
    assert duplicate.bbox.contains(*axis.title.get_window_extent(renderer).get_points()[1])
    assert not axis.get_legend().get_window_extent(renderer).overlaps(axis.get_window_extent(renderer))
    assert not axis.get_legend().get_window_extent(renderer).overlaps(axis.xaxis.label.get_window_extent(renderer))
    for figure in figures:
        plt.close(figure)
