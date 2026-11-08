# SPH aggregate metric-name clarification

Published before inspecting SPH performance. The frozen endpoint aggregator
uses `binary_metrics`, which reports sensitivity as `recall` and does not
include a point estimate named `npv`. Its patient-component bootstrap already
uses the names `sensitivity` and `npv`. The fixed aggregate plotter expects
the `sensitivity` point-estimate key, so the raw aggregate alone would omit
those points from that figure.

After the sealed raw aggregate and its receipt have been verified, run
`scripts/external_validation/normalize_sph_aggregate.py` on the aggregate
only. It retains the original report, aliases sensitivity to recall after
checking the confusion counts, calculates NPV as TN/(TN+FN), explicitly marks
a zero denominator, and leaves all bootstrap intervals unchanged. It embeds
the input aggregate SHA-256 in the new file. Preserve both files and hash the
normalizer and both outputs in the publication receipt. No predictions,
references, thresholds, weights, or inclusion criteria are modified.

The separately versioned `plot_sph_aggregate_corrected.py` is the designated
renderer for this normalized aggregate. It preserves the frozen figure layout
and draws absolute percentile interval endpoints, including intervals that do
not contain the point estimate. This avoids negative `xerr` rejection without
clipping or changing the interval. Preserve the original renderer and include
the corrected renderer's commit and SHA-256 in the figure receipt. This renderer
correction was prepared using synthetic tests before SPH metrics were inspected.
It also preserves endpoint labels on shared y-axes; the original renderer's
empty labels on the later axes otherwise erase the shared tick formatter.
