from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ci_installs_declared_development_requirements() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    requirements = (ROOT / "requirements" / "requirements-dev.txt").read_text(encoding="utf-8")
    assert "python -m pip install -r requirements/requirements-dev.txt" in workflow
    assert ".[data,optuna,dev]" in requirements
