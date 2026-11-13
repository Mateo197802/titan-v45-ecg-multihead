# Objetivo Optuna y límites de linaje

## Fuente V3C/V3F recuperada

La copia de `TRAINING/optuna_search_hpc.py` del archivo de fuentes CEDIA tiene 63.398 bytes y SHA-256 `dbfeea1d46f93f23297a74194ecd9e06d72e78f8163bdaab8db9767c2de0715c`. Es una copia histórica cuyo contenido coincide con el registro de exportación. No está vinculada por digest de consumo a los jobs V3C 16748–16759 ni a las generaciones 41M de mayo.

En esa implementación, la puntuación base es:

```text
0.60 * macro-F1(Primary-8) + 0.40 * macro-F1(Pathology-4)
```

Puede modificarse por un peso opcional del F1 de ritmos activos, una penalización de piso y una mezcla con F1 de ejes clínicos; resta 0,05 por cada clase primaria de ritmo o etiqueta de patología ausente. La copia declara por CLI peso de ritmos activos 0,0 y peso de ejes clínicos 0,08 por defecto. El ranking estable usa la media de las últimas tres puntuaciones menos 0,25 veces la desviación estándar poblacional. La semilla base CLI es 42 y el sampler TPE se parametriza desde la semilla y el número de trials persistidos. Son semántica/defaults de esta copia, no argumentos o estado comprobados de los jobs históricos.

La misma fuente utiliza una ruta multihead de 14 logits de ritmo y 7 de patología durante el entrenamiento de búsqueda. El contrato define 4 patologías primarias más ALMI/ILMI/LAE. Esto muestra una ruta implementada para esos targets cuando están presentes en los mapas de etiquetas, pero no vincula la fuente, los mapas, las pérdidas efectivas ni un trial con un checkpoint liberado.

## V3C trial 6

La tabla histórica versionada en el repo conserva nueve trials: trial 6 es el mayor `ranking_score` (0,6245117257), mientras trial 8 tiene el mayor `peak_composite_score` (0,6509403856). El resultado no se recalculó ni se encontró una SQLite nueva. Doce jobs Slurm completados no equivalen a doce trials completos.

La referencia `parent_checkpoint` de los metadatos estáticos de V3F y V3AG coincide con la ruta de checkpoint que job 16781 declara como entrada; esa concordancia hace más plausible la relación con el padre declarado por 16768. Es una coincidencia de referencia/ruta. No se recuperó el JSON exacto de trial 6, `titan_v4_final_best.pt`, la salida `titan_v4_v3f_finetuned_best.pt`, stdout/stderr, digest de lectura/escritura ni manifiestos consumidos. El peso publicado V3F conserva su hash verificable, pero su producción por 16781 sigue sin autenticarse.

## Optuna 41M de mayo: separación obligatoria

PR #4 conserva dos generaciones observadas en registros parciales: job 13172 (un trial 1 con estado COMPLETE en el recibo parcial, aunque el job falló) y job 13181 (trial 0 en otra generación, job fallido). Los jobs 13169, 13172 y 13181 constan fallidos; 13173/13182 y 13220–13222 constan cancelados sin inicio. Jobs posteriores 13239 y 13304 se interrumpen y no representan trials finales completos. Las bases SQLite y los sidecars siguen sin bytes recuperados.

El recibo de PR #4 transcribe de una fuente capturada una fórmula distinta de cuatro términos: 0,45 P9 + 0,35 P5 + 0,10 R14 + 0,10 Path7, con penalizaciones por etiquetas ausentes. La copia CEDIA recuperada en REV6 documenta otra implementación: 0,60 P8 + 0,40 P4 más modificadores. Como no hay hash de la fuente ejecutada por job, los argumentos ni la SQLite, **no es posible resolver cuál fórmula se ejecutó en cada job de mayo**. Se conservan ambas fuentes y no se combinan como una misma generación o estudio. El addendum de la fórmula 60/40 se entrega en PR #4, sin modificar sus observaciones anteriores.

**Conclusión:** existe evidencia verificable de una implementación objetivo 60/40 y evidencia parcial distinta de resultados de mayo. No se ha recuperado una base de trials completa, ni un ganador autenticado, ni una cadena trial→checkpoint. No declarar Optuna 41M recuperado.
