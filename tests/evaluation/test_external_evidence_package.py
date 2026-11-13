"""Test scientific, safety and provenance boundaries of the public delivery."""
import importlib
import io
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/external_evidence"
ZIP = PACKAGE / "TITAN_V45_EXTERNAL_EVIDENCE_PACKAGE.zip"


@pytest.fixture(scope="module")
def scripts():
    import sys

    path = str(ROOT / "scripts/evaluation")
    sys.path.insert(0, path)
    try:
        yield tuple(importlib.import_module(k) for k in ("external_evidence_tables", "verify_external_evidence"))
    finally:
        sys.path.remove(path)


def test_package_extracts_and_offline_reconciles(scripts, tmp_path):
    tables, verifier = scripts
    report = verifier.verify(PACKAGE)
    assert report["primary_models"] == 3
    assert report["endpoints"] == 5
    assert verifier.verify(ZIP) == report
    with ZipFile(ZIP) as z:
        z.extractall(tmp_path)
    assert verifier.verify(tmp_path) == report
    src = verifier.source_snapshot(verifier.read_zip(ZIP.read_bytes()))
    _, macro, comparison, pr = tables.calculate(src)
    assert [round(macro[2][k], 6) for k in (
        "macro_f1", "macro_auroc", "macro_auprc", "mean_binary_accuracy",
    )] == [.602658, .978102, .579463, .983052]
    assert [round(r["macro_f1_delta"], 6) for r in comparison] == [.254696, .232291]
    assert len(pr) == 1515
    assert macro[2]["mean_binary_accuracy_ci_low"] == "NOT_AVAILABLE"


def test_archive_rejects_unapproved_paths_and_symlinks(scripts):
    _, verifier = scripts
    data = verifier.read_zip(ZIP.read_bytes())
    for name in ("../private.csv", "restricted.npz", verifier.MANIFEST):
        stream = io.BytesIO(ZIP.read_bytes())
        if name == verifier.MANIFEST:
            clean = io.BytesIO()
            with ZipFile(clean, "w") as z:
                for member, payload in data.items():
                    info = ZipInfo(member)
                    info.create_system = 3
                    info.external_attr = (0o120777 if member == name else 0o100644) << 16
                    z.writestr(info, payload)
            raw = clean.getvalue()
        else:
            with ZipFile(stream, "a") as z:
                z.writestr(name, "private evidence")
            raw = stream.getvalue()
        with pytest.raises(ValueError, match="unsafe members|member type"):
            verifier.read_zip(raw)


def test_rejects_changed_counts_receipt_and_figure(scripts):
    tables, verifier = scripts
    payload = verifier.read_zip(ZIP.read_bytes())
    figure = "figures/figure_05_observed_precision_recall.svg"
    payload[figure] += b"\n"
    with pytest.raises(ValueError, match="checksum manifest"):
        verifier.verify_payload(payload)
    src = verifier.source_snapshot(payload)
    receipt = "WITHIN_CODE_INDEPENDENT_READBACK.json"
    doc = json.loads(src[receipt])
    doc["status"] = "FAIL"
    src[receipt] = json.dumps(doc).encode()
    with pytest.raises(ValueError, match="private readback receipt"):
        tables.calculate(src)
    with pytest.raises(ValueError, match="denominator"):
        tables.derive_counts({"tp": 56, "tn": 4770, "fp": 51, "fn": 45, "positive_ecgs": 101, "negative_ecgs": 4820})


def test_plot_file_roster_and_resolution(scripts):
    _, verifier = scripts
    for stem in verifier.FIGURES:
        with Image.open(PACKAGE / f"figures/{stem}.png") as p:
            assert 299 < p.info["dpi"][0] < 301
            assert p.width >= 2800
        svg = (PACKAGE / f"figures/{stem}.svg").read_text(encoding="utf-8")
        assert "<image" not in svg
