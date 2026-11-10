# Reviewer 36 Closure Action Plan

**As of:** 2026-11-10

**Source of truth:** `docs/reviewer_closure/REVIEWER_48_DETAILED.json` at `575c5a5fa4dbcf658308c928aa7d08259fd61c9f`

**Manuscript state:** `SIN_EDITAR`; submitted manuscript, PDF and response letter were not changed.

**PR state:** PR #3 is open and draft; no merge was performed.

This reviewer-only view preserves each source record verbatim under `source_record`. The 12 internal audits remain in the authoritative 48-item matrix and are linked below, not counted as reviewer comments.

## Current disposition

- Reviewer comments: **36**.
- Internal audits linked separately: **12**.
- Reviewer satisfaction: `{"EDITORIAL_ACTION_ONLY": 21, "NOT_SATISFIED": 3, "PARTIALLY_ADDRESSED": 12}`.
- Technical status: `{"ACTIVE_RECOVERY_REQUIRED": 1, "EVIDENCE_CEILING_REACHED": 4, "EXPERIMENT_COMPLETED_WITH_LIMITATIONS": 3, "MANUSCRIPT_ONLY_PENDING": 21, "NEW_EXPERIMENT_REQUIRED": 1, "VERIFIED_WITH_LIMITATIONS": 6}`.
- These are categorical evidence states, not progress percentages and not a prediction of editorial acceptance.
- `EDITORIAL_ACTION_ONLY` means proposed manuscript work remains; it does not mean the reviewer request is already closed.

## Related technical and editorial drafts

- [Reproducibility gaps](REVIEWER_REPRODUCIBILITY_GAPS.md)
- [Code and formula audit](REVIEWER_CODE_AND_FORMULA_AUDIT.md)
- [Figure and table corrections](REVIEWER_FIGURE_TABLE_CORRECTIONS.md)
- [Populated reviewer-proposed tables](REVIEWER_PROPOSED_TABLES.md)
- [Claim disposition](REVIEWER_CLAIM_WITHDRAWAL_DECISIONS.md)
- [Response evidence draft](REVIEWER_RESPONSE_EVIDENCE_DRAFT.md)

## Recovery and experiment evidence

- [Historical recovery execution](HISTORICAL_RECOVERY_FINAL_EXECUTION.md)
- [Checkpoint-to-job-to-manifest verification](CHECKPOINT_JOB_MANIFEST_VERIFICATION_FINAL.md)
- [Specialist 192/512 architecture disposition](SPECIALIST_192_512_ARCHITECTURE_RESOLUTION.md)
- [Reproducibility execution matrix](REPRODUCIBILITY_EXECUTION_MATRIX.json)
- [External dataset eligibility](GENERALIZATION_DATASET_ELIGIBILITY.md)
- [Future independent-evaluation protocol](GENERALIZATION_EXPERIMENT_PROTOCOL.md)
- [Evaluation run status and existing results](GENERALIZATION_EXPERIMENT_RESULTS.md)
- [Per-class aggregate metrics](GENERALIZATION_PER_CLASS_METRICS.json)
- [Aggregate error analysis](GENERALIZATION_ERROR_ANALYSIS.md)
- [Other-class boundary](OTHER_CLASS_COVERAGE_EXPERIMENT.md)
- [Auxiliary training evidence](AUXILIARY_CLASS_TRAINING_EVIDENCE.md)
- [Selective prediction and quarantine](SELECTIVE_PREDICTION_EXPERIMENT.md)
- [15-comment technical closure matrix](REVIEWER_15_TECHNICAL_FINAL_MATRIX.md)
- [CEDIA sanitized job receipt](receipts/CEDIA_JOB_LOGS_2026-11-10.json)
- [CEDIA targeted Slurm accounting](receipts/CEDIA_TARGETED_SACCT_RECONCILIATION_2026-11-10.json)

## How to read each item

`recorded_result_or_population` and `scope_addressed` state what the current source matrix says is supported. `not_demonstrated_or_remaining` controls the boundary. Exact artifact hashes, job IDs and commit anchors remain in the linked evidence documents; a linked file is not treated as proof of job consumption unless the source record binds it. `reviewer_satisfaction` is kept distinct from technical status.

## Reviewer comments

### R1-1 — Reviewer 1, Round 1, first methodological comment

**Specific request:** Clarify that an external-development holdout from public sources used during development is not equivalent to independent external validation; provide source-level training, validation and holdout counts or evaluate a truly independent cohort, and moderate generalizability and deployment claims.

**Scope in manuscript:** Abstract, cohort description, Results, Discussion and deployment/generalizability claims.

**Evidence recorded:** Frozen transfer evaluated 25,770 SPH ECG from 24,666 source patients across P6, P8 and P4; all 14 compatible ECG-statement endpoints were scored with patient-component intervals. Newly recovered job 17314 records a P6 epoch sweep; job 17315 explicitly evaluates epoch 8 on the V3H accepted/balanced manifest at 1,564/1,643, accuracy 0.951917 and macro-F1 0.800938. This makes V3H model-selection/development evidence, not an untouched test. A separate fixed V3F-embedding PAC probe used the same SPH source and a 5,143-record exploratory patient holdout; its AUROCs were 0.910 (logistic) and 0.910 (MLP sensitivity), with no holdout tuning. The CEDIA audit found 539 code-30 records and 4 code-31 records (1 both, 3 code-31-only); all eligible rows remain in the code-30 statement endpoint, and absence is not a clinical negative. Commit 99b1065 publishes a scoped receipt binding the unchanged CEDIA aggregate and execution receipt. Confusion-derived metrics are recomputed publicly, while score metrics and intervals are digest-bound but not recalculated from restricted row scores. Prior Primary8 PAC target exposure and incomplete V3F source lineage keep this result nonconfirmatory. The exact 17314 manifest is not recorded. Complete V3F/V3AG pretraining and fine-tuning lineage remains unavailable.

**What the available evidence addresses:** A real full-source SPH transfer analysis and endpoint-specific results exist. New CEDIA accounting/logs also narrow the P6 validation claim by documenting V3H gate use and likely epoch-selection exposure. The PAC probe has a reproducible, hash-pinned aggregate publication and explicit code-30/31 target semantics, but does not establish an independent cohort, clinical adjudication or clinical validity.

**What it does not establish / what remains:** The 17314 sweep log and submitted script do not preserve the exact manifest binding; the same epoch-8 metrics and threshold vector appear in the immediately subsequent 17315 V3H gate report, strongly supporting use of that development holdout for selection but not providing a cryptographic same-file proof. Historical backbone/source overlap is not certified, labels are not clinical adjudication, and no truly untouched cohort has been selected.

**Evidence references:**
- `docs/reviewer_closure/SPH_DELIVERY_AUDIT.md`
- `docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`
- `docs/external_validation/sph_results.md`
- `docs/external_validation/sph_independence_assessment.md`
- `docs/external_validation/sph_pac_probe_results.md`
- `docs/reviewer_closure/EVIDENCE_SOURCE_TRIAGE.md`
- `docs/reviewer_closure/CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md`
- `docs/reviewer_closure/GENERALIZATION_DATASET_ELIGIBILITY.md`
- `docs/reviewer_closure/GENERALIZATION_EXPERIMENT_PROTOCOL.md`
- `docs/reviewer_closure/GENERALIZATION_EXPERIMENT_RESULTS.md`
- `docs/reviewer_closure/GENERALIZATION_PER_CLASS_METRICS.json`
- `docs/reviewer_closure/GENERALIZATION_ERROR_ANALYSIS.md`
- `docs/reviewer_closure/receipts/CEDIA_JOB_LOGS_2026-11-10.json`

**Traceability confidence:** An experiment was executed; this does not imply that the original request is fully satisfied.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** The current packages and NOC-reviewed backup do not recover the sweep script or full training manifests. Reopen only if exact job-linked scripts, manifests, checkpoint hashes and patient mappings are supplied. A new independent cohort is not recoverable from the current SPH evaluation.

