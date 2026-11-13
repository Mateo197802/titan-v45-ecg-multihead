# Actualización de calibración, cohortes y duplicados

Esta actualización distingue calibración interna, evaluación de paneles seleccionados y transferencia SPH. Ninguna cifra se usa para recalibrar ni reemplaza la métrica canónica del release.

## P4: calibración interna frente a evaluación seleccionada

El checkpoint P4 serializa cuatro umbrales que el recibo vincula al job 17296 (`v3ag_p4cal_r1`, `COMPLETED`, `0:0`). El recibo suma 1.492 **observaciones ventana-panel**, no ECG ni pacientes únicos; los archivos de los paneles mencionados por el job no se recuperaron con bytes verificables.

| Panel | Umbral serializado | Ventanas de calibración | Accuracy interna | F1 interna | ¿accuracy ≥0,90? |
|---|---:|---:|---:|---:|---|
| ASMI | 0,670 | 432 | 0,7940 | 0,7813 | No |
| LVH | 0,705 | 374 | 0,7487 | 0,7513 | No |
| IMI | 0,635 | 492 | 0,7927 | 0,8075 | No |
| ISC_ | 0,595 | 194 | 0,8814 | 0,8856 | No |
| **Total / media de cuatro paneles** | — | **1.492** | **0,8042** | **0,8064** | **0 de 4** |

El grid guardado fue 0,05–0,95 con 181 pasos, criterio conjunto de accuracy 0,90 y F1 mínimo 0,70. El resumen de calibration no es el resultado reportado de P4 sobre los 962 panel-observations. No se debe mezclar ni usar como sustituto.

## P4: evaluación conservada de paneles

La reconciliación de predicciones guardadas arroja:

| Endpoint | Panel-observations | ECG en la unión | Accuracy | F1 |
|---|---:|---:|---:|---:|
| ASMI | 294 | — | 0,8333 | 0,8123 |
| LVH | 224 | — | 0,6741 | 0,6573 |
| IMI | 206 | — | 0,7816 | 0,7887 |
| ISC_ | 238 | — | 0,9202 | 0,9156 |
| **Total de observaciones / unión** | **962** | **733 ECG / 676 pacientes** | **media 0,8023** | **media 0,7935** |

Los paneles no son 962 ECG distintos; hay endpoints repetidos por diseño. El agregado de cuatro accuracies da 80,2290 % y el promedio de F1 por panel da 79,3456 %, coherente con 80,23 % y 79,35 % previamente reportados. Son decisiones archivadas, no estimaciones nuevas ni prueba de aislamiento de los pacientes usados para entrenar o calibrar.

## P6/P8: política operativa de umbrales

El metadata del release registra umbrales nativos, pero la salida operacional P6 conservada usa seis overrides: AFIB 0,82; SB 0,835; STACH 0,775; RBBB 0,515; 1AVB 0,57; PVC 0,43. El recibo indica 9.858 flags guardados que coinciden con la regla congelada y 169 que cambiarían aplicando umbrales nativos; estos son estados del artefacto analizado, no pacientes independientes.

P8 no tiene overrides frente a sus umbrales guardados. Sus 2.193 conjuntos predichos coinciden con la regla congelada y 58 casos usaron fallback top-1 después de conjunto vacío. El fallback no equivale a `Other`, abstención, cuarentena ni revisión humana.

## Cohortes, folds y duplicados

| Rama | Unidades conservadas | Alcance verificado | No demostrado |
|---|---|---|---|
| P6/V3H | 1.643 ECG; todos dentro de los 2.193 registros P8 | P6/P8 comparados en los 1.643 comunes. | V3H fue expuesto a selección/gating; no es test independiente. Falta población parental anterior a balanceo. |
| P8/V3H | 2.193 ECG | Snapshot de nueve trials y gate/recibos identificados en docs existentes. | El snapshot completo de selección y la independencia del preentrenamiento no están certificados. |
| P4/V3S | 962 panel-observations, unión de 733 ECG y 676 pacientes | Los metadatos nominales de PTB-XL no muestran intersección de pacientes entre folds 1–9 y 10. | No se autenticaron los manifests exactos leídos por cada job ni el parent/exclusion ledger V3S. Un fold nominal no prueba qué consumió el job. |
| SPH | 25.770 ECG, 24.666 pacientes, 14 endpoints compatibles | Agregado del job 32669 idéntico byte por byte al fijado en Git; no hubo inferencia nueva en esta integración. | SPH ya había sido consultado; no certifica independencia histórica total ni cubre toda la taxonomía. |

El ZIP trae un recibo de auditoría de firmas exactas de los archivos de desarrollo: un grupo duplicado de dos señales entre 2.193 registros de ritmo y ninguno en la unión de 733 P4; no reporta grupos que crucen etiquetas de fuente. Ese análisis es una **verificación derivada recibida**, no se repitió aquí porque el ZIP de esta tarea no contiene las señales originales. Según su análisis de sensibilidad, retirar el único grupo cambia P6 de 95,1917 % a 95,1859 % y P8 de 90,6065 % a 90,5979 %. Estos porcentajes describen decisiones de desarrollo y no convierten la cohorte en test.

El control SPH citado por el paquete tampoco halló firmas completas coincidentes con los 2.193 registros de ritmo y 733 de P4, pero no cubre la población histórica de entrenamiento no recuperada, segmentos, remuestreo ni duplicados aproximados. No se afirma independencia de pacientes.

## Disposición

Los valores de 1.492 ventanas, 962 panel-observations y 733 ECG son unidades distintas. Los únicos artefactos que cambiarían la conclusión sobre separación histórica son los manifests realmente consumidos, sus grupos de paciente, exclusiones y el vínculo autenticado job→checkpoint. Esta actualización no cambia las cifras canónicas, no cambia el estado de evaluación externa y no edita el manuscrito.
