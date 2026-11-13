# Patient split and waveform overlap checks

MIMIC assignment is deterministic, uses source patient keys and assigns every selected ECG of a patient to exactly one split. Selection and split assignment use separately salted hashes. Two ECGs per patient is a storage bound, not a label quota. Failed downloads remain in the denominator; they are not replaced by other records.

| Frozen selection | ECGs | Patients |
|---|---:|---:|
| Train | 4,396 | 2,662 |
| Validation | 690 | 410 |
| Calibration | 684 | 409 |
| Retained test | 1,014 | 615 |
| Total | 6,784 | 4,096 |

These are selection counts, not final waveform-QC or evaluable denominators. The retained labels were not extracted. The private manifest's aggregate hash is in the [execution receipt](../../outputs/results/external_validation_20261111/EXTERNAL_VALIDATION_REPRODUCIBILITY.json).

The outcome-blind waveform job rechecks the hashes and sizes of both WFDB components, validates gains and physical units and requires 12 distinct canonical leads at 500 Hz for 10 seconds. The private manifest retains acquisition failure, decode failure, physical peak amplitude, exact physical signature and waveform eligibility. The aligned near-duplicate screen uses 25 Hz time blocks, normalizes each lead independently, then compares the concatenated 12-lead vectors at mean cosine similarity >= 0.995. Both members of suspected pairs are excluded. It is an aligned screen and cannot rule out cropped, shifted, or differently processed copies.

Historical overlap checking implemented here is only a raw-byte comparison against available Stage A inventory hashes. It is not a physical cross-source near-duplicate comparison, and encoding differences can hide overlaps. The accessible historical backbones do not certify patient independence. CODE-15% uses its own publisher patient keys; neither those keys nor MIMIC keys can establish linkage across institutions.
