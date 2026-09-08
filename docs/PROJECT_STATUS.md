# Estado del proyecto

Última actualización: 2026-09-08 (America/Mexico_City)

## Estado actual

**VECTOR UroSight 1.0.0 Academic Demo** conserva el modelo operativo anterior. El ciclo Silver Review corrigió presentación, selección de umbrales, revisión/PDF y visibilidad de saturación en el código fuente. El piloto de fine-tuning terminó y fue rechazado por deterioro de mAP50–95 global y en cast, mycete y epithn; no existen entrenamientos activos. No se abrió TEST ni se sustituyeron pesos en este ciclo.

Este estado significa cierre técnico de la demo, no validación clínica. El sistema sigue siendo experimental y requiere confirmación visual profesional.

## Componentes actuales

| Componente | Estado |
|---|---|
| Modelo | YOLO11s, mejor checkpoint en época 13 de 15 |
| Derivado USE reconstruido en esta auditoría | 5,293 imágenes: 4,177 train / 848 validation / 268 test |
| Entrenamiento dirigido | 4,177 originales de train + 2,036 teselas generadas solo desde train |
| Inferencia | 448 px, aumento activado, default 0.44; referencia histórica de curva 0.443443; máximo 300 detecciones |
| UI | Flujo minimalista multimagen, temas claro/oscuro y configuración secundaria oculta |
| Exportaciones visibles | PDF adaptable, imágenes anotadas y estadísticas CSV |
| Pruebas | 60 aprobadas, 0 fallidas, incluida la protección de publicación |
| Operación | Local y sin servicios remotos |

## Métricas finales

| Split | Precision | Recall | mAP@50 | mAP@50-95 |
|---|---:|---:|---:|---:|
| Validation interna | 0.825059 | 0.815430 | 0.867705 | 0.509357 |
| Test interno independiente | 0.808721 | 0.813571 | 0.854268 | 0.494546 |

El test interno se abrió después de congelar checkpoint, configuración y umbral. El antecedente externo UMID del proyecto (mAP50–95 0.0348) documenta cambio de dominio, pero no acredita una evaluación externa del checkpoint actual.

Validation fue reproducida en este ciclo. TEST es un registro histórico,
no una nueva evaluación. El candidato obtuvo mAP50–95 0.505667 en validation frente
a 0.509357 del baseline. El QA sintético pasó de 31 a 33 coincidencias de presencia,
pero mantuvo las 10 omisiones cast y las 5 mycete; no es evidencia clínica.
Detalles y artefactos: `SILVER_REVIEW_DIAGNOSIS.md`, `HARD_CASE_ANNOTATION_AUDIT.md`
y `MODEL_IMPROVEMENT_REPORT.md`. El ejecutable portátil no se reconstruyó; las
correcciones de interfaz/exportación corresponden al código fuente de este checkout.

## Integridad

- SHA-256 del modelo congelado: `C5FBA1AECCB60CA8EAC49C1750123A5DC85F22456F02F805F62FFF6386669530`.
- El repositorio público excluye pesos, datasets, imágenes, PDFs, ejecutables, secretos y resultados generados.
- El portable oficial se conserva fuera del árbol Git y no forma parte de la distribución pública.
- La redistribución del modelo o del portable requiere revisar de forma independiente las licencias de dependencias y pesos.

## Pendientes externos

- Publicar la rama estable en GitHub desde la cuenta del propietario.
- Solicitar revisión jurídica y regulatoria independiente antes de cualquier uso clínico o comercial.
- Realizar validación externa multicéntrica antes de formular afirmaciones de desempeño clínico.
