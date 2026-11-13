# Figures and captions

Each plot has a white background and is supplied as SVG, vector PDF and
300-dpi PNG. All plots use the full matched PR #10 cohort. No individual
records are rendered.

1. **Matched global performance.** [SVG](../figures/figure_01_global_comparison.svg) | [PDF](../figures/figure_01_global_comparison.pdf) | [PNG](../figures/figure_01_global_comparison.png).
   Separate panels show five-endpoint macro-F1, macro-AUROC and macro-AUPRC
   for published P6, published P8 and the adapted model. Whiskers represent
   95% patient-bootstrap intervals for macro-F1 only.
2. **Performance by endpoint.** [SVG](../figures/figure_02_classwise_metrics.svg) | [PDF](../figures/figure_02_classwise_metrics.pdf) | [PNG](../figures/figure_02_classwise_metrics.png).
   F1 at each system's locked cut is shown separately from AUROC and AUPRC,
   which summarize ranking without a fixed operating cut.
3. **Sensitivity and PPV.** [SVG](../figures/figure_03_sensitivity_ppv.svg) | [PDF](../figures/figure_03_sensitivity_ppv.pdf) | [PNG](../figures/figure_03_sensitivity_ppv.png).
   Point estimates and 95% patient-bootstrap intervals for each endpoint
   and system. The thresholds are not shared across systems.
4. **Adapted model confusion matrices.** [SVG](../figures/figure_04_confusion_matrices.svg) | [PDF](../figures/figure_04_confusion_matrices.pdf) | [PNG](../figures/figure_04_confusion_matrices.png).
   Rows are publisher references, columns are binary model calls. Numbers
   are raw TN, FP, FN and TP counts; shading is normalized within each
   reference row. Each endpoint totals 4,921 observations.
5. **Observed Precision-Recall points.** [SVG](../figures/figure_05_observed_precision_recall.svg) | [PDF](../figures/figure_05_observed_precision_recall.pdf) | [PNG](../figures/figure_05_observed_precision_recall.png).
   Authenticated aggregate points at thresholds 0.00 through 1.00 in
   steps of 0.01; undefined PPV is omitted. No interpolated points or
   areas are added. These sampled points do not reconstruct the exact AP
   integral. No original ROC coordinates were identified in the primary
   receipt, so AUROC is shown as a scalar in figures 1 and 2.
