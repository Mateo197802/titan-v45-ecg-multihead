# SPH label harmonization before model evaluation

Status: draft; no SPH model scores or performance have been examined. The
[machine-readable mapping](sph_label_harmonization.json) was checked against
the [official code dictionary](https://doi.org/10.6084/m9.figshare.17912507.v1)
and the [dataset methods](https://doi.org/10.1038/s41597-022-01403-5). Code
matching is a comparison of **documented ECG statements**, not a clinical
diagnosis or independent reading of every absent condition.

| Endpoint | SPH code | Disposition |
| --- | --- | --- |
| AFIB, SB, STACH, RBBB, PVC | 50, 22, 21, 106, 60 respectively | Defensible statement-level targets. AF is not incident; PVC is not beat-level; 105 is incomplete RBBB and is not a positive for 106. |
| PAC | 30 | Defensible for this documented statement. Code 31 denotes nonconducted atrial premature complexes and is not silently pooled into the primary endpoint. |
| 1AVB, NSR | 82, 1 respectively | Proxy only: prolonged PR and normal ECG are not the corresponding TITAN diagnoses. Any separate proxy analysis needs explicit naming and denominators. |
| ASMI, IMI, LVH | 165, 161, 142 respectively | Defensible as coded ECG statements. Acute/recent/old modifiers are not interchangeable; no reference to biomarker-confirmed infarction or imaging-confirmed hypertrophy. |
| ISC_ | 145/146 are candidates only | Not evaluable with those ST/ST-T codes. Do not report ischemia accuracy. |

Primary statements and modifiers must be parsed separately; multiple primary
statements may coexist. Retain all technically valid inputs independently of
their labels. If the reference uses absence of an eligible code as negative,
state that it means "the statement was not recorded", not adjudicated disease
absence. Preserve excluded or incompatible related statements as a separately
documented sensitivity issue rather than silently declaring them true negatives.

Do not report a full P6, P8 or P4 accuracy or compare against the historical
profile percentages: the reference ontologies differ and not every class is
evaluable. Publish support and performance for an explicit set of comparable
endpoints only, using a patient-cluster bootstrap. No thresholds, label
selection or preprocessing may be adjusted after examining performance.
