# SPH delivery audit

This audit concerns the executed V4.5 SPH transfer evaluation, not clinical
approval or a newly independent cohort. The historical training lineage is
incomplete; SPH source independence from every training stage is not certified.
An absent coded statement is not adjudicated absence of disease.

## Checks performed

- The receipt validator passed all 19 checks connecting the preregistered
  protocol, five model hashes, source hashes, label-blind scoring receipt,
  frozen ledger hash, corrected aggregation and ECE correction wrapper.
  The protocol SHA-256 is
  `d788ad8cca94793cebb738496acc131e82b1ca1900976f11020b99a79a5fc366`;
  the frozen aggregate SHA-256 is
  `09f93d9f310baaca672a33b0f369593cd88835a8ef08dc9929945c57cf18c988`.
- The aggregate validator reconciled all three profile flows and 14 compatible
  endpoints against the frozen protocol, including confusion sums, binary
  point metrics, bootstrap replicate counts and duplicate-sensitivity
  denominators. It is not an independent rerun of every metric calculation.
- The separate point verification job `32672` recomputed eight checks per
  endpoint. Jobs `32677` and `32728` independently reimplemented the binary
  and score-metric intervals respectively, for primary and duplicate-sensitivity
  analyses. They use the same records and random draws, not new patient data.
- SLURM accounting was queried for jobs `32668`, `32669`, `32672`, `32677`
  and `32728`: each was `COMPLETED`, exit `0:0`. Accounting supports execution
  status, not an editorial decision or independent validation.
- The bounded `audit_sph_public_json.py` check inspected all 13 top-level JSON
  files under `outputs/results/external_sph` and detected none of its specified
  identifier fields or SPH `A` plus five-digit record patterns. It does not
  scan figures, other directories, identifiers of different formats, or certify
  that a data release is de-identified under any particular standard.

## Interpretation and remaining boundaries

The [result table](../external_validation/sph_results.md) lists each endpoint,
including the low P4 F1 values and P8 PAC, and links to the complete aggregate.
All 25,770 source ECG were scored; no technical exclusions or inference failures
were recorded. Incompatible NSR, 1AVB and ISC_ references are not converted to
false negatives or claimed as fully evaluated. No historical quarantine policy
was recovered; SPH quarantine is **not assessed**, not a 0% rate.

The [preregistered protocol](../external_validation/sph_protocol.md),
[results and figure sources](../external_validation/sph_results.md),
[receipt checks](../external_validation/sph_independent_bootstrap.md), and
[independence assessment](../external_validation/sph_independence_assessment.md)
remain separately reviewable. Outputs for individual records remain in
authorized CEDIA storage and are not needed to read the published aggregates.

The narrow JSON scanner complements, rather than replaces, a human review of
publication rights and disclosure risks. It must not be treated as proof that
the complete repository contains no sensitive data.
