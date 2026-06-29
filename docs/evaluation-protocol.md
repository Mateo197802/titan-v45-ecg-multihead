# Evaluation Protocol

## Rhythm

Rhythm profiles aggregate window logits by record, apply the frozen internal calibration, and make exactly one top-1 prediction for every eligible record. Accuracy is the fraction of correct top-1 predictions. Macro-F1 is the unweighted mean of per-class F1 over the declared profile order.

Primary8 is evaluated over all eight original classes. Primary6 is evaluated only over its six declared classes with full coverage inside that view. Excluding two classes changes the evaluation contract and is always disclosed.

## Pathology

Primary4 is evaluated as four classwise binary panels. Thresholds were selected internally. The reported accuracy is the arithmetic mean of panel accuracies and macro-F1 is the arithmetic mean of panel F1 values.

## Evidence Labels

Internal validation is used for fitting and calibration. Repeatedly observed external cohorts are `external-dev`. Cascade, accepted-subset, and uncertainty-quarantined results are secondary evidence and cannot replace primary full-coverage metrics.
