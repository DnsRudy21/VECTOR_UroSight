# Estado del proyecto

Última actualización: 2026-09-07 (America/Mexico_City)

## Estado actual

**VECTOR UroSight 1.0.0 Academic Demo** es la versión fuente estable destinada a presentación académica. El modelo, la interfaz y el generador de reportes están congelados; no existen entrenamientos activos.

Este estado significa cierre técnico de la demo, no validación clínica. El sistema sigue siendo experimental y requiere confirmación visual profesional.

## Componentes congelados

| Componente | Estado |
|---|---|
| Modelo | YOLO11s, mejor checkpoint en época 13 de 15 |
| Dataset canónico original | 5,292 imágenes: 4,176 train / 848 validation / 268 test |
| Entrenamiento dirigido | 4,177 originales de train + 2,036 teselas generadas solo desde train |
| Inferencia | 448 px, aumento activado, umbral 0.443443 |
| UI | Flujo minimalista multimagen, temas claro/oscuro y configuración secundaria oculta |
| Exportaciones visibles | PDF adaptable, imágenes anotadas y estadísticas CSV |
| Pruebas | 44 aprobadas, 0 fallidas |
| Operación | Local y sin servicios remotos |

## Métricas finales

| Split | Precision | Recall | mAP@50 | mAP@50-95 |
|---|---:|---:|---:|---:|
| Validation interna | 0.825059 | 0.815430 | 0.867705 | 0.509357 |
| Test interno independiente | 0.808721 | 0.813571 | 0.854268 | 0.494546 |
| UMID externo | 0.5238 | 0.1199 | 0.0685 | 0.0348 |

El test interno se abrió después de congelar checkpoint, configuración y umbral. UMID demuestra un cambio de dominio severo; por ello no se hacen afirmaciones de generalización clínica.

## Integridad

- SHA-256 del modelo congelado: `C5FBA1AECCB60CA8EAC49C1750123A5DC85F22456F02F805F62FFF6386669530`.
- El repositorio público excluye pesos, datasets, imágenes, PDFs, ejecutables, secretos y resultados generados.
- El portable oficial se conserva fuera del árbol Git y no forma parte de la distribución pública.
- La redistribución del modelo o del portable requiere revisar de forma independiente las licencias de dependencias y pesos.

## Pendientes externos

- Publicar la rama estable en GitHub desde la cuenta del propietario.
- Solicitar revisión jurídica y regulatoria independiente antes de cualquier uso clínico o comercial.
- Realizar validación externa multicéntrica antes de formular afirmaciones de desempeño clínico.
