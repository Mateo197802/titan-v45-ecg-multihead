# Reproducibility Verification Receipts

**Execution date:** 2026-11-10, Ecuador time.<br>
**Code baseline:** `0a32a57a32b50c421fc05323454507dba4265bb0`.<br>
**Python:** 3.12 for the focused pytest run.<br>
**Scope:** aggregate-only checks of retained public artifacts. No CEDIA job, GPU inference, retraining, MIMIC download or new external-data access was initiated.

## Fresh commands and outputs

| Check | Command | Result | Receipt |
| --- | --- | --- | --- |
| AF code/flag consistency | `python scripts/evaluation/audit_af_reference_contract.py --output docs/reviewer_closure/receipts/AF_REFERENCE_RECHECK_2026-11-10.json` | PASS. P6 1,643 records; P8 2,193; 390 AF reference positives in each overlapping profile; zero flag/code mismatches and unresolved rows. | SHA-256 `42199ccc5392daec3ce0fa0be793917509af7de3973d29e7a3418c3aab85300e`. |
| Release metric/manifest verification | `python scripts/evaluation/verify_release_evidence.py --output docs/reviewer_closure/receipts/RELEASE_METRICS_RECHECK_2026-11-10.json` | PASS. Recomputed P6/P8/P4 summaries from released predictions and manifests. | SHA-256 `86f6920813fb79b256c73903e9a91ad8eb0255f1ad995dd4f139737fd82b0647`. |
| SPH aggregate/protocol validation | `python scripts/external_validation/validate_sph_aggregate.py --aggregate outputs/results/external_sph/sph_aggregate_32669.json --protocol configs/external_validation/sph_frozen.json` | PASS. `source_records=25770`, `profiles_checked=3`, `endpoints_checked=14`. | SHA-256 `9100d70600709bfe6b8ab932efe8b07e86b622838e80e1de0c6bcbbe6bdaa9dc`. |
| AF reference regression tests | `python -m pytest tests/evaluation/test_af_pvc_reference_disposition.py tests/evaluation/test_label_reference.py -q` | PASS, 6 tests. | Console result: `6 passed in 0.07s`. |

Receipt hashes are computed from UTF-8 text after normalizing CRLF to LF. This makes the hash invariant to Git checkout line-ending conversion; the JSON values and evidence are unchanged.

The release recomputation produced P6 accuracy `0.9519172245891662` and macro-F1 `0.8009383239876122`; P8 accepted-label accuracy `0.9060647514819882` and macro-F1 `0.7614253535094375`; P4 mean binary accuracy `0.8022904853689048` and macro-F1 `0.7934563704063461`. These are recomputations from archived prediction rows, not a new signal inference or training reproduction.

The AF receipt hashes the whole input CSV artifacts, not individual ECG. It contains only source-level aggregates; no record or patient identifiers are exported. The release receipt likewise contains aggregate confusion counts, release-manifest asset hashes and whole-file hashes only. The SPH validator reads the already committed aggregate and frozen protocol; it does not read patient-level rows.

## Retained run evidence rechecked by inspection only

The following stored JSONs were not rerun. Their content and file hashes were inspected to keep the prior experimental boundary explicit:

| Artifact | Bytes | SHA-256 | Recorded scope/result |
| --- | ---: | --- | --- |
| `outputs/results/revision_20261107/rhythm_waveform.json` | 3,415 | `123d21f4512b988eb24bcff90b971c62510c547b7f766e059137f072c2d871b4` | Reconstructed selected waveforms; P6/P8; P8 has 58 selected fallbacks; no quarantine assessed; no independent validation. |
| `outputs/results/revision_20261107/pathology_waveform.json` | 2,186 | `592e2bbab96cd03e23caf5ba4c29b746293a0f6e7584ed4b6fc069160c2d5f46` | Reconstructed selected P4; 733 ECG; 962 saved panel pairs; decisions agree, max score difference `0.0006194114685058594` versus fixed `1e-5`; no quarantine assessed. |
| `outputs/results/external_sph/sph_aggregate_32669.json` | 106,915 | `09f93d9f310baaca672a33b0f369593cd88835a8ef08dc9929945c57cf18c988` | Frozen aggregate, 25,770 source ECG and 24,666 source patients. |
| `configs/external_validation/sph_frozen.json` | 16,731 | `d788ad8cca94793cebb738496acc131e82b1ca1900976f11020b99a79a5fc366` | Frozen endpoint/protocol contract. |
| `outputs/models/heads/global_head_contracts.json` | 1,605 | `ac73de5baf2e1b5416b37611c173f7d4979627639477fae2c68197e50c37d5fc` | 14 global rhythm and seven pathology outputs; this contract is not proof of historical class supervision. |
| `scripts/cedia/recovery_candidates/morphology_features_v4.py` | 6,611 | `2bd1c1822ed72d1531b1f62712d8007c7e2f21009056ad1a3ee905f37051fc3d` | Hash-pinned morphology candidate, not the exact original loader. |

## Reproducibility dimensions

| Dimension | Status | Evidence ceiling |
| --- | --- | --- |
| Release artifact listing and saved prediction/manifest arithmetic | Verified | Does not load model binaries or rerun inference. |
| Saved AF source-code/reference-field consistency | Verified within retained rows | Not clinical adjudication or longitudinal AF. |
| SPH aggregate metrics/denominators against the frozen protocol | Verified | Does not independently recreate hidden patient-level bootstrap assignments or rerun the SPH inference. |
| Selected waveform inference reconstruction | Previously executed; report hash rechecked only | It is selected development data, not the exact original loader; strict P4 score equivalence fails. |
| Historical checkpoint architecture metadata | Inconsistent for P6/P8 specialist hidden width | Saved run reports declared 192 versus tensor width 512. The current loader constructs from stored tensor shape and strict-loads; historical training intent is not established. |
| Original training, patient splits and selection | Not reproduced | Job/manifest/checkpoint edges are incomplete; no training run was started. |
| Original quarantine policy and human review | Not assessed | No authentic score/policy/transition ledger or human-action records. |
| Independent clinical validation | Not performed/certified | No untouched eligible cohort and clinically adjudicated reference. |

## Reproduction commands

From the repository root:

```powershell
python scripts/evaluation/audit_af_reference_contract.py --output docs/reviewer_closure/receipts/AF_REFERENCE_RECHECK_2026-11-10.json
python scripts/evaluation/verify_release_evidence.py --output docs/reviewer_closure/receipts/RELEASE_METRICS_RECHECK_2026-11-10.json
python scripts/external_validation/validate_sph_aggregate.py --aggregate outputs/results/external_sph/sph_aggregate_32669.json --protocol configs/external_validation/sph_frozen.json
python -m pytest tests/evaluation/test_af_pvc_reference_disposition.py tests/evaluation/test_label_reference.py -q
```

The SPH validator's stdout is the compact JSON recorded in the receipt file. The checks are deterministic over the committed inputs. Do not convert these verification commands into an assertion that the original model training, historical loader or external-validation study has been reproduced.
