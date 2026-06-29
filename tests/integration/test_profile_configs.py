from __future__ import annotations

from pathlib import Path

from titan_v45.contracts.config_io import load_profile_config
from titan_v45.contracts.profiles import CANONICAL_PROFILES


def test_disk_profiles_match_python_contracts() -> None:
    root = Path(__file__).resolve().parents[2]
    for name, expected in CANONICAL_PROFILES.items():
        assert load_profile_config(root / "configs" / "profiles" / f"{name}.json") == expected