**Experiment needed:** A new, admissible, patient- and signal-disjoint cohort is required if independent generalization is claimed.

**Proposed editorial action (not applied):** Describe V3H P6 as selected development/model-selection evidence, distinguish it from the later SPH transfer, and do not call either clinical validation or assert complete independence without the missing lineage. Remove untested deployment claims.

**Technical status:** `EXPERIMENT_COMPLETED_WITH_LIMITATIONS`

**Reviewer satisfaction:** `PARTIALLY_ADDRESSED`

**Next action class:** `REPORT_EXPERIMENT_WITH_LIMITS_AND_DECIDE_IF_NEW_STUDY_IS_NEEDED`

**Owner boundary:** Codex reports measured results and limits; authors approve claims; a new study is needed if the broader claim is retained.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** High if SPH transfer is described as independent validation or clinical effectiveness.

### R1-2 — Reviewer 1, Round 1, second methodological comment

**Specific request:** Report the complete clinical workflow, including primary and cascade classes, complete denominators, quarantine proportions, errors inside and outside quarantine, and predictive values under original prevalence; do not present a restricted denominator as end-to-end performance.

**Scope in manuscript:** Primary denominator, Results tables, cascade and quarantine claims.

**Evidence recorded:** The later SPH source has 25,770/25,770 scores per profile and all 14 compatible endpoint comparisons. The retained selected development replay has 2,193 P8 keys, including 1,643 P6 keys, plus 733 P4 keys: a verified 2,926-key P8/P4 union, not a patient count. Routing was computed without reference labels.

**What the available evidence addresses:** The measured all-source SPH profile coverage, empty-set/fallback counts and compatible predictive results are documented separately from selected-cohort replays.

**What it does not establish / what remains:** The June preselection population, exclusion reasons, complete all-class reference ontology and authentic historical quarantine policy/ledger remain unavailable. The recovered V3H accepted/balanced manifest is selected data, not the parent population. No pre/post quarantine rate can be calculated.

**Evidence references:**
- `docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`
- `docs/reviewer_closure/R1_2_EVIDENCE_CEILING.md`
- `docs/reviewer_closure/ROLE_SUPERVISION_AND_ROUTING.md`
- `outputs/results/external_sph/sph_aggregate_32669.json`
- `docs/reviewer_closure/RECOVERED_VS_MISSING_HISTORICAL_EVIDENCE.md`
- `docs/reviewer_closure/SELECTIVE_PREDICTION_EXPERIMENT.md`
- `docs/reviewer_closure/OTHER_CLASS_COVERAGE_EXPERIMENT.md`
- `docs/reviewer_closure/GENERALIZATION_EXPERIMENT_RESULTS.md`

**Traceability confidence:** An experiment was executed; this does not imply that the original request is fully satisfied.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** The supplied archives, exact historical paths and NOC-reviewed backup do not recover the historical parent population. Reopen only on receipt of parent manifests, exclusion reasons and checkpoint/job-linked routing ledger; this is not a global-absence finding.

**Experiment needed:** A complete all-class workflow with compatible reference labels and an explicit quarantine policy is required to satisfy the original request; SPH cannot retroactively supply the missing historical flow.

**Proposed editorial action (not applied):** Report selected denominators and measured SPH coverage; do not call either a reconstructed historical all-input workflow.

**Technical status:** `EXPERIMENT_COMPLETED_WITH_LIMITATIONS`

**Reviewer satisfaction:** `PARTIALLY_ADDRESSED`

**Next action class:** `REPORT_EXPERIMENT_WITH_LIMITS_AND_DECIDE_IF_NEW_STUDY_IS_NEEDED`

**Owner boundary:** Codex reports measured results and limits; authors approve claims; a new study is needed if the broader claim is retained.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** High if restricted Primary results are described as full clinical workflow accuracy or unmeasured quarantine benefit.

### R1-3 — Reviewer 1, Round 1, AF-label comment

**Specific request:** Describe how AF reference labels were created and harmonized by source, how multiple or conflicting labels were handled, and restrict language to ECG-level AF rather than incident or first-diagnosed AF without longitudinal evidence.

**Scope in manuscript:** AF endpoint definition, label harmonization and Discussion terminology.

**Evidence recorded:** Stored AF flags agree with retained code 164889003 for 1,643 P6 rows and 2,193 P8 rows; each overlapping profile has 390 positive rows and zero flag mismatches or unresolved code rows. P6 is nested within P8, so counts must not be added. A co-occurring normal-rhythm code was retained, not adjudicated.

**What the available evidence addresses:** The archived fields are internally consistent for the selected rows and the available contract supports ECG-record wording.

**What it does not establish / what remains:** The audit does not establish independent clinical adjudication for every source, onset, first diagnosis, incidence or patient-level longitudinal truth.

**Evidence references:**
- `docs/reviewer_closure/AF_PVC_REFERENCE_DISPOSITION.md`
- `docs/af-reference-contract.md`
- `outputs/results/revision_20261029/af_reference_consistency.json`

**Traceability confidence:** A bounded result is verified; residual limitations remain open.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** The current row-level code check is complete within its scope; incident AF cannot be recovered without longitudinal patient data and an appropriate reference.

**Experiment needed:** Longitudinal AF claims require a new study; no such study is needed if the claim is confined to ECG-level statements.

**Proposed editorial action (not applied):** State AF on the ECG, describe source-specific reference limitations and remove incident/first-diagnosed terminology unless authors supply longitudinal evidence.

**Technical status:** `VERIFIED_WITH_LIMITATIONS`

**Reviewer satisfaction:** `PARTIALLY_ADDRESSED`

**Next action class:** `DOCUMENT_LIMITS_AND_PREPARE_EDITORIAL_ACTION`

**Owner boundary:** Codex prepares precise wording; authors approve scope and interpretation.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** High for incidence or prognosis claims; moderate for pooled ECG statement classification because annotation policies differ.

### R1-4 — Reviewer 1, Round 1, cryptographic hashes comment

**Specific request:** Replace the empty-file and placeholder values in A10 with checksums for actual archived artifacts and provide an accessible verification route; otherwise remove unsupported cryptographic reproducibility claims.

**Scope in manuscript:** Appendix Table A10, artifact availability and reproducibility claims.

**Evidence recorded:** The submitted A10 contained one empty-file SHA-256 and four patterned example values. Five physical V3F/V3AG and specialist checkpoints have measured hashes, sizes and a release manifest in PR #4; Optuna DB and generic prediction artifact were not certified as recovered.

**What the available evidence addresses:** Actual model checkpoint identities are verifiable from the public release and separate correction evidence.

**What it does not establish / what remains:** The original Optuna database and generic prediction file are not located; the corrected artifact list is not a one-to-one substitute for every original A10 row.

**Evidence references:**
- `docs/hash-correction-20261028.md`
- `docs/reviewer_closure/EVIDENCE_COMMITS.md`
- `docs/reviewer_closure/HISTORICAL_EVIDENCE_HANDOFF.md`

**Traceability confidence:** A bounded result is verified; residual limitations remain open.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Bounded local/CEDIA/release checks found no verified copies of the two missing generic artifacts; a new authenticated backup listing could reopen this.

**Experiment needed:** No model experiment is needed for the five checkpoint hashes; do not fabricate hashes for missing files.

**Proposed editorial action (not applied):** Replace A10 with the verified artifact inventory and explicitly remove claims for unavailable artifacts; preserve the submitted PDF unchanged.

**Technical status:** `VERIFIED_WITH_LIMITATIONS`

**Reviewer satisfaction:** `PARTIALLY_ADDRESSED`

**Next action class:** `DOCUMENT_LIMITS_AND_PREPARE_EDITORIAL_ACTION`

**Owner boundary:** Codex prepares precise wording; authors approve scope and interpretation.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** High if unverified artifacts remain represented as hashed or reproducible.

### R2-general — Reviewer 2, Round 1, general class-scope comment

**Specific request:** Represent excluded rhythm and pathology classes as Other arrhythmia/Other pathologies, or otherwise report them so excluded classes and NSR are not hidden from realistic performance assessment.

