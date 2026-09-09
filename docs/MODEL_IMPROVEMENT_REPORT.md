# Informe del ciclo de mejora — VECTOR UroSight

Fecha: 2026-09-08. **Decisión: conservar el modelo operativo.** El candidato no se promovió porque su AP50–95 cayó globalmente y en cast, mycete y epithn en validation real. TEST no se abrió en este ciclo. El ciclo comprende correcciones de software, auditoría de datos y evaluación de un piloto dirigido.


## Diagnóstico inicial

 Los pesos recuperados son YOLO11s con siete clases. Los fallos sintéticos se reproducen, pero no demuestran ausencia de cast/mycete en datos reales. Hay problemas distintos de dominio visual, escala, umbral, límites de detección y presentación. Véase [diagnóstico por clase](SILVER_REVIEW_DIAGNOSIS.md).


## Bugs de mapping encontrados

 No hay intercambio de índices ni desactivación de cast/mycete. Sí había una etiqueta de presentación incorrecta para epithn: ahora se muestra “Núcleos epiteliales”. Se conserva el identificador canónico legado para compatibilidad. Filtros y revisión separan texto visible de ID; las correcciones escritas como alias también se normalizan. CSV/JSON conservan clases originales y canónicas y añaden `display_class` (al final del CSV).


## Problemas por clase

 cast y mycete siguen omitidos en los patrones sintéticos. epithn requiere distinguir núcleo de célula completa. eryth/leuko sufren campos densos y límites de salida; cryst presenta predicciones sintéticas posiblemente no respaldadas. epith no tiene soporte de presencia en el Silver Pack, por lo que no se extraen conclusiones sintéticas sobre esa clase. Todas las clases aparecen en la evaluación real, incluidas las que empeoran.


## Mejoras de corto plazo aplicadas

 Se corrigió la presentación de epithn, la exportación tras revisión humana, el uso incorrecto de precision/recall de máximo F1 en la herramienta histórica de thresholds y la ausencia de aviso de saturación. `LOCAL_MODEL_MAX_DETECTIONS` permite experimentos explícitos; conserva default 300. Se mantienen 448 px, augment=True, threshold=0.44 y preprocesamiento original.

Se evaluaron 0.15, 0.20, 0.25, 0.30, 0.35, 0.40 y 0.50, además de 0.44, exclusivamente en validation. Se hicieron seis pasadas de 848 imágenes; los ocho umbrales se aplicaron a las predicciones guardadas. El F1 macro es la media del F1 de las siete clases, con matching IoU 0.50; no es una métrica clínica.

| Variante | F1 macro a 0.44 | Mejor umbral probado por F1 macro | F1 macro en ese umbral |
|---|---:|---:|---:|
| original448 | 0.812067 | 0.5 | 0.816165 |
| original640 | 0.807337 | 0.5 | 0.819338 |
| clahe | 0.733937 | 0.4 | 0.736890 |
| contrast | 0.810987 | 0.5 | 0.812072 |
| brightness | 0.812169 | 0.5 | 0.816301 |
| denoise | 0.810017 | 0.5 | 0.810682 |


La mejora de brillo es mínima y no justifica activarlo. CLAHE perjudica claramente el rendimiento; contraste y reducción de ruido tampoco mejoran el F1 macro a 0.44. A 640 px sube recall de cast/mycete, con pérdidas de precision. Maximizar solo F1 macro a 0.50 penaliza objetivos por clase. Los umbrales exploratorios por clase a 448 son eryth 0.50, leuko 0.44, epith 0.50, epithn 0.50, cast 0.44, cryst 0.40 y mycete 0.44; no se activaron automáticamente.

En dos campos saturados se probó max_det=600. En nh03266 (513 etiquetas), TP/FP/FN pasaron de 296/4/217 a 505/55/8; en nh03845 (300 etiquetas), de 271/29/29 a 276/34/24. La prueba es acotada a esos campos y no demuestra mejora clínica. La NMS adicional de la aplicación, evaluada aparte en validation, elimina 144 cajas: reduce 135 FP y pierde 9 TP. Se conserva.


## Hard cases reales seleccionados

 20 campos por grupo (cast, mycete, epithn, eryth_leuko y cryst): 100 selecciones de grupo y 99 imágenes únicas. El manifiesto contiene 7,609 objetos objetivo y conserva imagen original, dataset, XML, bbox, split, motivo y hashes. Todos proceden de train. Son candidatos de revisión, no errores clínicos certificados. Se inspeccionaron visualmente 16 paneles de las cuatro clases débiles. [Auditoría de anotaciones](HARD_CASE_ANNOTATION_AUDIT.md).


## Cambios de dataset

 USE se reconstruyó desde la fuente original disponible, sin editar originales. Derivado: 5,293 imágenes (4,177 train / 848 val / 268 test), 41,697 objetos, 83 exclusiones por duplicación y 12 recortes de cajas registrados. Las 268 etiquetas de test coinciden con el derivado previo recuperado. No se hicieron correcciones clínicas de clases. UMID no estaba disponible en la ruta indicada y no se utilizó para tuning.


