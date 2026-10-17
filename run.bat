@echo off
title JARVIS Voice Assistant
echo ====================================================
echo      Starting JARVIS AI Voice Assistant...
echo ====================================================
call "%~dp0venv\Scripts\activate.bat"
python "%~dp0main.py"
pause
