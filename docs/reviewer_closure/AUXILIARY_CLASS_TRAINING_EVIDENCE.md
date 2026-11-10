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

## Recoverability and next action

Only a newly identified custodian source containing the exact historical manifests, label arrays/masks, job/config receipt and checkpoint digest could reopen the historical question. The bounded recovery search and gaps are recorded in [`historical recovery`](HISTORICAL_RECOVERY_FINAL_EXECUTION.md) and [`checkpoint lineage`](CHECKPOINT_JOB_MANIFEST_VERIFICATION_FINAL.md). Do not infer training from the existence of a class output or from V4.6 experiments.

If authors retain auxiliary-performance claims, a new experiment needs rights-cleared cohort data, an explicit reference ontology, patient/source-separated partitions, declared loss masks, class support thresholds, frozen thresholds and a separate untouched evaluation. Its results must be labeled new and must not be attributed retrospectively to the V4.5 checkpoints.
