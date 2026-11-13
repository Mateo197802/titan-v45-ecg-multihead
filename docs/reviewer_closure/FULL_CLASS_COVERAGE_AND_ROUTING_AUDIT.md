# Full-Class Coverage and Routing Audit

This report separates the global neural output contract, specialist profiles, emitted scores, historical supervision, scored reference endpoints and operational route decisions. These are different evidence levels.

## Declared outputs versus specialist profiles

| Layer | Class count | Classes / interpretation | Evidence status |
| --- | ---: | --- | --- |
| Global rhythm head | 14 | P8 classes `AFIB`, `SB`, `STACH`, `NSR`, `RBBB`, `PAC`, `1AVB`, `PVC`, plus `Flutter`, `LBBB`, `2AVB`, `3AVB`, `LQTS`, `Paced`. | Declared in the verified contract; not proof of class-specific historical training support. |
| Primary6 (P6) rhythm specialist | 6 | `AFIB`, `SB`, `STACH`, `RBBB`, `1AVB`, `PVC`; excludes `NSR` and `PAC`. | Released diagnostic profile; V3H selection exposure applies. |
| Primary8 (P8) rhythm specialist | 8 | `AFIB`, `SB`, `STACH`, `NSR`, `RBBB`, `PAC`, `1AVB`, `PVC`. | Released candidate profile; does not pass the complete project gate. |
| Secondary rhythm stream | 6 | `Flutter`, `LBBB`, `2AVB`, `3AVB`, `LQTS`, `Paced`. | Scores emitted for selected records; no frozen action policy or complete historical supervision evidence. |
| Global pathology head | 7 | Primary4 labels `ASMI`, `LVH`, `IMI`, `ISC_`, plus `ALMI`, `ILMI`, `LAE`. | Declared contract; not evidence of checkpoint-linked supports or validation for all seven. |
| Primary4 (P4) pathology specialist | 4 | Binary panels for `ASMI`, `LVH`, `IMI`, `ISC_`. | Selected panel evaluation and separate SPH statement endpoints; not all-input pathology classification. |
| Auxiliary pathology stream | 3 | `ALMI`, `ILMI`, `LAE`. | Reconstructed inference emitted scores for 733 selected ECG; historical supervision, calibration and performance remain unverified. |
| `Other arrhythmia` / `Other pathology` | 0 validated outputs | No separate trained/calibrated/evaluated Other class is established. | Not available as validated output; do not infer it from NSR, score absence or fallback. |

The full contract is in [`global_head_contracts.json`](../../outputs/models/heads/global_head_contracts.json). The secondary class constants are in [`cascade/policy.py`](../../src/titan_v45/cascade/policy.py). Neither file establishes class training prevalence, historical loss-mask participation or clinical validity.

## Evaluation coverage and units

### Retained selected development evidence

- P6: 1,643 selected ECG.
- P8: 2,193 selected ECG, including the P6 set.
- P4: 962 binary panel observations across 733 selected ECG and 676 linked patients.
- The P8/P4 key union is 2,926 record keys, not a unique-patient count.
- Selected waveform replay recorded 58 P8 fallbacks and 476 NSR top-1 decisions. P6 had one top-1 disagreement against saved decisions; P8 top-1/binary sets agreed 2,193/2,193. P4 panel decisions agreed 962/962, but the maximum probability residual exceeded the frozen tolerance.

### Frozen SPH transfer

The validated aggregate reconciles 25,770 source ECG (24,666 source patients) per profile, with 14 compatible statement endpoints total: five P6, six P8 and three P4. It does not convert incompatible or absent codes to negative disease labels and does not report pooled full-profile clinical accuracy. See [`sph_results.md`](../external_validation/sph_results.md) and [the validation receipt](receipts/SPH_AGGREGATE_VALIDATION_2026-11-10.json).

| Profile behavior on 25,770 SPH ECG | Count | Meaning |
| --- | ---: | --- |
| P6 empty threshold sets | 16,785 | No class crossed its threshold. These cases are still scored; the empty label set is not quarantine. |
| P4 empty threshold sets | 8,343 | No pathology threshold crossed; not `Other` and not quarantine. |
| P8 forced top-1 fallback | 801 | A top-1 label is forced by the implemented fallback when the membership set is empty. It is not an abstention, quarantine or human referral. |
| P8 NSR top-1 | 16,700 | A normal-rhythm top-1 output. NSR is not an “other arrhythmia” class. |

All 25,770 source ECG were technically scored per profile in the frozen aggregate. Quarantine has zero assessed rows and a null rate; that means **not assessed**, not zero quarantine. Endpoint-level support and metrics must remain separate by class/profile.

## Current role and route semantics

The reconstructed waveform runners use fixed release weights, preserve the available thresholds, do not use reference labels for routing and attach `no_frozen_policy` to auxiliary streams. The selected reports classify the bookkeeping state as `quarantine_not_assessed`; this phrase does not mean a record was sent to an operational quarantine queue.

- P6 returns its thresholded multi-label set; it can be empty and does not force a binary membership fallback.
- P8 uses its thresholded membership set and forces the highest-scoring class when the set is empty; the result is marked as a fallback.
- P4 returns per-class binary threshold decisions; an empty set is possible.
- The six secondary rhythm and three auxiliary pathology scores have no frozen clinical action policy in this reconstruction.
- No score, role name or fallback proves that a clinician saw a record or changed an outcome.

The selected replay is explicitly labeled new reconstructed inference, not the historical June cascade. The complete workflow and its known denominator boundary are in [all-input flow coverage](ALL_INPUT_FLOW_COVERAGE.md) and [role/supervision evidence](ROLE_SUPERVISION_AND_ROUTING.md).

## Historical supervision status

For each auxiliary class, answer three separate questions:

| Evidence question | Rhythm secondary classes | ALMI / ILMI / LAE |
| --- | --- | --- |
| Is an output declared in the global contract? | Yes, six output dimensions. | Yes, three output dimensions. |
| Are scores emitted in reconstructed selected-cohort inference? | Yes, 2,193 P8 records in the retained rhythm run. | Yes, 733 selected P4 records in the retained pathology run. |
| Is class-specific supervision, support, calibration and evaluation linked to the checkpoint-producing historical run? | No. | No. |

A shape, config entry, candidate manifest, or emitted score cannot fill the last row. Do not claim that the auxiliary classes were trained/evaluated or have validated performance without the exact labels/masks, split manifests, run receipt and checkpoint hash link.

## What would close the remaining claims

1. A validated `Other` endpoint requires a defensible ontology, eligible labeled examples for every included class, explicit unknown/out-of-scope handling and a prespecified evaluation. Adding a label name after inference is not a model.
2. Historical auxiliary performance requires the actual run's training/validation manifests, masks and per-class supports, checkpoint/config/job link and stored metrics. If those cannot be recovered, only a new experiment can measure performance.
3. Operational cascade/quarantine performance requires one complete eligible-input denominator, frozen score/threshold/action policy, transition ledger, compatible reference, failures and patient-level uncertainty. Human-in-the-loop claims additionally need records of referrals, reviewer actions and outcomes.

The historical vs prospective quarantine boundary is detailed in [QUARANTINE_HISTORICAL_VS_PROSPECTIVE.md](QUARANTINE_HISTORICAL_VS_PROSPECTIVE.md).
