# Specialist Stage A Calibration and Threshold Audit

The published baseline thresholds are immutable and were used unchanged. Candidate-specific thresholds were selected under the frozen V2 rule: maximize class-wise F1 on the separate calibration partition; ties select the highest threshold. The per-class aggregate CSV records the resulting threshold alongside the evaluation metrics.

## Partition use

- Rhythm Chapman-Shaoxing records were split by stable source-relative-record-key hash into train, early-stopping validation and threshold calibration partitions. The source-reported one-record-per-patient property is used only as a patient proxy; validated row-level patient IDs were not available.
- PTB-XL official folds 1-7 trained the P4 head, fold 8 selected the epoch, and fold 9 was divided by patient into calibration and internal-evaluation halves. Fold 10 was not accessed.
- Georgia served as a source holdout for the primary rhythm comparison. CPSC served as the held-out source only for the separately trained Chapman+Georgia-to-CPSC sensitivity models. Neither source's held-out outcomes were used to set the primary candidate thresholds.
- The original threshold vectors, model weights and historical predictions were not changed.

All intervals use 2,000 bootstrap replicates and seed `20261111`. Patient-group resampling is used only where a validated patient grouping exists. Georgia and CPSC intervals are record-grouped. These intervals quantify the observed split under this experimental design; they do not establish clinical calibration or transportability to an independent cohort.

The CSV arithmetic verifier checks supports and confusion-derived metrics, then independently reconstructs macro-F1 and its point-estimate delta. It does not reconstruct AUROC, average precision, Brier score, ECE, or bootstrap intervals from record-level probabilities; those require private row-level CEDIA data and remain reproducible there from the frozen code, cache and candidate checkpoints. No row-level probabilities or checkpoint hashes are published.

No post-hoc threshold adjustment is justified by the observed holdout sensitivity losses. Any prospective calibration change requires a new versioned protocol and data partition; it must not be represented as a correction to historical V4.5 thresholds.
