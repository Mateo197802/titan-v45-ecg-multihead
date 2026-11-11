# Historical V3C SQLite locator and V3C–V3F tool-event trace (2026-11-11)

## Scope and authenticity

Private preservation ZIP `TITAN_V45_V3C_V3F_TRACEABILITY_SHAREABLE_20261111.zip` (11,254 bytes) was independently inspected: SHA-256 `43716dbd9f252074394d929f1b5fbe7d9e244f0a90aaa75f738f16f0b2728ee6`, CRC OK, internal SHA256SUMS consistent for all listed members. It retains three command/output pairs from original June 29 session events. ZIP integrity is not a remote filesystem attestation.

Findings:
- A June 29 CEDIA source-output SHA256 print identifies the V3F run-path `titan_v4_v3f_finetuned_best.pt` as `ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8`, matching the released V3F asset as previously verified; this is a **known** path-to-release identity, not a new job-write proof.
- A separate CEDIA listing showed `titan_v4_final_best.pt` at a 223 MiB-ish human-readable size, modified June 22 16:56; no file digest, writer, or reader is certified.
- A third June 29 CEDIA `find` listing documented `slurm-16781.out` (17,799 bytes), `slurm-16781.err` (1,135 bytes), `submit_v3f_finetune.sbatch` (593 bytes) and the V3F output checkpoint (233,565,900 bytes), but preserved metadata only.

## Specific high-value previously untargeted Optuna file

The same historical `find` listing **explicitly names an original V3C SQLite database**:

| Field | Historical value |
|---|---|
| Basename | `optuna_primary8_primary4.db` |
| V3C run folder | `20260622_primary8_primary4_optuna_v3c_clinical_heads_v4_pathpanel` |
| Size recorded in historical CEDIA listing | **135,168 bytes** |
| Modification timestamp in historical listing | **2026-06-22T15:12:44.7776531200** |
| Historical evidence | Archived June 29 `find` tool-output event, source call `call_NFmAwAynzmKXSFuaTzY3fKgl`, session `019f0c95-308c-7660-a998-d83d47255619` |

**Important:** This filename is not `titan_v45_41m_multihead_optuna.db`. Previous narrow exact-path probes of the generic filename do not rule out this V3C-specific database surviving elsewhere in authorized backups, other bundles, or an old notebook/snapshot. The listing proves the specific DB **existed at the recorded time**, not that its bytes are available today; it does not mean an original V4.5 SQLite has been recovered.

### Search target for authorized custodian

Search by **exact basename + 135,168-byte size + June 22 2026 timestamp + V3C run folder**, including historical manuscript evidence archives/snapshots and backup catalogs. If found, preserve bytes read-only; compute SHA-256 and `sqlite integrity_check`, enumerate studies, trials, states, parameters, intermediate scores and checkpoint references. Keep original provenance and sidecar versions distinct. Never substitute V4 Primary-9 SQLite. Do not copy restricted clinical rows to public GitHub.

## Reviewer impact

The three recovered pairs are already-known evidence about file existence and path-to-release hash. They do **not** prove trial-6 actual consumption by job 16768, job 16768 output SHA, job 16781 reading that exact parent checkpoint, patient isolation or a new external cohort. **No newly completed subrequirement** in the current 40-item rubric: R1-4 `25.0%`, global `19.5/40 = 48.75%`. Recovery of and authentication of the genuine V3C SQLite could materially upgrade the study-history part of R1-4, subject to an exact rescoring of the reviewer-specific requirements.

**Do not publish private session JSONL, raw logs, checkpoints or patient-level data.**