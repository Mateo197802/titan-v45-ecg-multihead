# TITAN V4.5 — Estado técnico de 12 comentarios (aclaraciones y alcance)

Fecha: 2026-11-12. Documento independiente del manuscrito. **No edita figuras, resultados históricos, pesos ni carta de respuesta.** Este registro es una conciliación de la evidencia disponible, no una decisión editorial ni una validación experimental nueva.

## Alcance y métrica

De los 15 comentarios y 40 subrequisitos de la auditoría, se trabajan **12 comentarios / 33 subrequisitos**: se excluyen de esta entrega R1-1 (generalización), R2-4a (terminología/evaluación externa) y R2-2b (figuras e introducción), que siguen una vía separada. **R2-general permanece incluido**: concierne a cobertura de clases/denominadores y no es sinónimo de generalización entre fuentes. R2-3f conserva su análisis técnico de morfología; la edición de diagramas queda fuera.

Puntuación de evidencia disponible según rúbrica preexistente: **global 20,5/40 = 51,25 %** y **alcance 12 comentarios 16,5/33 = 50,00 %**. Estos porcentajes NO representan exactitud de clasificadores, probabilidad de aceptación, porcentaje de cumplimiento editorial ni eficacia de una política clínica. Ninguna observación consta como aceptada por revisores; un texto explicativo potencialmente suficiente sigue sujeto a aprobación y a los cambios concretos que decidan los autores.

| Comentario | Puntos/criterios | Cobertura | Estado de evidencia | Decisión |
|---|---:|---:|---|---|
| R1-2, flujo completo | 1/3 | 33,33 % | Insuficiente para rendimiento de extremo a extremo | CONSERVAR métricas P6/P4 con denominador restringido; NO afirmar workflow clínico |
| R1-3, AF | 1,5/3 | 50,00 % | ECG-level sustentado; incidencia no demostrada | CONSERVAR clasificación de AF por trazado; LIMITAR diagnóstico incidental/longitudinal |
| R1-4, hashes/Optuna | 1/2 | 50,00 % | Integridad de archivos release y ejecución parcial documentadas | CONSERVAR hashes auténticos y linaje parcial; NO reproducibilidad completa |
| R2-general, Other | 1/2 | 50,00 % | Clases declaradas verificadas; rendimiento Other no | CONSERVAR alcance de P6/P8/P4; no inventar clase Other |
| R2-3a, datos/splits | 2/3 | 66,67 % | Conteos y exposiciones vinculados a jobs; aislamiento integral no | CONSERVAR números verificados y revelar límite de separación por paciente |
| R2-3c, ritmo auxiliar | 2,5/3 | 83,33 % | Contrato de salida y semántica de pérdidas sustentados | CONSERVAR explicación concreta de supervisión V3F, limitar etapas previas |
| R2-3d, patología auxiliar | 2,5/3 | 83,33 % | ALMI/ILMI/LAE declaradas; sin prueba de supervisión directa V3F | CONSERVAR alcance Pathology4 y separar experimentos 41M |
| R2-3e, Role | 1,5/3 | 50,00 % | Role definido como asignación de endpoint | CONSERVAR definición técnica, no atribuir derivación humana |
| R2-3f, morfología | 1/4 | 25,00 % | Diez proxies implementados; fidelidad de loader no cerrada | CONSERVAR documentación y experimentación posible; no declarar replay exacto |
| R2-4e, umbrales | 1,5/3 | 50,00 % | Top-1/fallback cuantificados en cohortes delimitadas | CONSERVAR cifras por perfil; no confundir con abstención |
| R2-4k, cuarentena | 0/2 | 0,00 % | Eficacia y tasa históricas no evaluadas | NO SOSTENER tasas pre/post o beneficio clínico; no afirmar que nunca existió |
| R2-5, PVC | 1/2 | 50,00 % | Etiqueta por ECG/ventana evaluada; detección por latido no | CONSERVAR clasificación de intervalos, no prometer localización de latidos |

### R1-2 — Qué falta para declarar flujo clínico completo

Las cifras P6 publicadas (95,19 % accuracy, 80,09 % macro-F1) corresponden a **un perfil seleccionado de seis clases**, no a todos los ECG de un servicio clínico. El estudio SPH posterior puntuó técnicamente 25.770 ECG con P6/P8/P4, pero no acredita en la misma cohorte un workflow completo con referencias compatibles para todas las clases y derivaciones reales.

Para evaluar el flujo se necesita una cohorte de **todos los registros elegibles** (previa a filtrar clases); ontología y ground truth válidos; soporte y prevalencia por clase; política de clasificación/abstención/cascada congelada; decisión por ECG y referencia; TP/FP/TN/FN por clase y por ruta, incluidas rutas retenidas/rechazadas; PPV/NPV en prevalencias originales y cálculo de intervalos apropiados. Si una política no existe, no se inventará. Un nuevo estudio no reconstruye retroactivamente el workflow de junio.

