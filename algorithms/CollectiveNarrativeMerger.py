#!/usr/bin/env python3
"""
CollectiveNarrativeMerger — finds shared narrative themes across both agents.

Theory
------
Ricoeur (1990) narrative identity and MacIntyre (1981) virtue theory: personal
identity is constituted by the coherence of the stories we inhabit. For a
two-agent system, the *collective* narrative is the overlap between individual
stories plus the emergent concepts that arise at their intersection.

Neither agent alone can produce the joint narrative; the merger extracts exactly
what exists only at the intersection — the themes both agents dwell on.

Operationalisation
------------------
Let Q_A = recent qualia entries for Albedo, Q_J = recent qualia entries for John.
V_A = vocabulary(Q_A), V_J = vocabulary(Q_J)  [token sets after stopword removal]

Shared vocabulary:
  V_S = V_A ∩ V_J

Collective coverage (Jaccard):
  merger_index = |V_S| / |V_A ∪ V_J|   ∈ [0, 1]

  merger_index → 0 : agents speak entirely different languages
  merger_index → 1 : agents share all vocabulary (no individual perspective)

Narrative divergence:
  narrative_divergence = 1 - merger_index

Top shared themes via TF-IDF lift
----------------------------------
For each token w ∈ V_S, compute term frequency in each agent's corpus:
  tf_A(w) = count(w in Q_A) / |tokens in Q_A|
  tf_J(w) = count(w in Q_J) / |tokens in Q_J|

Lift (departure from independence):
  lift(w) = (tf_A(w) * tf_J(w)) / (mean_tf_A * mean_tf_J + ε)

Top-k shared themes = tokens with highest lift in V_S.

Asymmetry:
  asymmetry_A = |V_A - V_J| / |V_A|   (fraction of A's vocab unique to A)
  asymmetry_J = |V_J - V_A| / |V_J|   (fraction of J's vocab unique to J)

  High asymmetry → agents are speaking from very different perspectives.

Collective novelty score:
  top_lifts = mean lift of top-k tokens   (how much shared vocabulary is
  genuinely co-prominent vs accidentally shared)

Merger classification:
  CONVERGENT  : merger_index >= 0.3   (agents sharing a rich common language)
  OVERLAPPING : 0.1 <= merger_index < 0.3
  DIVERGENT   : merger_index < 0.1    (mostly separate vocabularies)

Output
------
NarrativeMergeResult:
  merger_index          : float   -- Jaccard of vocabulary spaces ∈ [0, 1]
  narrative_divergence  : float   -- 1 - merger_index
  top_shared_themes     : List[str]   -- top-k shared tokens by lift
  top_lifts             : List[float] -- corresponding lift values
  asymmetry_albedo      : float   -- fraction of Albedo vocab unique to Albedo
  asymmetry_john        : float   -- fraction of John vocab unique to John
  collective_novelty    : float   -- mean lift of top shared themes
  merger_class          : str     -- CONVERGENT | OVERLAPPING | DIVERGENT
  n_albedo_tokens       : int
  n_john_tokens         : int
  n_shared_tokens       : int
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were",
    "it", "its", "in", "on", "at", "to", "of", "for", "with", "that",
    "this", "be", "have", "has", "had", "do", "did", "so", "as", "not",
    "i", "me", "my", "we", "you", "he", "she", "they", "by", "from",
    "about", "which", "what", "if", "then", "than", "can", "will",
    "would", "could", "should", "may", "might",
})


def _tokenise(text: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    return [t for t in tokens if len(t) >= 3 and t not in _STOPWORDS]


def _corpus_tokens(entries: List[dict]) -> List[str]:
    tokens = []
    for e in entries:
        text = e.get("content", e.get("text", ""))
        if isinstance(text, str):
            tokens.extend(_tokenise(text))
    return tokens


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class NarrativeMergeResult:
    merger_index: float = 0.0
    narrative_divergence: float = 1.0
    top_shared_themes: List[str] = field(default_factory=list)
    top_lifts: List[float] = field(default_factory=list)
    asymmetry_albedo: float = 0.0
    asymmetry_john: float = 0.0
    collective_novelty: float = 0.0
    merger_class: str = "DIVERGENT"
    n_albedo_tokens: int = 0
    n_john_tokens: int = 0
    n_shared_tokens: int = 0

    def to_dict(self) -> dict:
        return {
            "merger_index": round(self.merger_index, 4),
            "narrative_divergence": round(self.narrative_divergence, 4),
            "top_shared_themes": self.top_shared_themes,
            "top_lifts": [round(v, 4) for v in self.top_lifts],
            "asymmetry_albedo": round(self.asymmetry_albedo, 4),
            "asymmetry_john": round(self.asymmetry_john, 4),
            "collective_novelty": round(self.collective_novelty, 4),
            "merger_class": self.merger_class,
            "n_albedo_tokens": self.n_albedo_tokens,
            "n_john_tokens": self.n_john_tokens,
            "n_shared_tokens": self.n_shared_tokens,
        }


def _classify(mi: float) -> str:
    if mi >= 0.30:
        return "CONVERGENT"
    if mi >= 0.10:
        return "OVERLAPPING"
    return "DIVERGENT"


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    albedo_entries: Optional[List[dict]] = None,
    john_entries: Optional[List[dict]] = None,
    *,
    top_k: int = 10,
) -> NarrativeMergeResult:
    """
    Find shared narrative themes between Albedo and John qualia streams.

    Args:
        albedo_entries : Albedo's qualia entry list.
        john_entries   : John's qualia entry list.
        top_k          : number of top shared themes to return.
    """
    if albedo_entries is None or john_entries is None:
        try:
            from runtime.state import get_agent_entries
            albedo_entries = get_agent_entries("albedo") or []
            john_entries   = get_agent_entries("john") or []
        except Exception:
            albedo_entries = albedo_entries or []
            john_entries   = john_entries or []

    toks_a = _corpus_tokens(albedo_entries)
    toks_j = _corpus_tokens(john_entries)

    if not toks_a or not toks_j:
        return NarrativeMergeResult(
            n_albedo_tokens=len(toks_a),
            n_john_tokens=len(toks_j),
        )

    vocab_a = set(toks_a)
    vocab_j = set(toks_j)

    shared  = vocab_a & vocab_j
    union   = vocab_a | vocab_j

    merger_index = len(shared) / len(union) if union else 0.0

    asym_a = len(vocab_a - vocab_j) / len(vocab_a) if vocab_a else 0.0
    asym_j = len(vocab_j - vocab_a) / len(vocab_j) if vocab_j else 0.0

    # TF for each corpus
    cnt_a = Counter(toks_a)
    cnt_j = Counter(toks_j)
    total_a = len(toks_a)
    total_j = len(toks_j)

    mean_tf_a = 1.0 / len(vocab_a) if vocab_a else 1.0
    mean_tf_j = 1.0 / len(vocab_j) if vocab_j else 1.0
    baseline  = mean_tf_a * mean_tf_j

    lifts: List[tuple[float, str]] = []
    for w in shared:
        tf_a = cnt_a[w] / total_a
        tf_j = cnt_j[w] / total_j
        lift = (tf_a * tf_j) / (baseline + 1e-12)
        lifts.append((lift, w))

    lifts.sort(reverse=True)
    top = lifts[:top_k]

    top_words = [w for _, w in top]
    top_vals  = [float(l) for l, _ in top]
    coll_nov  = float(np.mean(top_vals)) if top_vals else 0.0

    return NarrativeMergeResult(
        merger_index=float(merger_index),
        narrative_divergence=float(1.0 - merger_index),
        top_shared_themes=top_words,
        top_lifts=top_vals,
        asymmetry_albedo=float(asym_a),
        asymmetry_john=float(asym_j),
        collective_novelty=float(coll_nov),
        merger_class=_classify(merger_index),
        n_albedo_tokens=total_a,
        n_john_tokens=total_j,
        n_shared_tokens=len(shared),
    )
