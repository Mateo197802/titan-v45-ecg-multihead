# R1-2: historical population and evidence ceiling

**Recovery status: `EVIDENCE_CEILING_REACHED` for the sources inspected.**
The preselection population and its exclusion ledger have not been recovered.
This is a bounded recovery disposition, not evidence of editorial acceptance,
not a declaration that no other backup exists, and not completion of the
original historical flow experiment. A new authenticated, relevant source can
reopen the investigation. The manuscript has not been changed.

## Directly supported denominators

| Source and unit | Verified amount | Boundary |
| --- | ---: | --- |
| P6 selected rhythm manifest | 1,643 distinct ECG keys | P6 is a subset of the selected P8 keys, not an additional population. |
| P8 selected rhythm manifest | 2,193 distinct ECG keys | This selected development cohort is not the upstream eligibility universe. |
| P4 selected pathology panels | 962 binary panel observations; 733 unique ECG keys | Panel rows are not 962 unique ECGs; the same ECG may appear in multiple panels. |
| P4 selected patients linked to official metadata | 676 patients | Patient count derives from the official metadata linkage recorded in the fold-coverage audit, not from panel rows alone. |
| Official PTB-XL fold 10 | 2,198 ECG and 1,904 patients; 1,465 ECG are not in the selected P4 keys | Official fold membership does not prove this was the historical candidate universe or explain an individual exclusion. |
| Later SPH transfer source | 25,770 ECG scored from 24,666 source patients | A separate, later source; it cannot replace the missing historical preselection denominator. |

The selected rhythm keys and panel counts are reproducible from the
[manifests](../../data/manifests/external_dev/) and
`python scripts/evaluation/verify_release_evidence.py` (recomputed locally in
this audit; verification passed). The
[official-fold receipt](../../outputs/results/revision_replay_diagnostics_20261107/p4_official_fold_coverage.json)
records the 676 patients and its input fingerprint. These checks do not
recover the construction of any historical parent cohort. The separate
[waveform replay](../frozen-waveform-audit.md) starts after selection.

## What is unknown

The initial V3H/V3S candidate populations, selection and rejection records,
their reasons, and the authentic per-record quarantine transitions are not
available in the inspected sources. Historical V3F/V3AG training and tuning
inputs and V3M/V3P train, internal-validation and calibration splits are
incomplete. No count of patients considered, exclusions, original quarantine
rate, or split isolation can be inferred from the surviving selected rows or
from official dataset sizes. Absence from a panel does not prove exclusion
for a particular reason. P6 and P8 counts must not be summed as independent
records; cross-branch exact-key union is not a unique-patient count.

## Sources checked and scope

- The retained release and its selected cohort manifests, six prediction CSVs,
  and [recomputed evidence](../../outputs/results/release_evidence_verification.json)
  establish selected results, not unselected parents. The June stage archive
  inventory identified six selected prediction CSVs but not the requested
  historical parent manifests; a stage archive is not a preselection snapshot.
- Previously recorded recovery inspected 21 unique Git bundle contents and
  the received inventories, without finding the requested historical manifests
  or original Optuna database. No claim is made about inaccessible collaborator
  backups or unindexed archives. See [recovery status](../recovery-status-20261029.md).
- On this audit the original V3M, V3H, V3S, V3P and V3C hypothesis directories
  were checked at their documented CEDIA location and were not visible. Scheduler
  accounting identifies job `17296` as completed with exit `0:0`; the
  [sanitized artifact receipt](../../outputs/results/revision_20261028/cedia_artifact_recovery.json)
  identifies its surviving log. A completed job and a referenced path do not
  reconstruct the contents of its missing split manifests.
- A response from the infrastructure operator, supplied by the author as pasted
  correspondence rather than independently retrieved email, reports that the
  examined 4 September 2026 backup listing lacked the requested identifiers and
  files. It does not establish whether an earlier backup exists. This document
  does not publish private correspondence or certify a global negative search.

## Specific evidence that would reopen the issue

Request an authorized custodian's inventory first: original relative path,
file size, SHA-256, timestamp and associated job/checkpoint where available;
do not transfer ECG signals or credentials merely to identify a backup.

1. V3M: `v3m_ptbxl_full_p4_folds1_9_train_split90_manifest.csv`,
   `v3m_ptbxl_full_p4_folds1_9_val_split10_manifest.csv`,
   `v3m_internal_val_p4_panel_index.json`, and
   `v3m_internal_val_p4_ASMI_panel.csv`, `v3m_internal_val_p4_LVH_panel.csv`,
   `v3m_internal_val_p4_IMI_panel.csv` and `v3m_internal_val_p4_ISC__panel.csv`,
   with the job `17296` linkage to the checkpoint.
2. Rhythm: `v3p_rhythm_train_v3j_plus_incart_svdb_virtual_manifest.csv`,
   `label_separator_validation_strict_primary_model_ready.csv`, and the
   original V3F/V3AG source, split and job/checkpoint manifests. Do not infer
   exact unknown filenames from these clues.
3. V3H and V3S: parent, pre-filter and pre-balance manifests; eligibility and
   exclusion ledger with reasons; configuration and materialization receipt
   linking those parents to the selected files. The selected manifests alone
   are already available and do not satisfy this request.
4. Original per-ECG pre/post quarantine ledger, policy version, uncertainty
   inputs, transition reasons and execution/checkpoint linkage, if such an
   artifact exists. No such ledger should be presumed to exist.

On receipt, reconcile identities, source provenance, patient overlap,
selection rules and exclusions in restricted storage; publish only permitted
aggregate evidence. Without these inputs, the defensible manuscript action is
to state the selected denominators and the missing historical flow, not invent
the universe or imply that unmeasured exclusions or quarantine were zero.
