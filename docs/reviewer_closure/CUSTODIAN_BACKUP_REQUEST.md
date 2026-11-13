# Custodian backup request and residuals

**As of:** 2026-11-09. The first bounded backup inquiry has already been sent and answered. This record prevents that response from being overstated as a search of every institutional or collaborator archive.

## Response already received

On the inquiry about a pre-cleanup TITAN V4.5 snapshot, CEDIA NOC reported a backup dated 2026-09-04 17:00:01. NOC stated that the reviewed listing had no files or directories for the requested `20260623_*` identifiers and did not contain the exact `DATA_PIPELINE/data_loader_ultra.py` or `titan_v45_41m_multihead_optuna.db`. The response did not specify a timezone or a broader catalog-retention scope. The requested clean root was also absent at its exact live CEDIA path.

That is a negative result for the backup and listing NOC reviewed. It does not prove that no collaborator copy, offline archive, or separately administered cold-storage snapshot exists. Do not repeat a broad request for the same already-reviewed backup unless a new catalog, path or custodian is identified.

## Residual custodian-only questions

If a further request is necessary, keep it catalog-only and ask whether an additional archive retains any of the following without restoring or transferring ECG data:

1. The V3H preselection parent population, exclusion reasons and the submitted script/log for jobs 16785 and 16786.
2. The V3M train manifest, internal validation panel index and four panel files, plus the submitted script/logs for jobs 16816 and 16819.
3. The V3P rhythm train manifest and immutable submitted script for sweep job 17314; the script/log receipt for job 17315; and the output/checkpoint hash records connecting these runs to `specialists-v3p-e008-primary6-diagnostic.pt`.
4. The V3O/V3Q training scripts, configuration and checkpoint receipts for jobs 16887, 16904 and 16906; plus V3S selected-panel parent/exclusion records for job 16914.
5. The original Optuna SQLite database and any WAL/SHM files or authenticated study export, with job linkage to the released checkpoints.
6. Any V4.5 uncertainty-score, quarantine-policy and pre/post transition ledger linked to the relevant checkpoint and all-input denominator.

Request only the catalog/path, archive date/time/timezone, file size, modification time, a custodian-computed SHA-256 and the associated job/checkpoint identifier. Do not request signal restoration, patient rows, execution, or project modification. Any access or redistribution decision remains subject to the account holder's authority and applicable data licenses.

## Current action state

No second NOC request was sent as part of this audit. The next useful human action is only to ask whether an additional backup catalog or the listed job-script/log archive exists. If the answer is no, retain the documented unknowns and proceed with the authors' later scope/claim decisions; do not reconstruct historical data by tuning a new implementation against selected test results.
