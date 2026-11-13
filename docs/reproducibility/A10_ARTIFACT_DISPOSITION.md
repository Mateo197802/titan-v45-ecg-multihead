# A10 artifact identity and availability disposition

This disposition corrects the invalid identification table, not the historical
training record or the submitted PDF. `VERIFIED_ORIGINAL` below means the
named original **v0.1.0 release asset**, whose physical bytes were checked;
it does not assert that an ambiguous generic A10 filename is the same file or
that complete checkpoint training lineage has been recovered.

On 2026-11-08, CEDIA CPU job `32733` completed with exit `0:0` and reread
all seven physical assets against the tracked manifest. The aggregate-only
[receipt](../../outputs/results/revision_20261028/release_model_hashes_32733.json)
has SHA-256 `b251d49f2e5a16cd7350e987fb85b609a97312cde19dda3647ef7c74113b269b`.
GitHub's release API reported the same SHA-256 and byte count for the five
named model assets. This API comparison uses GitHub's reported metadata; it
does not constitute a fresh independent download of all remote asset bytes.

| Asset | Status | Bytes | SHA-256 | Verified identity and use |
| --- | --- | ---: | --- | --- |
| [backbone-v3f-original.pt](https://github.com/Mateo197802/titan-v45-ecg-multihead/releases/download/v0.1.0/backbone-v3f-original.pt) | VERIFIED_ORIGINAL | 233565900 | `ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8` | Released V3F rhythm backbone, used with the separately identified P6/P8 specialists. |
| [specialists-v3p-e008-primary6-diagnostic.pt](https://github.com/Mateo197802/titan-v45-ecg-multihead/releases/download/v0.1.0/specialists-v3p-e008-primary6-diagnostic.pt) | VERIFIED_ORIGINAL | 22354966 | `9c5a9265a7155e1206c551cc4e6d645b86363ba3dbdeb7baf7b9f173c314be3d` | Released P6 diagnostic specialist. |
| [specialists-v3q-primary8-best-candidate.pt](https://github.com/Mateo197802/titan-v45-ecg-multihead/releases/download/v0.1.0/specialists-v3q-primary8-best-candidate.pt) | VERIFIED_ORIGINAL | 29498326 | `b30cb2bbb45f1231c93ff1c196aa966b57b49831cadb296131c0283e7b0ceb02` | Released P8 candidate specialist; hash verification does not pass its project gate. |
| [backbone-v3ag-pathology.pt](https://github.com/Mateo197802/titan-v45-ecg-multihead/releases/download/v0.1.0/backbone-v3ag-pathology.pt) | VERIFIED_ORIGINAL | 233566092 | `bf71e4cf8acc34031cb3611c7031e0649822e705fd7dcea354a3ea583ce920ee` | Released V3AG pathology backbone, separate from V3F. |
| [specialists-v3ag-primary4-calibrated.pt](https://github.com/Mateo197802/titan-v45-ecg-multihead/releases/download/v0.1.0/specialists-v3ag-primary4-calibrated.pt) | VERIFIED_ORIGINAL | 29413606 | `cf5091e962fffb3254b1a71fe57236dd82ea0139093df192511499d931391dbc` | Released P4 specialist with its saved thresholds. |

| Other artifact or relationship | Disposition | Evidence boundary |
| --- | --- | --- |
| `external_development_preds.csv` as named in the submitted A10 | NOT_AVAILABLE in inspected sources | The six published, individually named prediction CSVs are **VERIFIED_REPLACEMENT_WITH_DIFFERENT_IDENTITY** for their own contents, not a recovered byte-identical generic file. Their hashes and results are in the [release evidence verifier](../../outputs/results/release_evidence_verification.json). |
| `optuna_study_trials.db` as named in A10 | NOT_AVAILABLE in inspected sources | Neither a new SQLite database nor a hash for an absent file is supplied. See the separate [Optuna disposition](optuna_evidence_disposition.md). |
| Exact upstream provenance and redistribution rights of the mixed rhythm package | PROVENANCE_UNRESOLVED | The physical release archive's hash matches, but the unresolved `data_test` component remains on HOLD; technical availability is not permission to redistribute. See the [source audit](../../data/licenses/README.md). |
| Mapping the old generic A10 entries directly onto the five names above | PROVENANCE_UNRESOLVED | The measured assets may support a corrected, explicitly renamed table, but cannot be claimed to be the unspecified original rows. |

The [release manifest](../../release-manifest.json) provides paths, URLs, sizes
and hashes. The release tag is preserved, not rewritten. Job `32731` failed
because the system Python lacked `Path.is_relative_to`; job `32732` failed
because a `/bin/sh` wrapper lacked the environment module command. Both failed
before successful verification; `32733` used the Bash launcher
[`verify_release_models.sbatch`](../../scripts/cedia/verify_release_models.sbatch)
and the cluster's PyTorch/Python module. No files were replaced to obtain a
passing result.

R1-4 can be **technically addressed for a corrected A10** by identifying the
measured release files and explicitly declaring the two originals unavailable
in inspected sources. This does not recover those originals, prove absence in
all backups, correct the submitted PDF retroactively, or substitute for author
approval and an editorial decision. The actual manuscript amendment remains
pending.
