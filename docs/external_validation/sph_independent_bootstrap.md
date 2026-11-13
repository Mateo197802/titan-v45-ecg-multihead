# Independent binary bootstrap reproduction

The separate `independent_sph_bootstrap.py` reimplements the seeded
patient-component bootstrap for accuracy, sensitivity, specificity, precision,
negative predictive value and F1. It compares the full 2,000-draw percentile
intervals for each endpoint, including the prespecified discordant-duplicate
sensitivity analysis. It reads restricted inputs only inside CEDIA and emits
an aggregate match receipt, not rows or predictions.

This implementation requires the audited condition that no exact-signal group
crosses source patient IDs. It stops if that condition, population identity,
or any compared interval does not hold. This binary-only check does not
calculate AUROC, average precision, Brier or ECE intervals; these are checked
separately below. Reproduction of intervals does not establish clinical validity
or complete historical independence.

CEDIA job `32677` completed with `0:0`; all six binary-metric intervals matched
for each of the 14 endpoints in both primary and duplicate-sensitivity
analyses. The [aggregate-only receipt](../../outputs/results/external_sph/sph_independent_bootstrap_32677.json)
has SHA-256 `1beb13bbabd38308efcdf929740e16e6b75dd018ddc6b916022789eb41cfb52f`.

## Independent score interval reproduction

Job `32728` completed with `0:0`, using the same sealed metadata, scoring
ledger, duplicate index, frozen protocol, corrected aggregate, patient groups,
seeds and 2,000 draws. The independent score verifier recomputes weighted
AUROC, average precision, Brier and ECE interval endpoints and valid/invalid
draw counts for all 14 endpoints, in the primary and discordant-duplicate
sensitivity analyses. All matched the aggregate within 1e-12. The
[aggregate-only receipt](../../outputs/results/external_sph/sph_independent_score_bootstrap_32728.json)
has SHA-256 `988953a16b61405c476776a7b657b5a6c8b78a36e569976e8939341a2c19d7d5`.

This is an independent implementation applied to the same records and random
draws, not independent data, new predictions, clinical adjudication or a
second external validation. It stops if exact duplicates cross patient IDs.
Job `32727` failed before reading data because a script in the login node's
local `/tmp` was unavailable on the compute node; job `32728` used the same
hash-verified script from shared storage. Neither job changed frozen outputs.
