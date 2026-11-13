# Independent confirmation eligibility

Status: **NOT_EVALUATED**. Public catalogue and study documentation only. No new waveform, diagnostic test, or patient-linked files were opened. HEEDB access and CEDIA processing authorization were not confirmed; it was neither downloaded nor processed.

| Candidate | Evidence available before acquisition | Disposition |
|---|---|---|
| [KURIAS-ECG v1.0](https://physionet.org/content/kurias-ecg/1.0/) | Korea University source; 10-second 12-lead waveforms and the target diagnostic concepts are described by the [dataset authors](https://pmc.ncbi.nlm.nih.gov/articles/PMC10209728/). | PhysioNet explicitly disabled downloads. Do not acquire from mirrors. |
| [CODE-II-open / CODE-II-test](https://doi.org/10.1038/s41746-026-02704-4) | From the same Minas Gerais telehealth network as CODE-15%; a later period does not exclude recurring patients. The release describes access for non-commercial use, not this project's historical overlap. | Not an additional institution. No cohort selected or downloaded. |
| [LUDB v1.0.1](https://physionet.org/content/ludb/1.0.1/) | 200 10-second 12-lead ECGs at 500 Hz, with P/QRS delineation. The provider reports 4 STACH, 10 first-degree AV block, and 4 complete RBBB ECGs. | Cannot meet 20 positive patients for these endpoints, even with a different ECG per patient. Incomplete RBBB is not a substitute. Potential future delineation-method check, not five-endpoint confirmation. |
| SPH, PTB-XL, Chapman, CPSC, Georgia | Used or analyzed previously in TITAN work; see [prior source-exposure audit](../specialist_heads/SPECIALIST_SOURCE_GENERALIZATION.md). | No new independent claim; Chapman/CPSC aggregates here are development diagnostics. |
| MIMIC-IV-ECG | The existing adaptation uses only training waveforms. Automatic reports do not supply the clinically reviewed positive/negative reference required for this gate. | No diagnostic label or held-out waveform access in this recovery study. |

Reopen confirmation only after an authorized additional institution provides a patient grouping key, signal contract and explicit five-endpoint label semantics including negatives. Document non-use by model development and search for exact and re-encoded overlaps against available historical and current sources. Seal a whole-cohort manifest, protocol, model and threshold hashes before viewing outcomes; report unresolved historical exposure as a limitation. The frozen promotion gate is not satisfied by a new split of already examined CODE patients.
