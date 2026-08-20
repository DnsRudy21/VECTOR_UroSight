# Registro de decisiones

## D-001 — PySide6
Aplicación de escritorio profesional y extensible.

## D-002 — Proveedor intercambiable
La inferencia se abstrae para evitar dependencia permanente de una plataforma.

## D-003 — Reglas auditables
La primera interpretación se genera mediante reglas explícitas.

## D-004 — Mock-first
La GUI se desarrolla y valida primero con un proveedor simulado.

## D-005 — Estudio multimagen y fallos parciales
Cada imagen representa un campo del mismo estudio. Los errores se conservan por campo y no invalidan resultados correctos de otras imágenes.

## D-006 — Procesamiento en hilo de Qt
La inferencia usa un worker en `QThread`. La cancelación ocurre entre imágenes y la GUI evita ejecuciones duplicadas.

## D-007 — Dependencias opcionales
La instalación base incluye el modo demostración. Ultralytics y Roboflow se instalan por separado para evitar descargas innecesarias.

## D-008 — Métricas no equivalentes a valores clínicos
Los promedios se rotulan por imagen procesada. No se convierten a valores clínicos ni se inventan rangos.

## D-009 — Sin datos clínicos incluidos
El repositorio no incorpora imágenes, datasets o pesos. Las capturas deberán usar material autorizado o sintético.

## D-010 — Trazabilidad antes que descarte
Las detecciones originales se conservan. La salida depurada diferencia detecciones aceptadas, ocultas por umbral y marcadas para revisión.

## D-011 — NMS neutral
La normalización aplica NMS por clase con IoU 0.50 después de resolver alias. Las cajas fuera de límites se ajustan y quedan marcadas para revisión.

## D-012 — Calidad técnica no bloqueante
Brillo, contraste y varianza de bordes usan umbrales explícitos documentados. No rechazan imágenes ni representan calidad clínica.

## D-013 — Transparencia del proveedor
El proveedor activo y la condición simulada forman parte del dominio y de todas las salidas. Los tiempos del mock no se presentan como rendimiento real.

## D-014 — Roboflow mediante REST directo
Windows Application Control bloquea una DLL importada indirectamente por `inference-sdk`. Sin modificar la política del sistema, el adaptador usa el endpoint REST oficial con `requests`, cuerpo base64, timeout y errores sanitizados.

## D-015 — Umbral único desde configuración
`CONFIDENCE_THRESHOLD` configura la solicitud remota, el resultado del estudio y el valor inicial del control de interfaz. Los cambios posteriores del usuario solo filtran las detecciones ya recibidas.

## D-016 — Validación remota real
La integración REST se ejecutó con una imagen y después con tres imágenes controladas. Se verificaron clases, confianza, cajas dentro de límites, normalización y exportaciones PDF, CSV y JSON sin presencia de la API key.

## D-017 — Clases verificadas contra respuesta real
En seis imágenes y tres umbrales el modelo devolvió `cast`, `epith` y `leuko`. Se verificó el mapeo `cast → cilindros`, `epith → celulas_epiteliales` y `leuko → leucocitos`; no se infirieron etiquetas no observadas.

## D-018 — Auditoría separada del diagnóstico
La respuesta JSON cruda solo se conserva con `ROBOFLOW_DIAGNOSTIC=true`. Las revisiones humanas y correcciones son metadatos explícitos; no alteran la predicción original.

## D-019 — Preprocesamiento experimental no combinable
CLAHE, ajuste moderado y reducción ligera de ruido generan copias temporales. La variante queda rotulada y sus resultados no se mezclan con el análisis original.

## D-020 — Auditoría separada por fuente y nivel de derivación
USE y UMID se auditan por separado. `datasets` contiene fuentes y `data_processed` derivados; no se suman como datasets independientes ni se consideran duplicados científicos solo por aparecer en ambos niveles.

## D-021 — Ontología conservadora
`epithn` se conserva como núcleo epitelial independiente de `epith`, de acuerdo con el README de USE. Las equivalencias `rbc/eryth`, `pus/leuko` y `ep/epith` conservan siempre clase cruda y fuente para no ocultar diferencias de dominio o anotación.

