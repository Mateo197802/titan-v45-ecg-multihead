# PR #10 adaptation history

The [implementation and selection record](https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/63c74b3fde2c51f7f8cde4ad396d77a1bd16cb29/docs/domain_adaptation/DOMAIN_ADAPTATION_IMPLEMENTATION.md)
preserves failed or non-selected strategies. The [aggregate evidence directory](https://github.com/Mateo197802/titan-v45-ecg-multihead/tree/63c74b3fde2c51f7f8cde4ad396d77a1bd16cb29/docs/domain_adaptation/evidence)
includes source and preprocessing comparisons, all completed fits and seed
curves, calibration and threshold evidence, MIMIC train-only SSL receipt,
model hashes, job ledger and negative promotion checks. No full-depth
training was performed in this study because its gate did not trigger.
Only the preselected partial Transformer + ResNet was scored as the
candidate on the PR #10 reserved cohort.
