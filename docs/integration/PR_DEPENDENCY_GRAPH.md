# Pull-request dependency graph

GitHub snapshot: 12 PRs, of which #1 and #2 are already merged. The snapshot
and the exhaustive commit and file inventories are recorded with this audit.

```text
main at 2677a33
|-- #3 SPH and reviewer evidence
|-- #4 A10 / Optuna (overlapping subject with #3, different commits)
|-- #7 twelve scoped clarifications
|-- #8 evidence reconciliation and historical scoring register
|-- bf081e9 four-reviewer base (no PR of its own)
|   `-- #9 scientific closure
|       `-- #12 morphology and selective prediction
|-- f4d6be3 Stage A specialist base (no PR of its own)
|   `-- #6 external preflight and CODE-15%
|       `-- #10 duration-aware adaptation
|           `-- #11 development-only recovery
`-- #5 BenchmarkMax V4.6, parallel experimental line
```

The two no-PR bases have the initial main as their merge base and are not
ancestors of that main. Both are explicit integration steps. The local-only
editorial branch ending at e979943 is not an open PR or an ancestor of the
selected heads and is excluded.
