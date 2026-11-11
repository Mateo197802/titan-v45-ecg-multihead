# CEDIA Runbook: Frozen-Backbone Specialist Stage A

This runbook executes the already frozen `specialist-heads-20261111-v1` study. It does not modify historical weights, thresholds, or prediction files. Do not submit the GPU jobs until the CPU preflight has been inspected and its split/label support is adequate.

## Isolation and resources

Use a new clone of the experiment branch and an output directory outside the raw data cache. Keep `private_inventory.json`, feature caches, row-level predictions, candidate checkpoints, and training receipts under the authorized CEDIA account with mode `0700` directories and `0600` files. Only sanitized aggregate metrics may be considered for publication.

The CPU preflight requests `cpu-dev`, 4 CPUs, 24 GB RAM, and up to 12 hours. Feature extraction requests one A100 40 GB, 8 CPUs, 64 GB RAM, and up to 12 hours. Stage A requests one A100 40 GB, 8 CPUs, 48 GB RAM, and up to 24 hours. The jobs use the pinned CEDIA `pytorch/2.2` module and the existing Python 3.11 dependency archive; they do not unpack dependencies into the login environment.

## Submission template

Set these values in a shell on the authorized CEDIA login node, after cloning the exact pushed branch commit into a new, clean experiment checkout:

```bash
REPO="$HOME/Mateo Gavilanes/specialist-heads-20261111-v1/repo"
DATA_ROOT="$HOME/Mateo Gavilanes/titan_v45_data_cache"
DEPS_TAR="$HOME/Mateo Gavilanes/life-4620846-revision-20261028/python_deps.tar"
EXPERIMENT_ROOT="$HOME/Mateo Gavilanes/specialist-heads-20261111-v1"
mkdir -p "$EXPERIMENT_ROOT/logs"
chmod 700 "$EXPERIMENT_ROOT" "$EXPERIMENT_ROOT/logs"
umask 077
sbatch --output="$EXPERIMENT_ROOT/logs/preflight-%j.out" \
  "$REPO/scripts/cedia/specialist_preflight.sbatch" \
  "$REPO" "$DATA_ROOT" "$EXPERIMENT_ROOT" "$DEPS_TAR"
```

Inspect only the aggregate `preflight_receipt.json` and the public-safe job log before authorizing the next stage. The initial-window signal QC reports finite-value fractions, flat leads, all-zero records, physical-unit summaries, and read failures descriptively; it does not filter records or apply a post hoc amplitude cutoff. Do not proceed if required classes lack positive/negative training support, a required source is missing, the configuration hash differs, or the label/source contract is contradicted.

After preflight review, feature extraction and training use:

```bash
sbatch --output="$EXPERIMENT_ROOT/logs/features-%j.out" \
  "$REPO/scripts/cedia/specialist_extract_features.sbatch" \
  "$REPO" "$DATA_ROOT" "$EXPERIMENT_ROOT/preflight" \
  "$EXPERIMENT_ROOT/features" "$DEPS_TAR"

sbatch --output="$EXPERIMENT_ROOT/logs/stage-a-%j.out" \
  "$REPO/scripts/cedia/specialist_train_evaluate.sbatch" \
  "$REPO" "$EXPERIMENT_ROOT/features" \
  "$EXPERIMENT_ROOT/stage-a" "$DEPS_TAR"
```

Submit each stage only after the prior job completed successfully and its receipt was checked. These scripts are templates; this repository commit does not claim a job was submitted or completed.

## Scientific boundaries

- The head-only candidates are new experiments on frozen released backbones, not recovered historical training.
- Chapman validation selects epochs; Chapman calibration selects new candidate thresholds. Georgia and CPSC source-held-out results do not tune the candidate.
- PTB-XL folds 1-7 train, fold 8 selects epoch, and fold 9 is patient-hash split into calibration/internal evaluation. Fold 10 is never read.
- CPSC patient identifiers are unavailable and Georgia patient identifiers are not supplied. Rhythm intervals on those sources are record-clustered, not patient-clustered.
- Exact raw-file SHA-256 duplicates are excluded. Near-duplicate signals are not ruled out.
- SPH, V3H, locked evaluation data, and manual-review queues are excluded. Independent external validation remains `NOT_RUN`.
- Stage B, a new Optuna search, and new quarantine/fallback policy are not part of this Stage A run.
