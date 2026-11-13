from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def rows(name):
    path = ROOT / "data/manifests/external_dev" / name
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_selected_denominators_do_not_double_count_p6():
    p6 = rows("rhythm_primary6_diagnostic_records.csv")
    p8 = rows("rhythm_primary8_records.csv")
    p4 = rows("pathology_primary4_panels.csv")
    p6_ids = {row["record_id"] for row in p6}
    p8_ids = {row["record_id"] for row in p8}
    p4_ids = {row["record_id"] for row in p4}
    assert len(p6) == len(p6_ids) == 1643
    assert len(p8) == len(p8_ids) == 2193
    assert p6_ids <= p8_ids
    assert len(p4) == 962
    assert len(p4_ids) == 733
    fold = json.loads((ROOT / "outputs/results/revision_replay_diagnostics_20261107/p4_official_fold_coverage.json").read_text())
    assert fold["selected_p4"] == {"ecgs": 733, "patients": 676, "panel_observations": 962}
    assert fold["historical_parent_population_recovered"] is False
    assert fold["historical_exclusion_reasons_known"] is False
    assert fold["historical_checkpoint_training_isolation_established"] is False


def test_r1_2_closure_discloses_scope_and_reopening_conditions():
    text = (ROOT / "docs/reviewer_closure/R1_2_EVIDENCE_CEILING.md").read_text(encoding="utf-8")
    for required in ("EVIDENCE_CEILING_REACHED", "1,643", "2,193", "962", "733", "676",
                     "17296", "v3m_internal_val_p4_panel_index.json", "not evidence of editorial acceptance"):
        assert required in text
