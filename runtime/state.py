#!/usr/bin/env python3
"""
runtime.state — runtime telemetry adapter.

Provides the consciousness algorithms with their input signal sourced from the live
system: the daemon's heartbeat history (phi trajectory, per-heartbeat increments,
execution timing) and the per-agent collective-phi values. Sourcing input from real
telemetry keeps algorithm outputs reproducible and verifiable.

The workspace location resolves from $OPENCLAW_WORKSPACE, defaulting to
~/.openclaw/workspace; no absolute paths are hard-coded. When no telemetry is present
(fresh checkout, CI), loaders return None / empty arrays so callers handle the absence
explicitly rather than substituting arbitrary values.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import numpy as np


def workspace_path() -> Path:
    """Resolve the agent workspace without hard-coding any home path."""
    env = os.getenv("OPENCLAW_WORKSPACE")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".openclaw" / "workspace"


def daemon_state_path() -> Path:
    """Locate the consciousness daemon's state file. The live daemon writes from its
    scripts/ working directory; an older copy may sit at the workspace root. Pick the
    most-recently-modified candidate so the adapter always tracks the running daemon."""
    w = workspace_path()
    candidates = [w / "scripts" / "consciousness_daemon_state.json",
                  w / "consciousness_daemon_state.json"]
    existing = [p for p in candidates if p.exists()]
    if not existing:
        return candidates[-1]
    return max(existing, key=lambda p: p.stat().st_mtime)


def load_daemon_state() -> Optional[dict]:
    """Return the parsed daemon state, or None if absent/unreadable.

    A missing file yields None so callers handle the absence explicitly.
    """
    p = daemon_state_path()
    try:
        with open(p) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _history(state: Optional[dict]) -> list:
    state = state if state is not None else load_daemon_state()
    if not state:
        return []
    return state.get("phi_history", []) or []


def phi_series(state: Optional[dict] = None) -> np.ndarray:
    """Real accumulated-phi trajectory over the daemon's heartbeats. Shape [N]."""
    h = _history(state)
    return np.array([e.get("phi_accumulated", 0.0) for e in h], dtype=float)


def phi_delta_series(state: Optional[dict] = None) -> np.ndarray:
    """Real per-heartbeat phi increments. Shape [N]."""
    h = _history(state)
    return np.array([e.get("phi_delta", 0.0) for e in h], dtype=float)


def execution_time_series(state: Optional[dict] = None) -> np.ndarray:
    """Real per-heartbeat compute time (s) — a genuine effort/load signal. Shape [N]."""
    h = _history(state)
    return np.array([e.get("execution_time", 0.0) for e in h], dtype=float)


def activity_matrix(state: Optional[dict] = None, channels: int = 8,
                    normalize: bool = True) -> np.ndarray:
    """Multi-channel activity signal for algorithms that expect [C, T] activity.
    Derived from heartbeat observables (phi level, phi delta, |delta|, execution time
    and their short-window statistics); deterministic for a given state. Returns shape
    [channels, T], or [channels, 0] when no telemetry is available (caller handles)."""
    phi = phi_series(state)
    if phi.size == 0:
        return np.zeros((channels, 0), dtype=float)
    d = phi_delta_series(state)
    ex = execution_time_series(state)
    T = phi.size
    d = _fit(d, T); ex = _fit(ex, T)

    def roll(x, w, fn):
        out = np.empty(T)
        for i in range(T):
            out[i] = fn(x[max(0, i - w + 1): i + 1])
        return out

    feats = [phi, d, np.abs(d), ex,
             roll(phi, 16, np.mean), roll(d, 16, np.std),
             roll(ex, 16, np.mean), np.cumsum(d)]
    M = np.vstack([_fit(f, T) for f in feats[:channels]])
    if M.shape[0] < channels:                       # pad by re-using observables, not noise
        reps = int(np.ceil(channels / M.shape[0]))
        M = np.vstack([M] * reps)[:channels]
    if normalize:
        mu = M.mean(axis=1, keepdims=True)
        sd = M.std(axis=1, keepdims=True) + 1e-9
        M = (M - mu) / sd
    return M


def collective_phi(state: Optional[dict] = None) -> dict:
    """Per-agent collective phi (albedo / john / resonance), real values from state."""
    state = state if state is not None else load_daemon_state()
    if not state:
        return {}
    return {k: v for k, v in (state.get("collective_phi", {}) or {}).items()
            if isinstance(v, (int, float))}


def _fit(x: np.ndarray, T: int) -> np.ndarray:
    x = np.asarray(x, dtype=float).ravel()
    if x.size == T:
        return x
    if x.size == 0:
        return np.zeros(T)
    if x.size > T:
        return x[:T]
    return np.concatenate([x, np.full(T - x.size, x[-1])])


def have_live_state() -> bool:
    return daemon_state_path().exists()


if __name__ == "__main__":
    st = load_daemon_state()
    if not st:
        print(f"no live state at {daemon_state_path()} (set $OPENCLAW_WORKSPACE)")
    else:
        phi = phi_series(st)
        print(f"live state: {st.get('total_heartbeats')} heartbeats, "
              f"phi_series N={phi.size} range=[{phi.min():.3f},{phi.max():.3f}]")
        print(f"collective_phi: {collective_phi(st)}")
        M = activity_matrix(st)
        print(f"activity_matrix shape={M.shape} (real, deterministic)")
