# Session-recovery evidence audit and 15-item coverage (11 November 2026)

**Scope:** incremental, privacy-safe audit of historical TITAN V4.5 sessions and CEDIA receipts. This is **not** an updated manuscript, a completed training replay, a new validation experiment, or an assertion of independent generalization. Raw/private ZIPs, model weights, row-level files, SQLite binaries and unredacted sessions are **not** published.

## Packages independently inspected

| Private input ZIP (SHA-256) | Independent ZIP check | In-package manifest check |
|---|---|---|
| `TITAN_V45_SESSION_RECOVERY_20261111.zip` — `32acce689604afb3babb3e7f5e7d162005ab46153a9a4e073631849997914c07` | 93 members; CRC OK | 92/92 SHA-256 OK |
| `TITAN_V45_SESSION_EVIDENCE_RECOVERY_2026-11-11.zip` — `4ea43dae0c97d008696f5ad02094efc83a5bc75f0816d56554a9cd7fae36141b` | 465 members; CRC OK | Outer manifest 464/464 SHA-256 OK |
| `TITAN_V45_SESSION_EVIDENCE_2026-11-11_shareable.zip` — `c60eab5556db4396719c071506bf4ab95a52640e9fd07542ad4626f9ff54c6ab` | 70 members; CRC OK | 69/69 SHA-256 OK |

Checks establish package integrity, **not** historical job-byte consumption. Source/remote comparison of 316 CEDIA log copies is supported by packaged remote/local SHA receipts, but was **not independently rerun over SSH in this integration**. The source package reports 316 log files (1,894,937 bytes), four source-session fingerprints, 47 exact selected records plus one withheld sensitive record, 84 additional screened archived outputs, and fingerprints for 12 current curated train/validation manifests.

## Findings with version boundaries

1. **V4 legacy, not V4.5:** The private package contains two original Primary-9 Optuna SQLite studies. Independent SQLite read-only `integrity_check` on extracted copies passes. Primary search: 21 trial rows (17 COMPLETE, 3 FAIL, 1 RUNNING). OPTUNA_MAX: 7 rows (6 COMPLETE, 1 RUNNING). The OPTUNA_MAX study has trial 5 value `0.8940844424620394`; the other study reports trial 4 value `0.8660466503602587`. These are separate V4 studies and do not supply V4.5 41M scores, external evaluation or checkpoint promotion.
2. **V4.5 41M, V5 rescue:** The preserved original CEDIA log `slurm_screening_v5_rescue_20260605_14341.log` has SHA-256 `1afcb37ddd76d18537145fad158e0d72eea9856c7ca11a76c90a61472132b5f5`. Log/session evidence reports trial 37 as the best completed screening trial, ranking/composite `0.41769041461394363`, and 8 COMPLETE trials in the final summary. Its peak composite is reported as `0.422852413085241`.
3. **V4.5 41M, V6 controlled:** The preserved CEDIA log `slurm_screening_v6_controlled_15181.log` has SHA-256 `852abe295690ed5912a7de56f74d67d2d679e58b31dd3b35ad09cb9a80e9f206`. Records report best completed trial 35, ranking/composite `0.45876922957268035`, and 10 COMPLETE trials. The log has a reused `stage=screening_v5` field: identify this stage from the log filename **and** its printed study/DB reference, not that field alone. Neither V5 nor V6 original SQLite was recovered.
4. **Plan Q / Plan R / R2:** Exact archived session tool-output records preserve a completed refinement score near `0.5024`, a **non-completed** trial-49 score `0.5299` at epoch 20/25, split/probe metrics, and a failed/negative confirmation disposition. These are not final model metrics and are not comparable to the screening objective.
5. **Manifest fingerprints:** A live CEDIA cache inventory records 12 file hashes/sizes/row counts, but not the patient-level rows or evidence that V3C/V5/V6/released-checkpoint jobs consumed these exact bytes. No patient-isolation upgrade follows.
6. **Quarantine:** Original Plan AF logs for jobs 15903 and 15905 and secondary Plan AE/AF receipts survived; a reported 23 handoff **rows** and a denied gate remain supportable. The frozen policy and quarantine manifest bytes, eligible parent denominator, per-ECG transitions, checkpoint binding, and pre/post outcomes remain missing. Do **not** translate 23 rows into unique ECGs or a quarantine rate.

## Reviewer coverage: actual 40-subrequirement rubric

Source of scoring: [REVIEWER_15_COVERAGE_AND_CEILING.json](REVIEWER_15_COVERAGE_AND_CEILING.json), with exact per-requirement weights: verified bounded=1, bounded/indirect=0.5, absent/unassessed=0. This is **evidence coverage**, not an acceptance likelihood, and it does not imply manuscript changes. Nothing in the additional session packages completes an additional previously unmet subrequirement at the reviewer-specified population, checkpoint and task scope. Consequently, this integration **preserves** the existing percentages. A corroborating physical log is meaningful, but not a substitute for the requested full V4.5 Optuna SQLite or trial-to-checkpoint edge.

| Reviewer item | Demonstrated coverage | Critical remaining work |
|---|---:|---|
| R1-1 | 50.0% | Independent eligible population and full checkpoint-to-source/patient lineage |
| R1-2 | 33.3% | Original June parent denominator, exclusions, complete quarantine transitions |
| R1-3 | 50.0% | Clinical/longitudinal AF adjudication or restrict wording to ECG rhythm |
| R1-4 | 25.0% | V4.5 Optuna SQLite/full trial export, artifact correction and trial-to-checkpoint promotion; see PR #4 |
| R2-general | 50.0% | Validated Other-class ontology and complete-class evaluation |
| R2-2b | 50.0% | Proven author/rights provenance for figures |
| R2-3a | 50.0% | Exact training/calibration manifests and patient maps consumed by historical jobs |
| R2-3c | 83.3% | Class-wise loss masks/support and job-linked evidence |
| R2-3d | 83.3% | ALMI/ILMI/LAE effective historical supervision and metrics per released checkpoint |
| R2-3e | 50.0% | Historical role/clinical-review and transition ledger |
| R2-3f | 25.0% | Exact original loader and strict numerical replay |
| R2-4a | 75.0% | Full development exposure/lineage or an eligible independent cohort |
| R2-4e | 50.0% | Historical no-threshold/fallback and route linkage |
| R2-4k | 0.0% | Original quarantine policy/denominator/per-ECG pre/post outcomes |
| R2-5 | 50.0% | Beat-level PVC reference/protocol or constrained ECG-level claim |

**Aggregate:** `19.5 / 40 = 48.75%`; **newly verified additional full subrequirements: 0**. This is not a reversal of the substantive recovery: the newly preserved logs have stronger provenance than session summaries, but the threshold for *reviewer-requested closure* has not been crossed. The manuscript, submitted PDF, response letter and model artifacts were not changed.

## Highest-value next actions

- Custodian search for the exact Plan AE policy/manifest, job 15887 stdout, original eligible denominator and predictions.
- Recover V3C trial-6-to-V3F checkpoint read/write receipts and exact job-consumed manifests.
- Recover original V4.5 41M/V5/V6 SQLite generations or complete authenticated state exports; do not substitute the two V4 legacy SQLite studies.
- Obtain original 36,271-byte loader and patient-map linkage, if any surviving authoritative backup exists.
- Carry out author-approved manuscript scope corrections and any genuinely independent experiments separately from recovery.

**Publication boundary:** Only this sanitized methodological addendum is suitable for the open PR. Do not commit the ZIPs, source path inventories, raw logs, patient identifiers, trial-level private databases, model binaries or whole archived sessions.