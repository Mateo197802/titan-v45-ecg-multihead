# Evaluation Protocol

## Rhythm

Rhythm profiles aggregate window logits by record, apply frozen release thresholds, and make exactly one top-1 prediction for every eligible record. Accuracy is the fraction of correct top-1 predictions. Macro-F1 is the unweighted mean of per-class F1 over the declared profile order.

Primary8 is evaluated over its eight declared rhythm classes. Primary6 diagnostic is evaluated over its six declared rhythm classes with full coverage inside that profile.

## Pathology

Primary4 is evaluated as four classwise binary panels using frozen release thresholds. The reported accuracy is the arithmetic mean of panel accuracies and macro-F1 is the arithmetic mean of panel F1 values.

## Evidence Labels

Internal validation reports, released validation cohorts, cascade outputs, and uncertainty-quarantined outputs are separated by directory. Primary reports use the declared class order, full eligible coverage, top-1 rhythm prediction, and classwise binary pathology panels.
