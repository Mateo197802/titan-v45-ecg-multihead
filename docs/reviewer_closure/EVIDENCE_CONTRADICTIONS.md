# Contradicciones y autoridad de la evidencia

Los códigos se resuelven en [el ledger](MASTER_EVIDENCE_LEDGER.csv). Una conclusión definitiva sobre un archivo no equivale a una conclusión definitiva sobre una cohorte clínica.

| Comentario | Contradicción | Fuente de mayor autoridad y razón | Conclusión |
|---|---|---|---|
| R1-4 | Hashes placeholder frente a archivos reales; corrida completada frente a reproducción íntegra. | HASH: hash físico y tamaño cotejados con manifest; TRAIN/OPT: stdout, promoción y reporte contemporáneos, superiores a nombres o estados SLURM aislados. | Identidad de release y ejecución registradas, definitivas en ese alcance. Identidad intermedia, SQLite y semillas de reanudación pendientes. |
| R2-3a | Conteos documentados frente a disyunción por paciente. | TRAIN para ventanas; SPLIT para el algoritmo archivado y el cruce reconstruido; P4 para observaciones y SCP. | Los conteos se conservan. El cruce V3M es condicionado al ECG faltante y no es prueba global. |
| R2-3c/d | Salida auxiliar y métricas 41M frente a supervisión de los pesos publicados. | LOSS: parche contemporáneo, índices de pérdidas y log de V3F; resultados 41M acreditan sus propias ramas. | Alcance directo determinado en el código recuperado; soportes, máscaras y rendimiento auxiliar del release pendientes. NSR es normal. |
| R2-3e | Role de contrato frente a ruta por ECG. | AE: código y agregados con digest concordante; AFLOG: stdout auténtico. Ninguno es un ledger de intervención clínica. | Definición por contrato verificable; derivación clínica o revisión humana no demostradas. |
| R2-3f | Diez descriptores frente a loader exacto y replay. | MORPH/LOSS: fuente capturada y llamadas; REPLAY: residual contra tolerancia, no solo concordancia en clase final. | Proxies verificables; replay seleccionado 962/962 decisiones pero residual máximo 0,0006194115 > 1e-5. No se determina la causa completa ni el loader exacto. |
| R2-4e | Vacío o sustitución top-1 frente a abstención. | THRESH: flags retenidos P6 y reconstrucción P8, con denominadores distintos. | Conteos verificables para sus perfiles; no son abstenciones. |
| R2-4k | 210/2.105 AE frente a tasa; 23 handoffs AF frente a elegibles; Tablas 11/A7. | AE autentica pertenencia de referencia y estado manifest-only; AFLOG autentica alcance distinto; THRESH/P4 permiten contrastar las tablas con las predicciones congeladas. | AE no midió eficacia. P6: 97,44% de 1.563 implica 40 errores, no 21; P4: 776 aciertos de panel, no 772. No sostener tasas ni pre/post, sin afirmar que jamás existió otra política. |
| R1-3 / R2-5 | Etiqueta de ECG frente a incidencia AF o detección por latido. | AF verifica código de referencia, no historia clínica; PVC cuenta ventanas derivadas de anotaciones, no aciertos temporales. | Conservar ECG/ventanas en su alcance; no inferir desenlaces clínicos. |

P4: 80,23% es media no ponderada de cuatro accuracies binarias; 776/962 es un recuento agrupado distinto. Concordar con presencia de la clave SCP, incluidas claves de likelihood cero, no constituye adjudicación clínica.
