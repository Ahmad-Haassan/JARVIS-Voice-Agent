@echo off
title JARVIS AI Assistant & Mobile Server
echo ====================================================
echo      Starting JARVIS AI Voice Assistant...
echo ====================================================

:: Start Mobile Remote Server in background if not already active
netstat -ano | findstr :8000 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [*] Starting Mobile Remote Server on port 8000...
    start "" /B "%~dp0venv\Scripts\python.exe" "%~dp0server.py"
)

echo [*] Launching Desktop Voice Assistant GUI...
"%~dp0venv\Scripts\python.exe" "%~dp0main.py"
pause
