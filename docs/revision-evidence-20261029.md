# Source Identity and Saved Decision Reconstruction, 29 October 2026

This follow-up narrows two previously open evidence gaps. It does not replace the archived scientific predictions, overwrite the 28 October audit, or certify the still-failed Primary4 waveform-equivalence check. Aggregate findings and portable fingerprints are in [`outputs/results/revision_20261029`](../outputs/results/revision_20261029).

## Resolved Selected-Record Source Identity

All **84 selected `data_test` signal files** match SHA-256 entries in the official [PhysioNet Challenge 2020 version 1.0.2](https://physionet.org/content/challenge-2020/1.0.2/) index: **3 CPSC 2018, 5 Georgia, 76 PTB-XL**. The complete official index hash is recorded in the export receipt. This establishes byte identity with an upstream release, not which download route originally supplied the files or isolation from development.

All 84 local headers differ in raw bytes from the upstream headers. They are not claimed to be byte-identical. WFDB 4.3.0 parsed comparisons agree on signal dimensions, sampling rate, lead names/order, gains, baselines, units (only `mv`/`mV` spelling canonicalized), encoding, samples per frame, skew, byte offset, resolution, zero, initial values, checksums, block sizes and diagnosis codes. All 84 saved prediction diagnosis-code sets agree with those upstream headers. Demographic fields were not exported or used to certify patient identity.

All 168 corresponding signal/header fingerprints agree with the recovered release-package inventory and a fresh physical-cache read. The CEDIA rhythm archive also retains its original release hash. No waveform or full header is newly redistributed here.

The upstream release states CC BY 4.0. Attribution, notices, modified-header descriptions and the remainder of the mixed archive still need a documented distribution review. The historical HOLD is **not automatically lifted**. The old report's unresolved-source finding is preserved as a dated snapshot and superseded only for these 84 selected records. A local folder named `data_test` does not represent an independent source institution.

Reproduce the exact-byte part offline:

```bash
python scripts/evaluation/verify_source_checksums.py \
  --inventory outputs/results/revision_20261029/data_test_file_fingerprints.json \
  --checksums outputs/results/revision_20261029/official_checksums_selected.txt \
  --output /path/to/source-check.json
```

The portable checker deliberately reports `signal_only` for these normalized headers. Semantic WFDB agreement is a separate audit, not an override making unequal bytes pass. `--details /path/to/details.json` explicitly opts into record-level identifiers; aggregate output omits them. The selected checksum file is a 168-entry excerpt, not the complete official index. Obtain the full index at the URL and verify its hash in `integrity.json` to reproduce against the original upstream list.

## Broader Package Findings

Matching the packaged waveform fingerprints to the official [Challenge 2021 version 1.0.3](https://physionet.org/content/challenge-2021/1.0.3/) index links **2,026/2,193** signals. The remaining 167 are CODE-test derivatives and are not expected to be identified by that index. Ten matched signals occur identically in the official Chapman-Shaoxing and Ningbo folders; a checksum cannot select a unique institution for them. No claim of eight independent centers is justified by eight literal source strings.

The 167 CODE-test `record_base` prefixes also differ from the packaged directory prefix (`codetest_zenodo_3765780` versus `codetest`). A unique record-identifier lookup locates them in the package inventory, but that lookup is not upstream content verification. This discrepancy remains explicit for future waveform loaders; archived CSV paths have not been rewritten.

## P8 Saved Decision Rule Reconstructed

The following fixed rule exactly reproduces **2,193/2,193 saved top-1 labels and binary label sets**:

1. Top-1 is the argmax of `membership_prob_<class>` in the declared class order.
2. Select every class whose membership score meets its already-published class threshold.
3. When that set is empty, insert the membership-score argmax. This occurs on **58 records**.

The separate `prob_<class>` stream has 580 argmax differences from the saved top-1. Membership thresholding **without** the empty-set fallback has 58 class-record differences. These are explained saved-field diagnostics, no longer unexplained decision mismatches. No thresholds, labels or archived outcomes were changed, and reference labels were not used to choose the rule. This is reconstruction from retained fields, not recovered original source code or waveform-to-output equivalence.

```bash
python scripts/evaluation/verify_membership_policy.py
```

The command fails if a saved decision differs from this rule. Tests cover ties, equality at threshold, all-negative membership sets, invalid scores and every archived P8 record. P6 uses a different saved binary contract and is not silently assigned the P8 fallback.

## P6 Calibration Lineage Clarified

The recovered original job `17315` log explicitly names `internal_zero_bias_f1_tuning`, 192 internal ECGs / 276 windows, mean-logit aggregation and six zero biases. Its internal and external reports use the same six-class threshold vector and reproduce the archived external aggregate result. Separately, the specialist's native eight-class threshold vector belongs to a different policy contract. These findings explain the distinction; the complete calibration source code, historical manifests and patient-disjointness are still not certified.

Compute-node job `31566` completed with exit `0:0` and recovered full non-weight checkpoint metadata without inference. Dimensions, report entries and stored settings are evidence; they do not recover absent operations such as the original twelve-event extractor or Transformer semantics not stored in a state dictionary.

## What Remains Open

The P4 candidate forward pass still differs on 166/962 panel decisions. Historical preprocessing/feature code, full training/calibration provenance, all-input routing and genuinely independent validation remain necessary. A fresh implementation or new locked validation study can be useful, but must be reported as new work, not retroactive restoration of the original experiment. No clinical-reader or HITL safety evidence is created by this audit.
