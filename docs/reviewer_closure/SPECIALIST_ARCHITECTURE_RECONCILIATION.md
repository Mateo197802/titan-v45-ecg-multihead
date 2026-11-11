# Reconciliación de arquitectura y checkpoints

## Identidad física de los cinco pesos publicados

En CEDIA se verificaron los archivos físicos de la ruta autorizada del release; sus tamaños y SHA-256 coinciden con [`outputs/models/release_weight_manifest.json`](../../outputs/models/release_weight_manifest.json). El hash confirma identidad con el asset nombrado, **no** el job que lo creó.

| Asset | Bytes | SHA-256 | Resultado |
|---|---:|---|---|
| `backbone-v3f-original.pt` | 233.565.900 | `ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8` | Coincide con manifest y archivo CEDIA. |
| `backbone-v3ag-pathology.pt` | 233.566.092 | `bf71e4cf8acc34031cb3611c7031e0649822e705fd7dcea354a3ea583ce920ee` | Coincide con manifest y archivo CEDIA. |
| `specialists-v3p-e008-primary6-diagnostic.pt` | 22.354.966 | `9c5a9265a7155e1206c551cc4e6d645b86363ba3dbdeb7baf7b9f173c314be3d` | Coincide con manifest y archivo CEDIA. |
| `specialists-v3q-primary8-best-candidate.pt` | 29.498.326 | `b30cb2bbb45f1231c93ff1c196aa966b57b49831cadb296131c0283e7b0ceb02` | Coincide con manifest y archivo CEDIA. |
| `specialists-v3ag-primary4-calibrated.pt` | 29.413.606 | `cf5091e962fffb3254b1a71fe57236dd82ea0139093df192511499d931391dbc` | Coincide con manifest y archivo CEDIA. |

El recibo es [`CEDIA_RELEASE_CHECKPOINT_HASHES_2026-11-10.json`](receipts/CEDIA_RELEASE_CHECKPOINT_HASHES_2026-11-10.json). La recuperación del 10 de noviembre corrige una afirmación anterior demasiado amplia: los P6/P8 no aparecían en las rutas repo/cache inspeccionadas entonces; en esta pasada se encontraron bajo el almacén de modelos del checkout autorizado y se midieron directamente.

## Dimensiones observadas sin deserializar

Los cinco archivos son contenedores PyTorch ZIP. Se verificó SHA del archivo completo y se tokenizó el `data.pkl` con `pickletools.genops`; no se llamó a `torch.load`, no se ejecutó pickle, no se asignaron tensores y no se hizo inferencia. El recibo de formas registra SHA del metadata leído y los nombres/formas inspeccionados.

| Checkpoint / salida | Forma serializada | Lectura |
|---|---|---|
| V3F y V3AG, `head_rhythm.4.weight` | `[14, 512]` | 14 salidas globales de ritmo. |
| V3F y V3AG, `head_pathology.4.weight` | `[7, 512]` | 7 salidas globales de patología. |
| V3F y V3AG, cabezas restantes | calidad `[1,128]`; biometría `[3,256]`; ejes `[3,256]`, `[2,256]`, `[2,256]`, `[6,256]`, `[1,256]` en capas finales | Coincide con los contratos públicos de calidad, biometría y cinco ejes. |
| P6 y P8, por cada uno de 8 especialistas | `heads.i.1.weight=[512,681]`; `heads.i.4.weight=[512,512]`; `heads.i.7.weight=[1,512]` | 24 matrices de peso por perfil; ancho oculto almacenado 512. |
| P4, por cada uno de 4 especialistas | `heads.i.1.weight=[512,670]`; `heads.i.4.weight=[512,512]`; `heads.i.7.weight=[1,512]` | Entrada morfológica/features de ancho 670, ancho oculto almacenado 512 y una salida binaria por especialista. |

El campo serializado `rhythm_hidden_dim` de P6/P8 declara 192, mientras que las matrices almacenan ancho 512. El cargador congelado actual toma el ancho de `heads.0.1.weight.shape[0]`, marca la diferencia y construye el módulo con 512 antes de `load_state_dict(strict=True)`: [código](../../src/titan_v45/models/frozen_rhythm.py). Por eso el replay puede cargar las matrices; no resuelve por qué se guardó `192` ni qué constructor usó el job original. El entrenador recuperado que declara 512 no tiene un vínculo hash→job→checkpoint que pruebe ser el productor de estos pesos.

## Alcance funcional

El contrato global versionado declara entrada `[12,1250]` a 125 Hz, 58.352.219 parámetros en el backbone, 14 salidas globales de ritmo y 7 de patología. Los perfiles publicados operacionalizan subconjuntos: P6 seis ritmos, P8 ocho ritmos y P4 cuatro patologías. Ni un tensor global ni una puntuación auxiliar implican que esa clase se haya supervisado o validado.

No hay clase `Other` explícita en el contrato. ALMI, ILMI y LAE existen como salidas del contrato global; esta auditoría de formas no demuestra máscaras de pérdida, positivos/negativos de entrenamiento, rendimiento ni selección de esas salidas. El recibo comparativo de V3F/V3AG informa algunas filas auxiliares iguales y otras distintas; el estado de esas filas no se interpreta como evidencia de supervisión.

## Conclusión de procedencia

Quedan **verificados dentro de alcance** los hashes físicos de los cinco assets y las dimensiones descritas. No se verificó la producción histórica de los assets, los datos/etiquetas que actualizaron cada salida ni independencia por paciente. El desacuerdo `192/512` sigue siendo una inconsistencia de metadata de causa histórica desconocida; no se corrigieron los pesos ni el metadata.

## Aclaracion de la segunda recuperacion

El paquete dirigido 2 vuelve a referenciar, con los hashes ya registrados, el trainer `8e8d59889a0458c47a90f9735ff6ba017c7e1a79582d11529a608e1816e671fe` y el runtime `f5161ac848b9012c0d541fba49a1a061c8258cb10e32fde75341934f21c90af3`. No son nuevos bytes recuperados. El informe de la ronda distingue el default/metadata de 192, el constructor classwise explicito de 512 y una linea de reporte por epoca que corresponde a patologia; esto acota la lectura de los extractos, pero no identifica el codigo que escribio `rhythm_hidden_dim=192` en P6/P8. La causa del desacuerdo, el job productor y la supervision efectiva siguen sin probarse. No se cambia la conclusion de procedencia.
