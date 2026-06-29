from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

TEXT_SUFFIXES = {
    ".cfg", ".csv", ".json", ".md", ".py", ".sh", ".toml", ".txt", ".yaml", ".yml"
}
PATTERNS = {
    "windows_user_path": re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+", re.IGNORECASE),
    "unix_home_path": re.compile("/" + r"home/[^/\s]+/"),
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "github_token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
}


@dataclass(frozen=True)
class PublicationFinding:
    path: str
    line: int
    kind: str


def audit_public_tree(root: str | Path) -> list[PublicationFinding]:
    base = Path(root).resolve()
    findings: list[PublicationFinding] = []
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(base)
        if any(part in {".git", ".venv", "__pycache__", ".pytest_cache"} for part in relative.parts):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, start=1):
            for kind, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append(PublicationFinding(str(relative).replace("\\", "/"), number, kind))
    return findings
