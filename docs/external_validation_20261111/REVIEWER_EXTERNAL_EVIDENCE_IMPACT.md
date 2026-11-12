# External evidence impact: historical rubric and supplemental PR #6 evidence

The [full frozen CODE-15% sample](CODE15_FULL_EVALUATION.md) now has
paired, independently recomputed metrics over all 18 archives. It does
not validate the 10 s waveform contract, historical independence or
clinically adjudicated generalization. The table below keeps PR #3's
historical rubric snapshot rather than grading the new PR #6 evidence.

The previous percentages below come from the historical [PR #3 matrix](https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/68274ee05dab1e5aaa48aa588262b5b8289cbbd4/docs/reviewer_closure/REVIEWER_15_COVERAGE_AND_CEILING.json), field `new_pct`. The new study does not edit that matrix or change a percentage based on acquisition, queued jobs, or label-blind inference.

| Reviewer | Previous | Current | What remains for scientific satisfaction |
|---|---:|---:|---|
| R1-1 | 50% | 50% | Historical rubric only. The completed CODE benchmark adds external agreement; clinically valid reference, duration and independent confirmation remain distinct. |
| R1-2 | 33.3% | 33.3% | Complete external eligibility/routing denominator, reference coverage, and decisions; does not recover the historical preselection population. |
| R2-general | 50% | 50% | Compatible source references and separate multilabel evaluation for Other categories, including coexistence and explicit unknown states. |
| R2-3a | 50% | 50% | Executed and audited splits, class supports and isolation for the new study; authentic training manifests linked to historical weights remain separate. |
| R2-3c | 83.3% | 83.3% | Historical supervision and evaluation for auxiliary heads; outputs of a new study cannot prove original loss participation. |
| R2-3d | 83.3% | 83.3% | Direct evidence or new valid separate evaluation for ALMI/ILMI/LAE; neither training nor results inferred. |
| R2-4a | 75% | 75% | Locked external-source and patient-holdout results distinguished from development evidence; historical selection claims require historical links. |
| R2-4e | 50% | 50% | Full population routing against a compatible reference and explicit uncovered endpoints; no clinical abstention or quarantine inferred from thresholds. |

The [execution receipt](../../outputs/results/external_validation_20261111/EXTERNAL_VALIDATION_REPRODUCIBILITY.json) adds verified metadata, a patient-level selection, real label-blind inference on three MIMIC ECGs, and a negative reference-support audit on 5,770 development ECGs. These improve implementation traceability and identify a concrete barrier, but do not satisfy a new scoring subrequirement of the existing rubric.

None of the above percentages is a probability of acceptance. A frozen baseline and an adapted patient holdout answer different questions. The former cannot establish independence from undocumented historical pretraining; the latter does not establish transport to another hospital. Cross-source confirmation remains separate.
