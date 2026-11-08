# Replacement evidence for Appendix A10

This is a technical table for editorial incorporation, not an update to the
submitted PDF. The hashes below identify the frozen model bytes measured
on CEDIA (job 32467) and checked against the
[v0.1.0 release manifest](https://github.com/Mateo197802/titan-v45-ecg-multihead/releases/download/v0.1.0/release-manifest.json).
They do not prove independence, training reproducibility or clinical performance.

| Artifact and download (v0.1.0) | Bytes | SHA-256 | Function |
| --- | ---: | --- | --- |
| [backbone-v3f-original.pt](https://github.com/Mateo197802/titan-v45-ecg-multihead/releases/download/v0.1.0/backbone-v3f-original.pt) | 233565900 | `ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8` | V3F backbone for P6 and candidate P8 |
| [specialists-v3p-e008-primary6-diagnostic.pt](https://github.com/Mateo197802/titan-v45-ecg-multihead/releases/download/v0.1.0/specialists-v3p-e008-primary6-diagnostic.pt) | 22354966 | `9c5a9265a7155e1206c551cc4e6d645b86363ba3dbdeb7baf7b9f173c314be3d` | Frozen P6 specialist package |
| [specialists-v3q-primary8-best-candidate.pt](https://github.com/Mateo197802/titan-v45-ecg-multihead/releases/download/v0.1.0/specialists-v3q-primary8-best-candidate.pt) | 29498326 | `b30cb2bbb45f1231c93ff1c196aa966b57b49831cadb296131c0283e7b0ceb02` | Frozen candidate P8 specialist package |
| [backbone-v3ag-pathology.pt](https://github.com/Mateo197802/titan-v45-ecg-multihead/releases/download/v0.1.0/backbone-v3ag-pathology.pt) | 233566092 | `bf71e4cf8acc34031cb3611c7031e0649822e705fd7dcea354a3ea583ce920ee` | Separate V3AG backbone for P4 |
| [specialists-v3ag-primary4-calibrated.pt](https://github.com/Mateo197802/titan-v45-ecg-multihead/releases/download/v0.1.0/specialists-v3ag-primary4-calibrated.pt) | 29413606 | `cf5091e962fffb3254b1a71fe57236dd82ea0139093df192511499d931391dbc` | Frozen P4 specialist package |

All five are available as release weights under the [separate model terms](../../MODEL_LICENSE.md).
Place them in the relative layout declared in the manifest and run:

```bash
python scripts/evaluation/verify_release_hashes.py --root "$RELEASE_ROOT" --require-models
python scripts/evaluation/verify_release_evidence.py
```

The first command verifies physical bytes and sizes. The second checks the
actual versioned prediction CSVs against canonical results and reports LF-normalized
input digests. Neither should be cited as a hash of a missing generic file.
The generic `external_development_preds.csv` and historical
`optuna_study_trials.db` from A10 are **NOT_AVAILABLE as identified originals**.
For Optuna, see the [separate evidence disposition](optuna_evidence_disposition.md).
No redistribution clearance is implied for the mixed rhythm signal archive.
