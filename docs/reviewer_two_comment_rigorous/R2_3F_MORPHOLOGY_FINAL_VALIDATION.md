# R2-3f: Final morphology validation

> Figure 5 - What are the 10 morphology features and how are they calculated? Why there is an arrow going in the "Pathology specialist" but such arrow is not present for "Rhythm specialist". Check the arrows in all block-diagrams – are they necessary everywhere (do they show any relation between the blocks)? For example, what is the meaning of the arrows between the blocks in Figure 6?

**IMPLEMENTATION_VERIFIED; EXPERIMENT_COMPLETED for the reconstructed candidate.**

CEDIA GPU job 33796 ran the hash-verified extractor, both backbones and all three specialists on 16 label-blind selected LUDB ECGs. Both same-batch forwards agreed exactly on these inputs. This is a repeatability statement for the reconstructed configuration, not a historical reproduction guarantee.

## Executed signal and tensor contract

WFDB physical mV, canonical I, II, III, aVR, aVL, aVF, V1–V6, original 500 Hz. The executable trace checked a causal third-order Butterworth 0.5–45 Hz on nonconstant leads, polyphase 1:4 downsampling, the padded central ten seconds, per-lead z-score, and a 125 Hz morphology call. The independent fixture pipeline and actual preprocessor agreed within its fixed numeric check. Signal: 12×1250; lead mask: 12; morphology: 10. The extractor selects II when nonflat, otherwise the highest-variance lead. It thresholds median-centered magnitude at max(p88, mean + 0.8 SD) and enforces 0.28 s peak spacing.

| Observed consumer | Input width | Morphology |
| --- | ---: | --- |
| Both V3F/V3AG backbones | 12×1250 + mask + 10 | Distinct auxiliary input |
| Global rhythm, both backbones | 650 | Direct 640–649 (zero-based) |
| Global pathology, both backbones | 640 | No morphology path; consumes the waveform/mask embedding |
| P6 and P8 specialist | 681 | Direct 640–649 plus separate score/event fields |
| P4 specialist | 670 | Direct 640–649 plus separate score fields |

Strict weight loading bound all five published artifacts to their SHA-256. Stored widths, not redundant metadata, govern loading (rhythm declared/stored: {'P6': {'declared': 192, 'stored': 512, 'metadata_matches': False}, 'P8': {'declared': 192, 'stored': 512, 'metadata_matches': False}}; P4 stored hidden width: 512). Both specialist arrows therefore denote direct feature input. The pathology specialist can additionally receive the indirect effect via global rhythm probabilities; the shared waveform/mask embedding and global pathology head do not consume the morphology vector. An arrow between blocks is justified only by a tensor or rule actually passed.
The loaded V3F and V3AG model objects each contained 58,352,219 parameters including their global heads, before attaching the separate specialists. This is a direct runtime count for these two released assets, not a count for the different historical 41M experiments.

## Ten formulas and numerical checks

| Descriptor | Raw computation | Scale | Fixture observed |
| --- | --- | ---: | ---: |
| hr_median_bpm | 60 / median positive RR in seconds | 220 | 66.66667 |
| rrv_cv | population SD(RR) / mean(RR) | 1 | 0.1111111 |
| rrv_rmssd_ms | 1,000 × RMS of successive RR differences | 500 | 200 |
| qrs_width_proxy_ms | median span above max(35% local maximum, p70) within ±0.18 s | 220 | 24 |
| p_to_r_proxy_ms | median lag to maximal pre-peak median-centered deflection 0.08–0.28 s before peak; retain 60–320 ms | 320 | 160 |
| qrs_band_ratio | 5–18 Hz / total one-sided FFT power | 1 | 0.2857143 |
| lowfreq_ratio | 0–0.7 Hz / total one-sided FFT power | 1 | 0.07142857 |
| hf_ratio | 35 Hz–Nyquist / total one-sided FFT power | 1 | 0.6428571 |
| lead_corr_abs_mean | mean absolute off-diagonal Pearson r across nonflat leads | 1 | 1 |
| limb_qrs_asymmetry | (I−aVF) / max(I+aVF, 1e−12) in 5–18 Hz power | 1 | 0.6 |

Ratios use mean power across leads unless indicated. Nonfinite samples are replaced with zero; nonfinite features default to zero, and normalized values clip to [0,1] (signed asymmetry [−1,1]) as float32. The pulse fixture found three expected peaks. **Detected failure mode:** the flat/invalid-sample fixture produced 36 spurious plateau peaks, a nonzero heart-rate proxy and a nonzero P-to-R proxy. The formulas match controlled examples; they are not universally physiologically valid or validated interval measurements. No retrospective patch was applied.

## New paired head training

