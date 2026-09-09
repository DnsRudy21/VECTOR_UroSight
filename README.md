<div align="center">

<img src="assets/vector_urosight_icon.png" width="100" alt="VECTOR UroSight">

# VECTOR UroSight

### Microscopía visible. Análisis local. Revisión humana.

[![CI](https://github.com/DnsRudy21/VECTOR_UroSight/actions/workflows/ci.yml/badge.svg)](https://github.com/DnsRudy21/VECTOR_UroSight/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![YOLO11s](https://img.shields.io/badge/YOLO11s-7_classes-0E7490)](docs/MODEL_CARD.md)
[![License](https://img.shields.io/badge/license-AGPL--3.0-15803D)](LICENSE)

**[Español](README.md) · [English](README.en.md)**

[Modelo y resultados](docs/MODEL_CARD.md) · [Guía de uso](docs/USER_GUIDE.md) · [Desarrollo](CONTRIBUTING.md)

</div>

VECTOR UroSight es una aplicación de escritorio para explorar imágenes de sedimento urinario, revisar detecciones y exportar resultados con su evidencia visual. La inferencia se ejecuta en el equipo del usuario.

> [!IMPORTANT]
> **Prototipo académico experimental.** Requiere revisión profesional y no cuenta con validación clínica. Los conteos corresponden a imágenes, no a valores clínicos calibrados por campo.

![Interfaz real en modo demostración, sin imágenes ni datos de pacientes](assets/interface-preview.png)

<div align="center"><sub>Interfaz en modo demostración</sub></div>

## De la imagen al reporte

```mermaid
flowchart LR
    A["01 · Cargar imágenes"] --> B["02 · Analizar"]
    B --> C["03 · Revisar detecciones"]
    C --> D["04 · Exportar resultados"]
```

| 🔬 Examinar | ✏️ Revisar | 📄 Compartir |
|:---|:---|:---|
| Una imagen, varias o una carpeta | Clase, confianza y cajas por objeto | Reporte PDF con evidencia |
| Vista original y anotada | Correcciones humanas trazables | Imágenes anotadas y CSV |
| Siete clases de partículas | Avisos de calidad y límite de detecciones | Resultados consolidados por estudio |

**Clases:** eritrocitos · leucocitos · células epiteliales · núcleos epiteliales · cilindros · cristales · levaduras/hongos.

## Agradecimientos

### Cómplice Sistemas C.A. de C.V.

Un reconocimiento especial a **[Complise Sistemas S.A. de C.V.](https://www.complise.mx/)** por su colaboración técnica en este proyecto y, de manera destacada, a su director general, **Ing. Alejandro Leal Cueva**.

### Universidad Tecnológica de Coahuila

Agradecemos también a la **Universidad Tecnológica de Coahuila**, como parte del entorno académico en el que se desarrolla este proyecto.

## Metodología

| Fase | Desarrollo |
|:---|:---|
| Preparación de datos | Imágenes USE y anotaciones Pascal VOC, revisión de cajas y eliminación de duplicados entre particiones. |
| Entrenamiento | Transferencia de aprendizaje con YOLO11s para detectar siete clases de partículas. |
| Evaluación | Selección del modelo y umbral en validación; evaluación del modelo seleccionado en test. |
| Aplicación | Interfaz de escritorio con PySide6, inferencia local, revisión por imagen y exportación de resultados. |

## Resultados y límites

Modelo operativo **YOLO11s**, resolución **448 px** e inferencia aumentada.

| Evaluación | Precisión | Recall | mAP@50 | mAP@50–95 |
|:---|---:|---:|---:|---:|
| Validación interna | 0.8251 | 0.8154 | 0.8677 | 0.5094 |
| Test interno | 0.8087 | 0.8136 | 0.8543 | 0.4945 |

Precisión y recall son los del punto de máximo F1 de la evaluación; no representan conteos al umbral fijo de la interfaz.

La generalización a otros microscopios y laboratorios no está validada.

[Ficha técnica y evaluación del modelo](docs/MODEL_CARD.md)

## Empezar

### 1. Instalar y abrir la demostración

Requiere **Python 3.11**. Las siguientes instrucciones corresponden a Windows y PowerShell. Descargue el repositorio y abra su carpeta; si tiene Git instalado:

```powershell
git clone https://github.com/DnsRudy21/VECTOR_UroSight.git
cd VECTOR_UroSight
```

Cree un entorno e instale las dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.main
```

Sin configuración local, la aplicación muestra **resultados simulados**. Este modo permite explorar la interfaz y no necesita pesos.

### 2. Activar inferencia real

Instale las dependencias y prepare la configuración:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-local.txt
Copy-Item .env.example .env
```

Coloque un checkpoint compatible y autorizado en `models/vector_urosight/best.pt`. Edite `.env`:

```dotenv
INFERENCE_PROVIDER=local
LOCAL_MODEL_PATH=models/vector_urosight/best.pt
CONFIDENCE_THRESHOLD=0.443443
LOCAL_MODEL_IMGSZ=448
LOCAL_MODEL_AUGMENT=true
LOCAL_MODEL_MAX_DETECTIONS=300
```

Inicie de nuevo con `.\.venv\Scripts\python.exe -m src.main`. Los pesos no se descargan ni se incluyen en este repositorio. Una vez instaladas las dependencias y el modelo, la inferencia funciona sin Internet.

## Pruebas y estructura

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

| Carpeta | Contenido |
|:---|:---|
| `src/` | Aplicación, inferencia, revisión y exportación |
| `tests/` | Pruebas de dominio, interfaz y reportes |
| `tools/` | Auditoría de datos, evaluación y entrenamiento |
| `docs/` | Guía de uso, arquitectura, modelo y experimentos |
| `assets/` | Iconos y vista de la aplicación |
| `scripts/` | Instalación, ejecución y empaquetado |

La ejecución de inferencia real requiere obtener por separado un checkpoint compatible. El repositorio permite ejecutar la demostración y las pruebas sin disponer del modelo entrenado.

## Autoría y licencia

Proyecto concebido y dirigido por **Ing. José Carlos Malacara Espinosa**.

Código bajo [GNU AGPL-3.0-only](LICENSE). Se conservan las licencias y atribuciones de terceros. La publicación incluye el código fuente; no incluye datasets, imágenes de pacientes, pesos ni ejecutables. Consulte [avisos de terceros](THIRD_PARTY_NOTICES.md) y [seguridad](SECURITY.md).
