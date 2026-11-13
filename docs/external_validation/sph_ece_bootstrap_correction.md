# SPH ECE bootstrap bin-edge correction

Identified with synthetic data before inspecting SPH performance: the frozen
point estimator assigns equal-width ECE bins using `searchsorted` on
`numpy.linspace` edges, whereas the frozen bootstrap uses integer conversion
of `score * bins`. At floating-point bin boundaries these can disagree, so an
ECE interval may not correspond to the reported point estimator. The other
metrics are unchanged by this correction.

The separate `evaluate_sph_ece_corrected.py` wrapper preserves the frozen
evaluator and its input checks while replacing only the bootstrap ECE bin
assignment with the point estimator's rule. It writes an additional receipt
with its own hash and the hashes of the frozen evaluator, aggregate, and
evaluator receipt. The original frozen implementation and scoring ledger are
not modified. Synthetic tests compare weighted results with explicit record
replication and preserve a regression demonstrating the original discrepancy.
This correction does not use performance to select models, thresholds, labels,
or records.
