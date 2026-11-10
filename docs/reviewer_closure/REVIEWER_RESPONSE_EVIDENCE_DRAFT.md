# Reviewer Response Evidence Draft

**NOT FOR SUBMISSION — requires author review and approval.**
**The manuscript has not been edited; the submitted PDF and response letter are unchanged.**

Source: [`docs/reviewer_closure/REVIEWER_48_DETAILED.json`](REVIEWER_48_DETAILED.json) at `01beb7a68077a44560b037dbee9b5deace557b8d`. This document turns the existing technical disposition into provisional evidence language; it does not assert that a proposed manuscript change has already been made or that the reviewer is satisfied.

Each reply below is conditional on authors approving and actually implementing the associated manuscript change. Keep the scientific limitation in the final response even when the proposed editorial action is accepted.

### R1-1 — Reviewer 1, Round 1, first methodological comment

**Current disposition:** `EXPERIMENT_COMPLETED_WITH_LIMITATIONS` / `PARTIALLY_ADDRESSED`.

**Reviewer request:** Clarify that an external-development holdout from public sources used during development is not equivalent to independent external validation; provide source-level training, validation and holdout counts or evaluate a truly independent cohort, and moderate generalizability and deployment claims.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: A real full-source SPH transfer analysis and endpoint-specific results exist. New CEDIA accounting/logs also narrow the P6 validation claim by documenting V3H gate use and likely epoch-selection exposure. The PAC probe has a reproducible, hash-pinned aggregate publication and explicit code-30/31 target semantics, but does not establish an independent cohort, clinical adjudication or clinical validity. This evidence does not establish: The 17314 sweep log and submitted script do not preserve the exact manifest binding; the same epoch-8 metrics and threshold vector appear in the immediately subsequent 17315 V3H gate report, strongly supporting use of that development holdout for selection but not providing a cryptographic same-file proof. Historical backbone/source overlap is not certified, labels are not clinical adjudication, and no truly untouched cohort has been selected. We therefore propose to revise the manuscript as follows, subject to author approval: Describe V3H P6 as selected development/model-selection evidence, distinguish it from the later SPH transfer, and do not call either clinical validation or assert complete independence without the missing lineage. Remove untested deployment claims.

**Required experiment or unresolved evidence:** A new, admissible, patient- and signal-disjoint cohort is required if independent generalization is claimed.

**Approval gate:** Codex reports measured results and limits; authors approve claims; a new study is needed if the broader claim is retained.

### R1-2 — Reviewer 1, Round 1, second methodological comment

**Current disposition:** `EXPERIMENT_COMPLETED_WITH_LIMITATIONS` / `PARTIALLY_ADDRESSED`.

**Reviewer request:** Report the complete clinical workflow, including primary and cascade classes, complete denominators, quarantine proportions, errors inside and outside quarantine, and predictive values under original prevalence; do not present a restricted denominator as end-to-end performance.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The measured all-source SPH profile coverage, empty-set/fallback counts and compatible predictive results are documented separately from selected-cohort replays. This evidence does not establish: The June preselection population, exclusion reasons, complete all-class reference ontology and authentic historical quarantine policy/ledger remain unavailable. The recovered V3H accepted/balanced manifest is selected data, not the parent population. No pre/post quarantine rate can be calculated. We therefore propose to revise the manuscript as follows, subject to author approval: Report selected denominators and measured SPH coverage; do not call either a reconstructed historical all-input workflow.

**Required experiment or unresolved evidence:** A complete all-class workflow with compatible reference labels and an explicit quarantine policy is required to satisfy the original request; SPH cannot retroactively supply the missing historical flow.

**Approval gate:** Codex reports measured results and limits; authors approve claims; a new study is needed if the broader claim is retained.

### R1-3 — Reviewer 1, Round 1, AF-label comment

**Current disposition:** `VERIFIED_WITH_LIMITATIONS` / `PARTIALLY_ADDRESSED`.

