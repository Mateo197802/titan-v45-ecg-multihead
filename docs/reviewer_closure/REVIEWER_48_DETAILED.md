# Detailed disposition of the 48 review and audit observations

**As of:** 2026-11-10
**Counts:** 36 peer-review observations; 12 project-audit observations; 48 total.

The 36 reviewer observations are paraphrased from the author-supplied Round 1 comment transcript in the platform attachment. The attached PDF is the manuscript draft, not the review report. A-01 through A-12 are project audit observations, not reviewer comments. No private correspondence or manuscript text is reproduced here.

This is a technical evidence matrix, not a response letter, an editorial decision or a claim that the submitted manuscript has been revised. The manuscript and editor response remain unchanged.

## Status counts

### Technical status

| Status | Count |
| --- | ---: |
| `ACTIVE_RECOVERY_REQUIRED` | 2 |
| `EVIDENCE_CEILING_REACHED` | 6 |
| `EXPERIMENT_COMPLETED_WITH_LIMITATIONS` | 3 |
| `MANUSCRIPT_ONLY_PENDING` | 23 |
| `NEW_EXPERIMENT_REQUIRED` | 3 |
| `VERIFIED_COMPLETE` | 2 |
| `VERIFIED_WITH_LIMITATIONS` | 9 |

### Reviewer satisfaction

| Status | Count |
| --- | ---: |
| `EDITORIAL_ACTION_ONLY` | 21 |
| `NOT_APPLICABLE_AUDIT` | 12 |
| `NOT_SATISFIED` | 3 |
| `PARTIALLY_ADDRESSED` | 12 |

The 12 `A-*` entries are internal audit observations and therefore use `NOT_APPLICABLE_AUDIT` in the reviewer-satisfaction dimension. A recovery ceiling is not a completed experiment, and a planned manuscript edit is not an implemented correction.

## Item-by-item disposition

### R1-1 - Reviewer 1, Round 1, first methodological comment

- **Request:** Clarify that an external-development holdout from public sources used during development is not equivalent to independent external validation; provide source-level training, validation and holdout counts or evaluate a truly independent cohort, and moderate generalizability and deployment claims.
- **Affected manuscript scope:** Abstract, cohort description, Results, Discussion and deployment/generalizability claims.
- **Technical status:** `EXPERIMENT_COMPLETED_WITH_LIMITATIONS`
- **Reviewer satisfaction:** `PARTIALLY_ADDRESSED`
- **Evidence:** [`docs/reviewer_closure/SPH_DELIVERY_AUDIT.md`](SPH_DELIVERY_AUDIT.md); [`docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`](ALL_INPUT_FLOW_COVERAGE.md); [`docs/external_validation/sph_results.md`](../external_validation/sph_results.md); [`docs/external_validation/sph_independence_assessment.md`](../external_validation/sph_independence_assessment.md); [`docs/external_validation/sph_pac_probe_results.md`](../external_validation/sph_pac_probe_results.md); [`docs/reviewer_closure/EVIDENCE_SOURCE_TRIAGE.md`](EVIDENCE_SOURCE_TRIAGE.md); [`docs/reviewer_closure/CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md`](CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md)
- **Protocol, population and observed result:** Frozen transfer evaluated 25,770 SPH ECG from 24,666 source patients across P6, P8 and P4; all 14 compatible ECG-statement endpoints were scored with patient-component intervals. Newly recovered job 17314 records a P6 epoch sweep; job 17315 explicitly evaluates epoch 8 on the V3H accepted/balanced manifest at 1,564/1,643, accuracy 0.951917 and macro-F1 0.800938. This makes V3H model-selection/development evidence, not an untouched test. A separate fixed V3F-embedding PAC probe used the same SPH source and a 5,143-record exploratory patient holdout; its AUROCs were 0.910 (logistic) and 0.910 (MLP sensitivity), with no holdout tuning. The CEDIA audit found 539 code-30 records and 4 code-31 records (1 both, 3 code-31-only); all eligible rows remain in the code-30 statement endpoint, and absence is not a clinical negative. Commit 99b1065 publishes a scoped receipt binding the unchanged CEDIA aggregate and execution receipt. Confusion-derived metrics are recomputed publicly, while score metrics and intervals are digest-bound but not recalculated from restricted row scores. Prior Primary8 PAC target exposure and incomplete V3F source lineage keep this result nonconfirmatory. The exact 17314 manifest is not recorded. Complete V3F/V3AG pretraining and fine-tuning lineage remains unavailable.
- **What the evidence addresses:** A real full-source SPH transfer analysis and endpoint-specific results exist. New CEDIA accounting/logs also narrow the P6 validation claim by documenting V3H gate use and likely epoch-selection exposure. The PAC probe has a reproducible, hash-pinned aggregate publication and explicit code-30/31 target semantics, but does not establish an independent cohort, clinical adjudication or clinical validity.
- **What remains unresolved:** The 17314 sweep log and submitted script do not preserve the exact manifest binding; the same epoch-8 metrics and threshold vector appear in the immediately subsequent 17315 V3H gate report, strongly supporting use of that development holdout for selection but not providing a cryptographic same-file proof. Historical backbone/source overlap is not certified, labels are not clinical adjudication, and no truly untouched cohort has been selected.
- **Recoverability:** The current packages and NOC-reviewed backup do not recover the sweep script or full training manifests. Reopen only if exact job-linked scripts, manifests, checkpoint hashes and patient mappings are supplied. A new independent cohort is not recoverable from the current SPH evaluation.
- **Experiment requirement:** A new, admissible, patient- and signal-disjoint cohort is required if independent generalization is claimed.
- **Future editorial action:** Describe V3H P6 as selected development/model-selection evidence, distinguish it from the later SPH transfer, and do not call either clinical validation or assert complete independence without the missing lineage. Remove untested deployment claims.
- **Scientific risk:** High if SPH transfer is described as independent validation or clinical effectiveness.

### R1-2 - Reviewer 1, Round 1, second methodological comment

- **Request:** Report the complete clinical workflow, including primary and cascade classes, complete denominators, quarantine proportions, errors inside and outside quarantine, and predictive values under original prevalence; do not present a restricted denominator as end-to-end performance.
- **Affected manuscript scope:** Primary denominator, Results tables, cascade and quarantine claims.
- **Technical status:** `EXPERIMENT_COMPLETED_WITH_LIMITATIONS`
- **Reviewer satisfaction:** `PARTIALLY_ADDRESSED`
- **Evidence:** [`docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`](ALL_INPUT_FLOW_COVERAGE.md); [`docs/reviewer_closure/R1_2_EVIDENCE_CEILING.md`](R1_2_EVIDENCE_CEILING.md); [`docs/reviewer_closure/ROLE_SUPERVISION_AND_ROUTING.md`](ROLE_SUPERVISION_AND_ROUTING.md); [`outputs/results/external_sph/sph_aggregate_32669.json`](../../outputs/results/external_sph/sph_aggregate_32669.json); [`docs/reviewer_closure/RECOVERED_VS_MISSING_HISTORICAL_EVIDENCE.md`](RECOVERED_VS_MISSING_HISTORICAL_EVIDENCE.md)
- **Protocol, population and observed result:** The later SPH source has 25,770/25,770 scores per profile and all 14 compatible endpoint comparisons. The retained selected development replay has 2,193 P8 keys, including 1,643 P6 keys, plus 733 P4 keys: a verified 2,926-key P8/P4 union, not a patient count. Routing was computed without reference labels.
- **What the evidence addresses:** The measured all-source SPH profile coverage, empty-set/fallback counts and compatible predictive results are documented separately from selected-cohort replays.
- **What remains unresolved:** The June preselection population, exclusion reasons, complete all-class reference ontology and authentic historical quarantine policy/ledger remain unavailable. The recovered V3H accepted/balanced manifest is selected data, not the parent population. No pre/post quarantine rate can be calculated.
- **Recoverability:** The supplied archives, exact historical paths and NOC-reviewed backup do not recover the historical parent population. Reopen only on receipt of parent manifests, exclusion reasons and checkpoint/job-linked routing ledger; this is not a global-absence finding.
- **Experiment requirement:** A complete all-class workflow with compatible reference labels and an explicit quarantine policy is required to satisfy the original request; SPH cannot retroactively supply the missing historical flow.
- **Future editorial action:** Report selected denominators and measured SPH coverage; do not call either a reconstructed historical all-input workflow.
- **Scientific risk:** High if restricted Primary results are described as full clinical workflow accuracy or unmeasured quarantine benefit.

### R1-3 - Reviewer 1, Round 1, AF-label comment

- **Request:** Describe how AF reference labels were created and harmonized by source, how multiple or conflicting labels were handled, and restrict language to ECG-level AF rather than incident or first-diagnosed AF without longitudinal evidence.
- **Affected manuscript scope:** AF endpoint definition, label harmonization and Discussion terminology.
- **Technical status:** `VERIFIED_WITH_LIMITATIONS`
- **Reviewer satisfaction:** `PARTIALLY_ADDRESSED`
- **Evidence:** [`docs/reviewer_closure/AF_PVC_REFERENCE_DISPOSITION.md`](AF_PVC_REFERENCE_DISPOSITION.md); [`docs/af-reference-contract.md`](../af-reference-contract.md); [`outputs/results/revision_20261029/af_reference_consistency.json`](../../outputs/results/revision_20261029/af_reference_consistency.json)
- **Protocol, population and observed result:** Stored AF flags agree with retained code 164889003 for 1,643 P6 rows and 2,193 P8 rows; each overlapping profile has 390 positive rows and zero flag mismatches or unresolved code rows. P6 is nested within P8, so counts must not be added. A co-occurring normal-rhythm code was retained, not adjudicated.
- **What the evidence addresses:** The archived fields are internally consistent for the selected rows and the available contract supports ECG-record wording.
- **What remains unresolved:** The audit does not establish independent clinical adjudication for every source, onset, first diagnosis, incidence or patient-level longitudinal truth.
- **Recoverability:** The current row-level code check is complete within its scope; incident AF cannot be recovered without longitudinal patient data and an appropriate reference.
- **Experiment requirement:** Longitudinal AF claims require a new study; no such study is needed if the claim is confined to ECG-level statements.
- **Future editorial action:** State AF on the ECG, describe source-specific reference limitations and remove incident/first-diagnosed terminology unless authors supply longitudinal evidence.
- **Scientific risk:** High for incidence or prognosis claims; moderate for pooled ECG statement classification because annotation policies differ.

