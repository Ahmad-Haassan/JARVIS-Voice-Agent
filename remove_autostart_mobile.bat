@echo off
title Remove JARVIS Mobile Autostart
echo ====================================================
echo   Removing JARVIS Mobile Server from Windows Startup
echo ====================================================
powershell -Command "Remove-Item -Path ([System.IO.Path]::Combine([Environment]::GetFolderPath('Startup'), 'JARVIS Mobile Server.lnk')) -ErrorAction SilentlyContinue"
echo [*] Removed from Windows Startup.
ping 127.0.0.1 -n 3 >nul
