# Reconciliación forense del paquete de recuperación

**Corte:** 2026-11-10. **PR #3 HEAD revisado:** `4d5e7cc6928c23d9088e20182cc5937b53ab3058`. **PR #4 HEAD revisado:** `54ef45e3b79e5b14f41d9e3edae084eb3f4e9bcf`. PR #5 no se consultó para sustentar V4.5.

## Integridad y clasificación

El archivo entregado `TITAN_V45_RECUPERACION_COMPLETA_2026-11-10.zip` coincide con SHA-256 `23523fb59501b916cc6cea55ad0ae669387dbd0b10267a2d4bac7d353f8b5d06`. La inspección estática contó 97 miembros: 95 filas de carga útiles, `INVENTARIO_COMPLETO.csv` y `SHA256SUMS.txt`. CRC, tamaños, SHA de cada fila de inventario y las 96 sumas declaradas coinciden. No hay rutas inseguras, miembros duplicados ni enlaces simbólicos.

La comparación por bytes contra los archivos rastreados en PR #3 y PR #4 encontró 11 contenidos ya presentes. Los 84 restantes no son automáticamente evidencia primaria: 14 comparten nombre base con documentos ya existentes, pero tienen bytes distintos; se tratan como revisiones/recibos que deben contrastarse, no como sustitutos silenciosos. El inventario clasifica 10 fuentes históricas sin vínculo demostrado a un job. Un CSV de trials y la configuración promovida V3C ya estaban idénticos en Git. El agregado SPH y el protocolo congelado también son duplicados exactos del estado fijado en Git.

El ZIP incluye 30 scripts, un lanzador y seis pruebas recuperadas. **No se ejecutó ninguno.** Solo se leyeron documentos, JSON y tablas agregadas; las comprobaciones ejecutadas en esta integración fueron escritas en el repo y tienen pruebas sintéticas. No se extrajeron respaldos ni se cargaron señales.

## Seguridad de publicación

La inspección encontró cero encabezados CSV con columnas de ID por registro y cero marcadores de claves privadas o formatos comunes de tokens en los archivos revisados. Esta es una revisión estática acotada, no una certificación universal de ausencia de secretos. Los recibos brutos contienen rutas internas y referencias a tablas por clave de registro; por eso no se copiarán al repositorio. El ZIP privado, SQLite, señales, filas individuales y reportes crudos permanecen fuera de Git. La vista pública se limita a nombres de artefactos publicados, hashes de checkpoints públicos y agregados sin identificadores.

El paquete registra que ocho bases SQLite y fuentes clínicas se excluyeron de la transferencia. No se generaron reemplazos, bases reconstruidas ni hashes ficticios para esos faltantes.

## Qué cambió

| Hallazgo | Clasificación | Resultado verificable | Límite que permanece |
|---|---|---|---|
| Integridad del ZIP, inventario y sumas | `NEW_DERIVED_VERIFICATION` | 95/95 filas y 96/96 sumas verificadas; CRC correcto. | El ZIP no se publica; la verificación del paquete no autentica por sí sola la procedencia científica de cada documento. |
| Cinco archivos de pesos del release en CEDIA | `NEW_PRIMARY_EVIDENCE` | Tamaño y SHA-256 físicos coinciden con `release_weight_manifest.json`; ver [recibo](receipts/CEDIA_RELEASE_CHECKPOINT_HASHES_2026-11-10.json). | No se recuperó un digest de salida que una cada peso con su job histórico. |
| Dimensiones serializadas de P6/P8 y cabezas globales | `NEW_DERIVED_VERIFICATION` | Tokenización de `data.pkl` con `pickletools`; sin `torch.load`, unpickling, inferencia ni asignación de tensores. Véase [recibo](receipts/CHECKPOINT_TENSOR_SHAPE_AUDIT_2026-11-10.json). | La forma de un tensor no identifica los datos, máscaras de pérdida ni job que lo entrenó. |
| V3C, trial 6 y cadena a V3F | `CORROBORATES_EXISTING_EVIDENCE` | El CSV/configuración V3C ya están en Git; el recibo SLURM aporta estados y rutas declaradas para 16748–16759, 16768 y 16781. | JSON seleccionado, scripts/logs completos, archivos intermedios, manifiestos y aristas de lectura/hash faltan. Ver [linaje](V3C_TRIAL6_CHECKPOINT_LINEAGE.md). |
| Optuna 41M | `NEW_PRIMARY_EVIDENCE` parcial | Registros archivados describen dos generaciones y dos trials completos en jobs fallidos. | Ningún byte de la SQLite original ni enlace a los pesos finales. Se documenta separado en PR #4, [Optuna 41M](https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/codex/titan-a10-optuna-evidence/docs/reproducibility/OPTUNA_41M_NEW_EVIDENCE.md). |
| Cuarentena V4 de mayo | `NEW_DERIVED_VERIFICATION` | La matriz 9×9 y el reporte agregado concuerdan; 461/672 aciertos y 211 errores. El ruteo actúa solo sobre esos 211. | No demuestra cuarentena V4.5 de junio. Ver [disposición](V4_LEGACY_QUARANTINE_DISPOSITION.md). |
| Calibración P4 | `CORROBORATES_EXISTING_EVIDENCE` | Se verificaron cuatro umbrales serializados y 1.492 observaciones de calibración; se mantiene separada la evaluación seleccionada de 962 observaciones. | Los bytes de los manifiestos consumidos y la separación paciente-job no están autenticados. Ver [actualización](HISTORICAL_CALIBRATION_AND_SPLIT_UPDATE.md). |
| Conteos SPH y duplicados de desarrollo | `ALREADY_VERIFIED` / recibo derivado | El agregado SPH es byte idéntico al ya fijado en Git. Un recibo nuevo describe un duplicado exacto en ritmo y ninguno en los 733 ECG P4. | No se repitió inferencia ni el hash de cada señal; el control no cubre el entrenamiento histórico ni duplicados parciales/remuestreados. |

## Dictamen

El paquete aporta nuevas verificaciones de integridad, dimensiones y aritmética, y documentación adicional de observaciones históricas. No recupera los archivos SQLite, el JSON exacto de selección V3C, el loader original, los manifiestos parentales ni el ledger de cuarentena V4.5. No cambia las métricas canónicas ni certifica separación histórica de pacientes. Los cambios por comentario están en [`REVIEWER_15_TECHNICAL_FINAL_MATRIX.md`](REVIEWER_15_TECHNICAL_FINAL_MATRIX.md); las tareas todavía abiertas se enumeran en [`REMAINING_HISTORICAL_RECOVERY_TARGETS.md`](REMAINING_HISTORICAL_RECOVERY_TARGETS.md).

**Reproducir la inspección y comparación byte a byte contra los HEAD examinados:** `python scripts/evaluation/audit_recovery_bundle.py <ruta-al-zip> --expected-sha256 23523fb59501b916cc6cea55ad0ae669387dbd0b10267a2d4bac7d353f8b5d06 --repo <checkout-PR3> --ref 4d5e7cc6928c23d9088e20182cc5937b53ab3058 --repo <checkout-PR4> --ref 54ef45e3b79e5b14f41d9e3edae084eb3f4e9bcf`. El informe imprime conteos de coincidencias/conflictos, pero no rutas internas de los archivos.
