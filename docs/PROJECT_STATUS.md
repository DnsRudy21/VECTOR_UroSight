# VECTOR UroSight — Project Status

Última actualización: 2026-08-20 (America/Mexico_City)

Progreso global técnico: 100 %

ETA técnico: completado. Árbol fuente preparado para el primer commit y publicación en GitHub.

Estado: CIERRE TÉCNICO COMPLETADO; CANDIDATO FUENTE PREPARADO PARA PUBLICACIÓN

Fase actual: repositorio público mínimo y verificable

Tarea actual: ninguna tarea técnica local pendiente

Última tarea completada: identidad de paciente, puerta operativa, PDF final y empaquetado portable

Siguiente tarea externa: crear el repositorio remoto y publicar desde la cuenta del propietario

## Progreso por área

| Área | Peso | Avance interno | Contribución |
|------|------|----------------|--------------|
| Auditoría | 10% | 100% | 10.0% |
| Dataset | 15% | 100% | 15.0% |
| Entrenamiento | 25% | 100% | 25.0% |
| Evaluación | 15% | 100% | 15.0% |
| Integración | 10% | 100% | 10.0% |
| UI / reportes | 10% | 100% | 10.0% |
| Pruebas | 7% | 100% | 7.0% |
| Documentación | 5% | 100% | 5.0% |
| GitHub | 3% | 100% | 3.0% |

TOTAL técnico: 100 %. La publicación remota permanece como acción externa del propietario.

El porcentaje representa completitud técnica, no desempeño clínico. El sistema no está clínicamente validado.

## Completado

- Arquitectura modular PySide6 con proveedores mock, Roboflow REST y adaptador Local YOLO.
- Flujo multimagen, revisión humana, reglas explícitas y exportación PDF/CSV/JSON.
- Suite ejecutada el 2026-08-17: 46 passed, 0 failed, 0 skipped en 7.47 s.
- Inventario inicial de fuentes: USE en Pascal VOC y UMID convertido a YOLO.
- Hardware verificado: Python 3.11.9, PyTorch 2.12.1+cpu, CUDA no disponible.
- Ontología inicial sustentada por README y etiquetas reales de las fuentes, incluidos conteos por clase de UMID.
- Auditoría reproducible con SHA-256: 26 grupos duplicados cruzaban splits USE; UMID no presentó fuga exacta entre splits.
- Dataset maestro USE: 5,292 imágenes, 41,695 objetos, splits 4,176/848/268 y siete clases.
- Validación del derivado: cero hashes cruzados entre splits y cero etiquetas YOLO inválidas.
- Corrida de medición YOLO11n a 320 px: 84 imágenes en 11.4 s; validación de 848 imágenes en 26.1 s.
- Primera época completa del baseline: 7 min 43 s de entrenamiento y 36.3 s de validación; mAP@50 de validación 0.299 y mAP@50–95 0.137 (resultado temprano, no final).
- Segunda época: precision 0.529, recall 0.534, mAP@50 0.515 y mAP@50–95 0.256 sobre validación; la época 3 está en ejecución.
- Tercera época: precision 0.564, recall 0.581, mAP@50 0.583 y mAP@50–95 0.304 sobre validación; la época 4 está en ejecución.
- Cuarta época sin mejora: precision 0.546, recall 0.548, mAP@50 0.557 y mAP@50–95 0.286. `best.pt` permanece en época 3; época 5 en ejecución.
- Quinta época, nuevo mejor checkpoint: precision 0.609, recall 0.622, mAP@50 0.624 y mAP@50–95 0.326; época 6 en ejecución.
- Sexta época, nuevo mejor checkpoint: precision 0.650, recall 0.620, mAP@50 0.634 y mAP@50–95 0.333.
- Séptima época, nuevo mejor checkpoint: precision 0.648, recall 0.655, mAP@50 0.674 y mAP@50–95 0.357; época 8 en ejecución.
- El arranque muestra un error controlado si el proveedor configurado no puede inicializarse.
- Herramientas probadas para evaluación final y empaquetado sin sobrescritura del checkpoint.
- Model card provisional, flujo reproducible y exclusiones de datos/pesos documentados.
- UMID externo preparado sin usarlo para ajuste: 363 imágenes, 2,979 objetos de las tres clases compartidas y tres imágenes sin anotación excluidas.
- Entrenamiento YOLO11n completado: 30 épocas; mejor checkpoint en época 30.
- Umbral 0.25 seleccionado solo en validación por máximo F1 global.
- Test interno usado una sola vez: precision 0.7811, recall 0.7476, mAP@50 0.7526 y mAP@50–95 0.4293.
- UMID externo: precision 0.5238, recall 0.1199, mAP@50 0.0685 y mAP@50–95 0.0348; domain shift severo documentado.
- Análisis de error: 1,415 TP, 545 FP, 241 FN y 36 confusiones de clase a IoU 0.50.
- Modelo local real probado; 12 ejemplos renderizados y captura visual offscreen generados.
- Suite final: 49 passed. Verificador de liberación aprobado y escaneo activo de rutas/secretos limpio.
- Identidad transitoria de paciente añadida a la GUI y a PDF/CSV/JSON, con ID automático por nueva selección.
- Puerta operativa final: 18 inferencias (6 imágenes × 3 rondas), cero fallos y resultados deterministas; mediana 44.0 ms, p95 49.9 ms, máximo 3172.6 ms incluyendo carga fría.
- PDF final generado con seis imágenes reales del conjunto de demostración, 165 detecciones aceptadas y leyenda dinámica; cinco páginas renderizadas e inspeccionadas.
- Portable Windows x64 configurado con modelo local congelado y sin secretos; la redistribución pública de pesos continúa sujeta a confirmación de licencia.
- Suite completa ejecutada el 2026-08-20: 49 passed, 0 failed, 0 skipped.
- Instalación editable y construcción de wheel verificadas; metadatos CFF/YAML válidos y enlaces locales del README íntegros.
- Auditoría de dependencias base, local, Roboflow, auditoría y build: cero vulnerabilidades conocidas reportadas por `pip-audit`.
- CI de GitHub, plantillas de colaboración, citación y documentación bilingüe preparados.

## En ejecución

- Ninguna tarea técnica local.

## Pendiente externo

- Crear el repositorio remoto y publicar bajo AGPL-3.0 desde la cuenta del propietario.
- Solicitar revisión jurídica independiente antes de cualquier uso comercial o clínico.

## Material excluido del repositorio público

- Datasets USE/UMID, derivados, imágenes y anotaciones.
- Pesos entrenados, checkpoints y modelos preentrenados.
- Artefactos de entrenamiento/evaluación, PDFs, portables y compilaciones.
- Credenciales, `.env`, cachés y rutas locales.

La baja generalización externa sigue bloqueando cualquier afirmación clínica, no la publicación académica del código fuente.

## Evidencia de datos disponible

- USE: 5,391 archivos de imagen, 5,376 XML; splits declarados 4,256/852/268; 42,235 objetos reportados en siete clases, con 12 cajas inválidas.
- UMID derivado YOLO: 366 imágenes y 363 etiquetas; splits 268/38/60; 2,979 líneas de objeto (2,097/362/520) en tres clases.
- El antiguo resumen combinado contabiliza originales y derivados juntos. Sus duplicados combinados no constituyen por sí solos evidencia de fuga entre splits.