### R1-4 - Reviewer 1, Round 1, cryptographic hashes comment

- **Request:** Replace the empty-file and placeholder values in A10 with checksums for actual archived artifacts and provide an accessible verification route; otherwise remove unsupported cryptographic reproducibility claims.
- **Affected manuscript scope:** Appendix Table A10, artifact availability and reproducibility claims.
- **Technical status:** `VERIFIED_WITH_LIMITATIONS`
- **Reviewer satisfaction:** `PARTIALLY_ADDRESSED`
- **Evidence:** [`docs/hash-correction-20261028.md`](../hash-correction-20261028.md); [`docs/reviewer_closure/EVIDENCE_COMMITS.md`](EVIDENCE_COMMITS.md); [`docs/reviewer_closure/HISTORICAL_EVIDENCE_HANDOFF.md`](HISTORICAL_EVIDENCE_HANDOFF.md)
- **Protocol, population and observed result:** The submitted A10 contained one empty-file SHA-256 and four patterned example values. Five physical V3F/V3AG and specialist checkpoints have measured hashes, sizes and a release manifest in PR #4; Optuna DB and generic prediction artifact were not certified as recovered.
- **What the evidence addresses:** Actual model checkpoint identities are verifiable from the public release and separate correction evidence.
- **What remains unresolved:** The original Optuna database and generic prediction file are not located; the corrected artifact list is not a one-to-one substitute for every original A10 row.
- **Recoverability:** Bounded local/CEDIA/release checks found no verified copies of the two missing generic artifacts; a new authenticated backup listing could reopen this.
- **Experiment requirement:** No model experiment is needed for the five checkpoint hashes; do not fabricate hashes for missing files.
- **Future editorial action:** Replace A10 with the verified artifact inventory and explicitly remove claims for unavailable artifacts; preserve the submitted PDF unchanged.
- **Scientific risk:** High if unverified artifacts remain represented as hashed or reproducible.

### R2-general - Reviewer 2, Round 1, general class-scope comment

- **Request:** Represent excluded rhythm and pathology classes as Other arrhythmia/Other pathologies, or otherwise report them so excluded classes and NSR are not hidden from realistic performance assessment.
- **Affected manuscript scope:** Class ontology, primary and cascade heads, Methods and full-population results.
- **Technical status:** `NEW_EXPERIMENT_REQUIRED`
- **Reviewer satisfaction:** `NOT_SATISFIED`
- **Evidence:** [`docs/reviewer_closure/ROLE_SUPERVISION_AND_ROUTING.md`](ROLE_SUPERVISION_AND_ROUTING.md); [`docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`](ALL_INPUT_FLOW_COVERAGE.md); [`docs/revision-data-dispositions.md`](../revision-data-dispositions.md); [`docs/external_validation/sph_pac_probe_results.md`](../external_validation/sph_pac_probe_results.md); [`outputs/models/heads/global_head_contracts.json`](../../outputs/models/heads/global_head_contracts.json)
- **Protocol, population and observed result:** The published architecture declares 14 rhythm and 7 pathology outputs; P8 includes NSR and PAC. SPH measured all profile predictions on 25,770 ECG, but only 14 endpoints have compatible statement references. P8 produced 16,700 NSR top-1 outputs; no validated Other output exists. The additional code-30 PAC probe reports one statement endpoint from the same SPH source; it is not an all-class evaluation and does not define or validate Other.
- **What the evidence addresses:** All-input profile decisions and the limits of declared auxiliary outputs are now visible; missing scores and incompatible labels are not converted to negatives. The separate PAC probe adds a fully reported model comparison for one endpoint only; it does not close the Other/cascade request.
- **What remains unresolved:** No validated Other class, complete ontology, class-level labels for all inputs, or evaluated primary-to-cascade performance is available.
- **Recoverability:** The old outputs cannot establish the requested Other-class performance. A new dataset/reference mapping and model or routing evaluation would be needed.
- **Experiment requirement:** Required if the original all-class performance request is retained; not satisfied by narrowing text alone.
- **Future editorial action:** Describe only evaluated primary endpoints and explicitly state that Other/cascade performance is not validated.
- **Scientific risk:** Very high if all-input or Other performance is implied from class declarations or fallback counts.

### R2-1a - Reviewer 2, Round 1, point 1, abstract

- **Request:** Briefly explain what Primary6 rhythm specialist and Primary4 pathology specialist mean in the abstract and at first use in the main text.
- **Affected manuscript scope:** Abstract and first occurrence in the Introduction or Methods.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/architecture.md`](../architecture.md); [`docs/reviewer_closure/REVIEWER_48_STATUS.md`](REVIEWER_48_STATUS.md)
- **Protocol, population and observed result:** The release contract identifies P6 as six rhythm targets and P4 as four binary pathology panels; their model assets and evaluation units are separate.
- **What the evidence addresses:** The technical definitions are documented and can be stated without a new experiment.
- **What remains unresolved:** The submitted manuscript has not been revised to define the terms at the requested locations.
- **Recoverability:** No historical recovery is needed.
- **Experiment requirement:** None; editorial clarification only.
- **Future editorial action:** Add one-sentence definitions at both locations and retain distinct denominators.
- **Scientific risk:** Low if corrected; ambiguity remains until the manuscript is edited.

### R2-1b - Reviewer 2, Round 1, point 1, abbreviations

- **Request:** Define abbreviations at first use throughout the manuscript, tables and figures.
- **Affected manuscript scope:** Whole manuscript, tables, captions and figures.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/reviewer_closure/REVIEWER_48_STATUS.md`](REVIEWER_48_STATUS.md)
- **Protocol, population and observed result:** No model or dataset calculation is requested; the remaining work is a full-document terminology pass after scope and tables are fixed.
- **What the evidence addresses:** The need is identified but no final manuscript audit has been performed in this phase.
- **What remains unresolved:** First-use consistency in the submitted source remains unchecked against the final revised layout.
- **Recoverability:** Fully addressable in editorial review; no archive is needed.
- **Experiment requirement:** None.
- **Future editorial action:** Expand each abbreviation on first use and verify captions independently.
- **Scientific risk:** Low scientific risk; substantial readability risk if left inconsistent.

### R2-2a - Reviewer 2, Round 1, point 2, Introduction references

- **Request:** Add adequate references to the Introduction's general statements and make the study objective clear at the end of the section.
- **Affected manuscript scope:** Introduction before subsection 1.1 and final paragraph of the Introduction.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/reviewer_closure/REVIEWER_48_STATUS.md`](REVIEWER_48_STATUS.md); [`docs/reviewer_closure/REVIEWER_48_DETAILED.json`](REVIEWER_48_DETAILED.json)
- **Protocol, population and observed result:** This is a literature and framing request. The final scope is constrained by measured selected-cohort and SPH transfer evidence, not a claim of clinical deployment.
- **What the evidence addresses:** The intended scope can now be bounded by the evidence package, but the bibliography has not been rewritten or fully checked here.
- **What remains unresolved:** Reference adequacy, citation-to-claim fit and the final objective wording remain to be assessed after the author-approved scope is fixed.
- **Recoverability:** Addressable by bibliography review; no historical compute files are needed.
- **Experiment requirement:** None for citations; a broader scientific claim would require additional evidence, not just references.
- **Future editorial action:** Audit each general claim against primary literature and state a narrow descriptive/evaluative objective.
- **Scientific risk:** Moderate if unsupported background claims or an overbroad objective remain.

### R2-2b - Reviewer 2, Round 1, point 2, Figures 1 and 2

- **Request:** Explain the purpose of Figures 1 and 2 and identify their sources or provenance.
- **Affected manuscript scope:** Introduction figure captions, callouts and source acknowledgments.
- **Technical status:** `ACTIVE_RECOVERY_REQUIRED`
- **Reviewer satisfaction:** `PARTIALLY_ADDRESSED`
- **Evidence:** [`docs/reviewer_closure/REVIEWER_48_STATUS.md`](REVIEWER_48_STATUS.md); [`docs/figure-evidence.md`](../figure-evidence.md); [`docs/reviewer_closure/R2-2B_FIGURES_1_2_PROVENANCE.md`](R2-2B_FIGURES_1_2_PROVENANCE.md); [`outputs/figures/figure_manifest.json`](../../outputs/figures/figure_manifest.json)
- **Protocol, population and observed result:** The author-supplied source ZIP has SHA-256 36c1c6db30a759ef9d349ae2e545577cfd7ce3af91a3b97fb459380113f294a8 and contains the archived TeX callouts/captions and both figure PNGs. The figures match the repository manifest byte-for-byte; exact paths, hashes, dimensions and stated purposes are recorded in R2-2B_FIGURES_1_2_PROVENANCE.md.
- **What the evidence addresses:** The supplied archive establishes immediate source-package provenance and the purposes stated in its TeX: a proposed modular P6/P4 architecture (Figure 1) and a data-curation/harmonization workflow (Figure 2). This does not independently validate depicted historical operations.
- **What remains unresolved:** Creator/editor identity, any third-party assets and permissions are not established. The authors must confirm Figure 2's cohort/split claims against run-level evidence; the ZIP alone cannot prove execution or patient-level independence.
- **Recoverability:** Archive-level provenance is recovered. Authorship, third-party source and rights require author/source records or licenses; if these cannot be established, replace or remove affected content.
- **Experiment requirement:** None unless a figure makes a new empirical claim.
- **Future editorial action:** After author confirmation, attribute or identify the figures as author-created only if supported; narrow Figure 2 to verified operations and use an authorized replacement or remove it if origin/permissions remain unclear.
- **Scientific risk:** Moderate for unsupported provenance; high if an illustrative figure is presented as measured evidence.

### R2-2c - Reviewer 2, Round 1, point 2, Table 1 comparator selection

- **Request:** Justify why Table 1 selects only Life/MDPI studies, replace the unsupported representative/comparator framing, and explain what the table is intended to compare.
- **Affected manuscript scope:** Introduction Table 1, caption and comparator rationale.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/reviewer_closure/REVIEWER_48_STATUS.md`](REVIEWER_48_STATUS.md); [`docs/revision-data-dispositions.md`](../revision-data-dispositions.md)
- **Protocol, population and observed result:** No new benchmark comparison has been performed. Existing published studies differ in task, label ontology, cohort, sampling, parameter reporting and evaluation unit, so their headline values are not directly comparable.
- **What the evidence addresses:** The non-equivalence risk is recognized; no replacement systematic or balanced literature table is yet verified.
- **What remains unresolved:** A defensible study-selection rule, broader sources and comparable task definitions are needed if the table remains.
- **Recoverability:** Editorial literature work is feasible; it should not be replaced by selecting only favorable studies.
- **Experiment requirement:** No model experiment; any quantitative comparison must use compatible published endpoints and disclose differences.
- **Future editorial action:** Remove the Life-only selection or define a transparent, reproducible comparator scope and revise the caption.
- **Scientific risk:** High risk of selection bias and misleading state-of-the-art claims if unchanged.

