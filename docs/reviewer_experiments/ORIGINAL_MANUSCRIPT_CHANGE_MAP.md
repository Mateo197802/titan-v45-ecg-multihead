# Proposed changes to the submitted manuscript

**For author approval. Not applied.** Anchors refer to
`mdpi_Articulo/manuscrito.tex` in the retained submission `life-4620846.zip`,
source SHA-256 `cd1a31ccfaf882cbffa6749bb9795d0e54531f810f563f6423c3006c0d0717b6`.
Line numbers are source anchors, not journal pagination. This map is limited
to the four reviewer comments; it does not rewrite the article or recalculate
the 40-item rubric. All experimental results below are explicitly November
post-study analyses. The evidence and scope limits are in
[November findings](NOVEMBER_FINDINGS.md).

## R1-2: Denominator and selection

- **Original:** Materials and Methods, Study Design and Evidence Boundary,
  lines 144-148; Results, Overall Specialist Performance, lines 381-393
  (`tab:overall`); Discussion line 527; Abstract line 44. P6 top-1 and P4
  binary-panel estimates remain valid as selected development results. Keep
  their values and units; use 962 panel observations from 733 ECGs for P4.
  Remove the inference that selection was eliminated, or that those metrics
  describe a clinical workflow or an untouched test. Do not replace P6 top-1
  accuracy with statement-level macro binary accuracy.
- **Add to Methods (33355, 33357, 33399):** "In a separate November 2026
  retrospective analysis, the unchanged P6, P8 and P4 artifacts scored every
  metadata ECG from SPH V1. No reference labels were used to select inputs or
  produce decisions. We compared the complete cohort with nested subsets
  containing at least one mapped statement of the corresponding profile.
  Endpoints were scored against compatible source statements, not clinically
  adjudicated diagnoses. Absence of a compatible statement denotes a negative
  for statement prediction, not confirmed absence of disease."
- **Add to Results (33357, 33399):** "All 25,770 ECGs from 24,666 source patient
  identifiers were scored. On compatible endpoints, macro-F1 on the full
  cohort was 0.7083 for P6, 0.6622 for P8 and 0.0388 for P4, compared with
  0.9057, 0.8553 and 0.7278 on the respective nested subsets (5,523, 5,925
  and 415 ECGs). The restricted and full-cohort analyses used identical
  scores. We report classwise predictive values, confusion counts and
  patient-component intervals separately from the selected original results."
- **Add to Discussion (33410):** "SPH did not provide compatible references
  for NSR, 1AVB or ISC_ under the primary mapping. An authorized PTB-XL
  fold 1-9 development cache supplied complementary 1AVB and ISC_ statements
  (6,205 of 19,601 metadata ECGs scored). These known-reference subsets do
  not replace the SPH cohort or establish independent clinical performance."
  Cite the per-class tables, not just a single mean. No June parent cohort
  or full clinical reference standard was recovered.

## R2-general: Class roles and Other

- **Original:** Study Design line 146, Clinical Rationale lines 165-169,
  `tab:contracts` lines 244-256 and Figure 6 `fig:fig03_cascade_contract`
  lines 269-270; check parallel descriptions in the Abstract, comparison
  tables and Conclusions. Keep P6/P8/P4 reporting classes and the named
  global outputs. Relabel "Cascade" as "Outside the primary reported profile
  (proposed secondary handling, not evaluated as an executed route)".
  Show the groups side by side, not as arrows between predictions. NSR is
  normal rhythm and belongs to P8, not to an arrhythmia residual class.
- **Replace routing language (released head audit):** "Class roles specify
  which outputs were scored for the reported profile, not a dispatch rule.
  The archived V3F fine-tuning loss selected the P8 rhythm labels; the
  separate V3AG backbone records a different rhythm subset that includes
  Flutter and Paced. The two recovered stages document Pathology4 targets.
  An auxiliary output does not establish its supervision in earlier
  training, calibration or clinical use."
- **Add November Results (33369, 33390, 33396, 33410):** "New development-only
  heads for mapped rhythm Other achieved F1 0.647 (P6 subset, 141 positives
  among 2,895 known ECGs) and 0.625 (P8 subset, 43 among 2,797), versus 0.092
  and 0.030 for calibrated auxiliary-score comparators. A new PTB-XL
  ALMI/ILMI/LAO-or-LAE union head achieved F1 0.939 on 153 known observations
  out of 390 held ECGs. These are new bounded experiments, not performance
  of the released specialists. Unknown and discordant references are listed
  in full source flow, not recoded as negatives."
- **Limit:** Do not claim all classes are covered. Paced and LQTS lack
  compatible SPH mappings; the individual 3AVB analysis lacked training or
  calibration support. LAO/LAE is a composite. The observed ranking of
  Flutter and LAE by released auxiliary outputs is not a calibrated
  classifier. Comprehensive, independently validated Other remains open.

