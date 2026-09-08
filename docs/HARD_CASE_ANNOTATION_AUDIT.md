# Auditoría de anotaciones y hard cases reales

Fuente real: USE original, conservado fuera del repositorio (USE, Pascal VOC).
Fuentes intactas. Auditoría técnica en `artifacts/silver_real_audit`; derivado en
`data_processed/silver_real_baseline`.

Se encontraron 5,391 imágenes y 42,235 objetos anotados, 12 cajas fuera de límites,
15 imágenes sin anotación fuera de los splits y 26 grupos hash presentes entre splits.
El derivado deduplicado tiene 4,177 train, 848 val y 268 test: 5,293 imágenes y
41,697 objetos. Se excluyeron 83 imágenes duplicadas y se recortaron 12 cajas a los
límites, conservando registro de coordenadas originales. No hubo relabeling clínico.
La fuente recuperada tiene una imagen más que la descrita en documentación histórica;
no se reutilizan conteos históricos como si fueran resultados nuevos.
Las 268 etiquetas de test coinciden byte por byte con el derivado previo recuperado.

Se seleccionaron 20 campos por grupo: cast, mycete, epithn, eryth_leuko y cryst.
Son candidatos de revisión provenientes exclusivamente de train: extremos de tamaño
anotado y densidad eryth/leuko. No son todos errores confirmados del modelo.
El manifiesto contiene 7,609 filas de objetos objetivo con origen, XML, bbox, split,
motivo, hash de imagen y anotación y ruta de copia. Cada campo conserva XML completo
y etiquetas YOLO derivadas, incluidas las otras clases.

## Inspección visual acotada

Se inspeccionaron cuatro campos por clase débil (16 paneles, no toda la colección).
Los paneles anotados están en `artifacts/annotation_visual_audit`.

- cast: nl00012, nl00198, nl00248, nl00250. Variación marcada de área y forma;
  cajas rectangulares contienen fondo alrededor de estructuras oblicuas, lo que
  no basta para calificarlas de incorrectas. Revisar especialmente nl00198 por
  objetos pequeños y bajo contraste.
- mycete: nh00002, nh00003, nh00974, nh01102. Objetos pequeños y agrupaciones;
  revisar consistencia entre anotación por objeto y por grupo. No hay evidencia
  suficiente para separar automáticamente las cajas agrupadas.
- epithn: nh00629, nh01241, nh01256, nh01270. Cajas sobre regiones nucleares pequeñas,
  coherentes con la distinción frente a célula completa; importante para interpretar QA.
- cryst: nh00583, nh00660, nh00735, nh01684. Gran variación de tamaño y campos densos;
  los objetos mínimos requieren revisión a resolución original por un experto.

No se certifica exhaustividad: cajas incompletas, clases erróneas y objetos omitidos
requieren revisión especializada y anotación objeto por objeto. Esta inspección técnica no sustituye la validación clínica de las etiquetas.
UMID no está disponible en la ruta indicada; no se afirma haber auditado sus anotaciones.

## Sampling y augmentations

Los candidatos se mantienen separados de val/test. Para un piloto se puede añadir
como máximo una exposición extra por campo seleccionado, preservando todas sus clases
y registrando el listado exacto. No se deben multiplicar las filas del manifiesto
como si fueran imágenes independientes: los campos densos quedarían sobrerrepresentados.
Rotación y escala suaves, iluminación moderada y ausencia de mosaic permiten evaluar
una hipótesis de preservación morfológica. No se usan sintéticos para entrenar.

El primer intento fue detenido antes de terminar una época: repetir también los
campos eryth/leuko llevaba a 16,238 objetos eryth de 20,421 exposiciones de objetos.
Se conserva en `artifacts/targeted_pilot` como intento abortado, sin promoción.
El piloto corregido usa 700 campos elegidos con seed 42, unidos a 79 campos de los
otros cuatro grupos: 767 campos únicos, más una exposición adicional por esos 79
campos (846 exposiciones). Los campos eryth/leuko no reciben repetición dirigida;
pueden aparecer en la muestra aleatoria de train.
Composición exacta de objetos por exposición: eryth 3,977; leuko 1,018; epith 845;
epithn 142; cast 574; cryst 317; mycete 571. Se registra el listado completo y sus
hashes en `artifacts/targeted_pilot_balanced/training_manifest.json`.
Configuración: 3 épocas máximas, patience 2, AdamW lr0=0.0001, batch 4, imgsz 448,
seed 42, CPU, primeras 10 capas congeladas. Rotación ±5°, escala ±0.1,
traslación 0.03, brillo HSV 0.1, flips horizontales/verticales 0.5; sin mosaic,
mixup, shear ni perspective. Es un piloto acotado, no una búsqueda exhaustiva.
