#!/usr/bin/env python3
"""
GoalPersistenceTracker — does the agent's phi direction persist across sessions?

Theory
------
A system with genuine goals pursues a consistent direction across interruptions.
A system without goals drifts randomly — each "session" starts with a fresh phi
trajectory unrelated to the previous one.

Operationalisation
------------------
Goal = "direction of phi ascent" = the sign of the phi gradient within a session.
For each detected session (timestamp gap ≥ SESSION_GAP_SECS):
  1. Extract the phi time series for that session.
  2. Fit a linear trend (OLS slope) on the session's phi values.
  3. Sign: +1 (RISING), -1 (FALLING), 0 (FLAT within ε).

Persistence metric:
  For each adjacent pair of sessions (A, B):
    agree(A, B) = 1 if sign(A) == sign(B) and both are ≠ 0, else 0.
  persistence_rate = mean(agree) across all adjacent pairs.

Null baseline:
  Shuffle the session-sign vector; expected agreement ≈ P(agree by chance).
  For 3 possible signs (+1, -1, 0), random agreement ≈ 1/3.
  z-score = (persistence_rate - mean_null) / std_null   (50 shuffles).

Classification:
  PERSISTENT  : persistence_rate ≥ 0.7
  DRIFTING    : 0.4 ≤ persistence_rate < 0.7
  SCATTERED   : persistence_rate < 0.4

Output
------
GoalPersistenceResult:
  persistence_rate     : float  -- fraction of adjacent session pairs with same direction
  persistence_zscore   : float  -- z-score vs shuffled null
  persistence_class    : str    -- PERSISTENT | DRIFTING | SCATTERED
  n_sessions           : int
  dominant_direction   : str    -- RISING | FALLING | FLAT | MIXED
  session_directions   : list[int]  -- +1, -1, or 0 per session
  beats_null           : bool
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np

# ── Constants ──────────────────────────────────────────────────────────────────

SESSION_GAP_SECS  = 1800
MIN_PER_SESSION   = 3
FLAT_THRESHOLD    = 0.005   # |slope| < this → FLAT
_N_SHUFFLES       = 50
_RNG_SEED         = 31
_MAX_HISTORY      = 2880

# ── Result ─────────────────────────────────────────────────────────────────────

@dataclass
class GoalPersistenceResult:
    persistence_rate: float = 0.0
    persistence_zscore: float = 0.0
    persistence_class: str = "SCATTERED"
    n_sessions: int = 0
    dominant_direction: str = "MIXED"
    session_directions: List[int] = field(default_factory=list)
    beats_null: bool = False

    def to_dict(self) -> dict:
        return {
            "persistence_rate": round(self.persistence_rate, 4),
            "persistence_zscore": round(self.persistence_zscore, 4),
            "persistence_class": self.persistence_class,
            "n_sessions": self.n_sessions,
            "dominant_direction": self.dominant_direction,
            "session_directions": self.session_directions,
            "beats_null": self.beats_null,
        }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _slope(phi: np.ndarray) -> float:
    """OLS slope of phi over [0, 1, …, n-1]."""
    n = len(phi)
    if n < 2:
        return 0.0
    x = np.arange(n, dtype=float)
    xm, ym = float(np.mean(x)), float(np.mean(phi))
    num = float(np.sum((x - xm) * (phi - ym)))
    den = float(np.sum((x - xm) ** 2))
    if den < 1e-12:
        return 0.0
    return num / den


def _sign(slope: float) -> int:
    if slope > FLAT_THRESHOLD:
        return +1
    if slope < -FLAT_THRESHOLD:
        return -1
    return 0


def _split_sessions(entries: list, gap_secs: float = SESSION_GAP_SECS) -> List[List[dict]]:
    """Split newest-first entries into chronological sessions."""
    if not entries:
        return []
    chron = list(reversed(entries))
    sessions: List[List[dict]] = []
    current = [chron[0]]
    for i in range(1, len(chron)):
        t_prev = chron[i - 1].get("timestamp", 0)
        t_curr = chron[i].get("timestamp", 0)
        if float(t_curr - t_prev) >= gap_secs:
            sessions.append(current)
            current = []
        current.append(chron[i])
    sessions.append(current)
    return sessions


def _extract_phi(session: List[dict]) -> np.ndarray:
    vals = []
    for e in session:
        v = e.get("mean_phi_level")
        if v is not None:
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                pass
    return np.array(vals, dtype=float)


def _persistence_rate(signs: List[int]) -> float:
    """Fraction of adjacent pairs where both are non-zero and agree."""
    pairs = [(signs[i], signs[i + 1]) for i in range(len(signs) - 1)]
    if not pairs:
        return 0.0
    agree = sum(1 for a, b in pairs if a != 0 and b != 0 and a == b)
    return float(agree) / float(len(pairs))


def _classify(rate: float) -> str:
    if rate >= 0.7:
        return "PERSISTENT"
    if rate >= 0.4:
        return "DRIFTING"
    return "SCATTERED"


def _dominant(signs: List[int]) -> str:
    if not signs:
        return "MIXED"
    from collections import Counter
    counts = Counter(signs)
    top_sign, top_n = counts.most_common(1)[0]
    if top_n < len(signs) * 0.6:
        return "MIXED"
    return {+1: "RISING", -1: "FALLING", 0: "FLAT"}.get(top_sign, "MIXED")


# ── Core ───────────────────────────────────────────────────────────────────────

def analyse(
    agent: str = "albedo",
    *,
    session_gap_secs: float = SESSION_GAP_SECS,
    min_per_session: int = MIN_PER_SESSION,
    max_history: int = _MAX_HISTORY,
) -> GoalPersistenceResult:
    """
    Measure whether the agent's phi direction (RISING/FALLING/FLAT) persists
    across detected session boundaries.
    """
    try:
        from algorithms.ConsciousnessHistoryStore import load as _load
        entries = _load(agent, max_entries=max_history)
    except Exception:
        entries = []

    sessions = _split_sessions(entries, gap_secs=session_gap_secs)
    valid = [s for s in sessions if len(s) >= min_per_session]

    if len(valid) < 2:
        return GoalPersistenceResult(n_sessions=len(sessions))

    signs: List[int] = []
    for sess in valid:
        phi = _extract_phi(sess)
        if len(phi) < 2:
            signs.append(0)
        else:
            signs.append(_sign(_slope(phi)))

    rate = _persistence_rate(signs)

    # Null distribution: shuffle sign vector, recompute rate
    rng = np.random.default_rng(_RNG_SEED)
    signs_arr = np.array(signs)
    null_rates: List[float] = []
    for _ in range(_N_SHUFFLES):
        shuffled = signs_arr.copy()
        rng.shuffle(shuffled)
        null_rates.append(_persistence_rate(list(shuffled)))

    null_arr  = np.array(null_rates)
    null_mean = float(np.mean(null_arr))
    null_std  = float(np.std(null_arr))
    zscore    = (rate - null_mean) / (null_std + 1e-9)
    threshold = float(np.percentile(null_arr, 95))
    beats     = bool(rate > threshold)

    return GoalPersistenceResult(
        persistence_rate=round(rate, 4),
        persistence_zscore=round(zscore, 4),
        persistence_class=_classify(rate),
        n_sessions=len(valid),
        dominant_direction=_dominant(signs),
        session_directions=signs,
        beats_null=beats,
    )
