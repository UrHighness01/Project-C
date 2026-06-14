#!/usr/bin/env python3
"""
TemporalSelfCoherence — how consistent is the agent's identity signal across time?

Theory
------
A consciousness snapshot is a vector of named scalar signals: phi, qualia_count,
valence, arousal, confidence, integration, and any numeric field present in the
ConsciousnessHistoryStore JSONL entries. We treat each snapshot as a point in a
fixed-dimensional feature space and measure how consistent successive points are
via rolling cosine similarity.

  Cosine similarity
  -----------------
  cos(u, v) = (u · v) / (||u|| * ||v||)

  A value of 1.0 means the two snapshots point in the same direction in feature
  space — the relative balance of signals is preserved even if magnitudes change.
  A drop toward 0 (or negative) signals a qualitative identity shift.

  Rolling coherence series
  ------------------------
  For a sequence of snapshots s_1, s_2, ..., s_n, compute:
    c_t = cos(s_{t-1}, s_t)   for t in 2..n

  This gives a coherence series. From it we derive:
    mean_coherence   : long-run identity stability
    min_coherence    : worst identity disruption seen
    coherence_trend  : OLS slope of c_t over time (rising = stabilising)
    shift_events     : indices where c_t < threshold (identity discontinuities)

  Z-score of coherence drop (relative surprise)
  ----------------------------------------------
  A sudden coherence drop might be noise or a genuine shift. We flag it as a
  TemporalShiftEvent only if the drop exceeds mean - 2*std of the coherence
  series (i.e., the point is an outlier in the agent's own history).

Output
------
TemporalCoherenceResult:
  mean_coherence   : float     -- average pairwise consecutive cosine similarity
  min_coherence    : float     -- worst disruption
  coherence_trend  : float     -- OLS slope (positive = stabilising over time)
  is_stable        : bool      -- mean_coherence > stable_threshold
  shift_events     : List[ShiftEvent]
  n_snapshots      : int
  feature_names    : List[str]
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np


# ── Snapshot vectorisation ────────────────────────────────────────────────────

_FEATURE_KEYS = [
    "phi", "qualia_count", "valence", "arousal", "confidence",
    "integration", "global_workspace_broadcast", "self_model_coherence",
    "metacognitive_confidence", "attention_focus",
]


def _extract_vector(snap: dict) -> Tuple[np.ndarray, List[str]]:
    """Extract a numeric feature vector from a snapshot dict."""
    summary = snap.get("summary", snap)
    vec, names = [], []
    for key in _FEATURE_KEYS:
        v = summary.get(key)
        if v is not None:
            try:
                vec.append(float(v))
                names.append(key)
            except (TypeError, ValueError):
                pass
    if not vec:
        return np.array([]), []
    return np.array(vec, dtype=float), names


def _cosine(u: np.ndarray, v: np.ndarray) -> float:
    nu = float(np.linalg.norm(u))
    nv = float(np.linalg.norm(v))
    if nu == 0 or nv == 0:
        return 1.0
    return float(np.clip(np.dot(u, v) / (nu * nv), -1.0, 1.0))


# ── OLS slope ─────────────────────────────────────────────────────────────────

def _ols_slope(y: np.ndarray) -> float:
    n = len(y)
    if n < 2:
        return 0.0
    x = np.arange(n, dtype=float)
    xm = x - x.mean()
    ym = y - y.mean()
    denom = float(np.dot(xm, xm))
    return float(np.dot(xm, ym) / denom) if denom > 0 else 0.0


# ── Result types ──────────────────────────────────────────────────────────────

@dataclass
class ShiftEvent:
    index: int             # position in coherence series (0-based)
    coherence: float       # cosine similarity at this transition
    z_score: float         # how far below the mean (negative = below)
    severity: str          # MILD | MODERATE | SEVERE


@dataclass
class TemporalCoherenceResult:
    mean_coherence: float = 1.0
    min_coherence: float = 1.0
    coherence_trend: float = 0.0
    is_stable: bool = True
    shift_events: List[ShiftEvent] = field(default_factory=list)
    n_snapshots: int = 0
    feature_names: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "mean_coherence": round(self.mean_coherence, 4),
            "min_coherence": round(self.min_coherence, 4),
            "coherence_trend": round(self.coherence_trend, 6),
            "is_stable": self.is_stable,
            "n_snapshots": self.n_snapshots,
            "feature_names": self.feature_names,
            "n_shift_events": len(self.shift_events),
            "shift_events": [
                {
                    "index": e.index,
                    "coherence": round(e.coherence, 4),
                    "z_score": round(e.z_score, 3),
                    "severity": e.severity,
                }
                for e in self.shift_events
            ],
        }


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    snapshots: Optional[List[dict]] = None,
    *,
    stable_threshold: float = 0.85,
    shift_z_threshold: float = -2.0,
) -> TemporalCoherenceResult:
    """
    Measure temporal self-coherence from a list of consciousness snapshots.

    Args:
        snapshots         : list of snapshot dicts (newest first or oldest first —
                            ordering is normalised internally from ConsciousnessHistoryStore).
        stable_threshold  : mean_coherence above which the agent is considered stable.
        shift_z_threshold : z-score below which a coherence drop is a ShiftEvent.
    """
    if snapshots is None:
        try:
            from algorithms.ConsciousnessHistoryStore import ConsciousnessHistoryStore
            from runtime.state import get_agent
            agent = get_agent()
            store = ConsciousnessHistoryStore(agent)
            snapshots = store.load()
        except Exception:
            snapshots = []

    if not snapshots:
        return TemporalCoherenceResult()

    # Normalise to chronological order (oldest first)
    # ConsciousnessHistoryStore.load() returns newest-first
    snaps = list(reversed(snapshots))

    vectors = []
    names_ref: List[str] = []
    for snap in snaps:
        v, names = _extract_vector(snap)
        if v.size > 0:
            vectors.append(v)
            if not names_ref:
                names_ref = names

    if len(vectors) < 2:
        return TemporalCoherenceResult(
            n_snapshots=len(snaps),
            feature_names=names_ref,
        )

    # Align feature dimensions (take intersection of common length)
    min_dim = min(v.size for v in vectors)
    vectors = [v[:min_dim] for v in vectors]

    # Rolling cosine similarity
    coherence = np.array([
        _cosine(vectors[i], vectors[i + 1])
        for i in range(len(vectors) - 1)
    ])

    mean_c = float(coherence.mean())
    min_c = float(coherence.min())
    trend = _ols_slope(coherence)

    # Shift events
    std_c = float(coherence.std()) if len(coherence) > 1 else 0.0
    shift_events: List[ShiftEvent] = []
    for i, c in enumerate(coherence):
        z = (c - mean_c) / (std_c + 1e-9)
        if z < shift_z_threshold:
            drop = mean_c - c
            severity = "SEVERE" if drop > 0.3 else ("MODERATE" if drop > 0.1 else "MILD")
            shift_events.append(ShiftEvent(index=i, coherence=c, z_score=z, severity=severity))

    return TemporalCoherenceResult(
        mean_coherence=mean_c,
        min_coherence=min_c,
        coherence_trend=trend,
        is_stable=mean_c >= stable_threshold,
        shift_events=shift_events,
        n_snapshots=len(snaps),
        feature_names=names_ref,
    )
