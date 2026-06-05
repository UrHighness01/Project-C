#!/usr/bin/env python3
"""
runtime.memory_store — episodic memory adapter.

Reads the agent's real memory journals (dated markdown the agent actually wrote) and
exposes them as a parseable signal: per-day entry cadence and volume, plus access to
recent entry text for content-level analysis. This is genuine autobiographical data,
not synthetic. Path resolves from runtime.state.workspace_path() (leak-free).
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    from runtime.state import workspace_path
except Exception:
    from pathlib import Path as _P
    import os as _os
    def workspace_path():
        return _P(_os.getenv("OPENCLAW_WORKSPACE", str(_P.home() / ".openclaw" / "workspace")))

_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def memory_dir() -> Path:
    return workspace_path() / "memory"


def journals() -> List[Tuple[datetime, Path, int]]:
    """Dated journal files as (date, path, size_bytes), chronological. Empty if none."""
    out = []
    d = memory_dir()
    if not d.exists():
        return out
    for p in d.glob("*.md"):
        m = _DATE.search(p.name)
        if not m:
            continue
        try:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            continue
        try:
            size = p.stat().st_size
        except OSError:
            size = 0
        out.append((dt, p, size))
    return sorted(out, key=lambda r: r[0])


def cadence_series() -> Dict[str, np.ndarray]:
    """Per-journal real episodic signal: volume (bytes) and inter-entry gap (days).
    Arrays are aligned and chronological; empty arrays if no journals."""
    js = journals()
    if not js:
        return {"volume": np.zeros(0), "gap_days": np.zeros(0)}
    vols = np.array([sz for _, _, sz in js], dtype=float)
    dates = [dt for dt, _, _ in js]
    gaps = np.array([0.0] + [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))],
                    dtype=float)
    return {"volume": vols, "gap_days": gaps}


def recent_text(n: int = 5, max_chars: int = 20000) -> str:
    """Concatenated text of the n most recent journals (for content analysis)."""
    js = journals()[-n:]
    chunks = []
    for _, p, _ in js:
        try:
            chunks.append(p.read_text(errors="ignore")[:max_chars])
        except OSError:
            pass
    return "\n\n".join(chunks)


def vocabulary_stats() -> Dict[str, float]:
    """Real lexical stats over the journals: token count, unique tokens, type-token
    ratio. A genuine (non-random) summary of what the agent has actually written."""
    text = recent_text(n=len(journals()) or 1, max_chars=4000)
    toks = re.findall(r"[a-zA-Z']+", text.lower())
    if not toks:
        return {"tokens": 0.0, "unique": 0.0, "ttr": 0.0}
    uniq = len(set(toks))
    return {"tokens": float(len(toks)), "unique": float(uniq),
            "ttr": uniq / len(toks)}


def have_memory() -> bool:
    return len(journals()) > 0


if __name__ == "__main__":
    js = journals()
    print(f"journals: {len(js)}")
    if js:
        c = cadence_series()
        print(f"volume bytes: min={c['volume'].min():.0f} max={c['volume'].max():.0f}")
        print(f"vocabulary: {vocabulary_stats()}")
