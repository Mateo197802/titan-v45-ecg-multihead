from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from titan_v45.evaluation.revision_report import (
    BinaryPanel,
    binary_metrics,
    build_revision_report,
    cluster_bootstrap,
    write_revision_report,
)

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path("outputs/results/external_dev/evidence")


def test_binary_metrics_use_confusion_denominators_and_tied_score_groups() -> None:
    result = binary_metrics([0, 0, 1, 1], [0, 1, 0, 1], [0.1, 0.4, 0.4, 0.9])
    assert [result[k] for k in ("tp", "tn", "fp", "fn")] == [1, 1, 1, 1]
    assert result["positive_support"] == result["negative_support"] == 2
    assert result["accuracy"] == result["precision"] == result["recall"] == 0.5
    assert result["f1"] == 0.5
    assert result["auroc"] == 0.875
    assert result["average_precision"] == pytest.approx(5 / 6)
    assert result["brier_score"] == pytest.approx(0.135)
    assert result["ece"] == pytest.approx(0.1)


def test_null_probabilities_and_no_positive_classes_are_explicit() -> None:
    result = binary_metrics([0, 0, 0], [0, 0, 0], [0.0, None, 1.0], ece_bins=10)
    assert result["rows"] == 3
    assert result["probability_rows"] == 2
    assert result["missing_probability_rows"] == 1
    assert result["positive_support"] == 0
    assert result["f1"] == 0.0  # Fixed-class macro convention; not silently excluded.
    assert result["recall"] is None
    assert result["auroc"] is None
    assert result["average_precision"] is None
    assert result["brier_score"] == 0.5
    assert result["ece"] == 0.5  # p=1 belongs to the last bin.
    assert result["undefined"]["average_precision"] == "no_positive_probability_rows"
    assert binary_metrics([1], [1], None)["brier_score"] is None
    assert binary_metrics([1, 1], [1, 1], [0.1, 0.9])["average_precision"] == 1.0
    with pytest.raises(ValueError, match="binary"):
        binary_metrics([0, None], [0, 1], None)
    with pytest.raises(ValueError, match="probabilit"):
        binary_metrics([0], [1], [1.1])


def _panel(keys: list[tuple[str, str]], truth: list[int], pred: list[int]) -> BinaryPanel:
    return BinaryPanel(tuple(keys), np.array(truth), np.array(pred))


def test_bootstrap_keeps_dependent_panels_together_instead_of_resampling_rows() -> None:
    # Every ECG has complementary errors across two panels. A joint draw must
    # always have mean panel accuracy .5; independent panel draws need not.
    keys = [("a", "ecg1"), ("a", "ecg2")]
    panels = {
        "A": _panel(keys, [1, 1], [1, 0]),
        "B": _panel(keys, [1, 1], [0, 1]),
    }
    result = cluster_bootstrap(panels, seed=19, n_bootstrap=200)
    assert result["n_clusters"] == 2
    assert result["mean_panel_accuracy"]["low"] == 0.5
    assert result["mean_panel_accuracy"]["high"] == 0.5
    assert result["macro_f1"]["low"] == 0.5
    assert result["macro_f1"]["high"] == pytest.approx(2 / 3)
    assert result == cluster_bootstrap(panels, seed=19, n_bootstrap=200)


def test_bootstrap_keeps_multiple_ecgs_from_one_patient_together() -> None:
    keys = [("source", "ecg1"), ("source", "ecg2")]
    panels = {"A": _panel(keys, [1, 1], [1, 0])}
    result = cluster_bootstrap(
        panels, seed=19, n_bootstrap=200,
        cluster_ids={keys[0]: "patient1", keys[1]: "patient1"},
    )
    assert result["unit"] == "supplied_patient_id"
    assert result["n_clusters"] == 1
    assert result["macro_f1"]["low"] == result["macro_f1"]["high"] == pytest.approx(2 / 3)
    assert result["mean_panel_accuracy"]["low"] == 0.5
    with pytest.raises(ValueError, match="cluster"):
        cluster_bootstrap(panels, cluster_ids={keys[0]: "patient1"})


def test_bootstrap_cluster_identity_is_source_plus_record_and_absent_panels_are_declared() -> None:
    panels = {
        "A": _panel([("a", "same")], [1], [1]),
        "B": _panel([("b", "same")], [0], [0]),
    }
    result = cluster_bootstrap(panels, seed=3, n_bootstrap=100)
    assert result["n_clusters"] == 2
    assert result["macro_f1"]["invalid_replicates"] > 0
    assert result["macro_f1"]["valid_replicates"] > 0
    assert result["macro_f1"]["low"] == result["macro_f1"]["high"] == 0.5
    duplicate = _panel([("a", "same"), ("a", "same")], [1, 1], [1, 1])
    with pytest.raises(ValueError, match="duplicate"):
        cluster_bootstrap({"A": duplicate}, seed=3, n_bootstrap=10)


