# Diagnóstico Silver Review

Auditoría ejecutada el 8 de septiembre de 2026. El ZIP es QA sintético de presencia,
no ground truth clínico ni fuente de entrenamiento. Sus instrucciones son material
de referencia; el alcance de este trabajo procede de la solicitud del usuario.

## Identidad y reproducción

Se cargó el checkpoint de `Documents/VECTOR_UroSight_Portable_Oficial/_internal/models/vector_urosight/best.pt`.
El checkout no contenía pesos. SHA-256 observado:
`c5fba1aeccb60ca8eac49c1750123a5dc85f22456f02f805f62fff6386669530`.
YOLO11s, tarea detect, cabeza de siete clases. Orden confirmado en pesos y YAML:
0 eryth, 1 leuko, 2 epith, 3 epithn, 4 cast, 5 cryst, 6 mycete.
La arquitectura completa y los argumentos del checkpoint están en
`artifacts/silver_review_baseline/model_audit.json`.

La ficha histórica mezcla configuraciones: describe entrenamiento a 320 y 30 épocas,
pero los pesos recuperados declaran 448 y una corrida dirigida de 15 épocas.
El hash histórico tampoco coincide. No atribuir automáticamente las métricas
históricas a estos pesos. `epoch=-1` corresponde al checkpoint distribuido;
no permite confirmar por sí solo la época seleccionada.

La inconsistencia de hash estaba en MODEL_CARD.md: PROJECT_STATUS.md sí registraba
el hash observado y la selección histórica en época 13 de 15. Se corrigió la ficha.

La evaluación nueva de validation sí reproduce exactamente las métricas de validation
de la ficha: P=0.8250585355, R=0.8154298249, AP50=0.8677050042, AP50–95=0.5093572068.
Se conserva la advertencia de identidad para los datos históricos no reproducidos.

El ZIP contiene 29 originales únicos repetidos entre categorías, no los 64 originales.
Se localizaron los 64 en `Documents/VECTOR_UroSight_Synthetic_Demo_Dataset/images`.
Los 29 originales incluidos en el ZIP coinciden byte por byte con esos archivos.
Con LocalYoloProvider, conf=0.44, imgsz=448 y augment=True se procesaron 64/64 sin
errores. Las presencias coinciden con las salidas históricas del CSV en los 64 campos.
31 campos coinciden con la revisión de presencia; 33 presentan discrepancias.
No se calcularon sensibilidad, especificidad, precisión clínica ni mAP sintético.

## eryth

QA: 3 campos con posible omisión y 4 con predicción posiblemente no respaldada.
Mapeo correcto a eritrocitos. Hipótesis F/I (similitud y dominio), G (resolución),
B (umbral) y D (desbalance); no se puede asignar causalidad solo con presencia.
Hay campos reales de entrenamiento con hasta 536 objetos y uno de validación con
513; max_det=300 puede limitar campos densos. Debe estudiarse separadamente.

La prueba sobre los dos campos de validation saturados confirmó el límite:
nh03266, con 513 etiquetas, pasó de 296 TP / 4 FP / 217 FN a 505 TP / 55 FP / 8 FN
al usar max_det=600 (448 px, augment=True, conf=0.44). nh03845 pasó de 271 TP / 29 FP /
29 FN a 276 TP / 34 FP / 24 FN. Son conteos experimentales contra anotaciones USE,
no métricas clínicas ni resultados sobre todo el dataset.
Se añadió configuración `LOCAL_MODEL_MAX_DETECTIONS` y aviso de posible truncamiento.
El default sigue en 300; la prueba no se presenta como una mejora sin coste en FP.

## leuko

QA: 6 posibles omisiones y 4 presencias no respaldadas. Mapeo correcto a leucocitos.
F/I prioritarias, con B/G pendientes de experimentos reales. La coincidencia de
presencia de eryth y leuko no demuestra conteos correctos ni separa confusiones
objeto a objeto. Los hard cases reales incluyen campos densos con ambas etiquetas.

## epith