**Reviewer request:** Describe how AF reference labels were created and harmonized by source, how multiple or conflicting labels were handled, and restrict language to ECG-level AF rather than incident or first-diagnosed AF without longitudinal evidence.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The archived fields are internally consistent for the selected rows and the available contract supports ECG-record wording. This evidence does not establish: The audit does not establish independent clinical adjudication for every source, onset, first diagnosis, incidence or patient-level longitudinal truth. We therefore propose to revise the manuscript as follows, subject to author approval: State AF on the ECG, describe source-specific reference limitations and remove incident/first-diagnosed terminology unless authors supply longitudinal evidence.

**Required experiment or unresolved evidence:** Longitudinal AF claims require a new study; no such study is needed if the claim is confined to ECG-level statements.

**Approval gate:** Codex prepares precise wording; authors approve scope and interpretation.

### R1-4 — Reviewer 1, Round 1, cryptographic hashes comment

**Current disposition:** `VERIFIED_WITH_LIMITATIONS` / `PARTIALLY_ADDRESSED`.

**Reviewer request:** Replace the empty-file and placeholder values in A10 with checksums for actual archived artifacts and provide an accessible verification route; otherwise remove unsupported cryptographic reproducibility claims.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: Actual model checkpoint identities are verifiable from the public release and separate correction evidence. This evidence does not establish: The original Optuna database and generic prediction file are not located; the corrected artifact list is not a one-to-one substitute for every original A10 row. We therefore propose to revise the manuscript as follows, subject to author approval: Replace A10 with the verified artifact inventory and explicitly remove claims for unavailable artifacts; preserve the submitted PDF unchanged.

**Required experiment or unresolved evidence:** No model experiment is needed for the five checkpoint hashes; do not fabricate hashes for missing files.

**Approval gate:** Codex prepares precise wording; authors approve scope and interpretation.

### R2-general — Reviewer 2, Round 1, general class-scope comment

**Current disposition:** `NEW_EXPERIMENT_REQUIRED` / `NOT_SATISFIED`.

**Reviewer request:** Represent excluded rhythm and pathology classes as Other arrhythmia/Other pathologies, or otherwise report them so excluded classes and NSR are not hidden from realistic performance assessment.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: All-input profile decisions and the limits of declared auxiliary outputs are now visible; missing scores and incompatible labels are not converted to negatives. The separate PAC probe adds a fully reported model comparison for one endpoint only; it does not close the Other/cascade request. This evidence does not establish: No validated Other class, complete ontology, class-level labels for all inputs, or evaluated primary-to-cascade performance is available. We therefore propose to revise the manuscript as follows, subject to author approval: Describe only evaluated primary endpoints and explicitly state that Other/cascade performance is not validated.

**Required experiment or unresolved evidence:** Required if the original all-class performance request is retained; not satisfied by narrowing text alone.

**Approval gate:** Authors/study team approve endpoint, data rights and protocol; Codex can implement and audit the approved workflow.

### R2-1a — Reviewer 2, Round 1, point 1, abstract

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Briefly explain what Primary6 rhythm specialist and Primary4 pathology specialist mean in the abstract and at first use in the main text.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The technical definitions are documented and can be stated without a new experiment. This evidence does not establish: The submitted manuscript has not been revised to define the terms at the requested locations. We therefore propose to revise the manuscript as follows, subject to author approval: Add one-sentence definitions at both locations and retain distinct denominators.

**Required experiment or unresolved evidence:** None; editorial clarification only.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-1b — Reviewer 2, Round 1, point 1, abbreviations

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Define abbreviations at first use throughout the manuscript, tables and figures.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The need is identified but no final manuscript audit has been performed in this phase. This evidence does not establish: First-use consistency in the submitted source remains unchecked against the final revised layout. We therefore propose to revise the manuscript as follows, subject to author approval: Expand each abbreviation on first use and verify captions independently.

**Required experiment or unresolved evidence:** None.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-2a — Reviewer 2, Round 1, point 2, Introduction references

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Add adequate references to the Introduction's general statements and make the study objective clear at the end of the section.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The intended scope can now be bounded by the evidence package, but the bibliography has not been rewritten or fully checked here. This evidence does not establish: Reference adequacy, citation-to-claim fit and the final objective wording remain to be assessed after the author-approved scope is fixed. We therefore propose to revise the manuscript as follows, subject to author approval: Audit each general claim against primary literature and state a narrow descriptive/evaluative objective.

