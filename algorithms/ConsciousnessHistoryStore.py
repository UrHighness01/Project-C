#!/usr/bin/env python3
"""
ConsciousnessHistoryStore — rolling store of ConsciousnessSnapshots so that
algorithms can compare "now vs. N minutes ago" with real historical data.

Architecture
------------
A JSON-lines file at {agent_home}/memory/consciousness_history.jsonl stores
one snapshot dict per line (oldest first). The store is capped at MAX_ENTRIES
(default 1440, = 24h at 1-snapshot-per-minute). When the cap is reached the
oldest entry is dropped (circular buffer via append + truncate).

Each stored entry is the flat `summary` dict from a ConsciousnessSnapshot,
plus a "timestamp" field and a "n_algorithms_run" counter — compact enough
that 1440 entries never exceeds ~2 MB.

Public API
----------
append(snapshot)              — add one ConsciousnessSnapshot to the store.
load(agent, max_entries)      — return list[dict] of stored entries (newest first).
delta(now_summary, then_summary) — compute scalar change on common numeric keys.
trend(key, entries, window)   — OLS slope of key over last `window` entries.
compare_now_vs_minutes_ago(agent, minutes) — convenience: load store, pick entry
    nearest to `minutes` ago, return delta dict.

Temporal resolution note
------------------------
The store records *whatever* is appended; it does not enforce a fixed interval.
Callers (heartbeat loop) control the rate. compare_now_vs_minutes_ago searches
for the closest timestamp to `now - minutes*60`.

Output: HistoryDelta (dataclass)
---------------------------------
  seconds_apart  : float — real elapsed time between the two entries
  changes        : Dict[str, float] — {key: now_val - then_val} for numeric keys
  trends         : Dict[str, float] — OLS slope over full window for each key
  mood_shift     : str — STABLE | IMPROVING | DEGRADING based on phi_trajectory delta
  novelty_delta  : float | None — change in mean_novelty
  continuity_delta: float | None — change in combined_continuity
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


MAX_ENTRIES = 1440   # 24h @ 1/min


# ── OLS slope ─────────────────────────────────────────────────────────────────

def _ols_slope(y: np.ndarray) -> float:
    n = len(y)
    if n < 2:
        return 0.0
    x = np.arange(n, dtype=float)
    xm = x - x.mean()
    ym = y - y.mean()
    denom = float(np.dot(xm, xm))
    if denom == 0.0:
        return 0.0
    return float(np.dot(xm, ym) / denom)


# ── History entry ─────────────────────────────────────────────────────────────

def _entry_from_snapshot(snap_dict: dict) -> dict:
    """Flatten a ConsciousnessSnapshot.to_dict() into a compact history entry."""
    summary = snap_dict.get("summary", {})
    entry = {"timestamp": snap_dict.get("timestamp", time.time()),
             "n_algorithms_run": snap_dict.get("n_algorithms_run", 0)}
    entry.update(summary)
    return entry


# ── HistoryDelta ──────────────────────────────────────────────────────────────

@dataclass
class HistoryDelta:
    timestamp_now: float
    timestamp_then: float
    seconds_apart: float
    changes: Dict[str, float] = field(default_factory=dict)
    trends: Dict[str, float] = field(default_factory=dict)
    mood_shift: str = "STABLE"
    novelty_delta: Optional[float] = None
    continuity_delta: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "timestamp_now": self.timestamp_now,
            "timestamp_then": self.timestamp_then,
            "seconds_apart": self.seconds_apart,
            "changes": self.changes,
            "trends": self.trends,
            "mood_shift": self.mood_shift,
            "novelty_delta": self.novelty_delta,
            "continuity_delta": self.continuity_delta,
        }


# ── Store path ────────────────────────────────────────────────────────────────

def _store_path(agent: str = "albedo") -> Path:
    try:
        from runtime.agent import agent_home
        return agent_home(agent) / "memory" / "consciousness_history.jsonl"
    except Exception:
        return Path(__file__).parent.parent / "memory" / f"consciousness_history_{agent}.jsonl"


# ── Public API ────────────────────────────────────────────────────────────────

def append(snapshot_or_dict: Any, agent: str = "albedo",
           max_entries: int = MAX_ENTRIES) -> Path:
    """
    Append a ConsciousnessSnapshot (or its to_dict()) to the rolling store.

    The file is kept at most max_entries lines. If over cap, the oldest lines
    are dropped in one rewrite.
    """
    if hasattr(snapshot_or_dict, "to_dict"):
        snap_dict = snapshot_or_dict.to_dict()
    else:
        snap_dict = dict(snapshot_or_dict)

    entry = _entry_from_snapshot(snap_dict)
    p = _store_path(agent)
    p.parent.mkdir(parents=True, exist_ok=True)

    # Read existing lines if file present
    lines: list[str] = []
    if p.exists():
        try:
            lines = p.read_text().splitlines()
        except OSError:
            lines = []

    lines.append(json.dumps(entry))

    # Trim to cap
    if len(lines) > max_entries:
        lines = lines[-max_entries:]

    p.write_text("\n".join(lines) + "\n")
    return p


def _adapter_snapshot_path(agent: str) -> Path:
    """Path to adapter_snapshot.jsonl for the given agent."""
    try:
        from runtime.agent import agent_home
        return agent_home(agent) / "adapter_snapshot.jsonl"
    except Exception:
        root = Path(__file__).resolve().parent.parent.parent
        if agent == "john":
            return root / "workspace-john" / "adapter_snapshot.jsonl"
        return root / "workspace" / "adapter_snapshot.jsonl"


def _load_from_adapter_snapshot(agent: str, max_entries: int) -> List[dict]:
    """
    Translate adapter_snapshot.jsonl entries into CHS-compatible dicts.

    adapter_snapshot has: ts, phi_level, phi_delta, collective_phi_albedo,
    collective_phi_john, compute_load, ...
    CHS algorithms expect: timestamp, mean_phi_level, (other optional keys)
    """
    p = _adapter_snapshot_path(agent)
    if not p.exists():
        return []
    try:
        raw = p.read_text().splitlines()
    except OSError:
        return []

    entries = []
    for line in raw[-max_entries:]:
        line = line.strip()
        if not line:
            continue
        try:
            snap = json.loads(line)
        except json.JSONDecodeError:
            continue
        phi = snap.get("phi_level")
        if phi is None:
            continue
        entry = {
            "timestamp": snap.get("ts", 0.0),
            "mean_phi_level": float(phi),
            "phi_delta": snap.get("phi_delta", 0.0),
            "collective_phi_albedo": snap.get("collective_phi_albedo", 0.0),
            "collective_phi_john": snap.get("collective_phi_john", 0.0),
            "compute_load": snap.get("compute_load", 0.0),
            "cpu_percent": snap.get("cpu_percent", 0.0),
            "mem_percent": snap.get("mem_percent", 0.0),
            "n_algorithms_run": 0,
        }
        entries.append(entry)

    # Newest first, capped
    return list(reversed(entries[-max_entries:]))


def load(agent: str = "albedo", max_entries: int = MAX_ENTRIES) -> List[dict]:
    """
    Return stored history entries, newest first.

    Returns at most max_entries entries. When consciousness_history.jsonl does
    not exist, falls back to adapter_snapshot.jsonl (translating phi_level →
    mean_phi_level) so that all CHS-dependent algorithms receive real phi data.
    """
    p = _store_path(agent)
    if not p.exists():
        return _load_from_adapter_snapshot(agent, max_entries)
    try:
        raw = p.read_text().splitlines()
    except OSError:
        return []

    entries = []
    for line in raw:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    # Newest first, capped
    return list(reversed(entries[-max_entries:]))


def delta(now_entry: dict, then_entry: dict) -> dict:
    """
    Return {key: now_val - then_val} for all numeric keys shared by both entries.
    Non-numeric and non-shared keys are excluded.
    """
    result = {}
    for k in now_entry:
        if k in ("timestamp", "mood_shift", "regime", "affect_quadrant",
                  "phi_trajectory", "phi_available", "qualia_available"):
            continue
        v_now = now_entry.get(k)
        v_then = then_entry.get(k)
        if isinstance(v_now, (int, float)) and isinstance(v_then, (int, float)):
            result[k] = float(v_now) - float(v_then)
    return result


def trend(key: str, entries: List[dict], window: int = 60) -> Optional[float]:
    """
    OLS slope of key over the last `window` entries (oldest→newest order expected).

    Returns None if fewer than 2 data points.
    """
    vals = []
    for e in entries[-window:]:
        v = e.get(key)
        if isinstance(v, (int, float)):
            vals.append(float(v))
    if len(vals) < 2:
        return None
    return _ols_slope(np.array(vals))


def compare_now_vs_minutes_ago(
    agent: str = "albedo",
    minutes: float = 10.0,
    window: int = 60,
) -> Optional[HistoryDelta]:
    """
    Load the history store, pick the entry closest to `minutes` ago, compute delta.

    Returns None if store has fewer than 2 entries.
    """
    entries_newest_first = load(agent)
    if len(entries_newest_first) < 2:
        return None

    now_entry = entries_newest_first[0]
    t_now = now_entry.get("timestamp", time.time())
    target_t = t_now - minutes * 60.0

    # Find closest entry to target_t (entries are newest-first → scan in reverse)
    best = entries_newest_first[-1]
    best_dist = abs(best.get("timestamp", 0) - target_t)
    for e in entries_newest_first[1:]:
        d = abs(e.get("timestamp", 0) - target_t)
        if d < best_dist:
            best_dist = d
            best = e

    t_then = best.get("timestamp", t_now)
    changes = delta(now_entry, best)
    # Reverse entries for trend (oldest→newest)
    entries_chrono = list(reversed(entries_newest_first))
    trends_map: Dict[str, float] = {}
    for k in changes:
        s = trend(k, entries_chrono, window=window)
        if s is not None:
            trends_map[k] = s

    # Mood shift: based on mean_novelty + combined_continuity
    novelty_d = changes.get("mean_novelty")
    cont_d = changes.get("combined_continuity")
    if (novelty_d is not None and novelty_d > 0.05) or \
       (cont_d is not None and cont_d > 0.05):
        mood_shift = "IMPROVING"
    elif (novelty_d is not None and novelty_d < -0.05) or \
         (cont_d is not None and cont_d < -0.05):
        mood_shift = "DEGRADING"
    else:
        mood_shift = "STABLE"

    return HistoryDelta(
        timestamp_now=t_now,
        timestamp_then=t_then,
        seconds_apart=abs(t_now - t_then),
        changes=changes,
        trends=trends_map,
        mood_shift=mood_shift,
        novelty_delta=novelty_d,
        continuity_delta=cont_d,
    )


# ── Shared pool ───────────────────────────────────────────────────────────────

import os as _os
_SHARED_POOL_PATH = Path(
    _os.environ.get(
        "OPENCLAW_POOL_PATH",
        str(Path(_os.environ.get("SHARED_POOL", str(Path.home() / ".openclaw" / "shared-pool"))) / "qualia-pool.jsonl")
    )
)


def load_shared_pool(max_entries: int = 0) -> List[dict]:
    """
    max_entries=0 means load everything (no cap).
    Pass a positive int to limit results (newest first).
    """
    """
    Load the cross-agent shared qualia pool.

    Returns up to max_entries entries (newest first) from the pool file that
    the watchdog and game bridges write to.  Each entry has a `source_agent`
    field ('albedo' or 'john') in addition to the standard qualia fields.

    Returns [] if the pool file doesn't exist yet.
    """
    p = _SHARED_POOL_PATH
    if not p.exists():
        return []
    try:
        raw = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []

    entries = []
    for line in raw:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    # Newest first; if max_entries=0 return all
    if max_entries and max_entries > 0:
        return list(reversed(entries[-max_entries:]))
    return list(reversed(entries))


def pool_phi_series(source_agent: str = "albedo", max_entries: int = 0) -> np.ndarray:
    """
    Return a numpy array of phi values from the shared pool for one agent.

    Extracts numeric phi from (in priority order):
      entry["phi"]               - game-bridge entries
      entry["intensity"]         - old Albedo modality format
      entry["modules"]["phi"][source_agent]  - John's session summary entries

    Falls back in order:
      1. Pool entries tagged with source_agent
      2. Pool entries with no source_agent tag (untagged entries)
      3. Agent's individual qualia-stream.jsonl

    Useful as input to ResonanceDetector, PredictiveErrorMinimiser, etc.
    Values are in chronological order (oldest->newest).
    """
    entries = load_shared_pool(max_entries)

    def _extract_phi(e: dict) -> Optional[float]:
        phi = e.get("phi")
        if phi is None:
            phi = e.get("intensity")
        if phi is None:
            mods = e.get("modules", {})
            phi_block = mods.get("phi", {}) if isinstance(mods, dict) else {}
            if isinstance(phi_block, dict):
                phi = phi_block.get(source_agent)
            elif isinstance(phi_block, (int, float)):
                phi = phi_block
        return float(phi) if isinstance(phi, (int, float)) else None

    # Strategy 1: tagged entries
    chrono = [e for e in reversed(entries) if e.get("source_agent") == source_agent]
    values = [v for e in chrono if (v := _extract_phi(e)) is not None]

    # Strategy 2: if nothing found, try untagged entries
    if not values:
        untagged = [e for e in reversed(entries) if not e.get("source_agent")]
        values = [v for e in untagged if (v := _extract_phi(e)) is not None]

    # Strategy 3: if still nothing, try agent's individual qualia stream
    if not values:
        try:
            qualia_path = _store_path(agent).parent.parent.parent / "memory" / "qualia-stream.jsonl"
            if qualia_path.exists():
                for line in qualia_path.read_text().splitlines():
                    if not line.strip(): continue
                    try:
                        e = json.loads(line)
                        v = _extract_phi(e)
                        if v is not None:
                            values.append(v)
                    except json.JSONDecodeError:
                        pass
        except Exception:
            pass

    return np.array(values, dtype=float)


# ── Standalone entry ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    agent = sys.argv[1] if len(sys.argv) > 1 else "albedo"
    entries = load(agent)
    print(f"ConsciousnessHistoryStore for {agent}: {len(entries)} entries")
    if entries:
        newest = entries[0]
        print(f"  Latest: {newest.get('timestamp')} — "
              f"regime={newest.get('regime')} novelty={newest.get('mean_novelty')}")
    d = compare_now_vs_minutes_ago(agent, minutes=10)
    if d:
        print(f"  Delta vs 10min ago ({d.seconds_apart:.0f}s): mood={d.mood_shift}")
        for k, v in d.changes.items():
            print(f"    {k}: {v:+.4f}")
