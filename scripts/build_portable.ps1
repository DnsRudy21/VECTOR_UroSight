$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

$modelPath = Join-Path $projectRoot "models/vector_urosight/final/best.pt"
$metadataPath = Join-Path $projectRoot "models/vector_urosight/final/model_metadata.json"
if (-not (Test-Path -LiteralPath $modelPath)) {
  throw "Falta models/vector_urosight/final/best.pt. Seleccione y congele el checkpoint antes de crear el portable."
}
if (-not (Test-Path -LiteralPath $metadataPath)) {
  throw "Falta la ficha de verificacion del modelo."
}
$modelMetadata = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json
if ($modelMetadata.approved_for_packaging -ne $true -or $modelMetadata.weights_sha256 -notmatch '^[a-fA-F0-9]{64}$') {
  throw "El modelo no tiene una aprobacion de empaquetado verificable."
}
$expectedHash = $modelMetadata.weights_sha256.ToLowerInvariant()
$actualHash = (Get-FileHash -LiteralPath $modelPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualHash -ne $expectedHash) {
  throw "El checkpoint no coincide con el modelo operativo aprobado. No se empaquetan pesos experimentales."
}
# Keep a separate local copy before replacing or moving any distribution.
$backupFolder = Join-Path $projectRoot "private/model_backups"
New-Item -ItemType Directory -Path $backupFolder -Force | Out-Null
$backupPath = Join-Path $backupFolder "$expectedHash.pt"
if (-not (Test-Path -LiteralPath $backupPath)) {
  Copy-Item -LiteralPath $modelPath -Destination $backupPath
}
if ((Get-FileHash -LiteralPath $backupPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) {
  throw "No se pudo verificar el respaldo del modelo."
}

python -m PyInstaller --noconfirm --clean --windowed `
  --name VECTOR_UroSight `
  --icon "assets/vector_urosight_icon.ico" `
  --add-data "models/vector_urosight/final/best.pt;models/vector_urosight/final" `
  --add-data "models/vector_urosight/final/model_metadata.json;models/vector_urosight/final" `
  --add-data "models/vector_urosight/final/evaluation_config.json;models/vector_urosight/final" `
  --add-data "assets/vector_urosight_icon.png;assets" `
  --collect-data ultralytics `
  --collect-all matplotlib `
  --collect-all torchvision `
  --hidden-import cv2 `
  --exclude-module IPython `
  --exclude-module pytest `
  --exclude-module pandas `
  --exclude-module torchaudio `
  --exclude-module tensorboard `
  --exclude-module pyarrow `
  --exclude-module openpyxl `
  --exclude-module sqlalchemy `
  --exclude-module tkinter `
  --exclude-module plotly `
  --exclude-module altair `
  src/main.py

if ($LASTEXITCODE -ne 0) { throw "PyInstaller no pudo crear el portable." }
foreach ($notice in @("LICENSE", "COPYRIGHT", "THIRD_PARTY_NOTICES.md")) {
  Copy-Item -LiteralPath $notice -Destination "dist/VECTOR_UroSight/$notice" -Force
}
@"
VECTOR UroSight

Abra VECTOR_UroSight.exe. No necesita instalar Python.
Mantenga el ejecutable y la carpeta _internal juntos.

Seleccione archivos, seleccione una carpeta o arrastre las imagenes a la ventana.
Pulse Analizar estudio, revise las detecciones y use Exportar resultados para
guardar un PDF, imagenes anotadas, estadisticas CSV o una sesion JSON.

El procesamiento es local. Prototipo academico sin validacion clinica.
Revise los resultados con un profesional antes de interpretarlos.
"@ | Set-Content -LiteralPath "dist/VECTOR_UroSight/LEEME.txt" -Encoding UTF8
Write-Host "Portable creado en dist/VECTOR_UroSight"