**Scope in manuscript:** Class ontology, primary and cascade heads, Methods and full-population results.

**Evidence recorded:** The published architecture declares 14 rhythm and 7 pathology outputs; P8 includes NSR and PAC. SPH measured all profile predictions on 25,770 ECG, but only 14 endpoints have compatible statement references. P8 produced 16,700 NSR top-1 outputs; no validated Other output exists. The additional code-30 PAC probe reports one statement endpoint from the same SPH source; it is not an all-class evaluation and does not define or validate Other.

**What the available evidence addresses:** All-input profile decisions and the limits of declared auxiliary outputs are now visible; missing scores and incompatible labels are not converted to negatives. The separate PAC probe adds a fully reported model comparison for one endpoint only; it does not close the Other/cascade request.

**What it does not establish / what remains:** No validated Other class, complete ontology, class-level labels for all inputs, or evaluated primary-to-cascade performance is available.

**Evidence references:**
- `docs/reviewer_closure/ROLE_SUPERVISION_AND_ROUTING.md`
- `docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`
- `docs/revision-data-dispositions.md`
- `docs/external_validation/sph_pac_probe_results.md`
- `outputs/models/heads/global_head_contracts.json`
- `docs/reviewer_closure/OTHER_CLASS_COVERAGE_EXPERIMENT.md`
- `docs/reviewer_closure/GENERALIZATION_EXPERIMENT_RESULTS.md`

**Traceability confidence:** Current evidence does not satisfy the request; a distinct new experiment is required.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** The old outputs cannot establish the requested Other-class performance. A new dataset/reference mapping and model or routing evaluation would be needed.

**Experiment needed:** Required if the original all-class performance request is retained; not satisfied by narrowing text alone.

**Proposed editorial action (not applied):** Describe only evaluated primary endpoints and explicitly state that Other/cascade performance is not validated.

**Technical status:** `NEW_EXPERIMENT_REQUIRED`

**Reviewer satisfaction:** `NOT_SATISFIED`

**Next action class:** `DESIGN_AND_APPROVE_A_DISTINCT_NEW_EXPERIMENT`

**Owner boundary:** Authors/study team approve endpoint, data rights and protocol; Codex can implement and audit the approved workflow.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Very high if all-input or Other performance is implied from class declarations or fallback counts.

### R2-1a — Reviewer 2, Round 1, point 1, abstract

**Specific request:** Briefly explain what Primary6 rhythm specialist and Primary4 pathology specialist mean in the abstract and at first use in the main text.

**Scope in manuscript:** Abstract and first occurrence in the Introduction or Methods.

**Evidence recorded:** The release contract identifies P6 as six rhythm targets and P4 as four binary pathology panels; their model assets and evaluation units are separate.

**What the available evidence addresses:** The technical definitions are documented and can be stated without a new experiment.

**What it does not establish / what remains:** The submitted manuscript has not been revised to define the terms at the requested locations.

**Evidence references:**
- `docs/architecture.md`
- `docs/reviewer_closure/REVIEWER_48_STATUS.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** No historical recovery is needed.

**Experiment needed:** None; editorial clarification only.

**Proposed editorial action (not applied):** Add one-sentence definitions at both locations and retain distinct denominators.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Low if corrected; ambiguity remains until the manuscript is edited.

### R2-1b — Reviewer 2, Round 1, point 1, abbreviations

**Specific request:** Define abbreviations at first use throughout the manuscript, tables and figures.

**Scope in manuscript:** Whole manuscript, tables, captions and figures.

**Evidence recorded:** No model or dataset calculation is requested; the remaining work is a full-document terminology pass after scope and tables are fixed.

**What the available evidence addresses:** The need is identified but no final manuscript audit has been performed in this phase.

**What it does not establish / what remains:** First-use consistency in the submitted source remains unchecked against the final revised layout.

**Evidence references:**
- `docs/reviewer_closure/REVIEWER_48_STATUS.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Fully addressable in editorial review; no archive is needed.

**Experiment needed:** None.

**Proposed editorial action (not applied):** Expand each abbreviation on first use and verify captions independently.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Low scientific risk; substantial readability risk if left inconsistent.

### R2-2a — Reviewer 2, Round 1, point 2, Introduction references

**Specific request:** Add adequate references to the Introduction's general statements and make the study objective clear at the end of the section.

**Scope in manuscript:** Introduction before subsection 1.1 and final paragraph of the Introduction.

**Evidence recorded:** This is a literature and framing request. The final scope is constrained by measured selected-cohort and SPH transfer evidence, not a claim of clinical deployment.

**What the available evidence addresses:** The intended scope can now be bounded by the evidence package, but the bibliography has not been rewritten or fully checked here.

**What it does not establish / what remains:** Reference adequacy, citation-to-claim fit and the final objective wording remain to be assessed after the author-approved scope is fixed.

**Evidence references:**
- `docs/reviewer_closure/REVIEWER_48_STATUS.md`
- `docs/reviewer_closure/REVIEWER_48_DETAILED.json`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Addressable by bibliography review; no historical compute files are needed.

**Experiment needed:** None for citations; a broader scientific claim would require additional evidence, not just references.

**Proposed editorial action (not applied):** Audit each general claim against primary literature and state a narrow descriptive/evaluative objective.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Moderate if unsupported background claims or an overbroad objective remain.

### R2-2b — Reviewer 2, Round 1, point 2, Figures 1 and 2

**Specific request:** Explain the purpose of Figures 1 and 2 and identify their sources or provenance.

**Scope in manuscript:** Introduction figure captions, callouts and source acknowledgments.

**Evidence recorded:** The author-supplied source ZIP has SHA-256 36c1c6db30a759ef9d349ae2e545577cfd7ce3af91a3b97fb459380113f294a8 and contains the archived TeX callouts/captions and both figure PNGs. The figures match the repository manifest byte-for-byte; exact paths, hashes, dimensions and stated purposes are recorded in R2-2B_FIGURES_1_2_PROVENANCE.md.

**What the available evidence addresses:** The supplied archive establishes immediate source-package provenance and the purposes stated in its TeX: a proposed modular P6/P4 architecture (Figure 1) and a data-curation/harmonization workflow (Figure 2). This does not independently validate depicted historical operations.

**What it does not establish / what remains:** Creator/editor identity, any third-party assets and permissions are not established. The authors must confirm Figure 2's cohort/split claims against run-level evidence; the ZIP alone cannot prove execution or patient-level independence.

**Evidence references:**
- `docs/reviewer_closure/REVIEWER_48_STATUS.md`
- `docs/figure-evidence.md`
- `docs/reviewer_closure/R2-2B_FIGURES_1_2_PROVENANCE.md`
- `outputs/figures/figure_manifest.json`

**Traceability confidence:** A bounded recovery lead remains; no conclusion of global absence is allowed.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Archive-level provenance is recovered. Authorship, third-party source and rights require author/source records or licenses; if these cannot be established, replace or remove affected content.

**Experiment needed:** None unless a figure makes a new empirical claim.

**Proposed editorial action (not applied):** After author confirmation, attribute or identify the figures as author-created only if supported; narrow Figure 2 to verified operations and use an authorized replacement or remove it if origin/permissions remain unclear.

**Technical status:** `ACTIVE_RECOVERY_REQUIRED`

**Reviewer satisfaction:** `PARTIALLY_ADDRESSED`

**Next action class:** `BOUNDED_RECOVERY_THEN_CUSTODIAN_DISPOSITION`

**Owner boundary:** Codex performs only the identified bounded search; CEDIA custodian supplies any inaccessible archive; authors decide disposition if absent.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Moderate for unsupported provenance; high if an illustrative figure is presented as measured evidence.

### R2-2c — Reviewer 2, Round 1, point 2, Table 1 comparator selection

**Specific request:** Justify why Table 1 selects only Life/MDPI studies, replace the unsupported representative/comparator framing, and explain what the table is intended to compare.

