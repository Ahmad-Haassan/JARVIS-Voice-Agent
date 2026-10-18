@echo off
title Stop JARVIS Mobile Server
echo ====================================================
echo      Stopping JARVIS Mobile Remote Server...
echo ====================================================
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8443') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo [*] Mobile server stopped.
ping 127.0.0.1 -n 2 >nul
