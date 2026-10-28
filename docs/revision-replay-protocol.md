# Frozen Evidence Replay Protocol

Protocol created during revision on 28 October 2026. This records a new reproducibility investigation, not prospective registration of the original experiments.

## Objectives

1. Recompute saved prediction metrics with explicit observation, ECG and patient units.
2. Recover historical model, threshold and dataset configuration from original CEDIA artifacts.
3. Compare fresh waveform predictions against archived probabilities under an identified processing contract.
4. Preserve disagreements and missing evidence as outcomes of the investigation.

## Frozen Inputs and Prohibited Adaptations

Use the five model files identified by the existing release manifest. Keep Primary6, Primary8 and Primary4 contracts and checkpoints separate. Retain original prediction evidence and manifest files. No threshold tuning, class relabeling, checkpoint selection or sample removal may be performed to improve agreement with evaluation labels or recover a target metric.

A candidate implementation recovered from a different source tree must be labeled as a candidate. Matching dimensions or fitting a checkpoint state dictionary does not establish its historical identity. Alternative feature orders or signal processing may be assessed only when justified by independently recovered configuration evidence; do not search permutations for the best test accuracy.

## Saved-Prediction Analysis

Primary6: accepted-reference-label top-1 and six one-versus-rest binary panels. Primary8: accepted-label, thresholded-membership and single-target views remain separate. Primary4: four selected binary panels, mean panel accuracy and pooled panel accuracy remain separate. Zero-positive predictions retain their observations in denominators.

Use 2,000 cluster bootstrap draws, PCG64 seed 2026 and percentile 95% intervals. The initial report resamples ECG `(source, record_id)` units jointly across panels. With recovered PTB-XL metadata, a separate sensitivity analysis clusters all ECGs belonging to a supplied patient identifier. Missing patient mappings fail that sensitivity analysis rather than silently reverting to ECGs.

AUROC and AP require both the declared reference and the named score column; retain missing-score counts and undefined-class reasons. Probability/decision disagreements are diagnostics, not permission to replace saved predictions.

## Waveform Replay Gates

- Verify model bytes and complete class orders before loading.
- Establish signal units, lead ordering, filtering, context padding, resampling, window selection, normalization and morphology/event-feature extraction.
- Distinguish native checkpoint thresholds from the later frozen evaluation policy.
- Run a bounded compatibility check before a complete cohort replay. A discrepancy triggers a provenance investigation; it does not authorize a test-tuned repair.
- Compare record coverage, window counts, logits/probabilities, threshold decisions and aggregate metrics. Report numeric differences directly. A successful partial replay does not certify the entire release.
- Run model inference only on SLURM compute allocations. Record job ID, exit code, environment, code hashes, model hashes and failure details. An environment failure does not count as an inference result.

## Scope Beyond Replay

Full-workflow validation requires an all-input denominator and a routing policy based solely on signals/model outputs. Selecting a panel using ground-truth labels is an eligibility analysis, not operational routing.

Genuinely independent validation requires a new cohort not previously used for model development, calibration or selection. Source-held-out validation requires accounting for backbone training as well as specialist training. A frozen replay on previously used data cannot establish this independence.

Human review outcomes require an actual reader study or recoverable historical review records. An uncertainty flag, synthetic test or class registry cannot establish that a human corrected a prediction or improved patient outcomes.

## Publication Gate

Publish only verified, rights-cleared artifacts with scoped claims. Keep confidential reviewer reports and original logs containing private infrastructure paths in the private revision workspace. Generate public aggregate findings and fingerprints from them. A comment requiring new evidence remains open even if its explanatory text has been improved.
