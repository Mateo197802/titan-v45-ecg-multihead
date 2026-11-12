# Cierre técnico documentado

- **Global:** 20,5/40 = 51,25%, 15 comentarios. **Activo:** 16,5/33 = 50,00%, 12 comentarios. Sin delta frente al punto de partida. R1-1, R2-4a y R2-2b se preservan sin reevaluar.
- **Evidencia suficiente para una respuesta acotada:** R1-3, R1-4, R2-3c, R2-3d, R2-3e, R2-3f, R2-4e y R2-5. R2-4k (0%) también admite una aclaración documentada de por qué se retiran las cifras; su afirmación experimental queda NO_DEMOSTRADO.
- **Parcial:** R2-3a (66,67%). Se conservan conteos originales y alcance P4; faltan el cruce fuente × clase × segmento × split y los manifiestos exactos.
- **Experimento necesario si se conserva la pretensión:** R1-2 (33,33%) y R2-general (50%). Hace falta una población completa con referencia, rutas y prevalencia, y una evaluación preespecificada de Other.
- **R2-3c/d (83,33% cada uno):** dos criterios completos y el tercero con 0,5 por semántica recuperada. Falta ligar soportes, máscaras y rendimiento auxiliar a la ejecución y checkpoint exactos; no falta una explicación del alcance directo de V3F.

## Hechos técnicos preservados

V3C registró semilla inicial 197802, nueve trials completos de doce registros y trials 10/11 PRUNED. Trial 6 fue promovido con ranking 0,6245117257. Job 16768 registró 50 épocas y best score 0,5984175972, P8 macro-F1 0,6948857468 y P4 macro-F1 0,5838061549 en su reporte interno, no métricas de los especialistas publicados. Los LR configurados inferidos del código (AdamW ≈3,25e-6, OneCycle máximo ≈4,88e-5) no son un schedule medido. Job 16781 registró 9.021/144 ventanas train/val de ritmo y 5.013/776 de patología; el checkpoint intermedio figura como entrada declarada, no como lectura autenticada por hash.

En 16768 las ventanas no nulas antes de dividir fueron: CPSC2018 3.394, CPSC2018 extra 45, Georgia 659, INCART 359, Ningbo 22, PTB-XL 5.420, PTB-XL Challenge2020 3, CPSC2018 extra 3AVB 29 y Ningbo 3AVB 14. Suman 9.945; no asignan conteos por clase o paciente. El panel interno V3M de 1.492 observaciones no es V3S de 962; el job 17296 comparó cuatro candidatos sobre el panel seleccionado. La disyunción de pacientes entre V3S seleccionado y folds 1–9 en la metadata oficial no borra el cruce reconstruido dentro de V3M.

Los diez proxies del extractor, en orden, son: FC mediana (60/mediana RR), CV RR, RMSSD, ancho QRS por extensión suprumbral alrededor del pico, P-a-R por deflexión previa máxima, potencia relativa de 5–18 Hz, 0–0,7 Hz y 35 Hz–Nyquist, correlación absoluta media entre derivaciones válidas, y diferencia normalizada de potencia 5–18 Hz I/aVF. La normalización divide por 220, 1, 500, 220, 320, 1, 1, 1, 1 y 1; recorta a [0,1] excepto asimetría [-1,1] y sustituye no finitos por cero. No valida intervalos clínicos. La supervisión V3F recuperada no se generaliza al entrenamiento anterior del backbone.

## Privacidad y verificación

El [ledger](MASTER_EVIDENCE_LEDGER.csv) usa una fila por SHA-256, agrupa apariciones y enlaza evidencia pública a commits concretos. Fuentes restringidas, predicciones por ECG, señales, logs operativos y pesos permanecen en sus orígenes autorizados. Un miembro reconstruido o redactado no se convierte en original por estar en un ZIP. V4 legacy, 41M, V3C/V3F, P6/P8/P4, AE/AF y SPH son linajes distintos; Stage A no sustituye resultados históricos.

Ejecutar desde la raíz: **python docs/reproducibility/verify_reviewer_evidence_reconciliation.py**. La opción **--git-refs** comprueba los blobs públicos anclados a commits locales. La matriz [global](REVIEWER_15_FULL_STATUS.csv), [activa](REVIEWER_12_ACTIVE_STATUS.md), [40 criterios](REVIEWER_40_VERIFIED_SCORE.json), [decisiones](CLAIM_KEEP_LIMIT_WITHDRAW.csv) y [contradicciones](EVIDENCE_CONTRADICTIONS.md) no registran aceptación editorial. Esta rama no modifica manuscrito, figuras, carta ni entrenamiento.
