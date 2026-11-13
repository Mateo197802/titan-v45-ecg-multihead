# Additional recovery: V3F fine-tuning reports historically authenticated (11 November 2026)

## Independent audit and evidence class

During inspection of the user's previously archived session outputs, a previously unextracted original shell-output record was located: session `019f0c95-308c-7660-a998-d83d47255619`, source line **5524**, timestamp **2026-06-29T14:00:29.755Z**, tool call `call_rp4Og2wgHARNlk5FchVxoaSp`. It contains a complete textual dump of two V3F fine-tuning JSON reports from the **local manuscript evidence copy** (not the original June SLURM output).

Both JSON texts were parsed and normalized to LF, then independently hashed. **Both sizes and SHA-256 values match the historical 2026-06-29 manuscript inventory in the same archived session, line 6033**:

| Report from V3F run | LF bytes | SHA-256 and historical comparison |
|---|---:|---|
| `v3f_finetune_summary.json` | 9,126 | `bb220d20249e7972c2846a6f4e0c3ad94f3cefa7157a4010b45aca0ec2e53d39` — exact match |
| `v3f_partial_finetune_report.json` | 7,639 | `1d686b975da6c04250ca146b47fb5a6b4634bb468706b4f8c2092a04965a4389` — exact match |

The tool-output text SHA-256 within the retained archive is `4288950b35ef123684bc6df1916dac71b7339ea3425a8e9862407672d67b8560`. Extraction produced a private, internally checksummed preservation ZIP; no private JSON or path-rich raw output was committed.

## Scientifically useful, now authenticated as archived copy

- The V3F summary reports **9,021 rhythm training windows, 144 rhythm validation windows; 5,013 pathology training windows, 776 pathology validation windows**, not unique-patient counts.
- Reported morphology dimension is **10**; it records **10,941,737 trainable** and **58,352,219 total model parameters** for the partial-fine-tuning configuration.
- Eight epoch records survive in both JSON reports, with rhythm and pathology losses and validation metrics. The report's last validation: rhythm macro-F1 `0.7518232227`, rhythm top-1 accuracy `0.7083333333`, pathology P4 macro-F1 `0.5188207610`. These are **historical internal development results**, not external clinical validation; never compare these denominator-specific results as if they were the released evaluation population.
- The full summary includes support counts for the eight rhythm targets and per-class confusion/precision/recall/F1 on its selected validation panels. They are useful for describing this historical V3F run but do not prove the entire training population's unique-patient count.
- Its `checkpoint` string declares `titan_v4_v3f_finetuned_best.pt` in the June 22 V3F output directory. An earlier 2026-06-29 **CEDIA path SHA print** in the same historical session, line **4886**, records this file's SHA-256 as `ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8` — identical to the verified published V3F backbone asset. Thus the historically named V3F output artifact and the released model have **corroborated byte identity via a historical digest**. This is materially stronger than a checkpoint-name coincidence.

## What is NOT proven

- The 16768 job's actual read of trial-6 configuration/weights or the original intermediary `titan_v4_final_best.pt` hash.
- That job 16781 executed the exact recovered code/configuration and read/wrote the checkpoint bytes specified by the reports. The SubmitLine has the V3F run directory and source input declarations, but lacks read/write digests.
- Exact train/val manifests with patient IDs, fold isolation or true independence.
- Original V3C Optuna SQLite, complete trial states, a new untouched external cohort, or full historical quarantine policy and outcomes.

The historical record now substantiates the **V3F output-file-path-to-release digest match** and the **V3F training summary/results content**. It still does not substantiate a complete trial-6→16768→16781 job-byte chain. Preserve these evidence levels separately.

## Reviewer impact: rigorous current rubric

Relevant items: **R1-4** (Optuna/A10 lineage), **R2-3a** (splits and source/class counts), and **R2-3f** (morphology/layout). They gain substantive historical report evidence and a stronger file-identity link, but the rubric's unsatisfied subrequirements explicitly require original Optuna DB or actual job-consumed manifests/loader. The reports alone do not cross those conditions.

**Official technical-coverage total remains 19.5 / 40 = 48.75%**, R1-4 `25.0%`, R2-3a `50.0%`, R2-3f `25.0%`; 0 additional fully scored subrequirements. Reassess if original job-read evidence or a permissible updated rubric precisely reflecting the reviewer request becomes available. The complete manuscript and the response letter remain unchanged.

**Custody:** Private evidence ZIP SHA-256 `e7f7b19463ba114681e6add4f6c2baecc87c1d67a9dcc74e059c8e63871dd614`. This audit document is the only GitHub deliverable; do not publish private inputs.