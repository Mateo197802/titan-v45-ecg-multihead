# Generalization Experiment Results and Non-Execution Record

**As of:** 2026-11-10.

**Independent confirmatory experiment:** `NOT_RUN`.

**Reason:** No untouched, rights-cleared cohort with verified source overlap and suitable reference was identified. No data were downloaded, no new CEDIA job was submitted and no GPU was used for this task.

## Existing evidence, kept in its actual scope

The existing frozen SPH transfer scored 25,770/25,770 ECG under each of P6, P8 and P4, with no technical exclusions or inference failures in the recorded flow. It contains 14 compatible ECG-statement endpoints and patient-component bootstrap intervals. These are later transfer results, not a new run in this task, not adjudicated clinical diagnoses, and not an independent test against all historical training sources. The exact aggregate is deterministically exported to [`GENERALIZATION_PER_CLASS_METRICS.json`](GENERALIZATION_PER_CLASS_METRICS.json) from [`sph_aggregate_32669.json`](../../outputs/results/external_sph/sph_aggregate_32669.json).

The endpoint results include unfavorable findings that must remain visible: SPH P8 PAC precision is 16.88% and F1 is 26.50%; P4 statement-level F1 is 4.73% for ASMI, 3.65% for LVH and 3.25% for IMI. Do not compare these imbalanced statement endpoints directly with the historical balanced P4 panels. This does not imply that every clinical pathology prediction is wrong; it shows that the proxy-reference/operating-point results do not support a broad clinical performance claim.

The P6 retained job logs add evidence that V3H was used for epoch gating: job 17315 reports 1,564/1,643, accuracy 0.9519172246 and macro-F1 0.8009383240 for epoch 8, meeting gates of 0.95 and 0.80. Job 17314 retains a 12-epoch sweep with the matching epoch-8 metrics, but not an exact sweep manifest digest. This is development/model-selection evidence, not independent validation.

## Not measured by this task

- No new external cohort, new patient split or independent clinical evaluation.
- No independent validation of a new `Other` class or auxiliary pathology targets.
- No historical quarantine effectiveness or pre/post outcome comparison.
- No complete historical patient-isolation certification, because checkpoint-to-training-manifest and backbone-source edges remain incomplete.

The CEDIA scheduler/log findings are recorded in [`CEDIA_JOB_LOGS_2026-11-10.json`](receipts/CEDIA_JOB_LOGS_2026-11-10.json). The original report and aggregates remain the evidence for SPH; this document does not imply a fresh reproduction of restricted row-level inputs.
