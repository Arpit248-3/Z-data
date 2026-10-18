"""SignalGate Latency Benchmarking Module

Measures end-to-end inference and decision routing latency,
strictly adhering to Blueprint Section 6.3, 6.5, and 8.2:
- High-precision timing via time.perf_counter_ns.
- Explicit warmup phase before timing to eliminate cold-start/JIT variance.
- Separate benchmarks for single-transaction path and batch-of-32 path.
- Reports p50, p90, p95, p99 percentiles, mean, min, and max in milliseconds.
- Captures complete host environment metadata (CPU, architecture, OS, Python/library versions).
- Strict hardware discipline: explicitly notes execution on local x86 hardware,
  with zero claims of IBM LinuxONE or hardware accelerator performance.
"""

import os
import platform
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Sequence
import numpy as np
import pandas as pd


def time_calls(
    fn: Callable[[Any], Any],
    input_data: Any,
    n_calls: int = 5000,
    batch_size: int = 1,
    warmup: int = 200,
) -> Dict[str, Any]:
    """Execute timed calls with explicit warmup and percentile reporting.

    Args:
        fn: Function to benchmark (accepts input_data).
        input_data: Input argument passed to fn on each call.
        n_calls: Number of timed benchmark iterations.
        batch_size: Number of transactions per call (1 for single, 32 for batch).
        warmup: Number of untimed warmup iterations.

    Returns:
        Dict[str, Any] containing latency percentiles (ms), throughput, and execution counts.
    """
    # 1. Warmup phase
    for _ in range(warmup):
        _ = fn(input_data)

    # 2. Timed loop
    durations_ns = np.empty(n_calls, dtype=np.int64)
    for i in range(n_calls):
        t0 = time.perf_counter_ns()
        _ = fn(input_data)
        t1 = time.perf_counter_ns()
        durations_ns[i] = t1 - t0

    durations_ms = durations_ns / 1_000_000.0

    p50 = float(np.percentile(durations_ms, 50))
    p90 = float(np.percentile(durations_ms, 90))
    p95 = float(np.percentile(durations_ms, 95))
    p99 = float(np.percentile(durations_ms, 99))
    mean_ms = float(np.mean(durations_ms))
    min_ms = float(np.min(durations_ms))
    max_ms = float(np.max(durations_ms))

    total_time_s = float(np.sum(durations_ms) / 1000.0)
    total_tx = n_calls * batch_size
    tx_per_sec = float(total_tx / total_time_s) if total_time_s > 0 else 0.0

    res = {
        "batch_size": batch_size,
        "n_calls": n_calls,
        "warmup_calls": warmup,
        "p50_ms": round(p50, 4),
        "p90_ms": round(p90, 4),
        "p95_ms": round(p95, 4),
        "p99_ms": round(p99, 4),
        "mean_ms": round(mean_ms, 4),
        "min_ms": round(min_ms, 4),
        "max_ms": round(max_ms, 4),
        "throughput_tx_per_sec": round(tx_per_sec, 2),
    }

    if batch_size > 1:
        res["per_tx_p50_ms"] = round(p50 / batch_size, 4)
        res["per_tx_p95_ms"] = round(p95 / batch_size, 4)
        res["per_tx_p99_ms"] = round(p99 / batch_size, 4)

    return res


def benchmark_pipeline_latency(
    single_predict_fn: Callable[[pd.DataFrame], Any],
    batch_predict_fn: Callable[[pd.DataFrame], Any],
    sample_row: pd.DataFrame,
    sample_batch_32: pd.DataFrame,
    n_single_calls: int = 5000,
    n_batch_calls: int = 1000,
    warmup_single: int = 200,
    warmup_batch: int = 50,
    status: str = "SYNTHETIC_SMOKE_ONLY",
) -> Dict[str, Any]:
    """Run full latency benchmark suite covering single and batch-of-32 paths."""
    import sklearn

    single_results = time_calls(
        fn=single_predict_fn,
        input_data=sample_row,
        n_calls=n_single_calls,
        batch_size=1,
        warmup=warmup_single,
    )

    batch_results = time_calls(
        fn=batch_predict_fn,
        input_data=sample_batch_32,
        n_calls=n_batch_calls,
        batch_size=len(sample_batch_32),
        warmup=warmup_batch,
    )

    env_metadata = {
        "os": platform.system(),
        "os_release": platform.release(),
        "platform_machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_logical_cores": os.cpu_count(),
        "python_version": sys.version.split()[0],
        "sklearn_version": sklearn.__version__,
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        "timing_clock": "time.perf_counter_ns",
    }

    return {
        "status": status,
        "single_transaction_path": single_results,
        "batch_32_path": batch_results,
        "environment": env_metadata,
        "acceptance_check_ac5": {
            "target_single_row_p95_ms": 50.0,
            "measured_single_row_p95_ms": single_results["p95_ms"],
            "passed": bool(single_results["p95_ms"] <= 50.0),
        },
        "disclaimer": (
            "Local environment benchmark executed on commodity x86_64 CPU. "
            "No IBM LinuxONE mainframe acceleration or hardware coprocessors were used. "
            "Metrics reflect software pipeline throughput, not enterprise SLA certification."
        ),
    }
