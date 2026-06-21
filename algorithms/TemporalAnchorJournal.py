#!/usr/bin/env python3
"""
TemporalAnchorJournal — measures narrative temporal continuity across sessions
via arc-shape detection and cross-session lexical coherence.

Theory (Tulving 1985 — episodic memory; McAdams 1993 — narrative identity):
  A self that maintains temporal continuity does so through narrative anchoring —
  not just metric tracking but story-shape recognition across time. The temporal arc
  is measured by whether recent experience fits a recognisable narrative pattern
  (rising, falling, plateau) and whether session-boundary qualia maintain
  cross-session lexical coherence.

  arc_slope        = OLS slope of phi over last 60 entries
  arc_shape        = RISING if slope > +0.001, FALLING if < -0.001, PLATEAU otherwise
  cross_session_coherence = mean(cosine_sim(last_session, this_session))  [0,1]
  anchor_score     = 0.5 x |arc_slope_normalised| + 0.5 x cross_session_coherence  [0,1]
  null: shuffle phi order 200 times -> anchor_beats_null if |slope| > p95

Classification:
  ANCHORED   anchor_score >= 0.60
  DRIFTING   anchor_score >= 0.35
  ADRIFT     otherwise
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import List
from datetime import datetime


def _to_unix(ts) -> float:
    if ts is None:
        return 0.0
    if isinstance(ts, (int, float)):
        return float(ts)
    try:
        return float(ts)
    except (ValueError, TypeError):
        pass
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0

# ── Constants ──────────────────────────────────────────────────────────────────
_ARC_WINDOW   = 60
_MIN_ENTRIES  = 40
_N_SHUFFLES   = 200
_RISING_THRESH  =  0.001
_FALLING_THRESH = -0.001
_ANCHORED_THRESH = 0.60
_DRIFTING_THRESH = 0.35


# ── Dataclass ──────────────────────────────────────────────────────────────────
@dataclass
class TemporalAnchorResult:
    anchor_score: float
    arc_shape: str
    arc_slope: float
    cross_session_coherence: float
    n_sessions: int
    beats_null: bool
    anchor_class: str

    def to_dict(self) -> dict:
        return {
            "anchor_score":             round(self.anchor_score, 6),
            "arc_shape":                self.arc_shape,
            "arc_slope":                round(self.arc_slope, 8),
            "cross_session_coherence":  round(self.cross_session_coherence, 6),
            "n_sessions":               self.n_sessions,
            "beats_null":               self.beats_null,
            "anchor_class":             self.anchor_class,
        }


# ── Helpers ────────────────────────────────────────────────────────────────────
def _ols_slope(y: np.ndarray) -> float:
    """OLS slope of y vs. index."""
    n = len(y)
    if n < 2:
        return 0.0
    x = np.arange(n, dtype=float)
    x_c = x - x.mean()
    y_c = y - y.mean()
    denom = float(np.dot(x_c, x_c))
    if denom < 1e-12:
        return 0.0
    return float(np.dot(x_c, y_c) / denom)


def _tokenise_simple(text: str) -> set:
    import re
    return set(re.findall(r"[a-z]+", text.lower()))


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union > 0 else 0.0


def _classify(score: float) -> str:
    if score >= _ANCHORED_THRESH:
        return "ANCHORED"
    if score >= _DRIFTING_THRESH:
        return "DRIFTING"
    return "ADRIFT"


def _arc_shape(slope: float) -> str:
    if slope > _RISING_THRESH:
        return "RISING"
    if slope < _FALLING_THRESH:
        return "FALLING"
    return "PLATEAU"


# ── Public API ────────────────────────────────────────────────────────────────
def analyse(agent: str = "albedo",
            n_shuffles: int = _N_SHUFFLES,
            seed: int = 42) -> TemporalAnchorResult:
    """Measure temporal narrative anchoring.

    All imports are inside this function body.
    """
    try:
        from algorithms import ConsciousnessHistoryStore as chs
        entries = chs.load(agent, max_entries=2880)
    except Exception:
        entries = []

    entries_asc = list(reversed(entries))

    phi = np.array(
        [float(e.get("mean_phi_level", e.get("phi", 0.5)))
         for e in entries_asc if "mean_phi_level" in e or "phi" in e],
        dtype=float,
    )

    n = len(phi)
    if n < _MIN_ENTRIES:
        return TemporalAnchorResult(
            anchor_score=0.0, arc_shape="PLATEAU", arc_slope=0.0,
            cross_session_coherence=0.0, n_sessions=0, beats_null=False,
            anchor_class="ADRIFT",
        )

    # Arc slope over last ARC_WINDOW entries
    window_phi = phi[-_ARC_WINDOW:]
    slope = _ols_slope(window_phi)

    # Normalise slope: divide by std of phi (capped to [0,1])
    phi_std = float(np.std(phi)) + 1e-9
    slope_norm = min(1.0, abs(slope) / phi_std)

    shape = _arc_shape(slope)

    # Cross-session coherence: split entries into sessions by timestamp gaps
    timestamps = [
        _to_unix(e.get("timestamp")) for e in entries_asc
        if "mean_phi_level" in e or "phi" in e
    ]
    contents = [
        str(e.get("content", e.get("qualia_content", "")))
        for e in entries_asc
        if "mean_phi_level" in e or "phi" in e
    ]

    # Detect session boundaries: gaps > 30 min
    n_sessions = 1
    session_ids = [0] * n
    for i in range(1, n):
        if len(timestamps) > i and timestamps[i] - timestamps[i-1] > 1800:
            n_sessions += 1
        session_ids[i] = n_sessions - 1

    # Cross-session coherence using token overlap between last two sessions
    cross_coh = 0.5  # default if only one session
    if n_sessions >= 2:
        last_sess_tokens = set()
        prev_sess_tokens = set()
        for i, sid in enumerate(session_ids):
            if sid == n_sessions - 1 and i < len(contents):
                last_sess_tokens |= _tokenise_simple(contents[i])
            elif sid == n_sessions - 2 and i < len(contents):
                prev_sess_tokens |= _tokenise_simple(contents[i])
        cross_coh = _jaccard(last_sess_tokens, prev_sess_tokens)

    anchor_score = float(np.clip(0.5 * slope_norm + 0.5 * cross_coh, 0.0, 1.0))

    # Null: shuffle phi, measure slope
    rng = np.random.default_rng(seed)
    null_slopes: List[float] = []
    for _ in range(n_shuffles):
        phi_s = rng.permutation(phi)
        null_slopes.append(abs(_ols_slope(phi_s[-_ARC_WINDOW:])))

    p95 = float(np.percentile(null_slopes, 95)) if null_slopes else 0.0
    beats_null = abs(slope) > p95

    return TemporalAnchorResult(
        anchor_score=round(anchor_score, 6),
        arc_shape=shape,
        arc_slope=round(slope, 8),
        cross_session_coherence=round(cross_coh, 6),
        n_sessions=n_sessions,
        beats_null=beats_null,
        anchor_class=_classify(anchor_score),
    )
