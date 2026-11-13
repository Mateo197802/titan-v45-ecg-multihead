# Optuna evidence disposition

Scope: TITAN V4.5, reviewer item A-06 and the Optuna row of R1-4. The
[versioned V3C summary](https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/8487b51/outputs/results/optuna/v3c_promoted_configuration.json)
and [subsequent trial snapshot](../../tests/figure_evaluation/tables_snapshot/optuna_trials.csv)
are historical records, not the original Optuna database.

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| V3C public summary | Study identifier, recorded scalar objective, TPE seed 197813, eight saved hyperparameters, 9 completed of 12 planned. | Original database, sampler replay, full trial provenance or promotion into final weights. |
| Nine-row CSV snapshot, introduced by `f4b744a` | Trial 6 has the largest recorded ranking score (0.6245117257); its eight parameters match the V3C summary to stored precision. Trial 8 has the largest peak composite (0.6509403856), a distinct field. | Identities or states of remaining trials, timestamps, intermediate values or independently reproduced scores. |
| [Recovered code](../recovery-status-20261029.md) | Inventory-matched historical Optuna source. The public runner is separately versioned. | Proof of which objective version, split and data were executed in a particular study. Do not conflate a scalar in the summary with a trace of the real historical objective. |
| Surviving partial scheduler/log evidence | Jobs 13169, 13172 and 13181 are historical pointers. The available output contains two recorded trial values and one failed trial; the three SLURM jobs themselves are recorded as failed. | Linkage of those fragments to the nine-row V3C snapshot or to the final V3F/V3AG checkpoints. A recorded trial is not a successful SLURM run. |
| Original SQLite or complete source export | **Not available in the inspected sources.** | No SHA-256 is supplied for the missing original. |

The manuscript should not report the original optimization or three-trial
comparison as verified, or attribute the final weights to trial 6. A methods
description may identify settings supported by checkpoint metadata or release
contracts without attributing them to a historically demonstrated search.
The V3C summary can be cited as a partial archival record, separate from the
canonical specialist metrics and from any new external-source study.

New receipt-level findings for jobs 13169, 13172 and 13181 are documented in
[Optuna 41M archived evidence reconciliation](OPTUNA_41M_NEW_EVIDENCE.md).
They distinguish two database generations, record two bounded completed-trial
observations and retain the failed SLURM states. They do not recover SQLite
bytes or establish a trial-to-published-checkpoint link; the original database
remains unavailable in the inspected package.

To close historical reconstruction, recover the original study or a complete
export with its version, objective, trial states and values, dataset/split
identities, and a job/configuration receipt binding the promoted trial to
the final checkpoints by hash. Preserve originals and do not rerun Optuna
to manufacture a historical result.
