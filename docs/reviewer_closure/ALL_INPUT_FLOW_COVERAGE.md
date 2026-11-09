# All-input flow and endpoint coverage

This report closes the executable coverage analysis for the frozen V4.5
predictions. It does **not** reconstruct the missing June preselection
population, certify the full historical training lineage, establish clinical
ground truth, or validate quarantine. The submitted manuscript and response
letter have not been changed.

## Evidence boundary

The primary evidence is the frozen SPH aggregate from job `32669`, checked by
the [delivery audit](SPH_DELIVERY_AUDIT.md) and frozen under protocol commit
`eb1c67b9229af875a9f868797b0c2f5c546e3dac` (protocol SHA-256
`d788ad8cca94793cebb738496acc131e82b1ca1900976f11020b99a79a5fc366`). The
source contains 25,770 ECG from 24,666 patients. Every source record was
scored by P6, P8 and P4: 25,770/25,770 per profile, with zero technical
exclusions, zero inference failures, and no missing signal or metadata in the
frozen scoring receipt. The 25,770 ECG are not 25,770 independent patients.
The SPH signals are stored at 500 Hz in float16; the HDF5 files do not certify
physical units, and the frozen pipeline performs no mV conversion.

This is a transfer evaluation against SPH ECG statements. A positive means the
specified code is present; a missing code is not adjudicated disease absence.
The source is institutionally distinct from the retained evaluation sources,
but incomplete V3F/V3AG pretraining and fine-tuning manifests prevent a claim
of complete historical independence.

## Profile-level decisions

All three profiles receive the full 25,770-record source. Their outputs are
separate decisions and must not be pooled into a single accuracy. Per-class
predicted-label counts can overlap because the profiles are multilabel.

| Profile | Scored / source | Empty threshold set | Forced fallback | Top-1 counts by class |
| --- | ---: | ---: | ---: | --- |
| P6 | 25,770 / 25,770 | 16,785 | 0 | AFIB 850; SB 12,701; STACH 1,631; RBBB 3,962; 1AVB 791; PVC 5,835 |
| P8 | 25,770 / 25,770 | 0 after decision fallback | 801 | AFIB 767; SB 3,261; STACH 926; NSR 16,700; RBBB 1,420; PAC 706; 1AVB 483; PVC 1,507 |
| P4 | 25,770 / 25,770 | 8,343 | 0 | ASMI 3,344; IMI 8,251; ISC_ 2,955; LVH 11,220 |

P6 and P4 can return an empty thresholded set. P8 forces its highest-scoring
class when no threshold is crossed; the 801 fallbacks are not quarantine,
`Other`, or human review. The positive-label counts are AFIB 740, SB 3,257,
STACH 802, RBBB 1,753, 1AVB 614, PVC 2,280 for P6; AFIB 768, SB 3,628,
STACH 913, NSR 17,651, RBBB 1,391, PAC 1,967, 1AVB 444, PVC 1,418 for P8;
and ASMI 2,275, LVH 8,019, IMI 6,472, ISC_ 5,207 for P4. These multilabel
counts are predictions, not reference prevalence.

## Compatible endpoint comparisons

The protocol defines 14 statement-level comparisons. Each uses all 25,770
records; the positive and negative supports below are recorded-code supports.
PPV/F1/AUROC are the frozen-threshold/score results in the
[aggregate](../../outputs/results/external_sph/sph_aggregate_32669.json);
patient-component 95% intervals and the remaining metrics are in the
[published results table](../external_validation/sph_results.md).

