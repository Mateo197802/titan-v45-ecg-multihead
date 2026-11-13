"""Verify the fixed rubric, reference integrity and optional published blobs."""
import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/reviewer_closure"
EXCLUDED = {"R1-1", "R2-2b", "R2-4a"}
PREFIX = "https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/"


def records(name):
    with (DOCS / name).open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows and all(None not in r and None not in r.values() for r in rows)
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--git-refs", action="store_true")
    args = p.parse_args()
    ledger = records("MASTER_EVIDENCE_LEDGER.csv")
    matrix = records("REVIEWER_15_FULL_STATUS.csv")
    claims = records("CLAIM_KEEP_LIMIT_WITHDRAW.csv")
    score = json.loads((DOCS / "REVIEWER_40_VERIFIED_SCORE.json").read_bytes())
    ids = {r["evidence_id"] for r in ledger}
    assert len(ids) == len({r["sha256"] for r in ledger}) == len(ledger)
    groups = {g for r in ledger for g in r["evidence_groups"].split(" | ")}
    links = 0
    for r in ledger:
        assert re.fullmatch(r"[a-f0-9]{64}", r["sha256"]) and int(r["bytes"]) > 0
        assert r["evidence_id"] == "E-" + r["sha256"][:16]
        for link in filter(None, r["github_links"].split(" | ")):
            assert link.startswith(PREFIX)
            commit, path = link.removeprefix(PREFIX).split("/", 1)
            assert re.fullmatch(r"[a-f0-9]{40}", commit)
            if args.git_refs:
                raw = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{commit}:{path}"])
                assert hashlib.sha256(raw).hexdigest() == r["sha256"] and len(raw) == int(r["bytes"])
            links += 1
    comments = {r["id"] for r in matrix}
    assert len(comments) == len(matrix) == 15
    assert {r["id"] for r in matrix if r["scope"] == "excluded"} == EXCLUDED
    assert set(score["scope_excluded"]) == EXCLUDED
    rubric = score["rubric"]
    assert [rubric[k] for k in ("full", "partial", "other")] == [1, .5, 0]
    assert len({r["id"] for r in score["rows"]}) == len(score["rows"]) == 40
    totals, ns = Counter(), Counter()
    for r in score["rows"]:
        assert r["comment"] in comments and r["id"].startswith(r["comment"]+".")
        assert r["scope"] == ("excluded" if r["comment"] in EXCLUDED else "active")
        points = 1 if r["status"] == rubric["full_status"] else .5 if r["status"] in rubric["partial_statuses"] else 0
        assert r["points"] == r["baseline_points"] == points
        assert set(r["evidence_ids"]) <= ids
        assert (r["scope"] == "active") == bool(r["evidence_ids"])
        assert set(r["evidence_groups"]) <= groups
        if r["scope"] == "active":
            assert set(r["evidence_ids"]) == {e["evidence_id"] for e in ledger
                if set(e["evidence_groups"].split(" | ")) & set(r["evidence_groups"])}
        totals[r["comment"]] += points
        ns[r["comment"]] += 1
    for r in matrix:
        i = r["id"]
        assert float(r["points"]) == totals[i] and int(r["criteria"]) == ns[i]
        assert abs(float(r["coverage_pct"]) - 100*totals[i]/ns[i]) < 1e-6
    for label, subset, expected in (
        ("global", comments, (20.5, 40, 15, 51.25)),
        ("active", comments-EXCLUDED, (16.5, 33, 12, 50.0)),
    ):
        points, n = sum(totals[i] for i in subset), sum(ns[i] for i in subset)
        got = (points, n, len(subset), 100*points/n)
        assert got == expected
        assert got == tuple(score["totals"][label][k] for k in ("points", "criteria", "comments", "coverage_pct"))
    for claim in claims:
        assert set(claim["comments"].split("|")) <= comments-EXCLUDED
        assert set(claim["evidence_groups"].split("|")) <= groups
    assert len({r["claim_id"] for r in claims}) == len(claims)
    active = (DOCS/"REVIEWER_12_ACTIVE_STATUS.md").read_text(encoding="utf-8")
    assert set(re.findall(r"(?m)^\| (R[^ |]+) \|", active)) == comments-EXCLUDED
    print(f"PASS: 40 criteria; 20.5/40 global; 16.5/33 active; {len(ledger)} unique artifacts; "
          f"{len(claims)} claims; {links} pinned links (hash checks={args.git_refs}).")


if __name__ == "__main__":
    main()
