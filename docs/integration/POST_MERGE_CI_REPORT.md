# Post-merge verification

The combined [GitHub CI run](https://github.com/Mateo197802/titan-v45-ecg-multihead/actions/runs/43338162743)
passed on Python 3.10, 3.11, and 3.12 for candidate `3e11ecf`. The
scientific merge `85c1d8e` has exactly the same Git tree. Its
[main CI run](https://github.com/Mateo197802/titan-v45-ecg-multihead/actions/runs/43338782307)
is recorded in the machine-readable verification receipt.

On a fresh detached checkout of the actual scientific merge in main:

- Pytest: **777 passed**. Ruff: passed. Python compilation: passed.
- Shell syntax: 69 changed launchers checked. JSON/TOML: 28 JSON
  configurations and package metadata parsed. 178 relative links across
  the integrated evidence and integration guides resolved.
- Byte inventory: all 1,148 files matched Git archive. The historical
  waveform receipts still match their published aggregates.
- Reconciliation: 40 criteria, 15 comments, 59 evidence artifacts,
  14 pinned Git links, and unchanged 20.5/40 overall.
- Reviewer evidence: original 70- and 29-member ZIPs verified, with
  morphology, selective prediction and cascade arithmetic recomputed.
- Independent aggregate readbacks: SPH (25,770 ECGs), Stage A,
  adaptation, recovery and BenchmarkMax B1, scale and prevalence.
- GitHub release metadata matched declared size and SHA-256 for all
  seven payloads. The binaries were not re-downloaded or replaced.
- The original CODE-15% native score, padding and independent delivery
  jobs 33573, 33574 and 33575 were confirmed `COMPLETED 0:0`. Both
  CEDIA receipts were read back and matched the integrated bytes.
  The integration-specific repeat is job 33831; its separately recorded
  status does not turn public receipt verification into record-level
  recomputation. No private inputs were copied to the public repository.

No original PR branch was deleted. A documentation-only receipt follows
the scientific integration commit and does not change the tested code.
