# Recovered Specialist Feature Definitions

This documents recovered code, not newly validated clinical interval measurements. The [source archive and identity manifest](provenance/README.md) distinguish inventory-matched V4.5 source from the older morphology candidate. No manuscript or editorial response is regenerated here.

## Input Composition

The inventory-matched `specialist_input_from_base` concatenates, in order:

1. Backbone features640.
2. Normalized morphology10, when enabled.
3. Eight categorical-softmax backbone rhythm probabilities in the declared primary class order.
4. Backbone rhythm probabilities in the checkpoint's specialist class order.
5. Four sigmoid backbone pathology probabilities in `ASMI, LVH, IMI, ISC_` order.
6. Signal-event features, only when the stored checkpoint contract enables them.

P4:640+10+8+8+4=670inputs. P6/P8:640+10+8+7+4+12=681inputs. Class orders are checkpoint-specific; equal widths do not justify substituting one order for another. The final specialist outputs are sigmoid binary scores; those are distinct from the categorical-softmax backbone features.

## Twelve Signal-Event Features

Source: exact147,362-byte trainer, SHA-256 `8e8d59889a0458c47a90f9735ff6ba017c7e1a79582d11529a608e1816e671fe`. Function `_signal_event_features_from_batch`; input is the prepared10-second125Hz tensor. LeadII is preferred if nonconstant; otherwise the highest-standard-deviation channel is used. Nonfinite samples become zero. Absolute median-centered amplitude supplies local-maxima candidates above the larger of its88th percentile and mean+0.8SD. Peaks are amplitude-ranked, separated by at least0.28seconds, then time-sorted. Epsilon is `1e-8`.

Every value below is clipped to `[0,1]`. RR is measured in seconds; RMSSD is converted to milliseconds. Undefined RR/amplitude statistics take the code's zero fallback. These peak/interval proxies are not expert-adjudicated fiducials.

| Position | Recorded quantity | Normalization |
|---:|---|---|
| 1 | Peak count `n` | `n/30` |
| 2 | Fixed10-second heart-rate proxy | `6*n/220` |
| 3 | RR coefficient of variation | `(SD(RR)/mean(RR))/1.5` |
| 4 | Successive-RR RMSSD, milliseconds | `RMSSD/600` |
| 5 | Minimum positive RR, seconds | `min(RR)/2` |
| 6 | Maximum RR, seconds | `max(RR)/2.5` |
| 7 | Fraction RR shorter than0.8medianRR | No additional scale |
| 8 | Fraction RR longer than1.25medianRR | No additional scale |
| 9 | Peak-amplitude coefficient of variation | `CV/2` |
| 10 | Mean absolute first difference divided by leadSD | Further divide by5 |
| 11 | Fraction absolute first differences exceeding `max(3*median(abs(diff)),epsilon)` | No additional scale |
| 12 | Fraction successive first derivatives with negative product | No additional scale |

Later source supports16features, appending QRS-width median/0.20seconds, QRS-widthCV/1.5, P-to-R proxy median/0.32seconds, and `1-min(PR_CV,1)` consistency. The released P6/P8 checkpoints declare12, not16. The recovered compatibility path uses the declared dimension; it is not valid to append four inputs to the released681-input heads. Flat-signal behavior is preserved as historical code, not silently redesigned or promoted as clinically meaningful.

## Ten Morphology Features: Candidate Identity Boundary

The preserved V4 module is [`morphology_features_v4.py`](../scripts/cedia/recovery_candidates/morphology_features_v4.py),6,611bytes, SHA-256 `2bd1c1822ed72d1531b1f62712d8007c7e2f21009056ad1a3ee905f37051fc3d`. Its definitions can be documented exactly; original V4.5 execution identity must not be inferred merely from the matching ten-input width.

For this candidate, input nonfinite values become zero. LeadII, or the most variable lead, supplies median-centered absolute peak detection with the same88th-percentile/mean+0.8SD and0.28-second exclusion pattern. Positive RR intervals determine the heart-rate and variability proxies. Nonfinite final values map to zero; normalized values are clipped to `[0,1]`, except asymmetry in `[-1,1]`.

| Position | Name | Raw definition / normalization |
|---:|---|---|
| 1 | `hr_median_bpm` | `60/median(RR seconds)`, divide by220 |
| 2 | `rrv_cv` | `SD(RR)/mean(RR)`, divide by1 |
| 3 | `rrv_rmssd_ms` | Successive-RR RMSSD in milliseconds, divide by500 |
| 4 | `qrs_width_proxy_ms` | Median active span in local peak neighborhoods, threshold `max(0.35*amplitude,70th percentile)`, divide by220 |
| 5 | `p_to_r_proxy_ms` | Median peak-to-largest-absolute-deflection lag searched0.28to0.08seconds before peak; retain60to320ms, divide by320 |
| 6 | `qrs_band_ratio` | Mean-channel FFT power5to18Hz divided by total mean-channel power |
| 7 | `lowfreq_ratio` | Mean-channel FFT power0to0.7Hz divided by total power |
| 8 | `hf_ratio` | Mean-channel FFT power35Hz to Nyquist divided by total power |
| 9 | `lead_corr_abs_mean` | Mean finite absolute off-diagonal correlation among nonconstant leads |
| 10 | `limb_qrs_asymmetry` | `(I_power-aVF_power)/(I_power+aVF_power)` in5to18Hz, clipped to `[-1,1]` |

These definitions explain the candidate implementation. They do not certify clinical PR/QRS measurement, explain any replay mismatch by themselves, or substitute for the missing exact V4.5 loader and its historical execution provenance.
