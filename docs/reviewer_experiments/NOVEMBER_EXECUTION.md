# November four-reviewer experiments

Separate from all historical June experiments and existing PRs. The
[phase 1 protocol](../../configs/reviewer_experiments/november_phase1.json)
freezes the first baseline and development selective design. The baseline
uses the exact previous scoring implementation and released assets in a
new execution directory. Existing SPH results do not become independent
because waveforms are rescored.

| Review item | Phase 1 | Evidence still required |
|---|---|---|
| R1-2 | Rescore every SPH V1 metadata row without routing or label-based selection. | Reconcile denominator, technical states, compatible references and metrics; validate a different cohort where labels are insufficient. |
| R2-general | Keep NSR separate from Other; audit the published output and reference contracts. | A positive/explicit-negative support audit before any auxiliary training or Other performance claim. Unmapped outputs do not gain reference labels by index or absence. |
| R2-3f | Use the frozen release scorer; retain the predeclared score tolerance for historical replay. | Actual paired historical replay and residual investigation, separate input perturbation, then a matched retrained ablation. |
| R2-4k | Baseline has no selective routing; the frozen development recipe is prediction-only at application time. | Seal calibration, generate private route ledger and report risk/coverage and per-route outcomes. A separate eligible test is needed for independent claims. |

The new work does not reuse the Plan AE reference-membership percentage
as a quarantine rate. Do not inspect a new test's outcome labels to choose
thresholds or ontology. Do not publish patient keys, waveform signatures
at record level, signals, predictions or checkpoints. Clinical review and
real second-stage inference are not implied by abstention.

## CEDIA execution registry

| Job | Phase | Gate | Expected evidence |
|---:|---|---|---|
| 33355 | New frozen P6/P8/P4 inference | Immutable SPH inputs, release weights and frozen scorer | Private scoring ledger and scoring receipt |
| 33356 | Pair new scores with job 32668 | afterok:33355 | Aggregate residuals, decisions and denominator reconciliation |
| 33357 | Aggregate new baseline metrics | afterok:33355 | Compatible-endpoint confusion/metrics and cluster intervals |
| 33362 | Freeze policy on calibration components, then evaluate held SPH development components | afterok:33355:33357 | Private split/route ledgers, cutoff seal, and aggregate selective metrics |
| 33363 | Rerun saved P4 waveform panel | P4 source 02019b832fafecd0c263ea556c70f16fa0a50ccf | Private replay ledger |
| 33364 | Rerun saved rhythm waveform panels | Rhythm source cfe6d59fa5cc4be10de0d7c6803fa5208fae0072 | Private replay ledger |
| 33365 | Audit historical panel residuals and decisions | afterok:33363:33364 | Aggregate decision and score differences |
| 33369 | Mapped auxiliary ranking and observable Other support | afterok:33355 | Complete-denominator reference states and ranking on explicit compatible controls |
| 33373 | Initial zero-morphology sensitivity submission | Held before execution: pinned P4 runner has no extractor-loader hook | Preserved preflight rejection; do not release |
| 33416 | Corrected paired zero-morphology sensitivity with immutable released weights | afterok:33363:33364 | Score/decision changes, not retraining |
| 33381 | Fresh paired extraction, matched retraining, calibration seal, held comparison | afterok:33355:33363:33364 | Private models plus aggregate paired intervals and original-baseline comparison |
| 33390 | New PTB-XL auxiliary and bounded pathology Other heads | afterok:33355:33369 | Complete reference flow, held metrics and patient intervals for supported endpoints |
| 33396 | New SPH mapped rhythm Other and auxiliary heads vs frozen-score comparator | afterok:33355:33369 | Paired held development metrics and full reference/scoring flow |
| 33399 | Same-score full-population vs restricted SPH analysis | afterok:33355:33357 | Statement prevalence, disjoint flow strata, and paired differences between denominators |
| 33403 | Compare both new waveform replays to archived predictions and previous native replays | afterok:33363:33364 | Anchored input hashes, score residuals, margins, decisions and missing-score counts |
| 33410 | Complementary unfiltered PTB-XL cache scoring with P6/P8/P4 | afterok:33355 | Complete denominator and technical flow; statement metrics for 1AVB/ISC_ and released pathology auxiliary ranking |
| 33414 | One joint P8/P4 accept-or-abstain decision per held SPH ECG | afterok:33362 | Verified private route ledger, coverage/risk intervals and classwise positive disposition |