@pytest.mark.parametrize("kwargs", [{"n_bootstrap": -1}, {"seed": -1}, {"confidence": 1.0}])
def test_invalid_bootstrap_settings_are_rejected(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        cluster_bootstrap({"A": _panel([("s", "1")], [1], [1])}, **kwargs)


@pytest.fixture(scope="module")
def report() -> dict:
    return build_revision_report(ROOT, seed=123, n_bootstrap=60)


def test_saved_evidence_denominators_and_metric_views_are_not_interchanged(report: dict) -> None:
    p6 = report["profiles"]["rhythm_primary6_diagnostic"]
    assert p6["supports"]["rows"] == p6["supports"]["unique_ecgs"] == 1643
    assert p6["accepted_label"]["correct"] == 1564
    assert p6["accepted_label"]["accuracy"] == pytest.approx(1564 / 1643)
    assert p6["binary_panels"]["macro_f1"] == pytest.approx(0.8009383239876123)
    panels = p6["binary_panels"]["classes"]
    assert panels["STACH"]["f1"] == pytest.approx(614 / 677)
    assert panels["RBBB"]["f1"] == pytest.approx(206 / 265)
    assert sum(s["rows"] for s in p6["sources"].values()) == 1643
    assert sum(p["positive_support"] for p in panels.values()) > 1643
    p8 = report["profiles"]["rhythm_primary8"]
    assert p8["accepted_label"]["correct"] == 1987
    assert p8["single_target"]["correct"] == 1870
    assert p8["single_target"]["rows"] == 2193
    assert p8["binary_panels"]["macro_f1"] == pytest.approx(0.7614253535094375)
    assert p8["probability_decision_audit"]["prob_argmax_disagreements"] == 580
    assert p8["binary_panels"]["classes"]["AFIB"]["probability_field"] == "membership_prob_AFIB"
    p4 = report["profiles"]["pathology_primary4"]
    assert p4["supports"] == {"rows": 962, "unique_record_ids": 733, "unique_ecgs": 733}
    assert p4["binary_panels"]["mean_panel_accuracy"] == pytest.approx(0.8022904853689048)
    assert p4["binary_panels"]["macro_f1"] == pytest.approx(0.793456370406346)
    assert p4["binary_panels"]["pooled_accuracy"] == pytest.approx(776 / 962)
    assert p4["binary_panels"]["pooled_accuracy"] != p4["binary_panels"]["mean_panel_accuracy"]
    assert [
        p4["binary_panels"]["classes"][c]["positive_support"]
        for c in ("ASMI", "LVH", "IMI", "ISC_")
    ] == [147, 112, 103, 119]
    assert [p4["binary_panels"]["classes"][c]["rows"] for c in ("ASMI", "LVH", "IMI", "ISC_")] == [
        294,
        224,
        206,
        238,
    ]
    assert p4["bootstrap"]["n_clusters"] == 733
    assert p6["model_contract"]["backbone_sha256"] != p4["model_contract"]["backbone_sha256"]
    assert report["scope"] == "saved_predictions"
    assert report["evidence_classification"] == "repeated_external_development"


def _copy_evidence(tmp_path: Path) -> Path:
    destination = tmp_path / EVIDENCE
    destination.mkdir(parents=True)
    for source in (ROOT / EVIDENCE).glob("*.csv"):
        shutil.copy2(source, destination / source.name)
    return destination


def _rewrite(path: Path, mutate) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        rows = list(reader)
    mutate(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


@pytest.mark.parametrize(
    "mutation", ["duplicate", "truth", "correct", "missing_id", "private_source"]
)
def test_invalid_evidence_fails_without_silent_row_dropping(tmp_path: Path, mutation: str) -> None:
    destination = _copy_evidence(tmp_path)
    path = destination / "rhythm_primary6_record_predictions.csv"

    def mutate(rows):
        if mutation == "duplicate":
            rows.append(rows[0].copy())
        elif mutation == "truth":
            rows[0]["truth_AFIB"] = "True"
        elif mutation == "correct":
            rows[0]["correct"] = "False"
        elif mutation == "missing_id":
            rows[0]["record_id"] = ""
        else:
            rows[0]["source"] = r"C:\Users\Private\data"

    _rewrite(path, mutate)
    with pytest.raises(ValueError):
        build_revision_report(tmp_path, n_bootstrap=0)


def test_missing_scores_are_reported_and_input_fingerprints_change(
    tmp_path: Path, report: dict
) -> None:
    destination = _copy_evidence(tmp_path)
    path = destination / "rhythm_primary6_record_predictions.csv"
    _rewrite(path, lambda rows: rows[0].update(prob_AFIB=""))
    changed = build_revision_report(tmp_path, n_bootstrap=0)
    panel = changed["profiles"]["rhythm_primary6_diagnostic"]["binary_panels"]["classes"]["AFIB"]
    assert panel["rows"] == 1643
    assert panel["probability_rows"] == 1642
    assert panel["missing_probability_rows"] == 1
    name = (EVIDENCE / path.name).as_posix()
    assert (
        changed["integrity"]["inputs"][name]["sha256"]
        != report["integrity"]["inputs"][name]["sha256"]
    )


def test_exports_are_reproducible_complete_and_do_not_leak_private_paths(
    tmp_path: Path, report: dict
) -> None:
    write_revision_report(report, tmp_path / "one")
    write_revision_report(report, tmp_path / "two")
    names = {p.name for p in (tmp_path / "one").iterdir()}
    assert {
        "revision_report.json",
        "revision_report.csv",
        "summary.csv",
        "class_metrics.csv",
        "source_supports.csv",
        "integrity.json",
    } <= names
    for name in names:
        content = (tmp_path / "one" / name).read_bytes()
        assert content == (tmp_path / "two" / name).read_bytes()
        assert str(ROOT).encode() not in content
        assert b"C:\\Users" not in content and b"/home/" not in content
    manifest = json.loads((tmp_path / "one/integrity.json").read_text())
    for name, digest in manifest["output_sha256"].items():
        assert hashlib.sha256((tmp_path / "one" / name).read_bytes()).hexdigest() == digest
    with (tmp_path / "one/revision_report.csv").open(newline="", encoding="utf-8") as handle:
        flat = {row["field"]: json.loads(row["value_json"]) for row in csv.DictReader(handle)}
    assert flat["/profiles/pathology_primary4/supports/unique_ecgs"] == 733
    assert flat["/profiles/pathology_primary4/binary_panels/macro_f1"] == pytest.approx(
        0.793456370406346
    )
    with (tmp_path / "one/summary.csv").open(newline="", encoding="utf-8") as handle:
        summaries = {(row["profile"], row["view"]): row for row in csv.DictReader(handle)}
    p4 = summaries[("pathology_primary4", "binary_panels")]
    assert float(p4["mean_panel_accuracy"]) == pytest.approx(0.8022904853689048)
    assert float(p4["pooled_accuracy"]) == pytest.approx(776 / 962)
    assert int(p4["rows"]) == 962 and int(p4["unique_ecgs"]) == 733
    assert float(
        summaries[("rhythm_primary8", "single_target")]["single_target_accuracy"]
    ) == pytest.approx(1870 / 2193)
    with (tmp_path / "one/source_supports.csv").open(newline="", encoding="utf-8") as handle:
        supports = list(csv.DictReader(handle))
    asmi = next(
        row for row in supports if row["profile"] == "pathology_primary4" and row["class"] == "ASMI"
    )
    assert int(asmi["rows"]) == 294
    assert int(asmi["positive_support"]) == 147


def test_disabled_bootstrap_and_all_missing_probabilities_are_explicit(tmp_path: Path) -> None:
    destination = _copy_evidence(tmp_path)
    path = destination / "pathology_primary4_ASMI_record_predictions.csv"

    def mutate(rows):
        for row in rows:
            row["probability"] = "null"

    _rewrite(path, mutate)
    payload = build_revision_report(tmp_path, n_bootstrap=0)
    p4 = payload["profiles"]["pathology_primary4"]
    assert p4["bootstrap"]["macro_f1"]["low"] is None
    assert p4["bootstrap"]["macro_f1"]["status"] == "disabled"
    panel = p4["binary_panels"]["classes"]["ASMI"]
    assert panel["missing_probability_rows"] == 294
    assert panel["brier_score"] is None
    assert panel["f1"] == pytest.approx(212 / 261)


def test_cli_runs_from_another_directory_and_honors_bootstrap_configuration(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / "scripts/evaluation/build_revision_report.py"),
            "--root",
            str(ROOT),
            "--output-dir",
            str(tmp_path / "metrics"),
            "--seed",
            "17",
            "--n-bootstrap",
            "5",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads((tmp_path / "metrics/revision_report.json").read_text())
    assert payload["configuration"]["seed"] == 17
    assert payload["configuration"]["n_bootstrap"] == 5
    assert (
        payload["profiles"]["pathology_primary4"]["bootstrap"]["macro_f1"]["valid_replicates"] == 5
    )


def test_optional_revision_figures_use_report_metrics_and_are_hashed(
    tmp_path: Path, report: dict
) -> None:
    pytest.importorskip("matplotlib")
    from PIL import Image

    manifest = write_revision_report(report, tmp_path, figures=True)
    assert "matplotlib" in manifest["figure_runtime"]
    for name in ("revision_metrics.png", "revision_metrics.pdf"):
        assert (tmp_path / name).stat().st_size > 5000
        assert (
            hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()
            == manifest["output_sha256"][name]
        )
    with Image.open(tmp_path / "revision_metrics.png") as image:
        pixels = np.asarray(image.convert("RGB"))
        assert image.width >= 1800 and image.height >= 800
        assert float(pixels.std()) > 10


def test_build_is_reproducible_from_the_same_evidence_and_configuration(report: dict) -> None:
    assert build_revision_report(ROOT, seed=123, n_bootstrap=60) == report
