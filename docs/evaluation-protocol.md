# Evaluation Protocol

## Rhythm

Rhythm profiles aggregate window logits by record and use frozen release thresholds. Each record has a top-1 label; the released evidence also retains classwise threshold decisions and, for Primary8, multilabel reference and prediction sets.

Primary8 uses the eight-class profile. Its reported accepted-label accuracy counts a top-1 prediction as correct when `predicted_label` belongs to the reference `accepted_labels` set. Its binary-panel macro-F1 compares `accepted_labels` and `predicted_labels` one class at a time, then averages the eight F1 scores. The single-target diagnostic (`target_label == predicted_label`) is a different metric.

Primary6 diagnostic uses its six-class profile. Its top-1 accuracy counts a prediction as correct when `pred_label` belongs to `true_labels`; some records have more than one true label. Its binary-panel macro-F1 is recalculated from the classwise `truth_<class>` and `threshold_pass_<class>` fields. Coverage is 100% within this profile.

## Pathology

Primary4 is evaluated as four classwise binary panels using frozen release thresholds. The reported accuracy is the unweighted mean of panel accuracies and macro-F1 is the unweighted mean of panel F1 values.

## Evidence Labels

Internal validation reports, released validation cohorts, cascade outputs, and uncertainty-quarantined outputs are separated by directory. Primary reports use the declared class order, full eligible coverage, top-1 rhythm prediction, and classwise binary pathology panels.
