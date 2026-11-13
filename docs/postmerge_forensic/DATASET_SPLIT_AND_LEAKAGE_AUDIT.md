# Dataset, split and leakage audit

The unit is not interchangeable: physical ECG, source person, overlapping
window, ECG-class panel and scored opportunity are different denominators.

| Experiment | Population and split | What the evidence does not prove |
|---|---|---|
| HIST-16768 | Archived account: 7,485 files enumerated, 9,945 windows; 9,021 + 924 windows. V3C excluded 390 by record_base. | File enumeration and exclusion by record key do not show what the loader consumed, subject isolation or exact/near waveform independence. |
| HIST-V3M | 9,885 train / 1,132 validation were recorded for the internal record-hash split. Conditional metadata reconstruction reports 206-207 overlapping persons train/validation and 165-166 train/internal panel, despite no same ECG IDs. | Not an actual consumed-manifest join; does not prove fold-10 contamination. See the [scoped R2-3a evidence](../reviewer_closure/REVIEWER_12_SCOPE_CLARIFICATIONS_2026-11-12.md). |
| RELEASE-P6/P8 | 1,643 and 2,193 selected ECG respectively; V3H was development/model-selection exposed, including the P6 sweep linkage. | No full original parent flow or source/person independence. P6 and P8 may share ECG. |
| RELEASE-P4 | 962 scored ECG-panel rows, 733 ECG, 676 subjects against official fold metadata; P4 selected fold 10. | No complete authenticated historical exposure log; not four diagnoses on 962 distinct patients/ECG. |
| SPH-FROZEN / ABSTENTION | 25,770 ECG, 12,901 coverage calibration and 12,869 held for the later policy. Patient and exact-waveform components kept together in that split. | Not proof of independence from all historical training or clinical negative adjudication. Later reanalysis used inspected results. |
| LUDB-TRANSFER | 200 source ECG/subjects, explicit reference mapping, no fitting; held-reference and technical status kept distinct. | Unknown nonreported endpoints are not negatives. No reliable cross-source linkage or clinical transport guarantee. |
| PTB-DIAGNOSTIC | 549 ECG from 290 source subjects. | Restricted named territory versus healthy-control analysis is not validation of all endpoints. |
| PTBXL-CACHE | 19,601 eligible fold 1-9 ECG, 6,205 scoreable, 13,396 not scored; coverage 31.66%. | Cache availability is not random; this study did not reopen fold 10. Cannot claim full-source inference. |
| STAGE-A / MORPH-ROBUST | Chapman record-as-patient proxy; official PTB-XL grouping and exact-signal grouping audit; morphology P4 uses folds 1-7 and separate fold-9 groups. | No definitive Chapman person linkage, and examined cohorts do not become confirmatory tests. |
| CODE-FULL | 345,779 publisher ECG / 233,770 patients; 43,187 sampled; 18,001 pre-score exclusions and 504 aligned-duplicate exclusions; 24,682 ECG / 17,300 patients analyzed. | CODE padding and observed lengths differ; selected benchmark is not all CODE and not certified historical independence. |
| ADAPTATION / RECOVERY / CORRECTIVE-PR15 | Within-CODE source-specific splits, separated calibration and evaluation; recovery development has 9,869 / 3,088 / 3,080 ECG for train/validation/calibration. | PR #6 eligibility predicate is not a direct comparison with its private held roster. Chapman groups are proxies; CPSC patient keys not certified. No independent institutional confirmation. |
| MIMIC-STRICT | Compatible strict reference support gate did not admit any two-sided target. | A missing statement is not a negative; no hidden patient-level outputs are republished. |

Publisher contracts: [PTB-XL v1.0.3](https://physionet.org/content/ptb-xl/1.0.3/),
[LUDB v1.0.1](https://physionet.org/content/ludb/1.0.1/),
[PTB Diagnostic v1.0.0](https://physionet.org/content/ptbdb/1.0.0/),
[CODE-15%](https://zenodo.org/records/4916206),
[MIMIC-IV-ECG v1.0](https://physionet.org/content/mimic-iv-ecg/1.0/),
and [SPH provider collection](https://doi.org/10.6084/m9.figshare.c.5779802).
Release-specific obligations and incomplete waveform source linkage are
recorded in [Stage A's source protocol](../specialist_heads/PROTOCOL_FREEZE_20261111.md).
These links are evidence of source definitions, not permission to
redistribute any private cache or linkage.
