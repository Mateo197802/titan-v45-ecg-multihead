# Verified endpoint and route tables

Generated from the sealed CEDIA aggregates. NA means undefined, unassessed, or no applicable operating point, not zero. See the aggregates for full precision, cluster intervals where estimable, and calibration. No individual records are reproduced here.

## LUDB: actual joint routes and risk

| Measure | Denominator | Estimate | Cluster 95% interval | Valid draws |
| --- | --- | --- | --- | --- |
| Coverage | 152 / 200 ECGs | 0.7600 | [0.7000, 0.8200] | 2000 |
| Abstention | 48 / 200 ECGs | 0.2400 | [0.1800, 0.3000] | 2000 |
| Baseline error | 192 / 924 endpoint opportunities | 0.2078 | [0.1824, 0.2342] | 2000 |
| Accepted error | 139 / 697 endpoint opportunities | 0.1994 | [0.1686, 0.2311] | 2000 |
| Abstained baseline counterfactual error | 53 / 227 endpoint opportunities | 0.2335 | [0.1798, 0.2851] | 2000 |
| AURC, jointly scored | 200 ECGs in curve | 0.1631 | [0.1284, 0.1980] | 2000 |

Technical non-scoring: 0/200. No referral or human review.

| Reference principal rhythm | Eligible | Accepted | Abstained | Technical | Abstention fraction |
| --- | --- | --- | --- | --- | --- |
| AFIB | 15 | 12 | 3 | 0 | 0.2000 |
| Flutter | 3 | 2 | 1 | 0 | 0.3333 |
| NSR | 142 | 104 | 38 | 0 | 0.2676 |
| SB | 24 | 20 | 4 | 0 | 0.1667 |
| STACH | 4 | 4 | 0 | 0 | 0.0000 |
| other_specified_principal_rhythm | 9 | 7 | 2 | 0 | 0.2222 |
| unknown | 3 | 3 | 0 | 0 | 0.0000 |

| P8/P4 endpoint | Positive refs | Emitted TP | Emitted FN | Withheld positive | Withheld baseline FN | Technical positive |
| --- | --- | --- | --- | --- | --- | --- |
| P4:ASMI | 0 | 0 | 0 | 0 | 0 | 0 |
| P4:IMI | 0 | 0 | 0 | 0 | 0 | 0 |
| P4:ISC_ | 0 | 0 | 0 | 0 | 0 | 0 |
| P4:LVH | 108 | 33 | 49 | 26 | 20 | 0 |
| P8:1AVB | 10 | 2 | 5 | 3 | 2 | 0 |
| P8:AFIB | 15 | 11 | 1 | 3 | 1 | 0 |
| P8:NSR | 142 | 71 | 33 | 38 | 18 | 0 |
| P8:PAC | 7 | 0 | 4 | 3 | 1 | 0 |
| P8:PVC | 7 | 3 | 1 | 3 | 1 | 0 |
| P8:RBBB | 4 | 3 | 1 | 0 | 0 | 0 |
| P8:SB | 24 | 19 | 1 | 4 | 0 | 0 |
| P8:STACH | 4 | 0 | 4 | 0 | 0 | 0 |

## LUDB: matched contrasts and per-endpoint operating points

| Contrast | Common evaluated endpoints | Subset | Macro-F1 | Mean binary accuracy |
| --- | --- | --- | --- | --- |
| P4 | none | all_eligible | NA | NA |
| P4 | none | restricted_known_positive_profile | NA | NA |
| P6 | P6:AFIB, P6:SB | all_eligible | 0.6949 | 0.9188 |
| P6 | P6:AFIB, P6:SB | restricted_known_positive_profile | 0.8778 | 0.9237 |
| P8 | P8:AFIB, P8:SB, P8:NSR | all_eligible | 0.7075 | 0.8257 |
| P8 | P8:AFIB, P8:SB, P8:NSR | restricted_known_positive_profile | 0.7407 | 0.8316 |
| P8/P4 selective | P8:AFIB, P8:SB, P8:NSR | jointly_scored_baseline | 0.7075 | 0.8257 |
| P8/P4 selective | P8:AFIB, P8:SB, P8:NSR | accepted | 0.7270 | 0.8322 |

Rows in abstained or technical strata describe baseline counterfactual calls, not predictions emitted by the joint policy. Sensitivity with only positive references is descriptive.

