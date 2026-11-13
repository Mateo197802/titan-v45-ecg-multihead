# CODE-15% duration: observed representation and limits

The [Zenodo release](https://zenodo.org/records/4916206) describes 4,096 rows,
400 Hz, and centered zero padding, illustrating nominal 7 s and 10 s
traces. The [2025 PhysioNet Challenge organizers](https://moody-challenge.physionet.org/2025/#data)
describe the same release as 7.3 s and 10.2 s. Their
[CODE-15% converter](https://github.com/physionetchallenges/python-example-2025/blob/main/prepare_code15_data.py#L123-L188)
removes the leading and trailing all-lead zero rows rather than assuming
fixed 48/648 borders. The [publisher's preprocessing implementation](https://github.com/antonior92/ecg-preprocessing/blob/439bc1bafde571feee9e79e86f475ae9ee37d9e4/ecgprep/preprocess.py#L60-L94)
resamples and can center-pad or center-crop to the configured output size.

The first-archive audit saw 581 all-lead zero rows on each side of
1,437 scored ECGs. 4,096 - 2 x 581 = 2,934 rows, or 7.335 s at the
published rate. This is consistent with the shorter release representation
and centered padding; a 0/0 envelope is consistent with 4,096 delivered
nonzero-envelope rows (10.24 s). Neither observation proves the raw device
duration, source clock, gain or exact preprocessing history of an exam.
The earlier rule can admit the short representation with zeros still
present and reject the unpadded longer representation. Its comparison is
an operational benchmark, not evidence for a verified 10 s signal contract.

The full preflight records original HDF5 shape, CRC, publisher MD5,
archive SHA-256, CSV membership and the raw zero-border distribution in
the locked patient sample, without using labels or scores. It does not
change the frozen rule or the first-archive predictions. The full result
and the signal contract must be reported separately.

## Prospective protocol draft, not executed

Do not apply a revised rule to previously opened CODE outcomes and call
it confirmatory. Select a distinct, authorized, demonstrably uninspected
cohort with ECG-level references and patient keys; audit historical overlap
before enrolling. Require source-backed sampling frequency, lead order,
gain and recording length for each acquisition. For a strict 10 s model
contract, remove only documented padding and extract a fixed centered
10 s window from a sufficiently long trace; exclude shorter or ambiguous
traces with reason codes, rather than representing padding as physiology.
Lock waveform handling, estimand, endpoints, weights, decision thresholds,
patient grouping and the analysis plan before opening reference outcomes.
Any post hoc application to this CODE cohort would be exploratory only.
