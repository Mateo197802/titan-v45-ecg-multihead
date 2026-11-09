# Data And Label Feasibility: BenchmarkMax

**Evidence snapshot:** 2026-11-09. This is a data-use and experiment-feasibility
record, not a manuscript revision or an external-validation claim.

## Current Sources

| Source | Availability / scale | Label and signal fit | Permitted role now |
| --- | --- | --- | --- |
| SPH V1 | Available in the authorized CEDIA workspace: 25,770 ECGs, 24,666 patients, 12 leads, 500 Hz, 10-60 s | Standardized AHA/ACC/HRS ECG diagnostic statements. The source paper says the original statements were checked by cardiologists and mapped to the standardized vocabulary. The V4.5 signal reader uses 10-60 s eligibility and expects no claimed mV conversion. | Exploratory V4.6 development/adaptation only. SPH was previously scored and inspected; no split within it is a new external test. |
| MIMIC-IV-ECG 1.0 | Public download subject to ODbL 1.0. PhysioNet describes about 800,000 ten-second 12-lead ECGs at 500 Hz from nearly 160,000 subjects; about 5% were withheld. `machine_measurements.csv` contains machine-generated report lines, not adjudicated cardiologist report text. No waveforms or labels were downloaded or inspected for this project. | Could support a separately frozen cross-source agreement analysis against machine statements. The current MIMIC-IV-Note 2.2 release documents discharge and radiology notes, not ECG report text. This is not a clinical reference. Historical V3F/V3AG exposure remains uncertified. | Candidate only; not selected or reserved as this study's final holdout. Use would require a frozen patient-level protocol, license review, duplicate/source checks, and a model whose training lineage does not include this cohort. |
| MIMIC-IV-ECG-Ext-ICD 1.0.0 | Restricted PhysioNet credentialed access, required training and DUA. The user reports no known or confirmed author access. No restricted data were accessed. | Encounter-level discharge ICD labels do not automatically identify the diagnosis present on an ECG and do not provide ECG-localized MI or adjudicated negative labels. | Not available unless an author obtains and documents authorized access and a clinically defensible endpoint is approved. |
| PTB Diagnostic ECG Database | Public PhysioNet source; descriptor reports 549 conventional 12-lead ECGs and broad clinical diagnostic classes, including 148 subjects with MI and 7 with myocardial hypertrophy. | Broad clinical diagnoses are not equivalent to the specific ASMI/IMI/LVH ECG-statement targets. Repeated ECGs exist; split by subject. The historical V3F/V3AG pretraining exposure is not fully documented. | Candidate for a separately specified broad-diagnosis analysis only; not a presently admissible locked test for the existing endpoints. |
| INCART | Public PhysioNet source; 75 thirty-minute 12-lead excerpts from 32 Holter records, with more than 175,000 beat annotations. | Beat-level reference unit, source selection enriched for abnormalities, and small subject count. Not the record-level PAC/PVC endpoint used by TITAN. | Candidate only for a new beat-level exploratory module, not a substitute external test for P6/P8. |
| MIT-BIH Arrhythmia | Public PhysioNet source; 48 approximately 30-minute, two-channel records from 47 subjects with expert-reviewed beat annotations. | Stronger beat-level references for selected arrhythmias, but only two leads, small/selected cohort, and incompatible with the current 12-lead record-level contract. | Candidate only for a separately defined beat-level task after a new model/input contract; not a profile-level external validation. |
| PTB-XL, Chapman/Shaoxing/Ningbo, selected PhysioNet Challenge records | Already present in the V4.5 release, development evidence, or source audit; complete historical training-source exclusion is not certified. | Signal/source overlap and prior exposure cannot be excluded merely from a new split or a different directory name. The mixed `data_test` archive remains under its documented distribution hold. | Do not relabel as unseen final data for V4.5 or V4.6. |

## SPH Label Semantics And Rights

The SPH dataset has separate Figshare items for waveforms, metadata, and the
diagnostic dictionary. Their version-specific API metadata reported CC0 on
2026-11-09; see [the repository attribution record](../../data/licenses/SPH-CC0.md).
The dataset descriptor reports 25,770 records from 24,666 patients, collected
at SPH from 2019-08 through 2020-08, at 500 Hz. It describes 44 primary ECG
statements and 15 modifiers. The paper states that original Chinese statements
were checked by cardiologists and converted to the AHA/ACC/HRS vocabulary.
This is evidence for standardized ECG interpretation labels, not a guarantee
of independent adjudication for this model study, disease absence, acute-event
status, or clinical outcome truth.

