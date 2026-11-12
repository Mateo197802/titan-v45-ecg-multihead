# Duration-aware adaptation of TITAN V4.5

The historical release weights, CODE results and decision gate are immutable.
This study trains a different five-endpoint specialist initialized from the
verified V3F backbone. Its output is not interchangeable with the original six-
or eight-class profile and does not extend P4's reference coverage.

## Backbone and trainable components

- The original representation is the 640-dimensional waveform backbone. The
  specialist concatenates seven descriptors computed from observed samples and
  two duration indicators. A LayerNorm, 128-unit SiLU hidden layer, dropout and
  five sigmoid endpoints replace the downstream historical heads in this arm.
  The instantiated V3F module contains 58,352,219 parameters including its
  original heads. The adaptation module stores 58,437,362 parameters including
  those original, unused output heads and the new 85,143-parameter specialist.
  Stored parameters are not the same as trainable parameters in any arm.
- The frozen control updates only 85,143 specialist parameters. The partial
  arms additionally allow the last two Transformer blocks and final norm, or
  those plus the last ResNet block and token projection. Backbone modules keep
  inference-mode normalization statistics; selected affine weights can receive
  gradients. Learning rates are lower for pretrained blocks, with a quadratic
  penalty toward V3F, gradient clipping and validation-only early stopping.
- The masked MIMIC arm reconstructs withheld waveform blocks on approved train
  patients without reports or inferred negatives, then starts the same partial
  CODE fit. It does not use MIMIC to estimate diagnostic performance.
- The Chapman-only and joint CODE/Chapman/CPSC variants use frozen preflight
  inventories. CPSC is train-only because its patient grouping is unverified;
  unsupported endpoints are masked. The joint arm balances steps per source and
  reweights source losses with a registered GroupDRO update. Chapman and CODE
  cross-scoring is a development comparison, not new hospital confirmation.
- The full regularized arm is conditional. An architectural target is not a
  result; these arms are counted as executed only when their SLURM and training
  receipts agree and each checkpoint and curve digest verifies.

## Evaluation boundary

The [parent protocol](MULTISOURCE_TRAINING_PROTOCOL.json) fixes splits, budget,
seeds and the promotion gate. [Selection](SELECTION_PROTOCOL.json) is based on
validation macro-AUPRC and repeated finalists. Threshold selection for the
chosen specialist uses calibration only. The within-CODE comparison uses the
same ECG and publisher flags for the selected candidate and both released
profiles, with the released per-lead normalization and unchanged thresholds.
The paired uncertainty procedure resamples patient clusters. No model can be
promoted as institutionally generalizable on this evidence alone.

Stage A required a +0.02 F1 gain and capped sensitivity loss at 0.03. The
historical PR #6 gate raised the gain target to +0.03 and allowed up to 0.05
sensitivity loss; this is stricter on gain and more permissive on that
safeguard, not uniformly stricter. Those historical criteria are preserved.
This new study separately records the 0.70 research target, paired F1 gain,
precision and sensitivity safeguards, and Brier change. A within-CODE pass
does not substitute for independent institutional confirmation.

## Executed ablations before finalist selection

| Job | Variant | Trainable | Validation AP | Validation F1 (0.5) |
|---:|---|---:|---:|---:|
| 33692 | Frozen, per-lead | 85143 | 0.438601 | 0.417968 |
| 33693 | Frozen, robust shared gain | 85143 | 0.273308 | 0.298860 |
| 33694 | Partial Transformer, per-lead | 9933463 | 0.467045 | 0.452656 |
| 33696 | Partial Transformer + ResNet, per-lead | 16992199 | 0.550205 | 0.582790 |
| 33701 | MIMIC SSL warm start + partial Transformer | 9933463 | 0.473650 | 0.478860 |

All five jobs completed with exit code `0:0`. AP and F1 are macro averages on
the same five CODE validation endpoints at each arm's best validation AP epoch.
The ResNet arm improved validation F1 by 0.164822 over the per-lead frozen
control, so the insufficient-within-CODE-improvement condition for full fine-
tuning is not triggered. Cross-source forgetting and seed stability are distinct
checks. These are not held-out performance or evidence of promotion.

