from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = (
    ROOT
    / "docs/reviewer_closure/receipts/CEDIA_TARGETED_SACCT_RECONCILIATION_2026-11-10.json"
)
EXPECTED_JOB_IDS = [
    "16781",
    "16782",
    "16783",
    "16785",
    "16786",
    "16816",
    "16819",
    "16887",
    "16903",
    "16904",
    "16906",
    "16914",
    "17296",
    "17314",
    "17315",
]


def test_targeted_sacct_receipt_is_complete_and_sanitized() -> None:
    assert RECEIPT.is_file()
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

    assert receipt["schema"] == "TITAN_V45_TARGETED_SACCT_RECEIPT_V1"
    assert receipt["collection"]["jobs_submitted"] == 0
    assert receipt["collection"]["private_paths_published"] is False
    assert receipt["collection"]["scheduler_timezone"] == "NOT_REPORTED_BY_SACCT"
    assert [job["job_id"] for job in receipt["jobs"]] == EXPECTED_JOB_IDS

    for job in receipt["jobs"]:
        assert job["state"] == "COMPLETED"
        assert job["exit_code"] == "0:0"
        assert job["submit_line_bytes"] > 0
        assert re.fullmatch(r"[0-9a-f]{64}", job["submit_line_sha256"])

    by_id = {job["job_id"]: job for job in receipt["jobs"]}
    assert by_id["16781"]["submission_paths_declared"] is True
    assert by_id["16781"]["checked_paths_status"].startswith("REFERENCED_")
    assert by_id["16782"]["declared_input_categories"] == [
        "fine_tuned_base_checkpoint_from_job_16781",
        "rhythm_train_manifest",
        "rhythm_validation_manifest",
        "pathology_train_manifest",
        "pathology_panel_index",
    ]
    assert by_id["16785"]["submission_paths_declared"] is False

    retained = receipt["retained_artifacts"]
    assert retained["17296_stdout"]["sha256"] == (
        "1f0b29540c84cb68a5719e74e02ce3c58a1a4c38da66a8b39c9862913d2b18e8"
    )
    assert retained["17314_stdout"]["sha256"] == (
        "19df83ca78f0688a99e06a967611e04b4f308d0fd5a1af8df1bdd3efe144452e"
    )
    assert retained["17315_stdout"]["sha256"] == (
        "74e03a97067b176c758c2c28b2faf0888c0bb555eb6a20a732b05f81385d43ec"
    )

    serialized = json.dumps(receipt, ensure_ascii=True)
    assert "/home/" not in serialized
    assert not re.search(r"[A-Za-z]:\\Users\\", serialized)
