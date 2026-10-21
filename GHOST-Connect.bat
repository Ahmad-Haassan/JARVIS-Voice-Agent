@echo off
title GHOST PC Client - Autonomous Desktop Agent
color 0b
cls

echo =====================================================================
echo              GHOST NEURAL PC CLIENT - SETUP & LAUNCH
echo =====================================================================
echo.
echo [*] Checking environment on your PC...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python was not detected in PATH.
    echo [*] Checking py launcher...
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Python 3.10+ is required to run GHOST on Windows.
        echo Please install Python from https://python.org/ (Check 'Add Python to PATH')
        echo.
        pause
        exit /b 1
    ) else (
        set PY_CMD=py
    )
) else (
    set PY_CMD=python
)

:: Virtual environment setup if needed
if not exist "venv\Scripts\python.exe" (
    echo [*] Setting up virtual environment...
    %PY_CMD% -m venv venv
    call venv\Scripts\activate.bat
    echo [*] Installing required lightweight dependencies...
    pip install fastapi uvicorn psutil pyautogui pywin32 requests
) else (
    call venv\Scripts\activate.bat
)

echo.
echo [*] Starting GHOST Desktop Server on your PC...
start "" /b venv\Scripts\python.exe server.py

timeout /t 2 /nobreak >nul

:: Detect Local IP
for /f "tokens=4" %%a in ('route print ^| findstr 0.0.0.0 ^| findstr /v "127.0.0.1" 2^>nul') do (
    set LOCAL_IP=%%a
    goto :ip_found
)
:ip_found

echo.
echo =====================================================================
echo        [+] GHOST IS ACTIVE & READY ON YOUR PC!
echo =====================================================================
echo.
echo >>> OPEN ON YOUR MOBILE PHONE (SAME WI-FI):
echo     http://%LOCAL_IP%:8000
echo.
echo >>> OR OPEN ON THIS PC:
echo     http://localhost:8000
echo.
echo =====================================================================
echo Keep this window open while using GHOST. Press Ctrl+C to stop.
echo =====================================================================
echo.

:: Automatically open browser
start http://localhost:8000

pause