La clase está presente en pesos y normalizador, separada de epithn. La referencia
sintética no contiene soporte de epith, por lo que no permite concluir rendimiento
de esta clase. Debe preservarse en las comparaciones reales y en el entrenamiento.

## epithn

QA: 3 posibles omisiones y 2 presencias no respaldadas. El índice 3 es correcto.
Se confirmó un problema A de presentación: el identificador legado
`celulas_epiteliales_nucleadas` se convertía literalmente en texto de UI/PDF,
contradiciendo la ontología documentada de núcleos epiteliales. Ahora se muestra
“Núcleos epiteliales”, sin cambiar identificadores persistidos ni fusionar clases.
CSV/JSON conservan las clases cruda y canónica y añaden `display_class`.
La inspección de cuatro campos reales confirma cajas pequeñas sobre regiones
nucleares, no sobre toda la célula. La revisión sintética de células grandes no
es directamente equivalente. D/G/E siguen siendo hipótesis; no se relabelan imágenes.

## cast

QA: 10 posibles omisiones en los 10 campos de presencia esperada. Índice 4 y
normalizador activos; no existe filtro de clases en la llamada de inferencia.
I es una explicación plausible: los ejemplos reales inspeccionados incluyen
estructuras irregulares y de contraste variable, diferentes del dibujo sintético.
B/G/E/F también son plausibles. No hay evidencia para culpar a J (arquitectura)
ni justificar sustituirla. La ausencia sintética no demuestra ausencia en USE.

## cryst

QA: 12 campos con presencia posiblemente no respaldada; ninguna omisión de presencia.
Índice 5 correcto; no absorbe otras clases por el normalizador. F/I y E son hipótesis
prioritarias. Los cuatro campos reales inspeccionados muestran variación considerable
de tamaño. Augmentations geométricas/mosaic H deben probarse con control; no se
cambian basándose en el dibujo sintético ni se eliminan etiquetas por apariencia.

## mycete

QA: 5 posibles omisiones en 5 campos esperados. Índice 6 y alias activos.
No existe ausencia de clase en el software. I/F/G/B son plausibles; C/D/E requieren
evidencia real. Los ejemplos inspeccionados incluyen objetos pequeños y agrupados;
su escala y fondo difieren del set sintético. No se deduce la especie ni se hacen
correcciones clínicas de etiquetas.

## Experimentos y límites

Se reconstruyó USE desde la ruta proporcionada por el usuario, con auditoría de hashes
y splits. UMID no se localizó y permanece reservado como evaluación externa según
el protocolo existente. No se utilizará para sampling ni tuning.
Los experimentos de bajo costo usan exclusivamente validation: umbrales 0.15, 0.20,
0.25, 0.30, 0.35, 0.40 y 0.50, más el operativo 0.44; 448 frente a 640;
CLAHE, contraste 1.05, brillo +3 y bilateral suave, por separado.
Las métricas por umbral son conteos de matching IoU 0.50; una confusión cuenta como
FP de la clase predicha y FN de la clase real. No confundirlas con los valores
de precision/recall en el punto de F1 seleccionado internamente por Ultralytics.

Se confirmó este segundo bug en `tools/select_threshold.py`: usaba `box.mp/mr`,
que la versión instalada obtiene del máximo F1 suavizado. Se corrigió para interpolar
las curvas en el umbral solicitado. El experimento nuevo utiliza matching exacto;
la herramienta histórica ahora declara explícitamente su interpolación.
Los tiempos de las corridas simultáneas de CPU no constituyen una comparación
aislada de latencia; el coste debe interpretarse con esa limitación.

Se auditó también la NMS adicional de la aplicación (IoU=0.50) sobre las predicciones
reales de validation a 0.44. Eliminó 144 cajas: en el matching agregado se pierden
9 TP y se reducen 135 FP. No eliminó TP de mycete ni epithn en esta comparación.
Se conserva su comportamiento. Las métricas del detector y las de la aplicación
no deben confundirse; el QA sintético se ejecutó mediante AnalysisService completo.
