# SPH Post-Dedup Support Results

**Status:** completed aggregate support audit; no model was trained or evaluated.

## Execution And Provenance

CEDIA SLURM job `32815` completed on `cpu-dev` with exit code `0:0` in 1 minute 18 seconds. It ran commit `158dce34588df2668703a3b4f73e907ddf5c39cc`, using the frozen configuration SHA-256 `b4b05d848fdb432cd39375738209be21090a8c3f46230c3b19680567746d516f` and runtime Python 3.11.14, NumPy 2.2.6, h5py 3.13.0. The source and runtime dependency hashes are recorded in the aggregate JSON.

The source metadata contains 25,770 ECGs from 24,666 patients. All 25,770 signals passed the frozen duration, HDF5, finiteness, and non-flat checks. The label-blind SHA-256 scan found 168 exact-signal groups with 168 excess records. Following the frozen policy of excluding every record in any duplicate group, 336 records were removed; 25,434 unique-signal ECGs from 24,509 patients remained. This matches the exact-duplicate counts in the prior source inventory and PAC pilot.

The scan did not detect near-duplicates, perform V3AG morphology extraction, or verify branch-specific model preprocessing. Labels were joined only after the signal and duplicate set was fixed. The third patient partition is the previously used exploratory PAC holdout, not an untouched or confirmatory test.

## Post-Dedup Statement Support

Each cell is `positive ECG records / patients with at least one positive ECG`. Denominators are 17,916 train ECGs / 17,265 patients, 3,821 development ECGs / 3,686 patients, and 3,697 exploratory-holdout ECGs / 3,558 patients. Totals are 25,434 ECGs / 24,509 patients. A missing AHA code means the statement was not recorded; it is not treated as a clinically adjudicated negative.

| Endpoint | Train | Development | Exploratory holdout | Total |
| --- | ---: | ---: | ---: | ---: |
| ASMI (code 165) | 64 / 60 | 7 / 6 | 16 / 15 | 87 / 81 |
| IMI (code 161) | 84 / 83 | 21 / 20 | 13 / 13 | 118 / 116 |
| LVH (code 142) | 142 / 137 | 40 / 38 | 25 / 25 | 207 / 200 |
| PAC (code 30) | 361 / 356 | 87 / 83 | 84 / 82 | 532 / 521 |
| PVC (code 60) | 720 / 705 | 163 / 159 | 170 / 161 | 1,053 / 1,025 |
| RBBB (code 106) | 512 / 480 | 81 / 76 | 101 / 94 | 694 / 650 |

## Interpretation

The audit supports a limited exploratory head study for PAC, PVC, and RBBB based on statement counts, subject to a frozen training protocol and branch-input implementation. LVH has modest development support. ASMI has only six positive development patients and IMI twenty; neither supports a reliable threshold or a complex model evaluation on this split. A regularized linear head on frozen features is a more defensible candidate than a high-capacity head for the rare endpoints, but this support audit alone does not authorize or validate that choice.

No metric, confidence interval, classifier decision, or clinical conclusion was computed here. SPH remains previously observed development/adaptation data. These counts do not establish independent generalization, clinical accuracy, or final external validation. No manuscript or V4.5 historical result was changed.

## Failed Preflight

Job `32814` failed after 3 seconds while importing h5py because the wrapper had omitted the pinned NumPy dependency archive. It failed before opening the SPH waveform archive; no records were scanned and no result was produced. The wrapper was corrected to verify and mount both dependency archives. The failure is preserved in the experiment registry.

## Artifacts

- Aggregate: [sph_postdedup_support_32815.json](../../outputs/results/benchmarkmax/sph_postdedup_support_32815.json), SHA-256 `c267b6f47cfacc17b56fd95e4bf60bc4b56c7ebd818d33a5ad473771cd1c4306`.
- CEDIA verification receipt: [sph_postdedup_support_32815.verification.json](../../outputs/results/benchmarkmax/sph_postdedup_support_32815.verification.json), SHA-256 `286f85b34dd2f925a9f3d11395dc30fce0a080378c8878b88e522608a5ce1c37`.
- Frozen protocol: [SPH_POSTDEDUP_SUPPORT_PROTOCOL.md](SPH_POSTDEDUP_SUPPORT_PROTOCOL.md).
- Frozen configuration: [sph_postdedup_support.json](../../configs/benchmarkmax/sph_postdedup_support.json).

The aggregate and receipt contain no ECG IDs, patient IDs, signals, diagnostic rows, or model scores. CEDIA retains the source files and private job logs.

After transfer, the stricter repository verifier was also run locally against the public aggregate. It rejected unexpected fields, rechecked all support denominators, passed, and produced the same receipt SHA-256 as the CEDIA output.
