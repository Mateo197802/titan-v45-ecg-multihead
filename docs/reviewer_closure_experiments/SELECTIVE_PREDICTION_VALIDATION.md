# Selective prediction, not historic quarantine (R2-4k)

**Historical disposition: `WITHDRAW_HISTORICAL_CLAIM`.** The historical
policy, eligible denominator and decision ledger are not jointly verified.
Do not report 0%, a threshold-empty percentage, or the Plan AE membership
fraction as an operational quarantine rate. This does not invalidate selected
historical classification results. There was no executed second stage or
human review in the new policy.

## Frozen policy and isolation

On a scoreable ECG the joint wrapper accepts only when both native P8 and
P4 confidence margins meet their frozen cutoffs (respectively
0.037162774801254295 and 0.014417142868041966). A failure to compute either
profile is a technical failure, not a clinical abstention. A scoreable ECG
failing either cutoff is withheld. References never control this decision.
For profile `p`, the margin is `min_c |score[p,c] - threshold[p,c]|`
over all native class thresholds. The signed joint margin is the minimum
of the two profile margins after subtracting the respective policy cutoff.
This is distance to a decision boundary, not a calibrated probability of
diagnostic correctness.
[The native SPH audit](../../outputs/results/reviewer_closure_experiments/sph_split_and_policy_audit.json)
rederived the original cutoff and verified zero shared patient, exact signal,
or connected component between 12,901 calibration and 12,869 held ECGs.
LUDB reuses this exact sealed policy with no target fitting.

- Coverage = accepted / eligible; abstention = abstained / eligible; these
  proportions plus technical non-scoring / eligible sum to one.
- Baseline risk uses known, scored endpoint opportunities before withholding;
  selective risk uses known opportunities among accepted ECGs only. AURC
  integrates error as coverage varies; the reported frozen operating point
  is not selected from that curve. Unknown references never enter accuracy,
  confusion counts or opportunity denominators.
- An emitted false negative is a known positive called negative among accepted
  ECGs. An abstained positive has no emitted classification; its
  counterfactual miss is computed from the score that would have been emitted
  without abstention. Do not treat these cases as corrected errors.

## Native route counts and matched estimates

| Source | Eligible | Accept | Abstain | Technical non-scoring | Coverage |
|---|---:|---:|---:|---:|---:|
| SPH held development | 12,869 | 10,391 | 2,478 | 0 | 80.74% |
| LUDB whole source | 200 | 152 | 48 | 0 | 76.00% |

[SPH 33414](../../outputs/results/reviewer_experiments/joint-selective_33414_aggregate.json)
reports a 19.26% abstention rate (patient-component 95% interval
18.55-19.89%), a mapped macro-F1 of 0.4555 before withholding and 0.4791
on accepted ECGs, and AURC 0.0871. The mean per-endpoint binary accuracy
was 0.9047 versus 0.9100 and the accepted risk on that mean was 0.0900.
The F1 difference (+0.0236; 95% interval +0.0189 to +0.0283) is conditional,
not improvement on the whole held cohort. For AFIB, 274/347 statement
positives had a true positive call, 10 had an emitted false negative and
63 had no prediction; 9 of the withheld positives were counterfactual
misses. For PAC the corresponding counts were 109/256, 69, and 78, with
35 counterfactual misses.

LUDB scoring and routing were sealed before opening the reference CSV. The
distinct transport result can characterize a frozen rule without proving
that the published weights never saw any overlapping historical patient or
that the rule is safe clinically. Risk comparisons across SPH and LUDB also
use different annotation contracts; they are not a pooled estimate.
