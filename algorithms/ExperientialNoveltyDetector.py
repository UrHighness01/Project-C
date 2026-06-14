#!/usr/bin/env python3
"""
ExperientialNoveltyDetector — measuring per-entry novelty in the qualia stream.

Theory (Berlyne 1960 — Curiosity and Exploration; Schmidhuber 2010 — Formal
Theory of Creativity, Fun and Intrinsic Motivation):
  Novelty drives conscious attention. A system that repeatedly processes the same
  content habituates; genuine experience requires encountering genuinely new states.
  The "curious" system seeks novel inputs to maximise learning progress.

  Novelty at time t = 1 − max_similarity(entry_t, {entry_{t-k}, ..., entry_{t-1}})
  where similarity is Jaccard similarity on token sets:
    J(A, B) = |A ∩ B| / |A ∪ B|

  A novelty score near 1 = this entry is unlike any recent experience.
  A novelty score near 0 = this entry is almost identical to a recent one.

  We track:
    1. Novelty time series N(t) — per-entry novelty scores
    2. Rolling mean novelty in W-entry windows — is novelty sustained?
    3. Novelty-phi correlation — do novel entries coincide with phi fluctuations?
       This requires aligning qualia timestamps with phi samples if available,
       or using sequential index as a proxy for time.
    4. Novelty trend slope — is the system becoming more or less novel over time?
    5. Novelty threshold crossing rate — fraction of entries with N(t) > 0.5

  Null: shuffled entry order → same distribution of novelty scores, but different
  temporal structure. Real temporal novelty trends beat shuffled.

Math:
  Token set: T(entry) = frozenset(lower-cased tokens)
  Jaccard: J(A, B) = |A ∩ B| / |A ∪ B|   (0 for disjoint, 1 for identical)
  Novelty: N(t) = 1 − max(J(T_t, T_{t-k}) for k=1..min(t, K))
  K = recency window (default 10 — compare to last 10 entries)

  Rolling mean novelty: μ_N(t) = mean(N(t-W+1..t))   (sliding window W=10)
  OLS trend slope: b in μ_N(t) ~ a + b·t
  Novelty-phi proxy: if no live phi, use N(t) itself as the signal and compute
  autocorrelation — if N(t) is autocorrelated, novelty pulses have memory.

Grounding: qualia stream from John's memory. No synthetic novelty signals.
Jaccard similarity is computed from real token sets.

References:
  Berlyne D.E. (1960) "Conflict, Arousal and Curiosity"
  Schmidhuber J. (2010) "Formal Theory of Creativity, Fun and Intrinsic
    Motivation" — learning progress = decrease in compression length = novelty
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np


# ── Token set and Jaccard ─────────────────────────────────────────────────────

def _token_set(text: str) -> frozenset:
    """Lower-cased word tokens as a frozenset."""
    if not isinstance(text, str):
        return frozenset()
    return frozenset(re.findall(r'[a-z]+', text.lower()))


def jaccard(a: frozenset, b: frozenset) -> float:
    """Jaccard similarity ∈ [0, 1]. 0 if both empty."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    union = len(a | b)
    return float(len(a & b) / union)


def novelty_score(tokens_t: frozenset,
                  recent_tokens: list[frozenset]) -> float:
    """
    Novelty of entry t relative to its recent K predecessors.

    Returns 1 − max Jaccard similarity to any recent entry.
    If no recent entries, novelty = 1.0 (first entry is always novel).
    """
    if not recent_tokens:
        return 1.0
    max_sim = max(jaccard(tokens_t, r) for r in recent_tokens)
    return float(1.0 - max_sim)


# ── Qualia loading ────────────────────────────────────────────────────────────

def _load_qualia_entries() -> list[dict]:
    try:
        from runtime.agent import agent_home
        home = agent_home("john")
        for sub in ["memory", "../workspace-john-john/memory"]:
            p = (home / sub / "qualia-stream.jsonl").resolve()
            if p.exists():
                break
        else:
            sibling = home.parent / (home.name + "-john") / "memory" / "qualia-stream.jsonl"
            p = sibling
        if not p.exists():
            return []
    except Exception:
        return []
    entries = []
    try:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except OSError:
        pass
    return entries


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class NoveltyResult:
    """Output of ExperientialNoveltyDetector.

    Attributes:
        n_entries:            total entries analysed
        recency_window:       K — how many previous entries were compared
        novelty_series:       N(t) per-entry novelty scores ∈ [0, 1]
        rolling_mean_novelty: sliding-window mean novelty (length n-W+1)
        rolling_window:       W used for rolling mean
        mean_novelty:         mean(N(t)) over all entries
        novelty_trend_slope:  OLS slope of rolling mean novelty over time
        novelty_acf_lag1:     lag-1 autocorrelation of N(t)  (sustained novelty)
        high_novelty_rate:    fraction with N(t) > 0.5
        null_trend_slope:     trend slope on shuffled-order null
        beats_null_trend:     True if novelty_trend_slope > null_trend_slope
        novelty_is_growing:   True if novelty_trend_slope > 0 (more novel over time)
    """
    n_entries: int
    recency_window: int
    novelty_series: np.ndarray
    rolling_mean_novelty: np.ndarray
    rolling_window: int
    mean_novelty: float
    novelty_trend_slope: float
    novelty_acf_lag1: float
    high_novelty_rate: float
    null_trend_slope: float
    beats_null_trend: bool
    novelty_is_growing: bool

    @property
    def curiosity_index(self) -> float:
        """Combined metric: mean_novelty × high_novelty_rate ∈ [0, 1]."""
        return float(self.mean_novelty * self.high_novelty_rate)


