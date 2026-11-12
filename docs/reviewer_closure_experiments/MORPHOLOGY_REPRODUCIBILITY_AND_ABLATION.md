# R2-3f: Morphology, implementation and reproducibility

The literal request concerns how the ten features are calculated and
what the arrows between model components mean. It does not require
positive ablation results or perfect recovery of the historical loader.
No article figures have been modified.

## Calculations and input contract

The [source-backed ten-feature contract](../reviewer_experiments/MORPHOLOGY_INPUT_CONTRACT.md)
gives the ordered formulas, units, scaling, clipping, nonfinite handling
and extractor SHA-256. The normalized features describe timing, power
and cross-lead relationships; QRS width and P-to-R are heuristic proxies,
not adjudicated intervals. Peak count is not an eleventh feature.

The [new executable audit](../../outputs/results/reviewer_closure_experiments/ludb_scoring_receipt.json)
used the pinned Stage A source at `f4d6be30b0befea739cf2e35df1033230a1f5d10`
with the same checksum-verified released packages. It first checked
native LUDB physical values in mV, 12 named leads and 5,000 samples at
500 Hz. The reconstructed preprocessing supplies 1,250 samples per lead
at 125 Hz, with padded context, causal third-order bandpass (0.5-45 Hz)
and per-lead centering/scaling. Rhythm uses the documented sliding
window contract; P4 uses the prepared first window. Lead mask and
morphology are separate tensors. Exact historical preprocessing bytes
are not inferred from this reconstructed path.

## Observed wiring, not only static diagrams

Native job 33697 checked every batch before the forward calls. Each
observed component below saw **200 windows in 13 batches**, with strict
state-dict load and no recorded technical failure:

| Component | Actual input | Evidence of morphology |
|---|---|---|
| V3F and V3AG backbone calls | 12 x 1,250 waveform, 12-element lead mask, ten-feature vector | Hooks checked exact equality with prepared mask and vector |
| Global rhythm head within either backbone | 650 columns | Ten morphology columns directly after 640 embedding columns |
| Global pathology head within either backbone | 640 columns | Embedding only; no direct ten-feature slice |
| P6 and P8 specialists | 681 columns each | Morphology at zero-based columns 640-649, with separate score and rhythm-event features |
| P4 specialist | 670 columns | Same direct morphology slice; distinct from the global pathology head |

The actual P6/P8 specialist tensors each have hidden width **512** despite
the redundant metadata declaring **192**; the loader builds from the
tensor shape and loads strictly. The P4 specialist's loaded hidden width
is also 512. This proves the topology of the audited release assets, not
which exact runtime parameters or intermediate checkpoints were used by
an unrecovered June job. Arrows in an architecture schematic should
represent the tensor flows above; class grouping does not establish
clinical dispatch or sequential inference.

## Replay and known residuals

The [November native contrast](../../outputs/results/reviewer_experiments/replay-contrast_33472_aggregate.json)
proved repeatability of the reconstruction and preserved the historical
differences: 836/962 P4 probabilities outside the frozen `1e-5`
tolerance with no matched binary call change; one P6 top-1 swap between
the same two leading candidates and no threshold-set changes. P8 had no
top-1 or threshold-set changes in 2,193 matched records, which is not
equivalence of scores. The [fixed-input batch probe](../replay-residual-diagnostics.md)
demonstrated that batch size alone can change scores and a call outside the
matched P4 panels. No choice of batch reproduced the historical scores
under the frozen tolerance. The surviving evidence does not identify
historical floating-point kernels, exact signal preparation and masks, or
the original import graph. Do not choose a variant by closeness to the
historical answers or relax the tolerance after inspecting the residuals.

## Paired predictive effect

[Matched job 33596](../../outputs/results/reviewer_experiments/retrained-eval_33596_aggregate.json)
held back the same groups for both arms and calibrated each on separate
groups. It compared newly fitted heads on frozen backbone representations,
not end-to-end retraining of the historical backbone. The paired changes
in macro-F1 (with minus without) were P6 +0.0072 (95% CI -0.0040 to
+0.0206), P8 +0.0146 (+0.0016 to +0.0276), and P4 +0.0006 (-0.0163 to
+0.0157). The original intervals were profile-specific, not adjusted
across profiles. P6 and P4 remain inconclusive, not equivalent.

[Job 33704](../../outputs/results/reviewer_closure_experiments/morphology_robustness_aggregate.json)
independently rederived the original paired point estimates and all 1,000
valid bootstrap replicates per profile from the sealed fitted arms, without
waveform inference or refitting. A separately identified post hoc robustness
test used 10,000 within-group swaps (1,251 P6/P8 and 254 P4 units).

| Profile | Observed delta macro-F1 | Paired 95% interval | Arm-swap p | Holm p, three profiles |
|---|---:|---:|---:|---:|
| P6 | +0.00722 | [-0.00405, +0.02059] | 0.2841 | 0.5681 |
| P8 | +0.01457 | [+0.00155, +0.02762] | 0.0452 | 0.1356 |
| P4 | +0.00061 | [-0.01628, +0.01575] | 0.9626 | 0.9626 |

P8's original unadjusted interval excludes zero, but this post hoc test
does not show a robust family-wise result at 0.05. Preserve both findings.
The two procedures answer different uncertainty questions; neither
identifies a causal effect in the published backbone or clinical setting.
P6 and P4 are inconclusive, not demonstrated equivalent.
