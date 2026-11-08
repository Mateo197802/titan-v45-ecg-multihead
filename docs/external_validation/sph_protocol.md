# SPH frozen-model source-transfer protocol

**Draft, not a preregistration or result.** No SPH model performance has been
computed. Seal this protocol, its machine-readable config, endpoint mapping,
code, environment, input fingerprints, and release model assets at a public
commit before executing model performance analysis.

## Study and analysis populations

Use all technically processable ECGs in the versioned SPH source, not a
positive-only or balanced subset. Enumerate metadata, archive membership,
readable arrays, technical eligibility, valid model outputs and reference
eligibility separately. Keep repeated ECGs within patient clusters, and
count exact and near-duplicate candidates separately. Patient pseudonyms
are source-specific and must not be assumed linkable to other databases.
See [source provenance](sph_dataset_audit.md) and the
[independence assessment](sph_independence_assessment.md).

The frozen variants are V3F with V3P e008 (P6), V3F with V3Q (P8 candidate)
and V3AG with its calibrated P4 specialist. Use the pre-existing class orders,
thresholds and decision policies from the release evidence. Do not tune or
recalibrate anything using SPH; do not reselect checkpoints. Do not create a
combined checkpoint or report all outputs as clinically validated classes.

## Signal handling to freeze

- Read the publisher HDF5 `ecg` array in the declared 12-lead order at 500 Hz.
  Verify lead interpretation, storage dtype, shape, `N` and any unit metadata
  on the staged bytes. If no conversion to absolute physical units is documented,
  report native amplitude representation and use only the scale-normalized
  candidate path; verify that its calculations do not assume physical amplitude.
- Use the source-backed candidate preprocessing already documented for the
  frozen models: named leads, filter 0.5–45 Hz, polyphase resampling to 125 Hz,
  deterministic context padding, and normalized 1,250-sample windows. Do
  not change the morphology candidate or the recovered event functions.
- P4 uses the first ten seconds as in the retained P4 candidate. Rhythm uses
  the existing ten-second schedule with five-second stride and fixed terminal
  rule. Aggregate all generated rhythm windows by the already documented
  P6/P8 rules; never select a window by labels or predicted performance.
- Predefine eligibility and technical exclusions before inference. A missing,
  malformed, nonfinite or incompatible array must be explicitly accounted
  for, not assigned a prediction. Quantify flat leads and preserve any
  applicable native-quality caveats. The candidate is not the original
  historical loader, and no retrospective equivalence claim is made.

## Endpoints and reporting

Use the [harmonization](sph_label_harmonization.md) for statement-level
binary endpoints. Separate any proxy analyses, or omit them. No pooled full
profile accuracy if any reference class is incompatible. No population
clinical negative inferred merely from an absent code. Compare to the
historical development metrics only descriptively and with separate
denominators. Preserve performance even if inferior.

Emit label-free private prediction and flow ledgers, then join reference
labels in a separate process after the ledger is sealed. Report coverage,
threshold crossings, fallback use and unresolved/no-output states without
creating an Other head or assuming clinical review. Quarantine is not
assessed without a valid policy; an undefined rate is not zero.

For the explicit evaluable class set, report positives/negatives and
confusion counts, sensitivity/specificity, PPV/NPV, F1, accuracy, AUROC,
average precision, Brier and calibration, with undefined values visible.
Use 2,000 patient-cluster bootstrap draws with a fixed seed and report
invalid replicates rather than dropping difficult endpoints. Any subgroup
analysis must report its support and disclosure restrictions. Publish only
aggregate results, checksums and the code needed to reproduce them.
