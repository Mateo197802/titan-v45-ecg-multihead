import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "reviewer_index", ROOT / "scripts/evaluation/export_reviewer_index.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_export_matches_all_48_unique_review_items():
    text = (ROOT / "docs/reviewer_closure/REVIEWER_48_STATUS.md").read_text(encoding="utf-8")
    result = MODULE.parse_index(text)
    assert len(result["items"]) == 48
    published = json.loads((ROOT / "docs/reviewer_closure/REVIEWER_48_STATUS.json").read_text())
    assert result == published
    with pytest.raises(ValueError, match="48 IDs"):
        MODULE.parse_index(text + "\n| R1-1 | duplicate | LIMITED | no |\n")
