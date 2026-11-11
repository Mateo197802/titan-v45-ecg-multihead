# Cuarentena selectiva V4 de mayo: alcance y límites

**Dictamen:** se verificó un diagnóstico legado de TITAN V4 de mayo de 2026 sobre el subconjunto de errores de un reporte Primary-9 de 672 ECG. No es evidencia de una política de cuarentena V4.5 de junio.

## Recomputación independiente

Se leyó solo la matriz de confusión agregada 9×9, el reporte agregado y los totales del reporte de ruteo. El verificador [`recompute_legacy_v4_quarantine.py`](../../scripts/evaluation/recompute_legacy_v4_quarantine.py) recalcula matriz, diagonal, fuera de diagonal, accuracy, macro-F1 y la partición de acciones; no exporta ni procesa claves por ECG.

| Medida | Recalculado | Interpretación |
|---|---:|---|
| Población del reporte legado | 672 | Denominador del diagnóstico V4. |
| Diagonal de la matriz | 461 | Aciertos top-1 registrados. |
| Fuera de diagonal | 211 | Errores; subconjunto que alimenta el reporte de predicción selectiva. |
| Accuracy | 461/672 = 68,60 % | Coincide con el reporte. |
| Macro-F1 | 0,6811623 | Coincide con el reporte calculado desde la matriz. |
| Aceptados entre errores | 107/211 = 50,71 % | Cobertura **del subconjunto de errores**, no de los 672 ECG. |
| Frontera conocida entre errores | 53 | Acción algorítmica del diagnóstico. |
| Etiqueta `ood_real` entre errores | 51 | Etiqueta de la regla archivada, no adjudicación clínica. |
| Suma de acciones | 107+53+51 = 211 | Partición completa de errores; cero en los otros dos contadores de cuarentena. |

El 49,29 % restante es la fracción no aceptada dentro de esos 211 errores. La tasa global de cuarentena sobre los 672 **no se calculó**: los 461 casos correctos no pasaron por este ledger de ruteo. No se atribuye al 50,71 % una cobertura global ni una tasa de seguridad clínica.

## Identidad de estudio

El reporte padre se identifica como V4 / Primary-9, colección de diagnóstico de mayo (`2026-05-24`). Nombra un checkpoint V4 y un manifiesto externo, pero este paquete no aporta un digest del checkpoint ni autentica que el manifiesto local homónimo sea el archivo consumido por el job. El recibo de análisis de recuperación dice que las 211 claves, referencias y decisiones del ledger coinciden con los errores fuera de diagonal; el ledger individual permanece privado y no se publicó.

La evidencia respalda los totales agregados y su relación aritmética, no el código exacto/umbrales leídos por una ejecución histórica ni los resultados posteriores a la acción. `accepted_prediction` no corrige el error. `ood_real` no prueba OOD clínico, revisión humana ni una decisión médica.

## Separación de V4.5 junio

Para V4.5 no se recuperó score de incertidumbre por ECG, política congelada, umbral, población elegible anterior a la derivación, ledger pre/post, referencia compatible, job/checkpoint vinculado ni resultado de revisión humana. La tasa V4.5 sigue `NOT_ASSESSED`, no cero. Los conjuntos vacíos P6/P4 y los 58 fallbacks P8 son estados distintos y no se sustituyen por el diagnóstico V4.

**Efecto sobre revisores:** este hallazgo completa solo la verificación aritmética del análisis legado dentro de su alcance. R1-2 y R2-4k siguen parcialmente abordados/no satisfechos para la solicitud V4.5. La cuarentena V4.5 de junio no se puede declarar resuelta con este resultado.

El recibo saneado está en [`LEGACY_V4_QUARANTINE_RECOMPUTATION_2026-11-10.json`](receipts/LEGACY_V4_QUARANTINE_RECOMPUTATION_2026-11-10.json). La fuente agregada de confusión tiene SHA-256 `88246c9c82ae9684bae90b22ee96c168085ae11a4a1c79a328995769e41876e9`; el agregado de ruteo tiene SHA-256 `9a7d026c95e084c955321d9f8f613542201ad435c88f32d2b4ff551f0b94cf2f`. No se publica el recibo crudo que contiene rutas y referencias a identificadores.
