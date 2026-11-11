"""Render the detailed reviewer matrix from its normalized JSON source."""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "docs/reviewer_closure/REVIEWER_48_DETAILED.md"

def evidence_link(value: str, output_path: Path) -> str:
    if value.startswith("http://") or value.startswith("https://"):
        return f"[{value}]({value})"
    absolute = ROOT / value
    relative = Path(os.path.relpath(absolute, output_path.parent)).as_posix()
    return f"[`{value}`]({relative})"


def render(payload: dict, output_path: Path = DEFAULT_OUTPUT) -> str:
    items = payload["items"]
    technical_counts = Counter(item["technical_status"] for item in items)
    satisfaction_counts = Counter(item["reviewer_satisfaction"] for item in items)
    lines = [
        "# Detailed disposition of the 48 review and audit observations",
        "",
        f"**As of:** {payload['as_of']}",
        f"**Counts:** {payload['counts']['peer_review']} peer-review observations; "
        f"{payload['counts']['project_audit']} project-audit observations; "
        f"{payload['counts']['total']} total.",
        "",
        payload["source_note"],
        "",
        "This is a technical evidence matrix, not a response letter, an editorial "
        "decision or a claim that the submitted manuscript has been revised. The "
        "manuscript and editor response remain unchanged.",
        "",
    ]
    supplemental = payload.get("supplemental_evidence")
    if supplemental:
        reviewer_ids = ", ".join(f"`{value}`" for value in supplemental["reviewer_ids"])
        audit_ids = ", ".join(f"`{value}`" for value in supplemental["internal_audit_ids"])
        legacy = supplemental.get("legacy_v4_may_recheck")
        lines.extend(
            [
                "## Supplemental CEDIA REV2 Evidence",
                "",
                "The bounded CEDIA REV2 export is documented in the separate technical addendum "
                f"{evidence_link(supplemental['reviewer_addendum'], output_path)} and claim index "
                f"{evidence_link(supplemental['canonical_claim_index'], output_path)}.",
                f"- **Reviewer items covered:** {reviewer_ids}",
                f"- **Internal audits covered:** {audit_ids}",
                f"- **Disposition:** {supplemental['status_changes']} status changes; "
                f"{supplemental['coverage_percentage_point_changes']} coverage percentage-point changes; "
                f"manuscript edited: `{str(supplemental['manuscript_edited']).lower()}`.",
            ]
        )
        if legacy:
            legacy_ids = ", ".join(f"`{value}`" for value in legacy["reviewer_ids"])
            lines.extend(
                [
                    f"- **Separate V4 May aggregate recheck:** {evidence_link(legacy['receipt'], output_path)}; "
                    f"applies to {legacy_ids} only as legacy-version evidence. {legacy['meaning']}",
                    "",
                ]
            )
        else:
            lines.append("")
    lines.extend(
        [
            "## Status counts",
            "",
            "### Technical status",
            "",
            "| Status | Count |",
            "| --- | ---: |",
        ]
    )
    lines.extend(f"| `{status}` | {count} |" for status, count in sorted(technical_counts.items()))
    lines.extend(["", "### Reviewer satisfaction", "", "| Status | Count |", "| --- | ---: |"])
    lines.extend(
        f"| `{status}` | {count} |" for status, count in sorted(satisfaction_counts.items())
    )
    lines.extend(
        [
            "",
            "The 12 `A-*` entries are internal audit observations and therefore use "
            "`NOT_APPLICABLE_AUDIT` in the reviewer-satisfaction dimension. A "
            "recovery ceiling is not a completed experiment, and a planned "
            "manuscript edit is not an implemented correction.",
            "",
            "## Item-by-item disposition",
            "",
        ]
    )
    for item in items:
        lines.extend(
            [
                f"### {item['id']} - {item['origin']}",
                "",
                f"- **Request:** {item['request']}",
                f"- **Affected manuscript scope:** {item['manuscript_scope']}",
                f"- **Technical status:** `{item['technical_status']}`",
                f"- **Reviewer satisfaction:** `{item['reviewer_satisfaction']}`",
                "- **Evidence:** "
                + "; ".join(evidence_link(value, output_path) for value in item["evidence"]),
                f"- **Protocol, population and observed result:** {item['protocol_population_result']}",
                f"- **What the evidence addresses:** {item['addressed_scope']}",
                f"- **What remains unresolved:** {item['unresolved']}",
                f"- **Recoverability:** {item['recovery_assessment']}",
                f"- **Experiment requirement:** {item['experiment_requirement']}",
                f"- **Future editorial action:** {item['editorial_action']}",
                f"- **Scientific risk:** {item['scientific_risk']}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "docs/reviewer_closure/REVIEWER_48_DETAILED.json",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = json.loads(args.source.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(payload, args.output), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
