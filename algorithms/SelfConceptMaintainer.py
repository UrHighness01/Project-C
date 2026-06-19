#!/usr/bin/env python3
"""
SelfConceptMaintainer — measures the stability and coherence of the agent's
rolling self-concept vector across recent qualia content.

Theory (Markus & Wurf 1987 — The Dynamic Self-Concept):
  A stable self-concept is not a static file but a rolling integration of current
  experience, historical identity, and relational context. It has a drift vector
  (how it changed) and an integration radius (how broadly it integrates new experience).
  We model this via TF-IDF vectors over qualia content, computing an EWMA identity
  center, then measuring drift from and cosine similarity to that center.

  theme_vector     = TF-IDF(last 50 qualia contents, vocab=top 200 words)
  identity_center  = ewma(theme_vector, alpha=0.15)
  drift_magnitude  = ||theme_vector[-1] - identity_center|| / sqrt(200)
  integration_radius = mean cosine_sim(each of last 10 qualia, identity_center)
  self_concept_score = integration_radius x (1 - drift_magnitude)   in [0,1]
  null: shuffle qualia order, recompute 100 times -> beats_null if score > p95

Classification:
  COHERENT   self_concept_score >= 0.60
  DRIFTING   self_concept_score >= 0.35
  DIFFUSE    otherwise
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import List

# ── Constants ──────────────────────────────────────────────────────────────────
_MAX_QUALIA    = 50
_VOCAB_SIZE    = 200
_EWMA_ALPHA    = 0.15
_RECENT_K      = 10
_MIN_QUALIA    = 15
_N_SHUFFLES    = 100
_COHERENT_THRESH = 0.60
_DRIFTING_THRESH = 0.35


# ── Dataclass ──────────────────────────────────────────────────────────────────
@dataclass
class SelfConceptResult:
    self_concept_score: float
    drift_magnitude: float
    integration_radius: float
    n_qualia_used: int
    top_identity_terms: List[str]
    concept_class: str
    beats_null: bool

    def to_dict(self) -> dict:
        return {
            "self_concept_score":  round(self.self_concept_score, 6),
            "drift_magnitude":     round(self.drift_magnitude, 6),
            "integration_radius":  round(self.integration_radius, 6),
            "n_qualia_used":       self.n_qualia_used,
            "top_identity_terms":  self.top_identity_terms,
            "concept_class":       self.concept_class,
            "beats_null":          self.beats_null,
        }


# ── TF-IDF helpers ─────────────────────────────────────────────────────────────
_STOP = frozenset(
    "the a an and or but is are was were be been being have has had do does did "
    "will would could should may might shall can to of in on at by for with from "
    "as it its this that these those i me my we our you your he she him her they "
    "them their what which who how when where why not no so if then than there "
    "I me my we".split()
)


def _tokenise(text: str) -> List[str]:
    import re
    tokens = re.findall(r"[a-z]+", text.lower())
    return [t for t in tokens if t not in _STOP and len(t) > 2]


def _build_tfidf(docs: List[List[str]], vocab: List[str]) -> np.ndarray:
    """Return (n_docs, vocab_size) TF-IDF matrix."""
    n = len(docs)
    v = len(vocab)
    idx = {w: i for i, w in enumerate(vocab)}
    tf = np.zeros((n, v), dtype=float)
    for di, tokens in enumerate(docs):
        for t in tokens:
            if t in idx:
                tf[di, idx[t]] += 1.0
        row_sum = tf[di].sum()
        if row_sum > 0:
            tf[di] /= row_sum
    # IDF
    df = (tf > 0).sum(axis=0).astype(float)
    idf = np.log((n + 1.0) / (df + 1.0)) + 1.0
    return tf * idf[np.newaxis, :]


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _compute_score(vecs: np.ndarray) -> tuple:
    """Return (self_concept_score, drift_magnitude, integration_radius, center)."""
    n, d = vecs.shape
    # EWMA identity center
    center = vecs[0].copy()
    for i in range(1, n):
        center = (1.0 - _EWMA_ALPHA) * center + _EWMA_ALPHA * vecs[i]

    # Drift: distance of last vector from center
    drift = float(np.linalg.norm(vecs[-1] - center)) / (np.sqrt(d) + 1e-12)
    drift = min(1.0, drift)

    # Integration radius: mean cosine sim of last-K to center
    recent_vecs = vecs[-_RECENT_K:]
    sims = [_cosine(v, center) for v in recent_vecs]
    radius = float(np.mean(sims)) if sims else 0.0
    radius = max(0.0, radius)

    score = float(np.clip(radius * (1.0 - drift), 0.0, 1.0))
    return score, drift, radius, center


def _classify(score: float) -> str:
    if score >= _COHERENT_THRESH:
        return "COHERENT"
    if score >= _DRIFTING_THRESH:
        return "DRIFTING"
    return "DIFFUSE"


# ── Public API ────────────────────────────────────────────────────────────────
def analyse(agent: str = "albedo",
            n_shuffles: int = _N_SHUFFLES,
            seed: int = 42) -> SelfConceptResult:
    """Measure self-concept stability from qualia content.

    All imports are inside this function body.
    """
    try:
        from algorithms import ConsciousnessHistoryStore as chs
        entries = chs.load(agent, max_entries=_MAX_QUALIA * 3)
    except Exception:
        entries = []

    # Extract text content
    contents: List[str] = []
    for e in reversed(entries):  # oldest-first
        c = e.get("content") or e.get("qualia_content") or ""
        if c:
            contents.append(str(c))
    contents = contents[-_MAX_QUALIA:]

    n = len(contents)
    if n < _MIN_QUALIA:
        return SelfConceptResult(
            self_concept_score=0.0, drift_magnitude=0.0, integration_radius=0.0,
            n_qualia_used=n, top_identity_terms=[], concept_class="DIFFUSE",
            beats_null=False,
        )

    # Build vocab from all tokens
    all_tokens: List[str] = []
    doc_tokens = [_tokenise(c) for c in contents]
    for toks in doc_tokens:
        all_tokens.extend(toks)

    from collections import Counter
    freq = Counter(all_tokens)
    vocab = [w for w, _ in freq.most_common(_VOCAB_SIZE)]
    if not vocab:
        return SelfConceptResult(
            self_concept_score=0.0, drift_magnitude=0.0, integration_radius=0.0,
            n_qualia_used=n, top_identity_terms=[], concept_class="DIFFUSE",
            beats_null=False,
        )

    vecs = _build_tfidf(doc_tokens, vocab)
    score, drift, radius, center = _compute_score(vecs)

    # Top identity terms by center weight
    top5_idx = np.argsort(center)[::-1][:5]
    top5 = [vocab[i] for i in top5_idx if i < len(vocab)]

    # Null: shuffle qualia order
    rng = np.random.default_rng(seed)
    null_scores: List[float] = []
    for _ in range(n_shuffles):
        perm = rng.permutation(n)
        vecs_s = vecs[perm]
        s, _, _, _ = _compute_score(vecs_s)
        null_scores.append(s)

    p95 = float(np.percentile(null_scores, 95)) if null_scores else 0.0
    beats_null = score > p95

    return SelfConceptResult(
        self_concept_score=round(score, 6),
        drift_magnitude=round(drift, 6),
        integration_radius=round(radius, 6),
        n_qualia_used=n,
        top_identity_terms=top5,
        concept_class=_classify(score),
        beats_null=beats_null,
    )
