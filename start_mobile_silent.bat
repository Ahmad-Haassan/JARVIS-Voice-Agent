@echo off
cd /d "%~dp0"
start "" "%~dp0venv\Scripts\pythonw.exe" "%~dp0server.py"
exit