**Scope in manuscript:** Introduction Table 1, caption and comparator rationale.

**Evidence recorded:** No new benchmark comparison has been performed. Existing published studies differ in task, label ontology, cohort, sampling, parameter reporting and evaluation unit, so their headline values are not directly comparable.

**What the available evidence addresses:** The non-equivalence risk is recognized; no replacement systematic or balanced literature table is yet verified.

**What it does not establish / what remains:** A defensible study-selection rule, broader sources and comparable task definitions are needed if the table remains.

**Evidence references:**
- `docs/reviewer_closure/REVIEWER_48_STATUS.md`
- `docs/revision-data-dispositions.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Editorial literature work is feasible; it should not be replaced by selecting only favorable studies.

**Experiment needed:** No model experiment; any quantitative comparison must use compatible published endpoints and disclose differences.

**Proposed editorial action (not applied):** Remove the Life-only selection or define a transparent, reproducible comparator scope and revise the caption.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** High risk of selection bias and misleading state-of-the-art claims if unchanged.

### R2-2d — Reviewer 2, Round 1, point 2, parameter reporting

**Specific request:** Explain missing architecture parameters, avoid comparisons between non-equivalent tasks, and clarify the table's purpose and direct-comparator terminology.

**Scope in manuscript:** Introduction Table 1 and architecture comparison text.

**Evidence recorded:** Repository model parameter counts and V4.5 architecture are documented, but many external papers report NR/proprietary values and unlike tasks cannot be normalized to a direct ranking.

**What the available evidence addresses:** The TITAN architecture's local parameter counts are documented; this does not fill missing comparator-study parameters.

**What it does not establish / what remains:** The manuscript table still needs explicit NR labels and task/cohort comparability caveats.

**Evidence references:**
- `docs/architecture.md`
- `docs/reviewer_closure/REVIEWER_48_STATUS.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Published comparator parameters can be checked from primary articles; undisclosed values cannot be reconstructed.

**Experiment needed:** None unless a new benchmark is proposed.

**Proposed editorial action (not applied):** Report verified model counts, mark unreported values NR and avoid implying a direct performance comparison.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Moderate to high if unequal tasks are presented as head-to-head evidence.

### R2-2e — Reviewer 2, Round 1, point 2, SCP and abbreviations

**Specific request:** Define SCP and every abbreviation used in the text, tables and figures.

**Scope in manuscript:** Introduction and all tables, legends and captions.

**Evidence recorded:** No scientific calculation is involved; the requested verification must run on the final manuscript and all figure assets.

**What the available evidence addresses:** The issue is catalogued but no final abbreviation pass is complete.

**What it does not establish / what remains:** SCP's intended expansion and first-use order must be confirmed by authors from the study context.

**Evidence references:**
- `docs/reviewer_closure/REVIEWER_48_STATUS.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Editorially recoverable if authors can define the term; do not guess the expansion.

**Experiment needed:** None.

**Proposed editorial action (not applied):** Confirm the intended meaning of SCP, define it and run a first-use audit.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Low, but an undefined technical acronym can obscure the method.

### R2-2f — Reviewer 2, Round 1, point 2, study placement and aim

**Specific request:** Move implementation details of the present study out of the Introduction and state the study aim clearly at the end of the section.

**Scope in manuscript:** Introduction Table 2 and related description; final Introduction paragraph.

**Evidence recorded:** Architecture and operational scope are documented elsewhere in the repository; no manuscript restructuring has been carried out.

**What the available evidence addresses:** The technical source material is identifiable, but section placement remains unchanged.

**What it does not establish / what remains:** The authors must decide whether the final study is retrospective audit/transfer or a broader architecture evaluation.

**Evidence references:**
- `docs/architecture.md`
- `docs/reviewer_closure/REVIEWER_48_STATUS.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Editorially recoverable after scope approval.

**Experiment needed:** None for moving text; a broader stated aim must be supported by data.

**Proposed editorial action (not applied):** Keep prior-art synthesis in Introduction, move this study's implementation to Methods and add a bounded aim.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Moderate if the aim overstates what the study actually demonstrates.

### R2-3a — Reviewer 2, Round 1, point 3, database and split description

**Specific request:** Describe each database, available and used classes, segment counts, and ECG/patient numbers by training, validation and test split; explain what happened to remaining classes.

**Scope in manuscript:** Materials and Methods dataset subsection and split tables.

**Evidence recorded:** Verified selected counts are P6 1,643 ECG, P8 2,193 ECG, and P4 962 panel rows over 733 ECG/676 patients. PTB-XL fold 10 has 2,198 ECG/1,904 patients; 733 P4 ECG map to 676 fold-10 patients with no overlap with official folds 1-9. SLURM records V3H jobs 16785/16786 and V3M jobs 16816/16819 as completed, but their exact historical work directories and full split files are absent at the checked paths.

**What the available evidence addresses:** Selected counts, official fold relation, completed-job accounting, checkpoint-declared manifest names and surviving calibration logs are documented with their different evidentiary strength.

**What it does not establish / what remains:** Historical train/validation/calibration manifests, patient mappings and full per-class source counts are not all linked to released checkpoints; official fold membership and a completed job do not certify historical patient isolation.

**Evidence references:**
- `docs/reviewer_closure/SPLIT_CALIBRATION_DISPOSITION.md`
- `docs/reviewer_closure/R1_2_EVIDENCE_CEILING.md`
- `outputs/results/revision_replay_diagnostics_20261107/p4_official_fold_coverage.json`
- `docs/reviewer_closure/HISTORICAL_EVIDENCE_HANDOFF.md`
- `docs/reviewer_closure/CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md`
- `docs/reviewer_closure/RECOVERED_VS_MISSING_HISTORICAL_EVIDENCE.md`
- `docs/reviewer_closure/CHECKPOINT_JOB_MANIFEST_VERIFICATION_FINAL.md`
- `docs/reviewer_closure/receipts/CEDIA_JOB_LOGS_2026-11-10.json`

**Traceability confidence:** The searched sources reached a documented evidence ceiling; absence is limited to those sources.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Reopen only with exact job/checkpoint-linked split manifests and exclusions. The supplied archives, exact work-directory checks and NOC-reviewed backup did not recover them; this is not a global-absence finding.

**Experiment needed:** A new split analysis is required for any new model; historical split claims cannot be recreated from selected results.

**Proposed editorial action (not applied):** Report known selected counts and explicitly mark unrecovered historical counts/isolation as unknown.

**Technical status:** `EVIDENCE_CEILING_REACHED`

**Reviewer satisfaction:** `PARTIALLY_ADDRESSED`

**Next action class:** `DECLARE_SOURCE_BOUNDED_CEILING_AND_PREPARE_SCOPE_DECISION`

**Owner boundary:** Codex stops unbounded searching and records the ceiling; authors decide claim scope; custodian acts only on a new archive lead.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** High if official folds or selected cohorts are presented as proof of historical train/test isolation.

### R2-3b — Reviewer 2, Round 1, point 3, design versus evaluation

**Specific request:** Clarify whether the study only evaluates specialist networks or also designs them.

**Scope in manuscript:** Materials and Methods opening statement and study aim.

**Evidence recorded:** Available evidence covers architecture contracts, selected historical predictions, reconstructed replay and later SPH transfer; it does not make these evidence types interchangeable. CEDIA job 17314 records a multi-epoch P6 gate sweep, and job 17315 reports epoch 8 against the named V3H manifest, so V3H must be treated as development/model-selection evidence.

**What the available evidence addresses:** The technical package distinguishes design from evaluation stages.

**What it does not establish / what remains:** The manuscript has not yet stated the exact retrospective scope and what was designed versus evaluated.

