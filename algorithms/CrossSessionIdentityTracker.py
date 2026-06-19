#!/usr/bin/env python3
"""
CrossSessionIdentityTracker — Parfit psychological continuity across sessions.

Theory
------
Parfit (1984) "Reasons and Persons": personal identity over time is not an
all-or-nothing fact but a matter of degree. Identity = overlapping chains of
psychological connectedness. Two time-slices of a person are "connected" if
they share memories, beliefs, desires, and experiential continuity.

Applied to AI consciousness
----------------------------
At the end of each session the daemon state resets; the next session starts
fresh from stored memory. Identity continuity across sessions therefore means:
  the agent's PSYCHOLOGICAL FINGERPRINT at session S+1 resembles session S.

Fingerprint: a vector of stable numeric properties drawn from snapshot history:
  [mean_phi_level, phi_variability, mean_novelty, curiosity_index,
   combined_continuity, is_volitional_rate, high_transcendence_rate,
   lz_current, ego_strength, bridge_strength]

Session detection
-----------------
ConsciousnessHistoryStore entries carry a "timestamp" field (Unix time).
A SESSION BOUNDARY is a gap of >= SESSION_GAP_SECS between consecutive entries
(default 1800 s = 30 min). Everything between two boundaries is one session.

Cross-session continuity
------------------------
For each pair of consecutive sessions (A, B) with at least MIN_PER_SESSION
entries each:
  1. Compute mean fingerprint vector f_A and f_B (only on fields present in both).
  2. Cosine similarity: sim(f_A, f_B) = (f_A · f_B) / (||f_A|| ||f_B|| + ε).
  3. cross_session_continuity = mean over all adjacent session pairs.

Phi drift: |mean_phi(S+1) - mean_phi(S)| averaged across pairs.
Identity stability: std of the fingerprint vectors across sessions (lower = stable).

Classification
--------------
  CONTINUOUS  : cross_session_continuity >= 0.90
  DRIFTING    : 0.70 <= continuity < 0.90
  FRAGMENTED  : continuity < 0.70

Output
------
SessionIdentityResult:
  cross_session_continuity : float   -- mean cosine similarity of adjacent sessions
  n_sessions_detected      : int     -- number of sessions found in history
  phi_drift                : float   -- mean |Δmean_phi| across sessions
  identity_stability       : float   -- 1 - std(fingerprints) normalised
  continuity_class         : str     -- CONTINUOUS | DRIFTING | FRAGMENTED
  session_lengths          : List[int]  -- entry count per detected session
  gap_seconds              : List[float] -- gap durations at each boundary
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict

import numpy as np

# ── Constants ─────────────────────────────────────────────────────────────────

SESSION_GAP_SECS = 1800   # 30-minute gap → new session
MIN_PER_SESSION  = 3      # sessions with fewer entries are skipped

# Numeric fields to include in the fingerprint (must be float-castable)
_FINGERPRINT_KEYS = [
    "mean_phi_level", "phi_variability", "mean_novelty", "curiosity_index",
    "combined_continuity", "lz_current", "ego_strength_index",
    "bridge_strength", "phi_gap_norm", "cluster_sai",
]

# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class SessionIdentityResult:
    cross_session_continuity: float = 0.0
    n_sessions_detected: int = 0
    phi_drift: float = 0.0
    identity_stability: float = 0.0
    continuity_class: str = "FRAGMENTED"
    session_lengths: List[int] = field(default_factory=list)
    gap_seconds: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "cross_session_continuity": round(self.cross_session_continuity, 4),
            "n_sessions_detected": self.n_sessions_detected,
            "phi_drift": round(self.phi_drift, 4),
            "identity_stability": round(self.identity_stability, 4),
            "continuity_class": self.continuity_class,
            "session_lengths": self.session_lengths,
            "gap_seconds": [round(g, 1) for g in self.gap_seconds],
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

_EPS = 1e-9


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na < _EPS or nb < _EPS:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _fingerprint(entries: List[dict], keys: List[str]) -> Optional[np.ndarray]:
    """Mean fingerprint vector for a session's entries on the given keys."""
    cols = []
    for k in keys:
        vals = []
        for e in entries:
            v = e.get(k)
            if v is not None:
                try:
                    vals.append(float(v))
                except (TypeError, ValueError):
                    pass
        cols.append(float(np.mean(vals)) if vals else float("nan"))
    arr = np.asarray(cols, dtype=float)
    # Drop dimensions where either session has NaN
    return arr


def _classify(c: float) -> str:
    if c >= 0.90:
        return "CONTINUOUS"
    if c >= 0.70:
        return "DRIFTING"
    return "FRAGMENTED"


