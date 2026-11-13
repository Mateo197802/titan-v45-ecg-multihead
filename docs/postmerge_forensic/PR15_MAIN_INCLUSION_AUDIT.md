# PR #15 versus consolidated main

At the observed GitHub snapshot, main is
`6f50a6337fc3e8b518655b05916ced7447598b47`, tree
`f4ce35f55af909786dd3e9e78c453db35c17024c`. CI run
[43339745585](https://github.com/Mateo197802/titan-v45-ecg-multihead/actions/runs/43339745585)
passed on Python 3.10, 3.11 and 3.12. PRs #1-#14 are merged; the earlier
integration receipt predates the new draft.

[PR #15](https://github.com/Mateo197802/titan-v45-ecg-multihead/pull/15) is
open, draft, head `732ecb1c8e697997cdedf85f67db70d38bd765ed`, base
`0b87b9354796807b3bab26f3ded158f38afcc489`. Its CI run
[43341193213](https://github.com/Mateo197802/titan-v45-ecg-multihead/actions/runs/43341193213)
passed. The head is not an ancestor of main. Compare the actual main
ancestor `2d1f8432177835e189cfa769e7880d4f0165cdcb` with the PR head:
one new scientific publication commit adds 11 artifacts and modifies the
corrective verifier. All 11 are absent in main, and the verifier in main
is the earlier version. The JSON receipt lists all 12 paths.

The separately audited result is development-only: macro-F1
0.580124 to 0.582916, paired difference +0.002792 with interval
[-0.013190,+0.021799]; macro-AUPRC 0.550330 to 0.539431. The gate
records `development_success=false`, `promotion=NOT_AUTHORIZED`,
`test_opened=false`. A passing CI cannot promote it.

Recommendation: retain the negative outcome and include it only as
separate corrective evidence after normal author review, never as a
released-weight metric. No retarget, merge, or original PR edit was made.

During the audit, [PR #16](https://github.com/Mateo197802/titan-v45-ecg-multihead/pull/16)
was also observed open in draft, at `8a2d8aab60f9d017ce515847bfa96c8de97ce565`,
based on #15. Its inspected delta added or modified protocol, launchers,
worker and audit code, workflow, and tests; no finished scientific
aggregate was in that delta. This is a separate development program,
not part of the pinned main and not an experiment run by this audit.
