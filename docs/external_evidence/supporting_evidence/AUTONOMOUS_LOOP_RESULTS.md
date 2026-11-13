# PR #16 autonomous optimization

The [frozen loop report](https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/0e1480b15739581e69f672df349cc3f86244d0f8/docs/performance_recovery/AUTONOMOUS_LOOP_RESULTS.md)
documents six cycles and 28 verified fits (29 attempts, including a timeout).
The final experimental composite had development macro-F1 0.557445 versus
0.580124 for the same-population incumbent. It was not promoted.
The [evidence directory](https://github.com/Mateo197802/titan-v45-ecg-multihead/tree/0e1480b15739581e69f672df349cc3f86244d0f8/docs/performance_recovery/autonomous_evidence)
retains failed and successful hypotheses, aggregate points, hashes, seed
variance, resource use and stopping decisions. The adaptive loop reused
development and transfer evidence; it did not reopen either historical test.
