# Quarantine: Historical Evidence vs Prospective Measurement

## Historical V4.5 evidence

No authentic historical record currently links all of the following to the released V4.5 checkpoints and their original eligible population:

- uncertainty score and its exact implementation/version;
- frozen threshold or action policy;
- per-record pre/post disposition and reason;
- complete input denominator and technical failures;
- compatible reference labels and post-action outcomes;
- job/config/checkpoint hashes proving which implementation ran.

Without these, the historical quarantine rate, pre-quarantine accuracy, post-quarantine accuracy, errors inside/outside quarantine, and effect of quarantine are not computable. The correct state is **not assessed**, not zero and not “all records passed.”

## What the available outputs mean

| Output | Observed count | Interpretation | Not equivalent to |
| --- | ---: | --- | --- |
| SPH P6 empty threshold set | 16,785 / 25,770 | No P6 class crossed its threshold. These cases are still scored; the empty label set is not quarantine. | Quarantine, `Other`, reviewer referral. |
| SPH P4 empty threshold set | 8,343 / 25,770 | No P4 pathology threshold crossed. | Quarantine, absence of pathology, referral. |
| SPH P8 forced top-1 fallback | 801 / 25,770 | Implemented fallback emits the highest membership score. | Abstention, quarantine, clinician review. |
| Selected P8 fallback | 58 / 2,193 | Same fallback rule on the selected development replay. | Original June quarantine rate. |
| Reconstructed selected replay state `quarantine_not_assessed` | 2,193 rhythm keys and 733 pathology keys | Explicit accounting state because no policy was applied or evaluated. | An action that moved ECGs into a real quarantine queue. |

In the SPH aggregate, zero records have quarantine assessment and the rate is null. Null records unavailable/not assessed; it must not be rendered as `0%`.

## Why the historical rate cannot be reconstructed

An aggregate prediction count cannot identify which original records entered a quarantine policy or their before/after outcomes. Empty sets and P8 fallbacks are model-decision behavior, while quarantine is a separate policy/action. No algebraic conversion can infer a quarantine denominator or recover reference labels for missing transitions. A quarantine file from another TITAN version or an unlinked experiment cannot be retroactively attached to V4.5.

The examined source ceiling is documented in [source triage](EVIDENCE_SOURCE_TRIAGE.md) and [recovered versus missing evidence](RECOVERED_VS_MISSING_HISTORICAL_EVIDENCE.md). The NOC checked a particular backup listing and did not find the requested historical directories, loader or Optuna database; that response does not prove absence from all institutional backups.

A separate legacy V4 May diagnostic has now been recomputed from its aggregate confusion matrix and error-subset routing totals. See [V4 May legacy quarantine disposition](V4_LEGACY_QUARANTINE_DISPOSITION.md) and its sanitized [recomputation receipt](receipts/LEGACY_V4_QUARANTINE_RECOMPUTATION_2026-11-10.json). It verifies only the 672-record Primary-9 aggregate and routing of 211 errors; it does not change the V4.5 June `NOT_ASSESSED` disposition above.

## Prospective workflow needed if the claim is retained

Freeze the design before evaluating any held-out outcomes:

1. **Target population:** eligibility, sources, ECG/patient unit, duplicate handling, exclusion reasons and original prevalence.
2. **Clinical reference:** ontology, source codes, positive/negative/unknown states, adjudication and how missing statements are treated.
3. **Frozen model package:** checkpoint hashes, code commit, preprocessing/loader, dependencies, class order and all thresholds.
4. **Frozen routing policy:** uncertainty score, threshold, empty-set/fallback/abstention/quarantine distinctions, human referral criteria and failure behavior.
5. **Complete ledger:** one row per eligible ECG stored privately, with pre-state, score, route, reason, post-state, reviewer action if any, timestamps and reference outcome. Publish only sanitized aggregate counts.
6. **Analysis:** complete denominator; coverage and failure rates; pre/post metrics using the same eligible set; errors inside and outside routes; PPV/NPV at the observed prevalence; patient-clustered confidence intervals; prespecified subgroup and duplicate sensitivity.
7. **Human-in-the-loop claim:** if asserted, record whether a clinician actually reviewed each routed ECG, the decision, disagreement/resolution, time and outcome. Routing alone is not human review, and reviewer study requires the appropriate approvals.

No such prospective experiment was started in this closure. It would be a new, explicitly labeled study, not a recovery or repair of historical V4.5 results. The cohort/protocol decision remains with the authors.