### R2-2d - Reviewer 2, Round 1, point 2, parameter reporting

- **Request:** Explain missing architecture parameters, avoid comparisons between non-equivalent tasks, and clarify the table's purpose and direct-comparator terminology.
- **Affected manuscript scope:** Introduction Table 1 and architecture comparison text.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/architecture.md`](../architecture.md); [`docs/reviewer_closure/REVIEWER_48_STATUS.md`](REVIEWER_48_STATUS.md)
- **Protocol, population and observed result:** Repository model parameter counts and V4.5 architecture are documented, but many external papers report NR/proprietary values and unlike tasks cannot be normalized to a direct ranking.
- **What the evidence addresses:** The TITAN architecture's local parameter counts are documented; this does not fill missing comparator-study parameters.
- **What remains unresolved:** The manuscript table still needs explicit NR labels and task/cohort comparability caveats.
- **Recoverability:** Published comparator parameters can be checked from primary articles; undisclosed values cannot be reconstructed.
- **Experiment requirement:** None unless a new benchmark is proposed.
- **Future editorial action:** Report verified model counts, mark unreported values NR and avoid implying a direct performance comparison.
- **Scientific risk:** Moderate to high if unequal tasks are presented as head-to-head evidence.

### R2-2e - Reviewer 2, Round 1, point 2, SCP and abbreviations

- **Request:** Define SCP and every abbreviation used in the text, tables and figures.
- **Affected manuscript scope:** Introduction and all tables, legends and captions.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/reviewer_closure/REVIEWER_48_STATUS.md`](REVIEWER_48_STATUS.md)
- **Protocol, population and observed result:** No scientific calculation is involved; the requested verification must run on the final manuscript and all figure assets.
- **What the evidence addresses:** The issue is catalogued but no final abbreviation pass is complete.
- **What remains unresolved:** SCP's intended expansion and first-use order must be confirmed by authors from the study context.
- **Recoverability:** Editorially recoverable if authors can define the term; do not guess the expansion.
- **Experiment requirement:** None.
- **Future editorial action:** Confirm the intended meaning of SCP, define it and run a first-use audit.
- **Scientific risk:** Low, but an undefined technical acronym can obscure the method.

### R2-2f - Reviewer 2, Round 1, point 2, study placement and aim

- **Request:** Move implementation details of the present study out of the Introduction and state the study aim clearly at the end of the section.
- **Affected manuscript scope:** Introduction Table 2 and related description; final Introduction paragraph.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/architecture.md`](../architecture.md); [`docs/reviewer_closure/REVIEWER_48_STATUS.md`](REVIEWER_48_STATUS.md)
- **Protocol, population and observed result:** Architecture and operational scope are documented elsewhere in the repository; no manuscript restructuring has been carried out.
- **What the evidence addresses:** The technical source material is identifiable, but section placement remains unchanged.
- **What remains unresolved:** The authors must decide whether the final study is retrospective audit/transfer or a broader architecture evaluation.
- **Recoverability:** Editorially recoverable after scope approval.
- **Experiment requirement:** None for moving text; a broader stated aim must be supported by data.
- **Future editorial action:** Keep prior-art synthesis in Introduction, move this study's implementation to Methods and add a bounded aim.
- **Scientific risk:** Moderate if the aim overstates what the study actually demonstrates.

### R2-3a - Reviewer 2, Round 1, point 3, database and split description

- **Request:** Describe each database, available and used classes, segment counts, and ECG/patient numbers by training, validation and test split; explain what happened to remaining classes.
- **Affected manuscript scope:** Materials and Methods dataset subsection and split tables.
- **Technical status:** `EVIDENCE_CEILING_REACHED`
- **Reviewer satisfaction:** `PARTIALLY_ADDRESSED`
- **Evidence:** [`docs/reviewer_closure/SPLIT_CALIBRATION_DISPOSITION.md`](SPLIT_CALIBRATION_DISPOSITION.md); [`docs/reviewer_closure/R1_2_EVIDENCE_CEILING.md`](R1_2_EVIDENCE_CEILING.md); [`outputs/results/revision_replay_diagnostics_20261107/p4_official_fold_coverage.json`](../../outputs/results/revision_replay_diagnostics_20261107/p4_official_fold_coverage.json); [`docs/reviewer_closure/HISTORICAL_EVIDENCE_HANDOFF.md`](HISTORICAL_EVIDENCE_HANDOFF.md); [`docs/reviewer_closure/CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md`](CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md); [`docs/reviewer_closure/RECOVERED_VS_MISSING_HISTORICAL_EVIDENCE.md`](RECOVERED_VS_MISSING_HISTORICAL_EVIDENCE.md)
- **Protocol, population and observed result:** Verified selected counts are P6 1,643 ECG, P8 2,193 ECG, and P4 962 panel rows over 733 ECG/676 patients. PTB-XL fold 10 has 2,198 ECG/1,904 patients; 733 P4 ECG map to 676 fold-10 patients with no overlap with official folds 1-9. SLURM records V3H jobs 16785/16786 and V3M jobs 16816/16819 as completed, but their exact historical work directories and full split files are absent at the checked paths.
- **What the evidence addresses:** Selected counts, official fold relation, completed-job accounting, checkpoint-declared manifest names and surviving calibration logs are documented with their different evidentiary strength.
- **What remains unresolved:** Historical train/validation/calibration manifests, patient mappings and full per-class source counts are not all linked to released checkpoints; official fold membership and a completed job do not certify historical patient isolation.
- **Recoverability:** Reopen only with exact job/checkpoint-linked split manifests and exclusions. The supplied archives, exact work-directory checks and NOC-reviewed backup did not recover them; this is not a global-absence finding.
- **Experiment requirement:** A new split analysis is required for any new model; historical split claims cannot be recreated from selected results.
- **Future editorial action:** Report known selected counts and explicitly mark unrecovered historical counts/isolation as unknown.
- **Scientific risk:** High if official folds or selected cohorts are presented as proof of historical train/test isolation.

### R2-3b - Reviewer 2, Round 1, point 3, design versus evaluation

- **Request:** Clarify whether the study only evaluates specialist networks or also designs them.
- **Affected manuscript scope:** Materials and Methods opening statement and study aim.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/architecture.md`](../architecture.md); [`docs/reviewer_closure/REVIEWER_48_STATUS.md`](REVIEWER_48_STATUS.md); [`docs/reviewer_closure/CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md`](CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md)
- **Protocol, population and observed result:** Available evidence covers architecture contracts, selected historical predictions, reconstructed replay and later SPH transfer; it does not make these evidence types interchangeable. CEDIA job 17314 records a multi-epoch P6 gate sweep, and job 17315 reports epoch 8 against the named V3H manifest, so V3H must be treated as development/model-selection evidence.
- **What the evidence addresses:** The technical package distinguishes design from evaluation stages.
- **What remains unresolved:** The manuscript has not yet stated the exact retrospective scope and what was designed versus evaluated.
- **Recoverability:** Editorially recoverable using existing evidence; no historical search required.
- **Experiment requirement:** None for wording; claims of a new design process require corresponding provenance.
- **Future editorial action:** State exactly which architecture was developed, which checkpoints were evaluated and which replays are reconstructed.
- **Scientific risk:** Moderate if design and evaluation evidence are conflated.

### R2-3c - Reviewer 2, Round 1, point 3, cascade and auxiliary rhythm labels

