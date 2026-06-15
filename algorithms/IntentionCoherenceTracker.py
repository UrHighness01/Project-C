#!/usr/bin/env python3
"""
IntentionCoherenceTracker — detects when stated intentions diverge from qualia content.

Theory
------
An agent's stated goals (from goal-state.json) describe what it *intends* to do.
Its qualia stream describes what it is *actually* processing. Coherence means the
two are aligned: the agent is thinking about what it intends to do.

  Intention signal
  ----------------
  For each active goal, extract tokens from name + description + sub_goals.
  Union all goal tokens into an intention vocabulary I.

  Qualia signal
  -------------
  Tokenise the recent N qualia entries into a vocabulary Q (last N=50 by default).

  Coherence score
  ---------------
  Jaccard similarity between I and Q:
    J(I, Q) = |I ∩ Q| / |I ∪ Q|

  This is a symmetric measure. We supplement it with a directed overlap:
    coverage   = |I ∩ Q| / |I|   -- fraction of intentions present in qualia
    infiltration = |I ∩ Q| / |Q| -- fraction of qualia occupied by intentions

  A high coverage means the agent is thinking about its goals.
  A low coverage means the agent's mind is elsewhere.

  Coherence classification:
    ALIGNED    : J >= 0.15  (substantial shared vocabulary)
    PARTIAL    : 0.05 <= J < 0.15
    DIVERGENT  : J < 0.05   (intentions and qualia share almost no tokens)

  Divergence alert
  ----------------
  If coverage drops below 0.05 AND the agent has active goals, this is flagged
  as a coherence alert: the agent's processing is detached from its stated purpose.

Output
------
IntentionCoherenceResult:
  jaccard              : float   -- J(I, Q)
  coverage             : float   -- |I∩Q|/|I|
  infiltration         : float   -- |I∩Q|/|Q|
  coherence_class      : str     -- ALIGNED | PARTIAL | DIVERGENT
  is_alert             : bool    -- coverage < alert_threshold and n_goals > 0
  n_active_goals       : int
  n_intention_tokens   : int
  n_qualia_tokens      : int
  shared_tokens        : List[str]  -- up to 10 tokens in both
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were",
    "it", "its", "in", "on", "at", "to", "of", "for", "with", "that",
    "this", "be", "have", "has", "had", "do", "did", "so", "as", "not",
    "should", "will", "can", "may", "must", "need", "want", "make",
})


def _tokenise(text: str) -> frozenset:
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    return frozenset(t for t in tokens if len(t) >= 4 and t not in _STOPWORDS)


def _goal_tokens(goal: dict) -> frozenset:
    parts = [
        goal.get("name", ""),
        goal.get("description", ""),
        " ".join(goal.get("sub_goals", [])),
    ]
    return _tokenise(" ".join(parts))


def _entries_tokens(entries: List[dict], n: int) -> frozenset:
    recent = entries[-n:] if len(entries) > n else entries
    tokens: set = set()
    for e in recent:
        text = e.get("content", e.get("text", ""))
        if isinstance(text, str):
            tokens |= _tokenise(text)
    return frozenset(tokens)


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class IntentionCoherenceResult:
    jaccard: float = 0.0
    coverage: float = 0.0
    infiltration: float = 0.0
    coherence_class: str = "DIVERGENT"
    is_alert: bool = False
    n_active_goals: int = 0
    n_intention_tokens: int = 0
    n_qualia_tokens: int = 0
    shared_tokens: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "jaccard": round(self.jaccard, 4),
            "coverage": round(self.coverage, 4),
            "infiltration": round(self.infiltration, 4),
            "coherence_class": self.coherence_class,
            "is_alert": self.is_alert,
            "n_active_goals": self.n_active_goals,
            "n_intention_tokens": self.n_intention_tokens,
            "n_qualia_tokens": self.n_qualia_tokens,
            "shared_tokens": self.shared_tokens,
        }


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    goals: Optional[List[dict]] = None,
    entries: Optional[List[dict]] = None,
    *,
    recent_n: int = 50,
    alert_threshold: float = 0.05,
    agent: str = "albedo",
) -> IntentionCoherenceResult:
    """
    Measure alignment between active goals and recent qualia stream.

    Args:
        goals        : list of goal dicts (active=True, with name/description).
        entries      : list of qualia/memory entry dicts.
        recent_n     : how many recent entries to consider.
        alert_threshold : coverage below this = coherence alert.
    """
    if goals is None:
        try:
            from algorithms.GoalAlignmentMeasure import _load_goals
            goals = _load_goals(agent)
        except Exception:
            goals = []

    if entries is None:
        try:
            from algorithms import ConsciousnessHistoryStore as chs
            entries = chs.load(agent) or []
        except Exception:
            entries = []

    active_goals = [g for g in (goals or []) if g.get("active", True)]

    intention_tokens: frozenset = frozenset()
    for g in active_goals:
        intention_tokens |= _goal_tokens(g)

    qualia_tokens = _entries_tokens(entries or [], recent_n)

    intersection = intention_tokens & qualia_tokens
    union = intention_tokens | qualia_tokens

    jaccard = len(intersection) / len(union) if union else 0.0
    coverage = len(intersection) / len(intention_tokens) if intention_tokens else 0.0
    infiltration = len(intersection) / len(qualia_tokens) if qualia_tokens else 0.0

    if jaccard >= 0.15:
        cls = "ALIGNED"
    elif jaccard >= 0.05:
        cls = "PARTIAL"
    else:
        cls = "DIVERGENT"

    is_alert = coverage < alert_threshold and len(active_goals) > 0

    shared = sorted(intersection)[:10]

    return IntentionCoherenceResult(
        jaccard=jaccard,
        coverage=coverage,
        infiltration=infiltration,
        coherence_class=cls,
        is_alert=is_alert,
        n_active_goals=len(active_goals),
        n_intention_tokens=len(intention_tokens),
        n_qualia_tokens=len(qualia_tokens),
        shared_tokens=shared,
    )
