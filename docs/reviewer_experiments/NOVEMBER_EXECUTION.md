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
| 33373 | Paired zero-morphology sensitivity with immutable released weights | afterok:33363:33364 | Score/decision changes, not retraining |
| 33381 | Fresh paired extraction, matched retraining, calibration seal, held comparison | afterok:33355:33363:33364 | Private models plus aggregate paired intervals and original-baseline comparison |
| 33390 | New PTB-XL auxiliary and bounded pathology Other heads | afterok:33355:33369 | Complete reference flow, held metrics and patient intervals for supported endpoints |

The submitted baseline uses experiment commit f989eccf74d38399d0298026e6f4c078a437fd2d.
The comparison job uses 891dacbca23d7685117f836f98bc3dd1482bb1af.
The matched retraining job uses 648c5a4b784b2307376d620eeb03fc0bb5d3198a.
The pathology Other job uses 6baab4228767219c048d8989a35a70e3bb2219fa.
Submission is not completion; the registry does not assert results.

The [morphology input contract](MORPHOLOGY_INPUT_CONTRACT.md) gives the formulas
and separates waveform replay, fixed-weight sensitivity and retraining.

The development calibrator groups ECGs by patient components linked by
exact waveform hashes, uses only the calibration half for cutoffs and
exports aggregate counts and the frozen thresholds. A subsequent scoring
stage must verify that receipt before processing held outcomes. The split
cannot convert previously inspected SPH into independent validation.

For auxiliary reference support, the versioned SPH dictionary provides
Flutter (51) and LAE (140). The frozen score interface exposes Flutter as
the first of the six rhythm auxiliary logits and LAE as a named pathology
auxiliary sigmoid. Ranking uses only target statements and explicit
Normal ECG-only controls; concurrent Normal and abnormal primary
statements are ambiguous. The complete source denominator includes
unknowns. Normal ECG does not authenticate an NSR endpoint. No operating
threshold or comprehensive Other classifier is inferred.

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
This design does not evaluate a comprehensive pathology Other or any new
rhythm Other head and does not establish independent generalization.

## Links to the 40-criterion register

R1-2.1 receives new reproducibility evidence only after successful scoring
and aggregation; R1-2.2–3 remain historical questions. R2-general.1
distinguishes declared outputs from evaluable references, and
R2-general.2 does not close on a mapped subset. R2-3f.3 requires score and
decision verification on the historical panels, not the SPH repeat;
R2-3f.1–2 and R2-3f.4 retain their source and checkpoint caveats.
R2-4k.1 remains historical; a selective SPH development result belongs to
R2-4k.2 and never updates the June rate. No automatic scoring changes.
