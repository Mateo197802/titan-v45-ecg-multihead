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

The candidate operating threshold was estimated only after validation-only
selection, using the separate calibration set and a frozen classwise objective.
The comparison preserves the released thresholds; candidate versus released
operating metrics measure both learned discrimination and the different
calibration policies. AP and AUROC accompany F1, sensitivity, PPV and error
counts to help distinguish changes in ranking from threshold effects. No choice
of preprocessing or threshold is optimized against the reserved test.

In the reserved comparison, the candidate macro-Brier was 0.014944 and
macro-ECE 0.014245, compared with 0.104780/0.157275 for P6 and
0.095117/0.142728 for P8. Candidate reliability curves suppress bins with
fewer than ten ECGs, while the aggregate ECE uses all eligible scores.
Lower Brier and ECE do not override sensitivity safeguards. In AFIB,
the candidate reduced false positives to 50 from P6's 309 and P8's 227,
but missed 45 positive ECG (versus 32 and 38). This trade-off fails the
AFIB sensitivity guard. See the [decision and matched counts](FINAL_MODEL_PROMOTION_DECISION.md).
