# Objetivos históricos que aún faltan

Este registro distingue archivos no recuperados de archivos no presentes en una ruta específica. La falta de hallazgo no prueba inexistencia universal. No repetir búsquedas amplias sin una pista nueva; solicitar solo copias, catálogos o recibos concretos al custodio autorizado.

## Faltantes técnicos decisivos

| Objetivo | Estado al 2026-11-10 | Evidencia que reabriría la arista |
|---|---|---|
| `selected_candidate_v3c_trial6_final.json` | `NOT_PRESENT_AT_REFERENCED_PATH`; 16768 lo cita, pero no hay bytes, SHA ni recibo de lectura. | Archivo exacto preservado con SHA, timestamp/metadata y salida de job que demuestre lectura por 16768. |
| Salida `titan_v4_final_best.pt` de 16768 | `NOT_PRESENT_AT_REFERENCED_PATH`; 16781 declara esa ruta como base; no se recuperó digest del output de 16768. | Checkpoint físico, SHA, metadata de serialización, logs/batch script de 16768 y evento de escritura. |
| Entrada y salida de 16781 | `NOT_PRESENT_AT_REFERENCED_PATH` en la ubicación consultada; el job se registra `COMPLETED`, pero falta evidencia de consumo/output hash. | Digest de la entrada abierta por 16781, su launcher/log real, y digest de `titan_v4_v3f_finetuned_best.pt` producido. |
| Relación salida 16781 → `backbone-v3f-original.pt` | `UNVERIFIED_EDGE`; el peso del release está autenticado, pero no hay equality hash con el output histórico. | Mismo SHA-256 de salida y asset de release, o recibo firmado de promoción que identifique bytes. |
| Base V3C y trial history completo | `NOT_RECOVERED`; existe un snapshot CSV de 9 filas, no la SQLite o export completo de 12 trials. | SQLite original/WAL coherente o export con estados, valores, tiempos y código de objetivo fijados, ligado a job/config. |
| `titan_v45_41m_multihead_optuna.db` y copia `..._before_resume.db` | `NOT_RECOVERED`; dos generaciones con el mismo nombre se describen en recibos distintos; no se transfirieron bytes SQLite. | Ambas DB o snapshot consistente, WAL/SHM pareados, `study_name`, secuencia de trial states y logs/checkpoint ligados. |
| Manifiestos efectivamente consumidos por V3C/V3F/V3AG/V3M/V3H/V3S | `REFERENCED_ONLY` en parte; algunos nombres y rutas aparecen en los envíos, no los bytes auténticos ni su digest de lectura. | Train/validation/calibration/test CSV/JSON exactos, SHA, exclusiones/parents, fuente y versión de datos, recibo de lectura por job. |
| Separación de pacientes/señales | `PATIENT_ISOLATION_NOT_CERTIFIED`; la comprobación de folds nominales no identifica lo abierto por cada job. | Mapas de paciente por partición dentro de CEDIA autorizado, comprobación exacta y near-duplicate con la población de entrenamiento, unida a manifests y checkpoints. No publicar IDs. |
| Loader histórico `DATA_PIPELINE/data_loader_ultra.py` | `NOT_RECOVERED`; ningún candidato inspeccionado tiene los 36.271 bytes LF y SHA esperado `fc8d7367f9f2c108376839435021ec3172fe2757faa4a615f0ef5d39cbf1e855`. | Copia con hash exacto, o fuente/job reproducible que identifique el archivo y dependencias originales. No renombrar el candidato de 32.435 bytes como original. |
| Cuarentena V4.5 de junio | `NOT_ASSESSED`; el diagnóstico V4 de mayo se limita a 211 errores y no está ligado a V4.5. | Ledger por ECG en CEDIA con población elegible, incertidumbre, política/umbral congelados, estado pre/post, decisión, motivo, referencia y job/checkpoint hashes. |
| Parent V3H/V3S antes de balance/selección | `NOT_RECOVERED`; manifests retenidos no permiten invertir a la población de entrada ni reconstruir descartes. | Parent manifests, descartes con motivos, fuente/dataset/versiones y hashes de los archivos realmente leídos. |
| Derechos/procedencia de fuentes mixtas | `REQUIRES_CUSTODIAN/AUTHOR`; bytes e identidades técnicas no bastan para redistribuir. | Licencias/permisos y procedencia por fuente revisadas por titular/autores. Mantener `HOLD` hasta esa verificación. |

## Búsquedas delimitadas ya documentadas

- La respuesta NOC compartida por los autores informa que se examinó un respaldo institucional del **04-09-2026 17:00:01** y que no contenía las rutas/identificadores `20260623_*` solicitados. Es un resultado negativo de ese backup, no de todos los respaldos institucionales o de todos los colaboradores.
- El inventario del ZIP informa búsquedas de rutas activas y auxiliares, del archivo parcial del 29 de junio y de objetos/logs disponibles. Clasifica los candidatos de loader como no idénticos y la base 41M como no recuperada.
- El 10-11-2026 se consultaron en CEDIA las tres rutas concretas registradas para el JSON de trial 6 y los checkpoints intermedios de 16768/16781; no estaban presentes en esos paths. Los cinco archivos físicos del release sí se localizaron y verificaron.
- Los recibos SLURM del ZIP marcan `SLURM_REPORTS_NONE` para batch/environment en los jobs relevantes. Un estado `COMPLETED 0:0` prueba el estado registrado, no la existencia del archivo de salida ni que un manifiesto se leyera.

## Límite de búsqueda y solicitud mínima

No se concluye que los archivos jamás existieron ni que se borraron intencionalmente. Para reabrir la recuperación bastaría con que el custodio autorizado entregue **un catálogo** con la ruta/fecha/tamaño y hash de una copia pertinente, o un recibo de job con el digest de entrada/salida. No se solicita transferencia de señales o filas individuales. Si no existe otro snapshot, ese hecho debe confirmarlo el custodio; una nota editorial no sustituye los experimentos o splits ausentes.
