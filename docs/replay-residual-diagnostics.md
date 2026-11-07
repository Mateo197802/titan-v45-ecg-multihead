# Replay residuals and official fold coverage

These diagnostics extend the [selected waveform audit](frozen-waveform-audit.md) without replacing canonical scores, changing preprocessing or thresholds, or introducing new evaluation labels. The [execution receipt](../outputs/results/revision_replay_diagnostics_20261107/receipt.json) links code revisions, CEDIA jobs and the exact aggregate bytes. Neither private ledger is redistributed.

## P4: agreement at the decision boundary

| Panel | Matched references | Score differences above 0.00001 | Largest difference | Smallest archived distance to threshold |
| --- | ---: | ---: | ---: | ---: |
| ASMI | 294 | 253 | 0.0003706 | 0.0008233 |
| LVH | 224 | 203 | 0.0005391 | 0.0005660 |
| IMI | 206 | 183 | 0.0006194 | 0.0006755 |
| ISC_ | 238 | 197 | 0.0005366 | 0.0057653 |

836/962 probabilities exceed the original P4 tolerance. Within each panel the observed maximum drift is smaller than its minimum archived threshold margin, consistent with all 962 calls agreeing. These margins describe the matched rows; they do not guarantee stability for future inputs.

The fixed-input GPU probe evaluated the same 733 prepared ECGs with the same model twice in batches of 32 and once in batches of one. The two size-32 runs agreed exactly on all 2,932 scores, also matching the earlier size-32 ledger. Size 1 versus size 32 differed by at most 0.0007278 and flipped one IMI call among the 2,932 ECG-class scores. The flip is outside the matched 962 panel comparisons; it is not a newly labeled error. Size 1 also fails the original probability tolerance against the archive (maximum 0.0003500, zero matched decision changes). Batch size demonstrably changes outputs but does not establish the original batch configuration or explain the entire historical residual. No runner or batch is selected by proximity to archived scores.

## P6 and P8: ranking, not exact probabilities

- **P6:** the sole top-1 change is an inversion of the same two leading classes. The archived probability gap was about 0.00001994; the replay reversed the ordering by about 0.00005590. Both gaps are nonzero. The binary sets still agree. This identifies the mechanism of the ranking change, not the upstream source of all drift. Across 9,858 probability pairs the mean absolute difference is about 0.00003470 and the maximum about 0.0019060.
- **P8:** no top-1 change in 2,193 records despite nonzero membership-score differences. Across 17,544 pairs the mean absolute difference is about 0.00004661 and the maximum about 0.0017379. Six archived top-1 margins are no larger than twice the largest observed score difference; this is a descriptive sensitivity bound, not evidence of any additional flips. The canonical performance and candidate status are unchanged.

The 0.00001 comparison is the pre-existing P4 tolerance. Counts at that and other scales for rhythm are descriptive, not a newly registered pass/fail rule for P6 or P8.

## P4: official-source denominator, not historical flow

The exact metadata bytes match the [official PTB-XL v1.0.3 SHA-256 index](https://physionet.org/files/ptb-xl/1.0.3/SHA256SUMS.txt). [PhysioNet's versioned dataset description](https://physionet.org/content/ptb-xl/1.0.3/#data-description) describes the patient-level fold assignment. The audit observes 21,799 ECGs and 18,869 patients across that metadata. Official fold 10 contains 2,198 ECGs and 1,904 patients; the 733 P4 ECGs are from 676 of those patients, with no official patient-ID overlap with folds 1 through 9. There are 1,465 fold-10 ECGs not represented in P4, including 110 from patients represented by another ECG. They are not labeled historical exclusions. The historical training/calibration manifest and reason for any omitted ECG are not inferred.

## Reproduce

```bash
python scripts/evaluation/audit_ptbxl_fold_coverage.py \
  --ptbxl-metadata /path/to/ptbxl_database.csv --output /path/to/p4-fold.json
sbatch scripts/cedia/run_replay_diagnostics.sbatch \
  "$REPO" "$P4_PRIVATE_LEDGER" "$RHYTHM_PRIVATE_LEDGER" "$PRIVATE_OUTPUT"
sbatch scripts/cedia/probe_p4_batch_sensitivity.sbatch \
  "$REPO" "$RELEASE_ROOT" "$PYTHON_DEPS_TAR" "$P4_PRIVATE_LEDGER" "$PRIVATE_OUTPUT"
```

The diagnostic scripts verify input identities; run with authorized access to the data and no signal or patient-level export. These checks support R1-2, R2-3a and R2-3f, not independent evaluation, an historical all-input denominator or an original quarantine policy.
