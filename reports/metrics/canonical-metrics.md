# Canonical Metrics

| Profile | Accuracy | Macro-F1 | Coverage | Metric definition |
|---|---:|---:|---:|---|
| Primary8 | 0.9060647515 | 0.7614253535 | 1.0 eligible | record top-1 plus binary-panel macro-F1 |
| Primary6 diagnostic | 0.9519172246 | 0.8009383240 | 1.0 eligible | record top-1 plus binary-panel macro-F1 |
| Primary4 | 0.8022904854 | 0.7934563704 | 1.0 selected panels | mean binary-panel accuracy plus binary-panel macro-F1 |

Rhythm accuracy is record-level top-1 over the declared rhythm profile. Primary4 accuracy is mean binary-panel accuracy over `ASMI`, `LVH`, `IMI`, and `ISC_`.
