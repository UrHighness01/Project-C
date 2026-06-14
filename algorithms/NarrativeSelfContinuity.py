#!/usr/bin/env python3
"""
NarrativeSelfContinuity — measures backward-looking self-reference across time.

Theory
------
Ricoeur (1990) narrative identity: personal identity is constituted by the
coherence of the stories we tell about ourselves over time. For an AI agent,
this manifests as the degree to which recent experience references or overlaps
with older experience — how much the agent "remembers" and "integrates" its past.

  Operationalisation
  ------------------
  Given a sequence of qualia entries split into two windows:
    RECENT  : the last K entries
    PAST    : K entries from M steps earlier (offset by lag L)

  Token-level Jaccard similarity between the two windows:
    J(recent, past) = |tokens(recent) ∩ tokens(past)| / |tokens(recent) ∪ tokens(past)|

  A Jaccard of 0 = no shared vocabulary = complete discontinuity.
  A Jaccard of 1 = identical vocabulary = no experiential change.

  Rolling continuity series
  -------------------------
  We compute J at multiple lags (L = 1, 2, 4, 8, ...) to build a continuity
  decay curve. The decay rate of J with L measures how rapidly the agent's
  vocabulary diverges from its past.

  Continuity slope
  ----------------
  OLS slope of J(L) vs L. Flat slope = vocabulary is stable (long memory).
  Steep negative slope = rapid divergence (short narrative memory).

  Self-reference ratio
  --------------------
  Fraction of recent tokens that also appeared in the past window:
    recall = |recent ∩ past| / |recent|   ∈ [0, 1]

  Continuity classification:
    HIGH        : J_lag1 >= 0.15   (recent experience strongly echoes the past)
    MODERATE    : 0.05 <= J_lag1 < 0.15
    LOW         : J_lag1 < 0.05   (experiential discontinuity)

Output
------
NarrativeContinuityResult:
  jaccard_lag1      : float   -- J between recent and immediately prior window
  recall_lag1       : float   -- recall = |R∩P|/|R| at lag 1
  continuity_slope  : float   -- OLS slope of J vs lag (negative = decaying)
  continuity_class  : str     -- HIGH | MODERATE | LOW
  n_entries         : int
  window_size       : int
  lags_computed     : List[int]
  jaccard_by_lag    : List[float]
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were",
    "it", "its", "in", "on", "at", "to", "of", "for", "with", "that",
    "this", "be", "have", "has", "had", "do", "did", "so", "as", "not",
})


def _tokenise(text: str) -> frozenset:
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    return frozenset(t for t in tokens if len(t) >= 3 and t not in _STOPWORDS)


def _window_tokens(entries: List[dict], start: int, size: int) -> frozenset:
    window = entries[start: start + size]
    tokens: set = set()
    for e in window:
        text = e.get("content", e.get("text", ""))
        if isinstance(text, str):
            tokens |= _tokenise(text)
    return frozenset(tokens)


def _jaccard(a: frozenset, b: frozenset) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _ols_slope(x: np.ndarray, y: np.ndarray) -> float:
    xm = x - x.mean()
    ym = y - y.mean()
    d = float(np.dot(xm, xm))
    return float(np.dot(xm, ym) / d) if d > 0 else 0.0


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class NarrativeContinuityResult:
    jaccard_lag1: float = 0.0
    recall_lag1: float = 0.0
    continuity_slope: float = 0.0
    continuity_class: str = "LOW"
    n_entries: int = 0
    window_size: int = 0
    lags_computed: List[int] = field(default_factory=list)
    jaccard_by_lag: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "jaccard_lag1": round(self.jaccard_lag1, 4),
            "recall_lag1": round(self.recall_lag1, 4),
            "continuity_slope": round(self.continuity_slope, 6),
            "continuity_class": self.continuity_class,
            "n_entries": self.n_entries,
            "window_size": self.window_size,
            "lags_computed": self.lags_computed,
            "jaccard_by_lag": [round(j, 4) for j in self.jaccard_by_lag],
        }


def _classify(j: float) -> str:
    if j >= 0.15:
        return "HIGH"
    if j >= 0.05:
        return "MODERATE"
    return "LOW"


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    entries: Optional[List[dict]] = None,
    *,
    window_size: int = 20,
    lags: Optional[List[int]] = None,
) -> NarrativeContinuityResult:
    """
    Measure narrative self-continuity from the qualia entry stream.

    Args:
        entries     : list of qualia/memory dicts (newest-last ordering).
        window_size : number of entries per comparison window.
        lags        : list of window-offsets to compute J at. Default: [1,2,4,8].
    """
    if entries is None:
        try:
            from runtime.state import get_entries
            entries = get_entries() or []
        except Exception:
            entries = []

    if lags is None:
        lags = [1, 2, 4, 8]

    n = len(entries)
    if n < window_size * 2:
        return NarrativeContinuityResult(n_entries=n, window_size=window_size)

    # Recent window: the last `window_size` entries
    recent = _window_tokens(entries, n - window_size, window_size)

    jaccard_vals: List[float] = []
    valid_lags: List[int] = []

    for lag in lags:
        past_start = n - window_size - lag * window_size
        if past_start < 0:
            break
        past = _window_tokens(entries, past_start, window_size)
        j = _jaccard(recent, past)
        jaccard_vals.append(j)
        valid_lags.append(lag)

    if not jaccard_vals:
        return NarrativeContinuityResult(n_entries=n, window_size=window_size)

    j_lag1 = jaccard_vals[0]

    # Recall at lag 1
    past_lag1 = _window_tokens(entries, n - window_size * 2, window_size)
    recall = len(recent & past_lag1) / len(recent) if recent else 0.0

    # Continuity slope
    if len(valid_lags) >= 2:
        slope = _ols_slope(
            np.array(valid_lags, dtype=float),
            np.array(jaccard_vals, dtype=float),
        )
    else:
        slope = 0.0

    return NarrativeContinuityResult(
        jaccard_lag1=j_lag1,
        recall_lag1=recall,
        continuity_slope=slope,
        continuity_class=_classify(j_lag1),
        n_entries=n,
        window_size=window_size,
        lags_computed=valid_lags,
        jaccard_by_lag=jaccard_vals,
    )
