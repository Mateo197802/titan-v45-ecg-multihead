# Historical Recovery and Remaining Technical Gaps

This is a technical recovery update, not a revised manuscript, reviewer response, journal acceptance or new validation experiment. Frozen scientific predictions and previous receipts are preserved. Sanitized machine-readable results are in `outputs/results/revision_20261029/`.

## Exact Historical Backbone Source Recovered

The CEDIA snapshot `titan_repo_stage_20260629.tar` contains `./src/titan_v45/models/backbone.py`: **9,189 bytes**, SHA-256 **46bb36737a93a4cfe4be4417f6c62bcbfd0e8e7e8356f31f532ad21662075c80**. These bytes exactly match the historical inventory entry `MODEL_CORE/titan_v4_hybrid.py`. The same content is retained in Git commit `b704df016bf9763146cf2a66ad75abfec32c452c` and is now preserved byte-for-byte in [`backbone_20260629.py`](../scripts/cedia/recovery_candidates/backbone_20260629.py).

All five forward/forward-features method bodies have identical Python ASTs in the recovered and current backbones. All shared methods, including the constructor, agree after the documented `clinical_axis` to `ecg_axis` identifier renaming. The current version adds `_load_from_state_dict` for axis-key migration. The snapshot factory explicitly specifies `nhead=10`; no head-count search against evaluation outcomes was performed.

The backbone was the first recovered source. Subsequent archived-event reconstruction now recovers **ten of the eleven inventoried source files**, as described below. Source identity does not prove which source/configuration was executed for each checkpoint, runtime numerical equivalence, or waveform preprocessing correctness. The initial backbone-specific analysis remains in [`backbone_static_recovery.json`](../outputs/results/revision_20261029/backbone_static_recovery.json).

## Ten Inventoried Sources Restored

Confirmed historical file-addition records and unified diffs were replayed with Git's patch parser, not by executing archived shell commands. Duplicate fork records were reconciled by call identity. After LF normalization, the restored trainer, runtime, contract, Optuna source, external evaluator, gate helper, source-CV helper, replacement-manifest builder, P6 calibration and backbone match their independent29June inventory hashes and byte counts. The trainer restoration includes99confirmed source-change records and yields147,362exact inventoried bytes.

The [source recovery manifest](../outputs/results/revision_20261029/inventory_matched_source_recovery.json) lists all eleven targets, ten matches and the missing loader. Exact matched bytes are preserved in [`recovered-original-sources-20261029.zip`](provenance/recovered-original-sources-20261029.zip), rather than reformatted as new implementation code. The old inventory labels one9062-byte helper `v3d_validation_tools.py`; the historical events identify the same bytes as `v3d_gate_tools.py`. The archive and new manifest explicitly retain that original filename mapping.

The twelve-event extractor is now present in the recovered trainer, including later16-feature compatibility handling. That code must be bound to each checkpoint's stored feature dimensions; a dimension match alone remains insufficient.

### Source-Backed P4 Diagnostic

The recovered `specialist_input_from_base` applies **categorical softmax** to backbone rhythm logits before specialist feature composition. The old diagnostic replay used independent sigmoid. These are distinct operations. The script now accepts `--recovered-trainer`, verifies its exact inventoried SHA-256, and then uses the documented softmax; omitting the flag retains the previous diagnostic behavior.

Before executing this new comparison, the criterion is fixed:733ECGs,962panel rows, zero decision disagreements and maximum absolute probability error at most `1e-5`, relative tolerance zero. The previous166-disagreement outputs are preserved. No threshold, class order, filter or hyperparameter is selected by evaluation accuracy. A source-backed replay is an existing-cohort equivalence test, not new independent validation. Its result must be reported even if it fails.

**Measured outcome:** job31577 completed `0:0` in46seconds; softmax alone still fails, with168decision disagreements, maximum absolute error0.6975915134and mean error0.1197770961. This is worse in decision agreement than the original166and is preserved in [the31577report](../outputs/results/revision_20261029/p4_recovered_softmax_31577.json); it was not discarded in favor of a better-looking score.

### Recorded Named-Lead Mapping

A packaged header uses uppercase `AVR/AVL/AVF`, while the old diagnostic searched the literal mixed-case names `aVR/aVL/aVF`. It consequently replaced those channels with zeros and marked them absent. The recorded loader helper normalizes alphanumeric lead tokens to uppercase and uses canonical names and explicit aliases. Its source-diff fingerprint and the observed header contract are in [the lead-mapping receipt](../outputs/results/revision_20261029/lead_mapping_recovery_contract.json).

