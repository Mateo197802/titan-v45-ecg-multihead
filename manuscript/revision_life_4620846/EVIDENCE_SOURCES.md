# Scientific evidence for the Life revision

**Scope:** author-review draft, not a finding of independent external validation or journal acceptance.

| Claim | Evidence source | Limit |
|---|---|---|
| P6, P8 and P4 decisions | `outputs/results/external_dev/` metrics and evidence CSVs; `RELEASE_RECALCULATION.json` records input hashes | Recalculation from archived predictions, not new inference or clinical adjudication |
| P4 label mapping | `docs/reviewer_closure/REVIEWER_12_SCOPE_CLARIFICATIONS_2026-11-12.md`; P4 panel manifest and source SCP audit | 962/962 statement mappings, not 962 independent ECGs or patient adjudications |
| V3C trial 6 | `outputs/results/optuna/v3c_promoted_configuration.json`; historical hash-matched selection reports and nine-row Optuna export | Reported search and selected parameters, not a full study database |
| Job 16768 | Preserved `slurm-16768.out` bytes, archived job report, and live Slurm accounting. Member SHA and 50 aggregate epoch rows are supplied. | Source stdout and job configuration are not read/write digest bindings |
| Job 16781 and V3F | `docs/reviewer_closure/V3F_HISTORICAL_FINETUNE_REPORTS_HASH_MATCH_2026-11-11.md` on draft forensic PR #17; live Slurm; historical CEDIA path digest | Historical named output matches release, but the intermediate checkpoint and exact reads/writes are not authenticated |
| Release weight identity | `outputs/models/release_weight_manifest.json`, [GitHub release v0.1.0](https://github.com/Mateo197802/titan-v45-ecg-multihead/releases/tag/v0.1.0), CEDIA file-check receipts | Five matching files, not proof of their producing jobs or training data |
| AF and PVC unit | `docs/af-reference-contract.md`, `docs/reviewer_closure/AF_PVC_REFERENCE_DISPOSITION.md` and archived profile predictions | Retained statements, not incident AF or PVC beat detection |
| SPH retrospective transfer | `outputs/results/external_sph/sph_aggregate_32669.json` and jobs 33357/33399; `docs/reviewer_experiments/ORIGINAL_MANUSCRIPT_CHANGE_MAP.md` | Distinct retrospective analyses on mapped statements; not the ongoing independent study |
| Other | Aggregates for jobs 33390 and 33396 and `docs/reviewer_closure_experiments/OTHER_CLASS_VALIDATION.md` | New development heads, not released specialist performance |
| Morphology | `docs/reviewer_two_comment_rigorous/R2_3F_MORPHOLOGY_FINAL_VALIDATION.md`; 33795/33796 | Instrumented reconstruction and new fixed-backbone heads; not exact June runtime |
| Withholding and partial fallback | `docs/reviewer_two_comment_rigorous/R2_4K_SELECTIVE_PREDICTION_FINAL_VALIDATION.md` and `R2_4K_CASCADE_EXPERIMENT.md`; 33414/33796/33799 | Later score-only analysis and actual partial P6 stage; no historical clinical quarantine |

The integrated Git baseline is `6f50a6337fc3e8b518655b05916ced7447598b47`. PRs #3, #4, #6, #7, #8, #9, #12, #13, and #14 were merged when verified. Corrective #15, #16 and forensic #17 were open drafts and are not treated as main. Release metadata and CEDIA accounting were checked in this revision. No retraining, threshold change or external-gate submission was made.

The manuscript uses the existing 40-criterion evidence rubric without adding points for editorial changes. The baseline is 20.5/40 (51.25%); R1-4 is 1/2 and R2-3a is 2/3. Unverified items remain unverified even where a narrower editorial answer is possible. R1-1 requires new independent evidence; R1-2, R2-general, R2-3a and R2-4a retain substantive limits. The other ten entries can be reviewed by the authors as bounded responses, not as editor-approved closures.
