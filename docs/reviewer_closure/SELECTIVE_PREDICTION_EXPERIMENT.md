# Selective Prediction and Quarantine Evidence

**Historical V4.5 quarantine:** `NOT_ASSESSED`; no authentic pre/post rate or effectiveness result is recoverable in the checked evidence.

**New selective-prediction experiment:** `NOT_RUN`.

## Historical behavior that is actually measured

- SPH P6 produced 16,785 empty threshold sets and P4 produced 8,343. These records were scored; empty membership is not an abstention or quarantine event.
- SPH P8 used 801 forced top-1 fallbacks. This is an algorithmic class assignment, not an uncertainty-based referral.
- The selected replay recorded 58 P8 fallbacks and 476 NSR top-1 decisions; neither quantity is a quarantine count.
- The SPH aggregate reports `quarantine_assessed_records = 0` and a null rate because no historical policy was frozen. Null means not assessed, not zero quarantine.

The codebase contains current quarantine utilities and a prospective workflow contract. Their presence does not establish that this policy was applied to the historical released checkpoints or population. See [`quarantine disposition`](QUARANTINE_HISTORICAL_VS_PROSPECTIVE.md) and [`routing provenance`](OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md).

## Evidence required to recover historical pre/post performance

The custodian would need to provide the checkpoint-linked uncertainty scores, exact policy/configuration and threshold, full eligible-input denominator, per-record pre/post route state and reason, inference failures, compatible reference labels, reviewer action/outcome if human review is claimed, job receipt and hashes. Without those, no historical quarantine rate, retained-population accuracy or error reduction is calculable from aggregates.

## Protocol for a future new experiment

Freeze the model/checkpoint, input population, uncertainty measure, threshold, coverage-risk curve, referral rules, endpoint, error-cost definitions and patient-clustered intervals before examining outcomes. Report coverage, abstention/referral rate, risk among retained cases, errors among referred cases, failures and the full denominator. If humans are in the loop, log blinded reviewer decisions, adjudication disagreements, time and downstream action; a model fallback alone is not human review. Publish aggregate results only.

Do not use this future experiment to claim that the historic V4.5 cascade/quarantine operated in the same way. Any such study is a new implementation and needs author/clinical protocol approval and eligible data.
