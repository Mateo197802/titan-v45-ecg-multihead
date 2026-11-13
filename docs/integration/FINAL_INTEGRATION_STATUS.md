# Final integration status

The ten open PRs found at the start are integrated in main with original
commit ancestry. GitHub confirms PRs #1 through #13 are all `MERGED`.
PRs #1 and #2 were already merged; #13 was the new consolidation PR.

Scientific integration commit on main:
`85c1d8e6f3603560af9aea47e33806a530428cfb`, tree
`30849a3dfcc34ea0d2f9b118f3e4cb154f5b8b60`.
Initial main: `2677a3333069c16915cb71acd55d0f0176570bcf`, anchored by
the published annotated `integration/titan-v45-main-pre-20261112` tag.
This receipt is published afterward, so its publication commit naturally
has a different SHA and changes only this audit directory.

| PR | Final state | GitHub merge SHA | Merge introducing audited head into integration history |
|---|---|---|---|
| #1 | Previously merged | 79af292 | already present |
| #2 | Previously merged | 2677a33 | already present |
| #3 | Merged | 84f989e | 84f989e |
| #4 | Merged | e0d6ce6 | e0d6ce6 |
| #5 | Merged | 6f9d7f3 | 6f9d7f3 |
| #6 | Merged | 05b5f2c | 6fa359c |
| #7 | Merged | 39c031f | 39c031f |
| #8 | Merged | 69ecb60 | 69ecb60 |
| #9 | Merged | ad0e8a9 | 83105a2 |
| #10 | Merged | a44984d | afd1979 |
| #11 | Merged | 0b87b93 | 181cb66, then 3e11ecf |
| #12 | Merged | 5117095 | 4e8f0c0 |
| #13 | Merged | 85c1d8e | combined integration into main |

The five stacked PRs were still open after the combined merge, although
their original heads were already ancestors of main. After verifying those
heads and the absence of blocking branch rules, they were merged normally
on their respective original base branches in order #6, #9, #10, #11, #12.
These extra GitHub merge commits do not change the verified main tree.
No branch was deleted or rewritten. No original PR was merely closed.

The original submitted article, figures, official response letter, weight
declarations and restricted material were not changed. See the
[provenance and seals](SCIENTIFIC_PROVENANCE_PRESERVATION.md),
[conflicts](CONFLICT_RESOLUTION_LEDGER.md), and the machine-readable
`GITHUB_MAIN_INTEGRATION_VERIFICATION.json` receipt.
