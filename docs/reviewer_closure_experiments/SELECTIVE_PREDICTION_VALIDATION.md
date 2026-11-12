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

### LUDB transport: measured effects and withheld positives

[The reference evaluation](../../outputs/results/reviewer_closure_experiments/ludb_fixed_policy_and_reference_aggregate.json)
produced 2,000 valid subject/exact-signal component bootstrap draws per
joint estimate. Coverage was 76.00% (95% interval 70.00-82.00%), and
abstention 24.00% (18.00-30.00%). The error unit below is a known
ECG-by-endpoint opportunity, not a whole-ECG diagnostic failure.

| Estimand | Error / opportunity count | Risk | Cluster 95% interval |
|---|---:|---:|---:|
| Baseline before withholding | 192 / 924 | 20.78% | 18.24-23.42% |
| Accepted ECGs only | 139 / 697 | 19.94% | 16.86-23.11% |
| Abstained ECGs, baseline counterfactual | 53 / 227 | 23.35% | 17.98-28.51% |

AURC was 0.1631 (0.1284-0.1980). For the common two-sided P8 AFIB, SB and
NSR endpoints, macro-F1 changed from 0.7075 to 0.7270, and mean binary
accuracy from 0.8257 to 0.8322, on the accepted subset. No P4 endpoint had
two reference polarities for this contrast. The modest point differences
and marginal intervals do not establish superiority on the entire release
or a clinical safety benefit.

| Endpoint | Positive refs | Emitted TP | Emitted FN | Withheld positive | Withheld baseline FN |
|---|---:|---:|---:|---:|---:|
| P8 AFIB | 15 | 11 | 1 | 3 | 1 |
| P8 NSR | 142 | 71 | 33 | 38 | 18 |
| P8 PAC | 7 | 0 | 4 | 3 | 1 |
| P8 STACH | 4 | 0 | 4 | 0 | 0 |
| P4 LVH | 108 | 33 | 49 | 26 | 20 |

Among accepted AFIB references, sensitivity was 11/12, specificity 134/137,
PPV 11/14 and NPV 134/135. On all eligible ECGs, only 11/15 AFIB positives
received a true-positive output. The 38/142 withheld NSR positives
contrast with 10/55 withheld records of other known principal rhythms
(and 0/3 among unknown principal rhythm). This is descriptive and does
not establish a population-level subgroup difference. The loss of output
on reference-positive ECGs is a cost, even when accepted-only metrics rise.