- **Request:** Explain how primary, cascade and auxiliary rhythm labels are used in training and evaluation, and do not describe NSR as a low-prevalence arrhythmia.
- **Affected manuscript scope:** Methods class-role description and training/evaluation flow.
- **Technical status:** `VERIFIED_WITH_LIMITATIONS`
- **Reviewer satisfaction:** `PARTIALLY_ADDRESSED`
- **Evidence:** [`docs/reviewer_closure/ROLE_SUPERVISION_AND_ROUTING.md`](ROLE_SUPERVISION_AND_ROUTING.md); [`outputs/models/heads/global_head_contracts.json`](../../outputs/models/heads/global_head_contracts.json); [`docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`](ALL_INPUT_FLOW_COVERAGE.md); [`docs/reviewer_closure/OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md`](OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md)
- **Protocol, population and observed result:** The contract declares P8's eight outputs, including NSR, plus six additional global rhythm outputs. SPH P8 predicts NSR top-1 on 16,700 records; P8 fallback is separately recorded. The code and outputs do not prove run-specific training support for each auxiliary class.
- **What the evidence addresses:** Implemented output and fallback roles are described; NSR is a rhythm category, not an arrhythmia class by that fact alone.
- **What remains unresolved:** Checkpoint-linked positive/negative training supports and exact historical class selection remain unavailable for auxiliary outputs.
- **Recoverability:** Recoverable only with original training labels/masks, manifests, configuration, logs and checkpoint linkage.
- **Experiment requirement:** No new experiment needed to state current contract; new supervised class performance requires a valid training/evaluation design.
- **Future editorial action:** Separate declared outputs, training supervision, scored predictions and role/routing; correct the NSR description.
- **Scientific risk:** High if output presence is treated as evidence of training or validated cascade performance.

### R2-3d - Reviewer 2, Round 1, point 3, ALMI/ILMI/LAE

- **Request:** Clarify whether ALMI, ILMI and LAE were trained and evaluated or merely logged as auxiliary pathology labels.
- **Affected manuscript scope:** Methods pathology head, training masks and results scope.
- **Technical status:** `EVIDENCE_CEILING_REACHED`
- **Reviewer satisfaction:** `NOT_SATISFIED`
- **Evidence:** [`docs/reviewer_closure/ROLE_SUPERVISION_AND_ROUTING.md`](ROLE_SUPERVISION_AND_ROUTING.md); [`docs/revision-data-dispositions.md`](../revision-data-dispositions.md); [`outputs/models/heads/global_head_contracts.json`](../../outputs/models/heads/global_head_contracts.json); [`docs/reviewer_closure/OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md`](OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md)
- **Protocol, population and observed result:** The global contract has seven pathology outputs, and reconstructed P4 inference emitted ALMI/ILMI/LAE scores on 733 selected ECG. A candidate manifest has positives, but it is not linked to the released checkpoint's training run.
- **What the evidence addresses:** It is verified that outputs are emitted in the reconstructed path, not that the historical checkpoint was trained on those labels.
- **What remains unresolved:** Historical supervision supports, loss masks, selection policy and evaluation metrics for these outputs are not certified.
- **Recoverability:** Requires exact training/validation manifests, labels/masks, run configuration and checkpoint-linked job receipt; no inference can reconstruct missing provenance.
- **Experiment requirement:** New training and evaluation are required if performance for these classes is claimed.
- **Future editorial action:** Describe them as unvalidated auxiliary outputs or remove claims of trained/evaluated pathology classes.
- **Scientific risk:** High if auxiliary scores are reported as established diagnostic performance.

### R2-3e - Reviewer 2, Round 1, point 3, Table 5 Role

- **Request:** Define what Role means in Table 5 and how role assignments are determined.
- **Affected manuscript scope:** Table 5 and Methods role/route definitions.
- **Technical status:** `VERIFIED_WITH_LIMITATIONS`
- **Reviewer satisfaction:** `PARTIALLY_ADDRESSED`
- **Evidence:** [`docs/reviewer_closure/ROLE_SUPERVISION_AND_ROUTING.md`](ROLE_SUPERVISION_AND_ROUTING.md); [`src/titan_v45/cascade/policy.py`](../../src/titan_v45/cascade/policy.py); [`docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`](ALL_INPUT_FLOW_COVERAGE.md); [`docs/reviewer_closure/OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md`](OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md)
- **Protocol, population and observed result:** The code declares primary, auxiliary and cascade roles; the selected replay measures only implemented decision behavior. The historic per-record role/transition ledger is unavailable; SPH fallback counts are not quarantine transitions.
- **What the evidence addresses:** Code roles, predicted outputs and observed transitions are explicitly distinguished.
- **What remains unresolved:** Historical assignment and role-transition counts for the original all-input pathway are not recoverable from the selected panels.
- **Recoverability:** Reopen only with the authentic role/transition ledger, policy version and linked predictions.
- **Experiment requirement:** A new measured operational workflow is required if human review or route effectiveness is retained as a claim.
- **Future editorial action:** Define Role as a declared data/model contract and avoid interpreting it as actual human review.
- **Scientific risk:** High if a declared role is mistaken for measured routing or clinician action.

### R2-3f - Reviewer 2, Round 1, point 3, Figures 5 and 6

- **Request:** Name and define the ten morphology features, explain asymmetric arrows and every block-diagram connection, and correct or remove unsupported flow arrows.
- **Affected manuscript scope:** Methods architecture and Figures 5-6 plus captions.
- **Technical status:** `EVIDENCE_CEILING_REACHED`
- **Reviewer satisfaction:** `PARTIALLY_ADDRESSED`
- **Evidence:** [`docs/recovered-feature-contract.md`](../recovered-feature-contract.md); [`docs/reviewer_closure/REPLAY_EQUIVALENCE_DISPOSITION.md`](REPLAY_EQUIVALENCE_DISPOSITION.md); [`docs/figure-evidence.md`](../figure-evidence.md); [`docs/reviewer_closure/HISTORICAL_LOADER_IDENTITY_AND_REPLAY.md`](HISTORICAL_LOADER_IDENTITY_AND_REPLAY.md)
- **Protocol, population and observed result:** Ten-feature candidate code and several historical event sources were recovered; 10 of 11 inventoried files match known hashes. The exact original loader is absent. P4 replay matched 962/962 decisions but maximum probability residual 0.0006194115 exceeds historical tolerance 1e-5.
- **What the evidence addresses:** The candidate feature contract and its provenance boundary are documented, and strict score equivalence is explicitly recorded as failed.
- **What remains unresolved:** Exact historical feature implementation, loader identity and the figure-to-runtime arrow semantics are not fully verified.
- **Recoverability:** The exact loader may reopen this only if supplied with its expected hash fc8d7367f9f2c108376839435021ec3172fe2757faa4a615f0ef5d39cbf1e855 or an independently linked source snapshot.
- **Experiment requirement:** No threshold retuning; a future replay may test equivalence only if the exact loader and inputs are recovered.
- **Future editorial action:** List each feature and unit, redraw arrows to match verified dataflow, and identify reconstructed code as such.
- **Scientific risk:** High if a candidate implementation is represented as the exact historical architecture.

### R2-3g - Reviewer 2, Round 1, point 3, Brier score statements

- **Request:** Move numerical Brier scores from Methods to Results if they are observed results, and distinguish the metric definition from the measured values.
- **Affected manuscript scope:** Evaluation Metrics and Confidence Intervals subsection and Results.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/reviewer_closure/METRIC_DEFINITIONS.md`](METRIC_DEFINITIONS.md); [`docs/external_validation/sph_results.md`](../external_validation/sph_results.md)
- **Protocol, population and observed result:** The metric definitions and later SPH Brier scores are available in separate documents; this reviewer comment concerns location and attribution of method versus results.
- **What the evidence addresses:** The evidence distinguishes definitions from observed results; the submitted manuscript has not been edited.
- **What remains unresolved:** All original numerical claims in Methods must be traced to their exact cohort and moved or removed.
- **Recoverability:** Editorially recoverable from the audited metric outputs.
- **Experiment requirement:** None if the original results are accurately sourced; no unsupported value should be retained.
- **Future editorial action:** Keep the Brier definition in Methods and report cohort-specific values only in Results.
- **Scientific risk:** Moderate if numbers are presented as prespecified method constants rather than measured outcomes.

### R2-3h - Reviewer 2, Round 1, point 3, accuracy metrics

- **Request:** Provide equations and explanations for all accuracy metrics and clarify whether rhythm and pathology metrics differ and why.
- **Affected manuscript scope:** Evaluation Metrics and Confidence Intervals subsection.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/reviewer_closure/METRIC_DEFINITIONS.md`](METRIC_DEFINITIONS.md); [`docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`](ALL_INPUT_FLOW_COVERAGE.md)
- **Protocol, population and observed result:** The repository defines panel-level binary P4 metrics separately from multiclass/top-1 rhythm metrics; the SPH endpoints are per-class statement-level binary comparisons.
- **What the evidence addresses:** The distinctions are documented and testable, but equations have not been inserted into the manuscript.
- **What remains unresolved:** The final manuscript still needs equations matched to each reported unit, averaging scheme, denominator and missing-label rule.
- **Recoverability:** Editorially recoverable from documented formulas and outputs.
- **Experiment requirement:** None for equations; any value must be recomputed if its denominator or metric definition changes.
- **Future editorial action:** Define accuracy, macro-F1, top-1, AUROC, AP and calibration with their exact units and averaging rules.
- **Scientific risk:** High if panel rows, ECG counts and class-wise binary endpoints are conflated.

### R2-4a - Reviewer 2, Round 1, point 4, Table 8 terminology

