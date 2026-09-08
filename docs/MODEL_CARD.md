# Model Card — VECTOR UroSight

## Auditoría de identidad — 2026-09-08

El checkpoint recuperado de la aplicación portátil tiene SHA-256
`c5fba1aeccb60ca8eac49c1750123a5dc85f22456f02f805f62fff6386669530`, arquitectura
YOLO11s y siete clases. Sus argumentos declaran el entrenamiento dirigido a 448 px
con máximo de 15 épocas. Esta ficha describe el modelo vigente.
La nueva evaluación de validation reproduce exactamente
precision 0.8250585355, recall 0.8154298249, mAP50 0.8677050042 y mAP50–95 0.5093572068.
Esos P/R corresponden al punto de máximo F1 de Ultralytics, no a conteos en un umbral fijo.
La latencia de esta nueva corrida no es válida por una interrupción del reloj de pared.
La auditoría y los límites de QA sintético se detallan en `SILVER_REVIEW_DIAGNOSIS.md`.
Los resultados históricos de TEST no se presentan como una nueva ejecución de TEST.

El piloto de este ciclo (SHA-256 `4410c4e7709ce04510570140f6b5b22403afc623bda8a28733a9165d287e99cf`)
fue rechazado: validation mAP50–95 0.505667 frente a 0.509357 del modelo operativo,
con deterioro también en cast, mycete y epithn. No se abrió TEST para este candidato.
El modelo operativo y sus pesos permanecen intactos.

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

- Arquitectura: YOLO11s mediante transferencia de aprendizaje, sin entrenamiento desde cero.
- Implementación: Ultralytics 8.4.90, PyTorch 2.12.1+cpu.
- Hardware auditado: Intel Core i7-7700HQ; CUDA no disponible.
- Resolución de entrenamiento confirmada en el checkpoint: 448 px.
- Configuración operativa seleccionada en validación: 448 px con inferencia aumentada.
- Batch: 4; máximo 15 épocas; patience 6; seed 42; workers 0.
- Selección histórica documentada: época 13 de 15. El checkpoint distribuido está depurado (`epoch=-1`) y no confirma por sí solo la época seleccionada.
- Umbral operativo: 0.443443 (mostrado como 0.44), seleccionado exclusivamente en validation por máximo F1 medio global.
- SHA-256 de pesos: `c5fba1aeccb60ca8eac49c1750123a5dc85f22456f02f805f62fff6386669530`.

## Datos

Fuente principal: USE, formato Pascal VOC. La auditoría histórica documentó 5,292 imágenes y 41,695 objetos tras excluir imágenes ilegibles y duplicados exactos entre splits (4,176 train, 848 validación y 268 test). La fuente recuperada en este ciclo produce 5,293 imágenes y 41,697 objetos (4,177 train, 848 validación y 268 test); esta reconstrucción y su diferencia de una imagen están documentadas en HARD_CASE_ANNOTATION_AUDIT.md.

Clases: `eryth`, `leuko`, `epith`, `epithn`, `cast`, `cryst` y `mycete`. La ontología y los conteos se detallan en `CLASS_ONTOLOGY.md`.

UMID se reserva para validación externa de las tres categorías semánticamente compatibles (`rbc`, `pus`, `ep`). El derivado externo contiene 363 imágenes etiquetadas y 2,979 objetos: 1,556 eritrocitos, 986 leucocitos y 437 células epiteliales. Tres imágenes sin etiqueta se excluyeron explícitamente. UMID no se usa para seleccionar checkpoint, hiperparámetros ni threshold.

## Integridad del dataset

- Cero duplicados exactos entre splits en el dataset maestro.
- Cero etiquetas YOLO inválidas después de conversión.
- Doce cajas con coordenadas negativas de uno o dos píxeles fueron recortadas al borde y registradas.
- Una imagen ilegible fue excluida.
- La procedencia, exclusiones y correcciones permanecen en artefactos auditables.

## Evaluación

Checkpoint congelado en época 13 de una corrida de 15 épocas. En validation homogénea a 448 px con inferencia aumentada obtuvo precision 0.8250585355, recall 0.8154298249, mAP@50 0.8677050042 y mAP@50–95 0.5093572068.

La configuración final congelada, YOLO11s a 448 px con aumento, obtuvo en test independiente precision 0.8087206951, recall 0.8135713135, mAP@50 0.8542678047 y mAP@50–95 0.4945459311. La evaluación midió 170.43 ms de inferencia por imagen en la CPU de desarrollo. El test no participó en entrenamiento, selección del checkpoint ni selección del umbral.

Por clase, mAP@50–95 en test final: `eryth` 0.562566, `leuko` 0.478175, `epith` 0.572052, `epithn` 0.328274, `cast` 0.382359, `cryst` 0.576591 y `mycete` 0.561804. `epithn` continúa siendo la clase más débil por esta métrica.

La evaluación histórica del proyecto en UMID, limitada a las tres clases compatibles, registró precision 0.5238, recall 0.1199, mAP@50 0.0685 y mAP@50–95 0.0348. Es un antecedente de cambio de dominio severo, no una evaluación externa nueva ni una medición verificada del checkpoint YOLO11s actual. UMID no estaba disponible durante la auditoría de septiembre; la validación externa del modelo vigente queda pendiente.

## Limitaciones y riesgos

- Dataset único para las siete clases; riesgo de domain shift.
- Resolución reducida por restricciones de CPU, potencialmente desfavorable para objetos pequeños.
- Desbalance de clases, especialmente `epithn`.
- Diferencias de protocolo y anotación entre USE y UMID.
- Rendimiento externo muy inferior al interno; no usar fuera del dominio documentado sin nueva validación y adaptación.
- No hay calibración clínica, estudio prospectivo, evaluación multicéntrica ni análisis regulatorio.
- Los datasets, imágenes y pesos se excluyen de la publicación. El código fuente público usa AGPL-3.0 para alinearse con la integración Ultralytics; cualquier distribución comercial requiere revisión jurídica y de licencias independiente.
