from __future__ import annotations

CASCADE_RHYTHMS = ("Flutter", "LBBB", "2AVB", "3AVB", "LQTS", "Paced")
CASCADE_PATHOLOGIES = ("ALMI", "ILMI", "LAE")


def cascade_evidence_role() -> str:
    return "secondary_safety_annex"