- **Request:** Define the external-development evidence package, say whether it is the test dataset, use consistent terminology and describe it in the database or Methods section.
- **Affected manuscript scope:** Results Table 8 and cohort/methods description.
- **Technical status:** `VERIFIED_WITH_LIMITATIONS`
- **Reviewer satisfaction:** `PARTIALLY_ADDRESSED`
- **Evidence:** [`docs/evidence-status.md`](../evidence-status.md); [`docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`](ALL_INPUT_FLOW_COVERAGE.md); [`docs/external_validation/sph_results.md`](../external_validation/sph_results.md); [`docs/reviewer_closure/CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md`](CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md)
- **Protocol, population and observed result:** The release separates selected development predictions from the later frozen SPH transfer. Primary6 contains 1,643 ECG; P8 contains 2,193 with P6 nested; P4 uses 962 panel rows/733 ECG. SPH is 25,770 ECG from another source. CEDIA jobs 17314/17315 show that the V3H P6 gate informed epoch selection and is not an untouched test.
- **What the evidence addresses:** The evidence packages and populations are now named and numerically distinguished in technical documentation.
- **What remains unresolved:** Complete historical usage and selection lineage of every development package remain unknown; V3H selection exposure is now documented, but the exact 17314 manifest and complete backbone lineage remain unavailable. The manuscript terminology has not been harmonized.
- **Recoverability:** Historical usage is bounded by the recovery ceiling; terminology is editorially recoverable.
- **Experiment requirement:** None for definition; new evidence is needed for any independent-test interpretation.
- **Future editorial action:** Define each package as a concrete artifact/population and use one term consistently.
- **Scientific risk:** High if selected development cohorts are described as independent tests.

### R2-4b - Reviewer 2, Round 1, point 4, figure cross-reference

- **Request:** Correct the paragraph after Table 8 to refer to Figure 8 rather than Figure 10.
- **Affected manuscript scope:** Results paragraph immediately following Table 8.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/reviewer_closure/REVIEWER_48_STATUS.md`](REVIEWER_48_STATUS.md)
- **Protocol, population and observed result:** A cross-reference correction is requested; no new data or model execution is needed.
- **What the evidence addresses:** The defect is identified, but the submitted manuscript remains unchanged.
- **What remains unresolved:** Final figure numbering may change during layout and must be checked after the final figure assembly.
- **Recoverability:** Fully editorially recoverable.
- **Experiment requirement:** None.
- **Future editorial action:** Correct the reference and recheck all figure/table references after composition.
- **Scientific risk:** Low scientific risk; incorrect references impair verification.

### R2-4c - Reviewer 2, Round 1, point 4, F1 interpretation

- **Request:** Do not call F1 values around 62.58% and 65.64% reliable performance; revise the strength of the interpretation.
- **Affected manuscript scope:** Results paragraph on 1AVB and PVC and corresponding Discussion claims.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`outputs/results/primary/canonical_profiles.json`](../../outputs/results/primary/canonical_profiles.json); [`docs/external_validation/sph_results.md`](../external_validation/sph_results.md)
- **Protocol, population and observed result:** Historical selected-panel P6 F1 is 62.58% for 1AVB and 65.64% for PVC. Later SPH statement-level results are lower for P6 PVC (54.08%) and differ in population/reference; they must not be conflated.
- **What the evidence addresses:** Canonical values and the unfavorable transfer result are available for a bounded interpretation.
- **What remains unresolved:** The original adjective remains in the submitted manuscript and requires author-approved replacement.
- **Recoverability:** Editorially recoverable from verified metrics; no further data recovery needed to remove the adjective.
- **Experiment requirement:** None to moderate the wording; any claim of reliability requires a defined operational criterion and validation.
- **Future editorial action:** Describe exact F1 values and cohort; avoid 'reliable' without a prespecified threshold.
- **Scientific risk:** High if a moderate F1 is framed as reliable diagnostic performance.

### R2-4d - Reviewer 2, Round 1, point 4, Figure 8 caption and uncertainty

- **Request:** Correct Figure 8's caption to acknowledge precision, recall and F1, and show or accurately describe the absence of 95% confidence bounds.
- **Affected manuscript scope:** Results Figure 8 graphic and caption.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/external_validation/sph_results.md`](../external_validation/sph_results.md); [`docs/reviewer_closure/REVIEWER_48_STATUS.md`](REVIEWER_48_STATUS.md)
- **Protocol, population and observed result:** The plotted metrics and the available patient-component intervals are distinct artifacts; the original figure/caption must be reconciled with the final values and intervals.
- **What the evidence addresses:** The evidence package defines available uncertainty intervals; the submitted figure has not been replaced or recaptioned.
- **What remains unresolved:** It is not established that every plotted bar has a matching interval in the current submitted figure.
- **Recoverability:** Editorially recoverable by regenerating the figure from the selected aggregate and explicitly displaying uncertainty where computed.
- **Experiment requirement:** No new ECG experiment; interval calculation is needed only if the final figure reports confidence intervals not already available.
- **Future editorial action:** Rebuild from the exact source table, label all three measures and either show valid bounds or state they are not shown.
- **Scientific risk:** Moderate if a point estimate is visually implied to carry confidence bounds it does not show.

### R2-4e - Reviewer 2, Round 1, point 4, threshold non-crossing

- **Request:** Explain what happens when no class score crosses its threshold and how such cases are counted.
- **Affected manuscript scope:** Decision policy in Methods and all-input Results.
- **Technical status:** `EXPERIMENT_COMPLETED_WITH_LIMITATIONS`
- **Reviewer satisfaction:** `PARTIALLY_ADDRESSED`
- **Evidence:** [`docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`](ALL_INPUT_FLOW_COVERAGE.md); [`docs/reviewer_closure/ROLE_SUPERVISION_AND_ROUTING.md`](ROLE_SUPERVISION_AND_ROUTING.md); [`outputs/results/revision_20261107/rhythm_waveform.json`](../../outputs/results/revision_20261107/rhythm_waveform.json); [`outputs/results/revision_20261107/pathology_waveform.json`](../../outputs/results/revision_20261107/pathology_waveform.json); [`docs/reviewer_closure/OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md`](OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md)
- **Protocol, population and observed result:** On all 25,770 SPH ECG, P6 had 16,785 empty threshold sets; P4 had 8,343; P8 applied top-1 fallback on 801. In the selected replay P8 fallback was 58/2,193. No reference labels were used to route.
- **What the evidence addresses:** No-crossing behavior and complete-source counts are now measured for the frozen profiles.
- **What remains unresolved:** P6/P4 empty sets and P8 fallback do not establish a quarantine rate, an Other class, or human review; historical all-input June routes remain unknown.
- **Recoverability:** Measured profile behavior is complete for the frozen SPH run; historical route history needs its original policy and ledger.
- **Experiment requirement:** No new experiment to state these frozen rules; a quarantine effectiveness claim requires a separate defined evaluation.
- **Future editorial action:** Define thresholding and fallback separately, report denominators and do not relabel fallback as quarantine.
- **Scientific risk:** High if empty sets/fallback are hidden or represented as clinical review.

### R2-4f - Reviewer 2, Round 1, point 4, Figure 9 units

- **Request:** Use a consistent numeric or percentage presentation across Figures 7 and 9.
- **Affected manuscript scope:** Results Figures 7 and 9 and captions.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/reviewer_closure/REVIEWER_48_STATUS.md`](REVIEWER_48_STATUS.md)
- **Protocol, population and observed result:** This is a visual consistency issue; no model or cohort calculation is requested.
- **What the evidence addresses:** The required edit is identified, but the submitted figures remain unchanged.
- **What remains unresolved:** The final unit convention must be applied after the final figure selection.
- **Recoverability:** Fully editorially recoverable.
- **Experiment requirement:** None.
- **Future editorial action:** Choose counts or percentages consistently and verify axis labels, color scales and captions.
- **Scientific risk:** Low scientific risk; mixed units can confuse comparative reading.

### R2-4g - Reviewer 2, Round 1, point 4, duplicate figures

- **Request:** Resolve the reported duplication between Figures 8 and 10.
- **Affected manuscript scope:** Results figures and final figure inventory.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/reviewer_closure/REVIEWER_48_STATUS.md`](REVIEWER_48_STATUS.md); [`docs/figure-evidence.md`](../figure-evidence.md)
- **Protocol, population and observed result:** The comment identifies duplicate content in the submitted layout; no new empirical result is required to remove a duplicate.
- **What the evidence addresses:** The figure-level issue is recorded; a final accepted figure set has not been assembled.
- **What remains unresolved:** Figure identity, captions and cross-references must be checked together after editorial revisions.
- **Recoverability:** Fully editorially recoverable from original figure sources.
- **Experiment requirement:** None unless the duplicate figure contains unique, unverified data.
- **Future editorial action:** Retain one authoritative figure or document the distinct information each figure conveys.
- **Scientific risk:** Low scientifically, but duplication undermines presentation quality and traceability.

### R2-4h - Reviewer 2, Round 1, point 4, ROC/PR evaluation unit

