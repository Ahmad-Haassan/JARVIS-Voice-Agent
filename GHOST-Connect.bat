@echo off
title GHOST PC Client - Autonomous Desktop Agent
color 0b
cls

echo =====================================================================
echo              GHOST NEURAL PC CLIENT - SETUP & LAUNCH
echo =====================================================================
echo.

:: Ensure we are running inside a clean dedicated directory
set "ROOT_DIR=%USERPROFILE%\GHOST-Agent"
if not exist "%ROOT_DIR%" mkdir "%ROOT_DIR%"
cd /d "%ROOT_DIR%"

:: Check if server.py exists, if not, automatically download GHOST files from GitHub
if not exist "server.py" (
    echo [*] First-time setup detected.
    echo [*] Downloading GHOST core files from GitHub to %ROOT_DIR%...
    curl -L -s https://github.com/Ahmad-Haassan/ghost/archive/refs/heads/main.zip -o ghost_core.zip
    if exist ghost_core.zip (
        echo [*] Extracting core files...
        tar -xf ghost_core.zip --strip-components=1
        del /f /q ghost_core.zip >nul 2>&1
    ) else (
        echo [ERROR] Failed to download GHOST core files. Please check your internet connection.
        pause
        exit /b 1
    )
)

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo [!] Python was not detected on this computer.
        echo [*] GHOST requires Python 3.10+ on Windows.
        echo Opening Python download page...
        start https://www.python.org/downloads/
        echo.
        echo Please install Python (Make sure to check 'Add Python to PATH' during install).
        echo Then double-click GHOST-Connect.bat again!
        echo.
        pause
        exit /b 1
    ) else (
        set PY_CMD=py
    )
) else (
    set PY_CMD=python
)

:: Create virtual environment if missing
if not exist "venv\Scripts\python.exe" (
    echo [*] Setting up virtual environment (one-time setup, please wait)...
    %PY_CMD% -m venv venv
    if %errorlevel% neq 0 (
        echo [!] Could not create venv. Running with global Python...
        set "RUN_PY=%PY_CMD%"
    ) else (
        set "RUN_PY=venv\Scripts\python.exe"
    )
    echo [*] Installing required lightweight packages...
    %RUN_PY% -m pip install --upgrade pip >nul 2>&1
    %RUN_PY% -m pip install fastapi uvicorn psutil pyautogui pywin32 requests python-multipart
) else (
    set "RUN_PY=venv\Scripts\python.exe"
)

echo.
echo [*] Starting GHOST Desktop Server on this PC...
start "" /b %RUN_PY% server.py

timeout /t 2 /nobreak >nul

:: Detect Local IP
set "LOCAL_IP=127.0.0.1"
for /f "tokens=4" %%a in ('route print ^| findstr 0.0.0.0 ^| findstr /v "127.0.0.1" 2^>nul') do (
    set "LOCAL_IP=%%a"
    goto :ip_found
)
:ip_found

echo.
echo =====================================================================
echo        [+] GHOST IS ACTIVE & READY ON YOUR PC!
echo =====================================================================
echo.
echo >>> TO CONTROL FROM YOUR PHONE (SAME WI-FI):
echo     http://%LOCAL_IP%:8000
echo.
echo >>> OPENING GHOST DASHBOARD ON THIS PC NOW...
echo.
echo =====================================================================
echo Keep this window open while using GHOST.
echo =====================================================================
echo.

start http://localhost:8000

echo Server is active. Press any key to stop GHOST.
pause >nul
taskkill /f /im python.exe >nul 2>&1
