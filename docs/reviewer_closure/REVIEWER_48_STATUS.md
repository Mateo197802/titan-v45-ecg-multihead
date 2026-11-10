# Reviewer and audit disposition

This is a technical index, not a response to reviewers or proof of editorial
acceptance. SPH scoring and statement-level aggregation have been performed;
their source-independence limitations remain. The submitted manuscript is unchanged.
The descriptions below are short project paraphrases, not reviewer quotations.
The [commit and job index](EVIDENCE_COMMITS.md) records the public evidence chain.
The [detailed 48-item matrix](REVIEWER_48_DETAILED.md) is the authoritative
point-by-point disposition; the [technical closure](FINAL_TECHNICAL_EVIDENCE_CLOSURE.md)
and [evidence-to-claim map](EVIDENCE_TO_CLAIM_MAP.md) summarize it. The
manuscript-readiness checklist is for the later editorial phase only.

`MANUSCRIPT_UPDATE_ONLY` means editing or assembly remains, not that it has been
incorporated. `VERIFIED_WITH_LIMITATIONS` identifies evidence that does not
support the original claim in full. `CLAIM_WITHDRAWAL_REQUIRED` means the claim
needs removal or restriction; that is not equivalent to the requested study.
`EXPERIMENT_COMPLETED` describes the executed SPH analysis, not certified
historical independence or reviewer acceptance.
`EVIDENCE_CEILING_REACHED` records a bounded recovery conclusion, not a completed
historical experiment or a reviewer acceptance; new evidence can reopen it.
`ACTIVE_RECOVERY_REQUIRED` means a concrete provenance or rights fact remains
actionable; it is not manuscript-only work.

