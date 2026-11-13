# Other classes and original output support (R2-general)

The reviewer asked what happened to quarantine-cascade and auxiliary classes
and explicitly requested eight rhythm and three pathology classes. NSR is
reported distinctly as normal rhythm. It is not merged into Other arrhythmia
to create a more favorable metric. The full-denominator scoring flow is in
[R1-2](FULL_WORKFLOW_VALIDATION.md).

## Definitions and comparisons

- **Rhythm Other in SPH:** the [frozen ontology](../../configs/reviewer_experiments/november_rhythm_other.json)
  maps P6 Other to PAC, Flutter, complete LBBB, second-degree AV block
  (including explicit Mobitz I, Mobitz II and 2:1 statements), or complete
  third-degree AV block. P8 Other uses the same union without PAC, which
  already has a native P8 output. Neither union includes NSR, Paced or
  LQTS. Positive means at least one mapped code with no Normal ECG code;
  negatives are explicit Normal-only controls. Mixed Normal labels or
  discordant exact signals are ambiguous; other records stay unknown.
  These binary logistic heads use frozen scores, not deployed routing.
- **Pathology Other in PTB-XL:** the mapped union of ALMI, ILMI and the
  combined LAO/LAE statement is contrasted with explicit source-compatible
  controls. LAO/LAE is an operational composite in that one experiment.
  It is not a measurement of isolated clinical LAE. The
  [frozen ontology](../../configs/reviewer_experiments/november_pathology_other.json)
  requires a positive-likelihood target without NORM; controls are
  positive-likelihood NORM with no other statement except optional SR.
  Target with NORM or zero target likelihood is ambiguous, not negative.
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
The grouped LUDB reference has 19 P6 Other and 12 P8 Other positives,
but no compatible known negatives for either union. Thus it does not
independently validate the SPH grouped F1 values. The strict LUDB pathology
union ALMI/ILMI/LAE has no compatible references for any of the 200 ECGs.

| Requested endpoint | Scientific disposition and evidence | Remaining compatibility or deployment limit |
|---|---|---|
| NSR | Native P8 evaluated on LUDB: 142 positive, 55 alternative principal rhythms, three unknown | Principal sinus rhythm is not a disease-free ECG. Do not call NSR an arrhythmia |
| PAC | Native P8 evaluated against SPH statements; LUDB positive-only corroborates seven references; included in experimental P6 Other | Statement agreement is not beat-by-beat PAC detection |
| Flutter | SPH held new head F1 0.857, 19 positives; auxiliary comparator F1 0.013 | Small source-stratified positive support; new head not deployed |
| Paced | Evaluated in held PTB-XL fold 9 using the unchanged V3AG global output and a new development threshold; sensitivity 22/26 | No native P6/P8 Paced decision. Electronic pacing evidence is not wandering atrial pacemaker or historical independence |
| LBBB | SPH held new head F1 0.400, 18 positives; comparator F1 0.013 | Complete and incomplete block are distinct; no native P6/P8 action |
| 2AVB | SPH held experimental head F1 0.778, 10 positives; comparator F1 0.006. V3AG pooled PTB-XL rank also evaluated | No held V3AG binary estimate: one positive subject in fold 9; no published specialist decision |
| 3AVB | V3AG pooled PTB-XL rank evaluated on 14 positives and 1,699 explicit controls; LUDB has five positives only | No held V3AG binary estimate: two positive subjects in fold 9; SPH fit support failed |
| LQTS | Not evaluable: no authorized compatible direct syndrome reference for these models | Prolonged QT does not establish congenital LQTS; a published genotype cohort does not grant data access |
| ALMI | Frozen experimental head evaluated on PTB Diagnostic: F1 0.646; original auxiliary rank AUROC 0.6064 on the same references | Neither is a native P4 ALMI decision; clinical sensitivity remains limited |
| ILMI | Frozen experimental head evaluated on PTB Diagnostic: F1 0.579; original auxiliary rank AUROC 0.7309 on the same references | Keep inferior and inferolateral localization distinct |
| LAE | Rank-only: SPH original auxiliary AUROC 0.3037 on 19 explicit LAE statements and 13,905 Normal-only controls | Isolated clinical LAE or a calibrated LAE decision not evaluable; no substitution of LAO |

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
counts alone cannot assign performance to Paced or 3AVB. The separate
cache readout below uses the unchanged V3AG global head, not a recovered
binary specialist decision.

