# CEDIA Scripts

CEDIA wrappers run the reproducibility verification suite against the checked-out repository, downloaded Release weights, and evaluated cohorts.

For actual waveform execution, `run_frozen_p4_cascade.sbatch` runs P4 or rhythm in a bounded GPU allocation. `run_waveform_reference.sbatch` compares the two completed private ledgers on a CPU node. Both retain commit and job-specific receipts outside Git. The [runbook](../../docs/frozen-waveform-audit.md) documents exact inputs and privacy boundaries.

`verify_waveform_delivery.sbatch` checks exact checkout bytes, frozen aggregate hashes, physical release assets, archived canonical metrics, P8 fallback and AF reference consistency without rerunning the models.
