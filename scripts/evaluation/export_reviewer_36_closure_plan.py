"""Build a reviewer-only action plan from the authoritative 48-item matrix."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA = "TITAN_V45_REVIEWER_36_CLOSURE_ACTION_PLAN_V1"
SOURCE_PATH = "docs/reviewer_closure/REVIEWER_48_DETAILED.json"
EXPECTED_COUNTS = {"reviewer_comments": 36, "internal_audits_linked_not_duplicated": 12}

STATUS_INTERPRETATIONS = {
    "VERIFIED_COMPLETE": "Verified within the bounded scope stated by the source record.",
    "VERIFIED_WITH_LIMITATIONS": "A bounded result is verified; residual limitations remain open.",
    "EXPERIMENT_COMPLETED_WITH_LIMITATIONS": "An experiment was executed; this does not imply that the original request is fully satisfied.",
    "EVIDENCE_CEILING_REACHED": "The searched sources reached a documented evidence ceiling; absence is limited to those sources.",
    "ACTIVE_RECOVERY_REQUIRED": "A bounded recovery lead remains; no conclusion of global absence is allowed.",
    "NEW_EXPERIMENT_REQUIRED": "Current evidence does not satisfy the request; a distinct new experiment is required.",
    "MANUSCRIPT_ONLY_PENDING": "Technical evidence is available for the bounded claim, but the manuscript remains unedited.",
}

OWNER_BY_STATUS = {
    "VERIFIED_COMPLETE": "Codex documents the bounded result; authors retain scientific approval.",
    "VERIFIED_WITH_LIMITATIONS": "Codex prepares precise wording; authors approve scope and interpretation.",
    "EXPERIMENT_COMPLETED_WITH_LIMITATIONS": "Codex reports measured results and limits; authors approve claims; a new study is needed if the broader claim is retained.",
    "EVIDENCE_CEILING_REACHED": "Codex stops unbounded searching and records the ceiling; authors decide claim scope; custodian acts only on a new archive lead.",
    "ACTIVE_RECOVERY_REQUIRED": "Codex performs only the identified bounded search; CEDIA custodian supplies any inaccessible archive; authors decide disposition if absent.",
    "NEW_EXPERIMENT_REQUIRED": "Authors/study team approve endpoint, data rights and protocol; Codex can implement and audit the approved workflow.",
    "MANUSCRIPT_ONLY_PENDING": "Codex prepares proposed edits; authors review and approve before any manuscript change or submission.",
}

ACTION_CLASS_BY_STATUS = {
    "VERIFIED_COMPLETE": "PRESERVE_TECHNICAL_RECEIPT_AND_REVIEW_CLAIM",
    "VERIFIED_WITH_LIMITATIONS": "DOCUMENT_LIMITS_AND_PREPARE_EDITORIAL_ACTION",
    "EXPERIMENT_COMPLETED_WITH_LIMITATIONS": "REPORT_EXPERIMENT_WITH_LIMITS_AND_DECIDE_IF_NEW_STUDY_IS_NEEDED",
    "EVIDENCE_CEILING_REACHED": "DECLARE_SOURCE_BOUNDED_CEILING_AND_PREPARE_SCOPE_DECISION",
    "ACTIVE_RECOVERY_REQUIRED": "BOUNDED_RECOVERY_THEN_CUSTODIAN_DISPOSITION",
    "NEW_EXPERIMENT_REQUIRED": "DESIGN_AND_APPROVE_A_DISTINCT_NEW_EXPERIMENT",
    "MANUSCRIPT_ONLY_PENDING": "PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT",
}


def _audit_ids(rows: list[dict[str, Any]]) -> list[str]:
    return sorted(row["id"] for row in rows if row["id"].startswith("A-"))


def _reviewer_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if not row["id"].startswith("A-")]


def build_plan(source: dict[str, Any], *, source_commit: str, as_of: str) -> dict[str, Any]:
    rows = source.get("items")
    if not isinstance(rows, list) or len(rows) != 48:
        raise ValueError("source matrix must contain exactly 48 items")
    reviewers = _reviewer_rows(rows)
    audits = _audit_ids(rows)
    if len(reviewers) != EXPECTED_COUNTS["reviewer_comments"] or len(audits) != EXPECTED_COUNTS[
        "internal_audits_linked_not_duplicated"
    ]:
        raise ValueError("source matrix must contain 36 reviewer comments and 12 audits")

    items = []
    for row in reviewers:
        status = row["technical_status"]
        satisfaction = row["reviewer_satisfaction"]
        if status not in STATUS_INTERPRETATIONS:
            raise ValueError(f"unsupported technical status for {row['id']}: {status}")
        if satisfaction not in {
            "FULLY_ADDRESSED_BY_EVIDENCE",
            "PARTIALLY_ADDRESSED",
            "ADDRESSED_BY_SCOPE_RESTRICTION",
            "NOT_SATISFIED",
            "EDITORIAL_ACTION_ONLY",
        }:
            raise ValueError(f"invalid reviewer satisfaction for {row['id']}: {satisfaction}")
        items.append(
            {
                "id": row["id"],
                "technical_status": status,
                "reviewer_satisfaction": satisfaction,
                "manuscript_state": "SIN_EDITAR",
                "closure_basis": (
                    "SOURCE_RECORD_AND_LINKED_EVIDENCE"
                    if satisfaction == "FULLY_ADDRESSED_BY_EVIDENCE"
                    else "NOT_CLOSED_BY_CI_OR_DOCUMENTATION_ALONE"
                ),
                "evidence_confidence": STATUS_INTERPRETATIONS[status],
                "traceability": {
                    "evidence_refs": row["evidence"],
                    "binding_rule": (
                        "Use the linked source documents for exact artifact hashes, job IDs and commits. "
                        "A path, filename, checkpoint metadata or completed scheduler state alone does "
                        "not prove that a job consumed an artifact; unresolved edges remain unverified."
                    ),
                },
                "evidence_assessment": {
                    "recorded_result_or_population": row["protocol_population_result"],
                    "scope_addressed": row["addressed_scope"],
                    "not_demonstrated_or_remaining": row["unresolved"],
                },
                "work_required": {
                    "code_change": (
                        "No new code change is identified by the current source record. "
                        "Implement one only if a specific reproducible defect is found."
                    ),
                    "repeat_verification": (
                        "Repeat only if new source bytes, code, data or a protocol change affects this item; "
                        "use the existing linked receipt as the current evidence."
                    ),
                    "targeted_recovery": row["recovery_assessment"],
                    "new_experiment": row["experiment_requirement"],
                    "manuscript_edit": row["editorial_action"],
                    "author_approval": "Required before final manuscript wording or submission.",
                },
                "remaining_actions": {
                    "recovery": row["recovery_assessment"],
                    "experiment": row["experiment_requirement"],
                    "editorial": row["editorial_action"],
                    "action_class": ACTION_CLASS_BY_STATUS[status],
                    "responsible_party": OWNER_BY_STATUS[status],
                },
                "source_record": row,
            }
        )

    return {
        "schema": SCHEMA,
        "as_of": as_of,
        "source_matrix": SOURCE_PATH,
        "source_commit": source_commit,
        "pr_state_checked": {
            "number": 3,
            "head": source_commit,
            "base": "main",
            "state": "OPEN_DRAFT",
            "merge_performed": False,
        },
        "counts": {
            **EXPECTED_COUNTS,
            "reviewer_satisfaction": dict(sorted(Counter(item["reviewer_satisfaction"] for item in items).items())),
            "technical_status": dict(sorted(Counter(item["technical_status"] for item in items).items())),
        },
        "internal_audit_ids": audits,
        "interpretation": (
            "Counts describe evidence disposition, not probability of acceptance. The 12 internal audits "
            "are linked to the authoritative 48-item matrix and are not duplicated among these 36 reviewer comments."
        ),
        "items": items,
    }


def _bullet_list(values: list[str]) -> str:
    return "\n".join(f"- `{value}`" if value.startswith(("docs/", "outputs/", "scripts/", "src/", "tests/")) else f"- {value}" for value in values)


def _sentence_text(value: str) -> str:
    """Normalize a source sentence at a generated prose boundary."""
    return value.rstrip().rstrip(".") + "."


def render_markdown(plan: dict[str, Any]) -> str:
    counts = plan["counts"]
    lines = [
        "# Reviewer 36 Closure Action Plan",
        "",
        f"**As of:** {plan['as_of']}",
        "",
        f"**Source of truth:** `{plan['source_matrix']}` at `{plan['source_commit']}`",
        "",
        "**Manuscript state:** `SIN_EDITAR`; submitted manuscript, PDF and response letter were not changed.",
        "",
        "**PR state:** PR #3 is open and draft; no merge was performed.",
        "",
        "This reviewer-only view preserves each source record verbatim under `source_record`. The 12 internal audits remain in the authoritative 48-item matrix and are linked below, not counted as reviewer comments.",
        "",
        "## Current disposition",
        "",
        f"- Reviewer comments: **{counts['reviewer_comments']}**.",
        f"- Internal audits linked separately: **{counts['internal_audits_linked_not_duplicated']}**.",
        f"- Reviewer satisfaction: `{json.dumps(counts['reviewer_satisfaction'], ensure_ascii=True)}`.",
        f"- Technical status: `{json.dumps(counts['technical_status'], ensure_ascii=True)}`.",
        "- These are categorical evidence states, not progress percentages and not a prediction of editorial acceptance.",
        "- `EDITORIAL_ACTION_ONLY` means proposed manuscript work remains; it does not mean the reviewer request is already closed.",
        "",
        "## Related technical and editorial drafts",
        "",
        "- [Reproducibility gaps](REVIEWER_REPRODUCIBILITY_GAPS.md)",
        "- [Code and formula audit](REVIEWER_CODE_AND_FORMULA_AUDIT.md)",
        "- [Figure and table corrections](REVIEWER_FIGURE_TABLE_CORRECTIONS.md)",
        "- [Populated reviewer-proposed tables](REVIEWER_PROPOSED_TABLES.md)",
        "- [Claim disposition](REVIEWER_CLAIM_WITHDRAWAL_DECISIONS.md)",
        "- [Response evidence draft](REVIEWER_RESPONSE_EVIDENCE_DRAFT.md)",
        "",
        "## How to read each item",
        "",
        "`recorded_result_or_population` and `scope_addressed` state what the current source matrix says is supported. `not_demonstrated_or_remaining` controls the boundary. Exact artifact hashes, job IDs and commit anchors remain in the linked evidence documents; a linked file is not treated as proof of job consumption unless the source record binds it. `reviewer_satisfaction` is kept distinct from technical status.",
        "",
        "## Reviewer comments",
        "",
    ]
    for item in plan["items"]:
        source = item["source_record"]
        lines.extend(
            [
                f"### {item['id']} — {source['origin']}",
                "",
                f"**Specific request:** {source['request']}",
                "",
                f"**Scope in manuscript:** {source['manuscript_scope']}",
                "",
                f"**Evidence recorded:** {item['evidence_assessment']['recorded_result_or_population']}",
                "",
                f"**What the available evidence addresses:** {item['evidence_assessment']['scope_addressed']}",
                "",
                f"**What it does not establish / what remains:** {item['evidence_assessment']['not_demonstrated_or_remaining']}",
                "",
                "**Evidence references:**",
                _bullet_list(item["traceability"]["evidence_refs"]),
                "",
                f"**Traceability confidence:** {item['evidence_confidence']}",
                "",
                f"**Code change indicated:** {item['work_required']['code_change']}",
                "",
                f"**Repeat verification:** {item['work_required']['repeat_verification']}",
                "",
                f"**Recoverability assessment:** {source['recovery_assessment']}",
                "",
                f"**Experiment needed:** {source['experiment_requirement']}",
                "",
                f"**Proposed editorial action (not applied):** {source['editorial_action']}",
                "",
                f"**Technical status:** `{item['technical_status']}`",
                "",
                f"**Reviewer satisfaction:** `{item['reviewer_satisfaction']}`",
                "",
                f"**Next action class:** `{item['remaining_actions']['action_class']}`",
                "",
                f"**Owner boundary:** {item['remaining_actions']['responsible_party']}",
                "",
                f"**Manuscript:** `{item['manuscript_state']}`",
                "",
                f"**Scientific risk:** {source['scientific_risk']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Internal audits",
            "",
            "The following 12 IDs remain in [`REVIEWER_48_DETAILED.json`](REVIEWER_48_DETAILED.json) and [`REVIEWER_48_DETAILED.md`](REVIEWER_48_DETAILED.md):",
            "",
            ", ".join(f"`{audit_id}`" for audit_id in plan["internal_audit_ids"]),
            "",
            "## Reopening criteria",
            "",
            "Reopen a row only on new source artifacts with verifiable hashes and authorized provenance, a new approved experiment, or an explicit author decision about claim scope. Do not convert missing evidence to a negative finding, infer acceptance from silence, or change the historical metrics to force closure.",
            "",
        ]
    )
    return "\n".join(lines)


def render_response_draft(plan: dict[str, Any]) -> str:
    lines = [
        "# Reviewer Response Evidence Draft",
        "",
        "**NOT FOR SUBMISSION — requires author review and approval.**",
        "**The manuscript has not been edited; the submitted PDF and response letter are unchanged.**",
        "",
        f"Source: [`{plan['source_matrix']}`]({Path(plan['source_matrix']).name}) at `{plan['source_commit']}`. This document turns the existing technical disposition into provisional evidence language; it does not assert that a proposed manuscript change has already been made or that the reviewer is satisfied.",
        "",
        "Each reply below is conditional on authors approving and actually implementing the associated manuscript change. Keep the scientific limitation in the final response even when the proposed editorial action is accepted.",
        "",
    ]
    for item in plan["items"]:
        source = item["source_record"]
        lines.extend(
            [
                f"### {item['id']} — {source['origin']}",
                "",
                f"**Current disposition:** `{item['technical_status']}` / `{item['reviewer_satisfaction']}`.",
                "",
                f"**Reviewer request:** {source['request']}",
                "",
                "**Evidence-only candidate wording, conditional on author approval:**",
                "",
                f"> We appreciate this comment. The evidence available for this point is: {_sentence_text(source['addressed_scope'])} This evidence does not establish: {_sentence_text(source['unresolved'])} We therefore propose to revise the manuscript as follows, subject to author approval: {_sentence_text(source['editorial_action'])}",
                "",
                f"**Required experiment or unresolved evidence:** {source['experiment_requirement']}",
                "",
                f"**Approval gate:** {item['remaining_actions']['responsible_party']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Submission gate",
            "",
            "Before any response is sent, authors must verify the cited evidence, approve the revised manuscript text and response, confirm that every proposed action was actually implemented, and decide how to report requests that remain unsatisfied. This draft is not a substitute for the editor's decision or the authors' approval.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--as-of", required=True)
    args = parser.parse_args()
    source = json.loads((args.root / SOURCE_PATH).read_text(encoding="utf-8"))
    plan = build_plan(source, source_commit=args.source_commit, as_of=args.as_of)
    out = args.root / "docs/reviewer_closure"
    out.mkdir(parents=True, exist_ok=True)
    (out / "REVIEWER_36_CLOSURE_ACTION_PLAN.json").write_text(
        json.dumps(plan, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    (out / "REVIEWER_36_CLOSURE_ACTION_PLAN.md").write_text(
        render_markdown(plan), encoding="utf-8"
    )
    (out / "REVIEWER_RESPONSE_EVIDENCE_DRAFT.md").write_text(
        render_response_draft(plan), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
