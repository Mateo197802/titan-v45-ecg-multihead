# V3C trial 6 y linaje de checkpoints

**Alcance:** V4.5, recibos archivados de CEDIA y artefactos públicos fijados. No se reconstruyó ni ejecutó el entrenamiento. No se modificó ningún checkpoint.

## Selección registrada

`outputs/results/optuna/v3c_promoted_configuration.json` y `tests/figure_evaluation/tables_snapshot/optuna_trials.csv` ya estaban en Git con bytes idénticos a los del ZIP. El CSV contiene nueve filas; la configuración declara 9 trials completados de 12 planificados.

| Trial | `ranking_score` guardado | `peak_composite_score` guardado | Lectura correcta |
|---:|---:|---:|---|
| 6 | 0.6245117257 | 0.6313837131 | Mayor `ranking_score`; el resumen promovido guarda este trial. |
| 8 | 0.5831962899 | 0.6509403856 | Mayor pico de composite, pero no mayor `ranking_score`. |

La elección del 6 sobre el 8 se explica por la diferencia entre las dos columnas registradas; no se volvió a calcular la función de selección ni se recuperó la base Optuna original. Los 12 jobs 16748–16759 aparecen como `COMPLETED`, pero no equivalen a doce trials completos: el snapshot muestra nueve filas y el resumen conserva el plan de doce.

## Cadena de procedencia

| Arista | Evidencia disponible | Estado | Qué falta para autenticarla |
|---|---|---|---|
| Estudio V3C → trial 6 | Resumen y CSV versionados; mayor `ranking_score` entre nueve filas. | `VERIFIED_COMPLETE_WITHIN_SCOPE` para la clasificación del snapshot; procedencia del estudio parcial. | SQLite/export completo, estados y valores intermedios de los doce trials, código/objetivo y split realmente consumido. |
| Trial 6 → `selected_candidate_v3c_trial6_final.json` | El registro de envío de 16768 nombra esa ruta. | `UNVERIFIED_EDGE`: referencia de ruta. | Bytes y SHA del JSON, fecha, contenido comparable con el resumen y evidencia de lectura por el proceso. |
| JSON seleccionado → job 16768 | 16768 figura `COMPLETED`, `0:0`; el envío declara train/val, directorio de salida y la ruta del JSON. | `UNVERIFIED_EDGE`: envío/estado no es recibo de lectura. | Batch script y log de ejecución íntegros, argumento efectivo, ambiente y manifest digests. |
| Job 16768 → `titan_v4_final_best.pt` | El run directory y el nombre de salida se registraron en el envío. | `UNVERIFIED_EDGE`. El archivo no está presente en la ruta histórica consultada el 2026-11-10. | Archivo físico y SHA de salida, metadata de producción, configuración y manifiestos consumidos. |
| Job 16781 → checkpoint base | 16781 figura `COMPLETED`, `0:0`, y su envío declara como base `titan_v4_final_best.pt`. | `UNVERIFIED_EDGE`: la ruta de entrada fue enviada, pero no se recuperó evento de lectura. El archivo no está presente en esa ruta consultada. | Hash de entrada o log de apertura/consumo, script de batch y configuración efectiva. |
| Salida de 16781 → V3F publicado | El archivo físico publicado `backbone-v3f-original.pt` está verificado por SHA en CEDIA y coincide con el manifiesto del release. | `UNVERIFIED_EDGE`: identidad del release verificada; vínculo al job no. | SHA del output de 16781 y correspondencia byte por byte con el asset del release. |
| V3C/V3F → V3AG publicado | Metadata y recibos declaran una ruta parental V3C; ambos pesos publicados tienen identidad física verificada. | `UNVERIFIED_EDGE`: nombre de padre sin hash no establece igualdad ni descendencia exacta. | Checkpoint padre e hijo, digest de salida por job y registro autenticado de promoción. |

En la consulta puntual de CEDIA del 2026-11-10, los tres objetos esperados en la cadena (JSON trial 6, `titan_v4_final_best.pt` y `titan_v4_v3f_finetuned_best.pt`) no estaban presentes en las rutas exactas declaradas en los envíos. Esto no afirma que nunca existieran ni que no haya otra copia fuera de las fuentes consultadas.

## Manifiestos y pacientes

Los envíos de 16768 y 16781 conservan nombres de train/validation. El envío de 16768 declara una bandera explícita `train_val_overlap=0`; los batch scripts y los bytes de los CSV no fueron recuperados. Ese flag no reemplaza un cruce de pacientes ni verifica que los CSV nombrados fueran leídos. No se certifica aislamiento de pacientes ni ausencia de solapamiento de señales.

El asset `backbone-v3f-original.pt` tiene SHA-256 `ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8` y tamaño 233.565.900 bytes. El hash acredita el archivo publicado, no su job productor. P4/P6/P8 y el backbone V3AG se detallan en [la reconciliación de arquitectura](SPECIALIST_ARCHITECTURE_RECONCILIATION.md).

## Conclusión

Queda respaldado que el snapshot V3C registró trial 6 como ganador de `ranking_score`, trial 8 con el mayor `peak_composite_score`, que los jobs indicados terminaron con estado exitoso y que V3F/V3AG se publicaron como archivos identificables. **No queda demostrada la cadena completa** `study → trial 6 → JSON consumido → 16768 → checkpoint de 16768 → 16781 → backbone V3F`. No se atribuyen los pesos finales a trial 6 como hecho autenticado.

## Recibo de recuperacion dirigida 2

El recibo CEDIA incluido en la ronda 2 vuelve a registrar `COMPLETED 0:0` para 16748-16759, 16768 y 16781, y conserva SHA-256 de los registros de envio de 16768/16781. Tambien confirma que el envio referencia el JSON de trial 6 y la ruta del checkpoint base. No aporta stdout/stderr, digest de lectura, archivo JSON, checkpoint intermedio ni digest de salida. Los doce jobs 16748-16759 siguen sin equivaler a doce trials completos. Esta es corroboracion de metadatos de envio/estado, no una nueva arista verificada; el grafo actualizado esta en [`HISTORICAL_PROVENANCE_GRAPH.md`](HISTORICAL_PROVENANCE_GRAPH.md).
