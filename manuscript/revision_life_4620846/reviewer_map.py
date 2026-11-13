"""Build the 15-comment/40-criterion crosswalk from the journal reports."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
DOCS = REPO / "docs" / "reviewer_closure"
REPORT = Path.home() / ".codex/attachments/8f89e4eb-c6de-4de0-b5b7-62f88d05ce01/Pasted text.txt"

# Literal report line prefixes, original source anchors, revised labels, disposition.
MAP = {
    "R1-1": ("The terminology and interpretation", 144, "sec:boundary", "EXPERIMENT_REQUIRED"),
    "R1-2": ("The primary performance estimates", 381, "sec:transfer-results", "PARTIAL"),
    "R1-3": ("The clinical meaning and harmonisation", 171, "sec:af-reference", "READY_FOR_AUTHOR_APPROVAL"),
    "R1-4": ("The strong claims regarding cryptographic", 829, "tab:app_hashes", "READY_FOR_AUTHOR_APPROVAL"),
    "R2-general": ("The manuscript presents modular ECG classifier", 165, "sec:other-results", "PARTIAL"),
    "R2-2b": ("There is not a single reference", 62, "fig:fig00_ecg_ai_context", "READY_FOR_AUTHOR_APPROVAL"),
    "R2-3a": ("I miss a subsection", 171, "sec:data", "PARTIAL"),
    "R2-3c": ("It is written: “Baseline physiological", 244, "sec:supervision", "READY_FOR_AUTHOR_APPROVAL"),
    "R2-3d": ("It is also written: “Anterolateral", 244, "sec:supervision", "READY_FOR_AUTHOR_APPROVAL"),
    "R2-3e": ('Table 5 - What means "Role"', 244, "tab:contracts", "READY_FOR_AUTHOR_APPROVAL"),
    "R2-3f": ("Figure 5 - What are the 10", 263, "sec:morphology", "READY_FOR_AUTHOR_APPROVAL"),
    "R2-4a": ("Table 8 – what does it mean", 384, "sec:boundary", "PARTIAL"),
    "R2-4e": ("What happens if there is not an output", 314, "sec:decision", "READY_FOR_AUTHOR_APPROVAL"),
    "R2-4k": ("How are estimated “Quarantine", 322, "sec:selective", "READY_FOR_AUTHOR_APPROVAL"),
    "R2-5": ("The authors point a problem", 527, "sec:pvc", "READY_FOR_AUTHOR_APPROVAL"),
}


def reports():
    return REPORT.read_text(encoding="utf-8-sig").splitlines()


def literal(prefix):
    return next(line for line in reports() if line.startswith(prefix))


def build():
    status = {r["id"]: r for r in csv.DictReader((DOCS / "REVIEWER_15_FULL_STATUS.csv").open(encoding="utf-8"))}
    score = json.loads((DOCS / "REVIEWER_40_VERIFIED_SCORE.json").read_text(encoding="utf-8"))
    with (ROOT / "REVIEWER_MANUSCRIPT_RECONCILIATION_MATRIX.csv").open("w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["reviewer", "comment", "criterion", "literal_request", "original_tex_line",
                         "scientific_issue", "existing_evidence", "new_evidence", "required_action",
                         "revised_label", "supporting_artifact", "technical_status", "points", "editorial_status",
                         "unresolved"])
        for row in score["rows"]:
            comment = row["comment"]
            prefix, line, label, disposition = MAP[comment]
            s = status[comment]
            writer.writerow([comment.split("-")[0], comment, row["id"], literal(prefix), line,
                             row["criterion"], s["proven"], ";".join(row["evidence_groups"]),
                             s["decision"], label, ";".join(row["evidence_ids"]), row["status"],
                             row["points"], disposition, s["remaining"] or row["limit"]])
    assert len(score["rows"]) == 40 and len(MAP) == 15
    assert sum(r["points"] for r in score["rows"]) == 20.5


if __name__ == "__main__":
    build()
