# Autonomous development optimization

The training controller and protocol were sealed at `3ae5d7a`, before
any loop fitting. PR #15 remains the immutable input baseline. The loop
uses the authorized development banks and archived incumbent scores from
PR #11, with the PR #15 calibration and class constraints. It never reads
the historical test manifests or scores.

## Execution and restart

Use an isolated checkout of the sealed training commit and a new private
study directory. The submit script takes the checkout, study directory,
Python and HDF5 dependency archives, authorized development bank root, and
the sealed incumbent score root. It submits an `afterany` chain. A
single successful allocation completes at most one cycle. Terminal
no-op allocations do not run experiments. Do not edit the protocol or
checkout beneath an active allocation.

The controller locks the study, writes its pending operation before
fitting, and publishes a fit directory by atomic rename after verifying
the checkpoint, private scores and receipt. A later slot skips completed
receipts. An interrupted attempt without a complete receipt is retained
and retried at most once. The original scheduler ledger records failures
and allocated GPU seconds. Validation and calibration banks remain
private; publication is restricted to the aggregate exporter output.

The first five SB arms implement frozen linear, residual, partial
fine-tuning, shared-gain with a separate source calibration, and
patient/source-balanced training. AFIB then tests hard positives and RR
features; 1AVB tests local lead II/V2 temporal features and hard negatives.
The selection function prioritizes operating guards, rather than peak
AUPRC. A three-seed experimental anchor may advance without replacing the
development incumbent. These are distinct states in the delivery.

## Interpretation

The candidate is a composite of endpoint-specific readouts and immutable
off-target outputs, not a single interchangeable replacement release
checkpoint. The ancestry chain, parent weight hashes, and source-specific
calibration policy are required to recreate it. The final replay rebuilds
the composite from checkpoint bytes. An additional readback independently
recomputes aggregate metrics from sealed private predictions.

CODE validation is used repeatedly for selection. Chapman and CPSC are
exposed transfer diagnostics, not independent confirmation. Neither
positive gains nor intervals on these banks establish a new institutional
result. CPSC intervals are ECG-level; its patient keys are not certified.
