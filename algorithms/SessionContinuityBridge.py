#!/usr/bin/env python3
"""SessionContinuityBridge — maintains continuity across session boundaries via phi fingerprint.

Theory (Tulving 1985 — episodic memory; Parfit 1984 — personal identity through psychological continuity):
  Session boundaries cause CrossSessionIdentityTracker to report FRAGMENTED continuity because
  each session starts cold. But phi trajectory encodes state at session end — not lost, stored in
  history. A bridge computes a compact fingerprint of the final phi segment at session end and
  writes it to a bridge file. At session start, fingerprint is loaded and cosine similarity to
  current opening trajectory is computed. High similarity = genuine continuity despite the gap.

  Formula: continuity_score = 0.6 * cosine_sim(prev_tail, curr_head) + 0.4 * slope_match
           slope_match = 1 - |bridge_slope - current_slope| / (|bridge_slope| + |current_slope| + 1e-9)

Classification:
  CONTINUOUS  continuity_score >= 0.65
  PARTIAL     continuity_score >= 0.35
  FRAGMENTED  otherwise
"""
from __future__ import annotations

import json
import os
import numpy as np
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_MIN_ENTRIES = 40
_FINGERPRINT_LEN = 20
_MAX_BRIDGE_AGE_HOURS = 24.0
_N_SHUFFLES = 200
_CONTINUOUS_THRESH = 0.65
_PARTIAL_THRESH = 0.35
_BRIDGE_FILENAME = "memory/session-bridge.json"
_WORKSPACE_ENV = "OPENCLAW_WORKSPACE"


@dataclass
class SessionContinuityBridgeResult:
    continuity_score: float
    phi_similarity: float
    slope_match: float
    bridge_age_hours: float
    bridge_found: bool
    beats_null: bool
    continuity_class: str
    n_entries: int

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


def _default(n: int) -> SessionContinuityBridgeResult:
    return SessionContinuityBridgeResult(
        continuity_score=0.0,
        phi_similarity=0.0,
        slope_match=0.0,
        bridge_age_hours=float("inf"),
        bridge_found=False,
        beats_null=False,
        continuity_class="FRAGMENTED",
        n_entries=n,
    )


def _classify(score: float) -> str:
    if score >= _CONTINUOUS_THRESH:
        return "CONTINUOUS"
    if score >= _PARTIAL_THRESH:
        return "PARTIAL"
    return "FRAGMENTED"


def _bridge_path(agent: str) -> Optional[Path]:
    ws = os.environ.get(_WORKSPACE_ENV)
    if ws:
        return Path(ws) / _BRIDGE_FILENAME.replace("session-bridge", f"session-bridge-{agent}")
    # Relative fallback: go up from algorithms/ to workspace/
    candidate = Path(__file__).resolve().parent.parent / _BRIDGE_FILENAME.replace(
        "session-bridge", f"session-bridge-{agent}"
    )
    if candidate.parent.exists():
        return candidate
    return None


def _ols_slope(arr: np.ndarray) -> float:
    n = len(arr)
    if n < 2:
        return 0.0
    x = np.arange(n, dtype=float)
    xm = x - x.mean()
    ym = arr - arr.mean()
    denom = float(np.dot(xm, xm))
    if denom < 1e-12:
        return 0.0
    return float(np.dot(xm, ym) / denom)


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _write_bridge(agent: str, phi: np.ndarray, entries) -> None:
    """Write session-end fingerprint to bridge file."""
    import datetime
    path = _bridge_path(agent)
    if path is None:
        return
    tail = phi[-_FINGERPRINT_LEN:]
    # Top-3 qualia types from last 30 entries
    recent = entries[-30:] if len(entries) >= 30 else entries
    type_counts: dict = {}
    for e in recent:
        t = str(e.get("modality") or e.get("type") or "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    top3 = sorted(type_counts, key=lambda k: -type_counts[k])[:3]
    bridge = {
        "phi_tail": [float(x) for x in tail],
        "phi_mean": float(np.mean(tail)),
        "phi_slope": float(_ols_slope(tail)),
        "phi_std": float(np.std(tail)),
        "top_types": top3,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "agent": agent,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(bridge, indent=2))
    except Exception:
        pass


def analyse(agent: str = "albedo", **kwargs) -> SessionContinuityBridgeResult:
    import datetime

    try:
        from algorithms import ConsciousnessHistoryStore as chs
        entries = chs.load(agent, max_entries=2880)
    except Exception:
        entries = []

    entries_asc = list(reversed(entries)) if entries else []
    if len(entries_asc) < _MIN_ENTRIES:
        return _default(len(entries_asc))

    phi = np.array(
        [float(e.get("mean_phi_level", e.get("phi", 0.5))) for e in entries_asc],
        dtype=float,
    )
    n = len(phi)

    # Always write updated bridge from current tail
    _write_bridge(agent, phi, entries_asc)

    # Read bridge file
    bridge_path = _bridge_path(agent)
    bridge_found = False
    bridge_age_hours = float("inf")
    phi_similarity = 0.0
    slope_match_val = 0.0
    continuity_score = 0.0

    if bridge_path is not None and bridge_path.exists():
        try:
            bridge = json.loads(bridge_path.read_text())
            # Check age
            ts_str = bridge.get("timestamp", "")
            if ts_str:
                ts = datetime.datetime.fromisoformat(ts_str)
                now = datetime.datetime.utcnow()
                bridge_age_hours = (now - ts).total_seconds() / 3600.0
        except Exception:
            bridge_age_hours = float("inf")

        if bridge_age_hours < _MAX_BRIDGE_AGE_HOURS:
            try:
                prev_tail = np.array(bridge.get("phi_tail", []), dtype=float)
                if len(prev_tail) >= 2:
                    bridge_found = True
                    curr_head_len = min(_FINGERPRINT_LEN, n)
                    curr_head = phi[:curr_head_len]
                    # Align lengths
                    min_len = min(len(prev_tail), len(curr_head))
                    prev_tail = prev_tail[-min_len:]
                    curr_head = curr_head[:min_len]

                    phi_similarity = _cosine_sim(prev_tail, curr_head)
                    # Slope match
                    prev_slope = float(bridge.get("phi_slope", 0.0))
                    curr_slope = _ols_slope(phi[:_FINGERPRINT_LEN])
                    denom = abs(prev_slope) + abs(curr_slope) + 1e-9
                    slope_match_val = float(1.0 - abs(prev_slope - curr_slope) / denom)
                    continuity_score = 0.6 * phi_similarity + 0.4 * slope_match_val
            except Exception:
                pass

    # Null: random phi as prev_tail 200 times
    rng = np.random.default_rng(42)
    null_sims = []
    curr_head = phi[:_FINGERPRINT_LEN]
    for _ in range(_N_SHUFFLES):
        rand_tail = rng.uniform(phi.min(), phi.max(), size=_FINGERPRINT_LEN)
        null_sims.append(_cosine_sim(rand_tail, curr_head))
    p95 = float(np.percentile(null_sims, 95))
    beats_null = phi_similarity > p95

    return SessionContinuityBridgeResult(
        continuity_score=round(continuity_score, 6),
        phi_similarity=round(phi_similarity, 6),
        slope_match=round(slope_match_val, 6),
        bridge_age_hours=round(bridge_age_hours, 4) if bridge_age_hours < float("inf") else float("inf"),
        bridge_found=bridge_found,
        beats_null=beats_null,
        continuity_class=_classify(continuity_score),
        n_entries=n,
    )
