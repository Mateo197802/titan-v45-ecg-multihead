# Figure reconciliation and replacement

Current repository main checked: `6bf133b1b503fe7e8092a3c109a896cecad6b8a8`. Original scientific evidence baseline: `6f50a6337fc3e8b518655b05916ced7447598b47`.

The original archive contained 15 figure calls but 14 unique image names. This revision retains every scientific figure purpose, replaces the duplicate pathology panel with a distinct plot and adds an aggregate internal-history figure. All 16 figures are newly generated code-based PDF vectors with 320-dpi PNG companions; no third-party illustration is reused.

| Final source | Purpose / source | Action |
|---|---|---|
| fig00_ecg_ai_context | Study schematic; Methods input and reporting contracts | New schematic; arrows represent stated contracts |
| fig00b_ecg_ai_evolution_gap | Endpoint scope schematic | New schematic; arrows represent stated contracts |
| fig01_graphical_abstract | Verified checkpoint and selected-profile contracts | New schematic; arrows represent stated contracts |
| fig02_data_processing_bias_workflow | Reconstructed preprocessing; evidence-stage distinction | New schematic; arrows represent stated contracts |
| fig03_internal_architecture | docs/reviewer_two_comment_rigorous/R2_3F_MORPHOLOGY_FINAL_VALIDATION.md | New schematic; arrows represent stated contracts |
| fig03_cascade_contract | Verified output ontology; no dispatch inferred | New schematic; arrows represent stated contracts |
| fig06_rhythm_confusion | Archived P6 record-level predictions; single-reference subset | Regenerated from real archived scores or aggregate log |
| fig08_class_metrics | Archived P6 predictions; 1000 confusion-multinomial bootstrap replicates, seed 4620846 | Regenerated from real archived scores or aggregate log |
| fig08b_pathology_class_metrics | Archived P4 predictions; 1000 confusion-multinomial bootstrap replicates, seed 4620846 | Replaces the duplicated Figure 10 with actual P4 metrics |
| fig07_pathology_confusion | Archived P4 panel predictions; panel-specific denominators | Regenerated from real archived scores or aggregate log |
| fig09_roc_curves | Archived P6/P4 probabilities; grouped distinct score thresholds; AP uses recall-weighted sum | Regenerated from real archived scores or aggregate log |
| fig10_precision_recall_curves | Archived P6/P4 probabilities; grouped distinct score thresholds; AP uses recall-weighted sum | Regenerated from real archived scores or aggregate log |
| fig11_calibration | Archived binary probabilities; 10 equal-width bins; nonempty bins only | Regenerated from real archived scores or aggregate log |
| fig12_source_performance | Archived P6 source aliases and correctness; Wilson ECG intervals | Regenerated from real archived scores or aggregate log |
| fig13_error_flows | Archived P6 single-reference top-1 confusions; ten largest observed counts | Actual bar chart; withdraws incorrect Sankey/quarantine-interception caption |
| fig16768_internal_history | supplementary/JOB_16768_AGGREGATE_EPOCHS.csv; historical internal run only | Regenerated from real archived scores or aggregate log |

Bootstrap intervals are row-level descriptions. Source accuracy intervals are Wilson ECG intervals. ROC/AP use distinct score thresholds; AP is recall-weighted precision. No figure depicts unfinished independent results.

Original files are preserved in the separate read-only original snapshot; archived artwork does not supply creator identity or third-party permissions. Current diagrams use only text, geometric shapes and verified scientific contracts.