## R2-3f: Morphology and arrows

- **Original:** Architecture and Specialist Branches, lines 199-270,
  Figure 5 `fig:fig03_internal_architecture`, Figure 6
  `fig:fig03_cascade_contract`. Keep the CNN/Transformer explanation and
  separate model packages. Show waveform and separate lead mask at each
  backbone call and ten morphology inputs into both backbone calls and
  corresponding specialist feature compositions. Depict the event
  descriptors separately on the rhythm side. Use arrows only for tensor
  flow; replace Figure 6 arrows with headings or braces for class membership.
  Do not imply one shared weight file or a clinical referral.
- **Add Methods (pinned source and contract):** "In the reconstructed
  implementation used for the November evaluation, the extractor summarizes
  peak timing, spectral power and inter-lead relationships as ten normalized
  waveform descriptors. Table [morphology contract] gives formulas,
  units, scaling, clipping and nonfinite-value handling. The width and P-to-R
  estimates are heuristic proxies, not clinically validated intervals.
  Morphology is passed to both rhythm and pathology model calls."
- **Add Results (33469-33473, 33596):** "Repeat November ledgers were
  byte-identical. Comparisons against the retained historical predictions
  did not meet the 1e-5 score tolerance: 836/962 P4 scores exceeded it
  despite unchanged decisions, and one of 1,643 P6 top-1 assignments
  changed. Zeroing the morphology vector at fixed weights changed
  decisions in both branches. In a separate matched frozen-backbone head
  retraining comparison, P8 macro-F1 was 0.7412 versus 0.7266 with and
  without morphology (paired delta +0.0146, 95% CI +0.0016 to +0.0276).
  P6 and P4 paired intervals included zero."
- **Limit:** Use the [formula table](MORPHOLOGY_INPUT_CONTRACT.md), not
  a claim about exact historical imports. Label the new estimates as
  frozen-backbone head comparisons. Chapman uses record-as-patient grouping;
  PTB-XL uses official patient folds with fold 10 excluded from the new
  training and evaluation. These are not clinical or external confirmation.

## R2-4k: Quarantine and selective prediction

- **Original:** Uncertainty and Quarantine Logic lines 322-338;
  Discrimination, Calibration, and Uncertainty lines 489-505
  (`tab:uncertainty_quarantine`); source-stratified figure and text lines
  520-523; Conclusions lines 614-616; `tab:app_quarantine_transitions`
  lines 765-779 and the `quarantine_flag` field at line 821. Check Abstract
  and title for the same claim. Keep independently verified historical
  classification results and their error graphic. Label the figure as a
  bar chart of frequent P6 reference-to-prediction errors, not a Sankey of
  quarantine intercepts.
- **Historical correction for approval:** "Operational quarantine and
  clinician overread were not assessed in the original study. A missing
  threshold-positive class or top-1 fallback was not an abstention. The
  available artifacts do not support a historical quarantine rate or
  pre/post-quarantine accuracy." Mark the unsupported cells as not
  assessed or withdraw them with explicit author approval. Do not present
  4.87%, 6.13%, 97.44%, 84.16%, the Plan AE 9.976%, or 0% as historical
  operational estimates. Keep baseline performance in its original
  specialist table; do not repurpose archival errors as referrals.
- **Add November Methods (33362, 33414):** "Per profile, confidence was the
  minimum absolute distance of its scores from the corresponding released
  class thresholds. A cutoff targeting 90% scored coverage was chosen
  without references on 12,901 calibration ECGs and frozen before the
  12,869-ECG held partition. The joint P8/P4 policy emitted both decisions
  only if both profile cutoffs were met. Abstentions and technical
  non-scoring were separate. No second-stage inference or clinician review
  occurred. Risk was mean mapped binary endpoint error among accepted
  records; pre-policy metrics used all scored held ECGs and post-policy
  metrics used accepted ECGs only."
- **Add November Results (33414):** "The joint policy abstained on
  2,478/12,869 ECGs (19.26%, 95% CI 18.55-19.89%), with 80.74% coverage.
  Mapped macro-F1 was 0.4555 before selection and 0.4791 among accepted
  ECGs; mean binary endpoint accuracy was 0.9047 and 0.9100 on these
  different denominators. Of 347 AFIB statement-positive ECGs, 274 had a
  correct emitted prediction, 10 an emitted false-negative prediction,
  and 63 no prediction because of abstention. The latter are not
  corrected cases. The result is retrospective development, not a
  historical or independently validated safety estimate."

**Boundary:** This map proposes minimal corrections and additions for author
review. It does not approve removal of manuscript content, replace figures,
attest to figure rights or declare any journal comment closed.