The recovered-trainer path now enables both the documented softmax and that recorded named-lead mapping. Tests enforce equivalent uppercase/mixed-case inputs, no fabricated missing channels, rejection of non-ECG channels and canonical-before-alias precedence. A further complete comparison uses the same predeclared tolerance and unchanged thresholds. Its result is pending until measured; the full inventoried loader remains unrecovered and neither earlier failure is overwritten.

## Header Modification Identified

All84selected `data_test` headers are **identical to upstream after newline normalization alone**: local CRLF, official LF. They remain unequal as raw byte strings. Record-line tokens, signal-line tokens and normalized comment fields also agree. The script validates local header fingerprints and indexed upstream header digests before comparing; it exports no record identifiers or comment values.

The [selected-file attribution and modification notice](../data/licenses/PhysioNet-Challenge-2020-selected-data-test.md) is now documented, using the official [PhysioNet release](https://physionet.org/content/challenge-2020/1.0.2/) and its [license](https://physionet.org/content/challenge-2020/view-license/1.0.2/). **The mixed archive remains HOLD.** This selected-file notice is not package-wide distribution clearance or proof of training isolation.

To reproduce, supply the private fingerprint inventory with exact header text and the previously checksum-verified upstream headers:

```bash
python scripts/evaluation/audit_header_modifications.py \
  --inventory /private/data_test_fingerprints_20261029.json \
  --checksums outputs/results/revision_20261029/official_checksums_selected.txt \
  --upstream-headers /private/upstream_headers \
  --output /tmp/header-modifications.json
python -m pytest tests/evaluation/test_header_modifications.py tests/evaluation/test_historical_source_contract.py -q
```

The private header inputs are not newly redistributed. Exact-body source comparisons can be repeated with the included historical source; tests enforce its inventory hash and forward AST identity.

## Search Coverage and Limits

- Local directed pass: six roots, 327,738 file entries, 88 archives, of which75inspected and13retained as data/size exclusions;87candidate entries represent12unique content hashes. Three access-denied Windows media junctions are recorded.
- CEDIA project pass: 6,567 files, ten archives, eight inspected and two data archives excluded; no time-bound termination. Six plan archives and the pre-cleanup stage snapshot were inspected.
- CEDIA home top level: 1,202 files. Legacy-docs, backup and transfer-root pass:46files. The configured `cedia-kevin` V4.5 project pass also completed:173files, two candidates, neither matching an original inventory hash. The broad first-account home traversal reached its240-second limit; that partial traversal is not described as complete.
- Local Git object audit: six unreachable blobs, none matching the eleven original source hashes. The corresponding historical backbone was found in reachable Git history, not an unreachable blob. The original CEDIA repository reported no unreachable objects in its separate audit.

Passes overlap: **do not sum their counts as unique files**. Only the two configured CEDIA access accounts were examined; no other account, privileged filesystem snapshot or undisclosed collaborator backup was accessed. The local worktree/backup/plan pass also completed658files. The session-metadata pass examined416files, identified111related contexts and139definition-pointer events; three large selected contexts hit a100MiB content bound. Subsequent source reconstruction fully read the relevant June archives separately. A negative result is not proof of absence in every backup. See [`recovery_search_summary.json`](../outputs/results/revision_20261029/recovery_search_summary.json); full paths and session contents remain private.

## Still Open

The original morphology extractor's V4.5 identity, exact inventoried loader, full historical training/calibration manifests, Optuna trial database and all-input routing ledger remain open. Runtime/trainer source and the twelve-event code are no longer wholly missing. The nearest loader reconstruction is36,465bytes and does not match the36,271-byte original target; it is not published as certified. The old P4 replay differs on **166/962** panel decisions. The newly evidenced softmax/sigmoid discrepancy requires a new measured comparison before assigning all mismatches to it.

Next technical work must recover an independently evidenced source/configuration before a new replay. Do not search filters, class permutations, Transformer heads or thresholds by evaluation accuracy. The selected external cohort and any new locked study are deferred until historical recovery is addressed; no costly retraining starts through this update. Manuscript and editorial responses remain frozen during evidence recovery and synchronization.
