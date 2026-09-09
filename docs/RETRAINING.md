# Reentrenamiento y conservación de evidencia

El modelo vigente se identifica en [MODEL_CARD.md](MODEL_CARD.md). Su reemplazo exige mejorar la validación real con el mismo método y revisar las clases prioritarias. Los 99 campos seleccionados son candidatos de revisión, no una garantía de mejora.

## Preparación

Instale Python 3.11 y `requirements-local.txt` más `requirements-audit.txt`. Obtenga cada dataset desde una fuente autorizada y conserve su licencia, versión y procedencia. El repositorio no concede permiso para redistribuir USE, UMID ni sus derivados.

Las herramientas aceptan rutas explícitas; consulte sus opciones antes de ejecutarlas:

```powershell
python -m tools.dataset_audit --help
python -m tools.build_vector_dataset --help
python -m tools.mine_real_hard_cases --help
python -m tools.targeted_finetune --help
python -m tools.evaluate_model --help
python -m tools.validation_experiments --help
```

`dataset_audit` solicita ambas fuentes, USE y UMID. Si UMID no está disponible, no invente su ruta ni sustituya esa evaluación por USE. La auditoría USE también puede ejecutarse con la función `audit_voc` de la herramienta.

## Protocolo del siguiente experimento

1. Revisar las anotaciones prioritarias con especialistas y registrar cada cambio, sin modificar los originales.
2. Preservar la separación por fuente y split; comprobar duplicados antes de entrenar.
3. Formular una hipótesis por experimento: muestreo, escala, augmentations o límite de detecciones. Registrar semilla, exposición de objetos y hash del checkpoint inicial.
4. Comparar con el modelo operativo sobre las mismas imágenes de validación y con idéntica inferencia. Separar AP de las métricas a umbral fijo.
5. Revisar AP por clase, omisiones, falsos positivos y localización. No promover por mejora del score sintético o del recall aislado.
6. Congelar el candidato antes de cualquier evaluación final. Para nuevas afirmaciones de generalización, obtener un conjunto externo adicional que no haya participado en las decisiones históricas.

El piloto de tres épocas documentado perdió mAP50–95. Repetirlo sin cambiar una hipótesis ni mejorar anotaciones no constituye una estrategia demostrada de mejora. Consulte [la comparación](MODEL_COMPARISON.md) y [el informe](MODEL_IMPROVEMENT_REPORT.md).