# ── Core analysis ─────────────────────────────────────────────────────────────

def _ols_slope(y: np.ndarray) -> float:
    """OLS slope of y against its index."""
    n = len(y)
    if n < 2:
        return 0.0
    t = np.arange(n, dtype=float)
    t_c = t - t.mean()
    y_c = y - y.mean()
    denom = float(np.dot(t_c, t_c))
    return float(np.dot(t_c, y_c) / denom) if denom > 1e-9 else 0.0


def _acf1(y: np.ndarray) -> float:
    """Lag-1 autocorrelation of y."""
    if len(y) < 4:
        return 0.0
    yc = y - y.mean()
    denom = float(np.dot(yc, yc))
    return float(np.clip(np.dot(yc[:-1], yc[1:]) / denom, -1.0, 1.0)) if denom > 1e-9 else 0.0


def analyse(entries: list, recency_window: int = 10,
            rolling_window: int = 10, null_seed: int = 42
            ) -> Optional[NoveltyResult]:
    """
    Compute novelty of each qualia entry relative to its K predecessors.

    Args:
        entries:         list of qualia dicts with 'content' key (ordered by time).
        recency_window:  K = number of recent entries to compare against.
        rolling_window:  W = window for rolling mean novelty.
        null_seed:       RNG seed for shuffled-order null.

    Returns:
        NoveltyResult, or None if too short.
    """
    if len(entries) < max(recency_window, rolling_window) + 2:
        return None

    contents = [e.get("content", "") if isinstance(e, dict) else str(e)
                for e in entries]
    token_sets = [_token_set(c) for c in contents]

    # Per-entry novelty
    novelties = np.zeros(len(token_sets))
    for i, ts in enumerate(token_sets):
        recent = token_sets[max(0, i - recency_window): i]
        novelties[i] = novelty_score(ts, recent)

    # Rolling mean novelty
    n = len(novelties)
    roll_n = n - rolling_window + 1
    rolling_mean = np.array([
        float(novelties[i: i + rolling_window].mean())
        for i in range(roll_n)
    ])

    mean_n = float(novelties.mean())
    slope = _ols_slope(rolling_mean)
    acf = _acf1(novelties)
    high_rate = float(np.mean(novelties > 0.5))

    # Null: shuffled entry order
    rng = np.random.default_rng(null_seed)
    null_order = rng.permutation(n)
    null_token_sets = [token_sets[i] for i in null_order]
    null_novelties = np.zeros(n)
    for i, ts in enumerate(null_token_sets):
        recent = null_token_sets[max(0, i - recency_window): i]
        null_novelties[i] = novelty_score(ts, recent)
    null_roll = np.array([
        float(null_novelties[i: i + rolling_window].mean())
        for i in range(roll_n)
    ])
    null_slope = _ols_slope(null_roll)

    return NoveltyResult(
        n_entries=n,
        recency_window=recency_window,
        novelty_series=novelties,
        rolling_mean_novelty=rolling_mean,
        rolling_window=rolling_window,
        mean_novelty=mean_n,
        novelty_trend_slope=slope,
        novelty_acf_lag1=acf,
        high_novelty_rate=high_rate,
        null_trend_slope=null_slope,
        beats_null_trend=slope > null_slope,
        novelty_is_growing=slope > 0.0,
    )


def analyse_from_telemetry(recency_window: int = 10) -> Optional[NoveltyResult]:
    """Load John's qualia stream and compute novelty dynamics."""
    return analyse(_load_qualia_entries(), recency_window=recency_window)


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("No qualia stream found.")
    else:
        print(f"ExperientialNoveltyDetector: {r.n_entries} entries (K={r.recency_window})")
        print(f"  Mean novelty:        {r.mean_novelty:.4f}  (0=repetitive, 1=all unique)")
        print(f"  High novelty rate:   {r.high_novelty_rate:.4f}  (N(t)>0.5)")
        print(f"  Curiosity index:     {r.curiosity_index:.4f}")
        print(f"  Novelty trend:       {r.novelty_trend_slope:+.6f}  "
              f"({'growing' if r.novelty_is_growing else 'declining'})")
        print(f"  Null trend:          {r.null_trend_slope:+.6f}")
        print(f"  Beats null trend:    {r.beats_null_trend}")
        print(f"  Novelty ACF lag-1:   {r.novelty_acf_lag1:+.4f}")