- **Request:** Define what 'evaluation tracings' means in the ROC and precision-recall description and use the correct ECG-level unit.
- **Affected manuscript scope:** Results text for Figures 11 and 12 and metric methods.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/reviewer_closure/METRIC_DEFINITIONS.md`](METRIC_DEFINITIONS.md); [`docs/external_validation/sph_results.md`](../external_validation/sph_results.md)
- **Protocol, population and observed result:** The frozen SPH score curves use ECG-record statements; historical development metrics use their own selected record/panel units.
- **What the evidence addresses:** The technical evidence identifies the relevant record-level units; the manuscript's ambiguous phrase remains unchanged.
- **What remains unresolved:** The text must identify the exact cohort, endpoint and unit for each plotted curve.
- **Recoverability:** Editorially recoverable from the plot source and protocol.
- **Experiment requirement:** None if the source arrays and endpoint remain unchanged.
- **Future editorial action:** Replace 'evaluation tracings' with the precise ECG-record denominator and name each target.
- **Scientific risk:** Moderate if rhythm classes, ECGs and panel rows are treated as the same unit.

### R2-4i - Reviewer 2, Round 1, point 4, AUROC interpretation

- **Request:** Revise the characterization of 87.46% pathology macro-AUROC as high.
- **Affected manuscript scope:** Results interpretation of rhythm and pathology macro-AUROC.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`outputs/results/primary/canonical_profiles.json`](../../outputs/results/primary/canonical_profiles.json); [`docs/external_validation/sph_results.md`](../external_validation/sph_results.md)
- **Protocol, population and observed result:** The selected P4 macro-AUROC is 87.46%; its unit and population differ from later endpoint-specific SPH AUROCs, including low PPV/F1 despite some high AUROC values.
- **What the evidence addresses:** Canonical and transfer values are available for a qualified description.
- **What remains unresolved:** The adjective and interpretation in the submitted manuscript have not been revised.
- **Recoverability:** Editorially recoverable from verified metrics.
- **Experiment requirement:** None to revise the adjective; broader clinical meaning requires a prespecified benchmark.
- **Future editorial action:** Report the value without 'high' or explain its context, metric uncertainty and class-specific limitations.
- **Scientific risk:** Moderate to high if discrimination is used to imply good operating performance.

### R2-4j - Reviewer 2, Round 1, point 4, Figure 13 calibration

- **Request:** Use consistent observed-frequency/empirical-accuracy terminology, define how it is estimated and make the ten confidence-bin axes match their stated range.
- **Affected manuscript scope:** Figure 13 axes, caption and calibration-method description.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/reviewer_closure/METRIC_DEFINITIONS.md`](METRIC_DEFINITIONS.md); [`outputs/results/external_sph/sph_aggregate_32669.json`](../../outputs/results/external_sph/sph_aggregate_32669.json)
- **Protocol, population and observed result:** The frozen SPH aggregate reports ECE with ten bins; calibration curves and metrics are defined for the actual scored endpoints. This does not certify the original Figure 13's plotted source or axis ticks.
- **What the evidence addresses:** A reproducible calibration definition and later source-specific ECE evidence exist.
- **What remains unresolved:** The submitted calibration plot and its data source must be matched to the final binning implementation and labels.
- **Recoverability:** Recoverable from the figure source data and plotting script; do not infer from the image alone.
- **Experiment requirement:** No new inference if the same saved probabilities and fixed bins are used; otherwise recompute from the correct source.
- **Future editorial action:** Define bin occupancy and mean confidence versus observed statement frequency; standardize labels/ticks and document empty bins.
- **Scientific risk:** Moderate if a calibration curve is mislabeled or its estimate cannot be reproduced.

### R2-4k - Reviewer 2, Round 1, point 4, quarantine rates

- **Request:** Define the quarantine rate and pre/post-quarantine accuracy and explain how these values are estimated.
- **Affected manuscript scope:** Methods quarantine policy and Results figures/tables reporting rates or accuracy.
- **Technical status:** `EVIDENCE_CEILING_REACHED`
- **Reviewer satisfaction:** `NOT_SATISFIED`
- **Evidence:** [`docs/reviewer_closure/ROLE_SUPERVISION_AND_ROUTING.md`](ROLE_SUPERVISION_AND_ROUTING.md); [`docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`](ALL_INPUT_FLOW_COVERAGE.md); [`outputs/results/revision_20261107/rhythm_waveform.json`](../../outputs/results/revision_20261107/rhythm_waveform.json); [`outputs/results/revision_20261107/pathology_waveform.json`](../../outputs/results/revision_20261107/pathology_waveform.json); [`docs/reviewer_closure/OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md`](OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md)
- **Protocol, population and observed result:** The selected reconstruction and all-input SPH flow contain no checkpoint-linked uncertainty score plus verified quarantine policy; quarantine is not assessed, not 0%. P8 fallback and empty sets are not quarantine.
- **What the evidence addresses:** The invalid inference from fallback to quarantine is explicitly rejected; routing counts are documented with their actual semantics.
- **What remains unresolved:** No historic pre/post ledger, quarantine denominator, policy version or uncertainty inputs are available; rates and pre/post accuracy cannot be reconstructed.
- **Recoverability:** Reopen only if an authentic policy, ledger, score inputs and checkpoint/job linkage are recovered.
- **Experiment requirement:** Required to support any quarantine effectiveness claim; otherwise the claim and rate must be removed.
- **Future editorial action:** Do not report an assumed quarantine percentage; mark historical rate unavailable or remove the claim.
- **Scientific risk:** Very high if invented or unmeasured quarantine benefit/rates remain.

### R2-4l - Reviewer 2, Round 1, point 4, rhythm top-1

- **Request:** Define rhythm top-1 accuracy and explain exactly how it is calculated.
- **Affected manuscript scope:** Metrics Methods and Results table/figure captions.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/reviewer_closure/METRIC_DEFINITIONS.md`](METRIC_DEFINITIONS.md); [`docs/reviewer_closure/ROLE_SUPERVISION_AND_ROUTING.md`](ROLE_SUPERVISION_AND_ROUTING.md); [`outputs/results/primary/canonical_profiles.json`](../../outputs/results/primary/canonical_profiles.json)
- **Protocol, population and observed result:** The selected P6 top-1 accuracy is 1,564/1,643 = 95.19%; P8 has its own accepted top-1 denominator and fallback semantics. Neither is pooled P4 panel accuracy.
- **What the evidence addresses:** The calculation and selected denominators can be traced in code and canonical results.
- **What remains unresolved:** The submitted manuscript must define argmax, denominator, treatment of fallback and selected-cohort scope.
- **Recoverability:** Editorially recoverable from canonical metrics and decision policy.
- **Experiment requirement:** None if definitions and data remain unchanged.
- **Future editorial action:** State the per-record argmax rule and report P6/P8 separately, including fallback treatment.
- **Scientific risk:** High if top-1 is interpreted as all-class or end-to-end accuracy.

### R2-4m - Reviewer 2, Round 1, point 4, Figures 14 and 15 readability

- **Request:** Improve unreadable axes and values in Figures 14 and 15 and check all figures.
- **Affected manuscript scope:** Final manuscript figure source, captions and rendered PDF.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/figure-evidence.md`](../figure-evidence.md); [`docs/reviewer_closure/REVIEWER_48_STATUS.md`](REVIEWER_48_STATUS.md)
- **Protocol, population and observed result:** The submitted figure quality concern is known; this technical phase intentionally does not regenerate the manuscript or its final figures.
- **What the evidence addresses:** A later layout/render check is explicitly reserved; no claim is made that the figures are currently fixed.
- **What remains unresolved:** Font sizes, axis labels, line weights, contrast and page-scale legibility remain unverified in the final layout.
- **Recoverability:** Editorially recoverable from vector/source figures after content and scope are frozen.
- **Experiment requirement:** None if plots use verified aggregates; new evidence is needed only if the plot content changes empirically.
- **Future editorial action:** Regenerate, render the final PDF and inspect every page at realistic size; verify captions and all figure callouts.
- **Scientific risk:** Moderate if key values cannot be read or visual framing overstates results.

### R2-5 - Reviewer 2, Round 1, point 5, PVC unit of analysis

- **Request:** Acknowledge that PVC is often analyzed at heartbeat level and avoid treating 10-second ECG-level classification as beat-level detection.
- **Affected manuscript scope:** Discussion of PVC performance and any heartbeat-level interpretation.
- **Technical status:** `VERIFIED_WITH_LIMITATIONS`
- **Reviewer satisfaction:** `PARTIALLY_ADDRESSED`
- **Evidence:** [`docs/reviewer_closure/AF_PVC_REFERENCE_DISPOSITION.md`](AF_PVC_REFERENCE_DISPOSITION.md); [`docs/external_validation/sph_results.md`](../external_validation/sph_results.md); [`configs/external_validation/sph_frozen.json`](../../configs/external_validation/sph_frozen.json)
- **Protocol, population and observed result:** SPH PVC uses ECG statement code 60: 1,067 positive and 24,703 negative recorded-statement comparisons per P6/P8; F1 is 54.08% for P6 and 66.16% for P8. No beat annotations or localization metric are present.
- **What the evidence addresses:** The available result is correctly bounded to record-level ECG statement agreement.
- **What remains unresolved:** Beat-level detection, temporal matching, episode counts and clinical adjudication are not measured.
- **Recoverability:** Cannot be recovered from record-level codes; needs beat-labeled ECGs and matching protocol.
- **Experiment requirement:** Required if beat detection or localization is claimed; not required for a strictly record-level statement study.
- **Future editorial action:** Explicitly state the ECG-level unit and remove any beat-level performance implication.
- **Scientific risk:** High if record-level F1 is interpreted as heartbeat detector accuracy.

### R2-6 - Reviewer 2, Round 1, point 6, distortion and citation

- **Request:** Clarify whether the claim that the framework eliminates diagnostic distortion refers to this study and justify or correct citation [4].
- **Affected manuscript scope:** Discussion claim and its cited reference.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `EDITORIAL_ACTION_ONLY`
- **Evidence:** [`docs/reviewer_closure/REVIEWER_48_STATUS.md`](REVIEWER_48_STATUS.md); [`docs/external_validation/sph_results.md`](../external_validation/sph_results.md)
- **Protocol, population and observed result:** Observed external transfer includes very low PPV/F1 for P4 and P8 PAC; the data do not establish that the framework eliminates diagnostic distortion or provides an uncompromised benchmark.
- **What the evidence addresses:** The measured evidence constrains the claim and identifies the need to verify the reference.
- **What remains unresolved:** The submitted sentence and citation have not been corrected; citation [4] must be checked against the final claim.
- **Recoverability:** Editorially recoverable, but a stronger causal claim would require new comparative evidence.
- **Experiment requirement:** None if the absolute claim is removed; required for any retained claim that the architecture eliminates distortion.
- **Future editorial action:** Replace the absolute claim with a bounded observation or remove it, and verify the cited source.
- **Scientific risk:** High if the manuscript asserts elimination of bias or distortion without an appropriate comparison.

