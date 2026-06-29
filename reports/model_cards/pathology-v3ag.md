# Pathology V3AG Branch Model Card

## Purpose

Research evaluation of four classwise pathology panels: `ASMI`, `LVH`, `IMI`, and `ISC_`.

## Artifacts

- V3AG backbone SHA-256: `bf71e4cf8acc34031cb3611c7031e0649822e705fd7dcea354a3ea583ce920ee`
- Calibrated Primary4 specialist SHA-256: `cf5091e962fffb3254b1a71fe57236dd82ea0139093df192511499d931391dbc`

## Results

The selected external-development panels reached 80.2290% mean accuracy and 79.3456% macro-F1 at 100% panel coverage. Status is `ACEPTADO_POR_DECISION_DEL_PROYECTO`, not metric-gate success. `LVH` is the weakest class at 65.7277% F1.

## Limitations

Panels were selected for high-confidence labels and do not represent complete external population coverage. This branch uses a separately fine-tuned backbone and must not be silently combined with the best rhythm specialist.