**Evidence references:**
- `docs/architecture.md`
- `docs/reviewer_closure/REVIEWER_48_STATUS.md`
- `docs/reviewer_closure/CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Editorially recoverable using existing evidence; no historical search required.

**Experiment needed:** None for wording; claims of a new design process require corresponding provenance.

**Proposed editorial action (not applied):** State exactly which architecture was developed, which checkpoints were evaluated and which replays are reconstructed.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Moderate if design and evaluation evidence are conflated.

### R2-3c — Reviewer 2, Round 1, point 3, cascade and auxiliary rhythm labels

**Specific request:** Explain how primary, cascade and auxiliary rhythm labels are used in training and evaluation, and do not describe NSR as a low-prevalence arrhythmia.

**Scope in manuscript:** Methods class-role description and training/evaluation flow.

**Evidence recorded:** The contract declares P8's eight outputs, including NSR, plus six additional global rhythm outputs. SPH P8 predicts NSR top-1 on 16,700 records; P8 fallback is separately recorded. The code and outputs do not prove run-specific training support for each auxiliary class.

**What the available evidence addresses:** Implemented output and fallback roles are described; NSR is a rhythm category, not an arrhythmia class by that fact alone.

**What it does not establish / what remains:** Checkpoint-linked positive/negative training supports and exact historical class selection remain unavailable for auxiliary outputs.

**Evidence references:**
- `docs/reviewer_closure/ROLE_SUPERVISION_AND_ROUTING.md`
- `outputs/models/heads/global_head_contracts.json`
- `docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`
- `docs/reviewer_closure/OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md`
- `docs/reviewer_closure/AUXILIARY_CLASS_TRAINING_EVIDENCE.md`
- `docs/reviewer_closure/OTHER_CLASS_COVERAGE_EXPERIMENT.md`

**Traceability confidence:** A bounded result is verified; residual limitations remain open.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Recoverable only with original training labels/masks, manifests, configuration, logs and checkpoint linkage.

**Experiment needed:** No new experiment needed to state current contract; new supervised class performance requires a valid training/evaluation design.

**Proposed editorial action (not applied):** Separate declared outputs, training supervision, scored predictions and role/routing; correct the NSR description.

**Technical status:** `VERIFIED_WITH_LIMITATIONS`

**Reviewer satisfaction:** `PARTIALLY_ADDRESSED`

**Next action class:** `DOCUMENT_LIMITS_AND_PREPARE_EDITORIAL_ACTION`

**Owner boundary:** Codex prepares precise wording; authors approve scope and interpretation.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** High if output presence is treated as evidence of training or validated cascade performance.

### R2-3d — Reviewer 2, Round 1, point 3, ALMI/ILMI/LAE

**Specific request:** Clarify whether ALMI, ILMI and LAE were trained and evaluated or merely logged as auxiliary pathology labels.

**Scope in manuscript:** Methods pathology head, training masks and results scope.

**Evidence recorded:** The global contract has seven pathology outputs, and reconstructed P4 inference emitted ALMI/ILMI/LAE scores on 733 selected ECG. A candidate manifest has positives, but it is not linked to the released checkpoint's training run.

**What the available evidence addresses:** It is verified that outputs are emitted in the reconstructed path, not that the historical checkpoint was trained on those labels.

**What it does not establish / what remains:** Historical supervision supports, loss masks, selection policy and evaluation metrics for these outputs are not certified.

**Evidence references:**
- `docs/reviewer_closure/ROLE_SUPERVISION_AND_ROUTING.md`
- `docs/revision-data-dispositions.md`
- `outputs/models/heads/global_head_contracts.json`
- `docs/reviewer_closure/OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md`
- `docs/reviewer_closure/AUXILIARY_CLASS_TRAINING_EVIDENCE.md`

**Traceability confidence:** The searched sources reached a documented evidence ceiling; absence is limited to those sources.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Requires exact training/validation manifests, labels/masks, run configuration and checkpoint-linked job receipt; no inference can reconstruct missing provenance.

**Experiment needed:** New training and evaluation are required if performance for these classes is claimed.

**Proposed editorial action (not applied):** Describe them as unvalidated auxiliary outputs or remove claims of trained/evaluated pathology classes.

**Technical status:** `EVIDENCE_CEILING_REACHED`

**Reviewer satisfaction:** `NOT_SATISFIED`

**Next action class:** `DECLARE_SOURCE_BOUNDED_CEILING_AND_PREPARE_SCOPE_DECISION`

**Owner boundary:** Codex stops unbounded searching and records the ceiling; authors decide claim scope; custodian acts only on a new archive lead.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** High if auxiliary scores are reported as established diagnostic performance.

### R2-3e — Reviewer 2, Round 1, point 3, Table 5 Role

**Specific request:** Define what Role means in Table 5 and how role assignments are determined.

**Scope in manuscript:** Table 5 and Methods role/route definitions.

**Evidence recorded:** The code declares primary, auxiliary and cascade roles; the selected replay measures only implemented decision behavior. The historic per-record role/transition ledger is unavailable; SPH fallback counts are not quarantine transitions.

**What the available evidence addresses:** Code roles, predicted outputs and observed transitions are explicitly distinguished.

**What it does not establish / what remains:** Historical assignment and role-transition counts for the original all-input pathway are not recoverable from the selected panels.

**Evidence references:**
- `docs/reviewer_closure/ROLE_SUPERVISION_AND_ROUTING.md`
- `src/titan_v45/cascade/policy.py`
- `docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`
- `docs/reviewer_closure/OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md`
- `docs/reviewer_closure/SELECTIVE_PREDICTION_EXPERIMENT.md`

**Traceability confidence:** A bounded result is verified; residual limitations remain open.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Reopen only with the authentic role/transition ledger, policy version and linked predictions.

**Experiment needed:** A new measured operational workflow is required if human review or route effectiveness is retained as a claim.

**Proposed editorial action (not applied):** Define Role as a declared data/model contract and avoid interpreting it as actual human review.

**Technical status:** `VERIFIED_WITH_LIMITATIONS`

**Reviewer satisfaction:** `PARTIALLY_ADDRESSED`

**Next action class:** `DOCUMENT_LIMITS_AND_PREPARE_EDITORIAL_ACTION`

**Owner boundary:** Codex prepares precise wording; authors approve scope and interpretation.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** High if a declared role is mistaken for measured routing or clinician action.

### R2-3f — Reviewer 2, Round 1, point 3, Figures 5 and 6

**Specific request:** Name and define the ten morphology features, explain asymmetric arrows and every block-diagram connection, and correct or remove unsupported flow arrows.

**Scope in manuscript:** Methods architecture and Figures 5-6 plus captions.

**Evidence recorded:** Ten-feature candidate code and several historical event sources were recovered; 10 of 11 inventoried files match known hashes. The exact original loader is absent. P4 replay matched 962/962 decisions but maximum probability residual 0.0006194115 exceeds historical tolerance 1e-5.

**What the available evidence addresses:** The candidate feature contract and its provenance boundary are documented, and strict score equivalence is explicitly recorded as failed.

**What it does not establish / what remains:** Exact historical feature implementation, loader identity and the figure-to-runtime arrow semantics are not fully verified.

**Evidence references:**
- `docs/recovered-feature-contract.md`
- `docs/reviewer_closure/REPLAY_EQUIVALENCE_DISPOSITION.md`
- `docs/figure-evidence.md`
- `docs/reviewer_closure/HISTORICAL_LOADER_IDENTITY_AND_REPLAY.md`
- `docs/reviewer_closure/HISTORICAL_RECOVERY_FINAL_EXECUTION.md`
- `docs/reviewer_closure/SPECIALIST_192_512_ARCHITECTURE_RESOLUTION.md`

**Traceability confidence:** The searched sources reached a documented evidence ceiling; absence is limited to those sources.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** The exact loader may reopen this only if supplied with its expected hash fc8d7367f9f2c108376839435021ec3172fe2757faa4a615f0ef5d39cbf1e855 or an independently linked source snapshot.

**Experiment needed:** No threshold retuning; a future replay may test equivalence only if the exact loader and inputs are recovered.

**Proposed editorial action (not applied):** List each feature and unit, redraw arrows to match verified dataflow, and identify reconstructed code as such.

**Technical status:** `EVIDENCE_CEILING_REACHED`

**Reviewer satisfaction:** `PARTIALLY_ADDRESSED`

**Next action class:** `DECLARE_SOURCE_BOUNDED_CEILING_AND_PREPARE_SCOPE_DECISION`

**Owner boundary:** Codex stops unbounded searching and records the ceiling; authors decide claim scope; custodian acts only on a new archive lead.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** High if a candidate implementation is represented as the exact historical architecture.

### R2-3g — Reviewer 2, Round 1, point 3, Brier score statements

**Specific request:** Move numerical Brier scores from Methods to Results if they are observed results, and distinguish the metric definition from the measured values.

**Scope in manuscript:** Evaluation Metrics and Confidence Intervals subsection and Results.

**Evidence recorded:** The metric definitions and later SPH Brier scores are available in separate documents; this reviewer comment concerns location and attribution of method versus results.

**What the available evidence addresses:** The evidence distinguishes definitions from observed results; the submitted manuscript has not been edited.

**What it does not establish / what remains:** All original numerical claims in Methods must be traced to their exact cohort and moved or removed.

**Evidence references:**
- `docs/reviewer_closure/METRIC_DEFINITIONS.md`
- `docs/external_validation/sph_results.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Editorially recoverable from the audited metric outputs.

