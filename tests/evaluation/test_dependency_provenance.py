import hashlib

import pytest

from titan_v45.evaluation.provenance import (
    read_required_sha256_environment,
    verify_implementation_sha256,
    verify_runtime_versions,
)


def test_dependency_receipt_requires_exact_sha256_values(monkeypatch):
    env_names = {
        "python_deps": "TITAN_PYTHON_DEPS_SHA256",
        "h5py_deps": "TITAN_H5PY_DEPS_SHA256",
    }
    with pytest.raises(ValueError, match="missing or invalid SHA-256"):
        read_required_sha256_environment(env_names)

    python_hash = "a" * 64
    h5py_hash = "b" * 64
    monkeypatch.setenv(env_names["python_deps"], python_hash)
    monkeypatch.setenv(env_names["h5py_deps"], h5py_hash)
    assert read_required_sha256_environment(env_names) == {
        "python_deps": python_hash,
        "h5py_deps": h5py_hash,
    }

    monkeypatch.setenv(env_names["python_deps"], "not-a-hash")
    with pytest.raises(ValueError, match="missing or invalid SHA-256"):
        read_required_sha256_environment(env_names)


def test_dependency_receipt_rejects_archive_hash_not_pinned_by_protocol(monkeypatch):
    env_names = {"python_deps": "TITAN_PYTHON_DEPS_SHA256"}
    monkeypatch.setenv(env_names["python_deps"], "a" * 64)

    with pytest.raises(ValueError, match="differs from the frozen protocol"):
        read_required_sha256_environment(
            env_names, expected_hashes={"python_deps": "b" * 64}
        )


def test_runtime_receipt_rejects_version_mismatch():
    with pytest.raises(ValueError, match="runtime version differs from frozen protocol"):
        verify_runtime_versions(
            {"python": "3.11.13", "torch": "2.10.0+cu128"},
            {"python": "3.11.14", "torch": "2.10.0+cu128"},
        )


def test_runtime_receipt_rejects_missing_frozen_components():
    with pytest.raises(ValueError, match="runtime receipt components differ"):
        verify_runtime_versions(
            {"python": "3.11.14"},
            {"python": "3.11.14", "scipy": "1.15.3"},
        )


def test_implementation_manifest_requires_every_expected_file_and_exact_hash(tmp_path):
    relative = "src/model.py"
    target = tmp_path / relative
    target.parent.mkdir()
    target.write_bytes(b"frozen implementation\n")
    expected = hashlib.sha256(target.read_bytes()).hexdigest()

    assert verify_implementation_sha256(
        tmp_path, {relative: expected}, required_paths=(relative,)
    ) == {relative: expected}

    with pytest.raises(ValueError, match="incomplete or unexpected"):
        verify_implementation_sha256(tmp_path, {}, required_paths=(relative,))
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_implementation_sha256(
            tmp_path, {relative: "0" * 64}, required_paths=(relative,)
        )


def test_implementation_manifest_rejects_paths_outside_repository(tmp_path):
    relative = "../outside.py"
    with pytest.raises(ValueError, match="unsafe PAC implementation path"):
        verify_implementation_sha256(
            tmp_path, {relative: "a" * 64}, required_paths=(relative,)
        )
