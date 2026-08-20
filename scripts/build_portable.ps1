$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

python -m PyInstaller --noconfirm --clean --windowed `
  --name VECTOR_UroSight `
  --add-data "models/vector_urosight/best.pt;models/vector_urosight" `
  --collect-data ultralytics `
  --hidden-import cv2 `
  --exclude-module IPython `
  --exclude-module pytest `
  --exclude-module pandas `
  --exclude-module scipy `
  --exclude-module matplotlib `
  --exclude-module torchvision `
  --exclude-module torchaudio `
  --exclude-module tensorboard `
  --exclude-module pyarrow `
  --exclude-module openpyxl `
  --exclude-module sqlalchemy `
  --exclude-module tkinter `
  --exclude-module plotly `
  --exclude-module altair `
  src/main.py

Copy-Item -LiteralPath "README.md" -Destination "dist/VECTOR_UroSight/README.txt" -Force
Write-Host "Portable creado en dist/VECTOR_UroSight"
