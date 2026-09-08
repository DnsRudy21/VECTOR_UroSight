param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Falló $Program (código $LASTEXITCODE). No se continúa." }
}

$pythonCommand = if (Test-Path -LiteralPath '.venv/Scripts/python.exe') { '.venv/Scripts/python.exe' } else { 'python' }
$branch = & git branch --show-current
if ($LASTEXITCODE -ne 0 -or $branch -ne 'main') { throw 'Publique desde main después de revisar e integrar sus cambios.' }
$remoteUrl = & git remote get-url --push origin
if ($LASTEXITCODE -ne 0 -or $remoteUrl -notin @('https://github.com/DnsRudy21/VECTOR_UroSight.git', 'git@github.com:DnsRudy21/VECTOR_UroSight.git')) {
    throw 'El destino no coincide con DnsRudy21/VECTOR_UroSight. Revise origin.'
}
Invoke-Checked $pythonCommand @('-m', 'tools.publication_check')
$env:QT_QPA_PLATFORM = 'offscreen'
Invoke-Checked $pythonCommand @('-m', 'pytest', '-q')
Invoke-Checked 'git' @('diff', '--check')
Invoke-Checked 'git' @('diff', '--cached', '--check')
if ($CheckOnly) { Write-Host 'Comprobaciones completadas. No se creó commit ni se publicó.'; exit 0 }

Invoke-Checked 'git' @('fetch', 'origin', 'main')
Invoke-Checked 'git' @('merge-base', '--is-ancestor', 'origin/main', 'HEAD')
Invoke-Checked 'git' @('add', '--all')
& git diff --cached --quiet
if ($LASTEXITCODE -eq 1) {
    Invoke-Checked 'git' @('commit', '-m', 'Prepare source release and update model evaluation documentation')
} elseif ($LASTEXITCODE -ne 0) { throw 'No se pudo inspeccionar el índice.' }
Invoke-Checked 'git' @('push', 'origin', 'main')
Write-Host 'Publicado: https://github.com/DnsRudy21/VECTOR_UroSight'