The submitted baseline uses experiment commit f989eccf74d38399d0298026e6f4c078a437fd2d.
The comparison job uses 891dacbca23d7685117f836f98bc3dd1482bb1af.
The corrected sensitivity job uses d2589a5e0a8d3174710d24e29b14d8b1fd385eea.
The matched retraining job uses 648c5a4b784b2307376d620eeb03fc0bb5d3198a.
The pathology Other job uses 6baab4228767219c048d8989a35a70e3bb2219fa.
The rhythm Other job uses 72dd436cd5a9e8ec397fccd1e70b9aa1abed4efe.
The full-population contrast job uses 63ff66fb9b49198f773973d5f579c404940c648b.
The replay contrast job uses c4f5e38b31cfad391bdb03ab979ab15d0b2e7543.
The complementary PTB-XL job uses 49e520c0d29b81fcc7f584663c4b5b9ad1fe7b64.
The joint selective job uses 772ec3558d952127fb098cad89d01bb808a8bda9.
Submission is not completion; the registry does not assert results.

The [population contrast protocol](../../configs/reviewer_experiments/november_population_contrast.json)
uses the same frozen predictions for both denominators. Its restricted
SPH subset requires at least one defensibly mapped statement for the
profile; it does not reconstruct the original panel selection. Counts
cover every metadata ECG, including normal-only, ambiguous, proxy,
out-of-profile, mixed-statement and technical failure strata. Metrics
are computed only on scored rows with a valid statement reference, never
imputing scores or clinically negative labels. The same patient/exact-signal
bootstrap draws compare the nested populations. No difference is
interpreted as the causal effect of cohort selection or an overall
clinical accuracy. P8 top-1 fallback remains an internal decision rule,
not clinical referral, abstention or a separately executed stage.

