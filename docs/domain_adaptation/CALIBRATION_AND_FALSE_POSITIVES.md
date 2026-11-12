# Calibration and false positives

In the corrected CODE validation cohort, released operating points retain their
registered thresholds. For sinus bradycardia with per-lead normalization, P6
has 35 true positives and 595 false positives; P8 has 43 and 855. This yields
precision of 5.56% and 4.79%, respectively, despite sensitivities of 66.04% and
81.13%. The observed positive support is 53/3088 ECG. This is a precision and
operating-point problem, not just a sensitivity problem.

With robust shared gain, P8's 1AVB false positives fall from 19 to 2, but its
true positives also fall from 10 to 1 (55 positives). A lower false-positive
count on its own is not an improvement. Full contingency counts, Brier score,
ECE, AP and AUROC are available in the [matched controls](evidence/SIGNAL_PROCESSING_ABLATIONS.csv).

The candidate operating threshold will be estimated only after validation-only
selection, using the separate calibration set and a frozen classwise objective.
The comparison preserves the released thresholds; candidate versus released
operating metrics measure both learned discrimination and the different
calibration policies. AP and AUROC accompany F1, sensitivity, PPV and error
counts to help distinguish changes in ranking from threshold effects. No choice
of preprocessing or threshold is optimized against the reserved test.
