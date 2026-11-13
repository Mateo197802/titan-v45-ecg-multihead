# Checkpoint-to-Job-to-Manifest Verification: Final

**As of:** 2026-11-10. This report distinguishes a verified scheduler/run-log edge from an authenticated checkpoint-to-input-bytes edge.

## Evidence Graph

| Profile/artifact | Verified edge | Evidence | Unverified edge / boundary |
|---|---|---|---|
| P6 release specialist `specialists-v3p-e008-primary6-diagnostic.pt` | Job 17315 log names epoch 8, the internal separator manifest alias, and the V3H accepted/balanced external manifest alias. Its gate is accuracy >=0.95 and macro-F1 >=0.80; result is 1,564/1,643, 0.9519172246 and 0.8009383240. | `sacct` 17315 COMPLETED 0:0; retained output SHA-256 `74e03a97067b176c758c2c28b2faf0888c0bb555eb6a20a732b05f81385d43ec`; [`sanitized receipt`](receipts/CEDIA_JOB_LOGS_2026-11-10.json). | The log checkpoint is named `v3o_rhythm_specialist_epoch_008.pt`, while the release asset is named V3P. No byte/hash edge between those files is retained. Training job, exact source/config, manifest bytes and patient mappings are missing. |
| P6 epoch sweep | Job 17314 records external metrics for epochs 1–12; epoch 8 is the only reported passing epoch under the subsequent job-17315 gate values. | `sacct` 17314 COMPLETED 0:0; retained output SHA-256 `19df83ca78f0688a99e06a967611e04b4f308d0fd5a1af8df1bdd3efe144452e`. | Exact sweep submit script, entrypoint source and manifest digest are absent. Same-file relation to the V3H manifest printed by 17315 is strongly supported by matching checkpoint basename and exact epoch-8 metrics, not cryptographically proved. |
| P4 release config/checkpoint | Job 17296 launcher names the V3M internal-calibration and V3S external-panel index aliases. The final four thresholds match `configs/profiles/pathology_primary4.json`; aggregate accuracy and macro-F1 match the release after rounding. | Launcher SHA-256 `8ff857b1e79cb9ccadaa657d52004120fc65eaa220fef5a0f75f554152acb615`; log SHA-256 `1f0b29540c84cb68a5719e74e02ce3c58a1a4c38da66a8b39c9862913d2b18e8`; [`receipt`](receipts/CEDIA_JOB_LOGS_2026-11-10.json). | Historical panel bytes, per-patient mappings, exact calibration script bytes and released-specialist SHA-to-job-output edge are absent. Different filenames do not establish patient-disjointness. |
| P8 release specialist | Released asset hash, selected P8 evaluation manifest and replay outputs are in the public evidence package. | [`checkpoint lineage`](CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md), [`replay`](HISTORICAL_LOADER_IDENTITY_AND_REPLAY.md), [`release receipt`](REPRODUCIBILITY_VERIFICATION_RECEIPTS.md). | This CEDIA pass found no new job-linked training split or exact source-to-checkpoint edge for P8. |
| Backbone V3F/V3AG | Physical release hashes and architecture are documented. | [`evidence map`](EVIDENCE_TO_CLAIM_MAP.md), [`release metrics receipt`](receipts/RELEASE_METRICS_RECHECK_2026-11-10.json). | Full pretraining/fine-tuning dataset versions, patient/signal overlap, and exact job-to-checkpoint lineage remain incomplete. |

## P4 Job 17296: Exact Scope

The surviving launcher statically specifies an internal V3M panel index for calibration and a distinct V3S high-confidence panel index for evaluation. It iterates four checkpoint candidates and searches a 181-step threshold grid from 0.05 to 0.95, with target accuracy 0.90 and minimum F1 0.70. Across the four class panels, calibration totals 1,492 windows, not 1,492 unique ECG. The log reports 16 `passes_target=false` flags and zero true flags across the 16 candidate/class combinations.

For the final candidate in the retained log, thresholds `[0.67, 0.705, 0.635, 0.595]` match the released config exactly. The external panel output has 962 panel observations, 80.2290% mean binary accuracy and 79.3456% macro-F1; these round to the reported P4 80.23% and 79.35%. Per-endpoint support sums to 962 panel rows; panel rows may refer to the same ECG across endpoints. The exact release checkpoint bytes are not linked to the logged candidate by hash.

## P6 Jobs 17314/17315: Selection Exposure

The selected P6 epoch 8 result meets the explicit accuracy/macro-F1 gate on the V3H manifest named in job 17315. Job 17314 exposes 12 external metric rows, and only epoch 8 has `gate_pass=true` under the matching criteria. This is sufficient to classify the V3H population as development/model-selection evidence for P6. It is not sufficient to certify the sweep's exact manifest digest, and it rules out describing this P6 result as untouched independent test performance.

## Status by Lineage Edge

| Edge | Status |
|---|---|
| Released asset filename/hash -> profile contract | `VERIFIED_WITH_DEFINED_SCOPE` |
| Scheduler job ID/state -> retained CEDIA log hash | `VERIFIED_WITH_DEFINED_SCOPE` |
| P6 epoch 8 gate report -> named V3H evaluation manifest alias | `VERIFIED_WITH_DEFINED_SCOPE` |
| P6 sweep all-epoch scores -> exact V3H manifest bytes | `UNVERIFIED_EDGE` |
| P6 epoch checkpoint -> released P6 asset bytes | `UNVERIFIED_EDGE` |
| P4 job threshold vector -> released P4 profile threshold vector | `VERIFIED_WITH_DEFINED_SCOPE` |
| P4 job metric -> rounded released P4 metric | `VERIFIED_WITH_DEFINED_SCOPE` |
| P4 internal/external filenames -> patient-disjoint partitions | `UNVERIFIED_EDGE` |
| Backbone/source manifests -> all released checkpoint training patients | `UNVERIFIED_EDGE` |

No finding of patient leakage is made from these missing links. Historical patient isolation is **not certified**. Reopening requires authenticated manifest bytes, patient/signal mappings, exact job/config sources and a checkpoint hash edge.