**Required experiment or unresolved evidence:** None for citations; a broader scientific claim would require additional evidence, not just references.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-2b — Reviewer 2, Round 1, point 2, Figures 1 and 2

**Current disposition:** `ACTIVE_RECOVERY_REQUIRED` / `PARTIALLY_ADDRESSED`.

**Reviewer request:** Explain the purpose of Figures 1 and 2 and identify their sources or provenance.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The supplied archive establishes immediate source-package provenance and the purposes stated in its TeX: a proposed modular P6/P4 architecture (Figure 1) and a data-curation/harmonization workflow (Figure 2). This does not independently validate depicted historical operations. This evidence does not establish: Creator/editor identity, any third-party assets and permissions are not established. The authors must confirm Figure 2's cohort/split claims against run-level evidence; the ZIP alone cannot prove execution or patient-level independence. We therefore propose to revise the manuscript as follows, subject to author approval: After author confirmation, attribute or identify the figures as author-created only if supported; narrow Figure 2 to verified operations and use an authorized replacement or remove it if origin/permissions remain unclear.

**Required experiment or unresolved evidence:** None unless a figure makes a new empirical claim.

**Approval gate:** Codex performs only the identified bounded search; CEDIA custodian supplies any inaccessible archive; authors decide disposition if absent.

### R2-2c — Reviewer 2, Round 1, point 2, Table 1 comparator selection

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Justify why Table 1 selects only Life/MDPI studies, replace the unsupported representative/comparator framing, and explain what the table is intended to compare.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The non-equivalence risk is recognized; no replacement systematic or balanced literature table is yet verified. This evidence does not establish: A defensible study-selection rule, broader sources and comparable task definitions are needed if the table remains. We therefore propose to revise the manuscript as follows, subject to author approval: Remove the Life-only selection or define a transparent, reproducible comparator scope and revise the caption.

**Required experiment or unresolved evidence:** No model experiment; any quantitative comparison must use compatible published endpoints and disclose differences.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-2d — Reviewer 2, Round 1, point 2, parameter reporting

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Explain missing architecture parameters, avoid comparisons between non-equivalent tasks, and clarify the table's purpose and direct-comparator terminology.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The TITAN architecture's local parameter counts are documented; this does not fill missing comparator-study parameters. This evidence does not establish: The manuscript table still needs explicit NR labels and task/cohort comparability caveats. We therefore propose to revise the manuscript as follows, subject to author approval: Report verified model counts, mark unreported values NR and avoid implying a direct performance comparison.

**Required experiment or unresolved evidence:** None unless a new benchmark is proposed.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-2e — Reviewer 2, Round 1, point 2, SCP and abbreviations

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Define SCP and every abbreviation used in the text, tables and figures.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The issue is catalogued but no final abbreviation pass is complete. This evidence does not establish: SCP's intended expansion and first-use order must be confirmed by authors from the study context. We therefore propose to revise the manuscript as follows, subject to author approval: Confirm the intended meaning of SCP, define it and run a first-use audit.

**Required experiment or unresolved evidence:** None.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-2f — Reviewer 2, Round 1, point 2, study placement and aim

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Move implementation details of the present study out of the Introduction and state the study aim clearly at the end of the section.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The technical source material is identifiable, but section placement remains unchanged. This evidence does not establish: The authors must decide whether the final study is retrospective audit/transfer or a broader architecture evaluation. We therefore propose to revise the manuscript as follows, subject to author approval: Keep prior-art synthesis in Introduction, move this study's implementation to Methods and add a bounded aim.

**Required experiment or unresolved evidence:** None for moving text; a broader stated aim must be supported by data.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-3a — Reviewer 2, Round 1, point 3, database and split description

**Current disposition:** `EVIDENCE_CEILING_REACHED` / `PARTIALLY_ADDRESSED`.

