import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def plan(rows, classes, allowed):
    tree = ast.parse((ROOT / "scripts/cedia/forensic_replay_primary4.py").read_bytes())
    function = next((node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name == "build_source_backed_panel_plan"), None)
    assert function is not None, "source-backed panel plan is missing"
    namespace = {"Path": Path}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "replay-plan", "exec"), namespace)
    return namespace[function.name](rows, classes, allowed)


def test_replays_overlapping_ecgs_separately_in_each_historical_panel():
    rows = [{"record_id": "b", "record_base": "root/b/b", "pathology": "LVH", "target": 1},
            {"record_id": "a", "record_base": "root/a/a", "pathology": "LVH", "target": 0},
            {"record_id": "a", "record_base": "root/a/a", "pathology": "ASMI", "target": 1}]
    expected = [("ASMI", [("a", "root/a/a")]), ("LVH", [("a", "root/a/a"), ("b", "root/b/b")])]
    assert plan(rows, ["ASMI", "LVH"], {"a", "b"}) == expected
    for row in rows:
        row["target"] = 1 - row["target"]
    assert plan(rows, ["ASMI", "LVH"], {"a", "b"}) == expected


def test_limit_is_explicit_and_does_not_change_panel_membership():
    rows = [{"record_id": "a", "record_base": "root/a/a", "pathology": "ASMI"},
            {"record_id": "b", "record_base": "root/b/b", "pathology": "ASMI"}]
    assert plan(rows, ["ASMI"], {"a"}) == [("ASMI", [("a", "root/a/a")])]


def test_duplicate_record_within_panel_is_rejected():
    row = {"record_id": "a", "record_base": "root/a/a", "pathology": "ASMI"}
    with pytest.raises(ValueError, match="duplicate"):
        plan([row, row], ["ASMI"], {"a"})


def test_ambiguous_shared_directory_order_is_not_invented():
    rows = [{"record_id": "a", "record_base": "root/a", "pathology": "ASMI"},
            {"record_id": "b", "record_base": "root/b", "pathology": "ASMI"}]
    with pytest.raises(ValueError, match="directory"):
        plan(rows, ["ASMI"], {"a", "b"})
