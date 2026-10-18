@echo off
title JARVIS Mobile Autostart Setup
echo ====================================================
echo    Adding JARVIS Mobile Server to Windows Startup
echo ====================================================
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([System.IO.Path]::Combine([Environment]::GetFolderPath('Startup'), 'JARVIS Mobile Server.lnk')); $s.TargetPath = '%~dp0start_mobile_silent.vbs'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'JARVIS Mobile Remote Silent Server'; $s.Save()"
echo [*] Starting silent background server now...
wscript.exe "%~dp0start_mobile_silent.vbs"

echo [*] Success! JARVIS Mobile Server is now ACTIVE and set to start on PC boot.
echo [*] You will NEVER need to open a terminal window again.
ping 127.0.0.1 -n 4 >nul
