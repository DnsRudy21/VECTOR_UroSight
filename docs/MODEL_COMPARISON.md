# Comparación de modelos

## Estado actual

El baseline YOLO11n terminó 30 épocas. No se presentan métricas ficticias ni resultados parciales como finales.

## Variante activa

| Run | Arquitectura | Resolución | Batch | Hardware | Estado |
|-----|--------------|------------|-------|----------|--------|
| `baseline_yolo11n_320` | YOLO11n preentrenado | 320 | 8 | CPU Intel Core i7-7700HQ | Completado, 30 épocas; test mAP@50 0.7526, mAP@50–95 0.4293 |

La corrida de medición con 2 % del train confirmó viabilidad y permitió estimar tiempos, pero no participa en selección porque no representa un entrenamiento comparable.

## Criterios de selección

- mAP@50–95 y mAP@50 en validación.
- Precision y recall globales y por clase.
- Rendimiento de clases minoritarias.
- Estabilidad entre épocas.
- Tamaño del checkpoint y tiempo de inferencia local.
- Análisis de falsos positivos, falsos negativos y confusiones.

El test interno no participa en la comparación. Se usa una sola vez después de congelar el checkpoint y threshold.

## Variante de mayor capacidad

No se entrenó YOLO11s porque el equipo solo dispone de CPU y el baseline de 30 épocas consumió varias horas. Una corrida mayor excedería el alcance temporal sin garantizar mejora y no sería una comparación equivalente si se acorta. YOLO11n ofrece 2.58 M de parámetros, un checkpoint de ~5.4 MB y 14.6 ms de inferencia de evaluación por imagen en esta CPU. Una variante mayor queda como experimento futuro controlado, no como requisito de liberación.
