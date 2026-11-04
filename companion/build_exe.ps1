# Builds "Arua Companion" (one-folder app) and copies it to game-folder\Arua Companion\.
# Run from anywhere: powershell -NoProfile -ExecutionPolicy Bypass -File companion\build_exe.ps1
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
python -m PyInstaller --noconfirm --clean --onedir --windowed --name "Arua Companion" `
    --add-data "ui;ui" --collect-submodules webview --exclude-module cryptography run_companion.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed' }
Copy-Item "data\items.json" "dist\Arua Companion\items.json" -Force
$dest = Join-Path (Split-Path $PSScriptRoot -Parent) 'game-folder\Arua Companion'
if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
Copy-Item "dist\Arua Companion" $dest -Recurse
Write-Host "built: $dest"