## D-022 — Entrenamiento condicionado a auditoría reproducible
No se inicia entrenamiento hasta validar correspondencias imagen-etiqueta, cajas, duplicados y splits. El equipo disponible es CPU sin CUDA; el ETA se calculará solo después de una corrida corta con segundos por época medidos.

## D-023 — USE para entrenamiento y UMID para validación externa
El baseline de siete clases se prepara con USE. UMID se reserva como conjunto externo independiente para `eritrocitos`, `leucocitos` y `celulas_epiteliales`; no se usa para ajustar hiperparámetros ni umbrales.

## D-024 — Deduplicación con prioridad de aislamiento
Al encontrar imágenes idénticas en varios splits se conserva una sola. La prioridad es test, luego validación y finalmente entrenamiento, evitando que una imagen del test reaparezca durante ajuste. Las cajas negativas de uno o dos píxeles se recortan al límite durante la conversión y quedan registradas; los originales no se modifican.

## D-025 — Baseline YOLO11n a 320 px en CPU
La medición local mostró 7 min 43 s para entrenar una época completa y 36 s para validar 848 imágenes. Se eligió YOLO11n a 320 px, batch 8, máximo 30 épocas y patience 7 como baseline viable en CPU. La resolución es una restricción operativa, no una afirmación de optimalidad clínica.

## D-026 — Selección en validación y uso único de test
El checkpoint se selecciona por mAP@50–95 de validación. Thresholds y decisiones de configuración se comparan en validación. El test interno permanece aislado y se evalúa una sola vez después de congelar modelo y threshold.

## D-027 — Checkpoint final y umbral congelados
La corrida YOLO11n completó 30 épocas y seleccionó la época 30. El umbral 0.25 se eligió exclusivamente en validación por máximo F1 global antes de evaluar test. Los pesos se identifican por SHA-256 `693e2a1b90601c962f1f83c88ba655a0cb55e974a5d084a0d229b703d6faa02f`.

## D-028 — Domain shift externo como limitación crítica
UMID obtuvo recall 0.1199 y mAP@50–95 0.0348 frente a 0.7476 y 0.4293 en test interno. El modelo se limita al dominio experimental documentado y no se presenta como generalizable ni clínicamente validado.

## D-029 — No entrenar una variante mayor en CPU
YOLO11s no se ejecuta porque no hay GPU, el baseline completo consumió varias horas y una corrida abreviada no sería comparable. YOLO11n satisface la integración local y deja la comparación de mayor capacidad como experimento futuro, condicionado a hardware y protocolo equivalentes.

## D-030 — Calidad operativa separada de exactitud clínica
La repetibilidad, ausencia de fallos y latencia se verifican con seis imágenes y tres rondas idénticas. Esta puerta operativa no mide sensibilidad ni especificidad y no puede compensar la baja generalización observada en UMID. Acercarse a 100 % exige un conjunto representativo rotulado y revisión de especialistas.

## D-031 — Identidad de paciente mínima y transitoria
Cada selección genera un ID `PT-AAAAMMDD-XXXXXX`; el nombre es opcional y ambos viajan con el resultado y sus exportaciones. No se implementa expediente, base de datos ni interoperabilidad clínica en esta fase, para evitar presentar un identificador local como identidad institucional.

## D-032 — Portable Windows autocontenido y sin secretos
El paquete `onedir` incluye Python, PySide6, el runtime de inferencia y el checkpoint congelado. No incluye `.env`, API keys ni datasets. La portabilidad se limita a Windows x64 compatible y la redistribución externa de pesos queda condicionada a su licencia.

## D-033 — Publicación fuente mínima bajo AGPL-3.0
El repositorio público excluye datasets, imágenes, pesos, checkpoints, portables, resultados generados, credenciales y artefactos de entrenamiento. Debido a la integración opcional con Ultralytics, el código público se alinea con AGPL-3.0. Cualquier distribución propietaria o comercial debe revisar licencias Enterprise de Ultralytics, términos de Qt y obligaciones regulatorias con asesoría independiente.
