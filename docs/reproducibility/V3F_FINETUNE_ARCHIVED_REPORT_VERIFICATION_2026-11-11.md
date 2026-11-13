# V3F authenticated June fine-tuning report recovery (source-session evidence)

**Distinct from original Optuna SQLite and from a new evaluation.** A private historic-session shell output dated 2026-06-29 (line 5524; call `call_rp4Og2wgHARNlk5FchVxoaSp`) printed two V3F internal training reports from manuscript evidence. Reconstructing the text with normalized LF reproduced their historical manuscript inventory SHA-256 hashes (line 6033):

- `v3f_finetune_summary.json` — 9,126 bytes, `bb220d20249e7972c2846a6f4e0c3ad94f3cefa7157a4010b45aca0ec2e53d39`.
- `v3f_partial_finetune_report.json` — 7,639 bytes, `1d686b975da6c04250ca146b47fb5a6b4634bb468706b4f8c2092a04965a4389`.

The preserved V3F run summary declares **9,021 rhythm training windows/144 rhythm validation windows; 5,013 pathology training windows/776 pathology validation windows**, 10,941,737 trainable parameters/58,352,219 total parameters, morphology dimension 10, and eight epochs. The last internal validation recorded rhythm macro-F1 `0.7518232227`, rhythm top-1 accuracy `0.7083333333`, and P4 pathology macro-F1 `0.5188207610`. This is a **historical development run**, not the final published external-development panel or an independent cohort.

Its named output checkpoint path `titan_v4_v3f_finetuned_best.pt` is separately included in a 2026-06-29 remote-path SHA print (historic session line 4886) with hash `ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8`, equal to released `backbone-v3f-original.pt`. This substantiates a **historical source-path-to-release byte identity**; it does **not** independently prove the job 16781 actually wrote those bytes or that job 16768 consumed the selected trial-6 artifact.

Original V3C/41M Optuna databases, job read/write evidence, exact patient-level manifests and original intermediate checkpoints remain missing. Accordingly, **R1-4/A10 has no newly satisfied 40-rubric subrequirement**; maintain its 25.0% formal coverage pending stronger proof. No original files, patient-level data, checkpoints or session outputs are committed.