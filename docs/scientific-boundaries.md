# Evaluation Scope

1. Primary8, Primary6 diagnostic, and Primary4 are separate release profiles with fixed class orders, thresholds, and artifact hashes.
2. Primary8's 90.61% result is accepted-label top-1 accuracy; its 76.14% macro-F1 compares the reference and predicted multilabel sets class by class. The separate single-target accuracy is 85.27%.
3. Primary6's 95.19% top-1 accuracy uses membership in `true_labels`; its 80.09% macro-F1 averages six thresholded binary panels.
4. Primary4 accuracy is mean classwise binary-panel accuracy over `ASMI`, `LVH`, `IMI`, and `ISC_`. Project acceptance does not alter the observed 80.23% accuracy or 79.35% macro-F1.
5. The V3F rhythm branch and V3AG pathology branch are separate operational branches; no single checkpoint contains both reported specialists.
6. Public metrics use full eligible coverage for each profile, with no top-k oracle and no hidden abstention.
7. MC-Dropout entropy, mutual information, cascades, and quarantine rules are research uncertainty controls.