## Estrategia de balance

 El intento inicial se abortó antes de completar una época al detectar sobrerrepresentación de eryth causada por repetir campos densos. El piloto corregido une una muestra de 700 campos con seed 42 a 79 campos de los otros cuatro grupos: 767 imágenes únicas, 846 exposiciones, máximo dos por campo. Objetos por exposición: eryth 3,977; leuko 1,018; epith 845; epithn 142; cast 574; cryst 317; mycete 571. La lista exacta y sus hashes están en `artifacts/targeted_pilot_balanced/training_manifest.json`.


## Augmentations utilizadas

 Rotación ±5°, escala ±0.1, traslación 0.03, brillo HSV 0.1, flips horizontal/vertical 0.5; sin mosaic, mixup, shear ni perspective. El piloto utiliza datos reales y conserva todas las clases de cada imagen. No se entrenó con el Silver Pack.


## Corridas realizadas

 `artifacts/run_baseline`: evaluación homogénea del modelo operativo. `artifacts/targeted_pilot`: intento abortado por composición. `artifacts/targeted_pilot_balanced/run_hardcases_v1`: tres épocas completas, mejor checkpoint en la segunda. `artifacts/run_candidate`: evaluación homogénea del candidato. Configuración del piloto: AdamW, lr0=0.0001, lrf=0.1, batch=4, imgsz=448, patience=2, seed=42, CPU y primeras 10 capas congeladas. No se entrenó desde cero. Los argumentos completos, composición y métricas por época están guardados. Es un piloto acotado, no una búsqueda exhaustiva ni una ablación que identifique una única causa.


## Modelo baseline

 `models/vector_urosight/best.pt` (ruta de instalación; el checkpoint operativo se conserva también en el portable local).
SHA-256: `c5fba1aeccb60ca8eac49c1750123a5dc85f22456f02f805f62fff6386669530`. Se corrigió el hash y la configuración obsoletos de MODEL_CARD.md; el registro histórico de entrenamiento ya registraba el hash correcto.


## Modelo candidato

 `artifacts/targeted_pilot_balanced/run_hardcases_v1/weights/best.pt`.
SHA-256: `4410c4e7709ce04510570140f6b5b22403afc623bda8a28733a9165d287e99cf`. Se conserva para inspección y trazabilidad, sin activarlo.


## Comparación global

 Evaluación real de las mismas 848 imágenes y 5,940 etiquetas de validation, mediante Ultralytics.val, 448 px, batch 4, augment=True y confianza mínima 0.001 para AP. P/R corresponden al punto de máximo F1 suavizado que devuelve la librería, no al umbral operativo fijo.

| Modelo | Precision | Recall | mAP50 | mAP50–95 |
|---|---:|---:|---:|---:|
| Baseline | 0.825059 | 0.815430 | 0.867705 | 0.509357 |
| Candidato | 0.821721 | 0.822326 | 0.871625 | 0.505667 |


## Comparación por clase

 P/R/F1 siguientes se calculan a 0.44 sobre `model.predict`, antes de la NMS adicional de la aplicación. AP50–95 procede de la evaluación estándar anterior. Cada comparación baseline/candidato utiliza el mismo método y configuración; no se mezclan sus puntos operativos.

| Clase | P a 0.44: baseline → candidato | R a 0.44: baseline → candidato | F1 a 0.44: baseline → candidato | AP50–95: baseline → candidato |
|---|---:|---:|---:|---:|
| eryth | 0.8960 → 0.8847 | 0.8849 → 0.8903 | 0.8904 → 0.8875 | 0.5180 → 0.5147 |
| leuko | 0.8508 → 0.7915 | 0.9171 → 0.9585 | 0.8827 → 0.8670 | 0.5656 → 0.5693 |
| epith | 0.7365 → 0.6845 | 0.8316 → 0.8853 | 0.7812 → 0.7721 | 0.5391 → 0.5472 |
| epithn | 0.7901 → 0.8493 | 0.8312 → 0.8052 | 0.8101 → 0.8267 | 0.4438 → 0.4380 |
| cast | 0.7204 → 0.6833 | 0.6489 → 0.6783 | 0.6828 → 0.6808 | 0.4236 → 0.4137 |
| cryst | 0.8395 → 0.7981 | 0.7968 → 0.7905 | 0.8176 → 0.7943 | 0.5343 → 0.5250 |
| mycete | 0.7843 → 0.7893 | 0.8584 → 0.8197 | 0.8197 → 0.8042 | 0.5411 → 0.5318 |


Las confusiones directas eryth→leuko pasan de 14 a 12, y leuko→eryth de 1 a 2, a IoU 0.50 y conf 0.44. Es un cambio pequeño. Las matrices completas, incluidas filas/columnas background para FP/FN, están en los artefactos. La caída de AP50–95 en las tres prioridades impide afirmar mejora; en algunas clases AP50 y P/R mejoran mientras la localización a IoUs más exigentes empeora. Esta observación no identifica por sí sola la causa del deterioro.


