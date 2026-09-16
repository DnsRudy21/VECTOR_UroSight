# Ficha del modelo · VECTOR UroSight 1.1.0

## Propósito
Detección de partículas en imágenes de sedimento urinario para investigación y revisión profesional. No es un diagnóstico autónomo ni un dispositivo clínicamente validado. Los conteos son por imagen, sin equivalencia automática con recuentos clínicos por campo.

## Modelo y reproducibilidad
- Arquitectura: YOLO11s; siete clases USE.
- Pesos SHA-256: `5b1d9d5b84450d2b1bd9ca1e496bcce38a74d09bf6e547ce666a06183c411b64`.
- Python 3.11.9; Ultralytics 8.4.90; PyTorch 2.12.1; PySide6 6.8.3.
- Ajuste sobre checkpoint previo mediante AdamW, LR inicial 0.00005, semilla 42, batch 4, 448 px, diez capas iniciales congeladas. Cinco épocas completadas, selección de la segunda; máximo de 6 épocas y patience 3.
- Inferencia CPU: 448 px, TTA, confianza 0.44, NMS del detector 0.70 y NMS adicional por clase 0.50. Límite de 300 detecciones. Letterbox y normalización estándar; sin CLAHE.
- La versión portable verifica el hash y usa configuración fija; requiere conservar su carpeta _internal. No descarga dependencias ni pesos.

## Datos y selección
Dataset USE: 5,293 imágenes, 41,697 objetos; entrenamiento 4,177, validación 848, test 268. Se conserva la separación por particiones, se excluyen duplicados exactos entre ellas y se registran ajustes geométricos. No hay adjudicación clínica independiente de etiquetas. El entrenamiento usa datos reales; Silver se utiliza exclusivamente como QA sintético.

Se seleccionó el mayor AP50–95 global de cinco checkpoints del ajuste, considerando las siete clases. Pesos y parámetros se congelaron antes de una única evaluación final de TEST. Este benchmark ya se había usado históricamente; no constituye una nueva cohorte independiente de todo el desarrollo.

## Resultados
| Partición | Imágenes | Precisión | Recall | F1¹ | AP50 | AP50–95 |
|---|---:|---:|---:|---:|---:|---:|
| VALIDATION | 848 | 0.824766 | 0.820456 | 0.822605 | 0.871297 | 0.513161 |
| TEST | 268 | 0.803647 | 0.814189 | 0.808884 | 0.858437 | 0.500787 |

¹ F1 es 2PR/(P+R) de precisión y recall macro del punto de máximo F1 suavizado de Ultralytics. No es F1 macro por clase ni una medición al umbral fijo de la interfaz. AP usa predicciones desde confianza 0.001 y NMS estándar del detector; las métricas de aplicación tras NMS adicional se calculan por separado. No representa rendimiento clínico.

| Clase TEST | Objetos | AP50 | AP50–95 |
|---|---:|---:|---:|
| eryth | 599 | 0.971884 | 0.573092 |
| leuko | 261 | 0.889150 | 0.505463 |
| epith | 418 | 0.891883 | 0.574873 |
| epithn | 35 | 0.723532 | 0.328520 |
| cast | 194 | 0.711531 | 0.384223 |
| cryst | 84 | 0.873405 | 0.585018 |
| mycete | 101 | 0.947674 | 0.554321 |

## Limitaciones
- Núcleos epiteliales: solo 35 objetos en TEST, AP50–95≈0.329. Cilindros: AP50–95≈0.384. El soporte desigual limita comparaciones por clase.
- Campos con más de 300 detecciones pueden truncarse; la aplicación muestra un aviso. Objetos pequeños, agrupaciones y contornos difíciles requieren revisión.
- Validación interna de un dataset. Generalización entre microscopios/laboratorios no establecida; no hay evaluación externa vigente ni estudio prospectivo/multicéntrico.
- La corrección humana permite rechazo y reclasificación. El registro de elementos omitidos no añade nuevas cajas al detector. La revisión se persiste mediante exportación.
- Confianza del modelo no calibrada como probabilidad clínica; interpretación orientativa por imagen.
- Código AGPL-3.0-only. El repositorio no redistribuye datasets ni pesos; el acceso y cualquier redistribución de material externo requieren sus autorizaciones correspondientes.
