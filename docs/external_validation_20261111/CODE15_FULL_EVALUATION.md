# CODE-15% full locked evaluation

**Operational benchmark complete; duration contract limited. P6: FAIL.
P8: FAIL. P4: NOT EVALUABLE. R1-1: PARTIAL.**

All 18 publisher ZIPs passed size, publisher MD5, SHA-256, ZIP CRC and
HDF5-to-CSV membership checks. The original patient-hash selection,
waveform rule, endpoints, weights, thresholds and promotion criteria were
unchanged. Published P6 and P8 and their respective frozen linear residual
adapters used the same ECGs and the same structured CODE references.
The sealed first archive was reused rather than scored again. Of its
1,442 scored ECGs, 31 were removed by the full aligned duplicate screen;
the other 1,411 were verified bit-for-bit. The sample
is not the entire CODE-15% release and the structured flags are not clinical
adjudications for this study.

| Population | ECGs | Patients |
|---|---:|---:|
| Publisher index across 18 ZIPs | 345,779 | 233,770 |
| Frozen patient-hash sample | 43,187 | 29,081 |
| Excluded before scoring | 18,001 | See patient count below |
| Scored but removed by within-CODE aligned duplicate rule | 504 | See patient count below |
| Final paired analysis | 24,682 | 17,300 |
| Selected patients with no ECG in the final analysis | Not applicable | 11,781 |

Exclusions before scoring: 17,890 unexpected zero-border patterns, 82
short or ambiguous traces under the frozen rule, and 29 flat-lead traces.
There were no recorded inference errors. Positive ECG support was AFIB
511, SB 427, STACH 599, RBBB 800 and 1AVB 433. All 24,682 final ECGs
had a usable publisher flag for each of the five endpoints.

| Profile | Published macro-F1 | Frozen linear macro-F1 | Paired delta (patient 95% CI) | Gate |
|---|---:|---:|---:|---|
| P6 | 0.428743 | 0.428104 | -0.000639 [-0.006899, +0.004992] | FAIL |
| P8 | 0.449186 | 0.436388 | -0.012798 [-0.019583, -0.005406] | FAIL |

Macro-F1 is the unweighted mean of the five endpoint F1 values. The frozen
gate required at least +0.03 and a positive paired lower confidence bound.
Neither condition was met by either profile. In P8, RBBB had 53 fewer
false negatives but 810 more false positives (933 to 1,743), and its F1
fell from 0.5540 to 0.4399. This is a benchmark observation, not an
estimate of clinical utility. No specialist was promoted.

## Signal and independence limits

The label-blind preflight found 25,111 selected traces with symmetric
581/581 all-lead zero borders and 16,400 with no zero border. The final
24,682 include 24,578 with symmetric 581/581 borders, 15 with symmetric
48/48 borders and 89 with other border pairs. At the documented 400 Hz,
581/581 leaves 2,934 delivered nonzero-envelope samples (7.335 s).
The frozen rule often admitted that shorter representation and excluded
the unpadded representation; this is not a validated 10 s acquisition
contract. The [signal contract note](CODE15_SIGNAL_DURATION_CONTRACT.md)
distinguishes evidence of zero padding from unknown raw recording
duration and provides a separate prospective protocol draft.

The aligned-signal screen found no matches against the 573 comparable
publisher CODE-test traces. It could not compare 254 other publisher
CODE-test traces or 167 converted historical traces under the frozen
signature contract. The 504 within-CODE exclusions are ECGs implicated
by the aligned-similarity rule, not duplicate patients. Absence of an
aligned match does not establish historical patient independence,
exclude shifted or cropped overlap, or certify clinical generalization.

## Artifacts

[Delivery and duration receipt](../../outputs/results/external_validation_20261111/code15-full/CODE15_FULL_DELIVERY_RECEIPT.json) |
[Execution receipt](../../outputs/results/external_validation_20261111/code15-full/CODE15_FULL_SLURM_RECEIPT.json) |
[Per-class metrics](../../outputs/results/external_validation_20261111/code15-full/EXTERNAL_CODE15_RESULTS.csv) |
[Confusion counts](../../outputs/results/external_validation_20261111/code15-full/EXTERNAL_PER_CLASS_CONFUSION.csv) |
[Macro-F1 and paired intervals](../../outputs/results/external_validation_20261111/code15-full/EXTERNAL_CODE15_MACRO.csv) |
[Calibration bins](../../outputs/results/external_validation_20261111/code15-full/EXTERNAL_CODE15_CALIBRATION.csv) |
[Verifier](../../scripts/external_validation/seal_full_code15_delivery.py)

Individual waveforms, identifiers, selection and predictions stay on
CEDIA. The aggregate verifier independently recomputes point metrics
from the private paired predictions, reconciles pre- and post-score
duration counts, checks the already replayed patient bootstrap and verifies
the first-archive scores that survive the full duplicate screen.
