# Candidate external source audit

Checked 2026-11-08, without downloading candidate waveforms, individual labels,
reports or outcome metrics. This is an eligibility audit, not a reservation of
an accessible cohort or a claim of independence. No candidate below is currently
certified as a genuinely unseen final holdout for the V4.5-derived checkpoints.
SPH has already been observed and is development data for any V4.6 adaptation.

| Candidate | Verified availability and reference | Consequence |
| --- | --- | --- |
| [MIMIC-IV-ECG 1.0](https://physionet.org/content/mimic-iv-ecg/1.0/) | Open waveforms and machine-generated report lines. The `waveform_note_links.csv` file contains links, not cardiologist report text. The source describes a future release of the ECG report text. | Machine statements can support a clearly labelled agreement study, not silently become expert-adjudicated clinical truth. Historical V3F/V3AG exposure and signal overlap are not certified. |
| [MIMIC-IV-Note 2.2](https://physionet.org/content/mimic-iv-note/2.2/) | Credentialed access and DUA required. Its documented tables are discharge and radiology notes, not ECG reports. | Access to this version alone does not establish that cardiologist ECG reports can be obtained. |
| [MIMIC-IV-ECG 0.1](https://physionet.org/content/mimic-iv-ecg/0.1/) | Its documented beta included `reports.csv` cardiologist text, but PhysioNet states that this version's files are no longer available. | Do not claim that the reports are downloadable from the current project page; a lawful existing copy and permission would need separate confirmation. Beta identifiers and linkage must be verified before any use. |
| [MIMIC-IV-ECG-Ext-ICD 1.0.0](https://physionet.org/content/mimic-iv-ecg-ext-icd-labels/1.0.0/) | Credentialing, training and DUA required. It links ECGs to ED or hospital discharge ICD diagnoses by encounter timing. | A discharge diagnosis is not automatically the rhythm present in an ECG, an ECG-localized infarct, or a negative reference. Any usable clinical endpoint and temporal window require a separately fixed, clinically reviewed definition. |
| [KURIAS-ECG 1.0](https://physionet.org/content/kurias-ecg/1.0/) | PhysioNet currently reports that files are no longer available. Its standardized diagnoses are based on ECG-machine statements and the source reports category-balanced sampling. | Not an immediately accessible natural-prevalence independent clinical reference; no use without authorized access and validation of selection and mapping. |
| [PTB-XL](https://physionet.org/content/ptb-xl/1.0.3/) and [Chapman/Shaoxing/Ningbo](https://physionet.org/content/ecg-arrhythmia/1.0.0/) | These sources occur in the V4.5 release evidence, development or retained source audit. | Do not relabel them as unseen external-final data for the historical checkpoints. |

The public V4.5 [source-independence audit](https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/e0d35716db9270d8e04c2357d8f0bf949d465e52/docs/external_validation/sph_independence_assessment.md)
records incomplete backbone training and fine-tuning source manifests. Absence
of a source name in available files is not evidence that its records were never
used. A separate candidate institution does not resolve this limitation.

For a possible final source, availability, legal conditions, reference
semantics and historical exposure must be established; waveform duplicates
must be checked against all accessible development data, while inaccessible
historical inputs remain a disclosed uncertainty. Before any new model training,
select and reserve an admissible final source and freeze the evaluation design.
Do not inspect candidate final labels or outcomes to choose the source, its
population, thresholds, model, or reference definition. If no source can meet
these conditions, report that limitation; do not label SPH or a machine report
as an independent adjudicated test to fill the gap.
