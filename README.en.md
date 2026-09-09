<div align="center">

<img src="assets/vector_urosight_icon.png" width="100" alt="VECTOR UroSight">

# VECTOR UroSight

### Visible microscopy. Local analysis. Human review.

[![CI](https://github.com/DnsRudy21/VECTOR_UroSight/actions/workflows/ci.yml/badge.svg)](https://github.com/DnsRudy21/VECTOR_UroSight/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![YOLO11s](https://img.shields.io/badge/YOLO11s-7_classes-0E7490)](docs/MODEL_CARD.md)
[![License](https://img.shields.io/badge/license-AGPL--3.0-15803D)](LICENSE)

**[Español](README.md) · [English](README.en.md)**

[Model and results](docs/MODEL_CARD.md) · [User guide](docs/USER_GUIDE.md) · [Contributing](CONTRIBUTING.md)

</div>

VECTOR UroSight is a desktop application for examining urinary sediment images, reviewing detections, and exporting results with visual evidence. Inference runs on the user's computer.

> [!IMPORTANT]
> **Experimental academic prototype.** Professional review is required; the application has not been clinically validated. Counts describe images, not calibrated clinical measurements per field.

![Current application in demonstration mode, without patient images or data](assets/interface-preview.png)

## From image to report

**Load images → Analyze → Review detections → Export results**

| 🔬 Examine | ✏️ Review | 📄 Export |
|:---|:---|:---|
| One image, multiple images, or a folder | Classes, confidence, and bounding boxes | PDF reports with visual evidence |
| Original and annotated views | Traceable human corrections | Annotated images and CSV |
| Seven particle classes | Quality and detection-limit warnings | Consolidated study results |

**Classes:** erythrocytes, leukocytes, epithelial cells, epithelial nuclei, casts, crystals, and yeast/fungi.

## Acknowledgments

### Cómplice Sistemas C.A. de C.V.

Special recognition to **[Cómplice Sistemas C.A. de C.V.](https://www.complise.mx/)** for its technical collaboration on this project, and especially to its General Director, **Eng. Alejandro Leal Cueva**.

### Universidad Tecnológica de Coahuila

Our thanks to **Universidad Tecnológica de Coahuila**, as part of the academic setting of this project.

## Results and limitations

The active model is **YOLO11s**, using **448 px** and test-time augmentation. The previous checkpoint remains active: the latest pilot did not improve the selection metric.

| Evaluation | Precision | Recall | mAP@50 | mAP@50–95 |
|:---|---:|---:|---:|---:|
| Internal validation, reproduced September 8, 2026 | 0.8251 | 0.8154 | 0.8677 | 0.5094 |
| Internal test, historical record | 0.8087 | 0.8136 | 0.8543 | 0.4945 |

Precision and recall refer to the evaluation's maximum-F1 operating point, not the interface's fixed confidence threshold. TEST was not evaluated again during the latest cycle.

Historical external UMID evaluation showed severe degradation (**0.0348 mAP@50–95**). This is a project-level historical result, not a new external evaluation of the current checkpoint. Generalization across laboratories and microscopes remains unverified.

Recent software changes corrected display labels, exports after human corrections, and saturation warnings. The Silver Review Pack was used only for synthetic functional checks, **never for training or clinical accuracy measurements**.

[Model card](docs/MODEL_CARD.md) · [Pilot comparison](docs/MODEL_COMPARISON.md) · [Experimental report](docs/MODEL_IMPROVEMENT_REPORT.md)

## Getting started

### 1. Install and run the demonstration

Requires **Python 3.11**. Run these commands in PowerShell from the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.main
```

Without local configuration, the application displays **simulated results**. This mode requires no model weights.

### 2. Enable real inference

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-local.txt
Copy-Item .env.example .env
```

Place a compatible, authorized checkpoint at `models/vector_urosight/best.pt` and edit `.env`:

```dotenv
INFERENCE_PROVIDER=local
LOCAL_MODEL_PATH=models/vector_urosight/best.pt
CONFIDENCE_THRESHOLD=0.443443
LOCAL_MODEL_IMGSZ=448
LOCAL_MODEL_AUGMENT=true
LOCAL_MODEL_MAX_DETECTIONS=300
```

Run `.\.venv\Scripts\python.exe -m src.main` again. Weights are not downloaded or distributed by this repository. Inference works offline once dependencies and weights are installed.

## Development and retraining

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m tools.publication_check
```

| Directory | Contents |
|:---|:---|
| `src/` | Application, inference, review, and exports |
| `tests/` | Domain, UI, and report tests |
| `tools/` | Data audits, evaluation, and training |
| `docs/` | User guide, architecture, model, and experiments |
| `assets/` | Icons and application preview |
| `scripts/` | Setup, execution, and packaging |

Datasets, private manifests, weights, and full experiment outputs remain local and excluded from Git. See the [retraining guide](docs/RETRAINING.md) for reuse without validation or test leakage.

## Credits and license

Conceived and directed by **Eng. José Carlos Malacara Espinosa**.

Source code is licensed under [GNU AGPL-3.0-only](LICENSE). Third-party licenses and attributions remain applicable. This repository excludes datasets, patient images, weights, and executables. See [third-party notices](THIRD_PARTY_NOTICES.md) and [security](SECURITY.md).