Cache inclusion was not uniform. The cache covers 6,205/19,601 eligible
ECGs (31.66%), but includes 252/252 Paced positives, 14/14 3AVB positives,
261/261 ALMI positives, and 426/482 complete LBBB positives. It contains
1,699/6,549 explicit Normal-only controls (25.94%), 10/29 PAC positives,
and 13/52 Flutter positives. Even within the known-reference
Paced/Normal contrast, the positive fraction is 252/1,951 in the cache
versus 252/6,801 in the eligible metadata. Cached PPV, NPV and precision-
recall estimates therefore cannot be interpreted at the original
PTB-XL reference prevalence or in a clinical all-comers population.

### Cached V3AG Paced and AV block evaluation

[Job 33747](../../outputs/results/reviewer_closure_experiments/ptbxl_cached_v3ag_rhythm_aggregate.json)
replayed the unchanged V3AG rhythm head on all 6,205 cached ECGs.
Sixteen archived probability columns agreed within a maximum absolute
error of 4.77e-7, below the frozen 1e-5 tolerance, before label joining.
The evidence proves the cached readout, not historical waveform replay.
No weights changed and no waveforms or fold-10 references were opened.

Folds 1-8 (5,410 ECGs) set the new threshold and fold 9 (795 ECGs)
assessed it. No patient or exact-signal group crossed those folds.
The held Paced contrast had 26 positive ECGs from 23 subjects and
190 controls from 188 subjects. The remaining 579 ECGs had unknown or
ambiguous reference states. At the frozen exploratory threshold
0.01818284, TP/FN/FP/TN were 22/4/35/155. Sensitivity was 0.8462
(cluster 95% interval 0.6571-1.0000), specificity 0.8158, PPV 0.3860,
NPV 0.9748, F1 0.5301 (0.3820-0.6437), AUROC 0.9136
(0.8468-0.9747), and AP 0.6436. The sensitivity and rank performance
do not imply high precision or calibration at population prevalence.

| Endpoint | Pooled descriptive AUROC (cluster 95% interval) | Pooled AP | Held positive subjects | Binary disposition |
|---|---:|---:|---:|---|
| Paced | 0.8636 (0.8369-0.8882) | 0.4715 | 23 | Exploratory held estimate above |
| 2AVB | 0.8028 (0.6701-0.8926) | 0.0222 | 1 | Below five-subject support rule; no threshold or held binary estimate |
| 3AVB | 0.8728 (0.7828-0.9554) | 0.1031 | 2 | Below five-subject support rule; no threshold or held binary estimate |

Pooled rank is descriptive, not an independent validation. Particularly
low AP for 2AVB and 3AVB must not be hidden by their AUROCs. This does not
change the released model or define a clinical route. See the
[generated tables](VERIFIED_ENDPOINT_AND_ROUTE_TABLES.md) and aggregate
for denominators and additional intervals.

### ALMI and ILMI transport with unchanged cutoffs

The [PTB Diagnostic transport](../../outputs/results/reviewer_closure_experiments/ptb_diagnostic_transport_aggregate.json)
compared original V3AG rank-only scores and separate PTB-XL-trained heads
on the same source-compatible subsets: 43 ALMI and 53 ILMI positives,
each against 80 explicit healthy-control ECGs. All 549 ECGs were scored;
426 ALMI and 416 ILMI references remained unknown. No target fitting
or threshold adjustment was performed.

| Endpoint | Original auxiliary AUROC (rank only) | Experimental head AUROC (cluster 95% interval) | Experimental fixed-threshold sensitivity | Specificity |
|---|---:|---:|---:|---:|
| ALMI | 0.6064 | 0.8997 (0.8408-0.9566) | 21/43 = 0.4884 | 79/80 = 0.9875 |
| ILMI | 0.7309 | 0.8807 (0.8085-0.9473) | 22/53 = 0.4151 | 79/80 = 0.9875 |

High rank discrimination did not translate into high sensitivity at the
transported cutoffs. Neither result establishes validated clinical
operating points. The original auxiliary outputs have no published binary
decision, and the fitted heads cannot be attributed to the original P4
specialist. The AUROC differences are descriptive, not paired confidence
intervals or significance tests for superiority.

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
