# Independent Generalization Experiment Protocol

**Status:** Protocol specification only; `NOT_RUN`.
**Purpose:** Conditions for a future confirmatory independent-cohort evaluation if an eligible cohort is approved and obtained. This protocol does not convert the existing SPH transfer into an independent test.

## Freeze before any outcome inspection

Create a signed or otherwise immutable protocol receipt containing the cohort/version and rights evidence; repository commit; release-manifest and checkpoint SHA-256 values; environment lock; preprocessing and lead mapping; profile thresholds and fallback behavior; endpoint ontology; inclusion/exclusion rules; metric definitions; confidence-interval method; and failure handling. Hash the protocol and configuration. Do not make a threshold, ontology, filtering or model change after accessing evaluation labels.

## Population and independence

- Include every technically eligible ECG in the prespecified source/time window. Report source records, unique patient IDs, patient-linked duplicate components, exclusions by reason, missing signals, inference failures and unscored records separately.
- Use the patient as the resampling and partition unit. Detect exact signal duplicates across the external cohort and all accessible pretraining, fine-tuning, calibration and selection sources. Document the method and its limits for approximate duplicates.
- A new split of SPH is ineligible because SPH has already been consulted. V3H is ineligible for P6 independent testing because job evidence shows its use in epoch gating. Do not use an external set to tune thresholds or choose among epochs.
- If any source lineage cannot be checked, label the corresponding independence edge `UNVERIFIED`; do not claim full independence.

## Endpoints and scoring

Evaluate P6, P8 and P4 separately against only prespecified, compatible references. Distinguish ECG-statement presence from clinical diagnosis and longitudinal outcomes. Do not convert absent codes or unsupported labels to negatives. Report endpoint-level support and confusion counts, sensitivity, specificity, precision/PPV, NPV, F1, AUROC, average precision and calibration metrics where defined. Include patient-clustered 95% intervals, the number of valid/invalid replicates and class support. Do not calculate pooled clinical accuracy across incompatible endpoints.

Apply the released profile thresholds unchanged. Report empty threshold sets and P8 forced top-1 fallback separately. Quarantine is a separate policy: do not introduce it into the confirmatory protocol unless its score, threshold, referral action and denominator were frozen before evaluation. Human review requires a measured workflow and reviewer outcomes, not merely an algorithmic fallback.

## Analysis safeguards and outputs

No retraining, calibration, threshold selection, post-hoc class remapping or case-level removal based on performance. Any prespecified duplicate sensitivity analysis must report both full-population and sensitivity denominators and retain the primary analysis. Keep record-level data in authorized storage. Publish only aggregate tables, figures, code/config hashes, environment and sanitized execution receipts.

## Readiness gate

Execution remains blocked until an eligible cohort, its permitted reference, rights/access, source-overlap evidence, frozen profile artifacts and compute/storage authorization are documented. The current decision is **NO eligible untouched cohort identified; no new evaluation executed**. See [`dataset eligibility`](GENERALIZATION_DATASET_ELIGIBILITY.md) and [`results status`](GENERALIZATION_EXPERIMENT_RESULTS.md).