Job `33700` also completed masked waveform training on one ECG per patient
for 2048 MIMIC training patients, with no report or held-out waveform access.
Its masked reconstruction loss decreased from 0.311588 to 0.295683. This
checks the self-supervised objective, not diagnostic transfer. The receipt
and its [two-epoch trace](evidence/mimic_ssl/SSL_LEARNING_CURVES.csv) are
sealed separately from the downstream CODE supervised comparison.
The supervised warm start exceeded the corresponding Transformer-only arm by
0.006605 macro-AP and 0.026203 F1 in this initial seed, but did not beat the
Transformer plus ResNet arm. These differences are development observations,
not a paired statistical claim about transfer to another institution.

The frozen per-lead repeat `33713` (seed 20261114) gave AP 0.437878 and
F1 0.462163 on the same validation set. Its AP stayed close to the first seed
while F1 at the fixed threshold shifted. Finalists are compared with all three
registered seeds and only the sealed candidate is calibrated on the separate
calibration partition. The other frozen repeat's original `33712` attempt
was cancelled during dependency staging on compute-0-2 before model fitting
and completed unchanged as `33735` on compute-0-1. Across the three frozen
per-lead seeds the mean macro-AP was 0.439628 (population SD 0.001986) and
mean macro-F1 at threshold 0.5 was 0.442429 (population SD 0.018349).

The additional-source bank was completed by `33741` in 24m31s with exit
code `0:0`, after a four-reader staging attempt was stopped without a receipt.
The protocol and selection were unchanged when the input reader was scaled to
12 CPUs. Its [public receipt](evidence/ADDITIONAL_SOURCE_RECEIPT.json)
reconciles 4294 eligible of 4300 planned ECG: 1998 Chapman training, 700 Chapman
validation and 1596 CPSC training. Two Chapman and four CPSC candidates failed
signal-contract validation; the receipt retains exception classes, not finer
reason counts. No match crossed the frozen cosine criterion against 8280
comparable 10-second CODE bank windows before final duplicate pruning, and no
additional-source aligned matches were found. This is not a patient-linkage
audit and does not rule out time-shifted matches or matches involving a short
CODE signal. CPSC SB and STACH are fully masked; CPSC patient support is unknown.
Where a long raw record is center-cropped, its source statement may not localize
an episodic finding to the retained 10-second excerpt.

The [run table](evidence/TRAINING_EXPERIMENTS_COMPLETE.csv),
[learning curves](evidence/FINETUNING_LEARNING_CURVES.csv), and
[artifact manifest](evidence/EXPERIMENT_REPRODUCIBILITY_MANIFEST.json) can be
verified without access to ECG or model files:

```sh
python scripts/domain_adaptation/verify_adaptation_delivery.py docs/domain_adaptation/evidence
```

The GPU evaluator emits one sealed private paired prediction file. A separate
CPU job reduces it to public aggregates and patient-cluster uncertainty, so
rechecking statistical output does not trigger another holdout inference.

## Independent-source eligibility

[HEEDB v5](https://bdsp.io/content/heedb/5.0/) is a candidate, not an executed
cohort. Before acquiring data, the team must verify permission and storage in
CEDIA under the applicable data-use agreement. Emory's `diagnoses_acquisition.csv`
distinguishes `codes_software` from `codes_physician`; `diagnoses_v24.csv` is
the separate automated reprocessing export. `codes_physician` can include
original software codes as well as overreads; human reference status and
negative semantics must be established for the exact eligible ECG, not inferred
from the column name. The public [LUDB](https://physionet.org/content/ludb/1.0.1/)
is a useful technical audit candidate but cannot support all five endpoints at
the registered minimum of 20 positive and negative patients per class. For P4,
the exact ECG-level phenotype, timing and anatomical labels must be compatible;
history of infarction and nonspecific ischemia codes are not substitutes.
The authors reported that HEEDB access and CEDIA processing permission are not
confirmed. No download or evaluation was attempted for this source.
