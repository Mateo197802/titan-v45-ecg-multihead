# Other classes and original output support (R2-general)

The reviewer asked what happened to quarantine-cascade and auxiliary classes
and explicitly requested eight rhythm and three pathology classes. NSR is
reported distinctly as normal rhythm. It is not merged into Other arrhythmia
to create a more favorable metric. The full-denominator scoring flow is in
[R1-2](FULL_WORKFLOW_VALIDATION.md).

## Definitions and comparisons

- **Rhythm Other in SPH:** a known positive is a verified mapped non-primary
  rhythm for the named profile; known negatives in the experimental contrast
  are explicit Normal-only controls, not all remaining records. P6 includes
  PAC in its Other union; P8 already has a native PAC output. A missing or
  incompatible statement remains unknown. These binary logistic heads are
  post-study components on frozen scores, not deployed routing.
- **Pathology Other in PTB-XL:** the mapped union of ALMI, ILMI and the
  combined LAO/LAE statement is contrasted with explicit source-compatible
  controls. LAO/LAE is an operational composite in that one experiment.
  It is not a measurement of isolated clinical LAE.
- An original native decision, a released auxiliary score, an auxiliary
  comparator threshold fitted for a comparison, and a newly fitted head
  are separate estimands. See the [asset and loss audit](../reviewer_experiments/RELEASE_HEAD_SUPPORT.md).
  V3F's directly supervised rhythm subset is P8; P6 reports six of those
  targets. V3AG uses a different rhythm contract. Neither a vector index
  nor unrelated 41M auxiliary results authenticate a published head.

The [LUDB native result](../../outputs/results/reviewer_closure_experiments/ludb_fixed_policy_and_reference_aggregate.json)
adds a compatible normal-rhythm reference for P8 NSR. It also identifies
seven PAC, nine Paced, four LBBB and five 3AVB positives, but no
endpoint-compatible negatives for those four classes. For Flutter there
were only three positives (194 known alternative principal rhythms);
V3F auxiliary AUROC 0.1048 is a sparse descriptive rank, not a calibrated
decision. Lack of annotation is not counted as a negative for incidental
conditions or as evidence of an effective Other classifier.

| Requested endpoint | Verified prior evidence | Remaining compatibility or deployment limit |
|---|---|---|
| NSR | Published P8 decision; no verified SPH NSR reference | LUDB principal rhythm is distinct from Normal-only controls; do not call NSR an arrhythmia |
| PAC | Published P8 decision, also included in the experimental P6 Other union; SPH statement evaluation | Statement agreement is not beat-by-beat PAC detection |
| Flutter | SPH held new head F1 0.857, 19 positives; auxiliary comparator F1 0.013 | Small source-stratified positive support; new head not deployed |
| Paced | No compatible SPH label; original auxiliary scores are not published P6/P8 Paced decisions | Keep explicit electronic pacing distinct from wandering atrial pacemaker. PTB-XL PACE is a functioning-pacemaker statement, not a historical independence certificate |
| LBBB | SPH held new head F1 0.400, 18 positives; comparator F1 0.013 | Complete and incomplete block are distinct; no native P6/P8 action |
| 2AVB | SPH held new head F1 0.778, 10 positives; comparator F1 0.006 | Small development test; no published specialist decision |
| 3AVB | Prior support failed the training/calibration screen; LUDB publisher reports five positives | No unsupported fitted decision or negative controls inferred |
| LQTS | No authorized compatible source establishing the endpoint for these models | Prolonged QT does not establish congenital LQTS; a published genotype cohort does not grant data access |
| ALMI | PTB-XL held new head F1 0.900; original auxiliary rank AUROC 0.818 | Neither is a native P4 decision; PTB Diagnostic territory/control is a separate endpoint |
| ILMI | PTB-XL held new head F1 0.571; original auxiliary rank AUROC 0.869 | Keep inferior and inferolateral localization distinct |
| LAE | SPH original auxiliary AUROC 0.3037 on 19 explicit LAE statements and 13,905 Normal-only controls | Poor rank performance on that contrast, not calibration or clinical adjudication; no substitution of LAO |

The [SPH held experiment](../../outputs/results/reviewer_experiments/rhythm-other_33396_aggregate.json)
gave Rhythm Other P6 F1 **0.647** (141 positives among 2,895 known ECGs)
and P8 F1 **0.625** (43 among 2,797). The [PTB-XL held experiment](../../outputs/results/reviewer_experiments/pathology-other_33390_aggregate.json)
gave Pathology Other F1 **0.939** on 153 known of 390 held ECGs
(46 TP, 6 FN, 101 TN, 0 FP); 237 were unknown, including 109 called positive.
These counts cannot be interpreted as the full set of errors. The aggregates
retain endpoint support, intervals and calibration where estimable.

### PTB-XL reference availability, not performance

A [read-only CEDIA audit](../../outputs/results/reviewer_closure_experiments/ptbxl_other_support_verified_v2.json)
reconciled the same 19,601 fold 1-9 records (16,965 source subjects) and
6,205 scoreable cached ECGs with the sealed 33410 ledger. No fold 10
references or waveforms were used. For every requested class it records
positive, normal-control, unknown and ambiguous or proxy ECGs and unique
source subjects, both in all eligible records and in each scoreable profile.
Exact cached signal hashes did not cross official folds. These are metadata
counts, not clinical prevalence or performance.

| Reference in scoreable cache | Positive ECGs / subjects | Explicit normal controls (ECGs / subjects) | Scope |
|---|---:|---:|---|
| Paced | 252 / 201 | 1,699 / 1,658 | Positive-likelihood PACE and explicit active pacing marker; 4 additional concordant ECGs with unknown SCP likelihood and 12 ambiguous ECGs were not positives |
| 2AVB | 12 / 9 | 1,699 / 1,658 | Exact second-degree statement, not inferred from 1AVB |
| 3AVB | 14 / 13 | 1,699 / 1,658 | Exact third-degree statement; small positive sample |

Normal-only controls are a restricted negative contrast, not confirmed
absence among all other patients. PTB-XL contributed no compatible direct
reference for congenital LQTS, isolated LAE or strict NSR in this audit.
The original 33410 ledger does not contain V3AG global rhythm scores;
counts alone cannot assign performance to Paced or 3AVB.

### Reference sources considered

[LUDB](https://physionet.org/content/ludb/1.0.1/) permits a bounded transport
analysis of compatible statements; it does not provide confirmed negatives
for all incidental diagnoses. [PTB Diagnostic](https://physionet.org/content/ptbdb/1.0.0/)
has exact infarct territory and explicit healthy controls, not an isolated
LAE reference. [PTB-XL's dictionary](https://physionet.org/content/ptb-xl/1.0.3/scp_statements.csv)
defines PACE; the earlier bridge is a development subset, with fold 10
locked. The [genotype-confirmed LQTS study](https://jamanetwork.com/journals/jamacardiology/fullarticle/2815659)
illustrates the required reference; [THEW LQTS Holter data](https://pmc.ncbi.nlm.nih.gov/articles/PMC10213876/)
use two or three channels and do not establish compatibility with the
frozen 12-lead specialist operating point.

These tests justify explaining the exclusions and reporting bounded new
results. They do not justify presenting an all-11-class Other diagnosis or
pooling dissimilar cohorts into an unbiased prevalence estimate.
