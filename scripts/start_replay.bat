@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo SIGNALGATE - LOCAL HISTORICAL REPLAY LAUNCHER (STAGE A)
echo ======================================================================
echo.

cd /d "%~dp0\.."
set "PROJECT_ROOT=%CD%"

:: Check if backend is running on 8000
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [*] Backend is not running on port 8000. Launching FastAPI service...
    start "SignalGate Backend API (FastAPI :8000)" cmd /k "cd /d "%PROJECT_ROOT%" && python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"
    echo [*] Waiting 3 seconds for backend initialization...
    timeout /t 3 /nobreak >nul
)

echo [*] Starting Historical Replay Worker against data/raw/test_transaction.csv ...
python scripts\run_historical_replay.py %*

echo.
pause