CPU job 33795 fit five matched seeds per arm, same MLP size and same ECG masks. Both arms use fixed backbone representations. The 98.333% paired component intervals control the three primary profile contrasts; the minimum effect is ±2.00 points. The class-wise JSON includes sensitivity, specificity, AUROC, average precision, Brier, ECE, support, training time and per-seed results. File name notwithstanding, this study is **exploratory**, not confirmatory.

| Profile | Endpoints evaluated | Mean Δ macro-F1 | Simultaneous interval | Interpretation | CPU fit seconds |
| --- | ---: | ---: | --- | --- | ---: |
| P6 | 6/6 | +0.17 pp | [-0.70 pp, +1.03 pp] | effects_within_prespecified_margin | 32.2 |
| P8 | 8/8 | -0.11 pp | [-0.76 pp, +0.60 pp] | effects_within_prespecified_margin | 43.7 |
| P4 | 4/4 | +0.31 pp | [-0.36 pp, +1.17 pp] | effects_within_prespecified_margin | 7.5 |

| Profile | Class | Held positive/negative | Mean paired Δ F1 | Range across seeds |
| --- | --- | ---: | ---: | --- |
| P6 | AFIB | 201/1050 | +0.59 pp | [-2.14 pp, +1.89 pp] |
| P6 | SB | 452/799 | +0.29 pp | [-0.02 pp, +0.60 pp] |
| P6 | STACH | 193/1058 | +0.77 pp | [-0.03 pp, +1.46 pp] |
| P6 | RBBB | 50/1201 | -0.13 pp | [-0.88 pp, +0.63 pp] |
| P6 | 1AVB | 33/1218 | -0.66 pp | [-5.38 pp, +4.60 pp] |
| P6 | PVC | 39/1212 | +0.12 pp | [-1.97 pp, +2.02 pp] |
| P8 | AFIB | 201/1050 | +0.59 pp | [-2.14 pp, +1.89 pp] |
| P8 | SB | 452/799 | +0.29 pp | [-0.02 pp, +0.60 pp] |
| P8 | STACH | 193/1058 | +0.77 pp | [-0.03 pp, +1.46 pp] |
| P8 | NSR | 216/1035 | -0.08 pp | [-0.94 pp, +0.64 pp] |
| P8 | RBBB | 50/1201 | -0.13 pp | [-0.88 pp, +0.63 pp] |
| P8 | PAC | 22/1229 | -1.77 pp | [-5.22 pp, +1.61 pp] |
| P8 | 1AVB | 33/1218 | -0.66 pp | [-5.38 pp, +4.60 pp] |
| P8 | PVC | 39/1212 | +0.12 pp | [-1.97 pp, +2.02 pp] |
| P4 | ASMI | 51/135 | +0.29 pp | [+0.00 pp, +1.45 pp] |
| P4 | LVH | 45/135 | +0.06 pp | [+0.00 pp, +0.29 pp] |
| P4 | IMI | 57/135 | +0.89 pp | [-5.33 pp, +6.44 pp] |
| P4 | ISC_ | 26/135 | +0.00 pp | [+0.00 pp, +0.00 pp] |

Ranges are training variability, not confidence intervals. Endpoint contrasts are descriptive and rare classes can have large instability; no class-wise significance claims are made. This is not a full-network retraining experiment, an effect on the released weights, or proof of transfer to a new source. Same-target cross-source transport and verified patient independence for Chapman are not established.

The PR #9 P8 linear-head estimate was +1.46 pp, exploratory IC95% [+0.16,+2.76] pp, post-hoc Holm p=0.1356. It is a prior study on inspected data, not another independent replication sample. The new comparisons, including adverse effects, are reported without replacing the earlier results.

## Fixed-input perturbations

Runtime: NVIDIA A100-SXM4-40GB; PyTorch 2.10.0+cu128, CUDA 12.8, NumPy 2.2.6, SciPy 1.15.3. Below are maximum absolute differences versus the reconstructed same-batch reference, not differences versus June output.

| Perturbation | P6 logit | P8 logit | P4 probability | P4 > 1e−5 |
| --- | ---: | ---: | ---: | ---: |
| singleton | 3.814697e-06 | 3.814697e-06 | 2.086163e-07 | 0 |
| zero_morphology | 0.8419437 | 0.9125252 | 0.008816719 | 62 |
| no_bandpass | 15.85842 | 13.55521 | 0.5157447 | 64 |
| no_standardization | 15.27859 | 13.97916 | 0.8490988 | 64 |
| drop_lead_II | 3.331774 | 2.676664 | 0.3224666 | 64 |
| CPU | 0.006747246 | 0.007545471 | 0.0005306602 | 57 |

**Historical inference:** [root-cause report](R2_3F_HISTORICAL_REPLAY_ROOT_CAUSE.md). Exact June input and loader identity are not demonstrated. The new instrumented job does not erase the 836/962 out-of-tolerance historical P4 comparisons.
