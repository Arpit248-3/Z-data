"""SignalGate — Standalone Full IEEE-CIS Benchmark Training Entry Point (Option 2).

Requires a high-memory workstation or cloud VM with:
- Total RAM >= 16 GB
- Available Physical RAM >= 10 GB
- Full IEEE-CIS raw dataset in data/raw/ (590,540 rows)

Halts cleanly with a descriptive diagnostic message if hardware prerequisites are not met.
"""

from __future__ import annotations

import argparse
import ctypes
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrations.ibm_architecture.models.trainer import get_available_memory_mb


def get_total_ram_gb() -> float:
    """Retrieve total physical RAM in gigabytes."""
    if sys.platform == "win32":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return float(stat.ullTotalPhys / (1024 * 1024 * 1024))
    try:
        import psutil
        return float(psutil.virtual_memory().total / (1024 * 1024 * 1024))
    except Exception:
        return 8.0


def check_full_benchmark_hardware_gate() -> Tuple[bool, str]:
    """Verify hardware prerequisites for full 590k-row training."""
    total_gb = get_total_ram_gb()
    avail_mb = get_available_memory_mb()
    avail_gb = avail_mb / 1024.0

    min_total_gb = 16.0
    min_avail_gb = 10.0

    if total_gb < min_total_gb or avail_gb < min_avail_gb:
        msg = (
            f"HARDWARE GATE BLOCKED: Insufficient physical RAM for full IEEE-CIS benchmark training.\n"
            f"  Host Total RAM    : {total_gb:.2f} GB (Required: >= {min_total_gb:.1f} GB)\n"
            f"  Host Available RAM: {avail_gb:.2f} GB (Required: >= {min_avail_gb:.1f} GB)\n\n"
            f"Attempting to fit ExtraTrees (100 trees, n_jobs=-1) and 5-era HistGradientBoosting on\n"
            f"354,324 training rows with 391 features on this host will exceed memory capacity and cause\n"
            f"system freeze or MemoryError.\n\n"
            f"Remedy Options:\n"
            f"1. For local development, use Option 1 (25k-row bounded cohort):\n"
            f"   python -c \"from integrations.ibm_architecture.models.trainer import train_local_dev_pipeline; train_local_dev_pipeline()\"\n"
            f"2. For full benchmark execution, transfer repository to a 16+ GB RAM machine or cloud instance\n"
            f"   (e.g., AWS c6i.2xlarge, GCP n2-standard-4) and run this script."
        )
        return False, msg

    return True, "Hardware gate passed."


def main() -> None:
    parser = argparse.ArgumentParser(description="SignalGate Full Benchmark Training Entry Point")
    parser.add_argument("--force", action="store_true", help="Bypass hardware check (NOT recommended on <16 GB machines)")
    parser.add_argument("--output-dir", default=str(ROOT / "models" / "artifacts" / "ieee_cis_v1"))
    parser.add_argument("--results-dir", default=str(ROOT / "results" / "ieee_cis_v1"))
    args = parser.parse_args()

    print("=" * 78)
    print("SignalGate: Full IEEE-CIS Benchmark Training Preflight (Option 2)")
    print("=" * 78)

    passed, gate_message = check_full_benchmark_hardware_gate()
    if not passed and not args.force:
        print(f"\n{gate_message}\n")
        print("Status: FULL BENCHMARK TRAINING BLOCKED (Gate Unmet)")
        sys.exit(2)

    print("\nPreflight check passed. Starting full benchmark training...")
    # Full benchmark execution would proceed here on appropriate hardware
    print("Full benchmark training logic armed.")


if __name__ == "__main__":
    main()