**Reviewer request:** Describe each database, available and used classes, segment counts, and ECG/patient numbers by training, validation and test split; explain what happened to remaining classes.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: Selected counts, official fold relation, completed-job accounting, checkpoint-declared manifest names and surviving calibration logs are documented with their different evidentiary strength. This evidence does not establish: Historical train/validation/calibration manifests, patient mappings and full per-class source counts are not all linked to released checkpoints; official fold membership and a completed job do not certify historical patient isolation. We therefore propose to revise the manuscript as follows, subject to author approval: Report known selected counts and explicitly mark unrecovered historical counts/isolation as unknown.

**Required experiment or unresolved evidence:** A new split analysis is required for any new model; historical split claims cannot be recreated from selected results.

**Approval gate:** Codex stops unbounded searching and records the ceiling; authors decide claim scope; custodian acts only on a new archive lead.

### R2-3b — Reviewer 2, Round 1, point 3, design versus evaluation

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Clarify whether the study only evaluates specialist networks or also designs them.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The technical package distinguishes design from evaluation stages. This evidence does not establish: The manuscript has not yet stated the exact retrospective scope and what was designed versus evaluated. We therefore propose to revise the manuscript as follows, subject to author approval: State exactly which architecture was developed, which checkpoints were evaluated and which replays are reconstructed.

**Required experiment or unresolved evidence:** None for wording; claims of a new design process require corresponding provenance.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-3c — Reviewer 2, Round 1, point 3, cascade and auxiliary rhythm labels

**Current disposition:** `VERIFIED_WITH_LIMITATIONS` / `PARTIALLY_ADDRESSED`.

**Reviewer request:** Explain how primary, cascade and auxiliary rhythm labels are used in training and evaluation, and do not describe NSR as a low-prevalence arrhythmia.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: Implemented output and fallback roles are described; NSR is a rhythm category, not an arrhythmia class by that fact alone. This evidence does not establish: Checkpoint-linked positive/negative training supports and exact historical class selection remain unavailable for auxiliary outputs. We therefore propose to revise the manuscript as follows, subject to author approval: Separate declared outputs, training supervision, scored predictions and role/routing; correct the NSR description.

**Required experiment or unresolved evidence:** No new experiment needed to state current contract; new supervised class performance requires a valid training/evaluation design.

**Approval gate:** Codex prepares precise wording; authors approve scope and interpretation.

### R2-3d — Reviewer 2, Round 1, point 3, ALMI/ILMI/LAE

**Current disposition:** `EVIDENCE_CEILING_REACHED` / `NOT_SATISFIED`.

**Reviewer request:** Clarify whether ALMI, ILMI and LAE were trained and evaluated or merely logged as auxiliary pathology labels.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: It is verified that outputs are emitted in the reconstructed path, not that the historical checkpoint was trained on those labels. This evidence does not establish: Historical supervision supports, loss masks, selection policy and evaluation metrics for these outputs are not certified. We therefore propose to revise the manuscript as follows, subject to author approval: Describe them as unvalidated auxiliary outputs or remove claims of trained/evaluated pathology classes.

**Required experiment or unresolved evidence:** New training and evaluation are required if performance for these classes is claimed.

**Approval gate:** Codex stops unbounded searching and records the ceiling; authors decide claim scope; custodian acts only on a new archive lead.

### R2-3e — Reviewer 2, Round 1, point 3, Table 5 Role

**Current disposition:** `VERIFIED_WITH_LIMITATIONS` / `PARTIALLY_ADDRESSED`.

**Reviewer request:** Define what Role means in Table 5 and how role assignments are determined.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: Code roles, predicted outputs and observed transitions are explicitly distinguished. This evidence does not establish: Historical assignment and role-transition counts for the original all-input pathway are not recoverable from the selected panels. We therefore propose to revise the manuscript as follows, subject to author approval: Define Role as a declared data/model contract and avoid interpreting it as actual human review.

**Required experiment or unresolved evidence:** A new measured operational workflow is required if human review or route effectiveness is retained as a claim.

**Approval gate:** Codex prepares precise wording; authors approve scope and interpretation.

### R2-3f — Reviewer 2, Round 1, point 3, Figures 5 and 6

**Current disposition:** `EVIDENCE_CEILING_REACHED` / `PARTIALLY_ADDRESSED`.

