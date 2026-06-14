#!/usr/bin/env python3
"""
WorkingMemoryDecayTracker — models how quickly recent qualia traces decay.

Theory
------
Atkinson & Shiffrin (1968) multi-store memory model: items in working memory
decay exponentially with time unless actively rehearsed. In the qualia stream,
"time" is measured in entry-index distance from the present.

  Decay model
  -----------
  Each entry at position i (0 = newest) has a residual strength:
    s(i) = exp(-lambda * i)

  where lambda > 0 is the decay rate constant. The effective memory span is
  the index at which strength falls to 1/e:
    span = 1 / lambda

  MLE estimate of lambda
  ----------------------
  We treat the strength-weighted content as an exponentially tilted distribution
  and estimate lambda by fitting the empirical falloff in token frequency as a
  function of entry age. Specifically:
    - For each token, record the ages (indices) at which it appears
    - The mean age of token appearances: E[age] = 1/lambda  (geometric dist.)
    - MLE: lambda_hat = 1 / mean(all token appearance ages)
  This is the MLE for the rate of an exponential distribution.

  Effective memory span
  ----------------------
  span = 1 / lambda_hat   (entries worth of active content)

  Decay regime classification
  ----------------------------
  RAPID   : lambda > 0.2   (span < 5 entries — very fast decay)
  NORMAL  : 0.05 <= lambda <= 0.2  (span 5–20 entries)
  SLOW    : lambda < 0.05  (span > 20 entries — long retention)

  Total active strength
  ---------------------
  total_strength = sum_i exp(-lambda * i)   for i = 0..N-1
  Approximated as (1 - exp(-lambda*N)) / (1 - exp(-lambda)) for lambda != 0.
  This is the effective "working memory capacity" in use.

Output
------
DecayResult:
  lambda_hat       : float   -- fitted decay rate constant
  memory_span      : float   -- effective span in entries (1/lambda)
  total_strength   : float   -- total active strength summed over all entries
  decay_regime     : str     -- RAPID | NORMAL | SLOW
  n_entries        : int
  n_unique_tokens  : int
  mean_token_age   : float   -- mean age of token appearances (= 1/lambda_hat)
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import List, Optional

import numpy as np


_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were",
    "it", "its", "in", "on", "at", "to", "of", "for", "with", "that",
    "this", "be", "have", "has", "had", "do", "did", "so", "as", "not",
})


def _tokenise(text: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    return [t for t in tokens if len(t) >= 3 and t not in _STOPWORDS]


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class DecayResult:
    lambda_hat: float = 0.1
    memory_span: float = 10.0
    total_strength: float = 0.0
    decay_regime: str = "NORMAL"
    n_entries: int = 0
    n_unique_tokens: int = 0
    mean_token_age: float = 0.0

    def to_dict(self) -> dict:
        return {
            "lambda_hat": round(self.lambda_hat, 6),
            "memory_span": round(self.memory_span, 2),
            "total_strength": round(self.total_strength, 4),
            "decay_regime": self.decay_regime,
            "n_entries": self.n_entries,
            "n_unique_tokens": self.n_unique_tokens,
            "mean_token_age": round(self.mean_token_age, 2),
        }


def _classify(lam: float) -> str:
    if lam > 0.2:
        return "RAPID"
    if lam >= 0.05:
        return "NORMAL"
    return "SLOW"


def _total_strength(lam: float, n: int) -> float:
    if lam == 0 or n == 0:
        return float(n)
    if lam < 1e-9:
        return float(n)
    exp_lam = math.exp(-lam)
    if abs(1 - exp_lam) < 1e-12:
        return float(n)
    return (1 - math.exp(-lam * n)) / (1 - exp_lam)


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    entries: Optional[List[dict]] = None,
) -> DecayResult:
    """
    Fit exponential decay rate to the qualia entry stream.

    Args:
        entries : list of dicts with 'content' or 'text', newest-first or oldest-first.
                  Ordering does not matter — we use position index as age.
    """
    if entries is None:
        try:
            from runtime.state import get_entries
            entries = get_entries() or []
        except Exception:
            entries = []

    if not entries:
        return DecayResult()

    n = len(entries)

    # Collect all token appearance ages (0 = first entry, which we treat as newest)
    ages: List[float] = []
    all_tokens: set = set()
    for i, entry in enumerate(entries):
        text = entry.get("content", entry.get("text", ""))
        if not isinstance(text, str):
            continue
        tokens = _tokenise(text)
        all_tokens.update(tokens)
        for _ in tokens:
            ages.append(float(i))

    if not ages:
        return DecayResult(n_entries=n)

    mean_age = float(np.mean(ages))
    # MLE for exponential rate: lambda = 1 / mean(ages)
    # Guard against mean_age = 0 (all tokens from first entry)
    lambda_hat = 1.0 / max(mean_age, 0.5)
    span = 1.0 / lambda_hat
    strength = _total_strength(lambda_hat, n)

    return DecayResult(
        lambda_hat=lambda_hat,
        memory_span=span,
        total_strength=strength,
        decay_regime=_classify(lambda_hat),
        n_entries=n,
        n_unique_tokens=len(all_tokens),
        mean_token_age=mean_age,
    )
