from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/benchmarkmax/analyze_prevalence_shift.py"
spec = importlib.util.spec_from_file_location("prevalence_shift", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_projection_agrees_with_observed_frozen_counts():
    source = json.loads((ROOT / "outputs/results/benchmarkmax/sph_baseline_diagnostic_32726.json").read_text())
    output = module.analyze(source)
    assert len(output["endpoints"]) == 5
    for item in output["endpoints"].values():
        assert math.isclose(item["observed_ppv"], item["projected_ppv_at_observed_prevalence"], abs_tol=1e-12)
        assert len(item["scenarios"]) == 7


def test_prevalence_bounds_and_zero_denominator():
    assert module.project_ppv(0, 0.8, 0.9) == 0
    assert module.project_ppv(1, 0.8, 0.9) == 1
    assert module.project_ppv(0, 1, 1) is None
    with pytest.raises(ValueError):
        module.project_ppv(-0.1, 0.8, 0.9)
    with pytest.raises(ValueError):
        module.analyze({"schema": "wrong"})


def test_rejects_inconsistent_population():
    source = json.loads((ROOT / "outputs/results/benchmarkmax/sph_baseline_diagnostic_32726.json").read_text())
    source["endpoints"]["P4:LVH"]["frozen_decisions"]["fn"] += 1
    with pytest.raises(ValueError, match="population"):
        module.analyze(source)


def test_published_projection_recomputes_from_aggregates():
    source_path = ROOT / "outputs/results/benchmarkmax/sph_baseline_diagnostic_32726.json"
    report_path = ROOT / "outputs/results/benchmarkmax/sph_prevalence_projection_v1.json"
    source = source_path.read_bytes()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report.pop("source_sha256") == hashlib.sha256(source).hexdigest()
    assert report.pop("script_sha256") == hashlib.sha256(SCRIPT.read_bytes()).hexdigest()
    assert report == module.analyze(json.loads(source))
