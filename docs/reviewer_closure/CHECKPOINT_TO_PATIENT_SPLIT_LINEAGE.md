# Checkpoint-to-patient-split lineage

**As of:** 2026-11-10. This is the strongest chain supported by current checkpoint metadata, retained CEDIA job accounting/logs, and selected manifests. “Declared” means written in checkpoint metadata or a scheduler submission record; it does not prove a training process read that file. Patient identifiers and split rows remain in restricted storage and are not reproduced here.

## Per-artifact lineage

| Released artifact / profile | Declared model and source lineage | Job evidence | Patient split evidence | Current conclusion |
| --- | --- | --- | --- | --- |
| `backbone-v3f-original.pt` | Checkpoint metadata declares the common parent `titan_v4_final_best.pt` and V3F partial-backbone fine-tuning. | Jobs 16781-16783 are recorded as completed. Their scheduler submission lines declare specific input/checkpoint paths, but the path-bearing run directories and files are absent at the checked locations. | No exact V3F train/validation manifest bytes, read receipts or patient mapping are linked to the released backbone. | Submission intent is more specific; full training exposure is still not verified. |
| `backbone-v3ag-pathology.pt` | Metadata also declares `titan_v4_final_best.pt` as parent and V3AG partial-backbone fine-tuning. | V3AG data-development and model jobs are recorded, but their job-to-checkpoint hash chain and patient manifests are incomplete. | No complete V3AG training/validation patient manifests were recovered. | A separate V3AG pathology backbone is verified; isolation from V3F/V3AG upstream exposure is not. |
| `specialists-v3p-e008-primary6-diagnostic.pt` / P6 | Metadata declares a V3O rhythm-only specialist at epoch 8, with rhythm training manifest `v3p_rhythm_train_v3j_plus_incart_svdb_virtual_manifest.csv` and validation manifest `v3h_rhythm_external_gate_holdout_accepted_balanced_manifest.csv`. The P6 profile has six classes and six thresholds. | V3O job 16887 completed. P6 sweep job 17314 recorded 12 distinct epochs. Gate job 17315 explicitly names the V3H manifest and epoch-8 checkpoint. | The referenced V3P train manifest and complete V3H parent population/patient map are missing. | The 1,643-record V3H result is development/model-selection evidence, not an untouched final test. Training overlap remains unknown. |
| `specialists-v3q-primary8-best-candidate.pt` / P8 | Metadata declares a V3O rhythm-only specialist and a P4-only child whose parent is `v3o_rhythm_specialist_epoch_010.pt`; P4 training/validation references are the V3M train manifest and internal panel index. | V3O training job 16887, V3P evaluation job 16903, and V3Q P4 jobs 16904/16906 are recorded as completed. | V3M and rhythm training manifests and patient mappings are missing. P8 is a candidate profile, not a fully passed project gate. | Released weights and class contract are identified; full lineage and patient isolation are not. |
| `specialists-v3ag-primary4-calibrated.pt` / P4 | Metadata names `v3d_specialists.pt` as the P4-only parent and the V3M train/validation files. Its four thresholds are ASMI `0.67`, LVH `0.705`, IMI `0.635`, ISC_ `0.595`. | Job 17296's retained script/log execute a V3D pathology threshold-calibration workflow. The final logged threshold vector and panel metrics match the P4 metadata. | The internal V3M panel rows/patient IDs are missing, so training-to-calibration separation cannot be tested. | Thresholds are cross-supported; the calibration output is not hash-linked to the released P4 weights. |

## P6 selection and profile-specific thresholds

### Newly checked scheduler records

The targeted 2026-11-10 query and bounded path checks are recorded in [the sanitized CEDIA receipt](receipts/CEDIA_TARGETED_SACCT_RECONCILIATION_2026-11-10.json). It covers 15 named jobs, all `COMPLETED` with exit code `0:0`; timestamps have no scheduler-reported timezone. Jobs 16781/16782 record the V3F parent-checkpoint and declared training-manifest path sequence, and job 16783 records the external manifest-index path. The exact referenced V3F files and dedicated run directories were absent at their recorded locations when checked. This is stronger evidence of submitted intent, not evidence that those bytes were read or that the released model was produced from them.

The CEDIA log for job 17314 records 13 rows for epochs 1-12, with epoch 11 repeated. Epoch 8 reports 1,564/1,643 correct, accuracy `0.9519172246`, macro-F1 `0.8009383240`, and passes the 0.95/0.80 gates. Epoch 11 reaches accuracy `0.9531345100` but macro-F1 `0.7939599826`, below the gate. The log does not name its evaluation manifest, and the submitted sweep script is missing.

Job 17315, submitted shortly afterward, explicitly records `v3h_rhythm_external_gate_holdout_accepted_balanced_manifest.csv`, the same epoch-8 V3O specialist, the same 1,643-record result and the same thresholds. The released P6 checkpoint metadata identifies epoch 8; the canonical six-class profile config contains `[0.82, 0.835, 0.775, 0.515, 0.57, 0.43]`, matching the 17315 log.

The checkpoint metadata also contains an eight-threshold Primary8 vector. That vector belongs to the eight-class profile and is not expected to equal the six-class P6 vector. This is a dimensional/profile distinction, not evidence of a threshold mismatch. The external-metric epoch sweep followed by an explicit V3H gate report strongly indicates that V3H informed epoch selection; the missing 17314 script prevents a cryptographic proof that both jobs consumed the exact same manifest bytes. Do not present V3H as an untouched validation set.

## P4 calibration and units

Job 17296's retained submit script points calibration at `v3m_internal_val_p4_panel_index.json` and external evaluation at the selected V3S high-confidence panel index. Its log records 1,492 window-panel observations summed across four classes; this is not 1,492 unique ECGs or patients. The final V3D threshold result matches P4 checkpoint metadata, but the script's output checkpoint is named `v3d_specialists_internal_thresholds.pt`, not the released P4 artifact name. No output-file hash in the job log closes that gap.

Job 17305 is a separate P6 calibration diagnostic sourced from `v3d_specialists.pt`; its calibrated external summary is not the canonical P6 epoch-8 report. Keep those run outputs distinct. Current profile configs define the P6 six-class and P8 eight-class threshold contracts independently.

## What patient-level checks can and cannot be made

Official PTB-XL fold metadata places the 733 selected P4 ECG in fold 10 and maps them to 676 patients; they do not overlap the official fold 1-9 patients in that selected mapping. This verifies only the selected identifiers against official fold metadata. It does not prove that the historical backbone, specialist, threshold selection or all 1,465 other fold-10 ECG were handled as implied by a filename.

The V3H accepted/balanced manifest and V3S selected panels establish selected cohorts only. The V3H parent pool, preselection exclusions, V3P training manifest, V3M train/validation manifests, patient mappings and signal-level duplicate mappings are absent. Consequently, no complete train/calibration/model-selection/test intersection table can be computed. No leakage finding is made; patient isolation is simply not certified.

## Required evidence to reopen the chain

For each checkpoint, a future chain needs the exact checkpoint SHA-256; the submitted script/configuration bytes or immutable source revision; job ID and output receipt; actual train, validation, calibration and selection manifests; patient mapping and exact/near-signal duplicate reconciliation; and the checkpoint hash recorded by the producing job. Keep row-level artifacts in authorized CEDIA storage. A job name, metadata path, official fold or architecture match cannot substitute for this chain.
