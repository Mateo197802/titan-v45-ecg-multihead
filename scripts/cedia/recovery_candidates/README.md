# Recovered Candidate, Not Certified Historical Preprocessing

`morphology_features_v4.py` was recovered from a surviving V4 source tree on CEDIA. Its exact-byte SHA-256 is `2bd1c1822ed72d1531b1f62712d8007c7e2f21009056ad1a3ee905f37051fc3d`.

It is retained without rewriting its bytes so the forensic replay can identify its provenance. The ten outputs are heuristic proxies, not validated clinical interval measurements. Matching the checkpoint's morphology width does not establish that this was the extractor used for V4.5 training or archived predictions.

The Primary4 forensic replay also reconstructs filtering/context/resampling/normalization from a surviving loader. Its failure to match archived predictions is documented in the revision evidence. Do not treat this candidate as a repaired or validated production pipeline, and do not substitute its scores for the original release results.
