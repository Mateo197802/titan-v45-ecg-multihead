# Historical evidence handoff

This document prepares later manuscript editing; it does not change the
submitted manuscript or constitute a reviewer response. SPH scoring is in
progress and no SPH result is included here. Historical development evidence
must not be described as a newly independent external validation.

## Canonical selected evaluations

| Profile | Unit and denominator | Historical result | Interpretation boundary |
| --- | --- | --- | --- |
| Primary6 rhythm | 1,643 selected ECG records | 1,564 top-1 correct; accuracy 95.19%; macro-F1 80.09% | Diagnostic selected profile; not full Primary8 and not independently validated by this table. |
| Primary8 rhythm | 2,193 selected ECG records | Accepted-rule accuracy 90.61%; macro-F1 76.14% | Candidate profile, not a passed full-profile gate. Its single-label accuracy is a different quantity. |
| Primary4 pathology | 962 binary panel observations, 733 unique record keys | Mean binary accuracy 80.23%; macro-F1 79.35% | Panel observations are not 962 distinct ECGs; project acceptance is not clinical validation. |

These values are recomputed from the versioned historical predictions by
`python scripts/evaluation/verify_release_evidence.py`. The same command
reports per-class counts and makes clear that it does not rerun ECG inference.
See [release evidence](../evidence-status.md), [selected waveform audit](../frozen-waveform-audit.md),
and [replay residuals](../replay-residual-diagnostics.md). Do not replace
canonical results with reconstructed replay outputs or omit their discrepancies.

## Known data and feature boundaries

| Evidence | Verified scope | Not established |
| --- | --- | --- |
| PTB-XL official metadata | 21,799 ECG and 18,869 patients; official fold 10 has 2,198 ECG and 1,904 patients. The P4 subset includes 733 ECG from 676 fold-10 patients; 1,465 fold-10 ECG are not in that subset. | The absence of an ECG from the selected panel does not identify a historical exclusion reason or prove training/calibration isolation. [Audit](../replay-residual-diagnostics.md). |
| Rhythm release cohort | 2,193 selected P8 records include multiple source labels; P6 is a 1,643-record diagnostic subset. | Source labels alone do not certify independent institutions or complete training lineage. [Attribution](../../data/licenses/README.md). |
| P4 specialist input | 670 features: 640 backbone, 10 morphology, 8 categorical rhythm probabilities, 8 specialist-order rhythm probabilities and 4 pathology probabilities. | A matching width does not establish historical identity of a reconstructed extractor. [Feature contract](../recovered-feature-contract.md). |
| P6/P8 specialist input | 681 features: 640 backbone, 10 morphology, 8 categorical rhythm probabilities, 7 specialist-order rhythm probabilities, 4 pathology probabilities and 12 event features. | The released checkpoints use 12 event features; proxies are not adjudicated clinical fiducials. [Feature contract](../recovered-feature-contract.md). |
| SPH processing | The frozen transfer protocol specifies 500 Hz source input, 125 Hz model windows and a 12-by-1,250 model tensor. | This is the reconstructed SPH processing contract, not proof of the unavailable historical loader. [Protocol](../external_validation/sph_protocol.md). |

## Claims and evidence boundaries

| Topic | Required treatment in the later manuscript |
| --- | --- |
| AF | Describe an AF-associated ECG statement, not incident AF or first diagnosis; see [reference contract](../af-reference-contract.md). |
| PVC | Preserve record-level versus beat-level distinction; do not claim beat-detection performance from record labels. |
| Cascade and Other | Distinguish measured selected-record transitions from the unavailable historical all-input flow; no validated Other output is established. |
| Quarantine | The historical patient-level policy and ledger are unavailable; an unassessed rate is undefined, not zero. |
| Backbone | P6 and P8 share V3F; P4 uses separate V3AG weights. See [waveform audit](../frozen-waveform-audit.md). |
| Features and replay | Identify the reconstructed loader and morphology as such; recovered code or matching decisions do not prove exact historical inference. |
| Split isolation | Historical training and calibration patient manifests are incomplete; do not assert complete patient-level separation. |
| Interpretability and readers | Do not claim clinically validated Grad-CAM, reader benefit, or measured human review without supporting studies. |
| A10 | Replace invalid placeholder hashes only with measured artifact-specific evidence; the missing generic predictions and Optuna database are not recovered. The separate [technical PR](https://github.com/Mateo197802/titan-v45-ecg-multihead/pull/4) contains the proposed disposition. |
| Data rights | The historical mixed archive remains on HOLD; public access to other assets does not grant redistribution rights for that archive. See [license evidence](../../data/licenses/README.md). |

The [48-item baseline](REVIEWER_48_STATUS.md) records individual dispositions.
It remains provisional until the frozen SPH run and its aggregate validation
are complete and the authors decide how to incorporate the evidence.
