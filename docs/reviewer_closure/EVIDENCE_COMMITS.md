# Evidence and revision traceability

This index records where evidence was introduced, not reviewer acceptance.
The [48-item index](REVIEWER_48_STATUS.md) is a technical disposition; an experiment
is not closed merely because supporting code or documentation exists.

| Scope | Public change | What it establishes | Remaining boundary |
| --- | --- | --- | --- |
| Earlier revision evidence | [PR #1, merge `79af292`](https://github.com/Mateo197802/titan-v45-ecg-multihead/pull/1) | Versioned recovery and reviewer evidence. | Does not recover every historical input or establish independent validation. |
| Replay diagnostics and fold coverage | [PR #2, merge `2677a33`](https://github.com/Mateo197802/titan-v45-ecg-multihead/pull/2) | Quantified replay residuals and official PTB-XL fold coverage. | Official fold assignment is not a recovered training manifest. |
| SPH source inventory | [PR #3, `fc8a839`](https://github.com/Mateo197802/titan-v45-ecg-multihead/commit/fc8a839) | Versioned source-only aggregate from CEDIA job 32617. | Source integrity is not model performance. |
| Duplicate/amplitude controls | [PR #3, `93e9423`](https://github.com/Mateo197802/titan-v45-ecg-multihead/commit/93e9423) and CEDIA job 32627 | Exact-signal duplicates and native amplitude audit. | No physical unit conversion is certified; see the [receipt field clarification](../external_validation/sph_control_receipt_correction.md). |
| Cross-source screen | [PR #3, `f3fe2bc`](https://github.com/Mateo197802/titan-v45-ecg-multihead/commit/f3fe2bc) and CEDIA job 32633 | A bounded signature screen against retained release cohorts. | Missing historical inputs prevent certifying complete independence. |
| SPH preregistration | [PR #3, `0767d78`](https://github.com/Mateo197802/titan-v45-ecg-multihead/commit/0767d78), amended [before performance in `eb1c67b`](https://github.com/Mateo197802/titan-v45-ecg-multihead/commit/eb1c67b) | Frozen model, mapping, preprocessing, endpoints and exact checkpoint threshold. | Amendment fixes representation of a saved threshold, not model selection. |
| SPH scoring | [PR #3, `acd2095`](https://github.com/Mateo197802/titan-v45-ecg-multihead/commit/acd2095), [receipt](../../outputs/results/external_sph/scoring_receipt_32668.json), CEDIA job 32668 | Complete label-blind scoring flow and input hashes. | Coverage is not accuracy; individual predictions remain restricted. |
| SPH aggregation and checks | [PR #3, `1f91c67`](https://github.com/Mateo197802/titan-v45-ecg-multihead/commit/1f91c67), CEDIA jobs 32669 and 32672 | Aggregate, figures, receipt chain and independent point-metric recomputation for 14 endpoints. | Bootstrap intervals use the documented ECE correction; historical source independence is not certified. |
| A10 and Optuna | [PR #4, `ec7d472`](https://github.com/Mateo197802/titan-v45-ecg-multihead/commit/ec7d472) | Separate measured checkpoint hashes, missing-artifact disposition, and tests. | PR remains open; Optuna's original complete database and promotion linkage are not recovered. |

The public PR state and CI must be rechecked at delivery. Neither a green
software check nor a commit substitutes for an editorial or clinical decision.
