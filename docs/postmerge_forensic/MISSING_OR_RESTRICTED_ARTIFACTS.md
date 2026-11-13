# Missing or restricted evidence

- **Historical V3C database:** exact `optuna_primary8_primary4.db` target,
  historically 135,168 bytes. Nine archival candidate results are not the
  database. Require SQLite bytes, integrity check, study/trial and
  intermediate-state readback with producer provenance.
- **Historical loader:** the inventoried 36,271-byte original and hash
  have not been authenticated. The reconstructed 36,465-byte candidate
  is deliberately not promoted. See [recovery and replay](../recovery-status-20261029.md).
- **16768 to 16781:** missing parent checkpoint content SHA and bound
  read/write evidence, exact train/validation manifests and linkage,
  original runtime environment and complete per-job input trace.
  Historical V3F output-path digest match is not a substitute.
  The directly inspected final completion excerpt confirms counts and
  completion but does not contain the full 50-epoch trace; the tracked
  shared-backbone figure table contains eight epochs and is not evidence
  for the full 16768 run.
- **Historical all-input workflow:** preselection roster, rejected
  records, original all-ECG quarantine and downstream dispositions are
  not available. No derivation from selected P6/P8/P4 subsets fills them.
- **Present but restricted:** native checkpoint and score byte hashes are
  retained without releasing paths or data. Many checkpoint architectures,
  tensor strict-load tests and producer bindings are not authenticated by
  a hash read; the register retains those gaps.
- **Coverage boundary:** this audit indexes explicit Git refs, named local
  archives and named authorized CEDIA roots; not every user directory,
  filesystem backup, data shard, live SQLite WAL, or notebook. A bounded
  negative search must not be interpreted as absence everywhere.
