# Recovery Evidence Handoff to PR #4

As of 2026-11-10. This memo transfers only relevant outcomes of the directed recovery packages and CEDIA REV2 export to the independent A10/Optuna workstream. PR #4 remains the governing branch; no PR #4 files were changed by this integration.

## New observations

- The supplied CEDIA receipt records jobs 13169, 13172 and 13181 as failed (`1:0`, `9:0`, `9:0` respectively).
- No bytes for `titan_v45_41m_multihead_optuna.db`, `titan_v45_41m_multihead_optuna_before_resume.db`, SQLite sidecars, or a complete trial export appear in the directed package.
- A damaged October log backup yielded literal references to a database/log name. Its SQLite integrity check failed; it is not a recoverable or queryable Optuna database and does not establish trial state.
- No new artifact hash, trial objective/parameter set, study generation, selected configuration, or checkpoint-promotion link was recovered. Keep the two previously documented 41M generations separate.
- The six source archives in this package are S4/S5/U plan code, not Optuna database files and not an A10 artifact set.

## CEDIA REV2 corroboration

- The newer CEDIA export also reports jobs 13169, 13172 and 13181 failed (`1:0`, `9:0`, `9:0`) and includes May launcher/preflight/test source copies. The export ZIP integrity is verified; the source-side history is not a signed scheduler attestation.
- No original SQLite bytes, WAL/SHM/journal set, complete Optuna history, new objective/parameter rows, selected-model receipt or trial-to-checkpoint edge was added. The two 41M generations remain distinct and unverified as databases.
- The V3C chain is unchanged: 12 completed SLURM segments do not mean 12 completed trials. Trial 6 selection and jobs 16768/16781 remain path/reference evidence without authenticated intermediate JSON/checkpoint bytes or read/write digests linking them to the released V3F backbone.
- Stable CEDIA claims and limitations are in [`HISTORICAL_RECOVERY_CANONICAL_INDEX.md`](HISTORICAL_RECOVERY_CANONICAL_INDEX.md) and [`HISTORICAL_PROVENANCE_GRAPH.md`](HISTORICAL_PROVENANCE_GRAPH.md). No hashes or rows are being added to PR #4 by this PR #3 integration.

## PR #4 disposition

The existing A10 correction and existing bounded Optuna evidence remain unchanged. This round does not justify adding fabricated trial rows, generating a replacement SQLite file, changing model hashes, or changing the PR #4 status. The local source package and raw CEDIA receipts are not copied into PR #4 or PR #3.

If new custodian evidence later becomes available, it should include the original DB and a consistent same-time WAL/SHM/journal set for each generation, file sizes and SHA-256 computed by the custodian, trial states/objectives/parameters, associated logs/configuration, and evidence linking any selected trial to the exact checkpoint bytes. A filename or job reference alone is insufficient.

Live PR #4 head at this audit: `3cfedf39a81a22c867fde04faf9b1a1dd2f60448`, open draft. See [`OPTUNA_41M_NEW_EVIDENCE.md`](https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/codex/titan-a10-optuna-evidence/docs/reproducibility/OPTUNA_41M_NEW_EVIDENCE.md) for the prior evidence already governed there and [`HISTORICAL_PROVENANCE_GRAPH.json`](HISTORICAL_PROVENANCE_GRAPH.json) for the round-2 job receipts.
