# Specialist Stage A: Source Generalization

This is a report of the frozen V2 development experiment. It is not a confirmatory external validation. See [the execution report](SPECIALIST_TRAINING_EXECUTION.md), [the frozen protocol](PROTOCOL_FREEZE_20261111.md), and [the sanitized per-class results](../../outputs/results/specialist_heads/20261111-v2/SPECIALIST_PER_CLASS_RESULTS.csv).

## Cohorts and comparison

| Profile | Evaluation source/scope | Records | Supported endpoints | Baseline macro-F1 | Fixed primary macro-F1 | Delta (95% paired CI) |
|---|---|---:|---:|---:|---:|---:|
| P6 | Georgia, Chapman+CPSC training to Georgia holdout | 1,097 | 6 | 0.7184 | 0.7204 | +0.0020 [-0.0261, 0.0297] |
| P8 | Georgia, Chapman+CPSC training to Georgia holdout | 1,097 | 7 | 0.6877 | 0.6902 | +0.0025 [-0.0251, 0.0298] |
| P6 | CPSC, Chapman+Georgia training to CPSC holdout | 1,681 | 3 | 0.9476 | 0.8394 | -0.1083 [-0.1254, -0.0909] |
| P8 | CPSC, Chapman+Georgia training to CPSC holdout | 1,681 | 5 | 0.8657 | 0.7275 | -0.1382 [-0.1581, -0.1183] |

The Georgia P6/P8 candidate was trained on Chapman and the training partition of CPSC; it was not tuned on Georgia. The separate CPSC sensitivity models were trained with Chapman and eligible Georgia records and evaluated on CPSC; they are not the same trained model as the Georgia-holdout candidate. Only endpoints with the required positive and negative support are scored. An unsupported endpoint is not imputed as a negative or assigned a zero metric.

The comparison uses baseline and candidate scores on the same source-specific records. The primary candidate and all thresholds were fixed using the protocol's train/validation/calibration partitions before the holdout scores were computed. Loss and seed ablations are retained descriptively; do not select or promote them by their Georgia/CPSC scores.

## Interpretation

Neither Georgia macro-F1 interval excludes zero. The CPSC sensitivity results are negative for both profiles, with paired record-level intervals below zero. These results do not support a generalization improvement from the new heads. Class-specific changes expose clinically important trade-offs that the macro average hides: P6 Georgia RBBB recall changes by -0.2533; P8 Georgia PAC by -0.0962; P6 CPSC RBBB by -0.2489; and P8 CPSC PAC by -0.4702. Complete class supports and metrics remain in the CSV.

Intervals for Georgia and CPSC resample ECG records, not patients, because validated patient keys were unavailable. The P4 PTB-XL internal evaluation has patient-grouped intervals but is not a source-held-out test. Do not compare these numbers directly to historical V3H/P6/P8 or the original manuscript metrics: cohorts, labels, thresholds and denominators differ.

## Independence ceiling

Byte-identical waveform checks found zero exact duplicate signal hashes among included records and no exact-signal cross-split overlap in PTB-XL. This does not rule out re-encoded/near-duplicate ECGs or cross-dataset patient overlap. The frozen V3F/V3AG backbone's exact consumed historical training manifests are not fully authenticated, and source exposure cannot be ruled out. Georgia and CPSC are development-source holdouts, not independent external or clinical cohorts. `INDEPENDENT_EXTERNAL_VALIDATION = NOT_RUN`.
