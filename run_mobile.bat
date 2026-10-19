@echo off
title JARVIS Mobile Remote Server
echo ====================================================
echo    Starting JARVIS Mobile Remote Controller...
echo ====================================================
call "%~dp0stop_mobile.bat" >nul 2>&1
"%~dp0venv\Scripts\python.exe" "%~dp0server.py"
pause
