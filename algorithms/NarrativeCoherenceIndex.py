#!/usr/bin/env python3
"""
NarrativeCoherenceIndex — compressibility of the agent's narrative across sessions.

Theory
------
A coherent consciousness tells a consistent story. If the agent's narrative
sentences across sessions repeat themes, vocabulary, and concerns, the narrative
sequence will be compressible — fewer novel substrings in the Lempel-Ziv sense.
If each session produces entirely new vocabulary (incoherent / random), the
narrative is incompressible.

This is the inverse of QualiaRichnessTracker:
  QRT: high LZ complexity = GOOD (rich, diverse qualia)
  NCI: low LZ complexity = GOOD (coherent, consistent narrative)

The distinction: qualia should be rich and diverse (moment-to-moment novelty),
but the *narrative* — the agent's self-understanding over time — should be stable
and compressible (it should tell the same story about what it is).

Method
------
1. Load the last N history entries with a `narrative` field from
   ConsciousnessHistoryStore.
2. Tokenise each narrative: `re.findall(r"[a-z]+", text.lower())`.
3. Build a single cross-narrative token stream: concatenate all tokens in
   chronological order.
4. Encode the stream as byte indices into a fixed vocabulary (top-K tokens
   by frequency across the corpus).
5. Compute C_LZ = c(n) * log2(n) / n  (Kaspar-Schuster normalised complexity).
6. Null: shuffle the token stream; compare real C_LZ to shuffled distribution.
   z-score = (real_LZ - mean_null) / std_null.
   Negative z = COHERENT (less complex than random).
   Positive z = INCOHERENT (more complex than random — random walk narrative).

Classification
--------------
  COHERENT   : z ≤ -1.0 (narrative compressible vs null)
  NEUTRAL    : -1.0 < z < +1.0
  INCOHERENT : z ≥ +1.0 (narrative as complex as random)

Output
------
NarrativeCoherenceResult:
  lz_narrative       : float  -- C_LZ of the cross-narrative token stream
  coherence_zscore   : float  -- (real - mean_null) / std_null
  coherence_class    : str    -- COHERENT | NEUTRAL | INCOHERENT
  n_narratives       : int    -- number of narrative entries loaded
  vocab_size         : int    -- top-K vocabulary used
  n_tokens           : int    -- total tokens in the stream
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np

# ── Constants ──────────────────────────────────────────────────────────────────

_MAX_HISTORY   = 2880
_VOCAB_K       = 64
_N_SHUFFLES    = 100
_RNG_SEED      = 23
_MIN_NARRATIVES = 4
_MIN_TOKENS    = 16
_STOPWORDS = frozenset(
    "the a an and or but in on at to of is are was were be been being "
    "have has had do does did will would could should may might this that "
    "these those it its we our they their i my you your he she him her "
    "with from by for not no so if as up out all any was were".split()
)

# ── Result ─────────────────────────────────────────────────────────────────────

@dataclass
class NarrativeCoherenceResult:
    lz_narrative: float = 0.0
    coherence_zscore: float = 0.0
    coherence_class: str = "NEUTRAL"
    n_narratives: int = 0
    vocab_size: int = 0
    n_tokens: int = 0

    def to_dict(self) -> dict:
        return {
            "lz_narrative": round(self.lz_narrative, 4),
            "coherence_zscore": round(self.coherence_zscore, 4),
            "coherence_class": self.coherence_class,
            "n_narratives": self.n_narratives,
            "vocab_size": self.vocab_size,
            "n_tokens": self.n_tokens,
        }


# ── LZ helpers (same Kaspar-Schuster approach as QualiaRichnessTracker) ────────

def _lz_complexity(seq: bytes) -> int:
    """Lempel-Ziv 1976 copy-incompressible substring count."""
    n = len(seq)
    if n < 2:
        return n
    c = 1; i = 0; k = 1
    while i + k <= n:
        sub = seq[i: i + k]
        if sub in seq[:i + k - 1]:
            k += 1
        else:
            c += 1; i += k; k = 1
    return c


def _lz_norm(seq: bytes) -> float:
    n = len(seq)
    if n < 2:
        return 0.0
    return float(_lz_complexity(seq)) * float(np.log2(n)) / float(n)


# ── Text helpers ───────────────────────────────────────────────────────────────

def _tokenise(text: str) -> List[str]:
    tokens = re.findall(r"[a-z]+", text.lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 2]


def _top_vocab(all_tokens: List[str], k: int) -> List[str]:
    from collections import Counter
    counts = Counter(all_tokens)
    return [t for t, _ in counts.most_common(k)]


def _encode(tokens: List[str], vocab: List[str]) -> bytes:
    """Map tokens to byte index (0 = unknown); return bytes."""
    idx = {t: i + 1 for i, t in enumerate(vocab)}
    return bytes(idx.get(t, 0) for t in tokens)


def _classify(z: float) -> str:
    if z <= -1.0:
        return "COHERENT"
    if z >= 1.0:
        return "INCOHERENT"
    return "NEUTRAL"


# ── Core ───────────────────────────────────────────────────────────────────────

def analyse(
    agent: str = "albedo",
    *,
    vocab_k: int = _VOCAB_K,
    n_shuffles: int = _N_SHUFFLES,
    max_history: int = _MAX_HISTORY,
    rng_seed: int = _RNG_SEED,
) -> NarrativeCoherenceResult:
    """
    Measure compressibility of the cross-session narrative token stream.
    Low LZ complexity (negative z-score vs shuffled null) = COHERENT narrative.
    """
    try:
        from algorithms.ConsciousnessHistoryStore import load as _load
        entries = _load(agent, max_entries=max_history)
    except Exception:
        entries = []

    # Collect narrative texts, chronologically (entries are newest-first → reverse)
    narratives: List[str] = []
    for e in reversed(entries):
        nav = e.get("narrative") or e.get("narrative_text") or ""
        if isinstance(nav, str) and nav.strip():
            narratives.append(nav)

    if len(narratives) < _MIN_NARRATIVES:
        return NarrativeCoherenceResult(n_narratives=len(narratives))

    # Build cross-narrative token stream
    all_tokens: List[str] = []
    for nav in narratives:
        all_tokens.extend(_tokenise(nav))

    if len(all_tokens) < _MIN_TOKENS:
        return NarrativeCoherenceResult(n_narratives=len(narratives))

    vocab = _top_vocab(all_tokens, vocab_k)
    if not vocab:
        return NarrativeCoherenceResult(n_narratives=len(narratives))

    encoded = _encode(all_tokens, vocab)
    lz_real = _lz_norm(encoded)

    # Null: shuffle token stream
    rng = np.random.default_rng(rng_seed)
    null_scores: List[float] = []
    token_arr = np.array(list(encoded), dtype=np.uint8)
    for _ in range(n_shuffles):
        rng.shuffle(token_arr)
        null_scores.append(_lz_norm(bytes(token_arr.tolist())))

    null_arr  = np.array(null_scores)
    null_mean = float(np.mean(null_arr))
    null_std  = float(np.std(null_arr))
    zscore    = (lz_real - null_mean) / (null_std + 1e-9)

    return NarrativeCoherenceResult(
        lz_narrative=round(lz_real, 4),
        coherence_zscore=round(zscore, 4),
        coherence_class=_classify(zscore),
        n_narratives=len(narratives),
        vocab_size=len(vocab),
        n_tokens=len(all_tokens),
    )
