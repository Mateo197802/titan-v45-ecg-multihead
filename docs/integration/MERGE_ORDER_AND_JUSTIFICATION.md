# Merge order and justification

Integrate #3, #4, #7, #8, the four-reviewer base, #9, #12, the Stage A base,
#6, #10, #11, and #5, in that order. The first four preserve the historical
evidence and distinct editorial assessments before integrating the reviewer
experiments. Stage A must precede external validation and its descendants.
BenchmarkMax is a separate V4.6 program and comes last; only shared packaging
and test infrastructure may be reconciled.

Use individual merge commits on a temporary worktree and one GitHub
integration PR to main after combined verification. This preserves the original
heads and bases, avoids modifying drafts or pushing to original branches,
and permits CI to test the complete result before main changes. Verify
original PR states and ancestor checks independently afterward. If GitHub
does not recognize a PR automatically, do not describe it as merged unless
the actual PR state confirms it.

Before integration, record the original tree and retain annotated tag
`integration/titan-v45-main-pre-20261112`. Never rewrite any published ref.

## Actual integration

The above order was executed. During verification, #11 advanced by four
commits from `880945f` to `2d1f843`, adding a corrective evaluator, receipt
validator, independent private readback, fixed development probe, and
tests. That delta was audited separately, merged cleanly at `3e11ecf`,
and included in the fresh combined CI run before #13 was merged.
The subsequent stacked-base bookkeeping merges are recorded in
[the final status](FINAL_INTEGRATION_STATUS.md).
