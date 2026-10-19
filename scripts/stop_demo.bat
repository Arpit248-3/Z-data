@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo SIGNALGATE - SAFE VERIFIED DEMO SHUTDOWN (WINDOWS)
echo ======================================================================
echo [*] Halting any active historical replay workers cleanly to preserve audit integrity...
python scripts\run_historical_replay.py --stop >nul 2>&1

echo [*] Inspecting processes listening on ports 8000 and 5173 with ownership verification...

powershell -NoProfile -Command ^
    "$ports = 8000, 5173; " ^
    "$conns = Get-NetTCPConnection -LocalPort $ports -State Listen -ErrorAction SilentlyContinue; " ^
    "if ($conns) { " ^
    "    $seenPids = @{}; " ^
    "    foreach ($c in $conns) { " ^
    "        $pidNum = $c.OwningProcess; " ^
    "        if ($seenPids.ContainsKey($pidNum)) { continue; } " ^
    "        $seenPids[$pidNum] = $true; " ^
    "        $proc = Get-CimInstance Win32_Process -Filter ('ProcessId = ' + $pidNum) -ErrorAction SilentlyContinue; " ^
    "        if ($proc) { " ^
    "            $cmd = [string]$proc.CommandLine; " ^
    "            $isSignalGate = $false; " ^
    "            if ($cmd -match 'uvicorn' -and $cmd -match 'backend\.app\.main') { $isSignalGate = $true; } " ^
    "            elseif ($cmd -match 'vite' -or $cmd -match 'signalgate') { $isSignalGate = $true; } " ^
    "            elseif ($proc.Name -match 'node|python' -and $cmd -match 'project') { $isSignalGate = $true; } " ^
    "            if ($isSignalGate) { " ^
    "                Write-Host ('[*] Verified SignalGate process on port ' + $c.LocalPort + ' (PID ' + $pidNum + '): ' + $proc.Name); " ^
    "                Stop-Process -Id $pidNum -Force; " ^
    "                Write-Host ('[SUCCESS] Safely terminated SignalGate listener PID ' + $pidNum + '.'); " ^
    "            } else { " ^
    "                Write-Host ('[WARN] Process ' + $proc.Name + ' (PID ' + $pidNum + ') on port ' + $c.LocalPort + ' does NOT match SignalGate command line. Leaving process running for safety.'); " ^
    "                Write-Host ('       Manual verification required if you intend to stop PID ' + $pidNum + '.'); " ^
    "            } " ^
    "        } " ^
    "    } " ^
    "} else { " ^
    "    Write-Host '[INFO] No listening processes found on port 8000 or 5173.'; " ^
    "}"

echo.
echo [*] Closing demo terminal windows if titled...
taskkill /FI "WINDOWTITLE eq SignalGate Backend API*" >nul 2>&1
taskkill /FI "WINDOWTITLE eq SignalGate Frontend*" >nul 2>&1

echo.
echo [DONE] Safe shutdown complete. Unrelated Python and Node processes remain untouched.
echo ======================================================================
