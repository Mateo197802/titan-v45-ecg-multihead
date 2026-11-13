# Autenticación de código recuperado en REV6

REV6 contiene diez miembros de código exportados como texto. Los SHA-256 de la tabla se calcularon sobre los bytes del miembro del ZIP; coinciden con `sha256_exportado` y `sha256_entrada` de la fila de procedencia correspondiente (`identico`). El recibo CEDIA también los clasifica como `CEDIA_HISTORICAL_COPY_VERIFIED` y `calculado_sobre_bytes`. No se recalculó el origen directamente en CEDIA durante esta integración ni se encontró una arista que demuestre qué job consumió cada fuente.

| Miembro exportado | Bytes | SHA-256 | Comparación con PR #3 |
|---|---:|---|---|
| `MODEL_CORE/titan_v4_hybrid.py.txt` | 9.189 | `46bb36737a93a4cfe4be4417f6c62bcbfd0e8e7e8356f31f532ad21662075c80` | Duplicado byte-identical de `scripts/cedia/recovery_candidates/backbone_20260629.py` |
| `TRAINING/build_v3ag_replacement_manifests.py.txt` | 19.107 | `1c0c290dee89985243a0402d5ea8663bb94d11b7fbd658788b41f0a7faece13f` | No existe contenido idéntico rastreado |
| `TRAINING/calibrate_primary6_no_nsr_pac.py.txt` | 12.760 | `caeaf533e9195cd56e52813dce5691ffb52b26abd928060b5767a17c3371cd11` | No existe contenido idéntico rastreado |
| `TRAINING/evaluate_external_v3c_adapted_hpc.py.txt` | 20.937 | `c03213c02f6432172259a08910b9cc62d2f6419cd6ada7fcead61baa13587f67` | No existe contenido idéntico rastreado |
| `TRAINING/optuna_search_hpc.py.txt` | 63.398 | `dbfeea1d46f93f23297a74194ecd9e06d72e78f8163bdaab8db9767c2de0715c` | No existe contenido idéntico rastreado |
| `TRAINING/titan_v45_multihead_contract.py.txt` | 23.314 | `fb64ce8f57119de896812c1d6609f1431e9fad4180605f73cb77eb25adacfd53` | No existe contenido idéntico rastreado |
| `TRAINING/titan_v45_multihead_runtime.py.txt` | 22.488 | `f5161ac848b9012c0d541fba49a1a061c8258cb10e32fde75341934f21c90af3` | No existe contenido idéntico rastreado |
| `TRAINING/train_v3d_specialists_hpc.py.txt` | 147.362 | `8e8d59889a0458c47a90f9735ff6ba017c7e1a79582d11529a608e1816e671fe` | No existe contenido idéntico rastreado |
| `TRAINING/v3ag_source_cv.py.txt` | 3.247 | `fc4d9e7f99bae13a2e4ceeb2937824dc605f4d3631518229db9df5db130a12ea` | No existe contenido idéntico rastreado |
| `TRAINING/v3d_gate_tools.py.txt` | 9.062 | `818428ed31cec0cd8a40c0c822eb9b9fb7eee28afc2b08201dd94ffc7d54cec3` | No existe contenido idéntico rastreado |

Así, diez nombres de fuente se empaquetaron; uno no añade contenido frente al árbol rastreado y nueve sí añaden contenido. Las otras tres adiciones de ruta en REV6 son dos scripts de sonda/captura y un recibo. Los pesos no se deserializaron: los recibos de arquitectura describen análisis sintáctico estático de los miembros `data.pkl`, sin importar PyTorch ni acceder a tensores. El código recuperado tampoco se ejecutó.

La integridad del export no certifica derechos de redistribución. Por eso este PR publica el registro saneado y los hashes, no el código fuente ni los recibos CEDIA crudos. El auditor [audit_cedia_exclusive_revisions.py](../../scripts/evaluation/audit_cedia_exclusive_revisions.py) permite repetir el conteo y la comparación con los árboles rastreados.
