# Evidence gaps and manuscript claim boundaries

This crosswalk is an evidence supplement to the original
[15-comment register](https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/4abb2de2bda3b3a2fa61b9418594690b5a3fc629/docs/reviewer_closure/REVIEWER_15_FULL_STATUS.csv)
(SHA-256 `01849f3cf60520cd8e2396308a3e7165821b860b20497baf3511102797a34028`)
and [40-subrequirement rubric](https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/4abb2de2bda3b3a2fa61b9418594690b5a3fc629/docs/reviewer_closure/REVIEWER_40_VERIFIED_SCORE.json)
(SHA-256 `275c28fa96d2429b4cbfca366196fd0fef195041a991a7a623d36f0fa7a8efa5`),
both pinned to the historical [PR #8](https://github.com/Mateo197802/titan-v45-ecg-multihead/pull/8).
The rows below use the eleven affected original identifiers, not new
rubric criteria. The other eleven comments are not reassessed here.
This phase does not change the rubric, weights, or scores.
See the [protocol](PROTOCOL_FREEZE.md) for literal scope and closure conditions
and the [execution register](CLOSURE_EXECUTION_REGISTER.md) for provenance.

| Historical subrequirement | Valid evidence and limit | Claim disposition |
|---|---|---|
| R1-2.1, eligible denominator for later SPH | 25,770/25,770 metadata entries scored by the frozen SPH workflow, not an independent study cohort; same-score nested comparisons. New LUDB scores reconcile 200/200 for each profile and show restricted-denominator differences for supported rhythm endpoints. | Preserve compatible-reference retrospective estimates and the full eligibility flow. No pooled whole-workflow diagnostic accuracy. |
| R1-2.2, June parent and exclusions | Selected P6/P8/P4 manifests and original panel counts do not recover the historical candidate population or exclusion order. | Restrict historical performance to its original selected denominator. New source populations cannot identify the June one. |
| R1-2.3, June quarantine pre/post and rate | No verified decision ledger links a historical policy and its eligible reference population. | `WITHDRAW_HISTORICAL_CLAIM`. Preserve independently supported historical classifier results. |
| R2-general.1, roles of declared outputs | Asset-specific V3F and V3AG loss/weight evidence and observed forward tensors. NSR is a P8 normal rhythm endpoint, not an arrhythmia residual. | Describe named outputs, direct training evidence and their scope. Presence of a head or a score is not a clinically usable class. |
| R2-general.2, classwise references or Other | Prior SPH and PTB-XL heads have bounded grouped results. LUDB and PTB Diagnostic add compatible NSR/territory comparisons; 33747 adds a held Paced operating point and descriptive AV-block ranks. | Every requested class has an explicit disposition. Do not equate rank with calibrated decisions, impute unsupported LAE/LQTS references, or claim a comprehensive deployed Other model. |
| R2-3f.1, candidate morphology | Exact formulas and hash, plus 200 runtime windows for the two backbones and all relevant global and specialist heads. | Can describe the source-backed reconstruction and actual tensor arrows; QRS and P-to-R remain proxies. |
| R2-3f.2, exact June loader | The candidate was verified, not authenticated as the historical import. | Do not assert exact original preprocessing or reproducibility. |
| R2-3f.3, replay under frozen tolerance | Same-execution November ledgers reproduce; 836/962 historical P4 scores outside tolerance, zero P4 threshold decisions changed, one P6 top-1 changed. | Record the non-equivalence; do not change the tolerance or select a repair by closeness to archived predictions. |
| R2-3f.4, hidden-width metadata | The pinned released P6/P8 state tensors are 512 wide although metadata says 192; strict tensor-shaped load observed, as was P4 width 512. | Can correct description of the executed release; not proof that an unrecovered June job used those exact loaded bytes. |
| R2-4k.1, historical quarantine denominator, policy and score | A threshold-empty P6/P8 set or fallback is not an abstention. Plan AE recorded reference membership, not a clinical routing event. | `WITHDRAW_HISTORICAL_CLAIM`; neither a positive rate nor 0% is supported for the original workflow. |
| R2-4k.2, SPH rate | 2,478/12,869 held SPH ECGs abstained under the newly defined joint policy. Reconstructed cutoff and subject/exact-signal split isolation are byte-verified. On LUDB, 48/200 abstained without refitting, with withheld positives separately accounted for. | Separate retrospective development and fixed-policy transport results. Neither proves historical use, clinical safety, or a general benefit. |

## What cannot be supplied by another rerun

- True population-level clinical sensitivity, specificity, and predictive
  values across all routes require representative, consecutively enrolled
  ECGs and explicitly adjudicated compatible positive and negative
  references. A mixture of independently selected releases is not that
  population. A new algorithmic cascade would be a separate system.
- Establishing historical patient separation requires historical lineage and
  compatible patient linkage. Within-cohort isolation and raw-byte
  duplicate checks cannot prove cross-provider person identity.
- Congenital LQTS is not a prolonged-QT statement. LAE is not LAO or an
  undifferentiated atrial-hypertrophy label. To claim those endpoints,
  require a source with explicitly compatible adjudication or exclude
  them from the diagnostic scope. A clinical version also requires
  sufficient negative references for class and route evaluation.
- Clinical quarantine effectiveness or human adjudication requires an
  actually executed, timestamped patient-level pathway with denominators
  and reference outcomes. Neither model confidence nor the retrospectively
  executed November abstention policy supplies those outcomes.
