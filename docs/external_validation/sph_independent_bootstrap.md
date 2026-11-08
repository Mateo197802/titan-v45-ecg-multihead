# Independent binary bootstrap reproduction

The separate `independent_sph_bootstrap.py` reimplements the seeded
patient-component bootstrap for accuracy, sensitivity, specificity, precision,
negative predictive value and F1. It compares the full 2,000-draw percentile
intervals for each endpoint, including the prespecified discordant-duplicate
sensitivity analysis. It reads restricted inputs only inside CEDIA and emits
an aggregate match receipt, not rows or predictions.

This implementation requires the audited condition that no exact-signal group
crosses source patient IDs. It stops if that condition, population identity,
or any compared interval does not hold. AUROC, average precision, Brier and
ECE intervals are not independently recalculated by this binary-only check;
their structural and binning tests remain separate. Reproduction of intervals
does not establish clinical validity or complete historical independence.
