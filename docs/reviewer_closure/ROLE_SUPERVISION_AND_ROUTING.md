# Role, supervision and routing evidence

This is a technical disposition for R2-3c, R2-3d, R2-3e, R2-4e,
R2-general and R2-4k, not a reviewer response or proof of editorial acceptance.
The three evidence levels below must not be substituted for one another.

## A. Implemented architecture and decision contract

The [published head contract](../../outputs/models/heads/global_head_contracts.json)
declares 14 backbone rhythm outputs: eight P8 classes plus Flutter, LBBB, 2AVB,
3AVB, LQTS and Paced. Its seven pathology outputs comprise ASMI, LVH, IMI,
ISC_, ALMI, ILMI and LAE. The specialist P4 decision contract contains the
first four pathology classes; the last three are auxiliary backbone outputs in
the reconstructed scoring path. A declared output or named `cascade` constant
does not establish an independently trained specialist or a clinical referral.

P8 includes NSR and PAC; P6's six-class view excludes both. NSR denotes sinus
rhythm, not an arrhythmia category simply because it is a rhythm-model output.
When no threshold passes, the implemented [P6 aggregation](../../src/titan_v45/models/frozen_rhythm.py)
returns an empty binary set while still computing a top-1; P8's
[membership rule](../../src/titan_v45/evaluation/decision_policy.py) forces
the highest-scoring label and marks `used_fallback`. This is a software rule,
not a validated Other class, quarantine decision, or human review.

## B. Historical supervision and selection

Recovered code supports loss and masking paths, and checkpoints provide
architecture and output contracts. Those facts do not prove that every
declared auxiliary class was supervised with sufficient positive examples in
the particular historical run producing a released checkpoint. In particular,
the available evidence does not establish checkpoint-linked training supports
for ALMI, ILMI and LAE. An unlinked candidate manifest is not a substitute for
the missing run-specific inputs and receipt. See the
[data disposition](../revision-data-dispositions.md) and
[recovered feature contract](../recovered-feature-contract.md).

Reopening requires the exact training and validation manifests, per-class
labels/masks and supports, configuration, job log and cryptographic linkage to
each released checkpoint. Do not infer supervision from score presence, tensor
width, a declared role or a configuration alone.

## C. Observed reconstructed decisions

The [selected waveform replay](../../outputs/results/revision_20261107/rhythm_waveform.json)
scored 1,643 P6 records and 2,193 P8 records. It reported 58 P8 fallbacks and
476 NSR top-1 outputs, with all P8 top-1 and binary sets agreeing with archived
comparisons; P6 top-1 differed on one record, while its binary sets agreed.
These are counts within already selected development cohorts, not prevalence
in all clinical inputs. The pathology replay emitted ALMI, ILMI and LAE scores
for 733 selected ECG; neither auxiliary stream had a recovered frozen action
policy. See the [waveform audit](../frozen-waveform-audit.md) for source hashes,
execution receipts and numerical residuals.

For the 2,926 selected record keys in the reconstructed audit, quarantine was
not assessed because linked uncertainty scores and a verified historical
policy were unavailable. The corresponding rate is undefined, not zero. A
future claim about historical pre/post quarantine requires a real ledger,
policy, score inputs, denominator and checkpoint/job linkage; a new policy
must be labeled as a new experiment. No reader performance or intervention
was measured by these outputs.

## Disposition

The implemented no-crossing behavior and bounded selected replay are technically
verifiable. The historical per-class supervision, all-input routing and
quarantine history remain at the evidence ceiling for examined sources. A
validated Other class, a full historical flow, or a clinical human-in-the-loop
study would require additional data or experiments; changing text alone does
not create those experiments. A later manuscript may accurately state the
verified rules and limitations after author review.
