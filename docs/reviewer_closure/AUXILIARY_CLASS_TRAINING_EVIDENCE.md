# Auxiliary-Class Training Evidence

**Status:** Historical supervision and performance for secondary rhythm outputs and ALMI/ILMI/LAE remain unverified. This document separates implementation from training and evaluation.

## Evidence levels

| Output group | Declared output | Reconstructed score emission | Historical supervision linked to released checkpoint | Historical performance established |
| --- | --- | --- | --- | --- |
| Rhythm secondary stream: Flutter, LBBB, 2AVB, 3AVB, LQTS, Paced | Yes; six dimensions in the global rhythm contract. | Scores are present in retained reconstructed workflow outputs for selected records. | No complete checkpoint-linked labels, positive/negative supports, loss masks and train/validation manifest chain. | No validated class-specific performance from the available linked evidence. |
| Pathology auxiliaries: ALMI, ILMI, LAE | Yes; three dimensions in the global pathology contract. | Reconstructed P4 inference emits these scores for the selected P4 records. | No authenticated checkpoint-linked supervision masks/supports, calibration or exact job-to-checkpoint edge establishing training. | No validated endpoint-specific performance is established. |

The profile/output definitions are available in [`global_head_contracts.json`](../../outputs/models/heads/global_head_contracts.json), [`full-class coverage`](FULL_CLASS_COVERAGE_AND_ROUTING_AUDIT.md) and [`role/supervision audit`](ROLE_SUPERVISION_AND_ROUTING.md). Current inference code exposes output contracts; it cannot recover the historical labels or loss masks used to create a checkpoint.

## Why emitted scores are insufficient

A tensor dimension, class-name constant, checkpoint output, config field or score file establishes at most that a score can be produced. To establish historical training, the evidence chain must bind the exact checkpoint to its producing job, source/config, manifest bytes actually read, label mapping, per-class mask/loss, positive and negative supports and optimizer/training log. To establish performance, it additionally needs a held-out compatible reference and the saved evaluation results tied to that checkpoint and partition. Those chains are incomplete for the auxiliary groups.

## REV6 static-source findings

The REV6 export adds byte-verified source copies, inspected without importing or executing them. The relevant source hashes and limits are in [source authentication](CEDIA_SOURCE_CODE_AUTHENTICATION.md).

- The multihead contract declares 14 rhythm outputs. Its default primary set has eight classes; the remaining six are represented as cascade classes in that source contract. The generic `train_multihead_epoch` passes the model's rhythm output and the batch rhythm target to a rhythm criterion. This establishes an implemented training path, but the job-specific class map, effective target support, masks, configuration, and checkpoint-producing job are not linked to the released weights.
- The same contract declares four primary plus three cascade pathology outputs, and `pathology_targets_for_paths` constructs a seven-wide target with a **row-level** presence mask. The generic training path applies a seven-output pathology loss to rows admitted by that mask. It does not preserve a separate unknown/known mask for every pathology. In the recovered implementation, omitted labels in a present vector are zeros for the loss; without the source ontology and label-completeness contract, those zeros cannot be interpreted as clinically confirmed negatives.
- A separate `train_v3f_partial_finetune` routine explicitly indexes Primary-8 rhythm logits and Pathology-4 outputs for its direct losses. It does not directly optimize the six secondary rhythm logits or ALMI/ILMI/LAE through those indexed losses.

These are two distinct code paths. The static source shows what a particular implementation can optimize, and one routine's explicit P8/P4 scope; it does not establish which path produced a released checkpoint, which labels were actually loaded, whether unknown labels were masked, or any auxiliary class performance. The prior statuses for historical supervision and performance therefore remain unproven.

## Recoverability and next action

Only a newly identified custodian source containing the exact historical manifests, label arrays/masks, job/config receipt and checkpoint digest could reopen the historical question. The bounded recovery search and gaps are recorded in [`historical recovery`](HISTORICAL_RECOVERY_FINAL_EXECUTION.md) and [`checkpoint lineage`](CHECKPOINT_JOB_MANIFEST_VERIFICATION_FINAL.md). Do not infer training from the existence of a class output or from V4.6 experiments.

If authors retain auxiliary-performance claims, a new experiment needs rights-cleared cohort data, an explicit reference ontology, patient/source-separated partitions, declared loss masks, class support thresholds, frozen thresholds and a separate untouched evaluation. Its results must be labeled new and must not be attributed retrospectively to the V4.5 checkpoints.
