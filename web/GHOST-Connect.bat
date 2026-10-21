@echo off
title GHOST PC Client
color 0b
cls

echo =====================================================================
echo              GHOST NEURAL PC CLIENT - SETUP AND LAUNCH
echo =====================================================================
echo.

set "ROOT_DIR=%USERPROFILE%\GHOST-Agent"
if not exist "%ROOT_DIR%" mkdir "%ROOT_DIR%"
cd /d "%ROOT_DIR%"

if exist "server.py" goto :check_python

echo [*] Downloading GHOST core files from GitHub to %ROOT_DIR%...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference = 'SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/Ahmad-Haassan/ghost/archive/refs/heads/main.zip' -OutFile 'ghost.zip'; Expand-Archive -Path 'ghost.zip' -DestinationPath 'temp_ext' -Force; Copy-Item -Path 'temp_ext\ghost-main\*' -Destination '.' -Recurse -Force; Remove-Item -Recurse -Force 'temp_ext', 'ghost.zip'"

if not exist "server.py" (
    echo.
    echo [ERROR] Failed to extract GHOST server.py into %ROOT_DIR%.
    echo Please check your internet connection and try again.
    echo.
    pause
    exit /b 1
)

:check_python
echo [*] Checking Python environment...

set "RUN_PY="
where python >nul 2>&1
if %errorlevel% equ 0 set "RUN_PY=python"

if "%RUN_PY%"=="" (
    where py >nul 2>&1
    if %errorlevel% equ 0 set "RUN_PY=py"
)

if "%RUN_PY%"=="" (
    echo.
    echo [!] Python 3.10+ is required but was not found on this computer.
    echo [*] Opening official Python download page...
    start https://www.python.org/downloads/
    echo.
    echo IMPORTANT: In the installer, CHECK 'Add python.exe to PATH'!
    echo Then run GHOST-Connect.bat again.
    echo.
    pause
    exit /b 1
)

echo [*] Using Python: %RUN_PY%

if not exist "venv\Scripts\python.exe" goto :create_venv

set "RUN_PY=venv\Scripts\python.exe"
goto :launch_server

:create_venv
echo [*] Setting up virtual environment (one-time setup, please wait)...
%RUN_PY% -m venv venv
if exist "venv\Scripts\python.exe" (
    set "RUN_PY=venv\Scripts\python.exe"
)

echo [*] Installing required lightweight packages...
%RUN_PY% -m pip install --upgrade pip >nul 2>&1
%RUN_PY% -m pip install fastapi uvicorn psutil pyautogui pywin32 requests python-multipart opencv-python numpy websockets

:launch_server
echo.
echo =====================================================================
echo              STARTING GHOST DESKTOP AGENT
echo =====================================================================
echo.

start http://localhost:8000

%RUN_PY% server.py

if %errorlevel% neq 0 (
    echo.
    echo [!] GHOST server encountered an error and stopped.
    echo.
    pause
)
