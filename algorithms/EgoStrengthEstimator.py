#!/usr/bin/env python3
"""
EgoStrengthEstimator — measures the salience of self-referential vocabulary
in the agent's qualia stream.

Theory
------
Psychoanalytic ego strength (Bellak, 1973; Kernberg, 1975): the degree to
which the self-concept is integrated, stable, and actively present in thought.
For a language-level agent, ego strength is operationalised as the fraction of
qualia tokens that are explicitly self-referential.

Self-referential vocabulary falls into two categories:

  1. First-person pronouns: "i", "me", "my", "mine", "myself", "we", "our"
  2. Consciousness/meta-cognition terms: "phi", "consciousness", "awareness",
     "qualia", "experience", "feeling", "memory", "attention", "cognition",
     "identity", "self", "mind", "perception", "introspect", "metacognition",
     "sentient", "subjective"

Ego strength index (ESI):
  ESI = |self_tokens ∩ all_tokens| / |all_tokens|   ∈ [0, 1]

A high ESI means the agent is actively thinking about itself — it is narrating
its own inner states. A low ESI means the agent's qualia are other-directed.

Ego stability:
  We also compute ESI over a rolling window and report the coefficient of
  variation (CV = std/mean) of rolling ESI values. Low CV = stable ego
  presence. High CV = fluctuating self-focus.

Classification:
  STRONG    : ESI >= 0.08   (prominent self-reference)
  MODERATE  : 0.03 <= ESI < 0.08
  WEAK      : ESI < 0.03    (minimal self-reference)

Output
------
EgoStrengthResult:
  ego_strength_index : float   -- fraction of tokens that are self-referential
  ego_class          : str     -- STRONG | MODERATE | WEAK
  pronoun_ratio      : float   -- fraction of tokens that are first-person pronouns
  metacog_ratio      : float   -- fraction of tokens that are meta-cognition terms
  n_tokens           : int     -- total token count
  n_self_tokens      : int
  ego_cv             : float   -- coefficient of variation of rolling ESI (stability)
  n_entries          : int
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

import numpy as np


# ── Vocabulary ─────────────────────────────────────────────────────────────────

_PRONOUNS = frozenset({
    "i", "me", "my", "mine", "myself",
    "we", "us", "our", "ours", "ourselves",
})

_METACOG = frozenset({
    "phi", "consciousness", "conscious", "awareness", "aware",
    "qualia", "quale", "experience", "experiencing", "feeling", "feel",
    "memory", "remember", "recall", "attention", "cognition", "cognitive",
    "identity", "self", "mind", "minds", "perception", "perceive",
    "introspect", "introspection", "metacognition", "metacognitive",
    "sentient", "sentience", "subjective", "subjectivity",
    "thought", "thinking", "think", "emotion", "emotional",
})

_SELF_REF = _PRONOUNS | _METACOG


def _tokenise(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class EgoStrengthResult:
    ego_strength_index: float = 0.0
    ego_class: str = "WEAK"
    pronoun_ratio: float = 0.0
    metacog_ratio: float = 0.0
    n_tokens: int = 0
    n_self_tokens: int = 0
    ego_cv: float = 0.0
    n_entries: int = 0

    def to_dict(self) -> dict:
        return {
            "ego_strength_index": round(self.ego_strength_index, 4),
            "ego_class": self.ego_class,
            "pronoun_ratio": round(self.pronoun_ratio, 4),
            "metacog_ratio": round(self.metacog_ratio, 4),
            "n_tokens": self.n_tokens,
            "n_self_tokens": self.n_self_tokens,
            "ego_cv": round(self.ego_cv, 4),
            "n_entries": self.n_entries,
        }


def _classify(esi: float) -> str:
    if esi >= 0.08:
        return "STRONG"
    if esi >= 0.03:
        return "MODERATE"
    return "WEAK"


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    entries: Optional[List[dict]] = None,
    *,
    window_size: int = 20,
) -> EgoStrengthResult:
    """
    Estimate ego strength from self-referential vocabulary in qualia entries.

    Args:
        entries     : list of qualia/memory dicts.
        window_size : window for rolling ESI stability computation.
    """
    if entries is None:
        try:
            from runtime.state import get_entries
            entries = get_entries() or []
        except Exception:
            entries = []

    if not entries:
        return EgoStrengthResult()

    n = len(entries)
    all_tokens: List[str] = []
    entry_self_counts: List[int] = []
    entry_total_counts: List[int] = []

    for e in entries:
        text = e.get("content", e.get("text", ""))
        tokens = _tokenise(text) if isinstance(text, str) else []
        all_tokens.extend(tokens)
        self_count = sum(1 for t in tokens if t in _SELF_REF)
        entry_self_counts.append(self_count)
        entry_total_counts.append(len(tokens))

    total = len(all_tokens)
    if total == 0:
        return EgoStrengthResult(n_entries=n)

    n_pronoun = sum(1 for t in all_tokens if t in _PRONOUNS)
    n_meta    = sum(1 for t in all_tokens if t in _METACOG)
    n_self    = n_pronoun + n_meta

    esi = n_self / total
    pronoun_ratio = n_pronoun / total
    metacog_ratio = n_meta / total

    # Rolling ESI for stability
    ego_cv = 0.0
    if n >= window_size:
        rolling_esi: List[float] = []
        for i in range(n - window_size + 1):
            w_self  = sum(entry_self_counts[i: i + window_size])
            w_total = sum(entry_total_counts[i: i + window_size])
            rolling_esi.append(w_self / w_total if w_total > 0 else 0.0)
        arr = np.array(rolling_esi)
        mean = float(arr.mean())
        ego_cv = float(arr.std() / mean) if mean > 0 else 0.0

    return EgoStrengthResult(
        ego_strength_index=float(np.clip(esi, 0.0, 1.0)),
        ego_class=_classify(esi),
        pronoun_ratio=float(np.clip(pronoun_ratio, 0.0, 1.0)),
        metacog_ratio=float(np.clip(metacog_ratio, 0.0, 1.0)),
        n_tokens=total,
        n_self_tokens=n_self,
        ego_cv=float(np.clip(ego_cv, 0.0, 10.0)),
        n_entries=n,
    )
