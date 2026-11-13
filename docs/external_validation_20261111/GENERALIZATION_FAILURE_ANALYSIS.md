# First CODE-15% archive: failure analysis

This is a paired operational result for `exams_part10.zip`, one of 18
archives, with both models evaluated on the same 1,442 ECGs and 1,403 source
patients. The [publisher's structured flags](https://zenodo.org/records/4916206)
are benchmark references, not a clinical overread. The duration audit below
limits scientific interpretation; do not compare these results directly with
the historical selected panels or combine them with MIMIC or SPH.

| Endpoint | Positives (ECG / patients) | P6 FN / FP, published to linear | P8 FN / FP, published to linear |
|---|---:|---|---|
| AFIB | 42 / 41 | 20 / 27 to 22 / 23 | 20 / 25 to 25 / 23 |
| SB | 24 / 24 | 5 / 245 to 3 / 294 | 3 / 341 to 2 / 374 |
| STACH | 32 / 32 | 5 / 32 to 5 / 31 | 4 / 34 to 5 / 30 |
| RBBB | 48 / 48 | 7 / 120 to 3 / 135 | 11 / 44 to 7 / 84 |
| 1AVB | 27 / 27 | 12 / 14 to 12 / 11 | 17 / 5 to 15 / 5 |

- P8 AFIB sensitivity decreased from 0.524 to 0.405, beyond the frozen
  0.05 maximum loss. The AUROC was almost unchanged (0.960 to 0.959),
  so this observed trade-off concerns the operating point; that does not
  show that a new threshold would generalize.
- SB positives represent 1.66% of the scored cohort. Both adapters gain
  sensitivity at the expense of many more false positives. P8 SB Brier
  worsens from 0.199 to 0.226 and ECE from 0.247 to 0.272. High ranking
  performance is not equivalent to useful precision under this prevalence.
- P8 RBBB has four fewer false negatives but 40 more false positives.
  The P8 1AVB improvement does not offset the AFIB/RBBB losses. P6 and P8
  five-endpoint empty sets decrease (888 to 858; 889 to 849), but an empty
  set is not clinical quarantine, referral, or evidence of Other.
- The direct MLP comparison in Georgia is [development evidence](SPECIALIST_ABLATION_STUDY.md)
  and does not establish a replacement. In that cohort SB represented
  333/1,097 ECGs, unlike 24/1,442 here. Distinct supports, labels and waveform
  properties are concurrent explanations, not separable causal effects.
  The published P6 median 1AVB score among Georgia positives was 0.735
  versus 0.772 among Chapman training positives; these descriptive scores
  do not establish patient independence or an architecture failure.

## Duration and coverage

Of 20,000 indexed ECGs, 2,461 entered the frozen patient-hash sample.
1,011 failed the zero-border rule, seven had no nonzero sample, and one
had a flat lead. The remaining 1,442 (58.59%) were scored without a
recorded inference error. The border audit found that 923 of 1,011 padding
failures had no all-lead zero border on either end. It also found 1,438
selected traces with a symmetric 581/581 border, inconsistent with the
documented nominal 48/48 or 648/648 cases. At nominal 400 Hz this leaves
2,934 nonzero-envelope samples (7.335 s); this is an envelope, not verified
acquisition duration or proof of the resampling mechanism.
Of the 1,442 scored ECGs, 1,437 have that exact pattern and the other five
have 581 trailing zero samples and more than 581 leading zeros. None has
the nominal 48/48 envelope.

The frozen operational rule admitted these traces because it checks a
minimum border and only flags a short trace if both borders reach 648.
Do not describe its output as verified 10-second ECG performance. Do not
change eligibility after reading outcomes. Any revised duration contract
requires source clarification and a separately frozen, unexamined evaluation.
Amplitude units and alignment beyond the documented layout are not certified.

The [publisher's preprocessing source](https://github.com/antonior92/ecg-preprocessing/blob/439bc1bafde571feee9e79e86f475ae9ee37d9e4/ecgprep/preprocess.py#L60-L94)
allows centered padding and cropping. It does not link a particular
CODE-15% ECG to an exact duration or prove that every row used those bytes.
All 1,442 scored ECGs supported the documented limb-lead order and sign
in a nearest-hypothesis comparison using the four expected limb relations
and their reversals. None matched all four identities exactly at the
numeric audit tolerance; for the three augmented leads, median normalized
residuals were approximately 2.69%, 2.37% and 2.08%, respectively. The
fitted coefficients remained close to the theoretical ones. This is
evidence against a simple limb swap or inversion, not certification of
precordial order, acquisition duration or units. No channel was reordered.

[Per-model results](../../outputs/results/external_validation_20261111/code15-first/EXTERNAL_CODE15_RESULTS.csv) ·
[Confusion counts](../../outputs/results/external_validation_20261111/code15-first/EXTERNAL_PER_CLASS_CONFUSION.csv) ·
[Calibration bins](../../outputs/results/external_validation_20261111/code15-first/EXTERNAL_CODE15_CALIBRATION.csv) ·
[Calibration plot generator](../../scripts/external_validation/plot_code15_calibration.py).
Render the figure to a path outside the repository; the manuscript image
manifest is unchanged.
