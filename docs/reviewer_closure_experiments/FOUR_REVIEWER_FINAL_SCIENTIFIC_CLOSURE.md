# TITAN V4.5: scientific closure of four reviewer comments

**Final evidence assessment:** zero unqualified satisfactions, three
scientifically satisfied with limitations (R2-general, R2-3f and R2-4k),
and one partial (R1-2). This closes the bounded evidence assessment, not
the untested end-to-end clinical claim or the editorial process. The
[native CEDIA receipt](../../outputs/results/reviewer_closure_experiments/native_closure_verification.json)
verifies 11 aggregate/receipt artifacts and five authoritative successful
jobs. It also preserves two pre-result failures and one superseded
evaluator. No changes are applied to the submitted article.

The immutable starting point is November commit
`bf081e9c2fd62704821f56d614399d7d0eb6e656`. This work adds evidence
without changing the 40-subrequirement rubric or scores. It distinguishes
original classifiers, original auxiliary scores, new fitted heads and a
new abstention wrapper.

## R1-2: complete workflow

The reviewer asked for performance on the whole eligible clinical
population, including normal ECGs, all routes and cascade classes,
quarantine, missed positives and predictive values at the original
prevalences. They explicitly warned against interpreting the selected
95.19% accuracy and 80.09% macro-F1 as end-to-end estimates.

1. **Experiment:** Original P6/P8/P4 were scored on all 25,770 SPH ECGs
   and all 200 LUDB ECGs. Original P4 also scored all 549 PTB Diagnostic
   ECGs, with supported infarct-territory/healthy-control comparisons.
   New executed joint abstention decisions are available; no actual
   downstream clinical cascade was run.
2. **Literal request:** Partly addressed. Full-source inference, narrower
   reference-based contrasts, and route dispositions are not a full
   reference-supported clinical workflow.
3. **Preserve:** Original selected-panel results and their exact denominators.
4. **Restrict:** No extrapolation to all diagnostic classes, clinical
   prevalence, historical quarantine or human referral.
5. **Essential evidence:** Actual cascade with timestamped decisions plus
   an appropriate population with independently adjudicated references.
   Recovering the June parent denominator is a distinct provenance question.
6. **Future manuscript:** The bounded denominators, matched restriction
   effects and executed abstention characterization are usable, not a
   new unrestricted diagnostic accuracy.

See [full workflow evidence](FULL_WORKFLOW_VALIDATION.md).

## R2-general: Other and auxiliary classes

The reviewer asked what excluded/auxiliary classes actually do and requested
individual treatment of NSR, PAC, Flutter, Paced, LBBB, 2AVB, 3AVB, LQTS,
ALMI, ILMI and LAE. NSR remains a normal rhythm endpoint.

1. **Experiment:** Asset supervision traced; bounded new Other and
   individual heads already fit and evaluated on held development subsets.
   Frozen transport, source reference audits and the 33747 cached readout
   supplement those experiments. Paced passed the held-support rule;
   V3AG 2AVB and 3AVB did not and remain pooled rank-only in that test.
2. **Literal request:** The class roles, explicit group membership and all
   eleven scientific dispositions are answerable. A comprehensive, unbiased
   Other classifier or deployed cascade has not been demonstrated.
3. **Preserve:** Native specialist scope and separately dated experimental
   mapped-reference results.
4. **Restrict:** Do not attribute post-study heads to V3F/V3AG, combine LAO
   and LAE into isolated LAE, substitute prolonged QT for LQTS or equate
   score presence with calibrated classification.
5. **Essential evidence:** None to report the stated class dispositions,
   including explicit exclusion of congenital LQTS and no clinical LAE
   estimate. A broader diagnostic claim still needs direct adjudication
   for those diagnoses, sufficient held support for AV block operating
   points, and representative all-class evaluation of any composed system.
6. **Future manuscript:** Class-by-class dispositions and bounded mapped
   results are usable. They are not a clinical full-scope Other result.

