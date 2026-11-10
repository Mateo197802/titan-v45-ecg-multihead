# Evidence source triage

**Audit date:** 2026-11-09
**Scope:** Read-only comparison of the authorized CEDIA evidence archives, the live CEDIA account and Slurm accounting, and the current public repository. This is a forensic evidence index, not a manuscript revision or reviewer response.

## Handling and integrity

The user confirmed authorization to inspect the private CEDIA evidence ZIP. The archives were read without extraction; no bundled script, notebook, model or database was executed. No ECG waveform, patient or record identifier, row-level prediction, or restricted manifest row was copied to the repository or printed in the report.

| Source | Integrity and contents | Scope limit |
| --- | --- | --- |
| `TITAN_CEDIA_EVIDENCIAS_PRIVADAS_2026-11-04.zip` | SHA-256 `0fb1c2b7fe587684f939d75e619495f093dad01ece6a86f197b2329d52bd6398`; 797 archive entries, including 781 CEDIA project files and 16 package records. All 781 path/size/hash rows in `RUTAS_Y_HASHES.csv` matched the archive bytes. | Contains selected artifacts and recovery snapshots, not a complete pre-cleanup project image. |
| `TITAN_CEDIA_FALTANTES_INCREMENTAL_2026-11-04.zip` | SHA-256 `a85af77b2ea9efdb18632f15444622ca82a15d33dc06ff7780c143e3a14f3f12`; 97 files. All 96 entries declared by its internal `SHA256SUMS` matched. The package reports 85 new unique content files after deduplication. | Its CEDIA scan was bounded; zero candidates does not prove global absence. |
| CEDIA NOC response | NOC reported a backup dated 2026-09-04 17:00:01 and said the reviewed listing contained none of the requested `20260623_*` directories, `DATA_PIPELINE/data_loader_ultra.py`, or `titan_v45_41m_multihead_optuna.db`. | The response does not identify a timezone and covers the backup/listing NOC reviewed, not every institutional archive. |
| Public repository | This audit was performed against branch `codex/titan-v45-external-review`, then at `a07e6c8ef00ef5149db4f4980d0cd0c9798c7f52`; PR #3 remained open, draft, and unmerged. | A repository commit or green CI does not prove historical job inputs or patient separation. |

## Live CEDIA accounting and retained job logs

Read-only `sacct` queries covered the account's TITAN-named jobs from 2026-06-20 through 2026-06-30. Job state proves scheduler accounting only. For jobs with a retained log, the log hash below fingerprints the bytes examined; it does not prove those bytes were consumed by the model or that the model is the released checkpoint.

| Job | Slurm name | State / exit | What the record supports | Missing link |
| ---: | --- | --- | --- | --- |
| 16785 / 16786 | V3H train / evaluation | COMPLETED / `0:0` | Training and a separate evaluation job were recorded. | Both exact work directories and standard Slurm logs are absent at their recorded locations; selected manifest is not the preselection population. |
| 16816 / 16819 | V3M download / P4-only training | COMPLETED / `0:0` | The P4 source download and training job were recorded. | Work directories and standard logs are absent; training and validation manifests are not recovered. |
| 16887 | V3O P8 retry 1 | COMPLETED / `0:0` | A P8 training job was recorded. | Work directory, training receipt and checkpoint-to-job hash link are absent. |
| 16903 / 16904 / 16906 / 16914 | V3P evaluation, V3Q P4 training/evaluation, V3S P4 evaluation | COMPLETED / `0:0` | The named jobs were recorded. | Their exact work directories and standard logs are absent; job names do not establish the files consumed or patient overlap. |
| 16953 | V3Y P4 calibration | COMPLETED / `0:0` | A calibration job was recorded. | Work directory and standard log are absent; it is not linked to the released P4 checkpoint. |
| 17296 | `v3ag_p4cal_r1` | COMPLETED / `0:0` | Retained calibration/evaluation log and submitted-script path are available. | The script calls V3D calibration code and records V3D checkpoints; it is not a cryptographic binding to the final released checkpoint. |
| 17305 | `p6_v3f_cal` | COMPLETED / `0:0` | Retained P6 calibration log and submitted-script path are available. | It is a separate V3D-source calibration run, not the final P6 epoch-8 gate result. |
| 17314 | `p6_v3p_sweep` | COMPLETED / `0:0` | Retained log records an epoch sweep and aggregate external metrics. | The submitted script and exact evaluation-manifest name are absent. |
| 17315 | `p6_e8_gate` | COMPLETED / `0:0` | Retained log explicitly names the V3H validation manifest and reports the epoch-8 gate result. | No immutable submitted-script hash or patient-level split comparison survives. |

