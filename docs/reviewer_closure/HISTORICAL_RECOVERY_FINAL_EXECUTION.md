# Historical Recovery: Final Execution

**As of:** 2026-11-10

**Scope:** Directed read-only checks in the authorized TITAN project areas of CEDIA and the current PR #3 checkout. This is not a claim that every CEDIA institutional backup was searched.

## New Evidence That Changes or Sharpens the Record

1. Slurm accounting plus retained job output confirms that P6 epoch 8 was explicitly gated on a population named by job 17315 as `v3h_rhythm_external_gate_holdout_accepted_balanced_manifest.csv`. The gate required top-1 accuracy >= 0.95 and macro-F1 >= 0.80; epoch 8 reported 1,564/1,643, 0.9519172246 and 0.8009383240. Job 17314 records external metrics for 12 epochs. The same checkpoint basename and exact epoch-8 metrics connect the reports strongly, but the 17314 sweep output has no manifest digest. This makes V3H model-selection/development evidence, not an independent test.
2. The surviving job 17296 launcher and Slurm output identify separate internal-calibration and external-panel manifest aliases. The final threshold vector `[0.67, 0.705, 0.635, 0.595]` matches the released P4 profile, and its evaluation metrics round to the released 80.23% accuracy and 79.35% macro-F1. The original panel files and patient maps are absent; the released P4 checkpoint is not hash-linked to the V3D job output. The logs also record 16 false `passes_target` flags across four candidates and four class panels under a requested 90% accuracy target.
3. CEDIA retains the June 29 staged TAR and the alternate loader candidate. Their verified SHA-256 values are recorded below. The TAR does not contain the requested loader, SQLite database or named training/calibration manifests. The candidate loader is not the expected original.

The new sanitized receipt is [`receipts/CEDIA_JOB_LOGS_2026-11-10.json`](receipts/CEDIA_JOB_LOGS_2026-11-10.json). Raw logs remain in CEDIA; no ECG rows, patient identifiers, internal absolute paths or raw log contents are published.

## Bounded Search Register

| Source inspected | Read-only action | Result | Limit |
|---|---|---|---|
| PR #3 CEDIA clone `titan-v45-pr3-99b1065` | HEAD, tracked status, ancestry | HEAD `31c4ccf`; tracked tree clean; it is an ancestor of current PR #3 HEAD `381c894`. | Not a newer evidence source than the PR #3 history. |
| Authorized CEDIA project home listing | List direct project entries and known archives | Cleanup manifests/inventories, June 29 stage TAR, V4.5 clone, data cache and revision work area are present. | Does not cover institutional archives or other collaborators. |
| `titan_repo_stage_20260629.tar` | SHA-256 and member-name search for exact requested files | 2,639,360 bytes; SHA-256 `483b7a722ec2432271f7d2593e42384decc650ed735afad2175fc2997a62d3e9`; none of the requested loader, Optuna DB, V3M split/index or P3 manifest names matched. | A partial repository stage, not a full experiment snapshot. |
| `life-4620846-revision-20261028/recovered/data_loader_ultra.py` | Size and SHA-256 | 32,435 bytes; SHA-256 `a2c854acd43615a1ed78b5ed77c46a0252ec3607438df32d6a88e52fb0f91ddc`. | Does not match expected 36,271 bytes / SHA-256 `fc8d7367f9f2c108376839435021ec3172fe2757faa4a615f0ef5d39cbf1e855`. |
| Named V3M/P4 files under the revision work area | Bounded filename lookup (maximum depth 6) | Only the 32,435-byte alternate loader was present; no requested train/validation manifests, panel-index JSON, or P3 training manifest was found. | Negative result applies only to this named directory and bounded depth. |
| Historical P4 output paths named by job 17296 | Exact existence checks for calibration index, external index and panel CSVs | The referenced files are not currently present at the checked paths. | The job log proves the paths were used/reported at runtime, not their current bytes or patient disjointness. |
| Job 17296 launcher and logs | Static read, SHA-256, scheduler accounting and aggregate-line extraction | Launcher 3,533 bytes, SHA-256 `8ff857b1e79cb9ccadaa657d52004120fc65eaa220fef5a0f75f554152acb615`; output hashes and sizes are in the sanitized receipt. | Calibration script, panel bytes and checkpoint bytes are not all retained. Launcher was not executed. |
| Jobs 17314/17315 | `sacct`, retained logs, bounded lookup for submit scripts | Both completed 0:0; logs survive and are hashed. Submit scripts and the sweep/audit entrypoint sources were not found at their recorded paths in the checked repo/revision areas. | Job success does not authenticate missing source/input bytes. |
| Optuna jobs 13169/13172/13181 | `sacct` status only | Failed with exit codes `1:0`, `9:0`, `9:0`, respectively. | Scheduler states do not recover the original SQLite DB, trial history or checkpoint promotion edge. PR #4 remains the owner. |

## Historical Artifacts Still Missing

- Authentic parent populations and exclusion ledgers before V3H/V3S selection, filtering or balancing.
- Job-linked V3F/V3AG training/validation manifests and patient/signal mappings for each released checkpoint.
- Exact original `DATA_PIPELINE/data_loader_ultra.py` at 36,271 bytes and expected SHA-256.
- Exact sweep/audit source and submit scripts for jobs 17314/17315, plus digest-bound input manifests.
- Original Optuna SQLite/WAL/SHM and complete trial-to-training-to-checkpoint promotion history.
- Historical uncertainty scores, quarantine policy and complete pre/post transition ledger.

## Disposition

The bounded findings sharpen the P6 selection-exposure and P4 threshold provenance records. They do **not** certify independent patient separation, prove the released checkpoint bytes equal a CEDIA candidate checkpoint, recover the June population, reproduce the original loader, or measure historical quarantine. The NOC response about the September 4 backup remains limited to the catalog/listing it checked; it is not proof that all institutional backups or collaborators lack another copy. The exact custodian request remains in [`CUSTODIAN_BACKUP_REQUEST.md`](CUSTODIAN_BACKUP_REQUEST.md).

No experiment, retraining, GPU job, external download, manuscript edit, PDF rebuild or PR merge occurred during this recovery pass.
