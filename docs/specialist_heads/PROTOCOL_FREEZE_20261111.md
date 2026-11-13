# TITAN Specialist Heads: Frozen Pilot Protocol

**Study:** `specialist-heads-20261111-v1`
**Protocol source:** [`study_20261111_v1.json`](../../configs/specialist_heads/study_20261111_v1.json)
**Scope:** new post-hoc development experiment. It does not reproduce or replace historical V4.5 training, checkpoints, thresholds, or reported metrics.

**Status:** Superseded before any feature extraction or performance evaluation. The V1 preflight attempts failed before creating an inventory or receipt. See [protocol amendment 01](PROTOCOL_AMENDMENT_20261111_01.md) and use V2 only.

## Models

The five published V3F/V3AG backbone and specialist assets are read-only baselines. Only new class-wise specialist heads may be optimized. The V3F/V3AG feature extractors remain frozen. Primary6 is trained as a six-output head; Primary8 as an eight-output head; P4 as four independent binary outputs.

## Rhythm labels and partitions

Rhythm labels come from SNOMED-CT diagnosis codes in the PhysioNet/CinC Challenge 2021 header contract, not from the cached PTB-XL convenience map. A missing or empty `Dx` header is excluded; a nonempty scored Challenge `Dx` list is interpreted under that benchmark's closed-set multi-label contract, and absent target codes are zeros only within that contract. This is not a claim that a missing clinical diagnosis is a confirmed negative. Unsupported source endpoints remain masked. The frozen mapping groups complete/incomplete RBBB with RBBB, SVPB with PAC, and VPB with PVC, as the Challenge scoring scheme does. This measures agreement with dataset ECG statements, not longitudinal clinical diagnoses. See the [Challenge 2021 data and scoring documentation](https://physionet.org/content/challenge-2021/1.0.3/) and its [source/mapping paper](https://physionet.org/files/challenge-2021/1.0.2/papers/2021ChallengePaperPMEA.pdf).

Available Chapman-Shaoxing records are split by a stable hash of the source-relative record key: 80% training, 10% early-stopping validation, and 10% threshold calibration. The source reports 10,247 patients for 10,247 recordings, so record is used as the patient-group proxy; the absence of row-level patient IDs remains a limitation. The available CPSC2018 training-source copy joins training only. Georgia is held out as a development source, with the previously used public-release records and exact duplicate waveforms excluded. Georgia patient IDs are unavailable, so intervals there cannot be described as patient-clustered. Endpoints with no positive source support are not scored.

## Pathology labels and partitions

The P4 experiment uses PTB-XL v1.0.3 only. A class-positive requires its SCP statement with likelihood greater than zero. A negative control requires an explicit `NORM` statement and no P4 target code whose value is positive or unknown. All other rows are masked. This is a code-statement case-control experiment, not an estimate of all-comer pathology prevalence or clinical diagnosis accuracy.

Official folds 1-7 train, fold 8 selects the epoch, and fold 9 is divided by patient into calibration and internal evaluation halves. Fold 10 is excluded from all new work. Patient IDs and row-level artifacts remain in authorized CEDIA storage.

## Preprocessing and duplicate policy

The new experiment uses the repository's declared reconstructed WFDB path at 125 Hz; it is not identified as the missing historical loader. Rhythm windows use the existing 10-second window schedule and record aggregation: mean logits for P6, mean sigmoid probabilities for P8. P4 uses the first fixed 10-second window. The morphology and event-extractor source hashes are pinned in the JSON protocol.

Raw waveform-file SHA-256 is used to remove byte-identical signals before partitioning. This does not detect every re-encoded or near-duplicate ECG. Preflight inspects at most the first 10 seconds for finite values, flat leads, zero signals, physical-unit labels, and amplitude summaries stratified by units; these are descriptive only and do not introduce a post hoc amplitude exclusion. No independent cross-dataset patient linkage is available, so the resulting source holdout is not a confirmatory external validation.

## Public source and copy provenance

The public PhysioNet Challenge 2021 v1.0.3 and PTB-XL v1.0.3 pages specify CC BY 4.0 access terms ([Challenge 2021](https://physionet.org/content/challenge-2021/1.0.3/), [PTB-XL](https://physionet.org/content/ptb-xl/1.0.3/)); the Challenge 2020 v1.0.2 page also specifies CC BY 4.0 for its source package ([Challenge 2020](https://physionet.org/content/challenge-2020/1.0.2/)). The CEDIA cache is an existing authorized local copy and is not redistributed here. Preflight hashes each waveform and verifies the PTB-XL metadata files against the pinned hashes, but the raw cache contains no upstream source checksum manifests for the Challenge waveform trees. Therefore the selected Challenge files' exact upstream release provenance is not cryptographically certified by this experiment; their source/version remains a documented cache-level attribution, not a proven download chain.

## Training and analysis

Stage A freezes both original backbones and trains only `ClassWiseBinaryMLP` heads (hidden width 192, dropout 0.25; AdamW at 0.001; up to 40 epochs; patience 6). The primary candidate is fixed as source-balanced weighted BCE with seed `20261111`; the positive multiplier is computed from training-only support and clipped to [1, 10]. Two predeclared ablations use the same data, architecture, seeds (`20261111`, `20261112`, `20261113`) and stopping contract: source-balanced BCE without a positive multiplier, and focal loss (gamma 2; positive alpha from training-only weighted prevalence). They are descriptive sensitivity analyses, not candidates to select by Georgia, CPSC, or PTB-XL fold-9 results. Early stopping is computed after ECG-level window aggregation, not by treating windows as independent validation records.

One complementary rhythm leave-one-source-out sensitivity trains the fixed weighted-BCE model on Chapman plus eligible Georgia records and scores CPSC. Georgia records previously present in a public V4.5 evaluation and exact-byte duplicates are excluded. This is a development-domain comparison, not independent external validation; CPSC and Georgia lack validated patient IDs. PTB-XL supplies only one eligible source here, so P4 cannot support a leave-one-source-out claim.

No Optuna search is run in this bounded Stage-A pilot: the architecture and small loss comparison are predeclared, and the source holdouts must not become tuning sets. Candidate thresholds are fit on the separate calibration split; original baseline thresholds remain unchanged. Partial backbone fine-tuning is deferred unless frozen-head diagnostics justify it and is not implicitly authorized by a positive score on a holdout.

Report class/source supports, all evaluable metrics, patient-grouped percentile bootstrap intervals where patient keys exist, and record-level intervals otherwise with their unit named. The primary candidate is the only confirmatory-within-development comparison; loss/seed ablations are exploratory. Do not infer equivalence to original training, clinical validation, or independent external validation. `INDEPENDENT_EXTERNAL_VALIDATION` remains `NOT_RUN`.
