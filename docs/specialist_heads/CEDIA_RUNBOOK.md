# CEDIA Runbook: Frozen-Backbone Specialist Stage A

This runbook executes `specialist-heads-20261111-v2`, frozen before any new performance metric. V1 preflight jobs 33021 and 33026 failed before writing an inventory, extracting features, or training; V1 is superseded by [protocol amendment 01](PROTOCOL_AMENDMENT_20261111_01.md). No V1 results are carried forward. Historical weights, thresholds, and predictions remain unchanged. Do not submit GPU jobs until the V2 CPU preflight has been inspected and its split/label support is adequate.

## Isolation and resources

Use a new clone of the experiment branch and an output directory outside the raw data cache. Keep `private_inventory.json`, feature caches, row-level predictions, candidate checkpoints, and training receipts under the authorized CEDIA account with mode `0700` directories and `0600` files. Only sanitized aggregate metrics may be considered for publication.

The CPU preflight requests `cpu-dev`, 4 CPUs, 24 GB RAM, and up to 12 hours. Feature extraction requests one A100 40 GB, 8 CPUs, 64 GB RAM, and up to 12 hours. Stage A requests one A100 40 GB, 8 CPUs, 48 GB RAM, and up to 24 hours. The jobs use CEDIA `pytorch/2.2` and the existing Python 3.11 dependency archive; they do not unpack dependencies into the login environment. Repository-revision receipts use the system Git from inside the checkout for compatibility with the login environment.

The preflight uses at most four I/O workers, matching its CPU allocation, and emits aggregate stage counts only. This changes execution scheduling, not hashing, eligibility, duplicate handling, split assignment, QC, or metric definitions. Preserve each attempt's log and output directory; do not run overlapping scans against the same NFS cache.

## Submission template

Set these values in a shell on the authorized CEDIA login node, after cloning the exact pushed branch commit into a new, clean experiment checkout:

```bash
REPO="$HOME/Mateo Gavilanes/specialist-heads-20261111-v2/repo"
DATA_ROOT="$HOME/Mateo Gavilanes/titan_v45_data_cache"
DEPS_TAR="$HOME/Mateo Gavilanes/life-4620846-revision-20261028/python_deps.tar"
EXPERIMENT_ROOT="$HOME/Mateo Gavilanes/specialist-heads-20261111-v2"
ASSET_ROOT="$HOME/Mateo Gavilanes/specialist-heads-20261111-v2/release-assets-v0.1.0"
mkdir -p "$EXPERIMENT_ROOT/logs"
chmod 700 "$EXPERIMENT_ROOT" "$EXPERIMENT_ROOT/logs"
umask 077
sbatch --output="$EXPERIMENT_ROOT/logs/preflight-%j.out" \
  "$REPO/scripts/cedia/specialist_preflight.sbatch" \
  "$REPO" "$DATA_ROOT" "$EXPERIMENT_ROOT" "$DEPS_TAR"
```

Inspect only the aggregate `preflight_receipt.json` and the public-safe job log before authorizing the next stage. The initial-window signal QC reports finite-value fractions, flat leads, all-zero records, physical-unit summaries, and read failures descriptively; it does not filter records or apply a post hoc amplitude cutoff. Do not proceed if required classes lack positive/negative training support, a required source is missing, the configuration hash differs, or the label/source contract is contradicted.

If an implementation defect affects only PTB-XL window QC after a sealed inventory has been produced, preserve the original receipt and use `scripts/cedia/specialist_qc_reuse.sbatch` with a new output directory. This verifies the source receipt, inventory, frozen config, and current PTB-XL waveform hashes, then writes a separate receipt; it does not reuse a failed QC summary or compute model performance.

After the corrected preflight receipt passes, materialize only the five public model weights in an external cache. This deliberately omits the release's external-development dataset archives:

```bash
sbatch --output="$EXPERIMENT_ROOT/logs/assets-%j.out" \
  "$REPO/scripts/cedia/specialist_fetch_assets.sbatch" "$REPO" "$ASSET_ROOT"
```

Before using the GPU, compare all five cache files' sizes and SHA-256 values with `release-manifest.json`. Feature extraction and training then use:

```bash
sbatch --output="$EXPERIMENT_ROOT/logs/features-%j.out" \
  "$REPO/scripts/cedia/specialist_extract_features.sbatch" \
  "$REPO" "$DATA_ROOT" "$EXPERIMENT_ROOT/preflight" "$ASSET_ROOT" \
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
- Every record in either pinned public V4.5 P6/P8 evaluation manifest is excluded from all new rhythm training, validation, calibration, and source-holdout splits. Exact-byte copies of those known evaluation waveforms are excluded too; manifest hashes are checked before inventory creation.
- Records whose header WFDB cannot parse are retained in the private inventory as explicitly excluded with `invalid_wfdb_header`; sampling metadata is never guessed or repaired. Their counts reduce reported class support.
- PTB-XL folds 1-7 train, fold 8 selects epoch, and fold 9 is patient-hash split into calibration/internal evaluation. Fold 10 is never read.
- CPSC patient identifiers are unavailable and Georgia patient identifiers are not supplied. Rhythm intervals on those sources are record-clustered, not patient-clustered.
- Exact raw-file SHA-256 duplicates are excluded. Near-duplicate signals are not ruled out.
- SPH, V3H, locked evaluation data, and manual-review queues are excluded. Independent external validation remains `NOT_RUN`.
- Stage B, a new Optuna search, and new quarantine/fallback policy are not part of this Stage A run.
