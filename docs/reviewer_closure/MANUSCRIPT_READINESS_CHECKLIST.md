# Manuscript readiness checklist

This checklist is for the later editorial phase. It is not permission to edit
the submitted manuscript now. The manuscript and response letter remain
unchanged until technical closure is reviewed and the authors approve the
scope.

## Required author decisions

- [ ] Confirm the revised article scope and title: selected V4.5 evidence plus
  bounded SPH transfer, without claiming full historical independence or
  clinical validation.
- [ ] Decide which original claims to withdraw if the missing historical
  population, auxiliary supervision, Optuna database or quarantine ledger
  cannot be recovered.
- [ ] Confirm that AF language is limited to ECG-record statements and PVC
  language to record-level statements, unless longitudinal/beat-level evidence
  is supplied.
- [ ] Approve how the 25,770-record SPH transfer, incompatible endpoints and
  low P4/P8 metrics are described; do not treat lack of a code as disease
  absence.
- [ ] Confirm figure sources/licensing for submitted Figures 1 and 2, the
  intended meaning of SCP, the replacement DOI for A-09 and the final
  source-comparator selection.
- [ ] Confirm the mixed-archive rights disposition with the relevant
  data/license holders before publishing additional files.
- [ ] Corresponding author approves the final response, authorship statements,
  declarations and journal submission; Codex cannot make this approval.

## Text and claims to reconcile

- [ ] Define P6/P8/P4 and every abbreviation at first use; distinguish
  specialist, output contract, training supervision, saved prediction and
  reconstructed replay.
- [ ] State exact cohort units: P6 1,643 selected ECG; P8 2,193 selected ECG
  including P6; P4 962 panel rows/733 ECG/676 linked patients; SPH 25,770
  ECG/24,666 patients. Do not sum nested P6/P8 or panel observations as
  independent ECG.
- [ ] Keep historical selected-development metrics separate from SPH transfer
  metrics. Describe SPH as transfer against ECG statements, not as fully
  independent clinical validation.
- [ ] Report the P4 replay residual and the fixed failed `1e-5` probability
  equivalence criterion if reproducibility is discussed; decision agreement
  alone is not strict score equivalence.
- [ ] Describe no-threshold behavior accurately: P6/P4 can return empty sets;
  P8 uses top-1 fallback. Quarantine is `not_assessed`, not zero, and no human
  review is evidenced.
- [ ] Remove or qualify claims of validated `Other`, auxiliary-class training,
  quarantine benefit, incident AF, beat-level PVC, clinical Grad-CAM, reader
  benefit and complete Optuna history unless the matrix's missing evidence is
  supplied.
- [ ] Correct the figure cross-reference, duplicated figure content, captions,
  displayed metric names, calibration terminology, axes, units and readability.
- [ ] Rework the introduction and comparator table using a transparent
  literature-selection rule, accurate citations and non-equivalent-task
  caveats.
- [ ] Replace A10 with only verified artifacts and clearly identify artifacts
  not recovered. Keep the originally submitted PDF intact as the record of
  what was submitted.

## Tables, figures and supplements

- [ ] Build every table and figure from the exact linked aggregate used in the
  text; verify denominators, class order, units, confidence intervals and
  rounding.
- [ ] Render the final PDF and inspect every page at readable scale; check all
  axes, labels, legends, page breaks, captions and cross-references.
- [ ] Assemble the final supplement and compare every announced filename with
  the actual ZIP contents; exclude restricted signals, patient IDs and
  unapproved mixed archive material.
- [ ] Run the release-evidence verifier, matrix tests, full test suite, Ruff and
  all repository CI checks after final data/code changes.
- [ ] Freeze the final manuscript, response letter, repository commit, release
  manifest and supplement hashes together before submission.

## Submission gate

- [ ] Authors have reviewed and approved each reviewer response and all
  remaining limitations.
- [ ] Every claim in the final PDF maps to a measured result or is explicitly
  labeled as limitation/future work.
- [ ] The editor's actual decision and journal instructions are checked at the
  time of submission; silence or a green CI is not editorial approval.
- [ ] If independent external validation, a clinical reader study or a
  complete historical workflow is not performed, those requests remain
  scientifically unsatisfied even if claims are narrowed.
