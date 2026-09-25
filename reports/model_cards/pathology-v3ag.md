# Pathology V3AG Branch Model Card

## Purpose

Research evaluation of four classwise pathology panels: `ASMI`, `LVH`, `IMI`, and `ISC_`.

## Artifacts

- V3AG backbone SHA-256: `bf71e4cf8acc34031cb3611c7031e0649822e705fd7dcea354a3ea583ce920ee`
- Calibrated Primary4 specialist SHA-256: `cf5091e962fffb3254b1a71fe57236dd82ea0139093df192511499d931391dbc`

## Results

On the repeated external-development evidence, the four panels reached 80.2290% mean binary-panel accuracy and 79.3456% macro-F1 at 100% coverage within the selected panels. `LVH` is the lowest classwise F1 at 65.7277%. The Primary4 branch was accepted by project decision; this status does not change the measured metrics or imply that a 90% or 95% accuracy threshold was reached. See the [evidence status](../../docs/evidence-status.md) and [recomputed metrics](../../outputs/results/external_dev/README.md).

## Limitations

Panels use high-confidence labels and classwise binary thresholds. This branch uses a separately fine-tuned backbone and should be loaded with the declared Primary4 specialist.
