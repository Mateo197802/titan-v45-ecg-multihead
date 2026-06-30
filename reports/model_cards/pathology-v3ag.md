# Pathology V3AG Branch Model Card

## Purpose

Research evaluation of four classwise pathology panels: `ASMI`, `LVH`, `IMI`, and `ISC_`.

## Artifacts

- V3AG backbone SHA-256: `bf71e4cf8acc34031cb3611c7031e0649822e705fd7dcea354a3ea583ce920ee`
- Calibrated Primary4 specialist SHA-256: `cf5091e962fffb3254b1a71fe57236dd82ea0139093df192511499d931391dbc`

## Results

The released validation panels reached 80.2290% mean accuracy and 79.3456% macro-F1 at 100% panel coverage. `LVH` is the lowest classwise F1 at 65.7277%.

## Limitations

Panels use high-confidence labels and classwise binary thresholds. This branch uses a separately fine-tuned backbone and should be loaded with the declared Primary4 specialist.
