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

## Independent-source eligibility

[HEEDB v5](https://bdsp.io/content/heedb/5.0/) is a candidate, not an executed
cohort. Before acquiring data, the team must verify permission and storage in
CEDIA under the applicable data-use agreement. Emory `codes_physician` contains
provider-described overread and automated coding; human reference status and
negative semantics must be established for the exact eligible ECG, not inferred
from the column name. The public [LUDB](https://physionet.org/content/ludb/1.0.1/)
is a useful technical audit candidate but cannot support all five endpoints at
the registered minimum of 20 positive and negative patients per class. For P4,
the exact ECG-level phenotype, timing and anatomical labels must be compatible;
history of infarction and nonspecific ischemia codes are not substitutes.
