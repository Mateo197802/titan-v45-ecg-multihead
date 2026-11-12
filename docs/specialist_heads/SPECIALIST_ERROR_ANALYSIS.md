# Specialist Stage A Error Analysis

This is a new post-hoc analysis using frozen published backbones and newly trained heads. The detailed sanitized counts are in [`SPECIALIST_PER_CLASS_RESULTS.csv`](../../outputs/results/specialist_heads/20261111-v2/SPECIALIST_PER_CLASS_RESULTS.csv). It is not an independent external or clinical evaluation.

## Main trade-offs in the fixed primary candidate

| Profile/scope | Endpoint | Baseline recall | Candidate recall | Change |
|---|---|---:|---:|---:|
| P4, PTB-XL internal | ASMI | 0.7647 | 0.8235 | +0.0588 |
| P4, PTB-XL internal | LVH | 0.8000 | 0.7111 | -0.0889 |
| P4, PTB-XL internal | IMI | 0.8947 | 0.7368 | -0.1579 |
| P4, PTB-XL internal | ISC_ | 0.9615 | 0.8462 | -0.1154 |
| P6, Georgia | RBBB | 0.8533 | 0.6000 | -0.2533 |
| P6, Georgia | PVC | 0.5128 | 0.4359 | -0.0769 |
| P8, Georgia | PAC | 0.4615 | 0.3654 | -0.0962 |
| P8, Georgia | RBBB | 0.7333 | 0.6933 | -0.0400 |
| P6, CPSC sensitivity | RBBB | 0.9689 | 0.7200 | -0.2489 |
| P8, CPSC sensitivity | PAC | 0.8808 | 0.4106 | -0.4702 |

The P4 macro-F1 increase therefore does not meet the predeclared maximum priority-sensitivity drop of 0.03. On Georgia, P6/P8 macro-F1 changes are small and their paired record-level intervals include zero. On CPSC, the leave-one-source-out candidate is materially worse in macro-F1 for both profiles. The class-wise outcome is not a uniform improvement.

## Error interpretation limits

These class-level aggregates do not identify individual ECG errors and do not establish a physiological cause. The records use dataset statement mappings, not adjudicated longitudinal clinical diagnoses. No unsupported endpoint is imputed. The aggregate output has no record IDs; any case-level error review must occur in authorized CEDIA storage under the approved data access and must not be copied into this repository.

No threshold was changed in response to these errors, no candidate was chosen by holdout score, and no manual-review or quarantine claim is made. A new training/tuning study would require a separately frozen protocol and must leave the already inspected Georgia/CPSC results descriptive rather than confirmatory.
