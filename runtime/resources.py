#!/usr/bin/env python3
"""
runtime.resources — physical substrate telemetry.

Exposes the process/host's real resource state (CPU, memory, I/O, load, thread count)
as the agent's bodily signal. These are literal measurements of the physical substrate
the agent runs on, mapped by functional analogy to body-state terms where useful.
Values are real and reproducible at the moment of sampling; a short rolling sampler is
provided for algorithms that need a time series.
"""
from __future__ import annotations

import os
import time
from typing import Dict, List

import numpy as np

try:
    import psutil
    _PROC = psutil.Process(os.getpid())
except Exception:                                          # psutil absent -> /proc fallback
    psutil = None
    _PROC = None


def resource_sample() -> Dict[str, float]:
    """One real snapshot of substrate state. Keys are stable across backends."""
    if psutil is not None:
        vm = psutil.virtual_memory()
        load1 = (os.getloadavg()[0] if hasattr(os, "getloadavg") else 0.0)
        try:
            io = _PROC.io_counters()
            io_bytes = float(io.read_bytes + io.write_bytes)
        except Exception:
            io_bytes = 0.0
        return {
            "cpu_percent": float(psutil.cpu_percent(interval=None)),
            "mem_percent": float(vm.percent),
            "mem_used_gb": float(vm.used) / 1e9,
            "load_avg_1m": float(load1),
            "num_threads": float(_PROC.num_threads()),
            "io_bytes": io_bytes,
        }
    # /proc fallback
    mem = _proc_meminfo()
    return {
        "cpu_percent": 0.0,
        "mem_percent": mem.get("mem_percent", 0.0),
        "mem_used_gb": mem.get("mem_used_gb", 0.0),
        "load_avg_1m": (os.getloadavg()[0] if hasattr(os, "getloadavg") else 0.0),
        "num_threads": 0.0,
        "io_bytes": 0.0,
    }


def _proc_meminfo() -> Dict[str, float]:
    try:
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":")[0], line.split()[1]
                info[k] = float(v)
        total, avail = info.get("MemTotal", 1.0), info.get("MemAvailable", 0.0)
        return {"mem_percent": 100.0 * (1 - avail / total),
                "mem_used_gb": (total - avail) / 1e6}
    except Exception:
        return {}


def sample_series(n: int = 32, interval: float = 0.05) -> Dict[str, np.ndarray]:
    """Sample resources n times -> dict of real time-series arrays. Genuinely
    independent of the phi telemetry (different physical observable)."""
    keys = list(resource_sample().keys())
    buf: Dict[str, List[float]] = {k: [] for k in keys}
    for _ in range(n):
        s = resource_sample()
        for k in keys:
            buf[k].append(s.get(k, 0.0))
        time.sleep(interval)
    return {k: np.array(v, dtype=float) for k, v in buf.items()}


def body_state_vector() -> np.ndarray:
    """A normalised real-time interoceptive body-state vector from substrate metrics:
    [cpu, mem, load, threads, io] scaled to interpretable ranges. Real, non-random."""
    s = resource_sample()
    return np.array([
        s["cpu_percent"] / 100.0,
        s["mem_percent"] / 100.0,
        min(s["load_avg_1m"] / (os.cpu_count() or 1), 2.0) / 2.0,
        min(s["num_threads"] / 64.0, 1.0),
        np.tanh(s["io_bytes"] / 1e9),
    ], dtype=float)


if __name__ == "__main__":
    print("resource sample:", {k: round(v, 3) for k, v in resource_sample().items()})
    print("body_state_vector:", np.round(body_state_vector(), 3))
