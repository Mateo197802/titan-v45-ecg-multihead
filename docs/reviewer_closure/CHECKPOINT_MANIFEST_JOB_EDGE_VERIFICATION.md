# Checkpoint to Job, Manifest and Patient-Split Edges

**As of:** 2026-11-10. This is a read-only reconciliation of the current checkpoint metadata, retained scheduler/log evidence and selected manifests already documented in PR #3. A job completion is not proof of input-file consumption. No patient/record identifiers or restricted manifest rows are reproduced here.

## Edge labels

- `VERIFIED`: bytes, hash or count can be directly checked in the retained artifact.
- `SUPPORTED_NOT_CRYPTO_LINKED`: multiple independent records support the relationship, but no immutable job receipt binds the exact bytes.
- `UNVERIFIED_EDGE`: a required relation has no direct surviving artifact.
- `NOT_RECOVERED_IN_CHECKED_SOURCES`: the expected artifact was absent from the sources listed in [evidence source triage](EVIDENCE_SOURCE_TRIAGE.md); this is not global absence.

## Additional targeted Slurm accounting (2026-11-10)

A read-only `sacct` query covered the 15 requested job IDs listed in [the sanitized accounting receipt](receipts/CEDIA_TARGETED_SACCT_RECONCILIATION_2026-11-10.json). All are recorded `COMPLETED` with exit code `0:0`; the scheduler did not report a timezone, so timestamps are preserved without a UTC label. No jobs were submitted.

For jobs 16781-16783, the retained `SubmitLine` records explicit V3F artifact paths. Job 16781 declares a base checkpoint, rhythm train/validation manifests, a pathology train manifest and a pathology panel index. Job 16782 declares the checkpoint output path from job 16781 as its base plus the same manifest categories. Job 16783 declares V3F checkpoints and an external-evaluation manifest index. SHA-256 commitments to the exact `SubmitLine` strings are in the receipt; the raw path-bearing strings remain in authorized CEDIA accounting.

Bounded checks found the referenced V3F inputs, checkpoints, dedicated run directories and manifest index absent at their recorded paths. Jobs 16785/16786 expose environment-variable names in their submission records but not resolved values; their project work directories are absent at the recorded paths. The named historical project work directories for jobs 16816, 16819, 16887, 16903, 16904, 16906, 16914 and the source root for 17314/17315 are also absent at those checked paths. The P4/P6 logs and 17296 submit script that remain are byte-hashed in the receipt. These findings improve the record of declared job intent, but do not prove manifest reads, patient separation, checkpoint promotion or global absence from backups.

## Per-checkpoint lineage

| Checkpoint/profile | Checkpoint to job | Job to exact code/config | Job to actual manifest | Patient/source split | Job output to released checkpoint | Assessment |
| --- | --- | --- | --- | --- | --- | --- |
| `backbone-v3f-original.pt` | V3F jobs 16781-16783 are recorded completed. | Their scheduler `SubmitLine` fields declare script, run-directory, parent-checkpoint and input-manifest paths; script bytes and dedicated run directories are absent at the checked paths. | The declared rhythm train/validation and pathology train/panel paths are recorded, but their file bytes and actual read events are not recovered. | Full patient/source maps are absent. | Release manifest identifies the published artifact; producing-job output hash is absent. | Submission intent is better specified; actual data exposure and checkpoint lineage remain uncertified. |
| `backbone-v3ag-pathology.pt` | V3AG data/model jobs are recorded. | Full job-to-checkpoint code/config chain is incomplete. | Complete V3AG train/validation manifests are missing. | Cross-stage patient/signal overlap cannot be determined. | Published artifact has a release hash, not a verified producing-job hash edge. | Separate pathology backbone is identified; training isolation remains unverified. |
| `specialists-v3p-e008-primary6-diagnostic.pt` / P6 | V3O job 16887 is recorded completed; sweep 17314 and gate 17315 logs are retained. | Job 17314's submitted script is missing; 17315 has no immutable script hash in the surviving record. | Job 17315 names `v3h_rhythm_external_gate_holdout_accepted_balanced_manifest.csv`; 17314 does not name its manifest. | The V3P training manifest and complete V3H parent pool/patient map are absent. | Checkpoint metadata identifies epoch 8; exact output-checkpoint hash binding to the job is not in the log. | V3H selection exposure is strongly supported, not cryptographically proven from 17314 bytes; do not call it untouched test evidence. |
| `specialists-v3q-primary8-best-candidate.pt` / P8 | V3O training and V3P/V3Q evaluation/training jobs 16887, 16903, 16904 and 16906 are recorded. | Exact submitted scripts and complete work-directory receipts are unavailable at checked paths. | V3M and rhythm train/validation manifest bytes and actual read events are not linked. | Patient maps across stages are missing. | Release artifact identity is hash-listed; promotion/trial-to-checkpoint chain is incomplete. | Candidate model identified; historical isolation and complete selection provenance are not certified. |
| `specialists-v3ag-primary4-calibrated.pt` / P4 | Job 17296 retained log/script records a V3D calibration/evaluation workflow. | Script/log refer to a V3D output checkpoint name, not the released P4 filename. | Script points to the V3M internal validation panel index and selected V3S panel index; exact input rows are not retained in a complete patient map. | Calibration/training patient isolation is unverified. | Logged four thresholds match the P4 checkpoint metadata; no output hash closes the job-to-released-checkpoint edge. | Threshold values are cross-supported, but the historical promotion chain is not hash-linked. |