**Reviewer request:** Name and define the ten morphology features, explain asymmetric arrows and every block-diagram connection, and correct or remove unsupported flow arrows.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The candidate feature contract and its provenance boundary are documented, and strict score equivalence is explicitly recorded as failed. This evidence does not establish: Exact historical feature implementation, loader identity and the figure-to-runtime arrow semantics are not fully verified. We therefore propose to revise the manuscript as follows, subject to author approval: List each feature and unit, redraw arrows to match verified dataflow, and identify reconstructed code as such.

**Required experiment or unresolved evidence:** No threshold retuning; a future replay may test equivalence only if the exact loader and inputs are recovered.

**Approval gate:** Codex stops unbounded searching and records the ceiling; authors decide claim scope; custodian acts only on a new archive lead.

### R2-3g — Reviewer 2, Round 1, point 3, Brier score statements

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Move numerical Brier scores from Methods to Results if they are observed results, and distinguish the metric definition from the measured values.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The evidence distinguishes definitions from observed results; the submitted manuscript has not been edited. This evidence does not establish: All original numerical claims in Methods must be traced to their exact cohort and moved or removed. We therefore propose to revise the manuscript as follows, subject to author approval: Keep the Brier definition in Methods and report cohort-specific values only in Results.

**Required experiment or unresolved evidence:** None if the original results are accurately sourced; no unsupported value should be retained.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-3h — Reviewer 2, Round 1, point 3, accuracy metrics

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Provide equations and explanations for all accuracy metrics and clarify whether rhythm and pathology metrics differ and why.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The distinctions are documented and testable, but equations have not been inserted into the manuscript. This evidence does not establish: The final manuscript still needs equations matched to each reported unit, averaging scheme, denominator and missing-label rule. We therefore propose to revise the manuscript as follows, subject to author approval: Define accuracy, macro-F1, top-1, AUROC, AP and calibration with their exact units and averaging rules.

**Required experiment or unresolved evidence:** None for equations; any value must be recomputed if its denominator or metric definition changes.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-4a — Reviewer 2, Round 1, point 4, Table 8 terminology

**Current disposition:** `VERIFIED_WITH_LIMITATIONS` / `PARTIALLY_ADDRESSED`.

**Reviewer request:** Define the external-development evidence package, say whether it is the test dataset, use consistent terminology and describe it in the database or Methods section.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The evidence packages and populations are now named and numerically distinguished in technical documentation. This evidence does not establish: Complete historical usage and selection lineage of every development package remain unknown; V3H selection exposure is now documented, but the exact 17314 manifest and complete backbone lineage remain unavailable. The manuscript terminology has not been harmonized. We therefore propose to revise the manuscript as follows, subject to author approval: Define each package as a concrete artifact/population and use one term consistently.

**Required experiment or unresolved evidence:** None for definition; new evidence is needed for any independent-test interpretation.

**Approval gate:** Codex prepares precise wording; authors approve scope and interpretation.

### R2-4b — Reviewer 2, Round 1, point 4, figure cross-reference

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Correct the paragraph after Table 8 to refer to Figure 8 rather than Figure 10.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The defect is identified, but the submitted manuscript remains unchanged. This evidence does not establish: Final figure numbering may change during layout and must be checked after the final figure assembly. We therefore propose to revise the manuscript as follows, subject to author approval: Correct the reference and recheck all figure/table references after composition.

**Required experiment or unresolved evidence:** None.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-4c — Reviewer 2, Round 1, point 4, F1 interpretation

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Do not call F1 values around 62.58% and 65.64% reliable performance; revise the strength of the interpretation.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: Canonical values and the unfavorable transfer result are available for a bounded interpretation. This evidence does not establish: The original adjective remains in the submitted manuscript and requires author-approved replacement. We therefore propose to revise the manuscript as follows, subject to author approval: Describe exact F1 values and cohort; avoid 'reliable' without a prespecified threshold.

**Required experiment or unresolved evidence:** None to moderate the wording; any claim of reliability requires a defined operational criterion and validation.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-4d — Reviewer 2, Round 1, point 4, Figure 8 caption and uncertainty

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Correct Figure 8's caption to acknowledge precision, recall and F1, and show or accurately describe the absence of 95% confidence bounds.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The evidence package defines available uncertainty intervals; the submitted figure has not been replaced or recaptioned. This evidence does not establish: It is not established that every plotted bar has a matching interval in the current submitted figure. We therefore propose to revise the manuscript as follows, subject to author approval: Rebuild from the exact source table, label all three measures and either show valid bounds or state they are not shown.

