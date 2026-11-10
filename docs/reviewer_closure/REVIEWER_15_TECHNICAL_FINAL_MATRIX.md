# Reviewer 15 Technical Final Matrix

**As of:** 2026-11-10

**Source:** [`REVIEWER_48_DETAILED.json`](REVIEWER_48_DETAILED.json), PR #3 HEAD checked at `381c8943189ade49ca1cb29b3b65be97133ada83`.

**New CEDIA receipt:** [`CEDIA_JOB_LOGS_2026-11-10.json`](receipts/CEDIA_JOB_LOGS_2026-11-10.json).

**Manuscript:** `SIN_EDITAR`. No submitted PDF, response letter, checkpoints, thresholds or archived predictions were changed.

## Disposition

This matrix covers the 15 technically substantive reviewer comments, not all 36 reviewer comments. The remaining 21 are editorial-only; the 12 `A-*` entries are internal audits and remain separate in the 48-item source matrix.

| Reviewer item | Technical status | Reviewer satisfaction | What is still needed |
|---|---|---|---|
| R1-1 | `EXPERIMENT_COMPLETED_WITH_LIMITATIONS` | `PARTIALLY_ADDRESSED` | Independent data and complete lineage; identify V3H as a P6 selection/gate population. |
| R1-2 | `EXPERIMENT_COMPLETED_WITH_LIMITATIONS` | `PARTIALLY_ADDRESSED` | Authentic June parent denominator/exclusions and quarantine ledger. |
| R1-3 | `VERIFIED_WITH_LIMITATIONS` | `PARTIALLY_ADDRESSED` | Clinical/longitudinal reference before incident-AF claims. |
| R1-4 | `VERIFIED_WITH_LIMITATIONS` | `PARTIALLY_ADDRESSED` | Original Optuna DB and generic prediction artifact; PR #4 stays separate. |
| R2-general | `NEW_EXPERIMENT_REQUIRED` | `NOT_SATISFIED` | Approved ontology, labels and a new all-class experiment. |
| R2-2b | `ACTIVE_RECOVERY_REQUIRED` | `PARTIALLY_ADDRESSED` | Author/rightsholder confirmation of creator and permissions. |
| R2-3a | `EVIDENCE_CEILING_REACHED` | `PARTIALLY_ADDRESSED` | Job-linked training/calibration manifests, exclusions and patient maps. |
| R2-3c | `VERIFIED_WITH_LIMITATIONS` | `PARTIALLY_ADDRESSED` | Historical loss masks/supports for primary, cascade and auxiliary labels. |
| R2-3d | `EVIDENCE_CEILING_REACHED` | `NOT_SATISFIED` | Historical ALMI/ILMI/LAE supervision, masks and metrics. |
| R2-3e | `VERIFIED_WITH_LIMITATIONS` | `PARTIALLY_ADDRESSED` | Historical role/transition ledger and any actual reviewer actions. |
| R2-3f | `EVIDENCE_CEILING_REACHED` | `PARTIALLY_ADDRESSED` | Original loader and checkpoint-linked implementation; P4 strict score equivalence fails. |
| R2-4a | `VERIFIED_WITH_LIMITATIONS` | `PARTIALLY_ADDRESSED` | Use development terminology; do not claim independence without a new eligible cohort. |
| R2-4e | `EXPERIMENT_COMPLETED_WITH_LIMITATIONS` | `PARTIALLY_ADDRESSED` | State no-threshold/fallback behavior; historical quarantine remains unassessed. |
| R2-4k | `EVIDENCE_CEILING_REACHED` | `NOT_SATISFIED` | Authentic quarantine score/policy/denominator/ledger or withdraw the claim. |
| R2-5 | `VERIFIED_WITH_LIMITATIONS` | `PARTIALLY_ADDRESSED` | Keep PVC at ECG-statement level unless beat labels and a new protocol are supplied. |

No reviewer-satisfaction label was upgraded during this pass. A reproducible bounded finding does not satisfy broader clinical, independence or historical requests.

## Companion Evidence

