@echo off
rem Arua Loot Filter - edit loot_filter.txt in this folder, save it, then double-click this file.
rem It writes the glow / beam rules into the Arua themes. Restart the game afterwards.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0arua_loot_filter.ps1" -GameDir "%~dp0."
echo.
pause
