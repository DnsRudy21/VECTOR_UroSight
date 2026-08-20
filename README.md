<div align="center">

# VECTOR UroSight

### Análisis trazable de imágenes de sedimento urinario

![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt&logoColor=white)
![Tests](https://img.shields.io/badge/tests-49%20passed-2EA44F)
![License](https://img.shields.io/badge/license-AGPL--3.0-blue)
![Status](https://img.shields.io/badge/status-academic%20prototype-orange)

**[Español](#español)** · **[English](#english)** · [Arquitectura](docs/ARCHITECTURE.md) · [Model Card](docs/MODEL_CARD.md) · [Seguridad](SECURITY.md)

</div>

> [!IMPORTANT]
> VECTOR UroSight es un prototipo académico experimental. **No es un dispositivo médico, no está clínicamente validado y no sustituye la revisión de profesionales del laboratorio.**

---

## Español

### Visión general

VECTOR UroSight es una aplicación de escritorio para apoyar la revisión humana de imágenes microscópicas de sedimento urinario. Detecta elementos visibles, conserva la evidencia de cada predicción, permite corregir resultados y genera reportes auditables en PDF, CSV y JSON.

El diseño sigue una idea central: toda salida automatizada debe ser **revisable, explicable y reversible**.

### Capacidades

| Área | Funcionalidad |
|---|---|
| Interfaz | Flujo multimagen en PySide6, arrastrar y soltar, filtros y revisión visual |
| Inferencia | Proveedor de demostración, Roboflow REST y YOLO local intercambiables |
| Trazabilidad | Clase original y normalizada, confianza, caja, modelo, umbral e imagen fuente |
| Revisión humana | Marcar detecciones correctas, incorrectas, clase equivocada o elementos omitidos |
| Calidad | Alertas técnicas de brillo, contraste y nitidez sin emitir conclusiones clínicas |
| Reportes | PDF profesional y exportaciones estructuradas CSV/JSON |
| Arquitectura | GUI, dominio, inferencia, reglas, procesamiento y reportes desacoplados |

### Flujo técnico

```mermaid
flowchart LR
    A["Imágenes microscópicas"] --> B["Interfaz PySide6"]
    B --> C["Servicio de análisis"]
    C --> D{"Proveedor de inferencia"}
    D --> E["Mock"]
    D --> F["Roboflow REST"]
    D --> G["YOLO local"]
    C --> H["Normalización y reglas auditables"]
    H --> I["Revisión humana"]
    I --> J["PDF · CSV · JSON"]
```

### Resultados experimentales

El checkpoint final es YOLO11n, entrenado a 320 px durante 30 épocas. El umbral 0.25 fue seleccionado exclusivamente sobre validación.

| Evaluación | Precision | Recall | mAP@50 | mAP@50–95 |
|---|---:|---:|---:|---:|
| Test interno USE | 0.7811 | 0.7476 | 0.7526 | 0.4293 |
| Evaluación externa UMID | 0.5238 | 0.1199 | 0.0685 | 0.0348 |

La caída en UMID muestra un **cambio de dominio severo**. Estas métricas describen un experimento reproducible; no demuestran desempeño clínico ni generalización a otros laboratorios, microscopios o protocolos.

### Inicio rápido

#### Requisitos

- Python 3.11
- Windows, Linux o macOS
- Entorno virtual recomendado

```bash
python -m venv .venv
```

Active el entorno e instale el modo de demostración:

```bash
python -m pip install -r requirements.txt
python -m src.main
```

#### Modelo YOLO local

Los pesos no se distribuyen en el repositorio. Instale las dependencias opcionales, copie `.env.example` como `.env` y configure una ruta local compatible:

```bash
python -m pip install -r requirements-local.txt
```

```dotenv
INFERENCE_PROVIDER=local
LOCAL_MODEL_PATH=models/vector_urosight/best.pt
CONFIDENCE_THRESHOLD=0.25
```

#### Roboflow REST

```bash
python -m pip install -r requirements-roboflow.txt
```

Configure `INFERENCE_PROVIDER=roboflow`, `ROBOFLOW_API_KEY` y `ROBOFLOW_MODEL_ID` únicamente en `.env`. Nunca publique ese archivo.

### Pruebas

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

La versión candidata pasa **49 pruebas automatizadas**. El flujo de integración continua repite la suite en Python 3.11 para cada `push` y `pull request`.

### Datos, privacidad y artefactos

- No se incluyen datasets, imágenes microscópicas, anotaciones, pesos, credenciales ni resultados generados.
- USE y UMID se mencionan únicamente para documentar procedencia experimental; deben obtenerse desde fuentes autorizadas.
- No use información identificable sin autorización institucional, controles de acceso y salvaguardas aplicables.
- La aplicación no es un expediente clínico electrónico ni un LIS.

### Estructura

```text
src/
├── domain/          # Entidades y trazabilidad
├── inference/       # Proveedores desacoplados
├── interpretation/  # Reglas explícitas
├── processing/      # Calidad y normalización
├── reports/         # Generación de reportes
├── services/        # Casos de uso
└── ui/              # Interfaz PySide6

tests/               # Suite automatizada
tools/               # Auditoría, datasets y evaluación
docs/                # Arquitectura, decisiones y evidencia
```

### Documentación

- [Visión del producto](docs/PRODUCT_VISION.md)
- [Arquitectura](docs/ARCHITECTURE.md)
- [Criterios de aceptación](docs/ACCEPTANCE_CRITERIA.md)
- [Model Card](docs/MODEL_CARD.md)
- [Auditoría final de calidad](docs/QUALITY_AUDIT_FINAL.md)
- [Análisis de errores](docs/ERROR_ANALYSIS.md)
- [Avisos de terceros](THIRD_PARTY_NOTICES.md)

### Autoría, desarrollo y licencia

Proyecto de maestría concebido y dirigido por **Ing. José Carlos Malacara Espinosa**, desarrollado con la colaboración y apoyo técnico de **Cómplices Sistemas**, con agradecimiento especial a la **Universidad Tecnológica de Coahuila**.

El proyecto siguió un enfoque de *vibe coding* responsable: desarrollo iterativo asistido por herramientas de IA, con dirección, revisión, pruebas y validación humana.

El código se publica bajo [GNU AGPL-3.0](LICENSE). La integración opcional con Ultralytics requiere conservar las obligaciones de AGPL-3.0 o contar con una licencia comercial aplicable. PySide6/Qt y las demás dependencias mantienen sus propias licencias. Consulte [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

---

## English

### Overview

VECTOR UroSight is an academic desktop prototype for human-supervised review of urinary sediment microscopy images. It detects visible elements, preserves prediction provenance, supports manual corrections, and produces auditable PDF, CSV, and JSON reports.

Its core principle is simple: automated output must remain **reviewable, explainable, and reversible**.

### Key features

- Multi-image PySide6 workflow with visual review and filtering.
- Interchangeable mock, Roboflow REST, and local YOLO providers.
- Traceability for raw/normalized class, confidence, box, model, threshold, and source image.
- Human review for incorrect classes, rejected detections, and omitted elements.
- Explicit rules and technical image-quality warnings.
- Structured PDF, CSV, and JSON exports.
- Modular architecture with 49 automated tests and GitHub Actions CI.

### Experimental status

| Evaluation | Precision | Recall | mAP@50 | mAP@50–95 |
|---|---:|---:|---:|---:|
| Internal USE test | 0.7811 | 0.7476 | 0.7526 | 0.4293 |
| External UMID evaluation | 0.5238 | 0.1199 | 0.0685 | 0.0348 |

The external result shows severe domain shift. VECTOR UroSight is **not a diagnostic device, is not clinically validated, and must not replace professional laboratory review**.

### Quick start

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python -m src.main
```

Local YOLO and Roboflow support are optional; see the Spanish setup sections above. Datasets, model weights, credentials, clinical images, and generated artifacts are intentionally excluded.

### License and attribution

Copyright © 2026 José Carlos Malacara Espinosa. Released under [GNU AGPL-3.0](LICENSE). Third-party components remain subject to their respective terms; see [Third-party notices](THIRD_PARTY_NOTICES.md).

---

<div align="center">

**Investigación reproducible · Supervisión humana · Trazabilidad por diseño**

</div>