- [CEDIA job-log receipt](receipts/CEDIA_JOB_LOGS_2026-11-10.json)
- [Bounded historical recovery](HISTORICAL_RECOVERY_FINAL_EXECUTION.md)
- [Checkpoint/job/manifest edges](CHECKPOINT_JOB_MANIFEST_VERIFICATION_FINAL.md)
- [192/512 specialist width disposition](SPECIALIST_192_512_ARCHITECTURE_RESOLUTION.md)
- [Component-level reproducibility matrix](REPRODUCIBILITY_EXECUTION_MATRIX.json)
- [Dataset eligibility](GENERALIZATION_DATASET_ELIGIBILITY.md), [future independent-evaluation protocol](GENERALIZATION_EXPERIMENT_PROTOCOL.md), and [run status/results](GENERALIZATION_EXPERIMENT_RESULTS.md)
- [Per-class aggregate metrics](GENERALIZATION_PER_CLASS_METRICS.json) and [aggregate error analysis](GENERALIZATION_ERROR_ANALYSIS.md)
- [Other-class boundary](OTHER_CLASS_COVERAGE_EXPERIMENT.md), [auxiliary training evidence](AUXILIARY_CLASS_TRAINING_EVIDENCE.md), and [selective-prediction/quarantine disposition](SELECTIVE_PREDICTION_EXPERIMENT.md)

## Individual Findings

### R1-1 — External validation and generalization
**Request:** Distinguish development holdouts from independent external validation, report source-level splits or evaluate a genuinely independent cohort, and limit generalizability claims.

- **Verified:** The later SPH transfer covered 25,770 ECG from 24,666 source patients and 14 compatible statement endpoints, but SPH had already been consulted.
- **New CEDIA evidence:** Job 17314 retains external metrics for 12 P6 epochs. Job 17315 names the V3H accepted/balanced manifest and evaluates epoch 8 against gates of 0.95 top-1 accuracy and 0.80 macro-F1. It reports 1,564/1,643, 0.9519172246 accuracy and 0.8009383240 macro-F1. The values match the rounded P6 headline. Thus the P6 external-development population was used for checkpoint gating; it is not an independent test.
- **What remains:** The sweep log lacks a manifest digest, and complete V3F/V3AG training-source/patient/signal lineage is missing. The job evidence does not create clinical adjudication or prospective validation.
- **Next action:** Report V3H as development/model-selection evidence. Use a new eligible cohort only if the authors retain an independent-generalization claim.
- **Evidence:** [`CEDIA job receipt`](receipts/CEDIA_JOB_LOGS_2026-11-10.json), [`cohort independence audit`](GENERALIZATION_AND_COHORT_INDEPENDENCE_AUDIT.md), [`split lineage`](CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md).

### R1-2 — Complete workflow and denominator
**Request:** Give the full population, routing, exclusions and pre/post-quarantine results.

- **Verified:** The later SPH transfer has a full technical denominator, but it is not the June V4.5 parent population.
- **Not recovered:** The parent population before selection/balancing, exclusion reasons and the historical quarantine ledger.
- **Interpretation:** A selected cohort cannot reconstruct its parent denominator. Null quarantine means not assessed, not 0%.
- **Next action:** Use only the bounded SPH flow description; seek the authentic parent/exclusion ledger only if a custodian identifies another backup.
- **Evidence:** [`all-input coverage`](ALL_INPUT_FLOW_COVERAGE.md), [`recovered vs missing`](RECOVERED_VS_MISSING_HISTORICAL_EVIDENCE.md), [`quarantine disposition`](QUARANTINE_HISTORICAL_VS_PROSPECTIVE.md).

### R1-3 — AF reference and timing
**Request:** Explain AF label harmonization, multiple labels and incident/prevalent status.

- **Verified:** Retained AF flags agree with the code mapping for P6 1,643/1,643 and P8 2,193/2,193; one AF/NSR co-occurrence remains unadjudicated.
- **Not established:** Onset, first diagnosis, longitudinal AF and independent clinical adjudication.
- **Next action:** Describe source-coded AF statement presence only; authors approve removal of incident-AF language unless suitable longitudinal data are available.
- **Evidence:** [`AF/PVC reference disposition`](AF_PVC_REFERENCE_DISPOSITION.md), [`AF recheck receipt`](receipts/AF_REFERENCE_RECHECK_2026-11-10.json).

### R1-4 — A10 hashes and Optuna
**Request:** Replace placeholders with measurements for the actual model, optimization and prediction artifacts.

