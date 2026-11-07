"""Summarize private header differences without exporting identifiers or values."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.evaluation.source_checksums import (
    audit_source_checksums,
    describe_header_changes,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True, help="Private JSON with header text")
    parser.add_argument("--checksums", type=Path, required=True)
    parser.add_argument("--upstream-headers", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Aggregate JSON only")
    args = parser.parse_args()
    try:
        inputs = [args.inventory, args.checksums]
        if (args.output.resolve() in {p.resolve() for p in inputs}
                or args.output.resolve().is_relative_to(args.upstream_headers.resolve())
                or (args.output.exists() and any(args.output.samefile(p) for p in inputs))):
            raise ValueError("output must not alias inputs or belong to the upstream directory")
        checksum_report, identities = audit_source_checksums(args.inventory, args.checksums)
        raw = args.inventory.read_bytes()
        index_raw = args.checksums.read_bytes()
        if (hashlib.sha256(raw).hexdigest() != checksum_report["receipt"]["inventory"]["sha256"]
                or hashlib.sha256(index_raw).hexdigest() != checksum_report["receipt"]["checksums"]["sha256"]):
            raise ValueError("inputs changed during audit")
        rows = json.loads(raw.decode("utf-8-sig"))["records"]
        if not rows:
            raise ValueError("no headers to audit")
        changes = []
        upstream_hashes = hashlib.sha256()
        for row, identity in zip(rows, identities, strict=True):
            identifier = row["record_id"]
            if not re.fullmatch(r"[A-Za-z0-9_-]+", identifier):
                raise ValueError("unsafe header identifier")
            if len(identity["matches"]) != 1 or identity["matches"][0]["official_hea_sha256"] is None:
                raise ValueError("require unique signal identity with indexed companion header")
            local = row["header"].encode("utf-8")
            if (len(local) != row["hea_bytes"]
                    or hashlib.sha256(local).hexdigest() != row["hea_sha256"]):
                raise ValueError("private header text does not match its physical fingerprint")
            path = (args.upstream_headers / (identifier + ".hea")).resolve()
            if not path.is_relative_to(args.upstream_headers.resolve()):
                raise ValueError("upstream header escapes directory")
            if args.output.exists() and args.output.samefile(path):
                raise ValueError("output aliases upstream header")
            upstream = path.read_bytes()
            digest = hashlib.sha256(upstream).hexdigest()
            if digest != identity["matches"][0]["official_hea_sha256"]:
                raise ValueError("upstream header differs from indexed bytes")
            upstream_hashes.update(bytes.fromhex(digest))
            changes.append(describe_header_changes(local, upstream))
        report = {
            "schema": "TITAN_V45_HEADER_REPRESENTATION_AUDIT_V1",
            "scope": "representation_changes_not_clinical_equivalence_or_rights_certification",
            "records": len(changes),
            "byte_identical_headers": sum(r["byte_identical"] for r in changes),
            "identical_after_newline_normalization": sum(
                r["identical_after_newline_normalization"] for r in changes
            ),
            "local_newline_styles": dict(Counter(r["local_newline_style"] for r in changes)),
            "upstream_newline_styles": dict(Counter(r["upstream_newline_style"] for r in changes)),
            "record_line_tokens_equal": sum(r["record_line_tokens_equal"] for r in changes),
            "signal_line_count_equal": sum(r["signal_line_count_equal"] for r in changes),
            "headers_with_changed_signal_token_column": dict(sorted(Counter(
                str(column) for r in changes for column in r["changed_signal_token_columns"]
            ).items())),
            "headers_with_changed_comment_field": dict(sorted(Counter(
                field for r in changes for field in r["changed_comment_fields"]
            ).items())),
            "receipt": {
                "inventory_sha256": hashlib.sha256(raw).hexdigest(),
                "checksums_sha256": hashlib.sha256(index_raw).hexdigest(),
                "upstream_header_digest_sequence_sha256": upstream_hashes.hexdigest(),
            },
            "clinical_equivalence_certified": False, "distribution_hold_lifted": False,
            "limitations": ["No waveform processing, patient matching or clinical adjudication.",
                            "Zero-based signal token columns include filename at column0.",
                            "No comment values or record identifiers exported.",
                            "Official index authenticity must be verified separately."],
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes((json.dumps(report, indent=2) + "\n").encode())
    except (OSError, TypeError, ValueError, KeyError) as exc:
        print(f"Header modification audit failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
