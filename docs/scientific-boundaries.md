# Scientific Boundaries

1. Full Primary8 did not pass its declared accuracy gate.
2. Primary6 is a diagnostic view that excludes `NSR` and `PAC`; it is not Primary8.
3. Promoted Primary4 has 80.2290% mean binary accuracy and 79.3456% macro-F1. Its project-acceptance status does not rewrite the observed accuracy as 90% or 95%.
4. The strongest rhythm and pathology branches do not share one frozen backbone.
5. Repeated external inspection creates external-development evidence and possible selection bias.
6. The Primary6 margin is narrow: three correct records above the 95% accuracy minimum and 0.0938 percentage points above the 80% macro-F1 threshold.
7. Source-held-out rhythm validation was weak. Generalization of full Primary8 remains unresolved.
8. Mean binary accuracy is not top-1 accuracy and must not replace it.
9. Primary metrics contain no top-k oracle or hidden abstention.
10. MC-Dropout and quarantine are uncertainty controls, not correctness guarantees.