| ID | Concern | Disposition | Evidence / remaining action |
| --- | --- | --- | --- |
| R1-1 | Independent external validation | EXPERIMENT_COMPLETED | [SPH delivery audit](SPH_DELIVERY_AUDIT.md), [all-input coverage](ALL_INPUT_FLOW_COVERAGE.md), [CEDIA lineage](CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md), and the separate [exploratory PAC probe](../external_validation/sph_pac_probe_results.md). Commit `99b1065` adds a PAC-scoped, hash-pinned publication receipt and code-30/31 audit; code-31-only rows remain included, and the probe remains same-source, previously exposed and nonconfirmatory. Confusion-derived metrics are recalculated publicly; score metrics/intervals are bound to the CEDIA execution digests, not recomputed from restricted rows. This does not supply independent clinical validation. Jobs 17314/17315 show V3H informed P6 epoch selection; exact 17314 manifest is missing. |
| R1-2 | Population and flow denominator | EVIDENCE_CEILING_REACHED | [All-input coverage](ALL_INPUT_FLOW_COVERAGE.md), [bounded recovery](R1_2_EVIDENCE_CEILING.md), and [recovered-vs-missing inventory](RECOVERED_VS_MISSING_HISTORICAL_EVIDENCE.md); historical preselection population and exclusion reasons remain unavailable. |
| R1-3 | AF incidence versus ECG statement | VERIFIED_WITH_LIMITATIONS | [AF/PVC reference disposition](AF_PVC_REFERENCE_DISPOSITION.md); 390 retained AF flags agree with stored codes per overlapping profile, not an incident-AF study. |
| R1-4 | Invalid artifact hashes | VERIFIED_WITH_LIMITATIONS | [Hash correction](../hash-correction-20261028.md); separate PR #4, missing historical artifacts remain unavailable. |
| R2-general | Excluded classes and Other | CLAIM_WITHDRAWAL_REQUIRED | [All-input coverage](ALL_INPUT_FLOW_COVERAGE.md) reports all three profiles across 25,770 SPH ECG and the 14 compatible endpoints; the [PAC-only exploratory probe](../external_validation/sph_pac_probe_results.md) does not evaluate `Other` or the full cascade. `Other` and incompatible references remain unvalidated. |
| R2-1a | Define P6 and P4 in abstract | MANUSCRIPT_UPDATE_ONLY | Define terms in the future manuscript. |
| R2-1b | Define abbreviations on first use | MANUSCRIPT_UPDATE_ONLY | Check first occurrence in the future manuscript. |
| R2-2a | Introduction references | MANUSCRIPT_UPDATE_ONLY | Align citations with the final scope. |
| R2-2b | Origin and purpose of figures 1 and 2 | ACTIVE_RECOVERY_REQUIRED | [Archive-level provenance](R2-2B_FIGURES_1_2_PROVENANCE.md) verifies purpose, paths and image hashes; author/source records for creation, third-party assets and permissions remain outstanding. |
| R2-2c | Comparator selection | MANUSCRIPT_UPDATE_ONLY | Reassess comparison table against final scope. |
| R2-2d | Unreported parameters and comparability | MANUSCRIPT_UPDATE_ONLY | Mark missing parameters and avoid unequal comparisons. |
| R2-2e | SCP and abbreviations | MANUSCRIPT_UPDATE_ONLY | Define terms and verify usage. |
| R2-2f | Introduction table placement | MANUSCRIPT_UPDATE_ONLY | Resolve placement and claims in the future manuscript. |
| R2-3a | Datasets and splits | EVIDENCE_CEILING_REACHED | [Split audit](SPLIT_CALIBRATION_DISPOSITION.md), [checkpoint-to-split lineage](CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md), and [recovery inventory](RECOVERED_VS_MISSING_HISTORICAL_EVIDENCE.md); SLURM records completed jobs, but linked split manifests and patient isolation remain unavailable. |
| R2-3b | Design versus evaluation | MANUSCRIPT_UPDATE_ONLY | Distinguish architecture, historical development, V3H model selection, reconstructed replay and later SPH transfer; see [checkpoint lineage](CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md). |
| R2-3c | Auxiliary classes and training | VERIFIED_WITH_LIMITATIONS | [Role/supervision audit](ROLE_SUPERVISION_AND_ROUTING.md) and [auxiliary-output disposition](OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md); output contracts alone do not establish checkpoint-linked training support. |
| R2-3d | ALMI, ILMI and LAE training | EVIDENCE_CEILING_REACHED | [Role/supervision audit](ROLE_SUPERVISION_AND_ROUTING.md) and [auxiliary-output disposition](OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md); checkpoint-linked supervision remains unverified. |
| R2-3e | Role definitions | VERIFIED_WITH_LIMITATIONS | [Role and routing audit](ROLE_SUPERVISION_AND_ROUTING.md) and [quarantine provenance](OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md); distinguish code roles and selected replay from historical all-input routing. |
| R2-3f | Morphology and feature architecture | EVIDENCE_CEILING_REACHED | [Replay equivalence](REPLAY_EQUIVALENCE_DISPOSITION.md) and [loader identity audit](HISTORICAL_LOADER_IDENTITY_AND_REPLAY.md): exact loader remains absent; 962/962 decisions do not meet the 1e-5 probability tolerance. |
| R2-3g | Brier score in methods | MANUSCRIPT_UPDATE_ONLY | Add definition and remove unsupported numerical methods claim. |
| R2-3h | Accuracy equations and tasks | MANUSCRIPT_UPDATE_ONLY | Define rhythm and pathology endpoints separately. |
| R2-4a | External-development terminology | VERIFIED_WITH_LIMITATIONS | [Evidence status](../evidence-status.md) and [checkpoint lineage](CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md); V3H informed P6 selection, and SPH remains a separate transfer result with incomplete full-backbone lineage. |
| R2-4b | Figure cross-reference | MANUSCRIPT_UPDATE_ONLY | Correct figure reference. |
| R2-4c | Overstated F1 interpretation | MANUSCRIPT_UPDATE_ONLY | Use measured values and qualified language. |
| R2-4d | Figure metrics versus confidence intervals | MANUSCRIPT_UPDATE_ONLY | Describe what is actually plotted. |
| R2-4e | No threshold crossed | EXPERIMENT_COMPLETED_WITH_LIMITATIONS | [All-input coverage](ALL_INPUT_FLOW_COVERAGE.md) and [routing disposition](OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md): P6/P4 empty sets and P8 fallback on 801/25,770 SPH ECG are measured; they are not quarantine or human review. |
| R2-4f | Confusion matrix presentation | MANUSCRIPT_UPDATE_ONLY | Harmonize labels and denominators. |
| R2-4g | Duplicated figures | MANUSCRIPT_UPDATE_ONLY | Reconcile figures against their source data. |
| R2-4h | ROC and PR tracing definition | MANUSCRIPT_UPDATE_ONLY | Define plotted units and derivation. |
| R2-4i | AUROC wording | MANUSCRIPT_UPDATE_ONLY | Qualify the interpretation of the reported value. |
| R2-4j | Frequency versus accuracy plot | MANUSCRIPT_UPDATE_ONLY | Verify axes, bins and denominators. |
| R2-4k | Quarantine and pre/post rates | CLAIM_WITHDRAWAL_REQUIRED | [All-input coverage](ALL_INPUT_FLOW_COVERAGE.md), [routing audit](ROLE_SUPERVISION_AND_ROUTING.md), and [quarantine provenance](OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md): no linked uncertainty-policy ledger; rate is not assessed, not zero. |
| R2-4l | Rhythm top-1 | MANUSCRIPT_UPDATE_ONLY | Define the decision and denominator. |
| R2-4m | Figure readability | MANUSCRIPT_UPDATE_ONLY | Final layout and rendering remain pending. |
| R2-5 | PVC record versus beat level | VERIFIED_WITH_LIMITATIONS | [AF/PVC reference disposition](AF_PVC_REFERENCE_DISPOSITION.md); SPH comparisons are ECG statements, not validated beat detection. |
| R2-6 | Distortion and citation claim | MANUSCRIPT_UPDATE_ONLY | Remove unsupported general claim and verify citation. |
| A-01 | P4 panel versus unique ECG count | VERIFIED_WITH_LIMITATIONS | [Data dispositions](../revision-data-dispositions.md); preserve 962 panel rows and 733 distinct record keys. |
| A-02 | Source distribution and aliases | VERIFIED_WITH_LIMITATIONS | [Source and rights disposition](SOURCE_RIGHTS_DISPOSITION.md); checksum matches and source aliases do not prove independent institutions or patient isolation. |
| A-03 | Per-class metric inconsistencies | MANUSCRIPT_UPDATE_ONLY | Use audited source tables and verify the final manuscript values. |
| A-04 | Thresholds and calibration isolation | VERIFIED_WITH_LIMITATIONS | [Split and calibration audit](SPLIT_CALIBRATION_DISPOSITION.md) and [CEDIA source triage](EVIDENCE_SOURCE_TRIAGE.md); P4 thresholds and P6/P8 vector dimensions are reconciled, but released-checkpoint linkage and patient isolation remain unverified. |
| A-05 | Backbone relationships | MANUSCRIPT_UPDATE_ONLY | Describe shared V3F and separate V3AG accurately. |
| A-06 | Optuna history and quarantine | CLAIM_WITHDRAWAL_REQUIRED | [Optuna/A10 evidence is tracked separately in PR #4](https://github.com/Mateo197802/titan-v45-ecg-multihead/pull/4); nine trial rows survive, but the original study database, complete history and promotion linkage are unavailable. |
| A-07 | Data availability URL | MANUSCRIPT_UPDATE_ONLY | Cite the verified final artifact and restricted inputs. |
| A-08 | Missing supplement CSVs | MANUSCRIPT_UPDATE_ONLY | Inventory only files actually included in the final supplement. |
| A-09 | Incorrect DOI | MANUSCRIPT_UPDATE_ONLY | Verify replacement reference in the final bibliography. |
| A-10 | Mixed archive provenance and rights | VERIFIED_WITH_LIMITATIONS | [Source and rights disposition](SOURCE_RIGHTS_DISPOSITION.md); 84 selected signals identified, package-wide additional redistribution remains on HOLD, and the existing release asset remains public. |
| A-11 | MC/Grad-CAM clinical claims | CLAIM_WITHDRAWAL_REQUIRED | No clinical adjudication established; remove unsupported claims. |
| A-12 | Reader study | CLAIM_WITHDRAWAL_REQUIRED | No reader study established; remove unsupported claims. |

Do not infer that an editorial disposition or a withdrawn claim satisfies a
requested experiment. Authors must review the scientific scope and final text;
the editor decides whether the submitted revision addresses the comments.
