# V3C trial-6 provenance: historically matching original JSON digests (11 November 2026)

**Scope:** V3C Primary-8/Pathology-4 selected-candidate evidence, separated from May 41M database generations, June V5/V6 screening and V4 legacy Primary-9.

A private source-session recovery yielded the full JSON **text** of `selected_candidate_v3c_trial6_final.json` (1,551 bytes) and `optuna_primary8_primary4.json` (12,747 bytes) from a literal `Get-Content -Raw` tool output dated 2026-06-29. In a separate 2026-06-29 output within the same archived session, the manuscript evidence inventory recorded the exact historical file digests, which match the restored bytes:

| Historical file | SHA-256 |
| --- | --- |
| `selected_candidate_v3c_trial6_final.json` | `3bc548cd8b0e8ecd70fcf1c34d63db16b9abaa8bf2101ffddbb181826cd6746b` |
| `optuna_primary8_primary4.json` | `42d4f46da9d8e8bb4983d3c753826b91a0164fb8553ebca292ada413d513349e` |

The Optuna summary digest also appears in an earlier historical remote-path SHA output. A manifest length match alone was previously reported; these **actual historical SHA matches** give stronger byte-identity support for the restored copies. All source observations remain within one historical session and are not an execution-time file-read attestation.

The recovered selection JSON reports trial **6** with stable ranking `0.6245117257061378`, peak `0.6313837131496386`, and fixed eight tuned hyperparameters. The complete nine-candidate summary records 9 COMPLETE of 12 planned, 12 epochs configured per trial, TPE seed `197813`, and 9,021 train/924 validation **windows**. Independent recalculation matches all nine `mean(last3)-0.25*pstdev(last3)` rankings. Trial 8 has the highest peak `0.6509403855805211`, not the highest stable ranking.

The historic SLURM SubmitLine for completed job 16768 **declared** the selected JSON path; 16781 declared `titan_v4_final_best.pt` as input. The missing original SQLite, input-consumption hashes and intermediate checkpoints **still prevent** a cryptographically closed chain between trial 6 and the released V3F backbone. In PR #3's existing rubric this leaves `R1-4 = 25.0%`, despite meaningful improvement to selection-artifact provenance.

Potential next custodian target: the June 29 manuscript-evidence tar listed in the same historical inventory (recorded size 1,955,840 bytes, SHA-256 `370f272fb2ea84dda5df7684ef54325c4eea66e2df275ff240f1538f15605add`), plus job 16768/16781 logs/checkpoint lineage. No SQLite, model weights, private raw session or patient-level records are published here.