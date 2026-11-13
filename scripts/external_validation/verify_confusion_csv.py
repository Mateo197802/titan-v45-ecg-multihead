"""Verify per-class confusion counts and published derived metrics in an aggregate CSV."""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from titan_v45.evaluation.external_metrics import from_confusion


def verify(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = csv.DictReader(stream)
        fields = set(rows.fieldnames or ())
        key_columns = {"profile", "source", "endpoint", "model"}
        confusion_columns = ("tp", "fp", "tn", "fn")
        metric_names = set(from_confusion(0, 0, 0, 0))
        allowed = key_columns | set(confusion_columns) | metric_names
        if fields != allowed or len(rows.fieldnames or ()) != len(allowed):
            raise ValueError("unexpected aggregate schema")
        seen = set()
        for row in rows:
            key = tuple(row[column] for column in sorted(key_columns))
            if key in seen:
                raise ValueError("duplicate aggregate key")
            seen.add(key)
            metrics = from_confusion(*(int(row[column]) for column in confusion_columns))
            for name, expected in metrics.items():
                actual = None if row[name] == "" else float(row[name])
                if actual is None or expected is None:
                    if actual != expected:
                        raise ValueError(f"missing or undefined estimate mismatch: {name}")
                elif not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9):
                    raise ValueError(f"incorrect confusion-derived estimate: {name}")
    if not seen:
        raise ValueError("empty aggregate table")
    return len(seen)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    args = parser.parse_args()
    print(f"verified_aggregate_rows={verify(args.csv)}")
