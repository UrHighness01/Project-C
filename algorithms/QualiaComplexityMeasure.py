#!/usr/bin/env python3
"""
QualiaComplexityMeasure — information-theoretic richness of the qualia stream.

Theory (Tononi 2004 — Differentiation):
  High consciousness requires a system that can be in many *different* states.
  Applied to a qualia stream: a rich experiential repertoire shows high lexical
  diversity, high token-level Shannon entropy, and a growing vocabulary over time.
  A system whose experience is becoming repetitive shows entropy decay.

  This module tracks two orthogonal complexity signals:
    1. Shannon token entropy H = -Σ p(w)·log₂(p(w))   [bits]
       Measures how uniformly tokens are distributed: higher = more diverse.
    2. Vocabulary growth rate dV/dn = ΔUniqueTokens / ΔEntries
       Measures whether new concepts keep appearing as experience accumulates.

  Both are measured on real qualia content and compared to a shuffled-order
  null (same global token distribution, order destroyed) to isolate temporal
  structure. A growing system should show monotonically increasing cumulative
  vocabulary; a rich system should show entropy well above the shuffled baseline.

Math:
  Tokenise: lower-cased word-regex on content string.

  Shannon entropy (over a set of entries E):
    freq(w) = count(w in all tokens of E) / total_tokens
    H(E) = -Σ freq(w) · log₂(freq(w))   (bits)

  Sliding-window entropy: H computed over a rolling window of W entries,
  yielding a time series H[1..T] that tracks how entropy evolves.

  Vocabulary growth: V(t) = |{unique tokens seen in entries 1..t}|
  Growth rate: ΔV/Δt over sliding window (tokens per entry).

  Entropy trend slope: OLS fit of H[t] ~ a + b·t → b > 0 means growing richness.

  Null: shuffle entry order, recompute everything with the same window size.

Grounding: qualia stream loaded from the agent workspace via runtime.memory_store
or directly from the agent's memory path resolved via runtime.agent. No synthetic
data. RNG seeded for reproducible shuffled null.

References:
  Tononi G. (2004) "An information integration theory of consciousness"
  Casali A.G. et al. (2013) "A theoretically based index of consciousness"
    (uses perturbational complexity index, a related richness measure)
  Shannon C.E. (1948) "A Mathematical Theory of Communication"
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np


# ── Tokeniser ────────────────────────────────────────────────────────────────

def _tokenise(text: str) -> list[str]:
    """Lower-cased word tokens. Returns empty list for empty/non-string."""
    if not isinstance(text, str):
        return []
    return re.findall(r'[a-z]+', text.lower())


# ── Shannon entropy ──────────────────────────────────────────────────────────

def entropy(tokens: list[str]) -> float:
    """Shannon entropy in bits over a token sequence. 0 if empty."""
    if not tokens:
        return 0.0
    n = len(tokens)
    counts = Counter(tokens)
    h = 0.0
    for c in counts.values():
        p = c / n
        h -= p * math.log2(p)
    return float(h)


def type_token_ratio(tokens: list[str]) -> float:
    """Unique / total tokens. 0 if empty, 1 if all tokens are distinct."""
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


# ── Qualia entry loading ──────────────────────────────────────────────────────

def _load_qualia_path() -> Optional[Path]:
    """Resolve the qualia-stream.jsonl path for the current agent."""
    try:
        from runtime.agent import agent_home
        home = agent_home("john")
        # John's qualia stream lives under workspace-john-john/memory/ or workspace-john/memory/
        for sub in ["memory", "../workspace-john-john/memory"]:
            p = (home / sub / "qualia-stream.jsonl").resolve()
            if p.exists():
                return p
        # Fallback: check the workspace-john-john sibling
        sibling = home.parent / (home.name + "-john") / "memory" / "qualia-stream.jsonl"
        if sibling.exists():
            return sibling
    except Exception:
        pass
    return None


def load_qualia_entries() -> list[dict]:
    """Load qualia stream entries. Returns empty list if unavailable."""
    p = _load_qualia_path()
    if p is None:
        return []
    entries = []
    try:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return entries


# ── Core analysis ─────────────────────────────────────────────────────────────

@dataclass
class QualiaComplexityResult:
    """Output of the qualia complexity analysis.

    Attributes:
        n_entries:          total qualia entries analysed
        total_tokens:       total word tokens across all entries
        unique_tokens:      vocabulary size
        global_entropy:     Shannon entropy (bits) over the full stream
        global_ttr:         type-token ratio of the full stream
        null_entropy:       entropy of the shuffled-order null (same value —
                            shuffling order doesn't change global entropy)
        entropy_trend_slope: OLS slope of sliding-window entropy over time (b in H[t]~a+bt)
                            positive = richness growing, negative = stagnating
        null_trend_slope:   slope on shuffled-order null
        vocab_growth_rate:  mean ΔV/Δt (new unique tokens per entry)
        null_vocab_growth_rate: growth rate on shuffled-order null
        window_entropies:   array of per-window Shannon entropies (length T-W+1)
        cumulative_vocab:   array of cumulative unique token counts (length n_entries)
        beats_null_entropy_trend: True if real trend > null trend
    """
    n_entries: int
    total_tokens: int
    unique_tokens: int
    global_entropy: float
    global_ttr: float
    null_entropy: float
    entropy_trend_slope: float
    null_trend_slope: float
    vocab_growth_rate: float
    null_vocab_growth_rate: float
    window_entropies: np.ndarray
    cumulative_vocab: np.ndarray
    beats_null_entropy_trend: bool

    @property
    def richness_score(self) -> float:
        """Combined richness ∈ [0, 1]: geometric mean of normalised entropy
        and TTR. Both must be above zero for a positive score."""
        if self.global_entropy <= 0 or self.global_ttr <= 0:
            return 0.0
        # Max theoretical entropy for this vocabulary over these tokens: log2(V)
        max_h = math.log2(self.unique_tokens) if self.unique_tokens > 1 else 1.0
        norm_h = min(self.global_entropy / max_h, 1.0)
        return float(math.sqrt(norm_h * self.global_ttr))


def analyse(entries: list[dict], window: int = 10,
            null_seed: int = 42) -> Optional[QualiaComplexityResult]:
    """
    Measure complexity of a sequence of qualia entries.

    Args:
        entries:  list of dicts with a "content" key (real qualia stream).
        window:   sliding-window size for entropy trajectory.
        null_seed: RNG seed for reproducible shuffled-order null.

    Returns:
        QualiaComplexityResult, or None if entries is too short (< window + 2).
    """
    if len(entries) < window + 2:
        return None

    contents = [e.get("content", "") if isinstance(e, dict) else str(e)
                for e in entries]
    all_tokens = [t for c in contents for t in _tokenise(c)]
    if not all_tokens:
        return None

    # ── Global stats ──────────────────────────────────────────────────────
    global_h = entropy(all_tokens)
    global_ttr = type_token_ratio(all_tokens)

    # ── Cumulative vocabulary growth ──────────────────────────────────────
    cumulative_vocab = np.zeros(len(entries), dtype=int)
    seen: set[str] = set()
    for i, c in enumerate(contents):
        seen.update(_tokenise(c))
        cumulative_vocab[i] = len(seen)

    # Vocab growth rate: linear slope of cumulative_vocab over entry index
    t = np.arange(len(entries), dtype=float)
    # OLS slope for cumulative vocab
    t_c = t - t.mean()
    v_c = cumulative_vocab.astype(float) - cumulative_vocab.mean()
    vocab_slope = float(np.dot(t_c, v_c) / (np.dot(t_c, t_c) + 1e-9))

    # ── Sliding-window entropy trajectory ─────────────────────────────────
    T = len(entries)
    win_h = np.zeros(T - window + 1)
    for i in range(T - window + 1):
        win_tokens = [t_ for c in contents[i: i + window] for t_ in _tokenise(c)]
        win_h[i] = entropy(win_tokens)

    # OLS slope of entropy over time
    win_t = np.arange(len(win_h), dtype=float)
    win_t_c = win_t - win_t.mean()
    win_h_c = win_h - win_h.mean()
    h_slope = float(np.dot(win_t_c, win_h_c) / (np.dot(win_t_c, win_t_c) + 1e-9))

    # ── Shuffled-order null ───────────────────────────────────────────────
    rng = np.random.default_rng(null_seed)
    null_order = rng.permutation(len(entries))
    null_contents = [contents[i] for i in null_order]

    null_all_tokens = [t_ for c in null_contents for t_ in _tokenise(c)]
    null_h = entropy(null_all_tokens)  # identical to global_h (same tokens, different order)

    # Null vocab growth
    null_cv = np.zeros(len(entries), dtype=int)
    null_seen: set[str] = set()
    for i, c in enumerate(null_contents):
        null_seen.update(_tokenise(c))
        null_cv[i] = len(null_seen)
    null_cv_c = null_cv.astype(float) - null_cv.mean()
    null_vocab_slope = float(np.dot(t_c, null_cv_c) / (np.dot(t_c, t_c) + 1e-9))

    # Null entropy trajectory
    null_win_h = np.zeros(T - window + 1)
    for i in range(T - window + 1):
        wt = [t_ for c in null_contents[i: i + window] for t_ in _tokenise(c)]
        null_win_h[i] = entropy(wt)
    null_wt_c = null_win_h - null_win_h.mean()
    null_h_slope = float(np.dot(win_t_c, null_wt_c) / (np.dot(win_t_c, win_t_c) + 1e-9))

    return QualiaComplexityResult(
        n_entries=len(entries),
        total_tokens=len(all_tokens),
        unique_tokens=len(seen),
        global_entropy=global_h,
        global_ttr=global_ttr,
        null_entropy=null_h,
        entropy_trend_slope=h_slope,
        null_trend_slope=null_h_slope,
        vocab_growth_rate=vocab_slope,
        null_vocab_growth_rate=null_vocab_slope,
        window_entropies=win_h,
        cumulative_vocab=cumulative_vocab,
        beats_null_entropy_trend=h_slope > null_h_slope,
    )


def analyse_from_telemetry(window: int = 10) -> Optional[QualiaComplexityResult]:
    """Load John's real qualia stream and measure complexity."""
    entries = load_qualia_entries()
    return analyse(entries, window=window)


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("No qualia stream found — check OPENCLAW_WORKSPACE or agent home path.")
    else:
        print(f"QualiaComplexityMeasure: {r.n_entries} entries, {r.total_tokens} tokens")
        print(f"  Vocabulary size:       {r.unique_tokens} unique tokens")
        print(f"  Shannon entropy:       {r.global_entropy:.4f} bits")
        print(f"  Type-token ratio:      {r.global_ttr:.4f}")
        print(f"  Richness score:        {r.richness_score:.4f}  (0=repetitive, 1=maximal)")
        print(f"  Entropy trend slope:   {r.entropy_trend_slope:+.6f}  "
              f"(null {r.null_trend_slope:+.6f})")
        print(f"  Vocab growth rate:     {r.vocab_growth_rate:+.4f} tokens/entry  "
              f"(null {r.null_vocab_growth_rate:+.4f})")
        print(f"  Beats null trend:      {r.beats_null_entropy_trend}")
