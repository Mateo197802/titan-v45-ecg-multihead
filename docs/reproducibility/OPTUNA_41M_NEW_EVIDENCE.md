# Optuna 41M: archived evidence reconciliation

**Scope:** TITAN V4.5, PR #4 only. This record is separate from the V3C nine-row snapshot, the A10 hash correction, and V4.6/PR #5. The manuscript and historical model artifacts were not changed.

## Source and integrity

The source is the sanitized, log-derived receipt `archived_41m_optuna_trial_receipt.json` inside the recovery ZIP with outer SHA-256 `23523fb59501b916cc6cea55ad0ae669387dbd0b10267a2d4bac7d353f8b5d06`. The receipt member SHA-256 is `9a0ecd850219eeca17bbb29ae424b786eb6d4407c6dd3abbf459b1cf77d09503`. The receipt records that it combines archived query/log observations; the original database bytes were not included. The receipt's captured objective source reports LF-normalized SHA-256 `cf28dbadb9e28a90736a9f82eb5d090cf4bbb384102116dcff4339ad3d054ed6`.

These hashes identify the transferred ZIP/member and a captured source representation. They do not authenticate the missing SQLite database or prove that a particular source revision was executed by any job.

## Two database generations, not one study

The historical basename `titan_v45_41m_multihead_optuna.db` was reused. The evidence describes an earlier database observation and a later fresh-study recreation; their trial IDs and outcomes must not be concatenated as one continuous study.

| Generation / job | Scheduler state | Trial observation | Logged epochs | What is supported |
|---|---|---|---:|---|
| Earlier observation / 13172 | SLURM job failed, `9:0`. | Trial 1 was later recorded COMPLETE with objective `0.19113820471846463`; earlier state output shows trial 0 FAIL and trial 1 RUNNING, followed by trial 1 COMPLETE and trial 2 RUNNING. | 30 | A bounded trial result and epoch log survived. A successful SLURM job is not established. |
| Recreated study / 13181 | SLURM job failed, `9:0`; log names a fresh study `titan_v45_41m_multihead_search`. | Trial 0 was recorded COMPLETE with objective `0.21677479658816123`; trial 1 was RUNNING and later marked failed/orphaned in the captured state sequence. | 8 | A distinct generation and one logged completed trial are supported. It is not a continuation of the earlier database. |
| Related pointer / 13169 | SLURM job failed, `1:0`. | No authenticated trial-to-checkpoint outcome is established by this job record. | Not established | It is a scheduler pointer only. |

All three scheduler jobs are recorded as failed. A completed trial state in a partial log/query is not equivalent to a successful job, a complete optimization run, or a promoted model.

## Recorded parameters

The two completed-trial observations each contain these eight parameters. They are transcribed from the archived receipt and are not a new Optuna replay.

| Parameter | Earlier observation, job 13172 / trial 1 | Recreated study, job 13181 / trial 0 |
|---|---:|---:|
| `base_lr` | 0.00002377838583571175 | 0.000009092920768852815 |
| `max_lr` | 0.0015003678533548667 | 0.00038232011746688546 |
| `weight_decay` | 0.000001677940279053466 | 0.000854127037465762 |
| `gamma` | 2.147028339304017 | 3.3178570074067153 |
| `label_smoothing` | 0.04206097310941042 | 0.07150606082144656 |
| `batch_size` | 32 | 16 |
| `mixup_alpha` | 0.05748907809873105 | 0.35943776353003876 |
| `lambda_pathology` | 0.5797773937376554 | 0.6104981085825801 |

## Objective and limits

The captured source receipt records the objective form:

`0.45 * primary9_macro_f1 + 0.35 * pathology5_macro_f1 + 0.10 * rhythm14_macro_f1 + 0.10 * pathology7_macro_f1 - 0.05 * missing_rhythm_classes - 0.05 * missing_pathology_labels`

The source receipt reports agreement with printed values at four-decimal precision for the two completed-trial observations. This is a cross-check of the captured formula and logged metrics, not an independent execution of the historical trial, nor proof that the captured source was the code consumed by the job. The 30 and 8 logged epochs do not establish complete planned training, convergence, or best-checkpoint promotion.

The package names `titan_v45_41m_multihead_optuna_before_resume.db` in a historical copy command. Neither that file's bytes nor the original study database, WAL/SHM companions, complete trial history, sampler state, or a cryptographic link to the published V3F/V3AG/P6/P8/P4 weights was recovered. A filename in a command is a route reference, not an authenticated file.

## Conclusion for A-06 / R1-4

This evidence improves the bounded historical record: two distinct database generations, two log/query-recorded completed-trial observations, their objectives/parameters, scheduler failures, and an objective-form cross-check are now explicit. It does **not** recover the SQLite database, establish the complete search, or connect either trial to released checkpoints. Do not merge these two generations, the V3C trial 6 result, or V4.6 experiments into one Optuna history. The reviewer point remains partial; the missing database and model-promotion edge remain unverified.

No SQLite binary, private raw receipt, row-level clinical data, or CEDIA-internal path is published here. The raw receipt remains in authorized storage.

## REV6 static objective source: separate, unlinked observation

The PR #3 integration reviewed a CEDIA-exclusive REV6 export containing a text copy of `TRAINING/optuna_search_hpc.py`, 63,398 bytes, SHA-256 `dbfeea1d46f93f23297a74194ecd9e06d72e78f8163bdaab8db9767c2de0715c`. Its in-package export record matches the member bytes. Static inspection shows a base objective of `0.60 × macro-F1 Primary-8 + 0.40 × macro-F1 Pathology-4`, with optional active-rhythm/clinical-axis modifiers, missing-class penalties, and a stability-ranking rule.

This source is not cryptographically linked to jobs 13169, 13172, 13181, 13239, or 13304, and effective CLI arguments are not recovered. It therefore does not replace or reconcile the captured May objective formula documented above (`0.45/0.35/0.10/0.10`). The difference is retained as two source observations with unresolved job/version attribution; it is not evidence that either formula produced a released checkpoint. The original SQLite generations, WAL/SHM files, complete trial history, and trial-to-checkpoint lineage remain absent.

The source copy is not republished in this PR. Its sanitized hash and interpretation are recorded in PR #3's evidence report, while this paragraph keeps the A-06/Optuna disposition visible in the PR #4 workstream. No artifact, trial row, A10 checksum, or historical result was changed.