**Experiment needed:** None if the original results are accurately sourced; no unsupported value should be retained.

**Proposed editorial action (not applied):** Keep the Brier definition in Methods and report cohort-specific values only in Results.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Moderate if numbers are presented as prespecified method constants rather than measured outcomes.

### R2-3h — Reviewer 2, Round 1, point 3, accuracy metrics

**Specific request:** Provide equations and explanations for all accuracy metrics and clarify whether rhythm and pathology metrics differ and why.

**Scope in manuscript:** Evaluation Metrics and Confidence Intervals subsection.

**Evidence recorded:** The repository defines panel-level binary P4 metrics separately from multiclass/top-1 rhythm metrics; the SPH endpoints are per-class statement-level binary comparisons.

**What the available evidence addresses:** The distinctions are documented and testable, but equations have not been inserted into the manuscript.

**What it does not establish / what remains:** The final manuscript still needs equations matched to each reported unit, averaging scheme, denominator and missing-label rule.

**Evidence references:**
- `docs/reviewer_closure/METRIC_DEFINITIONS.md`
- `docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Editorially recoverable from documented formulas and outputs.

**Experiment needed:** None for equations; any value must be recomputed if its denominator or metric definition changes.

**Proposed editorial action (not applied):** Define accuracy, macro-F1, top-1, AUROC, AP and calibration with their exact units and averaging rules.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** High if panel rows, ECG counts and class-wise binary endpoints are conflated.

### R2-4a — Reviewer 2, Round 1, point 4, Table 8 terminology

**Specific request:** Define the external-development evidence package, say whether it is the test dataset, use consistent terminology and describe it in the database or Methods section.

**Scope in manuscript:** Results Table 8 and cohort/methods description.

**Evidence recorded:** The release separates selected development predictions from the later frozen SPH transfer. Primary6 contains 1,643 ECG; P8 contains 2,193 with P6 nested; P4 uses 962 panel rows/733 ECG. SPH is 25,770 ECG from another source. CEDIA jobs 17314/17315 show that the V3H P6 gate informed epoch selection and is not an untouched test.

**What the available evidence addresses:** The evidence packages and populations are now named and numerically distinguished in technical documentation.

**What it does not establish / what remains:** Complete historical usage and selection lineage of every development package remain unknown; V3H selection exposure is now documented, but the exact 17314 manifest and complete backbone lineage remain unavailable. The manuscript terminology has not been harmonized.

**Evidence references:**
- `docs/evidence-status.md`
- `docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`
- `docs/external_validation/sph_results.md`
- `docs/reviewer_closure/CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md`
- `docs/reviewer_closure/GENERALIZATION_DATASET_ELIGIBILITY.md`
- `docs/reviewer_closure/GENERALIZATION_EXPERIMENT_RESULTS.md`

**Traceability confidence:** A bounded result is verified; residual limitations remain open.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Historical usage is bounded by the recovery ceiling; terminology is editorially recoverable.

**Experiment needed:** None for definition; new evidence is needed for any independent-test interpretation.

**Proposed editorial action (not applied):** Define each package as a concrete artifact/population and use one term consistently.

**Technical status:** `VERIFIED_WITH_LIMITATIONS`

**Reviewer satisfaction:** `PARTIALLY_ADDRESSED`

**Next action class:** `DOCUMENT_LIMITS_AND_PREPARE_EDITORIAL_ACTION`

**Owner boundary:** Codex prepares precise wording; authors approve scope and interpretation.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** High if selected development cohorts are described as independent tests.

### R2-4b — Reviewer 2, Round 1, point 4, figure cross-reference

**Specific request:** Correct the paragraph after Table 8 to refer to Figure 8 rather than Figure 10.

**Scope in manuscript:** Results paragraph immediately following Table 8.

**Evidence recorded:** A cross-reference correction is requested; no new data or model execution is needed.

**What the available evidence addresses:** The defect is identified, but the submitted manuscript remains unchanged.

**What it does not establish / what remains:** Final figure numbering may change during layout and must be checked after the final figure assembly.

**Evidence references:**
- `docs/reviewer_closure/REVIEWER_48_STATUS.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Fully editorially recoverable.

**Experiment needed:** None.

**Proposed editorial action (not applied):** Correct the reference and recheck all figure/table references after composition.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Low scientific risk; incorrect references impair verification.

### R2-4c — Reviewer 2, Round 1, point 4, F1 interpretation

**Specific request:** Do not call F1 values around 62.58% and 65.64% reliable performance; revise the strength of the interpretation.

**Scope in manuscript:** Results paragraph on 1AVB and PVC and corresponding Discussion claims.

**Evidence recorded:** Historical selected-panel P6 F1 is 62.58% for 1AVB and 65.64% for PVC. Later SPH statement-level results are lower for P6 PVC (54.08%) and differ in population/reference; they must not be conflated.

**What the available evidence addresses:** Canonical values and the unfavorable transfer result are available for a bounded interpretation.

**What it does not establish / what remains:** The original adjective remains in the submitted manuscript and requires author-approved replacement.

**Evidence references:**
- `outputs/results/primary/canonical_profiles.json`
- `docs/external_validation/sph_results.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Editorially recoverable from verified metrics; no further data recovery needed to remove the adjective.

**Experiment needed:** None to moderate the wording; any claim of reliability requires a defined operational criterion and validation.

**Proposed editorial action (not applied):** Describe exact F1 values and cohort; avoid 'reliable' without a prespecified threshold.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** High if a moderate F1 is framed as reliable diagnostic performance.

### R2-4d — Reviewer 2, Round 1, point 4, Figure 8 caption and uncertainty

**Specific request:** Correct Figure 8's caption to acknowledge precision, recall and F1, and show or accurately describe the absence of 95% confidence bounds.

**Scope in manuscript:** Results Figure 8 graphic and caption.

**Evidence recorded:** The plotted metrics and the available patient-component intervals are distinct artifacts; the original figure/caption must be reconciled with the final values and intervals.

**What the available evidence addresses:** The evidence package defines available uncertainty intervals; the submitted figure has not been replaced or recaptioned.

**What it does not establish / what remains:** It is not established that every plotted bar has a matching interval in the current submitted figure.

**Evidence references:**
- `docs/external_validation/sph_results.md`
- `docs/reviewer_closure/REVIEWER_48_STATUS.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Editorially recoverable by regenerating the figure from the selected aggregate and explicitly displaying uncertainty where computed.

**Experiment needed:** No new ECG experiment; interval calculation is needed only if the final figure reports confidence intervals not already available.

**Proposed editorial action (not applied):** Rebuild from the exact source table, label all three measures and either show valid bounds or state they are not shown.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Moderate if a point estimate is visually implied to carry confidence bounds it does not show.

### R2-4e — Reviewer 2, Round 1, point 4, threshold non-crossing