The [complementary PTB-XL protocol](../../configs/reviewer_experiments/november_ptbxl_reference_bridge.json)
records every one of the 19,601 fold 1-9 metadata rows, with 6,205
waveforms present in the authorized preflight cache. It reads neither
fold-10 waveforms nor their reference labels. The direct `1AVB` and
`ISC_` SCP statements complement SPH's insufficient references, but
the latter means non-specific ischemic ECG statement, not clinical
ischemia. Zero likelihood is unknown under the
[versioned PhysioNet data description](https://physionet.org/content/ptb-xl/1.0.3/#data-description).
`SR` is a sinus-rhythm statement, not an NSR control/positive, and its
likelihood is unknown in these folds. Patient-component intervals are
computed on matched references; case-control PPV and NPV are not
population estimates. The protocol also produces matched-reference
threshold-free ALMI/ILMI/LAO-or-LAE scores from the released V3AG
backbone. The previously inspected partial cache is not an independent
validation cohort and is not a replacement for the SPH denominator.

The [morphology input contract](MORPHOLOGY_INPUT_CONTRACT.md) gives the formulas
and separates waveform replay, fixed-weight sensitivity and retraining.
The corrected sensitivity job intercepts the extractor argument at the
pinned waveform preparation boundary. It leaves the loader source and
candidate extractor unchanged, including their integrity checks. The
verified P6 manifest defines its 1,643 intended ECGs independently
of the 2,193 ECG shared rhythm ledger. An unscored eligible P6 record
remains in its denominator; a P8-only ECG is not a missing P6 score.
Job 33403 authenticates the previous native ledgers and receipts from
32448 and 32461 and the archived prediction tables separately. It
records exact native byte agreement if observed, but can also quantify
native drift without redefining an archived residual as equivalence.
Neither contrast substitutes for the missing original loader. The
strict same-ledger audit 33365 remains unmodified. The old P4 denominator
is in panel observations, not distinct ECGs.

The development calibrator groups ECGs by patient components linked by
exact waveform hashes, uses only the calibration half for cutoffs and
exports aggregate counts and the frozen thresholds. A subsequent scoring
stage must verify that receipt before processing held outcomes. The split
cannot convert previously inspected SPH into independent validation.

The [joint selective protocol](../../configs/reviewer_experiments/november_joint_selective.json)
uses those same sealed cutoffs, without refitting. The compound policy
emits both P8 and P4 released decisions only if both component margins
pass; otherwise it emits no prediction. P6 remains a diagnostic
comparison, not a third gate. The joint ledger keeps the original
predictions for audit, and the aggregate separates emitted misses,
reference positives with no prediction due to abstention, and technical
non-scoring. Abstained-baseline FN is a counterfactual, not an emitted
FN. No real cascade or human adjudication is performed, and these
predeclared retrospective results do not define a historical rate.

For auxiliary reference support, the versioned SPH dictionary provides
Flutter (51) and LAE (140). The frozen score interface exposes Flutter as
the first of six window-mean auxiliary rhythm softmax probabilities and
LAE as a named pathology auxiliary sigmoid. The submitted job 33369
configuration calls the former a logit in its descriptive scale field;
the sealed scorer exports probabilities and the ranking code does not
apply an additional transform. Ranking uses only target statements and explicit
Normal ECG-only controls; concurrent Normal and abnormal primary
statements are ambiguous. The complete source denominator includes
unknowns. Normal ECG does not authenticate an NSR endpoint. No operating
threshold or comprehensive Other classifier is inferred.

The [released backbone audit](RELEASE_HEAD_SUPPORT.md) verifies both
published checkpoint payloads separately. V3AG and V3F have different
fine-tuning rhythm subsets despite sharing a global output contract;
the embedded V3AG Flutter/Paced panels must not be attributed to V3F
or to the released P4 specialist. This audit adds no inference results.

The [new PTB-XL pathology protocol](../../configs/reviewer_experiments/november_pathology_other.json)
defines the explicit statement endpoints ALMI, ILMI and LAO/LAE (combined
overload/enlargement, not isolated LAE), and evaluates their union as a
bounded pathology Other alternative. It retains the full official-fold
1-9 metadata denominator, including unscored and unknown reference states.
New heads use sealed Stage A P4 features, train on folds 1-7 and calibrate on
one patient-disjoint portion of fold 9. The other portion is evaluated
after sealing the models and thresholds. Fold 10 outcomes and waveforms
are not used; fold 8 is not used for fitting or evaluation. P4 has no
published specialist decision for these endpoints; SPH auxiliary ranks
from job 33369 are not a head-to-head comparison with this PTB-XL result.
This design does not evaluate a comprehensive pathology Other or
establish independent generalization.

The [SPH rhythm Other protocol](../../configs/reviewer_experiments/november_rhythm_other.json)
defines separate P6 and P8 unions of observable out-of-profile statements:
Flutter, LBBB, specified 2AVB and 3AVB; only the P6 union also includes PAC.
It evaluates those four auxiliary endpoints individually where supported.
Prolonged QT is not an LQTS syndrome label, Paced has no verified SPH
mapping, and Normal ECG is only an explicit control, not an NSR endpoint.
The head is a new logistic layer on frozen P6/P8 and auxiliary scores,
not an alteration to the released models. The released-score comparator
is a maximum of mapped auxiliary scores, with no P6 PAC score and no
published Other threshold. Both thresholds are fitted on the same
calibration patients and sealed before computing held performance.
Unknown and discordant references remain in full-population flow counts;
metrics and paired intervals apply only to matched known references.
This source is retrospective development, not independent validation.

## Links to the 40-criterion register

R1-2.1 receives new reproducibility evidence only after successful scoring
and aggregation; R1-2.2–3 remain historical questions. R2-general.1
distinguishes declared outputs from evaluable references, and
R2-general.2 does not close on a mapped subset. R2-3f.3 requires score and
decision verification on the historical panels, not the SPH repeat;
R2-3f.1–2 and R2-3f.4 retain their source and checkpoint caveats.
R2-4k.1 remains historical; a selective SPH development result belongs to
R2-4k.2 and never updates the June rate. No automatic scoring changes.
