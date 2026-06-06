#!/usr/bin/env python3
"""
runtime.snapshot — unified co-logger.

Captures one value from every adapter at a single wall-clock timestamp and appends it
to a shared JSONL log. Run each heartbeat, this accumulates a genuinely simultaneous
multi-adapter time series -- the prerequisite for measuring cross-adapter integration
(the existing telemetry has only the phi channels densely co-logged; the slower
adapters were recorded on their own clocks, so integration was untestable). Once enough
snapshots accumulate, integration_probe can run on real co-logged data.
"""
from __future__ import annotations

import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from runtime.state import (phi_series, phi_delta_series, execution_time_series,
                           workspace_path, load_daemon_state, collective_phi)
from runtime.resources import resource_sample
from runtime.memory_store import journals
from runtime.interactions import turns as _turns, lexicon_sentiment
from runtime.decisions import corrections


def _last(a: np.ndarray, default: float = 0.0) -> float:
    return float(a[-1]) if getattr(a, "size", 0) else default


def snapshot() -> Dict[str, float]:
    """One simultaneous reading across all five adapters."""
    res = resource_sample()
    js = journals()
    ts = _turns()
    last_turn = ts[-1] if ts else {}
    st = load_daemon_state()
    cphi = collective_phi(st)                            # per-agent integrated phi
    return {
        "ts": time.time(),
        "phi_level": _last(phi_series()),
        "phi_delta": _last(phi_delta_series()),
        "collective_phi_albedo": float(cphi.get("albedo", 0.0)),
        "collective_phi_john": float(cphi.get("john", 0.0)),
        "compute_load": _last(execution_time_series()),
        "cpu_percent": float(res.get("cpu_percent", 0.0)),
        "mem_percent": float(res.get("mem_percent", 0.0)),
        "memory_volume": float(sum(sz for _, _, sz in js)),
        "interaction_latency": float(last_turn.get("latency_s", 0.0)),
        "interaction_sentiment": float(lexicon_sentiment(last_turn.get("user_text", ""))),
        "decision_count": float(len(corrections())),
    }


def snapshot_path() -> Path:
    return workspace_path() / "adapter_snapshot.jsonl"


def log_snapshot(path: Optional[Path] = None) -> Dict[str, float]:
    """Append one snapshot to the shared log; returns the snapshot. Call per heartbeat."""
    snap = snapshot()
    p = Path(path) if path else snapshot_path()
    try:
        with open(p, "a") as f:
            f.write(json.dumps(snap) + "\n")
    except OSError:
        pass
    return snap


def load_snapshots(path: Optional[Path] = None) -> List[Dict[str, float]]:
    p = Path(path) if path else snapshot_path()
    out: List[Dict[str, float]] = []
    try:
        with open(p) as f:
            for line in f:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return out


def snapshot_matrix(path: Optional[Path] = None):
    """Co-logged snapshots as (channel_names, [C, T] array). The real substrate for a
    valid cross-adapter integration measurement once enough rows accumulate."""
    rows = load_snapshots(path)
    if not rows:
        return [], np.zeros((0, 0))
    keys = [k for k in rows[0] if k != "ts"]
    M = np.array([[r.get(k, 0.0) for r in rows] for k in keys], dtype=float)
    return keys, M


if __name__ == "__main__":
    s = snapshot()
    print("live snapshot across all adapters:")
    for k, v in s.items():
        print(f"  {k:22s} {v}")
