# Specialist promotion: P6 and P8 fail the full CODE gate

The [completed 18-archive comparison](CODE15_FULL_EVALUATION.md) is the
promotion decision for PR #6. P6 changed from 0.428743 to 0.428104 macro-F1
(paired delta -0.000639, patient 95% CI [-0.006899, +0.004992]); P8 changed
from 0.449186 to 0.436388 (-0.012798, [-0.019583, -0.005406]). Neither met
the frozen +0.03 gain or positive lower confidence bound. Neither profile
is promoted. P4 remains not evaluable against CODE's reference. This is
a completed operational benchmark, not validation of a 10 s waveform
contract or historical patient independence.

## Historical first-archive checkpoint

| Profile | Published macro-F1 | Frozen linear macro-F1 | Delta (patient IC95%) | Decision |
|---|---:|---:|---:|---|
| P6 | 0.42739 | 0.43105 | +0.00367 [-0.02006, +0.02609] | Partial metric gate fails; no promotion |
| P8 | 0.44975 | 0.42912 | -0.02064 [-0.05135, +0.01250] | Partial metric gate fails; no promotion |
| P4 | Not evaluable | Not fit | Not applicable | No additional endpoint-valid reference |

The macro is the unweighted mean of AFIB, SB, STACH, RBBB and 1AVB, all
estimable within the first archive. Both linear candidates fail the observed
gain and paired lower-bound criteria. P8 also fails the sensitivity guard
(AFIB -0.11905); P6's largest observed decrease is -0.04762 (AFIB).
The macro Brier changes are -0.00003 (P6) and +0.00657 (P8); the empty-set
fraction changes are -0.02080 and -0.02774. Those do not compensate for the
failures. The [machine receipt](../../outputs/results/external_validation_20261111/code15-first/code15_evaluation_receipt.json)
records `INCOMPLETE_NO_PROMOTION`, not final FAIL on all 18 archives.

The independent verifier recomputed 20 class/model rows from private scores
and reproduced the frozen patient bootstrap. This does not resolve the
[duration discrepancy](GENERALIZATION_FAILURE_ANALYSIS.md) or certify
historical independence. Stage A's +0.02 F1 / -0.03 sensitivity limits
remain separate from PR6's +0.03 / -0.05 limits plus the paired interval,
calibration, coverage, and complete-support checks.

Do not substitute a development MLP into the locked comparison. No MLP
demonstrated superiority over the linear adapter in the [executed ablation](SPECIALIST_ABLATION_STUDY.md).
No model is promoted, no threshold is changed, and any later candidate
requires confirmation on a distinct, eligible, unexamined population.
