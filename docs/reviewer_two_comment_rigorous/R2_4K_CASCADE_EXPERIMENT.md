# R2-4k: Executed partial P6 fallback

**EXPERIMENT_COMPLETED on LUDB** (CEDIA job 33796). Stage one reads the sealed P8/P4 scores and route. Every original abstention is routed to an actual new waveform preparation and inference through V3F and the released P6 specialist. Accepted ECGs are never scored again by the fallback. No labels enter selection or P6 inference. The output uses the published P6 thresholds without a top-1 override.

P6 completed on 48/48 original abstentions, with 0 fallback technical failures. At least partial coverage: 100.00%; complete original profile coverage: 76.00%, unchanged. Fallback adds only AFIB, SB, STACH, RBBB, 1AVB and PVC membership calls. P8 NSR/PAC and all P4 calls remain unresolved for those ECGs. No patient received review or referral.

| Strategy | Enrolled ECGs | Known opportunities emitted / original | Errors emitted | Known unresolved |
| --- | ---: | ---: | ---: | ---: |
| No abstention | 200 | 924/924 | 192 | 0 |
| Joint withholding only | 200 | 697/924 | 139 | 227 |
| Joint plus P6 fallback | 200 | 847/924 | 147 | 77 |

On the comparable fallback opportunities, it corrected **7** original errors and introduced **3** original errors. Final emitted FN: **103**; known positives still unresolved: **67**. Overall known emitted risk is 17.36%; this is not a full-denominator accuracy. Treating unresolved responses as pending at λ=.25 gives cost 17.99% on the original known denominator.

Incremental waveform preparation plus batch-one P6 latency on this allocation: median 0.452 s, p95 0.596 s, total 22.21 s. Model startup and the cached original primary runtime are not included. These timings are descriptive, not prospective service latency.

**Scope:** This is a new partial two-stage execution with a restricted ledger and sealed aggregates. The published P6 cutoffs were not calibrated for the subset rejected by the primary route. This is not the original system, not a complete pathology/rhythm cascade, and not evidence for June quarantine, referral effectiveness or clinical safety.
