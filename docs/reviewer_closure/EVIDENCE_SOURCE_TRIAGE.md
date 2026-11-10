# Evidence source triage

**Audit date:** 2026-11-10
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
| 16781 / 16782 / 16783 | V3F fine-tune / specialist / external evaluation | COMPLETED / `0:0` | New `SubmitLine` digests preserve explicit submitted artifact-path categories, including a declared 16781-to-16782 checkpoint path. | The referenced inputs, outputs and dedicated run directories were absent at the exact checked paths; no manifest-read or producing-checkpoint hash receipt survives. |
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

On 2026-11-10, a new read-only accounting pass covered 15 explicitly named jobs. Exact V3F input/checkpoint paths and the listed V3H/V3M/V3O/V3P/V3Q/V3S work directories were checked and were absent at those recorded locations; three retained logs and the P4 calibration submit script were re-hashed. A broader exact-name search for the historical loader under the full authorized project tree exceeded the 30-second command window and was stopped; it returned no usable result and is not evidence of absence. See [the sanitized targeted receipt](receipts/CEDIA_TARGETED_SACCT_RECONCILIATION_2026-11-10.json).

## Publication boundary

Only hashes, job IDs, class-level aggregates, source-level counts and sanitized interpretations belong in PR #3. Keep all signals, patient/record IDs, manifest rows, row-level predictions, duplicate links and per-patient bootstrap assignments in authorized CEDIA storage. PR #3 remains separate from PR #4 (A10/Optuna) and PR #5 (V4.6); this audit changes neither the manuscript nor the submission PDF.

## Reconciliation update (2026-11-10)

The inventory and tables above preserve the 2026-11-09 source snapshot; this addendum records the later checks without rewriting that history. GitHub currently reports PR #3 at `01beb7a68077a44560b037dbee9b5deace557b8d`, open and draft against `main`. CI for that exact head passed in workflow run [42886694683](https://github.com/Mateo197802/titan-v45-ecg-multihead/actions/runs/42886694683). The post-hoc SPH PAC probe remains exploratory: the target had already been inspected, and it does not establish V4.5 historical PAC-head performance or clinical/independent validation.

The two user-authorized ZIPs were rechecked against their declared whole-archive SHA-256 values. Static central-directory inspection found 97 incremental-archive entries and 797 private-archive entries, with zero absolute/traversal paths and zero symlink entries. No archive was extracted and no bundled script, notebook or model was executed in this check. The separately named `TITAN_TRIAGE_EVIDENCIA_CEDIA_2026-11-09.md` was not present in the checked local Downloads/attachment locations, so it is not treated as a source.

A read-only CEDIA check found the PR #3 clone at `31c4ccf2a7a899f1d38a2800f290472040becd06`, parent `99b1065f37fcb3cdb6adc70dfbbc6ebc93e2fb12`, with a clean worktree and one local commit ahead of its cached upstream ref. This is not the current GitHub head; the CEDIA commit is based on the earlier `99b1065` state and was not reset, rebased, cherry-picked or overwritten. Hash checks showed four of its seven changed files byte-identical to the newer PR #3 tree; three matrix snapshots differ. The overlapping PAC facts are present in the current PR #3 evidence, but the CEDIA-only commit remains preserved and the CEDIA clone is not yet synchronized to the GitHub head.

The new read-only `sacct` query verified all 15 requested job IDs as `COMPLETED`, exit `0:0`, and hashed their `SubmitLine` strings without publishing the raw path-bearing commands. For jobs 16781-16783, those strings declare V3F training, validation, parent-checkpoint and external-manifest path categories. The exact referenced files/directories were absent at the checked paths; the submission record is not a manifest-read receipt. Existing hashes for jobs 17296/17314/17315 were independently recomputed and match the retained aggregate receipt. No new historical train/validation manifest bytes, exact loader, Optuna database or authentic quarantine ledger were recovered. The evidence ceiling remains for those claims, bounded to the sources and paths actually checked.

## Reconciliation update (2026-11-10, cleanup-manifest lead)

Immediately before this addendum, GitHub reported PR #3 at `575c5a5fa4dbcf658308c928aa7d08259fd61c9f`, still open and draft against `main`; CI for that head passed in run [42893586345](https://github.com/Mateo197802/titan-v45-ecg-multihead/actions/runs/42893586345). The separate CEDIA checkout remains at its previously recorded local commit and was not synchronized, reset or overwritten.

A read-only parse of the retained CEDIA cleanup manifest produced the sanitized receipt [`CEDIA_CLEANUP_MANIFEST_TRIAGE_2026-11-10.json`](receipts/CEDIA_CLEANUP_MANIFEST_TRIAGE_2026-11-10.json). The manifest is 225,427 bytes with SHA-256 `91ac37b57bfe38e911f783194f69770ea967ead24a07580b7091414949aeab58`; its retained mtime is 2026-06-30 18:01:26.639710 UTC, not proof of creation time or job use. It contains 1,438 candidate rows with path and byte-count fields, but no per-entry hashes or mtimes. An embedded confirmation digest differs from the measured whole-file digest; its intended scope is not documented, so it is not treated as an integrity check.

The inventory lists three non-empty job logs (13169: 2,017,109 bytes; 13172: 2,011,026; 13181: 2,007,135) and three zero-byte error logs. A bounded name-only search of the two known project trees, capped at eight directory levels and not following symlinks, visited 4,914 directories. It found only the two previously known CSV snapshots (`optuna_trials.csv`, 1,319 bytes; `optuna_best_parameters.csv`, 210 bytes), not the six listed logs or an SQLite/database candidate. A name-only listing of `titan_repo_stage_20260629.tar` produced zero Optuna-name matches; the archive was not extracted. These checks do not prove global absence or recover the log contents.

The 1,438-entry cleanup inventory was also searched by basename for the exact requested V3M/V3P manifests, internal panel index, label-separation file, expected loader, Optuna database, and quarantine files. None was listed. Terms for V3H/V3S/V3M/V3P, loader, quarantine, split names, panel index, SQLite and manifest matched zero entries; the only Optuna matches were the six logs above. The exact target names and counts are in the receipt. This is a negative result for that inventory only; it does not extend to unlisted snapshots or all of CEDIA.

The new evidence changes the provenance description, not the scientific status: the six logs are now `REFERENCED_ONLY`, the SQLite study and trial-to-released-checkpoint link remain unrecovered, and A-06 remains at its existing evidence ceiling. No reviewer item is upgraded by a cleanup inventory entry.
