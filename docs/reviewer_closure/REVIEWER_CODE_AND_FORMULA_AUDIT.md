# Reviewer Code and Formula Audit

**As of:** 2026-11-10. Equations below reproduce the current public reconstruction where identified. They do not prove that the unavailable historical loader, trainer or cascade used an identical implementation.

## Audited implementation paths

- [`backbone.py`](../../src/titan_v45/models/backbone.py) and [`factory.py`](../../src/titan_v45/models/factory.py): current 12-lead ResNet-1D + squeeze/excitation + Transformer implementation.
- [`features.py`](../../src/titan_v45/models/features.py): backbone rhythm softmax and specialist-feature concatenation.
- [`frozen_rhythm.py`](../../src/titan_v45/models/frozen_rhythm.py) and [`frozen_pathology.py`](../../src/titan_v45/models/frozen_pathology.py): frozen P6/P8/P4 tensor contracts and output aggregation.
- [`decision_policy.py`](../../src/titan_v45/evaluation/decision_policy.py): membership thresholds and P8 empty-set fallback.
- [`calibration.py`](../../src/titan_v45/training/calibration.py): current per-class binary threshold-grid objective.
- [`primary.py`](../../src/titan_v45/evaluation/primary.py) and [`metrics.py`](../../src/titan_v45/evaluation/metrics.py): top-1 reports, accuracy, macro-F1 and confusion counts.
- [`reconstructed.py`](../../src/titan_v45/data/reconstructed.py) and [`morphology_features_v4.py`](../../scripts/cedia/recovery_candidates/morphology_features_v4.py): explicitly reconstructed waveform and morphology paths.
- [`cascade/policy.py`](../../src/titan_v45/cascade/policy.py), [`run_rhythm.py`](../../src/titan_v45/cascade/run_rhythm.py) and [`run_pathology.py`](../../src/titan_v45/cascade/run_pathology.py): secondary output declarations and reconstructed audit behavior; these do not provide a verified historical quarantine/referral policy.

## Architecture and class contract

The factory constructs 12 input channels, 14 backbone rhythm logits and seven pathology logits; ten morphology features; a 640-dimensional Transformer representation; nine Transformer encoder layers with ten attention heads; and four convolution stages with channels `[96, 192, 384, 768]`. The 14 rhythm outputs comprise the P8 eight-class contract plus Flutter, LBBB, 2AVB, 3AVB, LQTS and Paced. The seven pathology outputs comprise Primary4 ASMI/LVH/IMI/ISC_ plus auxiliary ALMI/ILMI/LAE. A declared output dimension is not evidence that its target had historical training support or validated performance.

P6 contains AFIB, SB, STACH, RBBB, 1AVB and PVC; it excludes NSR and PAC. P8 contains AFIB, SB, STACH, NSR, RBBB, PAC, 1AVB and PVC. P4 contains ASMI, LVH, IMI and ISC_. NSR is sinus rhythm, not an `Other arrhythmia` class.

## Decision and metric equations in the current implementation

Let `z[w,k]` be specialist logit for window `w` and class `k`, `W` the number of windows, and `sigma(x)=1/(1+exp(-x))`.

**P6** aggregates the **mean logits** before sigmoid:

`mean_logit[k] = (1/W) * sum_w z[w,k]`

`score[k] = sigma(mean_logit[k])`

`labels = {k: score[k] >= threshold[k]}`

Top-1 is `argmax_k mean_logit[k]`. The current code can return an empty threshold set; it does not force a P6 binary label.

**P8** takes the **mean per-window sigmoid** membership scores:

`score[k] = (1/W) * sum_w sigma(z[w,k])`

`labels = {k: score[k] >= threshold[k]}`. If this set is empty, the current decision policy assigns the highest membership score as a forced top-1 fallback and marks `used_fallback`. This is not `Other`, abstention, quarantine or human review.

**P4** applies sigmoid to the specialist's four output logits and compares each probability against its frozen class-specific checkpoint threshold. Empty sets are possible; no P4 fallback is applied.

**Accuracy** in the current top-1 evaluator is `sum_i 1[y_i = yhat_i] / N`.

**Class F1** is `2 TP_k / (2 TP_k + FP_k + FN_k)`. Current macro-F1 is the unweighted mean across the declared classes; a zero denominator yields class F1 of zero. Do not interchange top-1 accuracy, macro-F1, mean binary accuracy, PPV or AUROC.

**Current threshold-tuning utility:** `tune_binary_thresholds` independently maximizes each class's binary F1 over 181 candidate thresholds from 0.05 through 0.95 in 0.005 steps. This is what the present utility code does; it is not proof of the historical threshold grid, data isolation or selection procedure for the released checkpoints. Historical thresholds remain unchanged.

## Input and feature contract: reconstruction versus history

The current replay contract prepares a `[12, 1250]` tensor at 125 Hz (ten seconds), applies a third-order 0.5-45 Hz Butterworth filter using causal `lfilter`, polyphase-resamples source signals as needed, z-scores each lead with a `1e-6` standard-deviation floor, and preserves an explicit lead-availability mask. Rhythm windows use the source-coded 10-second schedule with five-second stride and a terminal-window rule. P4 uses a fixed first ten seconds represented in a padded context. No physical mV conversion is inferred where source units are absent.

The morphology candidate returns ten normalized descriptors: median heart rate, RR coefficient of variation, RR RMSSD, QRS-width proxy, P-to-R proxy, QRS-band power ratio, low-frequency ratio, high-frequency ratio, mean absolute interlead correlation, and limb-lead QRS asymmetry. They are heuristic features, not clinically validated interval measurements. A separate rhythm-event feature stream has width 12. The expected original `data_loader_ultra.py` SHA-256 was not recovered; therefore this current contract is not the recovered historical loader.

## Supervision, cascade and limits

The class/output shape, auxiliary score emission and code constants do not by themselves prove historical supervised positives/negatives, loss-mask participation, calibration or accuracy for ALMI/ILMI/LAE or the six secondary rhythm outputs. The current cascade policy file declares class names/roles; reconstructed replay records no frozen quarantine action (`no_frozen_policy`). Historical pre/post quarantine remains `not assessed`, not zero.

The independent SPH evaluation reports 14 compatible ECG-statement endpoints on 25,770 ECG from 24,666 patients. A missing statement is not an adjudicated negative; SPH performance is not historical model training evidence. The exploratory PAC embedding probe uses a separately fitted logistic baseline and MLP sensitivity model on the same SPH source, with prior PAC target inspection; it is not the original V4.5 PAC head and not a clinical or independent validation result.

## Findings for editorial review

1. Describe P6, P8 and P4 as separate operational profiles/checkpoints, not one all-class classifier.
2. State P8 fallback, P6/P4 empty sets and quarantine as three distinct concepts.
3. Present formulae only after checking that the manuscript's historical method is supported; label this code audit as the current reconstruction.
4. Keep the P4 probability residual and P6 one-record decision mismatch visible; never round them into equivalence.
5. State which auxiliary outputs are declared, emitted, historically supervised and evaluated as separate evidence levels.

See [role, supervision and routing evidence](ROLE_SUPERVISION_AND_ROUTING.md), [loader identity and replay](HISTORICAL_LOADER_IDENTITY_AND_REPLAY.md), and [metric definitions](METRIC_DEFINITIONS.md).
