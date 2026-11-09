# Data And Label Feasibility: BenchmarkMax

**Evidence snapshot:** 2026-11-09. This is a data-use and experiment-feasibility
record, not a manuscript revision or an external-validation claim.

## Current Sources

| Source | Availability / scale | Label and signal fit | Permitted role now |
| --- | --- | --- | --- |
| SPH V1 | Available in the authorized CEDIA workspace: 25,770 ECGs, 24,666 patients, 12 leads, 500 Hz, 10-60 s | Standardized AHA/ACC/HRS ECG diagnostic statements. The source paper says the original statements were checked by cardiologists and mapped to the standardized vocabulary. The V4.5 signal reader uses 10-60 s eligibility and expects no claimed mV conversion. | Exploratory V4.6 development/adaptation only. SPH was previously scored and inspected; no split within it is a new external test. |
| MIMIC-IV-ECG / ECG-Ext-ICD | No author access is known or confirmed as of this snapshot, per the user's answer. No restricted data were accessed. | Access and label semantics would need independent confirmation; discharge ICD diagnosis is not automatically the diagnosis present on a specific ECG. | Not available for this work unless an author obtains and documents authorized access. |
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
an LVH mechanism.

## Reproducible Development Split

`scripts/benchmarkmax/audit_sph_training_feasibility.py` assigns whole patients
deterministically to 70% train, 15% development, and 15% calibration-candidate
groups using a fixed SHA-256 namespace and seed. Labels are not used to assign
patients. The private report contains only source hash, aggregate record and
patient counts, and positive / not-recorded statement support per endpoint.
It exports no patient or ECG identifiers and is configured to refuse paths
inside either repository checkout. It does not define a test set and does not
change the fact that SPH is an already-observed development source.

The audit is a feasibility gate, not a training result. No training, threshold
selection, or candidate-model performance is reported until endpoint support
and the data contract are reviewed. Any internal split metrics will be labeled
development diagnostics, not external validation. The source's previously
reported V4.5 performance cannot be reused as V4.6 model-selection evidence
without explicit separation of development and calibration data.

## External Validation Gate

No source currently satisfies all of: authorized access, source and signal
independence from historical model training, patient-level separation,
compatible reference semantics for the exact endpoint, deduplication against
all accessible development data, and a frozen protocol before outcomes are
examined. Therefore no new external validation can be claimed now. A new
institutional cohort or separately authorized source is still required for a
confirmatory V4.6 claim. SPH adaptation, PTB clinical diagnosis, and beat-level
INCART/MIT-BIH results cannot be renamed to satisfy that requirement.
