# Builds installer\Output\Arua-<VERSION>-Setup.exe: rebuilds the Companion, then compiles arua.iss.
# Needs Inno Setup 6 (https://jrsoftware.org/isdl.php).
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File installer\build_installer.ps1
$ErrorActionPreference = 'Stop'
$iscc = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
          "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw 'Inno Setup 6 not found: install it from https://jrsoftware.org/isdl.php' }
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot '..\companion\build_exe.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Companion build failed' }
& $iscc /Q (Join-Path $PSScriptRoot 'arua.iss')
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup failed' }
Get-ChildItem (Join-Path $PSScriptRoot 'Output') -Filter *.exe | ForEach-Object { Write-Host "built: $($_.FullName)" }
