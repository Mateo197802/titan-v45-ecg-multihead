# Data And Label Feasibility: BenchmarkMax

**Evidence snapshot:** 2026-11-09. This is a data-use and experiment-feasibility
record, not a manuscript revision or an external-validation claim.

## Current Sources

| Source | Availability / scale | Label and signal fit | Permitted role now |
| --- | --- | --- | --- |
| SPH V1 | Available in the authorized CEDIA workspace: 25,770 ECGs, 24,666 patients, 12 leads, 500 Hz, 10-60 s | Standardized AHA/ACC/HRS ECG diagnostic statements. The source paper says the original statements were checked by cardiologists and mapped to the standardized vocabulary. The V4.5 signal reader uses 10-60 s eligibility and expects no claimed mV conversion. | Exploratory V4.6 development/adaptation only. SPH was previously scored and inspected; no split within it is a new external test. |
| MIMIC-IV-ECG 1.0 | Public download subject to ODbL 1.0. PhysioNet describes about 800,000 ten-second 12-lead ECGs at 500 Hz from nearly 160,000 subjects; about 5% were withheld. `machine_measurements.csv` contains machine-generated report lines, not adjudicated cardiologist report text. The PAC parser is implemented but has not been applied; no MIMIC files were downloaded or inspected. | Could support a separately frozen cross-source agreement analysis against machine statements. The current MIMIC-IV-Note 2.2 release documents discharge and radiology notes, not ECG report text. This is not a clinical reference. Historical V3F/V3AG exposure remains uncertified. | Candidate only; not selected or reserved as this study's final holdout. Use would require a frozen patient-level protocol, author-approved phrase mapping, license review, per-user storage confirmation, duplicate/source checks, and a model whose training lineage does not include this cohort. |
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

The audit is a feasibility gate, not the split or training result for the
separate PAC pilot below. A B1 calibration diagnostic was completed separately
on frozen V4.5 SPH scores: patient-grouped cross-fitting and threshold tuning
were performed, but no weights changed. This score-only analysis is exploratory
on previously observed SPH, not a trained candidate model or independent
validation; see the [B1 results](B1_SPH_CALIBRATION_RESULTS.md).
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
development/calibration for stable claims or a robust threshold estimate.

The table above predates waveform-level exact-duplicate exclusion. The frozen
post-dedup audit on CEDIA job `32815` now gives the stricter support counts for
new model development: all 25,770 source signals passed the technical signal
gate, but all 336 records participating in 168 exact-duplicate groups were
removed, leaving 25,434 ECGs from 24,509 patients. The audit cross-checked the
metadata supports against the source inventory and found no technical signal
exclusions. It did not inspect near-duplicates or run branch-specific model
preprocessing.

| Endpoint | Train records / patients | Development | Exploratory holdout | Total records / patients |
| --- | ---: | ---: | ---: | ---: |
| ASMI | 64 / 60 | 7 / 6 | 16 / 15 | 87 / 81 |
| IMI | 84 / 83 | 21 / 20 | 13 / 13 | 118 / 116 |
| LVH | 142 / 137 | 40 / 38 | 25 / 25 | 207 / 200 |
| PAC | 361 / 356 | 87 / 83 | 84 / 82 | 532 / 521 |
| PVC | 720 / 705 | 163 / 159 | 170 / 161 | 1,053 / 1,025 |
| RBBB | 512 / 480 | 81 / 76 | 101 / 94 | 694 / 650 |

ASMI and IMI have only 6 and 20 positive development patients, respectively;
LVH has 38. This is weak support for stable operating-threshold claims and
does not justify complex heads by itself. PAC, PVC, and RBBB have more support
for limited exploratory head comparisons, but their labels remain ECG
statements, and none of these splits is an independent test. Full denominators,
protocol, hashes, CEDIA job, and verification receipt are documented in the
[post-dedup results](SPH_POSTDEDUP_SUPPORT_RESULTS.md). The public JSON contains
aggregates only; identifiers remain in CEDIA.

The separate PAC pilot has now completed on CEDIA job `32805` under a frozen
protocol. Its population was 25,770 source records; 336 records in 168 exact
duplicate-signal groups were excluded before label join, leaving 25,434
eligible records. The patient-grouped, label-blind split contained 17,916
train records / 17,265 patients, 3,821 development / 3,686 patients, and 3,697
exploratory holdout / 3,558 patients. Holdout support was 84 code-30 statements
among 3,697 records. This is not the earlier feasibility split reported above;
the latter remains a separate support audit.

The frozen comparison used the CEDIA job-32668 V4.5 P8 PAC score as a
historical baseline, then fit one L2 logistic head and five prespecified MLP
seeds on frozen V3F mean+max embeddings. The baseline ledger and receipt
remain private and are hash-bound in configuration. New-head thresholds and
MLP early stopping used development data only; no winner was chosen from the
holdout. All 11 paired model comparisons used 2,000 patient-cluster bootstrap
replicates (seed `197813`), with no multiplicity adjustment. The public
[results report](SPH_PAC_HEAD_COMPARISON_RESULTS.md) links the aggregate,
verification receipt, and figure provenance. Patient IDs, row-level scores,
embeddings, signals and fitted head weights remain in CEDIA. CEDIA jobs
`32799`, `32800`, and `32802` failed on runner/configuration contract
mismatches; their private logs and hashes are preserved in the registry. Job
`32802` completed embedding and fit the logistic head, but its transient P8
and logistic holdout metric objects were neither emitted nor used for
selection; it failed before MLP fitting, bootstrap, or report writing. The
successful run followed code-to-config corrections without changing the
frozen endpoint or statistical choices. The feature builder does not persist
an SPH feature matrix.

The endpoint is the presence of SPH code `30` (“Atrial premature complex(es)”),
not adjudicated PAC disease; code `31` remains separate. The input pipeline
uses reconstructed 500 Hz to 125 Hz preprocessing and V3F mean+max temporal
embeddings; the historical loader was not recovered and equivalence is not
claimed. SPH amplitudes are not documented as mV and no physical amplitude
cutoff was applied. This experiment covers PAC only; it does not execute the
complete P6/P8/P4 profiles, full workflow routing, or quarantine analysis.
SPH was already observed in V4.5, so the holdout is exploratory development /
adaptation evidence, not independent, external, confirmatory, or clinical
validation. B1 remains a separate score-only calibration diagnostic, not a
trained candidate model; historical V4.5 metrics remain unchanged and are not
reported as V4.6 results.

## External Validation Gate

No source currently satisfies all of: authorized access, source and signal
independence from historical model training, patient-level separation,
compatible reference semantics for the exact endpoint, deduplication against
all accessible development data, and a frozen protocol before outcomes are
examined. Therefore no new external validation can be claimed now. A new
institutional cohort or separately authorized source is still required for a
confirmatory V4.6 claim. SPH adaptation, PTB clinical diagnosis, and beat-level
INCART/MIT-BIH results cannot be renamed to satisfy that requirement.