### R1-3 — AF: identificar un ritmo no equivale a establecer incidencia

El endpoint histórico reconoce una **etiqueta de AF asociada a un ECG de 10 segundos**. Una primera detección o AF incidente requiere línea temporal clínica y referencia longitudinal. La consistencia almacenada fue auditada: P6 1.643/1.643 y P8 2.193/2.193 flags/códigos reconciliados, 390 positivos AF en cada perfil solapado, una coocurrencia AF/NSR sin adjudicación. Son comparaciones con anotaciones/diagnósticos de referencia del ECG, no prueba de AF nueva ni de adjudicación uniforme por especialista. **La capacidad ECG-level sigue siendo un resultado legítimo, con sus límites de calidad y denominador.**

### R2-general — Cobertura de clases, no generalización geográfica

R1-1 pregunta por transferencia a fuentes/pacientes independientes. R2-general pregunta qué sucede al excluir NSR/PAC y patologías auxiliares y si hay un endpoint Other evaluado. Las salidas globales (14 de ritmo, 7 de patología) y especialistas P6/P8/P4 no implican un clasificador Other validado ni un denominador clínico completo. **NSR es normal, no una arritmia:** una agrupación solicitada por el revisor debe discutirse según ontología clínica, no adoptarse mecánicamente. Para afirmar rendimiento Other hace falta definición prespecificada, referencias compatibles, población completa y evaluación específica.

### R2-3a — Datos y particiones: hechos conservados

Job 16768 documenta 7.485 archivos enumerados, 9.945 ventanas, 9.021 train y 924 validation. V3C excluyó 390 filas por `record_base`, sin equivaler a paciente disjunto. V3M/V3AG interno registró 9.885 train y 1.132 validation por hash de registro; una reconstrucción condicionada por metadata encontró **206–207 pacientes compartidos entre train/validation** y **165–166 entre train/panel interno**, aun sin IDs de ECG comunes. **Esto NO prueba contaminación de fold 10** ni todos los experimentos. V3S P4: 962 observaciones ECG×etiqueta, 733 ECG y 676 pacientes; cuatro candidatos comparados en ese panel. Los manifiestos originales completos consumidos por los jobs y los cruces waveform-level permanecen sin certificar. No presentar cohortes de desarrollo como validación ciega final.

### R2-3c/d — Qué supervisó V3F

El código histórico de especialización V3F documenta pérdidas directas en **Primary8 (ritmo) y Pathology4 (ASMI, LVH, IMI, ISC_)**, sin términos directos de esa etapa para otras seis clases globales de ritmo ni ALMI, ILMI o LAE. La existencia de salidas/logits auxiliares NO demuestra supervisión eficaz ni rendimiento validado. Tampoco demuestra ausencia de entrenamiento en todas las etapas anteriores. Las métricas ALMI/ILMI/LAE en experimentos **41M/Plan Y/AJ** pertenecen a ramas separadas y no se atribuyen al P4 publicado. Las dos observaciones están al 83,33 % de **cobertura documental**, NO al 83,33 % de acierto clínico.

### R2-3e — Significado de Role

`Role` se define como **asignación de un endpoint dentro de un perfil o contrato de software** (primario, auxiliar o candidato a cascada, según versión). No acredita por sí solo que un ECG fue derivado, puesto en cuarentena o revisado por una persona. Mantener esta definición y separar reglas declaradas de transiciones observadas.

### R2-3f — Morfología: código recuperado, prueba de equivalencia pendiente

Se recuperó una implementación de **diez descriptores morfológicos/proxies**, incluida la evidencia de morfología suministrada a las ramas de ritmo y patología. Esto **NO es un experimento inexistente ni un 25 % de rendimiento**: el 25 % procede de 1/4 punto de cuatro comprobaciones de auditoría histórica. No se recuperó el loader exacto identificado por 36.271 bytes y SHA-256 `fc8d7367f9f2c108376839435021ec3172fe2757faa4a615f0ef5d39cbf1e855`. El replay estricto falla: P4 residual máximo de scores ≈0,0006194 frente a tolerancia 1e-5, y P6 tiene una discordancia top-1 de 1/1.643; P8 reconcilia 2.193/2.193.

**Se puede experimentar ahora**, pero hay que distinguir:
- **Auditoría de implementación**: verificar fórmulas, escalado, unidades, canales, máscara, NaN y contrato de entrada; recuperar versión exacta de loader si está disponible; repetir replay y explicar residuos.
- **Ablación nueva**: comparar, bajo protocolo congelado, especialistas con las diez features vs sin features, splits por paciente, calibración exclusivamente en desarrollo y test intacto; medir ΔF1, sensibilidad por clase, AUROC/AUPRC e IC95%. Si se ejecuta, será evidencia nueva y NO reproducción automática del entrenamiento de junio.
- **Cierre literal del revisor**: documentar cada una de las diez características y cómo se calcula; las figuras se tratan en otro flujo editorial.