| Endpoint | Subset | ECGs | Reference states | Known scored | TP/FN/FP/TN | Sens | Spec | PPV | NPV | F1 | AUROC | AP | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P4:ASMI | all_eligible | 200 | unknown: 200 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:ASMI | restricted_known_positive_profile | 108 | unknown: 108 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:ASMI | accepted | 152 | unknown: 152 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:ASMI | abstained | 48 | unknown: 48 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:ASMI | technical_unscored | 0 | none | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:ASMI | jointly_scored_baseline | 200 | unknown: 200 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:IMI | all_eligible | 200 | unknown: 200 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:IMI | restricted_known_positive_profile | 108 | unknown: 108 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:IMI | accepted | 152 | unknown: 152 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:IMI | abstained | 48 | unknown: 48 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:IMI | technical_unscored | 0 | none | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:IMI | jointly_scored_baseline | 200 | unknown: 200 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:ISC_ | all_eligible | 200 | unknown: 200 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:ISC_ | restricted_known_positive_profile | 108 | unknown: 108 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:ISC_ | accepted | 152 | unknown: 152 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:ISC_ | abstained | 48 | unknown: 48 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:ISC_ | technical_unscored | 0 | none | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:ISC_ | jointly_scored_baseline | 200 | unknown: 200 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:LVH | all_eligible | 200 | positive: 108; unknown: 92 | 108 | 39/69/0/0 | 0.3611 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P4:LVH | restricted_known_positive_profile | 108 | positive: 108 | 108 | 39/69/0/0 | 0.3611 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P4:LVH | accepted | 152 | positive: 82; unknown: 70 | 82 | 33/49/0/0 | 0.4024 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P4:LVH | abstained | 48 | positive: 26; unknown: 22 | 26 | 6/20/0/0 | 0.2308 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P4:LVH | technical_unscored | 0 | none | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P4:LVH | jointly_scored_baseline | 200 | positive: 108; unknown: 92 | 108 | 39/69/0/0 | 0.3611 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P6:1AVB | all_eligible | 200 | positive: 10; unknown: 190 | 10 | 5/5/0/0 | 0.5000 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P6:1AVB | restricted_known_positive_profile | 59 | positive: 10; unknown: 49 | 10 | 5/5/0/0 | 0.5000 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P6:AFIB | all_eligible | 200 | negative: 182; positive: 15; unknown: 3 | 197 | 13/2/6/176 | 0.8667 | 0.9670 | 0.6842 | 0.9888 | 0.7647 | 0.9890 | 0.8889 | evaluated |
| P6:AFIB | restricted_known_positive_profile | 59 | negative: 44; positive: 15 | 59 | 13/2/2/42 | 0.8667 | 0.9545 | 0.8667 | 0.9545 | 0.8667 | 0.9909 | 0.9758 | evaluated |
| P6:PVC | all_eligible | 200 | positive: 7; unknown: 193 | 7 | 6/1/0/0 | 0.8571 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P6:PVC | restricted_known_positive_profile | 59 | positive: 7; unknown: 52 | 7 | 6/1/0/0 | 0.8571 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P6:RBBB | all_eligible | 200 | positive: 4; unknown: 196 | 4 | 3/1/0/0 | 0.7500 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P6:RBBB | restricted_known_positive_profile | 59 | positive: 4; unknown: 55 | 4 | 3/1/0/0 | 0.7500 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P6:SB | all_eligible | 200 | negative: 173; positive: 24; unknown: 3 | 197 | 20/4/20/153 | 0.8333 | 0.8844 | 0.5000 | 0.9745 | 0.6250 | 0.9258 | 0.7081 | evaluated |
| P6:SB | restricted_known_positive_profile | 59 | negative: 35; positive: 24 | 59 | 20/4/1/34 | 0.8333 | 0.9714 | 0.9524 | 0.8947 | 0.8889 | 0.9679 | 0.9647 | evaluated |
| P6:STACH | all_eligible | 200 | negative: 193; positive: 4; unknown: 3 | 197 | 0/4/1/192 | 0.0000 | 0.9948 | 0.0000 | 0.9796 | 0.0000 | 0.6995 | 0.0533 | sparse_descriptive |
| P6:STACH | restricted_known_positive_profile | 59 | negative: 55; positive: 4 | 59 | 0/4/1/54 | 0.0000 | 0.9818 | 0.0000 | 0.9310 | 0.0000 | 0.6500 | 0.1324 | sparse_descriptive |
| P8:1AVB | all_eligible | 200 | positive: 10; unknown: 190 | 10 | 3/7/0/0 | 0.3000 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:1AVB | restricted_known_positive_profile | 188 | positive: 10; unknown: 178 | 10 | 3/7/0/0 | 0.3000 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:1AVB | accepted | 152 | positive: 7; unknown: 145 | 7 | 2/5/0/0 | 0.2857 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:1AVB | abstained | 48 | positive: 3; unknown: 45 | 3 | 1/2/0/0 | 0.3333 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:1AVB | technical_unscored | 0 | none | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P8:1AVB | jointly_scored_baseline | 200 | positive: 10; unknown: 190 | 10 | 3/7/0/0 | 0.3000 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:AFIB | all_eligible | 200 | negative: 182; positive: 15; unknown: 3 | 197 | 13/2/4/178 | 0.8667 | 0.9780 | 0.7647 | 0.9889 | 0.8125 | 0.9894 | 0.8978 | evaluated |
| P8:AFIB | restricted_known_positive_profile | 188 | negative: 173; positive: 15 | 188 | 13/2/1/172 | 0.8667 | 0.9942 | 0.9286 | 0.9885 | 0.8966 | 0.9950 | 0.9551 | evaluated |
| P8:AFIB | accepted | 152 | negative: 137; positive: 12; unknown: 3 | 149 | 11/1/3/134 | 0.9167 | 0.9781 | 0.7857 | 0.9926 | 0.8462 | 0.9921 | 0.9417 | evaluated |
| P8:AFIB | abstained | 48 | negative: 45; positive: 3 | 48 | 2/1/1/44 | 0.6667 | 0.9778 | 0.6667 | 0.9778 | 0.6667 | 0.9778 | 0.6389 | sparse_descriptive |
| P8:AFIB | technical_unscored | 0 | none | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P8:AFIB | jointly_scored_baseline | 200 | negative: 182; positive: 15; unknown: 3 | 197 | 13/2/4/178 | 0.8667 | 0.9780 | 0.7647 | 0.9889 | 0.8125 | 0.9894 | 0.8978 | evaluated |
| P8:NSR | all_eligible | 200 | negative: 55; positive: 142; unknown: 3 | 197 | 91/51/10/45 | 0.6408 | 0.8182 | 0.9010 | 0.4688 | 0.7490 | 0.7793 | 0.8568 | evaluated |
| P8:NSR | restricted_known_positive_profile | 188 | negative: 46; positive: 142 | 188 | 91/51/5/41 | 0.6408 | 0.8913 | 0.9479 | 0.4457 | 0.7647 | 0.8330 | 0.9249 | evaluated |
| P8:NSR | accepted | 152 | negative: 45; positive: 104; unknown: 3 | 149 | 71/33/8/37 | 0.6827 | 0.8222 | 0.8987 | 0.5286 | 0.7760 | 0.7957 | 0.8581 | evaluated |
| P8:NSR | abstained | 48 | negative: 10; positive: 38 | 48 | 20/18/2/8 | 0.5263 | 0.8000 | 0.9091 | 0.3077 | 0.6667 | 0.6868 | 0.8528 | evaluated |
| P8:NSR | technical_unscored | 0 | none | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P8:NSR | jointly_scored_baseline | 200 | negative: 55; positive: 142; unknown: 3 | 197 | 91/51/10/45 | 0.6408 | 0.8182 | 0.9010 | 0.4688 | 0.7490 | 0.7793 | 0.8568 | evaluated |
| P8:PAC | all_eligible | 200 | positive: 7; unknown: 193 | 7 | 2/5/0/0 | 0.2857 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:PAC | restricted_known_positive_profile | 188 | positive: 7; unknown: 181 | 7 | 2/5/0/0 | 0.2857 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:PAC | accepted | 152 | positive: 4; unknown: 148 | 4 | 0/4/0/0 | 0.0000 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:PAC | abstained | 48 | positive: 3; unknown: 45 | 3 | 2/1/0/0 | 0.6667 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:PAC | technical_unscored | 0 | none | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P8:PAC | jointly_scored_baseline | 200 | positive: 7; unknown: 193 | 7 | 2/5/0/0 | 0.2857 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:PVC | all_eligible | 200 | positive: 7; unknown: 193 | 7 | 5/2/0/0 | 0.7143 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:PVC | restricted_known_positive_profile | 188 | positive: 7; unknown: 181 | 7 | 5/2/0/0 | 0.7143 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:PVC | accepted | 152 | positive: 4; unknown: 148 | 4 | 3/1/0/0 | 0.7500 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:PVC | abstained | 48 | positive: 3; unknown: 45 | 3 | 2/1/0/0 | 0.6667 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:PVC | technical_unscored | 0 | none | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P8:PVC | jointly_scored_baseline | 200 | positive: 7; unknown: 193 | 7 | 5/2/0/0 | 0.7143 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:RBBB | all_eligible | 200 | positive: 4; unknown: 196 | 4 | 3/1/0/0 | 0.7500 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:RBBB | restricted_known_positive_profile | 188 | positive: 4; unknown: 184 | 4 | 3/1/0/0 | 0.7500 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:RBBB | accepted | 152 | positive: 4; unknown: 148 | 4 | 3/1/0/0 | 0.7500 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:RBBB | abstained | 48 | unknown: 48 | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P8:RBBB | technical_unscored | 0 | none | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P8:RBBB | jointly_scored_baseline | 200 | positive: 4; unknown: 196 | 4 | 3/1/0/0 | 0.7500 | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:SB | all_eligible | 200 | negative: 173; positive: 24; unknown: 3 | 197 | 23/1/35/138 | 0.9583 | 0.7977 | 0.3966 | 0.9928 | 0.5610 | 0.9448 | 0.7326 | evaluated |
| P8:SB | restricted_known_positive_profile | 188 | negative: 164; positive: 24 | 188 | 23/1/35/129 | 0.9583 | 0.7866 | 0.3966 | 0.9923 | 0.5610 | 0.9418 | 0.7326 | evaluated |
| P8:SB | accepted | 152 | negative: 129; positive: 20; unknown: 3 | 149 | 19/1/29/100 | 0.9500 | 0.7752 | 0.3958 | 0.9901 | 0.5588 | 0.9519 | 0.7830 | evaluated |
| P8:SB | abstained | 48 | negative: 44; positive: 4 | 48 | 4/0/6/38 | 1.0000 | 0.8636 | 0.4000 | 1.0000 | 0.5714 | 0.9205 | 0.5131 | sparse_descriptive |
| P8:SB | technical_unscored | 0 | none | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P8:SB | jointly_scored_baseline | 200 | negative: 173; positive: 24; unknown: 3 | 197 | 23/1/35/138 | 0.9583 | 0.7977 | 0.3966 | 0.9928 | 0.5610 | 0.9448 | 0.7326 | evaluated |
| P8:STACH | all_eligible | 200 | negative: 193; positive: 4; unknown: 3 | 197 | 0/4/1/192 | 0.0000 | 0.9948 | 0.0000 | 0.9796 | 0.0000 | 0.6567 | 0.0383 | sparse_descriptive |
| P8:STACH | restricted_known_positive_profile | 188 | negative: 184; positive: 4 | 188 | 0/4/1/183 | 0.0000 | 0.9946 | 0.0000 | 0.9786 | 0.0000 | 0.6658 | 0.0416 | sparse_descriptive |
| P8:STACH | accepted | 152 | negative: 145; positive: 4; unknown: 3 | 149 | 0/4/0/145 | 0.0000 | 1.0000 | NA | 0.9732 | 0.0000 | 0.6759 | 0.0536 | sparse_descriptive |
| P8:STACH | abstained | 48 | negative: 48 | 48 | 0/0/1/47 | NA | NA | NA | NA | NA | NA | NA | one_reference_polarity_only |
| P8:STACH | technical_unscored | 0 | none | 0 | NA | NA | NA | NA | NA | NA | NA | NA | no_known_scored_references |
| P8:STACH | jointly_scored_baseline | 200 | negative: 193; positive: 4; unknown: 3 | 197 | 0/4/1/192 | 0.0000 | 0.9948 | 0.0000 | 0.9796 | 0.0000 | 0.6567 | 0.0383 | sparse_descriptive |