### A-01 - Project audit A-01 (not a reviewer comment)

- **Request:** Reconcile the P4 panel denominator with unique ECG and patient counts.
- **Affected manuscript scope:** P4 cohort descriptions, tables and denominator statements.
- **Technical status:** `VERIFIED_COMPLETE`
- **Reviewer satisfaction:** `NOT_APPLICABLE_AUDIT`
- **Evidence:** [`docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`](ALL_INPUT_FLOW_COVERAGE.md); [`docs/reviewer_closure/R1_2_EVIDENCE_CEILING.md`](R1_2_EVIDENCE_CEILING.md); [`data/manifests/external_dev/pathology_primary4_panels.csv`](../../data/manifests/external_dev/pathology_primary4_panels.csv)
- **Protocol, population and observed result:** The selected P4 manifest has 962 panel rows, 733 distinct ECG record keys and 676 patients linked to PTB-XL metadata.
- **What the evidence addresses:** The units are separately counted and used consistently in the evidence report.
- **What remains unresolved:** Historical upstream candidate population and exclusion reasons remain outside this selected denominator.
- **Recoverability:** The selected counts are complete; the upstream historical population is at the recovery ceiling.
- **Experiment requirement:** None to verify the selected count; patient isolation still requires missing train/calibration manifests.
- **Future editorial action:** Use 'panel observations', 'unique ECG' and 'patients' with their correct denominators.
- **Scientific risk:** High if 962 binary panel observations are called 962 unique ECGs.

### A-02 - Project audit A-02 (not a reviewer comment)

- **Request:** Reconcile source distributions, aliases and potential duplicate signals across manuscript tables and manifests.
- **Affected manuscript scope:** Source-stratified Tables A5/A6 and claims of multicenter independence.
- **Technical status:** `VERIFIED_WITH_LIMITATIONS`
- **Reviewer satisfaction:** `NOT_APPLICABLE_AUDIT`
- **Evidence:** [`docs/reviewer_closure/SOURCE_RIGHTS_DISPOSITION.md`](SOURCE_RIGHTS_DISPOSITION.md); [`docs/external_validation/sph_independence_assessment.md`](../external_validation/sph_independence_assessment.md); [`configs/external_validation/sph_frozen.json`](../../configs/external_validation/sph_frozen.json)
- **Protocol, population and observed result:** Selected source support and signal-hash audits are documented; exact duplicate groups and cross-source signatures were tested for the frozen SPH transfer. The test does not certify all historical training sources or patient identities.
- **What the evidence addresses:** Known alias and signal-identity checks are recorded with scope limits.
- **What remains unresolved:** Historical cross-dataset patient linkage and incomplete training-source manifests prevent a global independence statement.
- **Recoverability:** Reopen with complete source manifests and permitted patient/signal linkage; absence of a name is not proof of no exposure.
- **Experiment requirement:** New source-independence checks are needed for any new external test using other data.
- **Future editorial action:** Report exact source counts and distinguish signal duplicate screening from patient-level independence.
- **Scientific risk:** High if source aliases or zero detected signatures are treated as proof of fully independent cohorts.

### A-03 - Project audit A-03 (not a reviewer comment)

- **Request:** Reconcile inconsistent per-class metrics between the manuscript and canonical release outputs.
- **Affected manuscript scope:** Per-class rhythm/pathology tables, figures and abstract values.
- **Technical status:** `VERIFIED_WITH_LIMITATIONS`
- **Reviewer satisfaction:** `NOT_APPLICABLE_AUDIT`
- **Evidence:** [`outputs/results/primary/canonical_profiles.json`](../../outputs/results/primary/canonical_profiles.json); [`outputs/results/external_dev/rhythm_primary6_metrics.json`](../../outputs/results/external_dev/rhythm_primary6_metrics.json); [`outputs/results/external_dev/rhythm_primary8_metrics.json`](../../outputs/results/external_dev/rhythm_primary8_metrics.json); [`outputs/results/external_dev/pathology_primary4_metrics.json`](../../outputs/results/external_dev/pathology_primary4_metrics.json)
- **Protocol, population and observed result:** The release verifier recomputed canonical values from the record-level prediction tables, including P6 95.19% top-1 and 80.09% macro-F1, P8 90.61% accepted accuracy and 76.14% macro-F1, and P4 80.23% mean panel accuracy and 79.35% macro-F1.
- **What the evidence addresses:** The source-of-truth metrics and denominators are reproduced by the release evidence verifier.
- **What remains unresolved:** The submitted manuscript's final table values and figure labels remain to be reconciled during the later editorial phase.
- **Recoverability:** Canonical released results are complete; no historical inference rerun is implied.
- **Experiment requirement:** None for metric transcription; rerun only if the population or metric definition changes.
- **Future editorial action:** Copy values only from canonical outputs and recheck every table/figure denominator.
- **Scientific risk:** High if P6 is mislabeled P8, panel rows are mislabeled ECGs, or metrics drift from source tables.

### A-04 - Project audit A-04 (not a reviewer comment)

- **Request:** Resolve threshold-vector inconsistencies and verify calibration/test separation.
- **Affected manuscript scope:** Threshold tables, calibration methods and patient-level split claims.
- **Technical status:** `EVIDENCE_CEILING_REACHED`
- **Reviewer satisfaction:** `NOT_APPLICABLE_AUDIT`
- **Evidence:** [`docs/reviewer_closure/SPLIT_CALIBRATION_DISPOSITION.md`](SPLIT_CALIBRATION_DISPOSITION.md); [`outputs/results/internal/pathology_primary4_calibration.json`](../../outputs/results/internal/pathology_primary4_calibration.json); [`outputs/results/revision_20261029/p6_calibration_lineage_summary.json`](../../outputs/results/revision_20261029/p6_calibration_lineage_summary.json); [`docs/reviewer_closure/EVIDENCE_SOURCE_TRIAGE.md`](EVIDENCE_SOURCE_TRIAGE.md); [`docs/reviewer_closure/CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md`](CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md)
- **Protocol, population and observed result:** P4 grid, saved threshold vector, four panel thresholds and reported values were cross-checked. Job 17296's retained V3D calibration log/script records the same final four thresholds as P4 checkpoint metadata, but the calibration output is not hash-linked to the released checkpoint. The P6 six-class vector in job 17315 matches its six-class profile config; the checkpoint metadata's separate eight-class vector is a different profile contract. Patient separation remains uncertified.
- **What the evidence addresses:** Threshold values and the P6 six-class versus P8 eight-class vector distinction are reconciled against surviving job logs, metadata and profile configs.
- **What remains unresolved:** The original calibration patient manifest and full training/checkpoint lineage remain unavailable.
- **Recoverability:** Requires exact job-linked calibration manifest and checkpoint lineage; official dataset folds alone do not establish isolation.
- **Experiment requirement:** A new calibration/test design is required for new models; no new threshold fitting on SPH confirmatory data.
- **Future editorial action:** Report the saved thresholds and distinguish them from the unverifiable historic isolation claim.
- **Scientific risk:** High if calibration observations or threshold selection leaked into reported evaluation.

### A-05 - Project audit A-05 (not a reviewer comment)

- **Request:** Correct the manuscript's shared-backbone description and parameter accounting for rhythm versus pathology.
- **Affected manuscript scope:** Architecture diagram, model description, abstract and parameter table.
- **Technical status:** `VERIFIED_COMPLETE`
- **Reviewer satisfaction:** `NOT_APPLICABLE_AUDIT`
- **Evidence:** [`docs/architecture.md`](../architecture.md); [`outputs/models/heads/global_head_contracts.json`](../../outputs/models/heads/global_head_contracts.json); [`scripts/evaluation/verify_release_evidence.py`](../../scripts/evaluation/verify_release_evidence.py)
- **Protocol, population and observed result:** P6 and P8 share the V3F rhythm backbone; P4 uses a separate V3AG pathology backbone. The two physical backbones and specialist weights have distinct release hashes.
- **What the evidence addresses:** The architecture boundary and parameter inventories are verified from code/contracts and release artifacts.
- **What remains unresolved:** The submitted text/diagram still needs correction in the later manuscript phase.
- **Recoverability:** Technical architecture is recovered; manuscript editing remains.
- **Experiment requirement:** None.
- **Future editorial action:** Show shared rhythm P6/P8 and separate P4 backbone; do not label a single shared encoder across all tasks.
- **Scientific risk:** High if separate models are described as one shared encoder or parameter counts are combined incorrectly.

### A-06 - Project audit A-06 (not a reviewer comment)