### R2-4e — Umbrales: fallback no es cuarentena

En el conjunto seleccionado P6, 79/1.643 ECG tuvieron conjunto vacío sobre umbral y 64/79 tuvieron top-1 correcto. En P8, 58/2.193 tuvieron conjunto vacío y se empleó sustitución top-1, con 22/58 correctos. En P4, bajo umbral es decisión binaria negativa en cada panel. No se excluyen automáticamente de los denominadores. En SPH, otros denominadores/protocolo: P6 16.785 conjuntos vacíos, P4 8.343 y P8 801 fallbacks. No mezclar SPH con resultados de panel seleccionados.

### R2-4k — Qué sabemos de cuarentena y qué NO

El código y artefactos Plan AE reconstruidos con hashes históricos muestran **210/2.105 = 9,976 % de pertenencia de etiqueta de referencia a clases candidatas a cascada**, no de decisiones de rechazo, abstención o derivación efectuadas por el modelo. El informe se clasifica `QUARANTINE_MANIFEST_ONLY`. Las 23 filas Plan AF no sirven de denominador. En SPH, `quarantine_assessed_records=0` y `quarantine_rate=null`: **significa que NO SE EVALUÓ esa política**, no que se midió una tasa del 0 %; tampoco permite afirmar que no existió ninguna ejecución histórica en otra fuente. La eficacia pre/post no está demostrada.

Opciones honestas: (1) retirar las tasas y alegaciones de beneficio no verificadas manteniendo resultados principales restringidos, o (2) diseñar un estudio nuevo, con política congelada y decisiones por ECG para medir cobertura/riesgo/falsos negativos, documentándolo como **experimento posterior**, no como prueba del histórico.

### R2-5 — PVC: predice presencia por intervalo, no localiza latidos

P6 clasifica un **ECG/ventana de 10 s** para una categoría relacionada con PVC. La predicción expresa presencia de la **etiqueta ECG-level**, no instante/posición, número ni identificación individual de cada latido prematuro. El F1 por umbral en la evaluación seleccionada es ≈65,64 % (y top-1 ≈61,54 % en la comparación informada); es rendimiento moderado, no validación clínica de detección de latidos. Históricamente se derivaron 3.478 ventanas PVC de INCART y 2.169 de SVDB a partir de anotaciones de latidos, pero **ventanas etiquetadas no equivalen a latidos detectados por el modelo**. Puede ser útil como clasificador o cribado a nivel de registro, pero un detector/contador de PVC por latido requiere arquitectura, anotaciones temporales y evaluación propia.

## Estados recomendados para seguimiento (no equivalen a aceptación editorial)

- **Pregunta metodológica susceptible de respuesta delimitada**: R1-3, R1-4, R2-3c, R2-3d, R2-3e, R2-4e, R2-5.
- **Parcial por proveniencia/implementación**: R2-3a, R2-3f.
- **Sin resultado experimental exigido por la afirmación amplia**: R1-2, R2-general, R2-4k.

Un alto porcentaje en una rúbrica interna no impone mantener afirmaciones falsas; una puntuación baja no impide responder una pregunta de definiciones. Para revisión editorial futura, la carta debe distinguir `claim verified`, `claim limited` y `claim withdrawn`.

## Fuentes auditadas previamente y límites de esta publicación

- Matriz base de 15 observaciones/40 subrequisitos: `docs/reviewer_closure/REVIEWER_15_COVERAGE_AND_CEILING.json` en PR #3 (rama `codex/titan-v45-external-review`).
- Recuperaciones: `TITAN_V45_FINAL_EVIDENCE_20261111_SHAREABLE.zip`, `TITAN_V45_REVIEWER_PRIMARY_DELTA_SHAREABLE.zip`, `TITAN_V45_SCIENTIFIC_DELTA_VERIFIED_20261111_SHAREABLE.zip`, `TITAN_V45_SCIENTIFIC_PRIMARY_DELTA_SHAREABLE.zip`, archivos de CEDIA y el resumen de reconciliación al 2026-11-12.
- Hashes específicos y evidencia de ejecución permanecen en paquetes archivados y documentos de conciliación; **este archivo no transfiere datos clínicos ni vuelve a autenticar los originales in situ**.
- La nueva rama de documentación parte de `main`; puede no contener aún los registros nuevos de PR #3/#4. No confundir enlaces a evidencia en otras ramas con archivos fusionados a `main`.
