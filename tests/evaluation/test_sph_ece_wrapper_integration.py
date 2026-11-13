import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / "scripts/external_validation/evaluate_sph_ece_corrected.py"


def test_wrapper_runs_frozen_evaluator_and_writes_traceable_receipt(tmp_path):
    repo = tmp_path / "frozen"
    evaluator = repo / "scripts/external_validation/evaluate_sph_ledger.py"
    evaluator.parent.mkdir(parents=True)
    evaluator.write_text(
        "import argparse, json\n"
        "from titan_v45.evaluation.sph_report import _metric_values\n"
        "p=argparse.ArgumentParser(); p.add_argument('--output'); p.add_argument('--receipt-output'); "
        "a,_=p.parse_known_args()\n"
        "m=_metric_values([0,1,0,1,1,0],[0,1,1,0,1,0],"
        "[.1,.8,.8,.3,.7,.2],[1]*6,10)\n"
        "open(a.output,'w').write(json.dumps(m))\n"
        "open(a.receipt_output,'w').write(json.dumps({'synthetic':True}))\n",
        encoding="utf-8",
    )
    aggregate, receipt, correction = (tmp_path / name for name in ("a.json", "r.json", "c.json"))
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    subprocess.run(
        [sys.executable, str(WRAPPER), "--repo", str(repo), "--output", str(aggregate),
         "--receipt-output", str(receipt), "--correction-receipt", str(correction)],
        check=True, env=environment, capture_output=True, text=True,
    )
    assert json.loads(aggregate.read_text())["ece"] == pytest.approx(0.25)
    trace = json.loads(correction.read_text())
    assert trace["wrapper_sha256"] == hashlib.sha256(WRAPPER.read_bytes()).hexdigest()
    assert trace["frozen_evaluator_sha256"] == hashlib.sha256(evaluator.read_bytes()).hexdigest()
    assert trace["aggregate_sha256"] == hashlib.sha256(aggregate.read_bytes()).hexdigest()
    assert trace["frozen_evaluator_receipt_sha256"] == hashlib.sha256(receipt.read_bytes()).hexdigest()
