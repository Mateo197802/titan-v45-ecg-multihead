# Reproducibility and provenance

- Selected candidate, job 33696; validation selection seal published before
  inference at [5060edb](https://github.com/Mateo197802/titan-v45-ecg-multihead/commit/5060edbf0bc86d4f1596a6596da05bd2fce144b1).
- Job 33768 scored the three systems once; 33769 reduced the sealed
  predictions and bootstrapped paired patients; 33772 independently
  recomputed points and macro-F1 bounds from those same private predictions.
- The [readback receipt](../technical_package/source_snapshot/evidence/WITHIN_CODE_INDEPENDENT_READBACK.json)
  reports 546 point comparisons (maximum error 2.22e-16) and 30 CI-bound
  comparisons (zero error). Independence refers to the implementation,
  not the clinical source or cohort.
- This package independently recomputes only quantities derivable from
  public aggregates and verifies receipt hash links. It does not recompute
  AUROC, AUPRC or bootstrap intervals from individual scores, nor certify
  the undocumented history of any published weight.
- [Traceability](../technical_package/SOURCE_TRACEABILITY.csv) links public
  original sources, including the exact job ledger and preprocessing receipt.
  Whole-artifact hashes are not patient identifiers. Individual material
  remains excluded from this delivery.