- **Request:** Reconcile the claimed Optuna trial history, objective and quarantine with the public training code and promoted checkpoints.
- **Affected manuscript scope:** Optuna appendix/table, training-method claims and checkpoint provenance.
- **Technical status:** `EVIDENCE_CEILING_REACHED`
- **Reviewer satisfaction:** `NOT_APPLICABLE_AUDIT`
- **Evidence:** [`docs/hash-correction-20261028.md`](../hash-correction-20261028.md); [`outputs/results/optuna/v3c_promoted_configuration.json`](../../outputs/results/optuna/v3c_promoted_configuration.json); [`outputs/results/optuna/README.md`](../../outputs/results/optuna/README.md); [https://github.com/Mateo197802/titan-v45-ecg-multihead/pull/4](https://github.com/Mateo197802/titan-v45-ecg-multihead/pull/4)
- **Protocol, population and observed result:** The repository retains nine trial rows and a best-parameter snapshot; the V3C promoted configuration declares 9 completed/12 planned trials. SLURM jobs 13169/13172/13181 are recorded as failed. The original SQLite database, complete history and a verifiable trial-to-published-checkpoint chain were not recovered.
- **What the evidence addresses:** Partial trial traces and the limits of historical Optuna reconstruction are documented in separate PR #4 evidence.
- **What remains unresolved:** Full search history, candidate failures, objective/config linkage and promotion to released weights remain unverified.
- **Recoverability:** Reopen only with the original DB/WAL/SHM or complete authenticated study export plus checkpoint-linked run receipts.
- **Experiment requirement:** No replay can recreate historical trial lineage; a new Optuna study is a new V4.6 experiment, not a repair of V4.5.
- **Future editorial action:** Remove unsupported claims about complete Optuna optimization and quarantine unless linked evidence is supplied.
- **Scientific risk:** High if a partial or unrelated study is represented as the search that produced the released weights.

### A-07 - Project audit A-07 (not a reviewer comment)

- **Request:** Replace or repair the broken Data Availability Statement repository URL and link to a verifiable artifact package.
- **Affected manuscript scope:** Data Availability Statement and repository citation.
- **Technical status:** `VERIFIED_WITH_LIMITATIONS`
- **Reviewer satisfaction:** `NOT_APPLICABLE_AUDIT`
- **Evidence:** [https://github.com/Mateo197802/titan-v45-ecg-multihead/releases/tag/v0.1.0](https://github.com/Mateo197802/titan-v45-ecg-multihead/releases/tag/v0.1.0); [`docs/reviewer_closure/EVIDENCE_COMMITS.md`](EVIDENCE_COMMITS.md); [`release-manifest.json`](../../release-manifest.json)
- **Protocol, population and observed result:** The public repository and immutable v0.1.0 release expose code, aggregate evidence and verified assets; restricted source signals/patient-level outputs are not included in public artifacts.
- **What the evidence addresses:** A working, versioned public evidence destination exists.
- **What remains unresolved:** The submitted manuscript URL remains unedited and the final revised supplement has not been assembled.
- **Recoverability:** The public release is verified; final citation/DOI depends on the authors' chosen release snapshot.
- **Experiment requirement:** None.
- **Future editorial action:** Replace the 404 target with the exact public repository/release and state which inputs remain restricted.
- **Scientific risk:** Moderate if readers cannot locate code or if public access is implied for restricted data.

### A-08 - Project audit A-08 (not a reviewer comment)

- **Request:** Resolve the mismatch between supplementary CSVs announced in the manuscript and the actual ZIP contents.
- **Affected manuscript scope:** Supplement inventory, Data Availability Statement and appendix references.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `NOT_APPLICABLE_AUDIT`
- **Evidence:** [`docs/reviewer_closure/HISTORICAL_EVIDENCE_HANDOFF.md`](HISTORICAL_EVIDENCE_HANDOFF.md); [`outputs/results/README.md`](../../outputs/results/README.md); [`release-manifest.json`](../../release-manifest.json)
- **Protocol, population and observed result:** Existing released aggregates and tables are inventoried, but the final revised supplement has deliberately not been assembled before the technical closure is complete.
- **What the evidence addresses:** The mismatch is catalogued and public artifacts are discoverable.
- **What remains unresolved:** The final ZIP/CSV set and manuscript filenames must be reconciled at submission assembly.
- **Recoverability:** Editorial packaging is recoverable from authorized aggregate outputs; restricted row-level data must remain out of the supplement.
- **Experiment requirement:** None if all announced tables are derived from existing verified aggregates.
- **Future editorial action:** Create a final file inventory and ensure every promised CSV exists, is authorized and is cited accurately.
- **Scientific risk:** Moderate if a missing supplement prevents reproduction or a restricted file is redistributed.

### A-09 - Project audit A-09 (not a reviewer comment)

- **Request:** Correct the bibliography DOI that resolves to a SARS-CoV-2 article rather than the intended ECG reference.
- **Affected manuscript scope:** Reference list and every in-text citation to the affected reference.
- **Technical status:** `MANUSCRIPT_ONLY_PENDING`
- **Reviewer satisfaction:** `NOT_APPLICABLE_AUDIT`
- **Evidence:** [`docs/revision-data-dispositions.md`](../revision-data-dispositions.md); [`docs/reviewer_closure/REVIEWER_48_STATUS.md`](REVIEWER_48_STATUS.md)
- **Protocol, population and observed result:** The DOI mismatch is catalogued as an editorial integrity issue; no manuscript bibliography has been modified during this phase.
- **What the evidence addresses:** The incorrect reference is flagged for replacement, not silently rewritten.
- **What remains unresolved:** The exact replacement reference and its support for the final claim must be independently checked in the final bibliography.
- **Recoverability:** Editorially recoverable by resolving DOI metadata and verifying the cited article.
- **Experiment requirement:** None.
- **Future editorial action:** Replace the DOI only after confirming the intended paper, metadata and claim-to-source fit.
- **Scientific risk:** High citation-integrity risk if a DOI is retained that points to unrelated work.

### A-10 - Project audit A-10 (not a reviewer comment)

- **Request:** Resolve the provenance and redistribution rights of data_test and the mixed archive, while keeping the analysis chain traceable.
- **Affected manuscript scope:** Data provenance, release assets, licenses and redistribution statements.
- **Technical status:** `ACTIVE_RECOVERY_REQUIRED`
- **Reviewer satisfaction:** `NOT_APPLICABLE_AUDIT`
- **Evidence:** [`docs/reviewer_closure/SOURCE_RIGHTS_DISPOSITION.md`](SOURCE_RIGHTS_DISPOSITION.md); [`data/licenses/README.md`](../../data/licenses/README.md); [`docs/external_validation/sph_dataset_audit.md`](../external_validation/sph_dataset_audit.md)
- **Protocol, population and observed result:** Eighty-four selected signals were identified and headers/notices cross-checked. The complete mixed archive provenance and rights are not certified; additional redistribution is on HOLD while the existing release asset remains public.
- **What the evidence addresses:** The release risk is explicitly bounded and no new restricted signal rows were added to the repository.
- **What remains unresolved:** Archive-wide distribution rights, provenance and any source-specific restrictions remain unresolved.
- **Recoverability:** Requires source custodian/license-holder confirmation and an archive-level inventory; filenames and public availability alone do not grant redistribution rights.
- **Experiment requirement:** No model experiment; legal/provenance review is required before any additional file publication.
- **Future editorial action:** Describe the data source and access conditions accurately; publish only permitted aggregate evidence.
- **Scientific risk:** Critical publication and privacy risk if restricted signals or patient-level rows are redistributed without authority.

### A-11 - Project audit A-11 (not a reviewer comment)

- **Request:** Determine whether MC-Dropout/Grad-CAM evidence supports the manuscript's clinical explanation and interpretability claims.
- **Affected manuscript scope:** Interpretability methods, figures and claims of clinical explanation.
- **Technical status:** `NEW_EXPERIMENT_REQUIRED`
- **Reviewer satisfaction:** `NOT_APPLICABLE_AUDIT`
- **Evidence:** [`docs/figure-evidence.md`](../figure-evidence.md); [`outputs/results/gradcam/README.md`](../../outputs/results/gradcam/README.md); [`docs/reviewer_closure/HISTORICAL_EVIDENCE_HANDOFF.md`](HISTORICAL_EVIDENCE_HANDOFF.md)
- **Protocol, population and observed result:** Publicly located Grad-CAM/salience material is synthetic or a code-path smoke test; it is not a model-derived clinical explanation or validation against expert interpretation.
- **What the evidence addresses:** The synthetic nature and limits of available interpretability evidence are identified.
- **What remains unresolved:** No clinical adjudication, faithfulness evaluation or user study validates the submitted interpretability claims.
- **Recoverability:** Historical clinical interpretation evidence is not found in the inspected sources; a new study is required if the claim is retained.
- **Experiment requirement:** No new experiment if unsupported clinical explanation claims are removed; otherwise an authorized and prespecified expert/faithfulness evaluation is needed.
- **Future editorial action:** Label synthetic figures as illustrative or remove them; do not claim clinical explainability from smoke tests.
- **Scientific risk:** High if synthetic visualization or code execution is presented as validated clinical explanation.

### A-12 - Project audit A-12 (not a reviewer comment)

- **Request:** Verify any claimed reader study, clinician review, benefit or human-in-the-loop performance against actual reader records and approvals.
- **Affected manuscript scope:** Methods, Results, Discussion and human-review/quarantine claims.
- **Technical status:** `NEW_EXPERIMENT_REQUIRED`
- **Reviewer satisfaction:** `NOT_APPLICABLE_AUDIT`
- **Evidence:** [`docs/revision-replay-protocol.md`](../revision-replay-protocol.md); [`docs/reviewer_closure/ROLE_SUPERVISION_AND_ROUTING.md`](ROLE_SUPERVISION_AND_ROUTING.md); [`docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md`](ALL_INPUT_FLOW_COVERAGE.md)
- **Protocol, population and observed result:** No reader-study dataset, adjudication protocol, clinician outcomes or measured human-review ledger is established. A quarantine flag or fallback is not evidence that a clinician saw or corrected an ECG.
- **What the evidence addresses:** The absence of reader evidence and the distinction between routing and human action are documented.
- **What remains unresolved:** Any benefit, reader performance or patient outcome claim lacks a verified study.
- **Recoverability:** Cannot be inferred from model outputs; historical records may reopen it only if authentic and approved.
- **Experiment requirement:** No experiment if reader-benefit claims are withdrawn; otherwise a separately approved reader study and appropriate ethics/data governance are required.
- **Future editorial action:** Remove claims of measured clinician review or benefit unless the authors provide verifiable study records.
- **Scientific risk:** Critical if unperformed human review or clinical benefit is represented as observed.
