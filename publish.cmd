@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\publish.ps1" %*
if errorlevel 1 (
  echo No se pudo completar la publicacion. Revise el mensaje anterior.
)
pause
