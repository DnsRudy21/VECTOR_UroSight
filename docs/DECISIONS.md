# Decisiones de diseño

## Aplicación local y revisión humana

PySide6 implementa la interfaz. La inferencia corre en un hilo de Qt y cada imagen conserva su estado, errores y resultados. El proveedor simulado permite probar el flujo sin pesos y siempre se identifica como tal. No hay proveedor remoto.

## Trazabilidad de detecciones

Se conservan clase original, clase canónica, confianza, geometría, imagen y modelo. La normalización aplica NMS por clase a IoU 0.50. Las correcciones humanas afectan las salidas revisadas sin sobrescribir la predicción original. El identificador legado de `epithn` se mantiene por compatibilidad; su texto visible es «Núcleos epiteliales».

## Identidad y resultados

El identificador del estudio es local y el nombre del paciente es opcional. No hay expediente ni integración con un sistema clínico institucional. Los conteos se expresan por imagen, sin equivalencia clínica automática por campo.

## Datos y separación experimental

USE aporta siete clases; UMID se reserva para evaluación externa de las clases compatibles. Los duplicados exactos se resuelven con prioridad test → validación → train. Las cajas ajustadas conservan registro de coordenadas originales. Las fuentes no se modifican.

Los modelos e hiperparámetros se seleccionan en validación. TEST no interviene en el ajuste. Debido a las evaluaciones históricas del mismo test, nuevas afirmaciones de generalización requieren un conjunto externo adicional y congelado.

## Modelo vigente

YOLO11s a 448 px con TTA, umbral 0.44 y siete clases. La selección compara balance global y AP por clase sobre validación. La configuración se congela antes de TEST; parámetros, pesos y resultados verificables se registran en la [ficha del modelo](MODEL_CARD.md).

Silver se reserva a QA sintético. No se aplica mejora experimental de imagen. El límite de 300 detecciones conserva un aviso visible; no se interpreta como recuento clínico completo de campos extremos.

## Distribución

Se publica código fuente bajo AGPL-3.0-only con avisos de terceros. Datasets, imágenes clínicas, pesos, portables y resultados privados quedan fuera de Git. PySide6 6.8.3 se conserva por compatibilidad verificada del portable; actualizarlo requiere volver a probar la carga de QtWidgets en el ejecutable.

La distribución portable verifica sus pesos y mantiene fijos los parámetros de inferencia.
