# P4 pathology evidence boundary

The [historical profile report](https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/6f50a6337fc3e8b518655b05916ced7447598b47/docs/evidence-status.md)
documents ASMI, LVH, IMI and ISC_ on **962 selected binary-panel
observations**: mean binary accuracy 0.802290 and macro-F1 0.793456.
Those observations represent 733 ECGs and 676 linked patients, according
to the [split audit](https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/6f50a6337fc3e8b518655b05916ced7447598b47/docs/reviewer_closure/HISTORICAL_CALIBRATION_AND_SPLIT_UPDATE.md).
The panels use PTB-XL-derived labels and are not a natural-prevalence
sample. Historical manifests actually consumed by every job and patient
isolation were not fully certified. P4 uses a separate V3AG branch.

The five CODE flags used in PR #10 do not support a matched evaluation
of all four P4 endpoints. CODE AUROC and accuracy in this package are
not P4 metrics. Prior transfer/development work is not independent P4
confirmation.

```text
P4_EXTERNAL_MACRO_F1: NOT_ESTIMABLE
P4_INDEPENDENT_VALIDATION: NOT_EVALUATED
P4_EXTERNAL_VALIDATION: NOT_EVALUATED
```