## Reference coverage and supplementary results

PTB-XL source and cached references do not imply clinical ground truth. Subject counts per state are unique within state and must not be summed across states. Unmapped and proxy labels do not count as negatives.

| Endpoint | LUDB references (200 ECGs) | PTB-XL cached references (6,205 ECGs) | PTB-XL cached source subjects by state |
| --- | --- | --- | --- |
| NSR | negative: 55; positive: 142; unknown: 3 | non_equivalent_proxy: 4575; unknown: 1630 | non_equivalent_proxy: 4257; unknown: 1452 |
| PAC | positive: 7; unknown: 193 | ambiguous: 155; explicit_normal_control: 1699; positive: 10; unknown: 4341 | ambiguous: 149; explicit_normal_control: 1658; positive: 10; unknown: 3836 |
| Flutter | negative: 194; positive: 3; unknown: 3 | ambiguous: 7; explicit_normal_control: 1699; positive: 13; unknown: 4486 | ambiguous: 7; explicit_normal_control: 1658; positive: 9; unknown: 3969 |
| Paced | positive: 9; unknown: 191 | ambiguous_pacing_reference: 12; concordant_marker_unknown_scp_likelihood: 4; explicit_normal_control: 1699; positive: 252; unknown: 4238 | ambiguous_pacing_reference: 11; concordant_marker_unknown_scp_likelihood: 4; explicit_normal_control: 1658; positive: 201; unknown: 3771 |
| LBBB | positive: 4; unknown: 196 | explicit_normal_control: 1699; positive: 426; unknown: 4080 | explicit_normal_control: 1658; positive: 347; unknown: 3642 |
| 2AVB | unknown: 200 | ambiguous: 1; explicit_normal_control: 1699; positive: 12; unknown: 4493 | ambiguous: 1; explicit_normal_control: 1658; positive: 9; unknown: 3969 |
| 3AVB | positive: 5; unknown: 195 | explicit_normal_control: 1699; positive: 14; unknown: 4492 | explicit_normal_control: 1658; positive: 13; unknown: 3969 |
| LQTS | unknown: 200 | non_equivalent_proxy: 15; unknown: 6190 | non_equivalent_proxy: 14; unknown: 5573 |
| ALMI | unknown: 200 | explicit_normal_control: 1699; positive: 261; unknown: 4245 | explicit_normal_control: 1658; positive: 222; unknown: 3774 |
| ILMI | unknown: 200 | explicit_normal_control: 1699; positive: 278; unknown: 4228 | explicit_normal_control: 1658; positive: 253; unknown: 3755 |
| LAE | unknown: 200 | non_equivalent_proxy: 304; unknown: 5901 | non_equivalent_proxy: 290; unknown: 5323 |