The metadata contains patient and ECG identifiers, demographics, and diagnoses.
The labels are interpreted strictly as statements present on that ECG; a
missing target code is *not recorded*, not an adjudicated negative. The frozen
V4.5 preprocessing record says the waveform store does not provide physical
units in HDF5 attributes and applies no mV conversion. Thus an amplitude
perturbation is a sensitivity probe only, not proof of physical calibration or
an LVH mechanism. A label-blind 128-record probe found exactly unchanged P4,
P6 and P8 scores under uniform 0.5x and 2x scaling, consistent with the
lead-wise z-score normalization. This does not certify mV units or robustness
to per-lead gain changes, clipping, noise or other acquisition shifts; see the
[scale-sensitivity result](SPH_SCALE_SENSITIVITY_RESULTS.md).

## Reproducible Development Split

`scripts/benchmarkmax/audit_sph_training_feasibility.py` assigns whole patients
deterministically to 70% train, 15% development, and 15% calibration-candidate
groups using a fixed SHA-256 namespace and seed. Labels are not used to assign
patients. The private report contains only source hash, aggregate record and
patient counts, and positive / not-recorded statement support per endpoint.
It exports no patient or ECG identifiers and is configured to refuse paths
inside either repository checkout. It does not define a test set and does not
change the fact that SPH is an already-observed development source.

The audit is a feasibility gate, not a training result. No candidate specialist
has been trained or selected. A B1 calibration diagnostic was completed
separately on frozen V4.5 SPH scores: patient-grouped cross-fitting and
threshold tuning were performed, but no weights changed. This score-only
analysis is exploratory on previously observed SPH, not a trained candidate
model or independent validation; see the [B1 results](B1_SPH_CALIBRATION_RESULTS.md).
CEDIA CPU job `32754` completed this audit
from commit `90483f5`; the aggregate is
[`sph_training_feasibility_32754.json`](../../outputs/results/benchmarkmax/sph_training_feasibility_32754.json)
(SHA-256 `5df61dbf6af4d6b9b5da6d8962ebfebb0f166299f9cf27acfe8d69a874d0830e`).
It assigned 18,136 ECG / 17,368 patients to train, 3,889 / 3,718 to development,
and 3,745 / 3,580 to calibration-candidate, with zero patients crossing splits.

| Endpoint | Train positive records / patients | Development | Calibration-candidate |
| --- | ---: | ---: | ---: |
| ASMI | 68 / 61 | 7 / 6 | 16 / 15 |
| IMI | 86 / 84 | 21 / 20 | 13 / 13 |
| LVH | 144 / 138 | 40 / 38 | 25 / 25 |
| PAC | 365 / 358 | 89 / 84 | 85 / 83 |

These are source-statement supports, not candidate-model metrics. PAC has
enough positive support for a limited exploratory head pilot; LVH is marginal
for a reliable threshold claim; ASMI/IMI support is too sparse in
development/calibration for stable claims or a robust threshold estimate. The
current training CLI consumes precomputed NPZ features, while the repository
has no audited SPH feature builder or feature matrix. No V4.6 checkpoint or
trained candidate specialist exists. B1's calibration result is a score-only
diagnostic, not a trained model result; its interpretation and limitations are
reported separately. Any future within-SPH split metrics remain development
diagnostics, not external validation. The source's previously reported V4.5
performance will not be reused as a V4.6 test result.

## External Validation Gate

No source currently satisfies all of: authorized access, source and signal
independence from historical model training, patient-level separation,
compatible reference semantics for the exact endpoint, deduplication against
all accessible development data, and a frozen protocol before outcomes are
examined. Therefore no new external validation can be claimed now. A new
institutional cohort or separately authorized source is still required for a
confirmatory V4.6 claim. SPH adaptation, PTB clinical diagnosis, and beat-level
INCART/MIT-BIH results cannot be renamed to satisfy that requirement.