**Required experiment or unresolved evidence:** No new ECG experiment; interval calculation is needed only if the final figure reports confidence intervals not already available.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-4e — Reviewer 2, Round 1, point 4, threshold non-crossing

**Current disposition:** `EXPERIMENT_COMPLETED_WITH_LIMITATIONS` / `PARTIALLY_ADDRESSED`.

**Reviewer request:** Explain what happens when no class score crosses its threshold and how such cases are counted.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: No-crossing behavior and complete-source counts are now measured for the frozen profiles. This evidence does not establish: P6/P4 empty sets and P8 fallback do not establish a quarantine rate, an Other class, or human review; historical all-input June routes remain unknown. We therefore propose to revise the manuscript as follows, subject to author approval: Define thresholding and fallback separately, report denominators and do not relabel fallback as quarantine.

**Required experiment or unresolved evidence:** No new experiment to state these frozen rules; a quarantine effectiveness claim requires a separate defined evaluation.

**Approval gate:** Codex reports measured results and limits; authors approve claims; a new study is needed if the broader claim is retained.

### R2-4f — Reviewer 2, Round 1, point 4, Figure 9 units

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Use a consistent numeric or percentage presentation across Figures 7 and 9.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The required edit is identified, but the submitted figures remain unchanged. This evidence does not establish: The final unit convention must be applied after the final figure selection. We therefore propose to revise the manuscript as follows, subject to author approval: Choose counts or percentages consistently and verify axis labels, color scales and captions.

**Required experiment or unresolved evidence:** None.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-4g — Reviewer 2, Round 1, point 4, duplicate figures

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Resolve the reported duplication between Figures 8 and 10.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The figure-level issue is recorded; a final accepted figure set has not been assembled. This evidence does not establish: Figure identity, captions and cross-references must be checked together after editorial revisions. We therefore propose to revise the manuscript as follows, subject to author approval: Retain one authoritative figure or document the distinct information each figure conveys.

**Required experiment or unresolved evidence:** None unless the duplicate figure contains unique, unverified data.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-4h — Reviewer 2, Round 1, point 4, ROC/PR evaluation unit

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Define what 'evaluation tracings' means in the ROC and precision-recall description and use the correct ECG-level unit.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The technical evidence identifies the relevant record-level units; the manuscript's ambiguous phrase remains unchanged. This evidence does not establish: The text must identify the exact cohort, endpoint and unit for each plotted curve. We therefore propose to revise the manuscript as follows, subject to author approval: Replace 'evaluation tracings' with the precise ECG-record denominator and name each target.

**Required experiment or unresolved evidence:** None if the source arrays and endpoint remain unchanged.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-4i — Reviewer 2, Round 1, point 4, AUROC interpretation

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Revise the characterization of 87.46% pathology macro-AUROC as high.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: Canonical and transfer values are available for a qualified description. This evidence does not establish: The adjective and interpretation in the submitted manuscript have not been revised. We therefore propose to revise the manuscript as follows, subject to author approval: Report the value without 'high' or explain its context, metric uncertainty and class-specific limitations.

**Required experiment or unresolved evidence:** None to revise the adjective; broader clinical meaning requires a prespecified benchmark.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-4j — Reviewer 2, Round 1, point 4, Figure 13 calibration

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Use consistent observed-frequency/empirical-accuracy terminology, define how it is estimated and make the ten confidence-bin axes match their stated range.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: A reproducible calibration definition and later source-specific ECE evidence exist. This evidence does not establish: The submitted calibration plot and its data source must be matched to the final binning implementation and labels. We therefore propose to revise the manuscript as follows, subject to author approval: Define bin occupancy and mean confidence versus observed statement frequency; standardize labels/ticks and document empty bins.

**Required experiment or unresolved evidence:** No new inference if the same saved probabilities and fixed bins are used; otherwise recompute from the correct source.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-4k — Reviewer 2, Round 1, point 4, quarantine rates

