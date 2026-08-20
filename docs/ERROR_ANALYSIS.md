# Análisis de errores

## Estado

Ejecutado con checkpoint y umbral congelados. El protocolo se definió antes de observar el test.

## Protocolo

- Split: test interno deduplicado, 268 imágenes.
- Threshold: seleccionado previamente sobre validación.
- Emparejamiento: IoU ≥ 0.50, uno a uno y por clase.
- Verdadero positivo: predicción y anotación de la misma clase emparejadas.
- Falso positivo: predicción sin anotación de la misma clase emparejable.
- Falso negativo: anotación sin predicción de la misma clase emparejable.
- Clasificación errónea: predicción y anotación con IoU ≥ 0.50 pero clases diferentes.

La herramienta `tools/error_analysis.py` genera conteos globales, desglose por clase y hasta veinte nombres de imágenes de ejemplo por categoría. No cambia etiquetas ni reentrena el modelo.

## Aspectos que se inspeccionarán

- Objetos pequeños perdidos por la resolución de 320 px.
- Confusión entre eritrocitos y leucocitos.
- Confusión entre células epiteliales y núcleos epiteliales.
- Falsos positivos en fondos, bordes y artefactos.
- Clases minoritarias con soporte o recall insuficiente.
- Diferencias de dominio en UMID para las tres clases compartidas.

## Resultados

Con umbral 0.25 e IoU 0.50: 1,415 verdaderos positivos, 545 falsos positivos, 241 falsos negativos y 36 clasificaciones erróneas. Los falsos positivos son el principal volumen de error; `cast` (recall 0.497, mAP@50–95 0.284) y `epithn` (mAP@50–95 0.282) son las clases internas más débiles.

UMID externo obtuvo recall 0.1199 y mAP@50–95 0.0348, una degradación mucho mayor que las variaciones internas. Esto apunta a diferencias de captura, escala, apariencia o política de anotación y no debe interpretarse como desempeño clínico generalizable.

La evidencia completa y las predicciones renderizadas se conservaron como artefactos locales de investigación y se excluyeron del repositorio público por tamaño, privacidad y licencia. Los resultados consolidados permanecen documentados aquí y en `MODEL_CARD.md`.
