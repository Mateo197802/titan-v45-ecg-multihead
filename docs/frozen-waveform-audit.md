# Frozen Waveform Audit: Selected Development Cohorts

This audit starts with ECGs, not the published prediction table. It is a new execution of a source-backed reconstruction against preserved checkpoints on the selected development cohorts. It is not the June study, a recovery of the population before selection, a new holdout, or a new canonical release. The architecture, specialist weights, thresholds and archived predictions are unchanged. The absent original loader prevents certifying historical preprocessing identity.

## Measured Results

| Profile | Input coverage | Compared archived decisions | Maximum score difference |
| --- | --- | --- | --- |
| P4 | 733/733 ECG keys; all four scores for each | 962/962 binary panel decisions agree | 0.0006194115; exceeds the unchanged 0.00001 tolerance |
| P6 | 1,643/1,643 ECG keys, 1,679 windows | 1,642/1,643 top-1 and 1,643/1,643 binary sets agree | 0.0019060100 |
| P8 | 2,193/2,193 ECG keys, 2,404 windows | 2,193/2,193 top-1 and binary sets agree | 0.0017378628 |

- P8 had 476 NSR top-1 outputs and 58 empty-set fallbacks. These are model outputs, not normal-record prevalence or a population screen. P6 has no P8-style forced binary fallback.
- P4 emitted 2,932 primary scores. Only the 962 available panel–ECG references enter its performance comparison; the other scores are not assumed negative. ALMI, ILMI and LAE have 733 auxiliary scores each from the backbone. Six auxiliary rhythm channels have 2,193 scores each. An emitted score does not establish supervision, calibrated accuracy or an auxiliary routing rule.
- The exact-key union is 2,926 keys: 733 pathology-only and 2,193 rhythm-only, with no exact cross-branch key overlap and P6 already included in P8. This is not a count of verified unique patients or a stream on which both specialists were tested for every input. Eligibility comes from already selected manifests, which can encode selection bias; no reference labels determine a branch transition during the new execution. Because no linked frozen uncertainty policy was recovered, every scored key is `quarantine_not_assessed`; the rate is **undefined**, not 0%.
- The reference comparison uses the same matched keys for the archived and new outputs. P6 has 1,563/1,643 newly correct accepted top-1 outcomes versus 1,564/1,643 archived; P8 has 1,987/2,193 in both. Neither replaces the reported metrics. P4 mean binary accuracy is unchanged (80.23%); its 95% ECG-cluster percentile interval is 77.65% to 82.66% (2,000 draws, seed 2026). No patient-level or clinical confidence is inferred.

## Inputs And Computation

1. **Identity.** The [release manifest](../release-manifest.json) provides names, sizes and SHA-256 for five model files and the two waveform bundles. Each inference job checks the files needed by its branch before opening weights or signals. The source, cohort and reference hashes are embedded in the exported JSONs.
2. **Preprocessing.** [`reconstructed.py`](../src/titan_v45/data/reconstructed.py) uses WFDB physical values, a fixed lead map and the candidate morphology. P4 uses the retained forensic replay's filter, resample, padding and centering operations. Rhythm uses the recovered source-backed sliding-window contract, including the terminal-window rule. Neither is certified byte-for-byte against the original missing loader. One documented CODE-test archive prefix is mapped explicitly; no manifest label or identifier is rewritten and no fuzzy fallback is used.
3. **Model.** [Frozen pathology](../src/titan_v45/models/frozen_pathology.py) uses V3AG and the 670-feature P4 head; [frozen rhythm](../src/titan_v45/models/frozen_rhythm.py) uses V3F and two 681-feature heads with the recorded 12-event functions. Both rhythm heads load strictly at the saved tensor width of 512; redundant metadata says 192. The failed first load is retained in the receipt. Classwise sigmoid specialist scores differ from the categorical-softmax backbone rhythm features. See the [feature order and definitions](recovered-feature-contract.md).
4. **Decisions.** P4 compares each sigmoid score with its own saved threshold. P6 uses mean logits and the recorded zero-bias six-class thresholds. P8 averages sigmoid membership scores and uses its saved threshold and fallback contract. Auxiliary outputs remain scores with no certified decision rule. Read failures, missing scores and missing policy are not negatives or retained-by-quarantine outcomes.
5. **References.** Inference can be run without exporting per-record results. The optional private ledger is written outside Git; the separate reference job verifies its inventory, joins archived references and computes per-class confusion counts, AUROC, average precision, Brier, ECE and ECG-cluster intervals where defined. P8 uses the membership-score stream and the accepted-label reference. The report does not substitute that stream for the distinct historical single-target analysis.

## Reproduce In An Authorized CEDIA Allocation

The dataset and private ledger roots must be approved and outside the checkout. Use absolute paths; run from a clean checkout. Compute must run under SLURM, not on the login node. Never push private outputs or raw ECGs.

```bash
sbatch scripts/cedia/run_frozen_p4_cascade.sbatch \
  "$REPO" "$RELEASE_ROOT" "$PYTHON_DEPS_TAR" "$PRIVATE_OUTPUT" pathology_primary4
sbatch --time=00:10:00 scripts/cedia/run_frozen_p4_cascade.sbatch \
  "$REPO" "$RELEASE_ROOT" "$PYTHON_DEPS_TAR" "$PRIVATE_OUTPUT" rhythm
# After both inference jobs complete successfully:
sbatch scripts/cedia/run_waveform_reference.sbatch \
  "$REPO" "$P4_PRIVATE_LEDGER" "$RHYTHM_PRIVATE_LEDGER" "$PRIVATE_OUTPUT"
```

The [execution receipt](../outputs/results/revision_20261107/execution.json) pins the exact commits, native job statuses, dependency bundle and aggregate byte hashes. The aggregate hashes verify those outputs, not that every hardware or library version must produce identical floating-point results. Compare score residuals and decisions separately. An older candidate yielded 166 P4 decision differences; subsequent recovery eliminated those decision differences without establishing probability equivalence. The earlier evidence remains available.

```bash
python scripts/evaluation/verify_release_evidence.py
python scripts/evaluation/verify_release_hashes.py --root "$RELEASE_ROOT" --require-models
python scripts/evaluation/verify_waveform_delivery.py
python -m pytest -q tests/evaluation/test_waveform_evidence_snapshot.py
```

## Publication And Remaining Limits

Only aggregate JSON, runnable code, tests and documentation are added. No new waveforms, weights, private scores or patient identifiers are redistributed. Existing code and model licenses are in [LICENSE](../LICENSE) and [MODEL_LICENSE.md](../MODEL_LICENSE.md); dataset-specific notices and citations are in the [source inventory](../data/licenses/README.md). Those citations do not prove which inputs were used by any particular training job. The CODE-test archive alias is not independent upstream checksum confirmation. The mixed rhythm archive's existing distribution hold is unchanged.

Training, calibration and study-population manifests, complete Optuna linkage, historical routing and independent evaluation are not supplied by this audit. The [data disposition index](revision-data-dispositions.md) records which claims have bounded evidence, which need restriction, and which work remains intentionally deferred.
