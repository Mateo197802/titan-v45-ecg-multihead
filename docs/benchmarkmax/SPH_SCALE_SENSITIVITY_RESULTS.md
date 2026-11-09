# SPH Uniform-Scale Sensitivity Results

**Status:** completed label-blind diagnostic. This is not a performance
evaluation, physical-unit certification, clinical validation, or independent
test. The V4.5 SPH protocol, checkpoints, thresholds, saved predictions and
manuscript were not changed.

## Frozen Probe

The probe selected 128 records deterministically from the already-scored SPH
source using the committed hash-based selector. Reference labels were not read
or used. For each record, the frozen P4, P6 and P8 pipeline was replayed at the
stored waveform scale and after multiplying the waveform globally by 0.5 or
2.0. The frozen V4.5 protocol and checkpoint hashes were checked by the runner.
The input HDF5 does not declare physical units, and this probe does not assert
that the signals are calibrated in millivolts.

## Measured Results

The scale-1 replay matched the archived decisions for all 128 records in each
profile. The largest per-class probability difference from the archived
predictions is shown below; no thresholded class label, top-1 decision, or P8
fallback changed.

| Profile | Maximum absolute score difference | Class-label changes | Top-1 changes | Fallback changes |
| --- | ---: | ---: | ---: | ---: |
| P4 | 4.172325e-07 | 0 | 0 | 0 |
| P6 | 1.591166e-07 | 0 | 0 | 0 |
| P8 | 1.788139e-07 | 0 | 0 | 0 |

Uniform scaling produced exactly identical floating-point scores and decisions
at both perturbation factors:

| Scale vs. 1.0x | Profile | Maximum absolute score change | Changed class outputs | Top-1 changes | Fallback changes |
| ---: | --- | ---: | ---: | ---: | ---: |
| `0.5x` | `P4` | 0 | 0/512 | 0/128 | 0/128 |
| `0.5x` | `P6` | 0 | 0/768 | 0/128 | 0/128 |
| `0.5x` | `P8` | 0 | 0/1024 | 0/128 | 0/128 |
| `2.0x` | `P4` | 0 | 0/512 | 0/128 | 0/128 |
| `2.0x` | `P6` | 0 | 0/768 | 0/128 | 0/128 |
| `2.0x` | `P8` | 0 | 0/1024 | 0/128 | 0/128 |

The invariance is consistent with the frozen lead-wise z-score normalization,
which removes a uniform nonzero gain factor before inference. It does not show
robustness to per-lead gain mismatch, clipping or saturation, additive noise,
baseline drift, lead reversal, missing leads, or differences in acquisition
systems. It also does not establish physical units, signal quality, or clinical
performance. The sample is a sensitivity probe only and does not change the
full-population V4.5 results.

## Execution And Provenance

- CEDIA SLURM job `32761`: `COMPLETED`, exit `0:0`, elapsed `00:01:11`, one
  NVIDIA A100-SXM4-40GB, 4 CPUs, 24 GB requested memory.
- The runner enforced the frozen runtime: Python 3.11.14, torch 2.10.0+cu128,
  CUDA 12.8, NumPy 2.2.6, SciPy 1.15.3, h5py 3.13.0, wfdb 4.3.0 and
  zstandard 0.23.0.
- V4.5 source commit: `eb1c67b9229af875a9f868797b0c2f5c546e3dac`. V4.6 code
  at execution: CEDIA commit `a2353f0863f05e4b1ea844f9b0c4dd4e270a6c85`,
  tree `d70a7342a122a63e37a1f3d93dd9b626b4141298`, matching public source
  commit `5ea692c1a4b8c651700e9b03a34981a80b419488` at execution time.
- Aggregate-only receipt:
  [`sph_scale_sensitivity_32761.json`](../../outputs/results/benchmarkmax/sph_scale_sensitivity_32761.json),
  SHA-256 `63c03aabb91d9507ee19151b27a320c2c6faa4471f8eda1d2dccb33f4fa8c694`.
  It contains no signal, record identifier, patient identifier, reference
  label, or row-level prediction.
- The first scheduler attempt, job `32760`, failed before producing an
  aggregate because its configured stdout/stderr directory did not exist. The
  corrected job `32761` used the existing private output directory. No result
  from job `32760` is used.

Validate the public receipt from the repository root:

```powershell
python scripts/benchmarkmax/verify_sph_scale_sensitivity.py `
  --report outputs/results/benchmarkmax/sph_scale_sensitivity_32761.json `
  --expected-job-id 32761 `
  --expected-experiment-commit a2353f0863f05e4b1ea844f9b0c4dd4e270a6c85
```
