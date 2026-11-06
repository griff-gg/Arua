# Builds every file a GitHub release needs, in installer\Output:
#   Arua-<VERSION>-Setup.exe          (what players download; the Companion's Update button runs it)
#   Arua-<VERSION>-arua_<theme>.zip    (the Companion's Themes tab downloads these)
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File installer\build_release.ps1
$ErrorActionPreference = 'Stop'
$out = Join-Path $PSScriptRoot 'Output'
if (Test-Path $out) { Remove-Item $out -Recurse -Force }
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'build_installer.ps1')
if ($LASTEXITCODE -ne 0) { throw 'setup build failed' }
python (Join-Path $PSScriptRoot '..\companion\tools\pack_themes.py') $out
if ($LASTEXITCODE -ne 0) { throw 'theme zips failed' }
Get-ChildItem $out | ForEach-Object { Write-Host ("{0}  {1:N0} MB" -f $_.Name, ($_.Length / 1MB)) }