| Endpoint | Positive / negative statements | PPV | F1 | AUROC |
| --- | ---: | ---: | ---: | ---: |
| P6:AFIB | 675 / 25,095 | 84.86% | 88.76% | 99.87% |
| P6:SB | 2,711 / 23,059 | 68.41% | 74.66% | 96.87% |
| P6:STACH | 725 / 25,045 | 77.06% | 80.94% | 99.19% |
| P6:RBBB | 710 / 25,060 | 39.13% | 55.70% | 98.75% |
| P6:PVC | 1,067 / 24,703 | 39.69% | 54.08% | 95.62% |
| P8:AFIB | 675 / 25,095 | 82.29% | 87.60% | 99.87% |
| P8:SB | 2,711 / 23,059 | 66.04% | 75.60% | 97.95% |
| P8:STACH | 725 / 25,045 | 69.77% | 77.78% | 99.02% |
| P8:RBBB | 710 / 25,060 | 48.09% | 63.68% | 98.96% |
| P8:PAC | 539 / 25,231 | 16.88% | 26.50% | 84.96% |
| P8:PVC | 1,067 / 24,703 | 57.97% | 66.16% | 97.28% |
| P4:ASMI | 91 / 25,679 | 2.46% | 4.73% | 87.62% |
| P4:LVH | 209 / 25,561 | 1.87% | 3.65% | 79.43% |
| P4:IMI | 120 / 25,650 | 1.65% | 3.25% | 90.88% |

The poor P8 PAC and P4 F1/PPV values are retained, not hidden by AUROC. NSR,
1AVB and ISC_ do not have a compatible primary reference mapping in this
protocol; they are not treated as negative examples and no pooled profile
accuracy is calculated. The PVC endpoint is an ECG-level statement, not
beat-level PVC localization or counting. AF is an AF statement on the ECG,
not incident or first-diagnosed AF. Complete TP/FP/TN/FN, sensitivity,
specificity, calibration and patient-component confidence intervals remain
available in the aggregate and results table.

## Selected historical-development replay is separate

The retained development manifests contain 2,193 P8 record keys, including
all 1,643 P6 keys, plus 733 distinct P4 record keys across 962 binary panel
rows. Exact-key comparison gives a 2,926-key P8/P4 union and no overlap
between those two manifest sets. This is a union of ECG record keys, not a
patient count. Reconstructed frozen-weight inference scored all 2,193 P8 and
733 P4 records without reference labels entering the routing code. P8 had 476
NSR top-1 decisions and 58 threshold fallbacks; P6 top-1 differed from the
saved decision on 1/1,643 records; P8 top-1 and binary sets agreed on
2,193/2,193; P4 panel decisions agreed on 962/962, while its maximum absolute
probability difference was `0.0006194115`, exceeding the original `1e-5`
tolerance. The exact historical loader was not recovered. These replays begin
after selection and do not establish June's parent population, exclusion
reasons or full historical cascade.

## Quarantine and human routing

Quarantine is `not_assessed` for all 25,770 SPH records and for the selected
reconstructed profile ledgers: there is no recovered, checkpoint-linked
uncertainty score plus historical quarantine policy from which to calculate
pre/post accuracy or a quarantine rate. The count must not be reported as
zero. Neither a P8 fallback nor an empty threshold set establishes that a
clinician reviewed a tracing. No reader study, human intervention or safety
outcome was measured.

## Reproducibility

- Frozen SPH aggregate SHA-256: `09f93d9f310baaca672a33b0f369593cd88835a8ef08dc9929945c57cf18c988`.
- SPH scoring, aggregation and independent-check jobs: `32668`, `32669`,
  `32672`, `32677`, `32728`; each completed with exit `0:0` as recorded in
  the [delivery audit](SPH_DELIVERY_AUDIT.md).
- The selected-cohort replay JSONs are
  [`rhythm_waveform.json`](../../outputs/results/revision_20261107/rhythm_waveform.json)
  and [`pathology_waveform.json`](../../outputs/results/revision_20261107/pathology_waveform.json).
- The selected manifest counts and key union were recomputed from
  [`rhythm_primary8_records.csv`](../../data/manifests/external_dev/rhythm_primary8_records.csv),
  [`rhythm_primary6_diagnostic_records.csv`](../../data/manifests/external_dev/rhythm_primary6_diagnostic_records.csv)
  and [`pathology_primary4_panels.csv`](../../data/manifests/external_dev/pathology_primary4_panels.csv).

This report supplements, but does not replace, the historical evidence-ceiling
disposition in [`R1_2_EVIDENCE_CEILING.md`](R1_2_EVIDENCE_CEILING.md).
