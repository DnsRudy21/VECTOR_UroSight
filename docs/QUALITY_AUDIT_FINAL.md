# Auditoría final de calidad

Fecha: 2026-08-19

## Conclusión

El flujo local es reproducible y estable en el equipo auditado, pero el detector no está cerca de 100 % de confiabilidad clínica. La diferencia entre test interno y UMID externo demuestra un cambio de dominio severo. No es responsable ajustar repetidamente el mismo conjunto hasta maximizar sus resultados: produciría sobreajuste sin evidencia de generalización.

## Exactitud observada

| Evaluación | Precisión | Recall | mAP@50 | mAP@50–95 |
|---|---:|---:|---:|---:|
| Test interno USE | 0.7811 | 0.7476 | 0.7526 | 0.4293 |
| Externo UMID | 0.5238 | 0.1199 | 0.0685 | 0.0348 |

En el análisis interno a IoU 0.50 se observaron 1,415 verdaderos positivos, 545 falsos positivos, 241 falsos negativos y 36 confusiones de clase. `cast` y `epithn` permanecen entre las clases débiles documentadas.

## Puerta operativa reproducible

Se procesaron las mismas seis imágenes durante tres rondas con el checkpoint SHA-256 `693e2a1b90601c962f1f83c88ba655a0cb55e974a5d084a0d229b703d6faa02f` y umbral 0.25.

- 18 solicitudes, cero errores.
- Huellas de detección idénticas entre rondas.
- Mediana 44.0 ms; p95 49.9 ms.
- Máximo 3172.6 ms por carga fría inicial del modelo.

Esto verifica constancia técnica, no sensibilidad clínica.

## Criterio para seguir mejorando

La siguiente iteración útil requiere imágenes del microscopio y preparación reales del laboratorio objetivo, anotadas y conciliadas por especialistas. Debe congelarse un conjunto externo antes de ajustar modelo o umbral y reportar métricas por clase con intervalos de confianza. Hasta entonces, la revisión humana y el registro de omisiones/correcciones son obligatorios para uso experimental supervisado.
