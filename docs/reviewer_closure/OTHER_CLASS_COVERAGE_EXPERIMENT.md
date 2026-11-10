# Other-Class Coverage Experiment Boundary

**Status:** No `Other arrhythmia` or `Other pathology` experiment has been run for V4.5. No manuscript or historical model artifact was changed.

## What V4.5 evidence establishes

- The released operational rhythm profiles are P6 (six classes) and P8 (eight classes); P8 includes NSR, which means normal sinus rhythm and is not an `Other` class.
- The four-label P4 specialist covers ASMI, LVH, IMI and ISC_. Seven global pathology outputs include ALMI, ILMI and LAE as auxiliary outputs; neither output width nor emitted scores establish validated `Other` behavior.
- Empty P6/P4 threshold sets and P8 forced top-1 fallback are distinct software decisions. They do not mean `Other`, abstention, quarantine or human review.
- The SPH endpoint protocol has 14 compatible statement comparisons. Unsupported labels are not converted to negatives; no pooled all-class clinical accuracy is defined.

See [`full-class coverage`](FULL_CLASS_COVERAGE_AND_ROUTING_AUDIT.md), [`role/supervision evidence`](ROLE_SUPERVISION_AND_ROUTING.md) and [`SPH results`](../external_validation/sph_results.md).

## What cannot be reconstructed historically

The checked evidence does not establish a trained/calibrated `Other` head, a complete ontology for out-of-panel diagnoses, all incoming cases with their labels, or checkpoint-linked loss masks and supports for all global outputs. Missing codes and missing scores are not negative labels. NSR cannot serve as a catch-all class. The June parent denominator and exclusion reasons are not recovered.

## New experiment required if the claim is retained

1. Authors/clinical collaborators define a mutually interpretable ontology: named diagnoses, normal/other/unknown states, co-occurrence rules and explicit out-of-scope handling.
2. Obtain rights-cleared data with compatible reference labels and full patient/source provenance; separate patient groups before any training, calibration or evaluation.
3. Freeze class mapping, inclusion/exclusion, loss masks, train/validation/calibration/test partitions, thresholds, fallback, abstention/referral action and target metrics before evaluation.
4. Measure class supports and error counts at record and patient level; report class-wise sensitivity, specificity, PPV, NPV, F1, AUROC/average precision where defined, calibration, coverage and patient-clustered intervals.
5. Keep the test cohort untouched and include empty/unknown/unsupported cases in the flow denominator with explicit reasons.

**Current conclusion:** `Other` performance is not assessed and cannot be supplied by relabeling the current predictions. A future experiment would be a new study, not retrospective proof of V4.5 training.
