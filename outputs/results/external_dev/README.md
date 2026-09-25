# External-Development Results

These are repeated external-development evaluations. The per-record tables are the inputs to [`verify_release_evidence.py`](../../../scripts/evaluation/verify_release_evidence.py); the script recalculates the results, compares them with the reports below, checks cohort manifests, and prints hashes of the evidence files.

| Profile | Result file | Per-record evidence | Interpretation |
| --- | --- | --- | --- |
| Rhythm Primary6 diagnostic | [`rhythm_primary6_metrics.json`](rhythm_primary6_metrics.json) | [`rhythm_primary6_record_predictions.csv`](evidence/rhythm_primary6_record_predictions.csv) | 1,643 records; 95.19% top-1 accuracy; 80.09% binary-panel macro-F1. Accuracy uses membership in `true_labels`; panel F1 uses `truth_*` and `threshold_pass_*`. |
| Pathology Primary4 | [`pathology_primary4_metrics.json`](pathology_primary4_metrics.json) | Four per-class prediction tables in [`evidence/`](evidence/README.md) | 962 panel observations; 80.23% mean binary-panel accuracy; 79.35% macro-F1. Accepted by project decision with the measured values unchanged. |
| Rhythm Primary8 | [`rhythm_primary8_metrics.json`](rhythm_primary8_metrics.json) | [`rhythm_primary8_record_predictions.csv`](evidence/rhythm_primary8_record_predictions.csv) | 2,193 records; 90.61% top-1 accepted-label accuracy; 76.14% binary-panel macro-F1. Candidate only; it does not meet the 97% accuracy and 80% macro-F1 gates. |

For Primary8, accepted-label accuracy checks whether `predicted_label` is contained in the reference `accepted_labels` set. Its binary-panel macro-F1 compares the reference `accepted_labels` and model `predicted_labels`. The separate single-target accuracy is 85.27% (1,870/2,193).

Counts, declared class order, frozen thresholds, release roles, and cohort scope are retained in the JSON reports. Cohort-to-prediction links are in [`data/manifests/external_dev/`](../../../data/manifests/external_dev/) and the [cohort reports](../../../data/external_dev/).
