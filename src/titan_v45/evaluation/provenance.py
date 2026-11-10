"""Strict provenance checks shared by frozen external-validation runners."""
from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

_SHA256 = re.compile(r"^[0-9a-f]{64}$")

PAC_IMPLEMENTATION_FILES = (
    "docs/external_validation/pac_v3f_embedding_probe.md",
    "scripts/cedia/audit_mimic_pac_source.sbatch",
    "scripts/cedia/audit_mimic_metadata_preflight.sbatch",
    "scripts/cedia/extract_sph_pac_embeddings.sbatch",
    "scripts/cedia/fit_sph_pac_probe.sbatch",
    "scripts/cedia/score_mimic_pac_machine_reports.sbatch",
    "scripts/external_validation/audit_mimic_pac_source.py",
    "scripts/external_validation/extract_sph_v3f_embeddings.py",
    "scripts/external_validation/fit_sph_pac_probe.py",
    "scripts/external_validation/score_mimic_pac_machine_reports.py",
    "src/titan_v45/data/mimic_ecg_reports.py",
    "src/titan_v45/data/mimic_ecg_waveform.py",
    "src/titan_v45/data/sph.py",
    "src/titan_v45/data/sph_waveform.py",
    "src/titan_v45/data/reconstructed.py",
    "src/titan_v45/evaluation/mimic_concordance.py",
    "src/titan_v45/evaluation/pac_probe.py",
    "src/titan_v45/evaluation/provenance.py",
    "src/titan_v45/models/backbone.py",
    "src/titan_v45/models/factory.py",
    "src/titan_v45/models/v3f_embeddings.py",
    "tests/evaluation/test_dependency_provenance.py",
    "tests/evaluation/test_mimic_concordance.py",
    "tests/evaluation/test_mimic_pac_reports.py",
    "tests/evaluation/test_pac_probe.py",
    "tests/evaluation/test_v3f_embeddings.py",
)


def read_required_sha256_environment(
    env_names: Mapping[str, str],
    expected_hashes: Mapping[str, str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return validated dependency archive hashes exported by a CEDIA job."""
    source = os.environ if environ is None else environ
    if not env_names:
        raise ValueError("dependency archive SHA-256 environment mapping is empty")
    if expected_hashes is not None and not set(env_names).issubset(expected_hashes):
        raise ValueError("frozen protocol lacks a required dependency archive hash")
    hashes = {}
    for archive, variable in env_names.items():
        value = source.get(variable)
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise ValueError(f"missing or invalid SHA-256 for dependency archive: {archive}")
        if expected_hashes is not None:
            expected = expected_hashes[archive]
            if not isinstance(expected, str) or not _SHA256.fullmatch(expected):
                raise ValueError(f"invalid frozen dependency archive SHA-256: {archive}")
            if value != expected:
                raise ValueError(f"dependency archive hash differs from the frozen protocol: {archive}")
        hashes[archive] = value
    return hashes


def verify_runtime_versions(
    actual: Mapping[str, str],
    expected: Mapping[str, str],
) -> dict[str, str]:
    """Reject runtime components that do not match the frozen protocol pins."""
    if not actual or set(actual) != set(expected):
        raise ValueError("runtime receipt components differ from the frozen protocol")
    for name, version in actual.items():
        if not isinstance(version, str) or expected.get(name) != version:
            raise ValueError(f"runtime version differs from frozen protocol: {name}")
    return dict(actual)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_implementation_sha256(
    repo: Path,
    hashes: Mapping[str, str],
    required_paths: Sequence[str] = PAC_IMPLEMENTATION_FILES,
) -> dict[str, str]:
    """Require the complete frozen implementation manifest and verify every file."""
    root = Path(repo).resolve(strict=True)
    expected_paths = set(required_paths)
    if not expected_paths or set(hashes) != expected_paths:
        raise ValueError("PAC implementation SHA-256 manifest is incomplete or unexpected")
    verified = {}
    for relative in sorted(expected_paths):
        expected = hashes[relative]
        if not isinstance(expected, str) or not _SHA256.fullmatch(expected):
            raise ValueError(f"invalid PAC implementation SHA-256: {relative}")
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"unsafe PAC implementation path: {relative}")
        candidate = root / relative_path
        if candidate.is_symlink():
            raise ValueError(f"unsafe PAC implementation path: {relative}")
        path = candidate.resolve(strict=True)
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"unsafe PAC implementation path: {relative}")
        actual = _sha256_file(path)
        if actual != expected:
            raise ValueError(f"PAC implementation hash mismatch: {relative}")
        verified[relative] = actual
    return verified

