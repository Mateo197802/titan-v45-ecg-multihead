# Exploratory PAC V3F embedding probe

## Status and intended use

This is a new exploratory analysis, separate from the frozen three-profile SPH
transfer results. The previously reported Primary8 PAC endpoint has already
been inspected; this probe is therefore not a prospective preregistration and
cannot be called confirmatory. Its purpose is to test whether a simple PAC
classifier can be fitted on frozen V3F representations under a strict patient
split. It is not a clinical validation, diagnostic study, or repair of a
historical V4.5 result.

Separate PAC-head artifacts also exist in a V4.6 benchmark checkout on CEDIA.
They are not inputs, checkpoints, metrics, or model-selection evidence for this
V4.5 probe. Their existence reinforces that PAC has prior target exposure; all
results from this probe remain exploratory and nonconfirmatory.

The complete machine-readable contract is
[`pac_v3f_embedding_probe.json`](../../configs/external_validation/pac_v3f_embedding_probe.json).
The protocol commit and configuration hash must be recorded before fitting or
reading any new probe metrics.

## SPH endpoint and feature construction

The positive target is SPH primary code `30`, an ECG-level PAC statement.
Code `31` is not pooled into that endpoint. A missing code means only that the
statement was not recorded, not that a clinician ruled PAC out. All technically
eligible records are retained in the population flow, with errors recorded by
reason.

The V3F checkpoint is the release-tag `v0.1.0` backbone and stays in inference
mode with gradients disabled. No rhythm/pathology output head, morphology
features, model weights, thresholds, or labels enter feature extraction. For
each frozen 10-second rhythm window, the probe captures the 640-dimensional
post-transformer token sequence before the backbone's final global
normalization/projection. Token-wise mean and max are concatenated to 1,280
dimensions. The record embedding is the mean of these window embeddings using
the existing 10-second/5-second-stride schedule.

Signal preprocessing reuses the hash-pinned reconstructed SPH rhythm path:
12-lead order, causal third-order 0.5-45 Hz filtering, polyphase 500-to-125 Hz
resampling, existing per-lead z-score and fixed 1,250-sample windows. No
physical-unit conversion is inferred. This definition does not claim identity
with the missing original historical loader.

## Split, duplicates, and probes

Split complete patient components 80/20, stratified by whether a component has
at least one PAC-positive ECG. Patients connected by an exact decoded waveform
hash remain in one partition. The split seed is `20261109`. The holdout is
exploratory; its labels cannot be used for model selection or threshold tuning.

The primary analysis retains all eligible holdout ECGs. During fitting, each
exact waveform hash has total base weight one; class-balancing weights are
computed from training rows only. A sensitivity analysis excludes the entire
holdout duplicate group only when PAC-code presence conflicts among its members.
Approximate waveform duplicate detection is not performed.

The fixed baseline is weighted L2 logistic regression (`C=1`, threshold `0.5`).
The sensitivity model is a fixed `1280 -> 256 -> 64 -> 1` MLP with ReLU,
dropout `0.2`, AdamW, learning rate `0.001`, weight decay `0.0001`, 100 epochs,
batch size 256, and seed `20261109`. There is no early stopping, hyperparameter
search, or holdout-based adjustment. Both models are compared at the same
prespecified threshold.

Report complete source/train/holdout counts, positive and negative supports,
confusion counts, accuracy, sensitivity, specificity, precision, F1, AUROC,
average precision, Brier score, and ten-bin ECE. Record-level point estimates
are accompanied by 2,000 unstratified percentile bootstrap draws clustered by
patient/exact-waveform component. Invalid draws remain counted. Any estimate
from the holdout is descriptive and not a claim of independent validation.

## MIMIC-IV-ECG v1.0 scope

The only approved MIMIC use in this protocol is exploratory concordance with
the machine-generated diagnostic report text in `machine_measurements.csv`.
The dataset describes approximately 800,000 10-second, 12-lead, 500-Hz ECGs
from nearly 160,000 subjects. The source reports approximately 90.4 GB
uncompressed and a 33.8 GB ZIP. Its `report_0..report_17` columns are generated
by the ECG machine, not cardiologist-adjudicated labels. The free-text
cardiologist reports are linked separately to credentialed MIMIC-IV-Note and
are not included or used here. See the [official dataset page](https://physionet.org/content/mimic-iv-ecg/1.0/),
its [machine-measurement data dictionary](https://physionet.org/content/mimic-iv-ecg/1.0/machine_measurements_data_dictionary.csv),
and the [separate restricted ICD-label project](https://physionet.org/content/mimic-iv-ecg-ext-icd-labels/1.0.0/).

The report parser has five states: positive mention, explicit negative
mention, not mentioned, ambiguous mention, and missing report text. Not
mentioned is not negative. Only the first two states can enter a report
concordance comparison; all states and their denominators are reported. This
is not clinical accuracy or external clinical validation. No MIMIC report is
used for training, threshold selection, or recalibration.

MIMIC preflight has two distinct scopes. The metadata-only preflight verifies
the supplied manifest entries for metadata files, enforces a one-to-one
`record_list.csv`/`machine_measurements.csv` join, and counts report-mention
states without opening waveform files. It emits no performance metrics and is
not sufficient to unlock scoring. When an approved full source is available,
the separate full-source audit verifies every manifest entry, checks waveform
duration, sampling rate, canonical leads and declared mV units, and records
amplitude quantiles, exact-duplicate counts and technical exclusions. Only
that full-source receipt can be reviewed, committed, hash-pinned and consumed
by the GPU scorer. The scorer then checks the same source-manifest digest, the
committed full-source receipt, the frozen V3F checkpoint and the private
SPH-trained probe bundle. Its output contains aggregate concordance and
patient/exact-waveform-clustered intervals only.

MIMIC-IV-ECG v1.0 is openly accessible subject to its Open Data Commons ODbL
terms. However, CEDIA has not returned a readable per-user/project quota
limit. The full download is blocked pending quota and storage approval; no
MIMIC dataset has been found in the authorized project area, and none has been
downloaded or analyzed here. Space available on the shared filesystem is not
equivalent to the project's quota. The configuration keeps
`complete_download_authorized=false` and has no committed full-source control
receipt. The metadata-only job is implemented but has not been run because
its metadata inputs are absent; full-source audit and scoring remain gated.

## Privacy and claims

Embeddings, patient/record keys, exact waveform hashes, split assignments,
fitted weights, row-level predictions, MIMIC identifiers, and report text stay
in authorized CEDIA storage. The public repository may contain only protocol
and code, tests, sanitized receipts and hashes, aggregate counts/metrics, and
aggregate-only figures. Existing SPH results and the submitted manuscript are
not modified by this pilot.

## Runtime and execution receipts

Each CEDIA runner verifies the complete SHA-256 manifest of the protocol,
implementation, tests, and SLURM launchers before processing data. It rejects
dependency archives whose measured hashes differ from the protocol pins and
requires an exact runtime-component set for each job. Missing or extra
components fail closed; every required version is compared with the frozen
CEDIA Python, PyTorch, CUDA, NumPy, SciPy, h5py, or WFDB pins as applicable.
Public-safe receipts record the exact code/configuration commit, verified
runtime subset, and dependency archive hashes. Private embeddings, model
bundles, and row-level outputs remain outside Git.
