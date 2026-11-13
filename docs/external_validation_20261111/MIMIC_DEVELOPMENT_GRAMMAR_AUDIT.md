# MIMIC machine-statement grammar audit: development only

Job 33316 joined the 5,770 fixed development ECGs (train, validation, calibration) to their machine statements and scanned all 18 report fields. It used no held-out ECG statements or model outcomes. The [aggregate JSON](../../outputs/results/external_validation_20261111/MIMIC_DEVELOPMENT_GRAMMAR_AUDIT.json) records counts and denominators. These are parser states, not estimates of diagnostic accuracy.

| Endpoint | Positive | Explicit negative | Ambiguous | Uncertain / historical | Unmentioned / unmapped |
|---|---:|---:|---:|---:|---:|
| AFIB | 214 | 0 | 196 | 15 | 5,345 |
| SB | 506 | 0 | 159 | 0 | 5,105 |
| STACH | 485 | 0 | 64 | 12 | 5,209 |
| RBBB | 166 | 0 | 15 | 0 | 5,589 |
| 1AVB | 0 | 0 | 0 | 0 | 5,770 |
| NSR | 0 | 0 | 0 | 0 | 5,770 |
| PAC | 1 | 0 | 0 | 0 | 5,769 |
| PVC | 5 | 0 | 4 | 0 | 5,761 |
| ASMI | 0 | 0 | 8 | 154 | 5,608 |
| LVH | 175 | 0 | 28 | 106 | 5,461 |
| IMI | 0 | 0 | 9 | 427 | 5,334 |
| ISC_ | 0 | 0 | 0 | 0 | 5,770 unmapped |

## What the parser missed

Examples below are generic, sanitized patterns, not copied patient reports.

| Pattern example | Evidence in development | Proposed disposition, not applied |
|---|---|---|
| `First degree A-V block` | 284 ECGs have the A-V pattern but 1AVB was unmentioned by the parser | Normalize the spelling and validate complete clause scope before accepting a positive. |
| `RBBB` | 165 abbreviation matches remain unmentioned | Validate whole-clause abbreviation use; distinguish incomplete RBBB and historical comparisons. |
| `Atrial fibrillation with [additional finding]` | 196 ambiguous and 12 uncertain cases under the compound pattern | Review safe suffixes separately; do not override negation, uncertainty or history. |
| `Sinus rhythm with [finding]` | 394 unmentioned for NSR | Sinus rhythm with a co-finding does not establish normal ECG. Do not upgrade to NSR automatically. |
| `Inferior infarct, age undetermined` | 387 historical-state cases under the matching pattern | Do not label as a current ECG manifestation without an accepted timing/target contract. |
| `Voltage criteria for LVH` | Two ambiguous matches to the audited voltage pattern | A voltage criterion is not automatically confirmed LVH. |

Expanding spelling and clause recognition can recover potential positive statements, but cannot produce a defensible negative reference. Any future MIMIC evaluation should validate a revised contract on independently reviewed development examples, lock it before the retained test, and either use explicit endpoint-compatible reference negatives or report a deliberately one-sided estimand. Generic silence remains unknown; this audit did not change thresholds, outcomes or any test label.
