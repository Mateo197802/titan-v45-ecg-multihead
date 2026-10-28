# Correction of Submitted Hash Evidence

## What Was Wrong

The submitted manuscript's Appendix A10 did not contain valid measured artifact evidence. Its backbone row used SHA-256 of empty content (prefix `e3b0c44298fc`); the other four rows used example-pattern strings. The generic filenames also did not identify the separate released V3F/V3AG branches. None of those five rows should be cited as verification of a physical study artifact.

The revised private manuscript removes that table and links the actual versioned code/evidence package. The submitted PDF remains immutable audit input: this correction does not retroactively alter the file already sent to the journal. The corresponding author must submit the corrected manuscript and response when approved.

## Real Model Evidence

These values were computed from actual CEDIA files and agree with [`release-manifest.json`](../release-manifest.json) and the [physical recovery inventory](../outputs/results/revision_20261028/cedia_artifact_recovery.json). They identify files, not clinical validity or end-to-end inference equivalence.

The [follow-up physical hash recheck](../outputs/results/revision_20261028/model_hash_recheck.json) re-read all five model files and again confirmed their sizes and SHA-256 values. It is separate from the metadata-only local checkout audit.

| Actual artifact | Bytes | Measured SHA-256 |
| --- | ---: | --- |
| `backbone-v3f-original.pt` | 233565900 | `ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8` |
| `backbone-v3ag-pathology.pt` | 233566092 | `bf71e4cf8acc34031cb3611c7031e0649822e705fd7dcea354a3ea583ce920ee` |
| `specialists-v3p-e008-primary6-diagnostic.pt` | 22354966 | `9c5a9265a7155e1206c551cc4e6d645b86363ba3dbdeb7baf7b9f173c314be3d` |
| `specialists-v3q-primary8-best-candidate.pt` | 29498326 | `b30cb2bbb45f1231c93ff1c196aa966b57b49831cadb296131c0283e7b0ceb02` |
| `specialists-v3ag-primary4-calibrated.pt` | 29413606 | `cf5091e962fffb3254b1a71fe57236dd82ea0139093df192511499d931391dbc` |

The old generic `optuna_study_trials.db` and `external_development_preds.csv` filenames are not certified as recovered physical artifacts. No replacement hashes are invented for missing files. The released prediction CSVs have their own identified paths and measured hashes in the [saved-prediction verifier](../outputs/results/release_evidence_verification.json).

## Automated Prevention

```bash
python scripts/evaluation/verify_release_hashes.py
```

This validates all manifest hash/size declarations, rejects empty/example hashes, checks duplicates and contradictory hash maps, and verifies size plus SHA-256 of each physical asset that is available. Missing files are explicitly listed; a metadata-only check does **not** become physical model verification.

Where all released models are present in the manifest's relative asset layout:

```bash
python scripts/evaluation/verify_release_hashes.py --root /path/to/release-root --require-models --output /path/to/hash-audit.json
```

`--require-models` fails if any declared model is missing. Any available asset with wrong bytes/hash also fails. Release generation rejects an empty source file before publishing the manifest. Unit tests exercise the submitted example values, empty artifacts, tampering, missing models and inconsistent metadata; the ordinary CI test suite runs these guards.

## Closure Boundary

- Corrected: invalid A10 claims withdrawn from the working revision; real model identities/sizes/hashes supplied; automated regression guard added.
- Not retroactively corrected: the original submitted PDF, which is deliberately preserved.
- Still open: historical preprocessing/features, patient split provenance, independent validation and the failed P4 waveform-equivalence check. A correct hash cannot resolve those issues.