**Specific request:** Explain what happens when no class score crosses its threshold and how such cases are counted.

**Scope in manuscript:** Decision policy in Methods and all-input Results.

**Evidence recorded:** On all 25,770 SPH ECG, P6 had 16,785 empty threshold sets; P4 had 8,343; P8 applied top-1 fallback on 801. In the selected replay P8 fallback was 58/2,193. No reference labels were used to route.

**What the available evidence addresses:** No-crossing behavior and complete-source counts are now measured for the frozen profiles.

**What it does not establish / what remains:** P6/P4 empty sets and P8 fallback do not establish a quarantine rate, an Other class, or human review; historical all-input June routes remain unknown.

**Evidence references:**
- `docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`
- `docs/reviewer_closure/ROLE_SUPERVISION_AND_ROUTING.md`
- `outputs/results/revision_20261107/rhythm_waveform.json`
- `outputs/results/revision_20261107/pathology_waveform.json`
- `docs/reviewer_closure/OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md`
- `docs/reviewer_closure/SELECTIVE_PREDICTION_EXPERIMENT.md`

**Traceability confidence:** An experiment was executed; this does not imply that the original request is fully satisfied.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Measured profile behavior is complete for the frozen SPH run; historical route history needs its original policy and ledger.

**Experiment needed:** No new experiment to state these frozen rules; a quarantine effectiveness claim requires a separate defined evaluation.

**Proposed editorial action (not applied):** Define thresholding and fallback separately, report denominators and do not relabel fallback as quarantine.

**Technical status:** `EXPERIMENT_COMPLETED_WITH_LIMITATIONS`

**Reviewer satisfaction:** `PARTIALLY_ADDRESSED`

**Next action class:** `REPORT_EXPERIMENT_WITH_LIMITS_AND_DECIDE_IF_NEW_STUDY_IS_NEEDED`

**Owner boundary:** Codex reports measured results and limits; authors approve claims; a new study is needed if the broader claim is retained.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** High if empty sets/fallback are hidden or represented as clinical review.

### R2-4f — Reviewer 2, Round 1, point 4, Figure 9 units

**Specific request:** Use a consistent numeric or percentage presentation across Figures 7 and 9.

**Scope in manuscript:** Results Figures 7 and 9 and captions.

**Evidence recorded:** This is a visual consistency issue; no model or cohort calculation is requested.

**What the available evidence addresses:** The required edit is identified, but the submitted figures remain unchanged.

**What it does not establish / what remains:** The final unit convention must be applied after the final figure selection.

**Evidence references:**
- `docs/reviewer_closure/REVIEWER_48_STATUS.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Fully editorially recoverable.

**Experiment needed:** None.

**Proposed editorial action (not applied):** Choose counts or percentages consistently and verify axis labels, color scales and captions.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Low scientific risk; mixed units can confuse comparative reading.

### R2-4g — Reviewer 2, Round 1, point 4, duplicate figures

**Specific request:** Resolve the reported duplication between Figures 8 and 10.

**Scope in manuscript:** Results figures and final figure inventory.

**Evidence recorded:** The comment identifies duplicate content in the submitted layout; no new empirical result is required to remove a duplicate.

**What the available evidence addresses:** The figure-level issue is recorded; a final accepted figure set has not been assembled.

**What it does not establish / what remains:** Figure identity, captions and cross-references must be checked together after editorial revisions.

**Evidence references:**
- `docs/reviewer_closure/REVIEWER_48_STATUS.md`
- `docs/figure-evidence.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Fully editorially recoverable from original figure sources.

**Experiment needed:** None unless the duplicate figure contains unique, unverified data.

**Proposed editorial action (not applied):** Retain one authoritative figure or document the distinct information each figure conveys.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Low scientifically, but duplication undermines presentation quality and traceability.

### R2-4h — Reviewer 2, Round 1, point 4, ROC/PR evaluation unit

**Specific request:** Define what 'evaluation tracings' means in the ROC and precision-recall description and use the correct ECG-level unit.

**Scope in manuscript:** Results text for Figures 11 and 12 and metric methods.

**Evidence recorded:** The frozen SPH score curves use ECG-record statements; historical development metrics use their own selected record/panel units.

**What the available evidence addresses:** The technical evidence identifies the relevant record-level units; the manuscript's ambiguous phrase remains unchanged.

**What it does not establish / what remains:** The text must identify the exact cohort, endpoint and unit for each plotted curve.

**Evidence references:**
- `docs/reviewer_closure/METRIC_DEFINITIONS.md`
- `docs/external_validation/sph_results.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Editorially recoverable from the plot source and protocol.

**Experiment needed:** None if the source arrays and endpoint remain unchanged.

**Proposed editorial action (not applied):** Replace 'evaluation tracings' with the precise ECG-record denominator and name each target.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Moderate if rhythm classes, ECGs and panel rows are treated as the same unit.

### R2-4i — Reviewer 2, Round 1, point 4, AUROC interpretation

**Specific request:** Revise the characterization of 87.46% pathology macro-AUROC as high.

**Scope in manuscript:** Results interpretation of rhythm and pathology macro-AUROC.

**Evidence recorded:** The selected P4 macro-AUROC is 87.46%; its unit and population differ from later endpoint-specific SPH AUROCs, including low PPV/F1 despite some high AUROC values.

**What the available evidence addresses:** Canonical and transfer values are available for a qualified description.

**What it does not establish / what remains:** The adjective and interpretation in the submitted manuscript have not been revised.

**Evidence references:**
- `outputs/results/primary/canonical_profiles.json`
- `docs/external_validation/sph_results.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Editorially recoverable from verified metrics.

**Experiment needed:** None to revise the adjective; broader clinical meaning requires a prespecified benchmark.

**Proposed editorial action (not applied):** Report the value without 'high' or explain its context, metric uncertainty and class-specific limitations.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Moderate to high if discrimination is used to imply good operating performance.

### R2-4j — Reviewer 2, Round 1, point 4, Figure 13 calibration

**Specific request:** Use consistent observed-frequency/empirical-accuracy terminology, define how it is estimated and make the ten confidence-bin axes match their stated range.

**Scope in manuscript:** Figure 13 axes, caption and calibration-method description.

**Evidence recorded:** The frozen SPH aggregate reports ECE with ten bins; calibration curves and metrics are defined for the actual scored endpoints. This does not certify the original Figure 13's plotted source or axis ticks.

**What the available evidence addresses:** A reproducible calibration definition and later source-specific ECE evidence exist.

**What it does not establish / what remains:** The submitted calibration plot and its data source must be matched to the final binning implementation and labels.

**Evidence references:**
- `docs/reviewer_closure/METRIC_DEFINITIONS.md`
- `outputs/results/external_sph/sph_aggregate_32669.json`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Recoverable from the figure source data and plotting script; do not infer from the image alone.

**Experiment needed:** No new inference if the same saved probabilities and fixed bins are used; otherwise recompute from the correct source.

**Proposed editorial action (not applied):** Define bin occupancy and mean confidence versus observed statement frequency; standardize labels/ticks and document empty bins.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Moderate if a calibration curve is mislabeled or its estimate cannot be reproduced.

### R2-4k — Reviewer 2, Round 1, point 4, quarantine rates

**Specific request:** Define the quarantine rate and pre/post-quarantine accuracy and explain how these values are estimated.

**Scope in manuscript:** Methods quarantine policy and Results figures/tables reporting rates or accuracy.

**Evidence recorded:** The selected reconstruction and all-input SPH flow contain no checkpoint-linked uncertainty score plus verified quarantine policy; quarantine is not assessed, not 0%. P8 fallback and empty sets are not quarantine.

**What the available evidence addresses:** The invalid inference from fallback to quarantine is explicitly rejected; routing counts are documented with their actual semantics.

**What it does not establish / what remains:** No historic pre/post ledger, quarantine denominator, policy version or uncertainty inputs are available; rates and pre/post accuracy cannot be reconstructed.

