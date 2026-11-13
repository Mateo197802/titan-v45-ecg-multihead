# CODE duration correction

The [signal audit](EXTERNAL_SIGNAL_CONTRACT_AUDIT.md) defines the contract and
links the executed preprocessing comparison. This note explains which historical
claim it changes: a fixed-shape stored waveform is not necessarily a ten-second
observation. The prior PR #6 has 24,578 accepted traces with 581 samples of zero
padding on each side, out of 24,682 evaluated. These traces contain 7.335 seconds
of observed data, not ten seconds. The historical benchmark is preserved rather
than recomputed and silently relabeled.

The new bounded cohort includes 12,742 short and 8,216 long ECG among 20,958
eligible ECG; the denominators differ from PR #6. The new selection explicitly
keeps the PR #6-selected patients out of validation, calibration and reserved
within-CODE evaluation. It does not exclude them from training and does not
certify cross-source independence. Cohort, exclusions and patient-group counts
are machine-readable in the [verified QC summary](evidence/EXTERNAL_DATA_MANIFESTS_SUMMARY.csv).

The code only creates fixed-length batches after recognizing the physical
observed window. The short branch does not pad to the long branch. Long traces
are center-cropped to 4000 observed samples. The validation controls isolate the
choice of normalizer on matched corrected input, not the causal contribution of
duration correction. A comparison with the historical PR #6 numbers must keep
selection, contract, and thresholds visible as separate factors.
