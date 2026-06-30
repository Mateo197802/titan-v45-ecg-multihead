from __future__ import annotations

from titan_v45.cascade.policy import CASCADE_PATHOLOGIES, CASCADE_RHYTHMS, cascade_evidence_role


def test_cascade_is_always_secondary_evidence() -> None:
    assert CASCADE_RHYTHMS == ("Flutter", "LBBB", "2AVB", "3AVB", "LQTS", "Paced")
    assert CASCADE_PATHOLOGIES == ("ALMI", "ILMI", "LAE")
    assert cascade_evidence_role() == "secondary_cascade_annex"