| Retained CEDIA artifact | Bytes | SHA-256 | Date and interpretation |
| --- | ---: | --- | --- |
| `slurm-17296.out` | 96,324 | `1f0b29540c84cb68a5719e74e02ce3c58a1a4c38da66a8b39c9862913d2b18e8` | 2026-06-27 20:42:10 -0500; V3D calibration/evaluation JSON summaries. |
| `submit_v3ag_p4_internal_threshold_calibration_retry1.sbatch` | 3,533 | `8ff857b1e79cb9ccadaa657d52004120fc65eaa220fef5a0f75f554152acb615` | Present in CEDIA and in the private ZIP with identical bytes; its current CEDIA mtime predates job 17296. This supports, but does not cryptographically prove, the submitted version. |
| `slurm-17305.out` | 19,142 | `0480470ae43c3f7883ca76cf56ed4868d34bd8d3734815aac1dac6d00ee22fe9` | 2026-06-27 22:02:02 -0500; P6 calibration diagnostics. |
| `submit_primary6_no_nsr_pac_clean_calibration_v3q_v3fbase.sbatch` | 2,213 | `e7efb82e0133babcfbcf675c581a4a8026159df68b9c50143986939cd514a489` | Present in CEDIA and in the private ZIP with identical bytes; current CEDIA mtime predates job 17305. |
| `slurm-17314.out` | 57,887 | `19df83ca78f0688a99e06a967611e04b4f308d0fd5a1af8df1bdd3efe144452e` | 2026-06-27 23:11:08 -0500; 13 JSON rows representing epochs 1-12, with epoch 11 repeated. |
| `slurm-17315.out` | 15,278 | `74e03a97067b176c758c2c28b2faf0888c0bb555eb6a20a732b05f81385d43ec` | 2026-06-27 23:14:34 -0500; P6 epoch-8 gate audit. |
| `full_checkpoint_metadata_20261029.json` | 134,728 | `5d853a2b3702f6846579b9e2b2d18cd6df00e0ceb0477a7b4ac9adc0357bf08b` | Inspection job 31566; checkpoint declarations and tensor shapes, not a training receipt. |

The submitted scripts for jobs 17314 and 17315 were not present at the exact paths recorded by `sacct`, in the inspected ZIPs, or in the inspected job work directories. The work directories for the listed V3H/V3M/V3O/V3P/V3Q/V3S/V3Y jobs were absent at the exact paths returned by `sacct`. This is a path-specific result, not a claim that no other copy exists anywhere.

## Material P6 selection evidence

The retained `slurm-17314.out` log contains 12 distinct epoch checkpoints. Epoch 8 is marked as passing both the 0.95 accuracy and 0.80 macro-F1 gates: 1,564/1,643 correct, accuracy `0.9519172246`, macro-F1 `0.8009383240`. Epoch 11 has higher accuracy (`0.9531345100`) but macro-F1 `0.7939599826` and does not pass. The log contains the epoch sweep and external metrics, but no occurrence of a manifest name; its submitted script is missing.

Three minutes later, job 17315 names `v3h_rhythm_external_gate_holdout_accepted_balanced_manifest.csv`, identifies `v3o_rhythm_specialist_epoch_008.pt`, records thresholds `[0.82, 0.835, 0.775, 0.515, 0.57, 0.43]`, and reports the same 1,564/1,643, `0.9519172246` accuracy, and `0.8009383240` macro-F1. This is strong evidence that the V3H gate result was used in P6 checkpoint selection. The exact 17314 manifest-to-job binding is not recoverable, so the shared-cohort link is not described as a cryptographic proof.

Consequently, V3H P6 results are development/model-selection evidence, not an untouched external test. The later SPH transfer evaluation is a separate analysis; it remains limited by unverified full V3F/V3AG training-source lineage and lack of clinical adjudication.

## Search boundary

The incremental inventory examined 3,613 CEDIA entries with bounded depth and metadata rules; it reported no target-header or SQLite database candidates. A separate recursive listing across multiple Slurm work directories did not finish within the execution window and was canceled; it is not used as evidence of absence. Exact expected manifest paths, selected work-directory paths, the NOC-reviewed backup result, and retained log/script paths were checked separately. No global-absence claim is made.

## Publication boundary

Only hashes, job IDs, class-level aggregates, source-level counts and sanitized interpretations belong in PR #3. Keep all signals, patient/record IDs, manifest rows, row-level predictions, duplicate links and per-patient bootstrap assignments in authorized CEDIA storage. PR #3 remains separate from PR #4 (A10/Optuna) and PR #5 (V4.6); this audit changes neither the manuscript nor the submission PDF.

## Reconciliation update (2026-11-10)

The original triage above is a 2026-11-09 snapshot at `a07e6c8`; it has not been rewritten as if it were created at the current head. The current PR #3 head was rechecked on GitHub as `31c4ccf2a7a899f1d38a2800f290472040becd06`, open and draft against `main`. CI at that head reports Python 3.10, 3.11 and 3.12 checks all passing in workflow run [42764288859](https://github.com/Mateo197802/titan-v45-ecg-multihead/actions/runs/42764288859). The PR adds the exploratory SPH PAC embedding probe after the original snapshot; that probe is post hoc, the PAC target had already been inspected, and it does not establish V4.5 historical PAC-head performance or clinical/independent validation.

The two user-authorized ZIPs were rechecked against their declared whole-archive SHA-256 values. Static central-directory inspection found 97 incremental-archive entries and 797 private-archive entries, with zero absolute/traversal paths and zero symlink entries. No archive was extracted and no bundled script, notebook or model was executed in this check. The separately named `TITAN_TRIAGE_EVIDENCIA_CEDIA_2026-11-09.md` was not present in the checked local Downloads/attachment locations, so it is not treated as a source.

A read-only CEDIA check confirmed that the authorized project checkout's `HEAD` equals the public PR #3 head and its working tree had no listed modifications. Its cached upstream-tracking status showed it one commit ahead; no fetch was performed, so this does not independently establish that the remote ref is current. Read-only accounting reports PAC jobs 32883 and 32884 as `COMPLETED`, exit `0:0`. No new historical train/validation manifests, exact loader, Optuna database or quarantine ledger were recovered by these checks. The evidence ceiling for those historical claims is unchanged.
