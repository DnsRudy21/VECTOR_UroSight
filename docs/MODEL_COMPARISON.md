# Comparación de modelos

Evaluación del 8 de septiembre de 2026: 848 imágenes reales de validación, 5,940 objetos; 448 px, batch 4 e inferencia aumentada. AP usa confianza mínima 0.001. Precisión y recall corresponden al máximo F1 de Ultralytics.

| Modelo | Precisión | Recall | mAP@50 | mAP@50–95 | Decisión |
|:---|---:|---:|---:|---:|:---|
| YOLO11s operativo | 0.825059 | 0.815430 | 0.867705 | 0.509357 | Conservar |
| Piloto dirigido, 3 épocas | 0.821721 | 0.822326 | 0.871625 | 0.505667 | No promover |

El candidato también perdió AP50–95 en cilindros, núcleos epiteliales y levaduras/hongos. TEST permaneció reservado. El aumento de recall global y AP50 no compensó la caída del criterio de selección ni de las clases prioritarias.

Los hashes, resultados por clase, configuración y comparaciones a umbral fijo están en el [informe experimental](MODEL_IMPROVEMENT_REPORT.md). Las variantes anteriores se documentan en el historial Git; no representan el modelo activo.
