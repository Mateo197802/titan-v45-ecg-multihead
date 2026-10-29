"""Offline content-identity audit of caller-supplied fingerprints and GNU checksums."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

SHA256 = re.compile(r"[0-9a-fA-F]{64}")
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


def parse_checksums(text: str) -> dict[str, str]:
    """Parse plain PhysioNet or GNU lines; reject conflicting and unsafe paths."""
    index: dict[str, str] = {}
    for number, line in enumerate(text.split("\n"), 1):
        line = line.removesuffix("\r")
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-fA-F]{64})[ \t]+(\*?)([^ \t].*)", line)
        if not match:
            raise ValueError(f"malformed checksum line {number}")
        digest, marker, name = match.groups()
        if marker and name.startswith((" ", "\t")):
            raise ValueError(f"unsafe checksum path on line {number}")
        path = PurePosixPath(name)
        if (path.is_absolute() or PureWindowsPath(path.as_posix()).drive or "\\" in name
                or ".." in name.split("/") or path == PurePosixPath(".")
                or name.split("/")[-1] in {"", "."}
                or name.startswith("*")
                or any(unicodedata.category(c).startswith("C") or c in "\u2028\u2029" for c in name)):
            raise ValueError(f"unsafe checksum path on line {number}")
        key, digest = path.as_posix(), digest.lower()
        if key in index and index[key] != digest:
            raise ValueError(f"conflicting checksum path on line {number}")
        index[key] = digest
    return index


def _fingerprint(record: dict[str, Any], kind: str) -> tuple[int | None, str | None]:
    size, digest = record.get(f"{kind}_bytes"), record.get(f"{kind}_sha256")
    if size is None and digest is None:
        return None, None
    if (type(size) is not int or size <= 0 or not isinstance(digest, str)
            or not SHA256.fullmatch(digest) or digest.lower() == EMPTY_SHA256):
        raise ValueError(f"invalid {kind} size/hash pair; require nonempty bytes and SHA-256")
    return size, digest.lower()


def audit_source_checksums(
    inventory: Path, checksums: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return aggregate and opt-in detail rows, without copying header/patient fields.

    Both inputs are read once and receipted as exact bytes. Fingerprints are supplied,
    not recalculated from waveforms. Full verification means one signal path and its
    matching companion header; ambiguity never selects a source, even if one header
    matches. Empty inputs cannot establish full verification. This is not validation
    of clinical performance, cohort independence, index authenticity, or data rights.
    """
    raw = {"inventory": Path(inventory).read_bytes(), "checksums": Path(checksums).read_bytes()}
    data = json.loads(raw["inventory"].decode("utf-8-sig"))
    if not isinstance(data, dict) or not isinstance(data.get("records"), list):
        raise ValueError("inventory must contain a records list")
    index = parse_checksums(raw["checksums"].decode("utf-8-sig"))
    signals: dict[str, list[str]] = defaultdict(list)
    for name, digest in sorted(index.items()):
        if PurePosixPath(name).suffix.lower() == ".mat":
            signals[digest].append(name)
    seen: set[str] = set()
    details = []
    unique_sources: Counter[str] = Counter()
    verified_sources: Counter[str] = Counter()
    for record in data["records"]:
        if not isinstance(record, dict):
            raise ValueError("each inventory record must be an object")
        record_id = record.get("record_id")
        if (not isinstance(record_id, str) or not record_id.strip()
                or any(ord(c) < 32 or ord(c) == 127 for c in record_id)):
            raise ValueError("invalid inventory record_id")
        if record_id in seen:
            raise ValueError("duplicate inventory record_id")
        seen.add(record_id)
        mat_size, mat_hash = _fingerprint(record, "mat")
        hea_size, hea_hash = _fingerprint(record, "hea")
        matches = []
        for name in signals.get(mat_hash, []):
            hea_path = str(PurePosixPath(name).with_suffix(".hea"))
            official_hea_hash = index.get(hea_path)
            header_status = ("missing_local" if hea_hash is None else "missing_index"
                             if official_hea_hash is None else "matched"
                             if hea_hash == official_hea_hash else "mismatch")
            matches.append({"mat_path": name, "hea_path": hea_path,
                            "official_hea_sha256": official_hea_hash, "header_status": header_status})
        selected = matches[0] if len(matches) == 1 else None
        header_status = selected["header_status"] if selected else "not_selected"
        status = ("missing_signal" if mat_hash is None else "unresolved" if not matches
                  else "ambiguous" if not selected else "fully_verified"
                  if header_status == "matched" else "signal_only")
        source = str(PurePosixPath(selected["mat_path"]).parent) if selected else None
        if source is not None:
            unique_sources[source] += 1
            if status == "fully_verified":
                verified_sources[source] += 1
        details.append({"record_id": record_id, "mat_bytes": mat_size, "mat_sha256": mat_hash,
                        "hea_bytes": hea_size, "hea_sha256": hea_hash, "status": status,
                        "signal_status": "missing" if mat_hash is None else "matched" if matches else "unmatched",
                        "header_status": header_status, "matches": matches,
                        "selected_match_path": selected["mat_path"] if selected else None,
                        "verified_source": source if status == "fully_verified" else None})
    counts = dict(sorted(Counter(row["status"] for row in details).items()))
    report = {
        "schema": "TITAN_V45_SOURCE_CHECKSUM_AUDIT_V1",
        "records_total": len(details), "checksum_entries": len(index), "record_status_counts": counts,
        "signal_status_counts": dict(sorted(Counter(r["signal_status"] for r in details).items())),
        "selected_header_status_counts": dict(sorted(Counter(r["header_status"] for r in details).items())),
        "unique_signal_source_counts": dict(sorted(unique_sources.items())),
        "fully_verified_source_counts": dict(sorted(verified_sources.items())),
        "all_records_fully_verified": bool(details) and counts.get("fully_verified", 0) == len(details),
        "independent_validation": False, "rights_review": "not_performed", "hold_action": "none",
        "receipt": {key: {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}
                    for key, value in raw.items()},
        "limitations": ["Caller-supplied fingerprints; waveform/header files were not read or rehashed.",
                        "Index authenticity/current official availability not checked offline.",
                        "Checksums establish content identity, not cohort independence, clinical validity or rights."],
    }
    return report, details