- **Verified within PR #4:** Five physical model hashes/sizes and the A10 correction are documented there.
- **Not recovered:** Original Optuna SQLite/WAL/SHM and the generic prediction artifact/checkpoint linkage.
- **Next action:** Keep A10/Optuna in PR #4. Do not infer a complete trial history from partial CSVs or job failures.
- **Evidence:** [PR #4 A10/Optuna disposition](https://github.com/Mateo197802/titan-v45-ecg-multihead/pull/4), [A10 correction note](../hash-correction-20261028.md), and [`scheduler receipt`](receipts/CEDIA_JOB_LOGS_2026-11-10.json).

### R2-general — Other classes
**Request:** Train/evaluate Other arrhythmia and Other pathology and route them through the full cascade.

- **Verified:** The global output contracts and operational P6/P8/P4 scopes are explicit.
- **Not satisfied:** No validated `Other` class, complete ontology or all-input reference set exists. NSR is a rhythm class, not Other.
- **Next action:** A clinical/author-approved ontology and new labeled experiment are required. Absence of a code cannot create a negative label.
- **Evidence:** [`class coverage audit`](FULL_CLASS_COVERAGE_AND_ROUTING_AUDIT.md), [`Other experiment boundary`](OTHER_CLASS_COVERAGE_EXPERIMENT.md).

### R2-2b — Figures 1 and 2 provenance
**Request:** Explain figure purpose and source.

- **Verified:** Archived source-file provenance, callouts and hashes are recorded.
- **Requires humans:** Creator identity, third-party rights/permissions and whether every depicted operation actually occurred.
- **Next action:** Authors confirm attribution/permissions and approve later figure explanation.
- **Evidence:** [`figure provenance`](R2-2B_FIGURES_1_2_PROVENANCE.md).

### R2-3a — Databases and splits
**Request:** Report datasets/classes, segment counts and ECG/patient counts for train, validation and test.

- **Verified:** Selected units are P6 1,643 ECG; P8 2,193 ECG including P6; P4 962 panel observations over 733 ECG/676 linked patients; SPH 25,770 ECG/24,666 source patients.
- **Newly cross-checked:** Job 17315 names internal and V3H evaluation manifest aliases. Job 17296 uses different V3M internal-calibration and V3S external-panel aliases; its 962 panel observations and final metric/threshold vector match the rounded P4 release values.
- **Not recovered:** Full historical training/validation/calibration manifests, patient maps, exclusions and released-checkpoint hashes. The different manifest names do not establish patient separation.
- **Next action:** Present selected denominators with units; keep historical patient-isolation status unknown.
- **Evidence:** [`checkpoint/job receipt`](receipts/CEDIA_JOB_LOGS_2026-11-10.json), [`final lineage audit`](CHECKPOINT_JOB_MANIFEST_VERIFICATION_FINAL.md), [`split lineage`](CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md).

### R2-3c — Rhythm primary, cascade and auxiliary labels
**Request:** Explain training/evaluation roles and whether NSR is rare.

- **Verified:** The global contract has 14 rhythm outputs; P8 has eight operational labels and P6 six. SPH recorded 16,700 NSR top-1 outputs; that is not prevalence.
- **Not recovered:** Historical per-class supervision, loss masks, positive/negative supports and checkpoint-linked evaluation for auxiliary/cascade outputs.
- **Next action:** Do not claim auxiliary training/performance solely because scores are emitted.
- **Evidence:** [`role/supervision audit`](ROLE_SUPERVISION_AND_ROUTING.md), [`auxiliary evidence`](AUXILIARY_CLASS_TRAINING_EVIDENCE.md).

### R2-3d — ALMI, ILMI and LAE
**Request:** Establish whether these labels were trained/evaluated or only emitted as auxiliary outputs.

- **Verified:** The outputs exist in the seven-class global pathology contract; reconstructed P4 inference emitted scores on 733 selected ECG.
- **Not satisfied:** Historical supervision supports, masks, manifests, checkpoint-linked metrics and selection evidence are absent.
- **Next action:** Restrict claims to output emission unless authentic training evidence is recovered; any new evaluation is a separate study.
- **Evidence:** [`auxiliary class evidence`](AUXILIARY_CLASS_TRAINING_EVIDENCE.md), [`pathology replay`](../../outputs/results/revision_20261107/pathology_waveform.json).

### R2-3e — Role and cascade transitions
**Request:** Define Table 5 `Role` and how assignments/transitions occur.

- **Verified within reconstructed run:** P8 has 58 selected-cohort fallbacks; reference labels were not used for routing.
- **Not recovered:** Authentic historic role ledger and actual human review actions/outcomes.
- **Next action:** Define code-level roles only; do not call fallback, empty sets or quarantine-not-assessed human review.
- **Evidence:** [`all-input flow`](ALL_INPUT_FLOW_COVERAGE.md), [`routing provenance`](OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md).

### R2-3f — Loader, morphology and replay
**Request:** Define the ten morphology features and figure arrows, and reproduce the original preprocessing.

- **Verified within the reconstructed run:** P4 decisions agree 962/962, but max score residual is `0.0006194114685058594`, exceeding `1e-5`; P6 has one top-1 mismatch/1,643; P8 top-1/binary sets agree 2,193/2,193.
- **Not recovered:** Exact 36,271-byte historical loader with expected SHA-256 `fc8d7367f9f2c108376839435021ec3172fe2757faa4a615f0ef5d39cbf1e855`. The 32,435-byte candidate is not the original.
- **192/512:** The waveform receipt records 192 declared vs 512 stored for P6/P8. A recovered trainer using 512 classwise heads is not checkpoint-linked, so it does not prove the historical cause.
- **Next action:** Preserve thresholds and replay residuals; report the loader and width limitations explicitly.
- **Evidence:** [`loader/replay audit`](HISTORICAL_LOADER_IDENTITY_AND_REPLAY.md), [`192/512 resolution`](SPECIALIST_192_512_ARCHITECTURE_RESOLUTION.md), [`equivalence disposition`](REPLAY_EQUIVALENCE_DISPOSITION.md).

### R2-4a — External-development package
**Request:** Define package membership and whether it is a test independent from training.

- **Verified:** Cohort units and model selection exposure are bounded by retained manifests/logs.
- **Not satisfied:** P6's V3H population was used for model gating, and complete pretraining/source independence is not certified.
- **Next action:** Describe development/selection use and reserve independent validation claims for a new eligible cohort.
- **Evidence:** [`CEDIA job receipt`](receipts/CEDIA_JOB_LOGS_2026-11-10.json), [`cohort independence audit`](GENERALIZATION_AND_COHORT_INDEPENDENCE_AUDIT.md).

### R2-4e — No-threshold behavior
**Request:** Explain how no class crossing its threshold is handled.

- **Verified:** On SPH, P6 had 16,785 empty sets, P4 8,343 and P8 801 forced top-1 fallbacks; on the selected waveform replay P8 had 58 fallbacks.
- **Not established:** These outcomes are not Other, quarantine, abstention or human review. Historical quarantine remains unassessed.
- **Next action:** Describe exact profile behavior and population, then separately state that no frozen quarantine policy is evidenced.
- **Evidence:** [`class/routing audit`](FULL_CLASS_COVERAGE_AND_ROUTING_AUDIT.md), [`quarantine disposition`](QUARANTINE_HISTORICAL_VS_PROSPECTIVE.md).

### R2-4k — Quarantine rates
**Request:** Define quarantine rate and pre/post-quarantine accuracy.

- **Not recovered:** Original score, policy, denominator and per-ECG pre/post ledger.
- **Verified boundary:** SPH and replay receipts mark quarantine as unassessed with a null rate. Null is not 0%.
- **Next action:** Withdraw unsupported historical rates or recover the authentic ledger; a new selective-prediction study requires a distinct protocol and data.
- **Evidence:** [`quarantine historical vs prospective`](QUARANTINE_HISTORICAL_VS_PROSPECTIVE.md), [`routing provenance`](OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md).

### R2-5 — PVC unit of analysis
**Request:** Distinguish ECG-level PVC classification from beat-level detection.

- **Verified:** V4.5 evidence is ECG-record/statement level.
- **Not measured:** Beat timing, localization, episode counts and beat-level clinical adjudication.
- **Next action:** Limit the claim to ECG-level PVC statement classification unless a beat-labeled study is separately approved.
- **Evidence:** [`AF/PVC reference disposition`](AF_PVC_REFERENCE_DISPOSITION.md), [`metric definitions`](METRIC_DEFINITIONS.md).

## Reproducibility and Approval Boundary

The CEDIA receipt includes checksums for the retained job logs and the surviving 17296 launcher, plus only aggregate metrics. Raw logs and patient-level material remain in authorized CEDIA storage. Job completion, different manifest names, checkpoint metadata and rounded metric agreement are not substitutes for manifest bytes, patient maps or a checkpoint SHA edge.

No independent dataset was eligible and executed in this pass. No external files were downloaded, no jobs were submitted, no GPU was used, and no manuscript or response letter was regenerated. Scientific interpretation, figure rights, ontology, and final manuscript wording remain subject to author approval.