## Resultado sobre TEST

 No ejecutado en este ciclo: el candidato fue rechazado en validation antes de ser candidato final. No se seleccionaron umbrales ni hiperparámetros con TEST. Como antecedente, el registro histórico de entrenamiento documenta para el baseline P=0.808721, R=0.813571, mAP50=0.854268, mAP50–95=0.494546; son resultados históricos, no mediciones nuevas. No se generó una nueva matriz de TEST.


## QA sobre Silver Review Pack

 Se procesaron 64/64 campos sin fallos con ambos modelos. Los 29 originales incluidos en el ZIP coinciden byte por byte con el conjunto localizado. Coincidencias de presencia: 31→33. Posibles omisiones: cast 10→10, mycete 5→5, epithn 3→4, eryth 3→3, leuko 6→6 y cryst 0→1. Presencias posiblemente no respaldadas de cryst: 12→8. Este resultado es mixto y exclusivamente sintético; no se calcularon métricas clínicas ni mAP con el paquete.


## Bugs y regresiones

 Se corrigieron los problemas descritos de presentación, umbral y revisión/PDF. El PDF podía dividir entre cero al corregir a una clase antes ausente; ahora usa clases revisadas, muestra advertencias y las anotaciones exportadas reflejan la revisión. Las clases originales siguen disponibles en CSV/JSON. Pytest completo: 56 aprobadas, 0 fallidas. Se ejecutó inferencia real individual y múltiple, selección de carpeta, PDF/CSV/JSON, revisión humana y prueba real de saturación. No se afirma una revisión manual exhaustiva de la GUI ni validación clínica.


## Modelo finalmente integrado

 Se conserva el baseline operativo, con su hash verificado sin cambios. No hubo reemplazo ni promoción. Las correcciones de interfaz/exportación están en el código fuente de este checkout; el ejecutable portátil no se reconstruyó.


## Archivos modificados y artefactos

 Código/configuración: `.env.example`, `src/config.py`, `src/main.py`, `src/domain/models.py`, `src/inference/local_yolo_provider.py`, `src/processing/class_normalizer.py`, `src/services/export_service.py`, `src/ui/main_window.py`, `src/ui/image_renderer.py`, `src/reports/pdf_report.py`. Herramientas: `tools/evaluate_model.py`, `tools/select_threshold.py` y los nuevos `silver_review.py`, `validation_experiments.py`, `mine_real_hard_cases.py`, `targeted_finetune.py`, `inference_benchmark.py`. Pruebas: `test_config.py`, `test_exports_and_pdf.py`, `test_ui_smoke.py`, `test_local_yolo_provider.py`, `test_silver_review.py`. Documentación: README, MODEL_CARD, PROJECT_STATUS y los tres informes de este ciclo.

Artefactos principales: `artifacts/model_comparison_before_after.csv`, `artifacts/model_comparison_fixed_threshold.csv`, `artifacts/model_selection_decision.json`, `artifacts/silver_review_baseline/`, `artifacts/silver_review_after/`, `artifacts/silver_review_before_after.csv`, `artifacts/validation_short_term/`, `artifacts/candidate_fixed_thresholds/`, `artifacts/silver_real_audit/`, `artifacts/annotation_visual_audit/`, `data_processed/hard_cases_real/hard_cases_manifest.csv` y `artifacts/pytest_final.txt`. Los datasets/pesos/resultados permanecen fuera de Git conforme a `.gitignore`.


## Próxima mejora recomendada

 Priorizar la revisión experta de cajas cast y agrupaciones mycete, y separar experimentalmente sampling de augmentation/localización. El siguiente piloto debe preservar mejor la distribución original y comprobar AP por clase antes de abrir TEST. El límite de detecciones merece un experimento específico en campos reales densos. No añadir sintéticos al entrenamiento ni fijar objetivos porcentuales arbitrarios.

La suspensión del equipo y la ejecución compartida de CPU invalidan comparar los tiempos de pared de las corridas largas. Se conservaron los registros originales y se realizó una medición secuencial aparte, sin reutilizar esos tiempos como latencia del modelo.

Medición separada: 16 imágenes de validation elegidas con seed 42, tres rondas por variante, calentamiento previo, conf=0.44 y augment=True. Incluye lectura, preprocesamiento e inferencia; excluye matching de métricas. La carga del resto del equipo no está controlada.

| Variante | Mediana ms/imagen | RSS máximo muestreado (MiB) |
|---|---:|---:|
| original448 | 254.7 | 437.9 |
| original640 | 390.7 | 472.4 |
| clahe | 273.5 | 473.8 |
| contrast | 280.6 | 473.6 |
| brightness | 273.1 | 473.7 |
| denoise | 268.3 | 473.8 |

RSS es memoria del proceso compartido, incluidos buffers retenidos entre variantes; no es memoria aislada de cada transformación ni un pico instantáneo certificado. Datos y muestras individuales: `artifacts/inference_benchmark.json`.