See [Other class validation](OTHER_CLASS_VALIDATION.md).

## R2-3f: morphology and real connections

The reviewer asked for all ten calculations, why the morphology arrow
appears for pathology but not rhythm, and what arrows in Figures 5 and 6
actually represent.

1. **Experiment:** The candidate formula and load audit is paired with
   instrumented native execution on 200 ECGs and the prior matched
   head-only comparison, independently rederived by 33704. P8's
   exploratory effect is +0.01457 macro-F1; Holm-adjusted p = 0.1356
   in the separate post hoc arm-swap test.
2. **Literal request:** The candidate formulas and actual data flow in the
   executed reconstruction can be explained, including global versus
   specialist connections. Historical identity is a separate claim.
3. **Preserve:** The existence of ten proxies in the verified reconstruction
   and the measured branch-specific matched-head result.
4. **Restrict:** No clinically validated intervals, universal morphology
   benefit, original June loader authentication or exact archived replay.
5. **Essential evidence:** None to describe these measured connections.
   Exact historical equivalence would need the original loader and run
   configuration (or provenance-equivalent evidence), not a changed
   tolerance or parameter selection against archived predictions.
6. **Future manuscript:** The verified contract supports later explanation
   and correction of diagram semantics; no figure is edited here.

See [morphology evidence](MORPHOLOGY_REPRODUCIBILITY_AND_ABLATION.md).

## R2-4k: definition and measurement of quarantine

The reviewer asked how Quarantine Rate and the pre/post accuracy quantities
were calculated. The source literally repeats “Pre-Quarantine Accuracy.”

1. **Experiment:** New joint P8/P4 abstention was actually executed on SPH
   and LUDB, with calibration isolation and fixed-cutoff transport audited
   separately from historical model exposure.
2. **Literal request:** The methodology can give explicit formulas and state
   that the original measures are not supportable. New measurements are
   separately dated and must not be substituted as historical values.
3. **Preserve:** The distinction between a native classifier output and a
   separately applied policy.
4. **Withdraw:** `WITHDRAW_HISTORICAL_CLAIM`; a threshold-empty set and
   fallback do not establish historical clinical quarantine or a 0% rate.
5. **Essential evidence:** None to withdraw and explain the unsupported
   claim. Any claim of effective clinical quarantine would require a real
   downstream pathway and reference follow-up; historical proof would
   require the original policy and per-ECG ledger.
6. **Future manuscript:** The withdrawal and bounded retrospective results
   are usable. No prospective or clinical validation is implied.

See [selective prediction validation](SELECTIVE_PREDICTION_VALIDATION.md).

## Scope and traceability

[Literal-request protocol](PROTOCOL_FREEZE.md) |
[execution and verification register](CLOSURE_EXECUTION_REGISTER.md) |
[endpoint and route tables](VERIFIED_ENDPOINT_AND_ROUTE_TABLES.md) |
[15-comment / 40-subrequirement crosswalk](REVIEWER_EVIDENCE_GAP_RESOLUTION.md).
All individual waveforms, patient or signal linkage, scored ledgers and
experimental fits remain in CEDIA. The manuscript, figures, abstract,
conclusions, letter, existing PRs and historical weights remain unchanged.

## Reproduce the documentary delivery

From the scientific branch, verify the CEDIA export and documentary ZIP
without acquiring any clinical records:

```sh
python scripts/evaluation/verify_reviewer_scientific_closure.py --public-dir outputs/results/reviewer_closure_experiments --native-receipt outputs/results/reviewer_closure_experiments/native_closure_verification.json
python scripts/evaluation/build_reviewer_scientific_closure_zip.py verify outputs/results/reviewer_closure_experiments/TITAN_V45_FOUR_REVIEWER_SCIENTIFIC_CLOSURE.zip
```

The ZIP uses an explicit member allowlist, hashes native aggregates and
reused November evidence, and verifies the generated tables against
their sources. The full implementation and historical register are linked
from this branch. Native record-level replay is restricted to CEDIA.
