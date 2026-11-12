# Experimental design and reproduction

This branch extends [PR #9](https://github.com/Mateo197802/titan-v45-ecg-multihead/pull/9)
at `e5aa65ec1ef43cf5477e688c934577f5dcc4d75c`. It does not change any
published checkpoints, archived observations, manuscript text, figure,
abstract, conclusion, response letter or existing PR. SHA-256 identifies
bytes, not undocumented historical execution.

## Scope

1. The instrumented reconstruction uses sixteen hash-selected LUDB ECGs
   and separately evaluates the actual P6 secondary inference on every
   withheld LUDB ECG. Native waveform checks authenticate both headers
   and payloads. Scope is retrospective and includes no clinical or human
   referral inference.
2. The new ablation fits equal nonlinear heads in two arms. The
   intervention zeroes ten inputs **at the frozen backbone interface
   and before direct specialist composition**. This removes their
   direct columns and indirect input via global rhythm probabilities,
   without changing the shared waveform embedding. The identical
   frozen caches, record masks, loss, seed, batch order, architecture
   and calibration rule isolate that intervention for the new fitting
   procedure. Feature standardization and thresholds are separately fit
   within each arm using only its designated split. Equal per-ECG
   weighting avoids giving an ECG multiple votes because of window
   count. Held records do not select checkpoints, epochs or thresholds.
3. The selective utility analysis checks one original score-only route
   per ECG, then compares five fixed rules. Equal-coverage rank rules
   select without labels; ties use a hash, not diagnosis. The random
   rule reports expected counts and a ratio of those counts, not a
   data-selected random run. AURC integrates accepted opportunity error
   over ECG coverage, with ties admitted together. Reliability bins
   describe how raw signed margins rank risk; they do not treat margins
   as probabilities. Class score Brier and ECE are descriptive on the
   available references, not clinical calibration.

## Why development-only

SPH was already used to calibrate the original unlabeled coverage cuts
and its held results were inspected. LUDB was used as an external
transport diagnostic before this phase. Chapman and PTB-XL development
features had already been used for the matched logistic experiment. A
new analysis plan does not make the same outcomes unobserved again.
Chapman uses a documented record proxy, not authenticated patient IDs.
PTB-XL uses official patient folds and a sealed exact-signal check.
Different tasks across the two sources cannot estimate same-target
cross-source robustness.

No new cohort was authenticated with the necessary compatible leads,
reference coverage, access, and historical independence. The
[CODE-II access record](https://github.com/PetrusAbreu/code-ii)
and [Harvard-Emory access terms](https://bdsp.io/content/heedb/5.0/)
are leads for a subsequent preregistered study, not data used here.
The prior [transport protocol](https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/e5aa65ec1ef43cf5477e688c934577f5dcc4d75c/docs/reviewer_closure_experiments/PROTOCOL_FREEZE.md)
documents limits on treating sparse references or inferred negatives as
clinical labels. Chapman and PTB-XL fold 10 are not newly opened.

The two-point minimum effect is an engineering threshold for
interpreting this ablation, not a clinical decision threshold. Sample
size is fixed by the eligible frozen data. A benefit or equivalence
claim requires the simultaneous interval to clear the corresponding
margin, not merely a positive point estimate or a nonsignificant test.
The five seeds quantify training variation; they do not multiply the
number of independent patients. Full end-to-end reoptimization of both
41M networks would be a distinct factorial experiment, requiring
authorized reusable train and calibration manifests, sufficient paired
GPU allocations, and a fresh same-target test. This phase does not
substitute the frozen-feature result for that experiment.

## Reproduce

Use the exact code archives and native evidence in the execution
receipts. Execute on SLURM rather than on the login node. Install the
pinned native runtime and dependencies referenced by the launcher and
maintain the original authorization boundaries. From a compatible
checkout, use the documented argument order:

```bash
sbatch scripts/cedia/reviewer_two_comment.sbatch "$CODE" "$CEDIA_BASE" selective
sbatch scripts/cedia/reviewer_two_comment.sbatch "$CODE" "$CEDIA_BASE" morphology
sbatch --partition=gpu-dev --gres=gpu:a100-sxm4-40gb:1 --time=00:45:00 \
  scripts/cedia/reviewer_two_comment.sbatch "$CODE" "$CEDIA_BASE" runtime
python scripts/evaluation/verify_reviewer_two_comment_rigorous.py \
  --results outputs/results/reviewer_two_comment_rigorous \
  --docs docs/reviewer_two_comment_rigorous --zip PATH_TO_DELIVERY_ZIP
```

The verifier reconstructs aggregate accounting from the reported class
counts, checks artifact hashes, validates cohort and opportunity
denominators, and compares all ZIP members byte-for-byte. It does not
claim that a public aggregate is a substitute for the restricted
per-ECG source. The latter remains in CEDIA, together with all model
inputs and individual predictions.
