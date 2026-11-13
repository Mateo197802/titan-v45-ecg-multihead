# Pre-merge pull-request matrix

Scope and state are from GitHub before the first integration commit. Full
names, full SHAs, original base/head pair, reviews and checks are in
`PR_PREFLIGHT.json`. Per-ref commit IDs, messages and name-status file lists
are in `PR_COMMIT_FILE_INVENTORY.json`. The archived tree listing includes
all 361 initially tracked paths and their Git object IDs.

| PR/ref | Original state | Commits/files vs base | Evidence and verification | Conflict, privacy and decision |
|---|---|---:|---|---|
| #1 | Merged | Historical | Frozen waveform audit and failed replay equivalence | Already on main; do not remerge |
| #2 | Merged | Historical | Replay residuals and official fold coverage | Already on main; do not remerge |
| #3 | Draft open | 84/252 | SPH transfer, archive hashes, reviewer provenance; aggregate and historical evidence validators | Shared packaging with #5; aggregate plots only; preserve non-submission response draft as evidence; first |
| #4 | Draft open | 9/13 | A10 artifact identity, Optuna V3C and June provenance; focused release/audit tests | Same studies as #3 are not independent observations; preserve both evidence tracks; second |
| #7 | Draft open | 2/2 | Twelve reviewer items and permitted claim scopes; editorial assessment | Parallel scope matrix, not a new rubric or manuscript edit; third |
| #8 | Draft open | 1/8 | 15 comments, 40-item reconciliation, calculation verifier | Distinct historical score and claims register; no clinical data; fourth |
| Four-reviewer base | No PR | 38/87 | Historical replay, morphology/logistic and selective experiments; receipts and validators | Review ancestor independently, aggregate-only; before #9 |
| #9 | Draft open | 28/57 | Four-reviewer evidence ZIP, LUDB/SPH and morphology robustness | Verify archive and native receipt; independent evidence scopes; before #12 |
| #12 | Draft open | 8/24 | Five-seed morphology, abstention and partial P6 fallback; receipt and ZIP verifier | No individual ECG or checkpoints; no historical quarantine claim; follows #9 |
| Stage A base | No PR | 13/42 | Frozen checkpoints interface and aggregate new specialists | No checkpoint payloads; privacy, model identity and protocol separation; before #6 |
| #6 | Draft open | 30/85 | Executed external preflight and 18-archive CODE-15% benchmark | Aggregate tables; existing and reconstructed model identities distinct; before #10 |
| #10 | Draft open | 27/83 | Duration-aware adaptation, verified held-out outcomes and negative promotion | Aggregate accounting/plots only; workflow additions retained; before #11 |
| #11 | Draft open | 11/33 | Development-only performance recovery; audit, grouped fits and receipts | No promotion or experimental checkpoints; preflight CI in progress; after #10 |
| #5 | Draft open | 31/114 | V4.6 BenchmarkMax experimental program, SPH/MIMIC aggregate audits | Shared packaging and figure tests; separate experimental namespace; last |

No archive-looking binary beyond the two evidence ZIPs was found among
the incoming history in the preflight blob listing. Verify the two ZIPs
with their respective project verifiers. Aggregate Slurm receipts must
not contain raw command lines, cluster account paths or record identifiers.
