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

The submitted baseline uses experiment commit f989eccf74d38399d0298026e6f4c078a437fd2d.
The comparison job uses 891dacbca23d7685117f836f98bc3dd1482bb1af.
Submission is not completion; the registry does not assert results.

The development calibrator groups ECGs by patient components linked by
exact waveform hashes, uses only the calibration half for cutoffs and
exports aggregate counts and the frozen thresholds. A subsequent scoring
stage must verify that receipt before processing held outcomes. The split
cannot convert previously inspected SPH into independent validation.