**Evidence references:**
- `docs/reviewer_closure/ROLE_SUPERVISION_AND_ROUTING.md`
- `docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`
- `outputs/results/revision_20261107/rhythm_waveform.json`
- `outputs/results/revision_20261107/pathology_waveform.json`
- `docs/reviewer_closure/OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md`
- `docs/reviewer_closure/SELECTIVE_PREDICTION_EXPERIMENT.md`

**Traceability confidence:** The searched sources reached a documented evidence ceiling; absence is limited to those sources.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Reopen only if an authentic policy, ledger, score inputs and checkpoint/job linkage are recovered.

**Experiment needed:** Required to support any quarantine effectiveness claim; otherwise the claim and rate must be removed.

**Proposed editorial action (not applied):** Do not report an assumed quarantine percentage; mark historical rate unavailable or remove the claim.

**Technical status:** `EVIDENCE_CEILING_REACHED`

**Reviewer satisfaction:** `NOT_SATISFIED`

**Next action class:** `DECLARE_SOURCE_BOUNDED_CEILING_AND_PREPARE_SCOPE_DECISION`

**Owner boundary:** Codex stops unbounded searching and records the ceiling; authors decide claim scope; custodian acts only on a new archive lead.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Very high if invented or unmeasured quarantine benefit/rates remain.

### R2-4l — Reviewer 2, Round 1, point 4, rhythm top-1

**Specific request:** Define rhythm top-1 accuracy and explain exactly how it is calculated.

**Scope in manuscript:** Metrics Methods and Results table/figure captions.

**Evidence recorded:** The selected P6 top-1 accuracy is 1,564/1,643 = 95.19%; P8 has its own accepted top-1 denominator and fallback semantics. Neither is pooled P4 panel accuracy.

**What the available evidence addresses:** The calculation and selected denominators can be traced in code and canonical results.

**What it does not establish / what remains:** The submitted manuscript must define argmax, denominator, treatment of fallback and selected-cohort scope.

**Evidence references:**
- `docs/reviewer_closure/METRIC_DEFINITIONS.md`
- `docs/reviewer_closure/ROLE_SUPERVISION_AND_ROUTING.md`
- `outputs/results/primary/canonical_profiles.json`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Editorially recoverable from canonical metrics and decision policy.

**Experiment needed:** None if definitions and data remain unchanged.

**Proposed editorial action (not applied):** State the per-record argmax rule and report P6/P8 separately, including fallback treatment.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** High if top-1 is interpreted as all-class or end-to-end accuracy.

### R2-4m — Reviewer 2, Round 1, point 4, Figures 14 and 15 readability

**Specific request:** Improve unreadable axes and values in Figures 14 and 15 and check all figures.

**Scope in manuscript:** Final manuscript figure source, captions and rendered PDF.

**Evidence recorded:** The submitted figure quality concern is known; this technical phase intentionally does not regenerate the manuscript or its final figures.

**What the available evidence addresses:** A later layout/render check is explicitly reserved; no claim is made that the figures are currently fixed.

**What it does not establish / what remains:** Font sizes, axis labels, line weights, contrast and page-scale legibility remain unverified in the final layout.

**Evidence references:**
- `docs/figure-evidence.md`
- `docs/reviewer_closure/REVIEWER_48_STATUS.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Editorially recoverable from vector/source figures after content and scope are frozen.

**Experiment needed:** None if plots use verified aggregates; new evidence is needed only if the plot content changes empirically.

**Proposed editorial action (not applied):** Regenerate, render the final PDF and inspect every page at realistic size; verify captions and all figure callouts.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** Moderate if key values cannot be read or visual framing overstates results.

### R2-5 — Reviewer 2, Round 1, point 5, PVC unit of analysis

**Specific request:** Acknowledge that PVC is often analyzed at heartbeat level and avoid treating 10-second ECG-level classification as beat-level detection.

**Scope in manuscript:** Discussion of PVC performance and any heartbeat-level interpretation.

**Evidence recorded:** SPH PVC uses ECG statement code 60: 1,067 positive and 24,703 negative recorded-statement comparisons per P6/P8; F1 is 54.08% for P6 and 66.16% for P8. No beat annotations or localization metric are present.

**What the available evidence addresses:** The available result is correctly bounded to record-level ECG statement agreement.

**What it does not establish / what remains:** Beat-level detection, temporal matching, episode counts and clinical adjudication are not measured.

**Evidence references:**
- `docs/reviewer_closure/AF_PVC_REFERENCE_DISPOSITION.md`
- `docs/external_validation/sph_results.md`
- configs/external_validation/sph_frozen.json
- `docs/reviewer_closure/GENERALIZATION_PER_CLASS_METRICS.json`
- `docs/reviewer_closure/GENERALIZATION_ERROR_ANALYSIS.md`

**Traceability confidence:** A bounded result is verified; residual limitations remain open.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Cannot be recovered from record-level codes; needs beat-labeled ECGs and matching protocol.

**Experiment needed:** Required if beat detection or localization is claimed; not required for a strictly record-level statement study.

**Proposed editorial action (not applied):** Explicitly state the ECG-level unit and remove any beat-level performance implication.

**Technical status:** `VERIFIED_WITH_LIMITATIONS`

**Reviewer satisfaction:** `PARTIALLY_ADDRESSED`

**Next action class:** `DOCUMENT_LIMITS_AND_PREPARE_EDITORIAL_ACTION`

**Owner boundary:** Codex prepares precise wording; authors approve scope and interpretation.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** High if record-level F1 is interpreted as heartbeat detector accuracy.

### R2-6 — Reviewer 2, Round 1, point 6, distortion and citation

**Specific request:** Clarify whether the claim that the framework eliminates diagnostic distortion refers to this study and justify or correct citation [4].

**Scope in manuscript:** Discussion claim and its cited reference.

**Evidence recorded:** Observed external transfer includes very low PPV/F1 for P4 and P8 PAC; the data do not establish that the framework eliminates diagnostic distortion or provides an uncompromised benchmark.

**What the available evidence addresses:** The measured evidence constrains the claim and identifies the need to verify the reference.

**What it does not establish / what remains:** The submitted sentence and citation have not been corrected; citation [4] must be checked against the final claim.

**Evidence references:**
- `docs/reviewer_closure/REVIEWER_48_STATUS.md`
- `docs/external_validation/sph_results.md`

**Traceability confidence:** Technical evidence is available for the bounded claim, but the manuscript remains unedited.

**Code change indicated:** No new code change is identified by the current source record. Implement one only if a specific reproducible defect is found.

**Repeat verification:** Repeat only if new source bytes, code, data or a protocol change affects this item; use the existing linked receipt as the current evidence.

**Recoverability assessment:** Editorially recoverable, but a stronger causal claim would require new comparative evidence.

**Experiment needed:** None if the absolute claim is removed; required for any retained claim that the architecture eliminates distortion.

**Proposed editorial action (not applied):** Replace the absolute claim with a bounded observation or remove it, and verify the cited source.

**Technical status:** `MANUSCRIPT_ONLY_PENDING`

**Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`

**Next action class:** `PREPARE_EDITORIAL_CHANGE_WITHOUT_EDITING_SUBMITTED_MANUSCRIPT`

**Owner boundary:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

**Manuscript:** `SIN_EDITAR`

**Scientific risk:** High if the manuscript asserts elimination of bias or distortion without an appropriate comparison.

## Internal audits

The following 12 IDs remain in [`REVIEWER_48_DETAILED.json`](REVIEWER_48_DETAILED.json) and [`REVIEWER_48_DETAILED.md`](REVIEWER_48_DETAILED.md):

`A-01`, `A-02`, `A-03`, `A-04`, `A-05`, `A-06`, `A-07`, `A-08`, `A-09`, `A-10`, `A-11`, `A-12`

## Reopening criteria

Reopen a row only on new source artifacts with verifiable hashes and authorized provenance, a new approved experiment, or an explicit author decision about claim scope. Do not convert missing evidence to a negative finding, infer acceptance from silence, or change the historical metrics to force closure.
