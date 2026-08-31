# Arquitectura

```text
src/
├── main.py
├── config.py
├── domain/
├── inference/
├── processing/
├── interpretation/
├── reports/
├── services/
└── ui/
```

## Regla principal

Ninguna clase de interfaz importa directamente Ultralytics.

## Proveedores

- `MockInferenceProvider`
- `LocalYoloProvider`

Cada proveedor declara un nombre visible y si es simulado. El servicio transfiere esos metadatos al estudio; interfaz, PDF, CSV y JSON los consumen sin importar SDKs específicos.

`LocalYoloProvider` carga un checkpoint incluido o indicado por ruta local. La inferencia no requiere credenciales ni conexiones de red. `MockInferenceProvider` se limita al desarrollo y siempre se identifica como simulado.

## Flujo

GUI → servicio de análisis → proveedor → normalización → consolidación → reglas → visualización → exportaciones.

## Trazabilidad

El proveedor entrega detecciones neutrales. El procesamiento conserva la respuesta original por imagen, normaliza clases, valida confianza y geometría, ajusta cajas a los límites y aplica NMS por clase con IoU 0.50. El umbral pertenece al estudio y separa detecciones aceptadas de ocultas sin borrarlas de la representación interna.

## Calidad técnica

`processing/image_quality.py` calcula resolución, brillo medio, desviación estándar y varianza de bordes. Genera advertencias no bloqueantes y no se usa para interpretación clínica.
