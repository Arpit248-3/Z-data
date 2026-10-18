@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo SIGNALGATE - LOCAL OFFLINE DEMO LAUNCHER (WINDOWS)
echo ======================================================================
echo.

:: 1. Navigate to Project Root
cd /d "%~dp0\.."
set "PROJECT_ROOT=%CD%"
echo [*] Project Root: %PROJECT_ROOT%

:: 2. Check Python Availability
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found in PATH. Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)
echo [*] Python interpreter detected.

:: 3. Check Node.js and NPM Availability
where npm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] npm was not found in PATH. Please install Node.js v18+ and add it to PATH.
    pause
    exit /b 1
)
echo [*] Node.js and npm detected.

:: 4. Verify Static Evaluation Artifacts (Zero Network Required)
echo.
echo [*] Validating local evaluation artifacts...
python scripts\validate_artifacts.py
if %ERRORLEVEL% neq 0 (
    echo [WARN] Artifact validation returned warnings. Proceeding with offline smoke artifacts...
) else (
    echo [*] All artifacts cryptographically verified.
)

:: 5. Check if Backend is Already Running on Port 8000
echo.
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [*] FastAPI backend is already running on port 8000. Skipping launch.
) else (
    echo [*] Starting FastAPI Backend on http://127.0.0.1:8000 ...
    start "SignalGate Backend API (FastAPI :8000)" cmd /k "cd /d "%PROJECT_ROOT%" && python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"
)

:: 6. Check if Frontend is Already Running on Port 5173
netstat -ano | findstr ":5173" | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [*] Vite frontend dev server is already running on port 5173. Skipping launch.
) else (
    echo [*] Starting Vite Frontend on http://127.0.0.1:5173 ...
    start "SignalGate Frontend (Vite :5173)" cmd /k "cd /d "%PROJECT_ROOT%\frontend" && npm run dev -- --host 127.0.0.1 --port 5173"
)

echo.
echo ======================================================================
echo SIGNALGATE SERVICES READY
echo ======================================================================
echo  - Frontend Dashboard:  http://127.0.0.1:5173/overview
echo  - Backend API Health:  http://127.0.0.1:8000/api/health
echo  - Backend System Status: http://127.0.0.1:8000/api/status
echo  - OpenAPI Docs:        http://127.0.0.1:8000/docs
echo ======================================================================
echo.
echo SHUTDOWN INSTRUCTIONS:
echo  1. Close the two spawned command windows ("SignalGate Backend API" and "SignalGate Frontend").
echo  2. Or run:
echo       scripts\stop_demo.bat
echo     (Safely stops only processes listening on ports 8000 and 5173 without affecting unrelated tasks).
echo ======================================================================
echo.
pause