**Current disposition:** `EVIDENCE_CEILING_REACHED` / `NOT_SATISFIED`.

**Reviewer request:** Define the quarantine rate and pre/post-quarantine accuracy and explain how these values are estimated.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The invalid inference from fallback to quarantine is explicitly rejected; routing counts are documented with their actual semantics. This evidence does not establish: No historic pre/post ledger, quarantine denominator, policy version or uncertainty inputs are available; rates and pre/post accuracy cannot be reconstructed. We therefore propose to revise the manuscript as follows, subject to author approval: Do not report an assumed quarantine percentage; mark historical rate unavailable or remove the claim.

**Required experiment or unresolved evidence:** Required to support any quarantine effectiveness claim; otherwise the claim and rate must be removed.

**Approval gate:** Codex stops unbounded searching and records the ceiling; authors decide claim scope; custodian acts only on a new archive lead.

### R2-4l — Reviewer 2, Round 1, point 4, rhythm top-1

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Define rhythm top-1 accuracy and explain exactly how it is calculated.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The calculation and selected denominators can be traced in code and canonical results. This evidence does not establish: The submitted manuscript must define argmax, denominator, treatment of fallback and selected-cohort scope. We therefore propose to revise the manuscript as follows, subject to author approval: State the per-record argmax rule and report P6/P8 separately, including fallback treatment.

**Required experiment or unresolved evidence:** None if definitions and data remain unchanged.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-4m — Reviewer 2, Round 1, point 4, Figures 14 and 15 readability

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Improve unreadable axes and values in Figures 14 and 15 and check all figures.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: A later layout/render check is explicitly reserved; no claim is made that the figures are currently fixed. This evidence does not establish: Font sizes, axis labels, line weights, contrast and page-scale legibility remain unverified in the final layout. We therefore propose to revise the manuscript as follows, subject to author approval: Regenerate, render the final PDF and inspect every page at realistic size; verify captions and all figure callouts.

**Required experiment or unresolved evidence:** None if plots use verified aggregates; new evidence is needed only if the plot content changes empirically.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

### R2-5 — Reviewer 2, Round 1, point 5, PVC unit of analysis

**Current disposition:** `VERIFIED_WITH_LIMITATIONS` / `PARTIALLY_ADDRESSED`.

**Reviewer request:** Acknowledge that PVC is often analyzed at heartbeat level and avoid treating 10-second ECG-level classification as beat-level detection.

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The available result is correctly bounded to record-level ECG statement agreement. This evidence does not establish: Beat-level detection, temporal matching, episode counts and clinical adjudication are not measured. We therefore propose to revise the manuscript as follows, subject to author approval: Explicitly state the ECG-level unit and remove any beat-level performance implication.

**Required experiment or unresolved evidence:** Required if beat detection or localization is claimed; not required for a strictly record-level statement study.

**Approval gate:** Codex prepares precise wording; authors approve scope and interpretation.

### R2-6 — Reviewer 2, Round 1, point 6, distortion and citation

**Current disposition:** `MANUSCRIPT_ONLY_PENDING` / `EDITORIAL_ACTION_ONLY`.

**Reviewer request:** Clarify whether the claim that the framework eliminates diagnostic distortion refers to this study and justify or correct citation [4].

**Evidence-only candidate wording, conditional on author approval:**

> We appreciate this comment. The evidence available for this point is: The measured evidence constrains the claim and identifies the need to verify the reference. This evidence does not establish: The submitted sentence and citation have not been corrected; citation [4] must be checked against the final claim. We therefore propose to revise the manuscript as follows, subject to author approval: Replace the absolute claim with a bounded observation or remove it, and verify the cited source.

**Required experiment or unresolved evidence:** None if the absolute claim is removed; required for any retained claim that the architecture eliminates distortion.

**Approval gate:** Codex prepares proposed edits; authors review and approve before any manuscript change or submission.

## Submission gate

Before any response is sent, authors must verify the cited evidence, approve the revised manuscript text and response, confirm that every proposed action was actually implemented, and decide how to report requests that remain unsatisfied. This draft is not a substitute for the editor's decision or the authors' approval.
