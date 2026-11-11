# Cobertura y techo de los 15 comentarios técnicos

**Corte:** 2026-11-11, posterior a REV3–REV6. La escala es la existente en `REVIEWER_15_EVIDENCE_UPDATE.json`: requisito verificado en alcance = 1; evidencia parcial/indirecta = 0,5; requisito ausente, no evaluado o fallido = 0. El denominador permanece en 40 subrequisitos ya definidos. Cobertura no equivale a satisfacción del revisor ni probabilidad de aceptación.

Se agregaron dos estados parciales de igual peso (0,5): `STATIC_SOURCE_SEMANTICS_VERIFIED_NOT_JOB_LINKED` y `STATIC_SOURCE_MISMATCH_MECHANISM_VERIFIED_NOT_JOB_LINKED`. Describen semántica/mecanismo de copias de código autenticadas frente al recibo, no el código que ejecutó un job concreto. Solo afectan los subrequisitos técnicos R2-3c y R2-3d; no cambian el estado global ni satisfacción de esos comentarios. Los deltas se calculan con las fracciones exactas (`0,5/3 × 100 = 16,666…`) y se redondean a una cifra; por eso el delta mostrado es +16,7 pp aunque la resta de los porcentajes ya redondeados (83,3 − 66,7) dé 16,6.

La cobertura agregada pasa de **18,5/40 = 46,25 %** a **19,5/40 = 48,75 %** (+2,5 puntos porcentuales). No se satisface plenamente ningún comentario: **0 satisfechos, 12 parcialmente atendidos, 3 no satisfechos**. El techo documental global no tiene porcentaje calculable, porque el conjunto de todos los respaldos posibles no es enumerable. “Techo histórico” en la tabla es cualitativo y limitado a las fuentes inspeccionadas.

| Comentario | Antes | Después | Cambio | Estado científico | Techo histórico dentro de fuentes consultadas | Para 100 % / próximo requisito |
|---|---:|---:|---:|---|---|---|
| R1-1 | 50,0 % | 50,0 % | 0,0 pp | Parcial | Falta vínculo de fuentes/manifiestos a pacientes y checkpoints | Recuperar manifiestos consumidos y demostrar independencia; validación intacta sería nuevo experimento |
| R1-2 | 33,3 % | 33,3 % | 0,0 pp | Parcial | Población padre/ledger posiblemente dependen del custodio | Población elegible, exclusiones y transiciones pre/post auténticas |
| R1-3 | 50,0 % | 50,0 % | 0,0 pp | Parcial | No puede derivarse de salidas del modelo | Referencia clínica/temporal para AF incidente o restringir la afirmación a la señal ECG |
| R1-4 | 25,0 % | 25,0 % | 0,0 pp | Parcial | A10 corregido; DB/historial solo si existe copia custodiada | SQLite y sidecars originales, historial completo y trial→checkpoint autenticado |
| R2-general | 50,0 % | 50,0 % | 0,0 pp | No satisfecho | Cobertura histórica de clases no completa | Ontología compatible y evaluación all-class nueva si se conserva `Other` |
| R2-2b | 50,0 % | 50,0 % | 0,0 pp | Parcial | Evidencia de creador/permiso puede requerir autores | Confirmar autoría, licencia y si la figura representa un proceso ejecutado |
| R2-3a | 50,0 % | 50,0 % | 0,0 pp | Parcial | Manifiestos exactos y mapas dependen del custodio | Train/val/calibration/selection por job, pacientes y señales cotejados en CEDIA |
| R2-3c | 66,7 % | 83,3 % | +16,7 pp | Parcial | Semántica de fuentes recuperada; enlace de ejecución faltante | Supports, masks, manifiestos, job y métricas por clase vinculados al checkpoint |
| R2-3d | 66,7 % | 83,3 % | +16,7 pp | No satisfecho | Hay ruta de entrenamiento de 7 patologías en código, no ejecución autenticada | Supports y rendimiento ALMI/ILMI/LAE ligados al checkpoint, o retirar claims de rendimiento |
| R2-3e | 50,0 % | 50,0 % | 0,0 pp | Parcial | No se encontró ledger de rol histórico | Política real y transiciones/acciones de revisión, o definición editorial acotada |
| R2-3f | 25,0 % | 25,0 % | 0,0 pp | Parcial | Mecanismo de metadato 192/512 posible; loader original sigue ausente | Loader exacto más vínculo de importación y replay dentro de `1e-5` |
| R2-4a | 75,0 % | 75,0 % | 0,0 pp | Parcial | Uso/desarrollo histórico incompleto | Separar transferencia de SPH de validación independiente y clínica |
| R2-4e | 50,0 % | 50,0 % | 0,0 pp | Parcial | Ruteo histórico completo no recuperado | Política por ECG, fallback, cuarentena y población completa sin etiquetas en ruteo |
| R2-4k | 0,0 % | 0,0 % | 0,0 pp | No satisfecho | Ledger/política solo recuperables si los conserva custodio | Denominador, incertidumbre, política, checkpoint, referencias y transiciones pre/post |
| R2-5 | 50,0 % | 50,0 % | 0,0 pp | Parcial | No hay anotación temporal/por latido en la evidencia recuperada | Limitar a ECG-record o ejecutar estudio separado con referencia por latido |

## Límites de interpretación

- El aumento de R2-3c/d es semántico y parcial: en una rutina la búsqueda multihead produce vectores de 14/7 objetivos y puede aplicar pérdida a siete salidas patológicas; otra rutina de fine-tuning selecciona Primary-8/Pathology-4. No prueba qué rama se ejecutó para un peso publicado.
- R2-3f no sube: el código tiene una rama que construye ancho 512 y escribe metadato 192, pero no se vinculó esa rama al checkpoint. El hash del loader `fc8d...` sigue ausente, y P4 conserva diferencia máxima `0.0006194115` frente a tolerancia `1e-5`.
- V3H sigue siendo una población seleccionada/balanceada; SPH ya fue examinada y no es prueba confirmatoria intacta. Independencia histórica por paciente no certificada.
- No se asignan porcentajes a “porción del máximo recuperable” o “porción del universo documental”: la primera depende de qué artefactos aún guarde el custodio, la segunda no se puede enumerar.

El detalle machine-readable con límites y acciones por ID está en [REVIEWER_15_COVERAGE_AND_CEILING.json](REVIEWER_15_COVERAGE_AND_CEILING.json). La matriz rectora de 48 observaciones se mantiene separada: 36 comentarios de revisores y 12 auditorías internas.
