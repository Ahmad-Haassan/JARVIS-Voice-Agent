@echo off
title GHOST PC Client - Autonomous Desktop Agent
color 0b
cls

echo =====================================================================
echo              GHOST NEURAL PC CLIENT - SETUP & LAUNCH
echo =====================================================================
echo.

:: Automatically unblock downloaded batch script
powershell -NoProfile -Command "Unblock-File -Path '%~f0' -ErrorAction SilentlyContinue" >nul 2>&1

:: Dedicated Working Directory in User Profile
set "ROOT_DIR=%USERPROFILE%\GHOST-Agent"
if not exist "%ROOT_DIR%" mkdir "%ROOT_DIR%"
cd /d "%ROOT_DIR%"

:: Check if server.py exists, if not download clean repo zip and extract using native PowerShell
if not exist "server.py" (
    echo [*] First-time setup: Downloading GHOST core files from GitHub...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference = 'SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri 'https://github.com/Ahmad-Haassan/ghost/archive/refs/heads/main.zip' -OutFile 'ghost_core.zip'; Expand-Archive -Path 'ghost_core.zip' -DestinationPath 'temp_extract' -Force; Copy-Item -Path 'temp_extract\ghost-main\*' -Destination '.' -Recurse -Force; Remove-Item -Recurse -Force 'temp_extract', 'ghost_core.zip'; Write-Host '[+] Core files downloaded successfully.' } catch { Write-Host '[ERROR] Download failed: ' $_; exit 1 }"
    if not exist "server.py" (
        echo.
        echo [ERROR] Failed to extract GHOST server.py into %ROOT_DIR%.
        echo Please ensure you have internet access and run again.
        echo.
        pause
        exit /b 1
    )
)

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo [!] Python 3.10+ is required but was not found on this computer.
        echo [*] Opening official Python download page...
        start https://www.python.org/downloads/
        echo.
        echo IMPORTANT: When installing Python, CHECK 'Add python.exe to PATH'!
        echo After installation finishes, double-click GHOST-Connect.bat again.
        echo.
        pause
        exit /b 1
    ) else (
        set PY_CMD=py
    )
) else (
    set PY_CMD=python
)

:: Setup Virtual Environment
if not exist "venv\Scripts\python.exe" (
    echo [*] Preparing isolated virtual environment (one-time setup)...
    %PY_CMD% -m venv venv
    if not exist "venv\Scripts\python.exe" (
        echo [!] Could not create venv. Using system Python...
        set "RUN_PY=%PY_CMD%"
    ) else (
        set "RUN_PY=venv\Scripts\python.exe"
    )
    echo [*] Installing required high-performance modules...
    %RUN_PY% -m pip install --upgrade pip >nul 2>&1
    if exist "requirements.txt" (
        %RUN_PY% -m pip install -r requirements.txt
    ) else (
        %RUN_PY% -m pip install fastapi uvicorn psutil pyautogui pywin32 requests python-multipart opencv-python numpy websockets
    )
) else (
    set "RUN_PY=venv\Scripts\python.exe"
)

:: Verify server.py is ready
if not exist "server.py" (
    echo.
    echo [ERROR] server.py not found in %ROOT_DIR%!
    pause
    exit /b 1
)

echo.
echo [*] Launching GHOST Desktop Server...
echo.

:: Detect Local IP Address
set "LOCAL_IP=127.0.0.1"
for /f "tokens=4" %%a in ('route print ^| findstr 0.0.0.0 ^| findstr /v "127.0.0.1" 2^>nul') do (
    set "LOCAL_IP=%%a"
    goto :ip_found
)
:ip_found

echo =====================================================================
echo        [+] GHOST IS ONLINE & READY ON YOUR PC!
echo =====================================================================
echo.
echo >>> TO CONTROL FROM YOUR PHONE (ON SAME WI-FI):
echo     http://%LOCAL_IP%:8000
echo.
echo >>> OPENING GHOST DASHBOARD IN YOUR BROWSER...
echo =====================================================================
echo Keep this command window open while controlling your PC.
echo =====================================================================
echo.

start http://localhost:8000

:: Run server directly in this window so output and logs are immediately visible
%RUN_PY% server.py

if %errorlevel% neq 0 (
    echo.
    echo [!] GHOST server stopped unexpectedly.
    echo.
    pause
)
