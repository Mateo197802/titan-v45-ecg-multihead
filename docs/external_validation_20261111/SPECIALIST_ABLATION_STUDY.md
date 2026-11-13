# Development-only specialist ablation

The [frozen design](FROZEN_DEVELOPMENT_ABLATION.json) was committed before any
CODE-15% outcome was read. CEDIA step `33296.1` fit residual MLPs with frozen
features and released decision thresholds. It compared source-balanced BCE
with asymmetric loss (negative focal gamma 2), using the same five supervised
endpoints. Chapman+CPSC supplied 8,415 training ECGs; Chapman validation
supplied 812 ECGs for epoch selection. The 1,097 Georgia ECGs were used only
for descriptive development transfer; this source was previously inspected
in Stage A. The paired intervals cluster by ECG record, not patient.
The shared CSV writer's `n_*_patients` columns therefore count record
surrogate groups in this CSV, not known distinct people.

| Profile | Published macro-F1 | Frozen linear | MLP BCE | MLP asymmetric |
|---|---:|---:|---:|---:|
| P6 | 0.77119 | 0.79849 | 0.78782 | 0.79921 |
| P8 | 0.77474 | 0.79701 | 0.78932 | 0.79278 |

The asymmetric loss reduced the largest class sensitivity loss versus the
released baseline in this development comparison: P6 0 instead of -0.023
for linear, and P8 -0.019 instead of -0.047. This does not establish generalization.
CEDIA step `33296.6` reloaded hash-verified checkpoints, reproduced all 60
published aggregate rows, and computed the following direct paired contrasts:

| Profile and loss | MLP minus linear macro-F1 (95% IC) |
|---|---:|
| P6 BCE | -0.01067 [-0.02275, -0.00082] |
| P6 asymmetric | +0.00071 [-0.01321, +0.01348] |
| P8 BCE | -0.00769 [-0.02350, +0.00774] |
| P8 asymmetric | -0.00424 [-0.02039, +0.01132] |

No MLP demonstrated improvement over the existing linear adapter. The P6
BCE variant performed worse in this comparison. No checkpoint is promoted
or substituted into CODE-15%. Neither CODE nor MIMIC was read for fitting or
selection. Partial backbone fine-tuning, MIMIC adaptation and GroupDRO were
not run; this head-only ablation cannot determine whether the backbone or
source labels cause the remaining errors. P4 has no additional admissible
endpoint-level reference here.

[Class metrics](../../outputs/results/external_validation_20261111/SPECIALIST_IMPROVEMENT_EXPERIMENTS.csv) ·
[Fit receipt](../../outputs/results/external_validation_20261111/DEVELOPMENT_ABLATION_33296_1.json) ·
[Replay receipt](../../outputs/results/external_validation_20261111/DEVELOPMENT_ABLATION_REPLAY_33296_6.json)
