# TITAN V4.5 external-source evidence package

**Primary result:** patient-disjoint held-out evaluation within CODE-15% following
supervised domain adaptation. The three systems were compared on the same
4,921 ECGs from 3,891 patients for AFIB, SB, STACH, RBBB and 1AVB.
This is not independent institutional validation.

- [Download the complete ZIP](TITAN_V45_EXTERNAL_EVIDENCE_PACKAGE.zip) from the GitHub directory. The ZIP does not contain itself.
- [Primary summary](manuscript_core/PRIMARY_RESULTS_SUMMARY.md), [global table](manuscript_core/PRIMARY_RESULTS_TABLE.csv),
  [per-class results](manuscript_core/PER_CLASS_RESULTS.csv) and [paired comparison](manuscript_core/BASELINE_COMPARISON.csv).
- [Methods and cohort](manuscript_core/METHODS_AND_COHORT.md), [figures and captions](manuscript_core/FIGURE_CAPTIONS.md) and
  [claim boundaries](manuscript_core/ALLOWED_AND_DISALLOWED_CLAIMS.md).
- [Secondary evidence](supporting_evidence/SECONDARY_EVIDENCE_INDEX.md) and [verification instructions](technical_package/PACKAGE_VERIFICATION.md).

The primary source is the [immutable PR #10 snapshot](https://github.com/Mateo197802/titan-v45-ecg-multihead/tree/63c74b3fde2c51f7f8cde4ad396d77a1bd16cb29/docs/domain_adaptation).
The ZIP includes a minimal snapshot of the public aggregate sources for offline audit.
Larger or exploratory evidence is linked, not duplicated. No ECG-level predictions,
signals, patient IDs, credentials or model weights are included.
See the [CODE-15% provider record](https://zenodo.org/records/4916206) for
data attribution and access terms. This package does not redistribute the dataset.

```text
WITHIN_CODE_HELD_OUT_EVALUATION: COMPLETED
INDEPENDENT_INSTITUTIONAL_VALIDATION: NOT_EVALUATED
P4_EXTERNAL_VALIDATION: NOT_EVALUATED
MODEL_PROMOTION: NOT_AUTHORIZED
MANUSCRIPT_MODIFIED: FALSE
```
