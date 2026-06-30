# Architecture

## Backbone

TITAN V4.5 uses 12 leads sampled to 125 Hz and fixed ten-second windows of 1,250 samples. A four-stage residual 1D encoder with channels `(96, 192, 384, 768)` feeds a Transformer with `d_model=640`, ten attention heads, and nine layers. Missing-lead masks and ten morphology features are explicit inputs.

The backbone has 58,352,219 parameters. Its state dictionary also contains 10,960 normalization-buffer elements, which are not parameters.

## Global Heads

- Rhythm: 14 logits.
- Pathology: 7 logits.
- Signal quality: 1 output.
- Biometrics: 3 outputs.
- ECG axes: rate/frequency, supraventricular irregularity, ectopy, conduction, and repolarization/QT.

## Operational Branches

The V3F rhythm branch and V3AG pathology branch use separately fine-tuned backbones. A profile bundle pairs the backbone hash, specialist hash, class contract, and threshold vector declared in its JSON profile and release manifest.

The classwise rhythm specialist has 4,909,720 parameters. The 512-unit pathology specialist has 2,432,244 parameters.
