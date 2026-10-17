@echo off
title JARVIS Mobile Remote Server
echo ====================================================
echo    Starting JARVIS Mobile Remote Controller...
echo ====================================================
"%~dp0venv\Scripts\python.exe" "%~dp0server.py"
pause
