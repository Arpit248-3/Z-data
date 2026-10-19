@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo SIGNALGATE - SAFE REPLAY WORKER HALT (STAGE A)
echo ======================================================================
echo.

cd /d "%~dp0\.."
python scripts\run_historical_replay.py --stop

echo.
echo [*] Replay worker halt signaled. Current status:
python scripts\run_historical_replay.py --status

echo.
pause