## P6 selection details

The retained 17314 log records the epoch sweep, including the epoch-8 result that passes the stated 0.95 accuracy / 0.80 macro-F1 gates. The log does not name an evaluation manifest. Job 17315 names the V3H accepted/balanced manifest and records the same epoch-8 result and six-class thresholds later associated with P6. This is strong evidence that V3H informed model selection; the exact bytes consumed by the 17314 sweep remain an `UNVERIFIED_EDGE`.

The P6 result is development/model-selection evidence. Nothing in the 17314/17315 pair certifies patient-disjoint training, and no leakage finding is made.

## P4 calibration details

Job 17296 records 1,492 window-panel observations across four classes; that number is not 1,492 unique ECGs or patients. Its threshold vector matches the released P4 metadata, but the logged output filename is a V3D calibration checkpoint. No immutable output hash establishes that this file became the released P4 specialist. The original V3M patient-level calibration manifest is not present in the checked source set.

## Specialist width metadata discrepancy

The retained reconstructed rhythm run report `outputs/results/revision_20261107/rhythm_waveform.json` records `declared=192`, `stored=512`, and `metadata_matches=false` for both P6 and P8. The current [`build_frozen_rhythm_head`](../../src/titan_v45/models/frozen_rhythm.py) reads the first specialist tensor's actual shape, constructs a 512-wide head, and loads the state dict strictly. A unit test exercises that stale-metadata case with a synthetic state dict. This explains how the current replay can load the stored weights despite the metadata mismatch; it does **not** prove which hidden width the historical training process intended or used before saving.

Do not edit the archived checkpoint metadata or change the weights. The discrepancy is separate from the global backbone parameter count and must be disclosed wherever specialist architecture is described.

## Patient-split and reproduction conclusion

Selected P4 records map to official PTB-XL fold 10, and the selected mapping has no patient overlap with official folds 1-9. This is evidence about the selected mapping only. It does not prove the exact historical manifests were consumed by V3AG/V3M jobs. The complete train/validation/calibration/model-selection/test intersection remains unavailable; report `PATIENT_ISOLATION_NOT_CERTIFIED`, not “leakage found” and not “no leakage.”

The exact original loader expected by the inventory is 36,271 bytes, SHA-256 `fc8d7367f9f2c108376839435021ec3172fe2757faa4a615f0ef5d39cbf1e855`. The examined 34 candidates did not match. The replay results and fixed tolerance are detailed in [loader identity and replay](HISTORICAL_LOADER_IDENTITY_AND_REPLAY.md).

## Reopen criteria

Reopen a specific edge only with the corresponding exact artifact: submitted script/config bytes; actual manifest bytes and patient map; job receipt tying file hashes to reads; and a producing-job receipt containing the released checkpoint hash. Keep row-level records in authorized CEDIA storage. The bounded NOC response and prior source triage are described in [recovered versus missing evidence](RECOVERED_VS_MISSING_HISTORICAL_EVIDENCE.md); neither justifies a claim about every institutional backup.
