# Model Card — VECTOR UroSight

## Estado

Modelo experimental entrenado y evaluado. Está integrado para uso local supervisado, pero no está clínicamente validado.

## Propósito

Detector de partículas en imágenes microscópicas de sedimento urinario para un prototipo académico de apoyo a revisión humana. No diagnostica, no sustituye al profesional del laboratorio y no está clínicamente validado.

## Uso previsto

- Mostrar detecciones, clases, confianza y cajas revisables.
- Consolidar conteos por las imágenes cargadas.
- Facilitar corrección y trazabilidad humana.
- Apoyar investigación y demostración tecnológica controlada.

## Usos no previstos

- Diagnóstico autónomo o decisiones terapéuticas.
- Sustituir el recuento o criterio profesional.
- Interpretar detecciones por imagen como valores clínicos por campo sin controlar preparación, aumento, área y protocolo.
- Uso como dispositivo médico validado o regulado.

## Arquitectura y entrenamiento

- Arquitectura: YOLO11n mediante transferencia de aprendizaje, sin entrenamiento desde cero.
- Implementación: Ultralytics 8.4.90, PyTorch 2.12.1+cpu.
- Hardware auditado: Intel Core i7-7700HQ; CUDA no disponible.
- Resolución de entrenamiento: 320 px.
- Configuración operativa seleccionada en validación: 448 px con inferencia aumentada.
- Batch: 8; máximo 30 épocas; patience 7; seed 42; workers 0.
- Selección: fitness de Ultralytics sobre validación interna; mejor checkpoint en época 30.
- Umbral operativo: 0.25, seleccionado exclusivamente en validación por máximo F1 global.
- SHA-256 de pesos: `693e2a1b90601c962f1f83c88ba655a0cb55e974a5d084a0d229b703d6faa02f`.

## Datos

Fuente principal: USE, formato Pascal VOC. El dataset maestro derivado contiene 5,292 imágenes y 41,695 objetos tras excluir imágenes ilegibles y duplicados exactos entre splits. Splits: 4,176 train, 848 validación y 268 test.

Clases: `eryth`, `leuko`, `epith`, `epithn`, `cast`, `cryst` y `mycete`. La ontología y los conteos se detallan en `CLASS_ONTOLOGY.md`.

UMID se reserva para validación externa de las tres categorías semánticamente compatibles (`rbc`, `pus`, `ep`). El derivado externo contiene 363 imágenes etiquetadas y 2,979 objetos: 1,556 eritrocitos, 986 leucocitos y 437 células epiteliales. Tres imágenes sin etiqueta se excluyeron explícitamente. UMID no se usa para seleccionar checkpoint, hiperparámetros ni threshold.

## Integridad del dataset

- Cero duplicados exactos entre splits en el dataset maestro.
- Cero etiquetas YOLO inválidas después de conversión.
- Doce cajas con coordenadas negativas de uno o dos píxeles fueron recortadas al borde y registradas.
- Una imagen ilegible fue excluida.
- La procedencia, exclusiones y correcciones permanecen en artefactos auditables.

## Evaluación

Checkpoint congelado en época 30. En validación interna obtuvo precision 0.7606, recall 0.7605, mAP@50 0.8032 y mAP@50–95 0.4574.

La evaluación histórica a 320 px produjo precision 0.7811, recall 0.7476, mAP@50 0.7526 y mAP@50–95 0.4293. Una primera optimización a 480 px alcanzó mAP@50 0.825461 y mAP@50–95 0.469418 en test. Tras observar menor cobertura operativa en las imágenes sintéticas, se compararon resoluciones finas e inferencia aumentada exclusivamente en validation. La configuración final congelada, 448 px con aumento, obtuvo en test precision 0.7710333312410897, recall 0.8159774487925525, mAP@50 0.8359672915142167 y mAP@50–95 0.4872195835201552. La inferencia fue 67.80 ms por imagen en CPU.

Por clase, mAP@50–95 en test final: `eryth` 0.546, `leuko` 0.501, `epith` 0.585, `epithn` 0.334, `cast` 0.367, `cryst` 0.562 y `mycete` 0.516. `epithn` es la clase más débil por esta métrica.

En UMID externo, limitado a las tres clases compatibles, obtuvo precision 0.5238, recall 0.1199, mAP@50 0.0685 y mAP@50–95 0.0348. La caída evidencia domain shift severo y limita la generalización fuera de USE.

## Limitaciones y riesgos

- Dataset único para las siete clases; riesgo de domain shift.
- Resolución reducida por restricciones de CPU, potencialmente desfavorable para objetos pequeños.
- Desbalance de clases, especialmente `epithn`.
- Diferencias de protocolo y anotación entre USE y UMID.
- Rendimiento externo muy inferior al interno; no usar fuera del dominio documentado sin nueva validación y adaptación.
- No hay calibración clínica, estudio prospectivo, evaluación multicéntrica ni análisis regulatorio.
- Los datasets, imágenes y pesos se excluyen de la publicación. El código fuente público usa AGPL-3.0 para alinearse con la integración Ultralytics; cualquier distribución comercial requiere revisión jurídica y de licencias independiente.