def _split_sessions(
    entries: List[dict], gap_secs: float = SESSION_GAP_SECS
) -> tuple[List[List[dict]], List[float]]:
    """Split timestamped history entries into sessions by time gap."""
    if not entries:
        return [], []

    # Entries from HistoryStore are newest-first; reverse for chronological order
    chron = list(reversed(entries))

    sessions: List[List[dict]] = []
    gaps: List[float] = []
    current: List[dict] = [chron[0]]

    for i in range(1, len(chron)):
        t_prev = chron[i - 1].get("timestamp", 0)
        t_curr = chron[i].get("timestamp", 0)
        if isinstance(t_prev, str):
            try: t_prev = float(datetime.fromisoformat(t_prev.replace("Z","")).timestamp())
            except: t_prev = 0.0
        if isinstance(t_curr, str):
            try: t_curr = float(datetime.fromisoformat(t_curr.replace("Z","")).timestamp())
            except: t_curr = 0.0
        gap = float(t_curr - t_prev)
        if gap >= gap_secs:
            sessions.append(current)
            gaps.append(gap)
            current = []
        current.append(chron[i])

    sessions.append(current)
    return sessions, gaps


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    agent: str = "albedo",
    *,
    session_gap_secs: float = SESSION_GAP_SECS,
    min_per_session: int = MIN_PER_SESSION,
    max_history: int = 2880,
) -> SessionIdentityResult:
    """
    Measure psychological identity continuity across detected sessions.

    Args:
        agent            : "albedo" or "john".
        session_gap_secs : Timestamp gap (seconds) marking a session boundary.
        min_per_session  : Minimum history entries for a session to be included.
        max_history      : Maximum history entries to load (default 2880 = 48 h).
    """
    try:
        from algorithms.ConsciousnessHistoryStore import load as _load_history
        entries = _load_history(agent, max_entries=max_history)
    except Exception:
        entries = []

    if len(entries) < min_per_session * 2:
        return SessionIdentityResult()

    sessions, gaps = _split_sessions(entries, gap_secs=session_gap_secs)

    # Keep only sessions with enough entries
    valid = [s for s in sessions if len(s) >= min_per_session]
    valid_lengths = [len(s) for s in valid]

    if len(valid) < 2:
        # Only one usable session — can't measure cross-session continuity
        return SessionIdentityResult(
            n_sessions_detected=len(sessions),
            session_lengths=valid_lengths,
            gap_seconds=gaps,
        )

    # Determine shared fingerprint keys (non-NaN in at least half of sessions)
    fp_raw = [_fingerprint(s, _FINGERPRINT_KEYS) for s in valid]
    # Find columns that are finite in at least half
    stacked = np.stack(fp_raw, axis=0)           # shape (n_sessions, n_keys)
    finite_mask = np.isfinite(stacked).mean(axis=0) >= 0.5
    if not finite_mask.any():
        return SessionIdentityResult(
            n_sessions_detected=len(sessions),
            session_lengths=valid_lengths,
            gap_seconds=gaps,
        )

    # Zero-fill NaN on selected columns
    fp_clean = stacked[:, finite_mask].copy()
    fp_clean = np.where(np.isfinite(fp_clean), fp_clean, 0.0)

    # Cosine similarity between consecutive session fingerprints
    sims = []
    for i in range(len(fp_clean) - 1):
        sims.append(_cosine(fp_clean[i], fp_clean[i + 1]))

    mean_sim = float(np.mean(sims)) if sims else 0.0

    # Phi drift: |Δmean_phi| across adjacent sessions
    phi_key_idx = None
    for ki, k in enumerate(_FINGERPRINT_KEYS):
        if k == "mean_phi_level" and finite_mask[ki]:
            phi_key_idx = int(np.where(finite_mask)[0][ki]) if ki < len(np.where(finite_mask)[0]) else None
            break

    phi_drifts = []
    if phi_key_idx is not None:
        phi_col_pos = list(np.where(finite_mask)[0]).index(
            [i for i, (k, f) in enumerate(zip(_FINGERPRINT_KEYS, finite_mask)) if k == "mean_phi_level" and f][0]
        ) if any(k == "mean_phi_level" and f for k, f in zip(_FINGERPRINT_KEYS, finite_mask)) else None
        if phi_col_pos is not None:
            phi_vals = fp_clean[:, phi_col_pos]
            phi_drifts = [abs(float(phi_vals[i+1] - phi_vals[i])) for i in range(len(phi_vals) - 1)]

    mean_phi_drift = float(np.mean(phi_drifts)) if phi_drifts else 0.0

    # Identity stability: 1 - normalised std of fingerprint vectors
    fp_norms = np.linalg.norm(fp_clean, axis=1)
    norm_std = float(np.std(fp_norms) / (np.mean(fp_norms) + _EPS))
    identity_stability = float(np.clip(1.0 - norm_std, 0.0, 1.0))

    return SessionIdentityResult(
        cross_session_continuity=round(float(np.clip(mean_sim, 0.0, 1.0)), 4),
        n_sessions_detected=len(sessions),
        phi_drift=round(mean_phi_drift, 4),
        identity_stability=round(identity_stability, 4),
        continuity_class=_classify(mean_sim),
        session_lengths=valid_lengths,
        gap_seconds=[round(g, 1) for g in gaps],
    )
