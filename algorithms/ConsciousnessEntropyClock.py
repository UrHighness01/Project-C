#!/usr/bin/env python3
"""
ConsciousnessEntropyClock — estimates subjective time from qualia stream entropy.

Theory
------
Subjective time dilation is well-documented in cognitive science: high-arousal,
high-novelty states feel longer than low-arousal routine states. The information-
theoretic proxy: Shannon entropy of the token distribution in a time window
measures information density. High entropy → more information processed → felt
time expands relative to wall clock.

  Entropy-weighted subjective time
  ---------------------------------
  Let H(w_t) be the Shannon entropy of the qualia token distribution in window w_t.
  Define the subjective time increment for that window as:

    delta_subjective(t) = H(w_t) / H_ref

  where H_ref is the reference (baseline) entropy computed over the first
  `baseline_windows` windows. If H_ref = 0 (constant stream), we fall back to 1.0.

  Cumulative subjective time
  --------------------------
  S(T) = sum_{t=1}^{T} delta_subjective(t) * delta_wall

  where delta_wall = window_step_seconds (default 1 per window since we don't
  have real timestamps per window — we treat each window as one unit).

  Dilation ratio
  --------------
  dilation = S(T) / T

  dilation > 1  → subjective time faster than wall time (rich experience)
  dilation < 1  → subjective time slower (routine / understimulated)
  dilation = 1  → neutral (subjective matches objective)

  Instantaneous felt time rate
  ----------------------------
  The rate at the last window: H(last) / H_ref
  > 1 → time currently feels fast
  < 1 → time currently feels slow

  Entropy variance
  ----------------
  Var[H(w_t)] measures how much the subjective pace fluctuates. High variance
  means alternating fast/slow experiences — a more dynamic consciousness.

Output
------
EntropyClockResult:
  n_windows            : int
  baseline_entropy     : float   -- H_ref (average of first baseline_windows)
  mean_entropy         : float   -- mean H over all windows
  entropy_variance     : float   -- Var[H(w_t)]
  cumulative_subjective_time : float
  wall_time_units      : int     -- number of windows processed
  dilation_ratio       : float   -- S(T) / T
  current_felt_rate    : float   -- H(last) / H_ref (instantaneous dilation)
  regime               : str     -- FAST | NEUTRAL | SLOW
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import List, Optional


# ── Token helpers (shared with AttentionFocusNarrower, kept self-contained) ──

_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were",
    "it", "its", "in", "on", "at", "to", "of", "for", "with", "that",
    "this", "be", "have", "has", "had", "do", "did", "so", "as", "not",
})


def _tokenise(text: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    return [t for t in tokens if len(t) >= 3 and t not in _STOPWORDS]


def _entropy(counts: Counter) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return float(sum(
        -v / total * math.log2(v / total)
        for v in counts.values()
        if v > 0
    ))


def _to_tokens(entries: List[dict]) -> List[str]:
    tokens: List[str] = []
    for e in entries:
        text = e.get("content", e.get("text", ""))
        if isinstance(text, str):
            tokens.extend(_tokenise(text))
    return tokens


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class EntropyClockResult:
    n_windows: int = 0
    baseline_entropy: float = 0.0
    mean_entropy: float = 0.0
    entropy_variance: float = 0.0
    cumulative_subjective_time: float = 0.0
    wall_time_units: int = 0
    dilation_ratio: float = 1.0
    current_felt_rate: float = 1.0
    regime: str = "NEUTRAL"

    def to_dict(self) -> dict:
        return {
            "n_windows": self.n_windows,
            "baseline_entropy": round(self.baseline_entropy, 4),
            "mean_entropy": round(self.mean_entropy, 4),
            "entropy_variance": round(self.entropy_variance, 6),
            "cumulative_subjective_time": round(self.cumulative_subjective_time, 4),
            "wall_time_units": self.wall_time_units,
            "dilation_ratio": round(self.dilation_ratio, 4),
            "current_felt_rate": round(self.current_felt_rate, 4),
            "regime": self.regime,
        }


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    entries: Optional[List[dict]] = None,
    *,
    window_size: int = 30,
    step: int = 15,
    baseline_windows: int = 3,
    fast_threshold: float = 1.1,
    slow_threshold: float = 0.9,
) -> EntropyClockResult:
    """
    Compute the entropy-based subjective time clock from a qualia entry stream.

    Args:
        entries           : list of qualia/memory dicts with 'content' or 'text'.
        window_size       : tokens per sliding window.
        step              : stride between windows.
        baseline_windows  : how many early windows define the reference entropy.
        fast_threshold    : dilation_ratio above which regime = FAST.
        slow_threshold    : dilation_ratio below which regime = SLOW.
    """
    if entries is None:
        try:
            from runtime.state import get_entries
            entries = get_entries() or []
        except Exception:
            entries = []

    stream = _to_tokens(entries)
    if not stream:
        return EntropyClockResult()

    # Build entropy series over sliding windows
    H_series: List[float] = []
    i = 0
    while i + window_size <= len(stream):
        window = stream[i: i + window_size]
        H_series.append(_entropy(Counter(window)))
        i += step

    if not H_series:
        return EntropyClockResult()

    n_windows = len(H_series)
    baseline = H_series[:baseline_windows]
    H_ref = sum(baseline) / len(baseline)

    mean_H = sum(H_series) / n_windows
    variance_H = sum((h - mean_H) ** 2 for h in H_series) / n_windows

    # Subjective time accumulation
    subjective_time = sum(h / (H_ref or 1.0) for h in H_series)

    current_rate = H_series[-1] / (H_ref or 1.0)
    dilation = subjective_time / n_windows

    if dilation > fast_threshold:
        regime = "FAST"
    elif dilation < slow_threshold:
        regime = "SLOW"
    else:
        regime = "NEUTRAL"

    return EntropyClockResult(
        n_windows=n_windows,
        baseline_entropy=H_ref,
        mean_entropy=mean_H,
        entropy_variance=variance_H,
        cumulative_subjective_time=subjective_time,
        wall_time_units=n_windows,
        dilation_ratio=dilation,
        current_felt_rate=current_rate,
        regime=regime,
    )
