# Evaluation Scope

1. Primary8, Primary6 diagnostic, and Primary4 are separate release profiles with fixed class orders, thresholds, and artifact hashes.
2. Rhythm accuracy is record-level top-1 accuracy over the declared rhythm profile.
3. Primary4 accuracy is mean classwise binary-panel accuracy over `ASMI`, `LVH`, `IMI`, and `ISC_`.
4. The V3F rhythm branch and V3AG pathology branch are distributed as separate operational branches.
5. Public metrics use full eligible coverage for each profile, with no top-k oracle and no hidden abstention.
6. MC-Dropout entropy, mutual information, and quarantine rules are research uncertainty controls.
