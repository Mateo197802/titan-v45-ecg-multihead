from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

TEXT_SUFFIXES = {
    ".cfg", ".csv", ".json", ".md", ".py", ".sh", ".toml", ".txt", ".yaml", ".yml"
}
PRIVATE_PATTERNS = {
    "windows_user_path": re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+", re.IGNORECASE),
    "unix_home_path": re.compile("/" + r"home/[^/\s]+/"),
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "github_token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
}
PUBLIC_COPY_PATTERNS = {
    "legacy_label_1": re.compile(r"\b" + "NO" + r"_PASA\b"),
    "legacy_label_2": re.compile(r"\b" + "PASA" + r"_METRICA\b"),
    "internal_acceptance_label": re.compile(
        r"\b" + "ACEP" + r"TADO_POR_DECI" + r"SION_DEL_PROYECTO\b"
    ),
    "legacy_contract_field": re.compile(r"\b" + "canonical" + r"_stat" + r"us\b"),
    "external_final_phrase": re.compile(r"external[- ]final", re.IGNORECASE),
    "metric_boundary_phrase": re.compile(r"metric[-_ ]?" + "ga" + r"te", re.IGNORECASE),
    "accuracy_boundary_phrase": re.compile(r"accuracy " + "ga" + r"te", re.IGNORECASE),
    "internal_decision_phrase": re.compile(r"project " + "deci" + r"sion", re.IGNORECASE),
    "project_acceptance_phrase": re.compile(r"project[- ]acceptance", re.IGNORECASE),
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
        if any(part in {".git", ".venv", "__pycache__", ".pytest_cache", "tmp"} for part in relative.parts):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, start=1):
            patterns = dict(PRIVATE_PATTERNS)
            if relative.as_posix() != "src/titan_v45/artifacts/publication_audit.py":
                patterns.update(PUBLIC_COPY_PATTERNS)
            for kind, pattern in patterns.items():
                if pattern.search(line):
                    findings.append(PublicationFinding(str(relative).replace("\\", "/"), number, kind))
    return findings
