# R2-3f: morphology input contract and experimental contrasts

The source is the [recovered candidate extractor at the pinned replay baseline](https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/2677a3333069c16915cb71acd55d0f0176570bcf/scripts/cedia/recovery_candidates/morphology_features_v4.py), LF-normalized SHA-256 2bd1c1822ed72d1531b1f62712d8007c7e2f21009056ad1a3ee905f37051fc3d. Its identity is verified for this candidate, not for the exact historical loader. The fixed waveform path supplies 12 channels and 1,250 samples at 125 Hz with its separate lead mask; the feature extractor accepts a channel-by-sample array and has no independent mask input. Missing or unreadable whole records remain unscored by the waveform pipeline. No waveform is imputed to recover an absent record.

The candidate converts samples to float64 and replaces NaN and infinities with zero; finite extreme samples are not winsorized by this extractor. It uses channel 2 if its standard deviation exceeds 1e-6, otherwise the maximum-variance channel. On absolute deviation from the channel median, peaks are local maxima at least the larger of the 88th percentile and mean plus 0.8 standard deviations; greedy distance exclusion uses 0.28 s. RR uses positive peak-index intervals in seconds. Spectral power is the squared magnitude of the real FFT, averaged across leads before forming ratios.

| Normalized vector entry | Raw definition | Raw unit | Divisor |
|---|---|---|---:|
| hr_median_bpm | 60 divided by median RR | beats/min proxy | 220 |
| rrv_cv | Population SD(RR) / mean(RR) | ratio | 1 |
| rrv_rmssd_ms | Square root of mean squared consecutive RR differences × 1,000 | ms | 500 |
| qrs_width_proxy_ms | Median span of samples above max(35% segment maximum, 70th percentile) of the median-centered magnitude within ±0.18 s of a peak | ms proxy | 220 |
| p_to_r_proxy_ms | Median time from the maximum absolute median-centered deflection 0.08–0.28 s before a peak to that peak; only candidate lags 60–320 ms | ms proxy | 320 |
| qrs_band_ratio | 5–18 Hz power / total power | ratio | 1 |
| lowfreq_ratio | 0–0.7 Hz power / total power | ratio | 1 |
| hf_ratio | 35 Hz–Nyquist power / total power | ratio | 1 |
| lead_corr_abs_mean | Mean absolute off-diagonal Pearson correlation of leads with SD > 1e-6 | ratio | 1 |
| limb_qrs_asymmetry | (5–18 Hz power lead I − power aVF) / max(sum of the two powers, 1e-12) | signed ratio | 1 |

Nonfinite derived values become zero; total power at or below 1e-12 gives a zero band ratio. Scaled finite values are clipped to [0,1], except limb asymmetry in [-1,1], and emitted as float32. Peak count is an intermediate, not a vector element. These are not clinically validated interval measurements.

In the pinned extraction path, rhythm and pathology both pass morphology to the frozen backbone and into the specialist feature composition. The released rhythm feature width is 681 and the released P4 width 670; event features are separate and are held fixed by the morphology intervention.

1. **Replay:** run the archived reconstruction of each retained panel and compare with its saved predictions. Decision agreement alone does not satisfy the 1e-5 numerical tolerance; missing or incompatible ECGs stay visible.
2. **Fixed-weight sensitivity:** replace the ten normalized inputs with zeros while holding the released architecture and weights fixed. A score change measures sensitivity to that intervention, not the value of retraining.
3. **Matched head retraining:** extract both arms again with the same immutable backbones and fit new, equal-dimensional logistic heads with identical class-masked training and calibration rules. Report paired held differences and separate release-baseline metrics on the same compatible observations. This is a frozen-backbone ablation, not a from-scratch backbone comparison. PTB-XL grouping uses patient folds; Chapman uses the documented record-as-patient proxy. No claim of independence from all prior model development is made.
