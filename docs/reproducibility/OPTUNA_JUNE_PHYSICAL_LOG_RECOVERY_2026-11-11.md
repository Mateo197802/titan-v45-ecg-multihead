# June 2026 V4.5 screening: recovered physical logs and session evidence

**Recorded 11 November 2026.** Supplement to [OPTUNA_41M_NEW_EVIDENCE.md](OPTUNA_41M_NEW_EVIDENCE.md). This report distinguishes original CEDIA log bytes, archived tool-output text, V4 legacy databases and unrecovered V4.5 databases. It does not establish complete training reproducibility or update any trial result.

## Integrity and evidence classes

The original private recovery `TITAN_V45_SESSION_EVIDENCE_RECOVERY_2026-11-11.zip` has SHA-256 `4ea43dae0c97d008696f5ad02094efc83a5bc75f0816d56554a9cd7fae36141b`. ZIP CRC and its outer 464/464 manifest hashes were independently checked. The earlier `TITAN_V45_SESSION_RECOVERY_20261111.zip` has SHA-256 `32acce689604afb3babb3e7f5e7d162005ab46153a9a4e073631849997914c07`; its 92/92 internal checksums passed. No private binary is uploaded.

The package receipt reports 316 original CEDIA home logs (1,894,937 bytes) with source/local SHA matches. The hashes below were independently checked against *packaged* bytes; a current remote SSH recheck was not conducted in this integration. Retrieval-time digests are not independently anchored June 2026 signatures.

| Stage | Physical log basename | Preserved SHA-256 | Recorded result |
|---|---|---|---|
| V5 rescue, 41M | `slurm_screening_v5_rescue_20260605_14341.log` | `1afcb37ddd76d18537145fad158e0d72eea9856c7ca11a76c90a61472132b5f5` | Trial 37 best printed composite/ranking `0.41769041461394363`; final screen summary reports 8 COMPLETE |
| V6 controlled, 41M | `slurm_screening_v6_controlled_15181.log` | `852abe295690ed5912a7de56f74d67d2d679e58b31dd3b35ad09cb9a80e9f206` | Trial 35 best printed composite/ranking `0.45876922957268035`; 10 COMPLETE |

The V5 archived output also reports peak `0.422852413085241` and parameters (`base_lr=1.235699016878097e-05`, `max_lr=0.00019971603712748044`, `weight_decay=0.00016905053635969162`, `gamma=1.9526930109870293`, `label_smoothing=0.02366750322109276`, `batch_size=16`, `mixup_alpha=0.17139781199231766`, `lambda_pathology=0.3646205131260345`). These are **recorded** parameters, not an authenticated later promotion. The V6 log's embedded JSON reused a `stage=screening_v5` label; V6 identity is corroborated by its filename and printed `STUDY_DB` path. Neither complete Optuna SQLite nor sampler trajectory survives in these packages.

A separate 18-log collection documents 18 terminal-recorded finished-trial lines spread across **six different studies**: `screening_corrected_v2`, `screening_v5_rescue`, `screening_v6_controlled`, `plan_v_active12`, `plan_an_active14`, `plan_ap_full_physical`. Each log has an individual source SHA receipt and Slurm metadata; they must not be concatenated into a single 18-trial Optuna study. Source-level `COMPLETED` jobs are not guaranteed full-study success or checkpoint promotion.

## Other archived outcomes, kept separate

- Plan Q completed refinement best approximately `0.5024`; another trial (49) reached `0.5299` **only at epoch 20/25**. Its original refinement DB and completion receipt were not recovered; this does not pass a confirmation gate.
- Plan R/R2 logs provide split/calibration probes (including `0.580524` rhythm macro-F1 and a `0.646907` R2 calibrated validation score), **not** the same composite objective or a final test.
- The V3C nine-row snapshot and promoted trial 6 (`0.6245117257`) represent a different study and model path.
- Two newly recovered, read-only-integrity-checked **V4 legacy** `primary9_optuna` SQLite snapshots are separate from V4.5. Primary search has 21 rows (17 COMPLETE, 3 FAIL, 1 RUNNING), best COMPLETE trial 4 value `0.8660466503602587`; OPTUNA_MAX has 7 rows (6 COMPLETE, 1 RUNNING), best COMPLETE trial 5 value `0.8940844424620394`. Neither value is V4.5 41M final accuracy or external F1.

## Reviewer item R1-4 / audit A-06

The new physical log copies make the June V5/V6 *printed screening histories* stronger than archival chat references. They do **not** recover the original V4.5 SQLite generations, exact consumed data manifests, checkpoints, or trial-to-published-model hashes. PR #3's existing 40-subrequirement evidence rubric therefore remains at **R1-4 = 25.0%**, aggregate **48.75%**, pending source-linked artifacts. Do not raise those values because of a larger file count. No evidence was transferred to the manuscript.

## Private custody

The full ZIPs contain path/record metadata, source-session references and model-related files, so remain under authorized private custody. Only safe study names, aggregate results, filenames, verification outcomes and whole-file digests are reproduced here. No raw logs, record-level clinical data, SQLite binaries, credentials, checkpoint files or unredacted chat captures are committed.