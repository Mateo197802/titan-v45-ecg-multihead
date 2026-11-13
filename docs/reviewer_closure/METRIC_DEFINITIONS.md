# Metric definitions for later editorial use

This is a technical handoff, not an edit to the submitted manuscript. The
historical selected panels and the SPH statement-level endpoints are distinct
evaluations and do not have interchangeable populations or label ontologies.

## Binary endpoint counts

For a specified endpoint and scored population, `TP`, `TN`, `FP`, and `FN`
refer to the model decision versus that endpoint's stated reference. Define
`N = TP + TN + FP + FN`; report the population eligible, scored, and unscored
separately. The following quantities use the displayed denominator:

| Quantity | Definition |
| --- | --- |
| Accuracy | `(TP + TN) / N` |
| Sensitivity / recall | `TP / (TP + FN)` |
| Specificity | `TN / (TN + FP)` |
| Positive predictive value / precision | `TP / (TP + FP)` |
| Negative predictive value | `TN / (TN + FN)` |
| F1 | `2 TP / (2 TP + FP + FN)` |

Zero-denominator ratios are undefined. The existing binary evaluator records
F1 as zero when its denominator is zero and marks that convention explicitly;
this is not equivalent to an observed positive-class success. Report supports
and undefined values rather than replacing them with favorable estimates.

For probability `p_i` and binary reference `y_i`, the Brier score is the
mean of `(p_i - y_i)^2` over rows with an available score. Equal-width ECE
uses ten bins and the score-count-weighted absolute difference between mean
score and observed reference frequency in each nonempty bin. AUROC integrates
the empirical ROC; average precision is the step integral of precision over
recall. Both group tied scores. AUROC requires both positive and negative
references; average precision requires positive references. See
[`binary_metrics`](../../src/titan_v45/evaluation/revision_report.py) and the
[pre-result ECE bootstrap correction](../external_validation/sph_ece_bootstrap_correction.md).

## Historical profile quantities

Primary6 top-1 accuracy counts a record correct when its top-ranked class is
in the reference label set. Its macro-F1 is the arithmetic mean of six
one-versus-rest thresholded F1 values, not F1 computed from top-1 alone.
Primary8 accepted-label accuracy uses the analogous accepted-label membership
rule; its single-target accuracy is a distinct measure. Primary4 mean accuracy
and macro-F1 are unweighted means over four binary panels; the panel observation
count is not the number of distinct ECGs. The authoritative calculations and
denominators are linked in [the historical handoff](HISTORICAL_EVIDENCE_HANDOFF.md).

## SPH reference and uncertainty

The frozen SPH comparison uses the presence of specified publisher ECG
statements. Absence of a statement is not an adjudicated absence of disease.
No pooled profile accuracy is defined across incompatible references. Report
each compatible endpoint and its scored positive and negative supports.

For each endpoint, the frozen protocol specifies 2,000 unstratified percentile
bootstrap replicates over connected components of source patients linked by
exact duplicate waveforms. Point estimates remain record-level. The 2.5th and
97.5th percentiles of valid replicates define the interval; valid and invalid
replicate counts must accompany it. An interval does not establish historical
independence, calibration-patient isolation, prospective utility, or clinical
safety. The [SPH protocol](../external_validation/sph_protocol.md) specifies
the seed, duplicate sensitivity analysis and full flow accounting.