PTB Diagnostic compares exact clinical territory with explicit healthy controls. PPV and NPV apply only to the enriched reference subset. Rank-only rows have no operational call.

| Territory | Score source | ECGs | Reference states | Known scored | TP/FN/FP/TN | Sens | Spec | PPV | NPV | F1 | AUROC | AP | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALMI | released_V3AG_rank_only | 549 | negative: 80; positive: 43; unknown: 426 | 123 | NA | NA | NA | NA | NA | NA | 0.6064 | 0.5355 | rank_only |
| ALMI | separately_trained_PTBXL_head | 549 | negative: 80; positive: 43; unknown: 426 | 123 | 21/22/1/79 | 0.4884 | 0.9875 | 0.9545 | 0.7822 | 0.6462 | 0.8997 | 0.8631 | evaluated |
| ASMI | released_P4_threshold | 549 | negative: 80; positive: 77; unknown: 392 | 157 | 63/14/20/60 | 0.8182 | 0.7500 | 0.7590 | 0.8108 | 0.7875 | 0.8489 | 0.8886 | evaluated |
| ILMI | released_V3AG_rank_only | 549 | negative: 80; positive: 53; unknown: 416 | 133 | NA | NA | NA | NA | NA | NA | 0.7309 | 0.7300 | rank_only |
| ILMI | separately_trained_PTBXL_head | 549 | negative: 80; positive: 53; unknown: 416 | 133 | 22/31/1/79 | 0.4151 | 0.9875 | 0.9565 | 0.7182 | 0.5789 | 0.8807 | 0.8643 | evaluated |
| IMI | released_P4_threshold | 549 | negative: 80; positive: 89; unknown: 380 | 169 | 66/23/21/59 | 0.7416 | 0.7375 | 0.7586 | 0.7195 | 0.7500 | 0.8136 | 0.8454 | evaluated |

PTB-XL cached V3AG rhythm: pooled rank estimates are descriptive. Held operating-point estimates appear only when both split supports passed. None of these operating points belongs to the published specialists.

| Endpoint | Held references | Held positive / control subjects | New threshold | Held TP/FN/FP/TN | Sens | Spec | PPV | NPV | F1 | AUROC | AP | Pooled AUROC | Pooled AP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2AVB | explicit_normal_control: 190; positive: 1; unknown: 604 | 1 / 188 | NA | NA | NA | NA | NA | NA | NA | NA | NA | 0.8028 | 0.0222 |
| 3AVB | explicit_normal_control: 190; positive: 2; unknown: 603 | 2 / 188 | NA | NA | NA | NA | NA | NA | NA | NA | NA | 0.8728 | 0.1031 |
| Paced | ambiguous_pacing_reference: 1; concordant_marker_unknown_scp_likelihood: 1; explicit_normal_control: 190; positive: 26; unknown: 577 | 23 / 188 | 0.018182838 | 22/4/35/155 | 0.8462 | 0.8158 | 0.3860 | 0.9748 | 0.5301 | 0.9136 | 0.6436 | 0.8636 | 0.4715 |
