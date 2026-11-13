# Autonomous loop result

**Decision: retain the incumbent; no promotion.** CEDIA completed six
cycles, 28 verified fits and 29 attempts. Slot `33851` timed out. Slot
`33852` kept the sealed fits, restarted only the interrupted SB seed and
completed the fourth cycle. The stop was `CYCLE_BUDGET`, not a third
stagnant cycle or depletion of the 12 GPU-hour ceiling.

The frozen protocol's short stop description refers to incumbent change,
while its more specific `working_anchor` rule defines stagnation using
the experimental rank. The controller implemented the latter: cycles
5 and 6 were the only consecutive stagnant rounds. A better diagnostic
rank did not imply better CODE F1 or allow an incumbent replacement.
CODE determined epoch selection; the exposed source diagnostics also
influenced arm/family ranking as required by the source-priority rule.

| Cycle | Focus | Decision |
|---|---|---|
| 1 | SB readout, normalization and balance | Shared-gain source policy retained as experimental anchor only |
| 2 | AFIB hard positives and RR features | RR readout retained as experimental anchor only |
| 3 | 1AVB local conduction vs hard negatives | Hard-negative readout retained as experimental anchor only |
| 4 | SB over the composite | Balanced readout retained as experimental anchor only |
| 5 | AFIB over the revised composite | No reproducible advance |
| 6 | 1AVB over the revised composite | No reproducible advance |

CODE selection used 3,088 ECGs from 2,426 patients, with a separate
calibration bank. The best individual F1 (0.580978, cycle 1 residual SB)
and AP (0.553960, cycle 4 linear SB) came from different screens, neither
of which passed SB. Neither is the frozen finalist. The highest-ranked
three-seed experimental family was cycle 4 balanced SB. Its median F1
representative is `04-SB-balanced-20261113`, checkpoint SHA-256
`9104f3c9f9d5371f59b17250949c4ae9aeee8cc2c51a4e84b8bf04edddf16ebb`.
That hash identifies the newest readout checkpoint, not the full
composite: the active AFIB and 1AVB readouts, the superseded SB readout,
and parent weight hashes are in the sealed ancestry.

| CODE metric | Incumbent | Frozen experimental composite |
|---|---:|---:|
| Macro-F1 | 0.580124 | 0.557445 |
| Macro-AUPRC | 0.550330 | 0.536772 |
| Brier | 0.017123 | 0.013754 |
| ECE | 0.015397 | 0.007124 |

The paired patient-bootstrap macro-F1 difference is -0.022679 (95%
interval [-0.048088, +0.002268]), descriptive on repeatedly used
selection data, not confirmation. The three family F1 scores were
0.552629, 0.557445 and 0.557485. One passed all class guards; none improved
F1 over the incumbent. The representative failed SB. AFIB and SB
sensitivity/PPV were 0.576/0.507 and 0.509/0.351; 1AVB was 0.745/0.336.
The 1AVB false positives increased from 61 to 81. STACH and RBBB were
unchanged by construction.

This is three-seed repeatability of the focal adjustment with the same
prior composite fixed, not three independent reruns of the full search
or evidence of stability on an untouched population.

Chapman five-class macro-F1 was 0.526211 to 0.559327. Its SB AP rose
from 0.651744 to 0.955119, but sensitivity at the locked CODE cut only
rose from 24/265 to 42/265. This candidate trained on the Chapman
development training bank, not its validation rows. The 1AVB support
was below the frozen threshold for a five-class interval. CPSC three-class
macro-F1 was 0.806283 to 0.823636 (paired ECG-bootstrap difference
+0.017352, interval [+0.005739, +0.029394]). CPSC had prior exposure
and lacks authenticated patient grouping.

The operating-point mismatch between sources remains a stronger lead
than another topology sweep: the shared-gain/source-calibration SB arm
had useful Chapman discrimination but did not pass CODE constraints.
An independent institution with harmonized references and authorized
processing is still needed. The prior reserved tests were not opened.
HEEDB was not acquired. `INDEPENDENT_GENERALIZATION: NOT_EVALUATED`.

## Verification

The nine controller slots allocated 9,603 GPU-seconds (2 h 40 min 3 s),
including the timeout and two terminal no-op slots. Checkpoint replay
`33861` added 78 GPU-seconds; the CPU audits did not allocate a GPU.
The complete measured GPU allocation was 9,681 seconds (2 h 41 min 21 s).
Export job `33860` verified all checkpoint and score hashes and independently
recalculated 364 rows with maximum absolute metric error 3.33e-16.
[Checkpoint replay](AUTONOMOUS_CHECKPOINT_REPLAY.json) reproduced all five
scores with zero error on 64 ECGs each in CODE, Chapman and CPSC.
[Interval audit](AUTONOMOUS_INTERVAL_READBACK.json) reproduced all 1,000
CODE paired patient replicates for macro-F1 to within 1.08e-16 at the
reported point and interval bounds.

The [public bundle](autonomous_evidence/) contains the decisions, SLURM
ledger, curves, class metrics, three-seed results and hash manifest.
Individual predictions and experimental weights remain in CEDIA.
