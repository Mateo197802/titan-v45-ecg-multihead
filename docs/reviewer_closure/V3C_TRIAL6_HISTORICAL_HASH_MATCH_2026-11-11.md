# V3C trial-6 source-session restoration — historical checksum reconciliation

**Audit date:** 2026-11-11. **Scope:** V3C Primary-8/Pathology-4, June 2026 only. This receipt supplements but does not replace the unrecovered original V3C Optuna SQLite, model-output checkpoint bytes or job-read traces. No manuscript, weights, raw sessions, or patient-level records were modified or published.

## Material and historical anchor

A preserved PowerShell `Get-Content -Raw` command, issued 2026-06-29T16:51:24.082Z (archived session `019f0c95-308c-7660-a998-d83d47255619`, call `call_yPIkMcxGzhW7NPYjL0LAFboY`, source line 6612), printed two complete JSON texts (tool output line 6616, 2026-06-29T16:51:29.424Z). The command read the local manuscript-evidence copy, **not an execution-time input trace from SLURM**.

Independent checks of the submitted private recovery found that:
- Original request/response raw-event SHA-256 values reconcile exactly with preserved raw JSONL event bytes: request `a73681f42d1c9b3055db03bbcf67daee3dfc33f0e1f9020bdd5567c8b041a8ff`; response `597dc0f532119c0e22d6520eb6876192ef257d3c8622dd51edbbe0e179dc3fc3`.
- A **different tool-output event in the same historical session**, line **6033**, dated 2026-06-29T16:00:56.507Z, lists the sizes **and historical SHA-256 digests** of the two files in a manuscript evidence artifact inventory.
- The earlier line **4886**, dated 2026-06-29T04:41:03.337Z, additionally prints a SHA-256 tied to the remote CEDIA path for `optuna_primary8_primary4.json`.

| Source document | Restored LF text bytes | SHA-256 recomputed from restored bytes | Matches historical line 6033 | Historical CEDIA-path hash at line 4886 |
| --- | ---: | --- | --- | --- |
| `selected_candidate_v3c_trial6_final.json` | 1,551 | `3bc548cd8b0e8ecd70fcf1c34d63db16b9abaa8bf2101ffddbb181826cd6746b` | **YES** | Not recorded there |
| `optuna_primary8_primary4.json` | 12,747 | `42d4f46da9d8e8bb4983d3c753826b91a0164fb8553ebca292ada413d513349e` | **YES** | **YES**, identical digest |

**New stronger finding compared with the recovery README:** the restored text is byte-identical by SHA-256 to the corresponding historical manuscript-evidence copies indexed on 29 June. For the Optuna summary, a separate earlier remote-path checksum print in that same historical session also matches. This does **not** establish an independently authenticated June job-read record or that the missing original remote directory remains accessible. It corrects the narrower claim that only byte lengths had historical corroboration.

The historic inventory also names `titan_manuscript_evidence_20260629.tar` (1,955,840 bytes; recorded SHA-256 `370f272fb2ea84dda5df7684ef54325c4eea66e2df275ff240f1538f15605add`). This is a **specific recovery lead**, not a newly recovered archive.

## Scientific details verified in the restored source copies

- Source-selected trial: **6** with ranking `0.6245117257061378`, peak `0.6313837131496386`, and last-three scores `0.623041316167568`, `0.6222158543408968`, `0.6313837131496386`.
- Nine candidate records numbered 0–8. Recalculation of `mean(last_3) - 0.25 * population_std(last_3)` matches all nine stored ranking values within floating-point precision; trial 6 has the highest ranking and trial 8 the highest **peak** (`0.6509403855805211`). The two ranking notions must remain distinct.
- Source summary declares 12 requested trials and 9 complete, 12 epochs per trial, `TPESampler(seed=197813, multivariate=True, n_startup_trials=10)`, a weighted sampler, morphology of dimension 10, and **9,021 train / 924 validation windows**. These are **declared windows**, not verified independent ECG or patient counts.
- Objective text in `optuna_primary8_primary4.json`: `0.6 * primary8_macro_f1 + 0.4 * pathology4_macro_f1 - 0.05 * missing_primary_rhythm_classes - 0.05 * missing_primary_pathology_labels`. The document carries generic fields `protocol=TITAN_V45_41M_MULTIHEAD_OPTUNA` and `stage=screening_v5`, but its V3C identity is supported by the selected-candidate document and V3C run context. Do not merge it with May's 41M Optuna generations or June V5 rescue.
- Selected trial-6 parameters and checkpoint path match the nine-candidate summary. These are historically documented **selection records**, not an authenticated consumed checkpoint.

## Train-lineage boundary

Historical SLURM job 16768 finished `COMPLETED 0:0` and its SubmitLine **declared** `TITAN_V45_SELECTED_CANDIDATE` as the selected JSON path. Job 16781 finished `COMPLETED 0:0` and its SubmitLine **declared** `TITAN_V45_BASE_CHECKPOINT` as `titan_v4_final_best.pt`. The V3F published checkpoint's preserved SHA is `ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8`, corroborated separately by CEDIA/release records.

The original completed-trial checkpoint, the intermediate `titan_v4_final_best.pt`, job 16768/16781 input/output read-write digests, complete Optuna SQLite and exact job-consumed patient manifests remain unavailable in the examined material. **Neither SLURM success nor an internal `parent_checkpoint` path proves the complete trial-to-published-model byte lineage.**

## Reviewer coverage disposition

This changes the authenticated **identity of two historical V3C selection documents**, rather than satisfying the outstanding reviewer requirement for the **full V4.5 Optuna database plus checkpoint promotion**. Under the existing [40-subrequirement rubric](REVIEWER_15_COVERAGE_AND_CEILING.json), `R1-4 = 25.0%` and global `19.5/40 = 48.75%` therefore remain unchanged, subject to a documented rescoring if additional qualifying job/SQLite evidence is recovered. `R2-3a` similarly remains at `50.0%` without certified job-consumed patient splits. This is **meaningful provenance progress**, not a completed reviewer closure.

No private ZIP or original full text was uploaded to public GitHub. The raw historical session events, original restored JSONs and path-rich inventories are held in the user's private recovery package.