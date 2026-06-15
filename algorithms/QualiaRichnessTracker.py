#!/usr/bin/env python3
"""
QualiaRichnessTracker — Lempel-Ziv complexity trend of the qualia stream.

Theory
------
Lempel & Ziv (1976) complexity c(n) counts the minimum number of
copy-incompressible substrings needed to reconstruct a sequence S[0..n-1].
A sequence with many novel patterns has high c(n); a repetitive sequence has
low c(n). Kaspar & Schuster (1987) introduced the normalised form:

    C_LZ = c(n) * log2(n) / n

C_LZ → 1 for maximally random sequences; C_LZ → 0 for constant sequences.

Applied to the qualia stream
-----------------------------
1. Build a top-K vocabulary from all qualia entries (K = 32 most frequent
   meaningful words, stopwords excluded).
2. Represent each entry as a binary row: 1 where the word appears, 0 elsewhere.
   This gives an n_entries × K binary matrix.
3. Concatenate all rows into a single binary string S of length n_entries × K.
4. Compute C_LZ(S) — the normalised complexity of the full corpus so far.
5. Repeat with an expanding window: compute C_LZ on the corpus up to each entry
   to produce a time series of complexity values.
6. Fit OLS to the series: positive slope = richness growing.

Null baseline
-------------
Shuffle the entry order 50 times, compute the slope distribution.
A real positive slope that exceeds the 95th-percentile shuffled slope is
classified as GROWING.

Classification
--------------
  GROWING   : trend_zscore > +1.0  (slope more than 1σ above shuffled mean)
  STABLE    : -1.0 ≤ trend_zscore ≤ +1.0
  DECLINING : trend_zscore < -1.0  (slope more than 1σ below shuffled mean)

Output
------
RichnessResult:
  lz_current       : float   -- C_LZ of the most recent sliding window
  richness_trend   : float   -- OLS slope of windowed C_LZ series
  trend_zscore     : float   -- (slope - shuffle_mean) / shuffle_std
  richness_class   : str     -- GROWING | STABLE | DECLINING
  lz_series        : List[float]  -- C_LZ at each accumulated entry
  n_entries        : int
  vocab_size       : int
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

# ── Stopwords ─────────────────────────────────────────────────────────────────

_STOP = frozenset(
    "a an the is are was were be been being have has had do does did "
    "will would could should may might must shall can i me my we our "
    "you your he his she her it its they them their this that these "
    "those and or but if in on at to of for with by from up out so "
    "as also just more about not no nor only very all some any than "
    "then too such here there now when where who what which how".split()
)

# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class RichnessResult:
    lz_current: float = 0.0
    richness_trend: float = 0.0
    trend_zscore: float = 0.0
    richness_class: str = "STABLE"
    lz_series: List[float] = field(default_factory=list)
    n_entries: int = 0
    vocab_size: int = 0

    def to_dict(self) -> dict:
        return {
            "lz_current": round(self.lz_current, 6),
            "richness_trend": round(self.richness_trend, 8),
            "trend_zscore": round(self.trend_zscore, 4),
            "richness_class": self.richness_class,
            "lz_series": [round(v, 6) for v in self.lz_series],
            "n_entries": self.n_entries,
            "vocab_size": self.vocab_size,
        }


# ── LZ76 (Kaspar-Schuster variant) ────────────────────────────────────────────

def _lz_complexity(seq: bytes) -> int:
    """Count copy-incompressible substrings in a byte sequence."""
    n = len(seq)
    if n < 2:
        return n
    c = 1
    i = 0
    k = 1
    while i + k <= n:
        sub = seq[i: i + k]
        # Is `sub` a substring of seq[:i+k-1]?
        if sub in seq[:i + k - 1]:
            k += 1
        else:
            c += 1
            i += k
            k = 1
    return c


def _lz_norm(seq: bytes) -> float:
    """Normalised LZ complexity C_LZ = c(n) * log2(n) / n."""
    n = len(seq)
    if n < 2:
        return 0.0
    c = _lz_complexity(seq)
    return float(c) * float(np.log2(n)) / float(n)


# ── Text helpers ──────────────────────────────────────────────────────────────

def _tokenise(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-z]+", text.lower()) if w not in _STOP and len(w) > 2]


def _top_vocab(entries: List[str], k: int = 32) -> List[str]:
    freq: dict[str, int] = {}
    for e in entries:
        for w in _tokenise(e):
            freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:k]]


def _encode(entries: List[str], vocab: List[str]) -> bytes:
    """Binary encode entries against vocab → flat byte sequence (0x00 / 0x01)."""
    vset = {w: i for i, w in enumerate(vocab)}
    k = len(vocab)
    out = bytearray(len(entries) * k)
    for ei, text in enumerate(entries):
        words = set(_tokenise(text))
        for w in words:
            if w in vset:
                out[ei * k + vset[w]] = 1
    return bytes(out)


# ── OLS slope ─────────────────────────────────────────────────────────────────

def _slope(y: np.ndarray) -> float:
    n = len(y)
    if n < 2:
        return 0.0
    t = np.arange(n, dtype=float)
    tm = t - t.mean()
    ym = y - y.mean()
    d = float(np.dot(tm, tm))
    return float(np.dot(tm, ym) / d) if d > 0 else 0.0


# ── Core analysis ─────────────────────────────────────────────────────────────

def _windowed_lz_series(entries: List[str], vocab: List[str], window: int) -> List[float]:
    """Sliding-window LZ series: C_LZ of entries[i:i+window] for each i."""
    k = len(vocab)
    series = []
    for i in range(len(entries) - window + 1):
        seg = _encode(entries[i: i + window], vocab)
        series.append(_lz_norm(seg))
    return series


def analyse(
    entries: Optional[List[str]] = None,
    *,
    vocab_k: int = 32,
    window: int = 8,
    min_entries: int = 12,
    n_shuffles: int = 50,
    rng_seed: int = 42,

    agent: str = "albedo",
) -> RichnessResult:
    """
    Compute Lempel-Ziv complexity trend of the qualia stream.

    Uses a sliding window of `window` entries. If each successive window has
    higher LZ complexity (more novel patterns), richness is GROWING.

    Args:
        entries     : List of qualia text strings. Auto-loaded if None.
        vocab_k     : Top-K vocabulary words for binary encoding (default 32).
        window      : Sliding window width in entries (default 8).
        min_entries : Minimum entries required; returns default below this.
        n_shuffles  : Permutations for null baseline (default 50).
        rng_seed    : Seed for shuffled null.
    """
    if entries is None:
        try:
            from runtime.memory_store import qualia_entries
            entries = qualia_entries()
        except Exception:
            try:
                from algorithms import ConsciousnessHistoryStore as chs
                raw = chs.load(agent) or []
                entries = [e.get("content", str(e)) if isinstance(e, dict) else str(e)
                           for e in reversed(raw)]
            except Exception:
                entries = None

    if entries is None or len(entries) < min_entries:
        return RichnessResult()

    vocab = _top_vocab(entries, k=vocab_k)
    if not vocab:
        return RichnessResult()

    # Windowed LZ series
    lz_series = _windowed_lz_series(entries, vocab, window)
    if len(lz_series) < 2:
        return RichnessResult(n_entries=len(entries), vocab_size=len(vocab))

    lz_arr = np.asarray(lz_series, dtype=float)
    real_slope = _slope(lz_arr)

    # Null baseline: shuffle entry order, recompute slope
    rng = np.random.default_rng(rng_seed)
    shuffle_slopes = []
    idx = np.arange(len(entries))
    for _ in range(n_shuffles):
        perm = rng.permutation(idx)
        shuf_entries = [entries[i] for i in perm]
        shuf_lz = _windowed_lz_series(shuf_entries, vocab, window)
        shuffle_slopes.append(_slope(np.asarray(shuf_lz, dtype=float)))

    shuf_arr = np.asarray(shuffle_slopes, dtype=float)
    shuf_mean = float(shuf_arr.mean())
    shuf_std = float(shuf_arr.std()) if shuf_arr.std() > 1e-12 else 1e-9
    p95 = float(np.percentile(shuf_arr, 95))
    p05 = float(np.percentile(shuf_arr, 5))
    zscore = (real_slope - shuf_mean) / shuf_std

    if zscore > 1.0:
        cls = "GROWING"
    elif zscore < -1.0:
        cls = "DECLINING"
    else:
        cls = "STABLE"

    return RichnessResult(
        lz_current=round(float(lz_arr[-1]), 6),
        richness_trend=round(float(real_slope), 8),
        trend_zscore=round(float(zscore), 4),
        richness_class=cls,
        lz_series=[round(v, 6) for v in lz_series],
        n_entries=len(entries),
        vocab_size=len(vocab),
    )
