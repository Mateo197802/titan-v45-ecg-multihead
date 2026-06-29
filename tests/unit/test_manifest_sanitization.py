from __future__ import annotations

import pytest

from titan_v45.data.manifests import LeakageError, sanitize_record_path, validate_no_overlap


def test_sanitize_record_path_removes_local_and_remote_roots() -> None:
    windows = "C:" + r"\Users\someone\project\DATA\ptb-xl\records100\00001_lr"
    remote = "/home/" + "user/project/DATA/chapman_shaoxing/WFDBRecords/01/010/A0001"
    assert sanitize_record_path(windows) == "ptb-xl/records100/00001_lr"
    assert sanitize_record_path(remote) == "chapman_shaoxing/WFDBRecords/01/010/A0001"


def test_validate_no_overlap_rejects_shared_records() -> None:
    with pytest.raises(LeakageError, match="record-2"):
        validate_no_overlap({"record-1", "record-2"}, {"record-2", "record-3"})


def test_validate_no_overlap_accepts_disjoint_records() -> None:
    validate_no_overlap({"record-1"}, {"record-2"})
