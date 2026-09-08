# Análisis de errores

## Modelo operativo

La revisión actual usa las 848 imágenes reales de validación a 448 px. Los errores prioritarios afectan cilindros, agrupaciones de levaduras/hongos, núcleos pequeños y campos densos. Consulte el [diagnóstico por clase](SILVER_REVIEW_DIAGNOSIS.md) y la [auditoría de anotaciones](HARD_CASE_ANNOTATION_AUDIT.md).

## Método

Las comparaciones a confianza 0.44 emparejan cajas uno a uno, por clase, con IoU ≥ 0.50. Una confusión de clase contribuye a un falso positivo y un falso negativo. Se distinguen las predicciones del detector de la NMS adicional de la aplicación.

La NMS de la aplicación eliminó 144 cajas en validación: 135 falsos positivos y 9 verdaderos positivos. Dos campos alcanzaron el límite de salida del detector; elevarlo recuperó objetos y también aumentó falsos positivos. El límite permanece en 300 con aviso visible.

Las confusiones directas eritrocito → leucocito fueron 14 con el modelo operativo y 12 con el candidato; en sentido contrario, 1 y 2. El piloto perdió AP50–95 global y en las tres clases prioritarias, por lo que se conserva el modelo operativo.

## Próxima revisión

Examinar con especialistas los 99 campos reales seleccionados exclusivamente desde train, preservando imagen, XML, cajas, clase original y motivo. No tratarlos como errores confirmados ni cambiar automáticamente etiquetas por discrepancia con el detector.

Las cifras completas y los límites del QA sintético están en el [informe experimental](MODEL_IMPROVEMENT_REPORT.md). Los resultados de TEST de versiones previas permanecen en el historial y no se reutilizan para ajustar el modelo.
