# TITAN post-merge forensic audit

**Pinned scientific tree:** `6f50a6337fc3e8b518655b05916ced7447598b47`.
This audit independently checks bytes and selected calculations, distinguishes
receipt readback from experiment execution, and leaves the source repository
and all scientific outputs unchanged. It is not a complete authentication of
every checkpoint/claim or a clinical validation report.

## Where to start

1. [GitHub and PR #15](PR15_MAIN_INCLUSION_AUDIT.md)
2. [Artifact ledger](MASTER_ARTIFACT_SHA256_LEDGER.csv) and
   [experiment inventory](MASTER_EXPERIMENT_INVENTORY.csv)
3. [Weights and lineage](CHECKPOINT_IDENTITY_AND_LINEAGE.csv),
   [training jobs](TRAINING_JOB_PROVENANCE_MATRIX.csv), and
   [dataset and leakage audit](DATASET_SPLIT_AND_LEAKAGE_AUDIT.md)
4. [Recalculation](METRICS_INDEPENDENT_RECALCULATION.csv),
   [claim routes](EXPERIMENT_TO_CLAIM_TRACEABILITY.csv), and
   [scientific verification](SCIENTIFIC_CLAIM_VERIFICATION_MATRIX.csv)
5. [Native receipts](NATIVE_AUDIT_RECEIPTS.json) and
   [verification results](POSTMERGE_VERIFICATION_RESULTS.json)
6. [Contradictions](SCIENTIFIC_CONTRADICTIONS_AND_RESOLUTION.md),
   [missing evidence](MISSING_OR_RESTRICTED_ARTIFACTS.md) and
   [verdict](FINAL_SCIENTIFIC_INTEGRITY_VERDICT.md)

## Method and trust boundaries

* Content identity is SHA-256 of the bytes. The same ID can have multiple
  provenance rows, which must not be counted as separate evidence. Git OIDs
  are independent object identifiers, not SHA-256 of file contents. The
  ledger includes current tree paths, newly introduced PR #15 paths, other
  reachable historical blobs, ZIP members and native checkpoint evidence.
* CEDIA path locators for restricted inputs are hashed. The file is read on
  the compute node; its content, record identifiers, and absolute path are
  not included. Accounting success does not bind a specific input file
  unless the job receipt does. A pathname-derived job hint is not a producer.
* Historical archived tool outputs are distinguished from native logs.
  Independently recomputed point estimates are not new predictions, and
  reading private weights is not inference or clinical validation.
* The experiment inventory contains family/run entries plus catalog-only
  rows for otherwise unmapped result files. Do not equate the total number
  of rows with the number of independent experiments. The full repository
  tree is indexed, but candidate-by-candidate tensor verification and
  line-by-line scientific documentation review remain incomplete.

## Substantive findings

- Canonical P6/P8/P4 accuracy and macro-F1 reproduce from their actual
  selected predictions. Under identical profile contracts, no recomputed
  matched metric contradicts its canonical reference. Derived AUC, AP,
  Brier and ECE are not claimed as historical published endpoints.
- The restored historical V3C summary matches its 29 June digest; all nine
  tail scores reproduce. No full study DB or exact parent checkpoint was
  established. The 2,705-byte 16768 completion excerpt
  (`sha256:0ac230ddea139b22decd6d6a950fe75aebafe774fd67e9b51eb9350dafa50738`)
  directly corroborates 9,021/924 windows. The 7,485-file count is from
  the archived reconciliation rather than that excerpt. The full
  50-epoch trace was not authenticated in this audit.
- CEDIA job 33831 re-read the CODE-15% native evidence and re-sealed the
  original delivery byte-for-byte. It is a repeat of point/reference
  checks, not new training or fresh independent bootstrap. All 18
  source archives and separate historical evaluation receipt remain bound.
- PR #15's negative development result is native-backed and not on main.
  Its published point readback of 26 rows is verified by its native
  receipt and does not establish a model promotion.
- Later selective utility and cascade arithmetic are reproduced from
  sealed aggregates, not claimed as a new per-record bootstrap. The
  morphology mean effects are recomputed from seed/class confusion
  counts, not an end-to-end backbone ablation.

## Verification coverage

The clean pinned checkout passed **777 tests**, Ruff, release and
evidence checks, and the public adaptation and recovery readbacks.
The SHA ledger indexes 4,972 occurrences of 2,967 distinct contents.
It includes 98 observed checkpoint locations, representing 69 unique
checkpoint hashes, including the 11 verified adaptation finalists.
The master inventory separates 70 scoped study/run entries from 143
artifact catalog entries. Of the 70, 1 is verified with primary evidence
for its stated claim, 4 are independently recalculated within scope,
44 are scope-limited, 6 partial, 14 receipt-only, and 1 unsupported.
These are claim-specific verification levels, not a count of
end-to-end reproduced training experiments. No complete historical
training was reproduced.

The metric register contains 145 independently matched calculations
and 170 additional derivations, with no mismatches in the matched
comparisons. The latter include descriptive score metrics, not
retroactive scientific claims. For the two-comment studies, the present
pass recomputes point estimates from counts and preserves the original
native CI/paired bootstrap receipts rather than claiming new intervals.

## Reproduce

Use the exact audited Git refs and trusted CEDIA access. Run native
inventory on SLURM with `forensic_native_readback.py`, not on the login
node. The native checkpoints and archive arguments are optional for a
public-only check; omitting them explicitly reduces coverage.

```text
python scripts/evaluation/verify_postmerge_forensic_audit.py --out NEW_DIRECTORY
python scripts/evaluation/verify_integrated_public_evidence.py
python scripts/evaluation/verify_postmerge_forensic_bundle.py PATH_TO_ZIP
```

To reproduce the full ledger snapshot, provide the original sanitized
native JSON with `--native`, the GitHub snapshot with `--github`, the
historical JSON with `--archived-v3c`, and the inspected archives with
repeatable `--local-zip`. No restricted archive is included in the
documentary packet.
