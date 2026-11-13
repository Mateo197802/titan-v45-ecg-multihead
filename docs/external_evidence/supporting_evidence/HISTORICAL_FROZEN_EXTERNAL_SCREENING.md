# HISTORICAL_FROZEN_EXTERNAL_SCREENING

The [PR #6 frozen screening report](https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/85d673ac04986fe1c50a8cf39d8279344a708647/docs/external_validation_20261111/CODE15_FULL_EVALUATION.md)
evaluated 24,682 eligible CODE-15% ECGs from 17,300 patients, selected
by a different patient hash and a frozen waveform contract. It compared
released P6 and P8 with their frozen linear residual adapters, not the
PR #10 Transformer + ResNet candidate. P6 macro-F1 was 0.428743 vs 0.428104
with its adapter; P8 was 0.449186 vs 0.436388. Both adapters failed the gate.

Of the 24,682 ECGs, 24,578 had symmetric 581/581 zero borders. The frozen
contract admitted these short representations and excluded the unpadded
representation; it was not a validated 10-second acquisition contract.
An aligned-similarity rule removed 504 ECGs after scoring; this was not
patient deduplication. Available historical comparisons were incomplete.
PR #10 used duration-aware processing and a different patient-disjoint
sample. Do not subtract, pool or pair the metrics across these cohorts.
