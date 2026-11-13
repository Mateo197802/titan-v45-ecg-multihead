# Historical loader identity and replay

**As of:** 2026-11-09. This report separates exact-source recovery, deterministic replay of the reconstructed implementation, and agreement with saved decisions. It does not change the model, thresholds, historical outputs or manuscript.

## Expected source and candidates

The inventory's expected original `data_loader_ultra.py` is 36,271 bytes with SHA-256 `fc8d7367f9f2c108376839435021ec3172fe2757faa4a615f0ef5d39cbf1e855`. No exact raw or CRLF-to-LF-normalized match was found among 34 examined loader candidates.

The candidate recovered at `recovered/data_loader_ultra.py` is 32,435 bytes, SHA-256 `a2c854acd43615a1ed78b5ed77c46a0252ec3607438df32d6a88e52fb0f91ddc`. Its CRLF-normalized form is 31,765 bytes, SHA-256 `0e35bd15fedf88420e34ee7cef77eab929b8454d02600f8c1301c375ad135fec`. Neither is the expected source. A filename match, tensor shape or successful `load_state_dict` does not establish equivalent lead order, resampling, filtering, normalization, morphology, padding or event definitions.

The incremental inventory and NOC response did not recover the expected loader. The surviving candidate is useful for forensic comparison only and must be described as reconstructed/candidate code, not as the exact historical loader.

## Replay results

| Profile | Stored-decision comparison | Numerical comparison | Interpretation |
| --- | --- | --- | --- |
| P4 | 962/962 panel decisions agree. | Maximum probability difference `0.0006194115`, exceeding the prefixed tolerance `0.00001`. | Decision replay succeeds; strict probability equivalence fails. Do not widen the tolerance. |
| P6 | 1,642/1,643 top-1 decisions agree; binary sets agree. | Same-reference replay is not the canonical published estimate; one decision differs. | High decision concordance, not exact replay or independent validation. |
| P8 | 2,193/2,193 top-1 decisions and binary sets agree, including 58 fallback cases. | Does not establish score equivalence or a passed full-profile gate. | Rule concordance only; retain candidate status and canonical metrics. |

The SPH transfer run uses the explicitly frozen reconstructed processing contract in its protocol: source input is normalized to the model's 125 Hz, 12-lead, 1,250-sample window. This is reproducible evidence for that new transfer experiment, not evidence that the unavailable historical loader used the identical operations.

## Related CEDIA logs

Jobs 17296 and 17305 provide calibration/gate summaries but do not identify the exact waveform loader bytes consumed by each training stage. Job 17314 contains an epoch sweep and job 17315 records the V3H gate; their missing submitted scripts prevent a complete source-code-to-output hash chain. None of these logs repairs the loader identity gap.

## Closure rule

Do not claim the original waveform pipeline was exactly reproduced unless an independently linked source snapshot matching the expected identity is recovered and the complete input/checkpoint/configuration chain is demonstrated. Preserve the observed residuals and discrepancies. No model tuning, threshold search on evaluation data, tolerance relaxation or replacement historical prediction has been performed for this audit.

The recovered CEDIA cleanup manifest did not list the expected `data_loader_ultra.py` name or any V3H/V3S/V3M/V3P split or panel-index names. The check is limited to that path/size inventory; it does not prove absence from every CEDIA backup. See the [sanitized manifest receipt](receipts/CEDIA_CLEANUP_MANIFEST_TRIAGE_2026-11-10.json).
