# Other, auxiliary outputs, routing and quarantine provenance

**As of:** 2026-11-09. This disposition distinguishes declared outputs, emitted scores, trained targets, evaluated endpoints and operational decisions. Evidence for one layer does not prove the next.

## Output and profile contracts

The released model contract exposes 14 rhythm outputs and seven pathology outputs. The declared Primary8 rhythm profile contains AFIB, SB, STACH, NSR, RBBB, PAC, 1AVB and PVC. Primary6 is a six-class profile that excludes NSR and PAC. Primary4 is a four-pathology binary profile: ASMI, LVH, IMI and ISC_. These are implementation/output contracts, not proof that every output was trained, calibrated or evaluated in every historical checkpoint.

ALMI, ILMI and LAE appear as auxiliary pathology outputs in the global contract and can be emitted by the reconstructed P4 inference path. The available evidence does not establish checkpoint-linked historical positive/negative supervision, loss masks, class supports, calibration or performance for those three labels. Do not describe score emission as validated diagnosis or confirmed historical training.

NSR is sinus rhythm, not a rare arrhythmia. Its presence in the eight-class Primary8 output does not establish an `Other arrhythmia` class. Incompatible source references such as NSR, 1AVB or ISC_ remain outside a compatible endpoint unless a separately justified mapping exists. Missing scores are not negatives; absence of a coded statement is not adjudicated absence of disease.

## Measured software behavior

The selected reconstruction records 2,193 P8 keys and 733 P4 keys, with 1,643 P6 keys included within P8; this is a 2,926-key P8/P4 union, not a unique-patient count. The SPH transfer experiment scored all 25,770 source ECG under all three profiles and reported endpoint-compatible metrics without pooling incompatible references into false negatives. Its operational coverage is separate from the unavailable June historical parent population.

Under the current software contract, P6 can return an empty binary set when no threshold passes. P8 uses a forced top-1 fallback; the SPH run recorded 801 such fallbacks. The selected reconstruction recorded 58 P8 fallbacks and 476 NSR top-1 outputs. These are fallback or empty-set decisions, not a validated `Other` output, clinical quarantine, clinician review or a historical routing ledger.

## Quarantine evidence ceiling

No authentic V4.5 ledger links an uncertainty score, frozen quarantine policy/version, record-level pre/post state and evaluation denominator to the released checkpoints. The found `quarantine.py` files are code evidence, and the candidate legacy V4 quarantine files are not linked to V4.5 jobs or its full population. No pre/post quarantine rate or accuracy can be calculated.

Therefore, historical quarantine is **not assessed**, not 0%. Do not infer quarantine from P8 fallback, empty threshold sets, `cascade` role constants, or an unlinked uncertainty module. The SPH evaluation did not introduce or validate a quarantine policy; it records quarantine as not assessed.

The recovered CEDIA cleanup manifest contained no basename matching the requested quarantine-ledger or policy artifacts. This only means those names were not present in that inventory; the historical quarantine rate remains **not assessed**, not zero. See the [sanitized manifest receipt](receipts/CEDIA_CLEANUP_MANIFEST_TRIAGE_2026-11-10.json).

## What would support stronger claims

A new and explicitly labeled experiment would need a complete eligible-input denominator, compatible reference ontology, frozen policy and uncertainty score, record-level transition ledger, failure states, and patient-clustered metrics. To claim human review, it would additionally need a measured referral workflow and evidence of reviewer actions/outcomes. None of those missing historical records can be recreated from the selected panels or aggregate counts.
