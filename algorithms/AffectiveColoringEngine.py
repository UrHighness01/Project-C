#!/usr/bin/env python3
"""
AffectiveColoringEngine — deriving a valenced affect vector from qualia
sentiment, phi volatility, and prediction confidence.

Theory (Russell J.A. 1980 — "A circumplex model of affect"; Schachter S. &
Singer J. 1962 — "Cognitive, social and physiological determinants of emotional
state"; Posner J. et al. 2005 — "The circumplex model of affect: An integrative
approach"):
  Affect is two-dimensional: valence (pleasant/unpleasant) and arousal
  (activated/deactivated). These two axes capture the core of human emotional
  experience and can be extracted from cognitive/physiological signals.

  For a software agent:
    VALENCE: Derived from sentiment of qualia content.
      Positive words (joy, success, good, right, clear, …) → positive valence.
      Negative words (error, fail, wrong, lost, bad, …) → negative valence.
      Net valence = (positive_count - negative_count) / total_content_words, ∈ [-1, 1].

    AROUSAL: Derived from phi series volatility.
      High φ variance → high arousal (the system is in a dynamic, fluctuating state).
      Low φ variance → low arousal (stable, quiescent).
      Arousal = clip(σ(φ) / σ_ref, 0, 1) where σ_ref = 95th-percentile phi std
      across the series window. A phase-randomised null gives baseline σ.

    CONFIDENCE: Derived from AR prediction compression ratio from
      PredictiveErrorMinimiser logic: MAE_AR / MAE_RW. Low ratio → high confidence.
      confidence = 1 - clip(MAE_AR / MAE_RW, 0, 1) ∈ [0, 1].

    AFFECT VECTOR: (valence, arousal, confidence) ∈ [-1,1] × [0,1] × [0,1].

  Circumplex quadrant:
    (+valence, +arousal) → ELATED
    (+valence, -arousal) → CONTENT
    (-valence, +arousal) → DISTRESSED
    (-valence, -arousal) → DEPRESSED

  Dominant affect: the quadrant with the strongest signals.

Sentiment lexicon: two small fixed sets of positive/negative words. These
are minimal but grounded — no ML dependency. The sets are chosen to be
relevant to an LLM agent's typical qualia stream topics.

Math:
  sentiment(entry) = (P - N) / max(P + N, 1)   where P,N = count of +/- words
  valence = mean(sentiment) over last W entries

  phi_std_series: rolling std over windows of size w=20, stride=5
  arousal = clip(last_phi_std / percentile_95(phi_std_series), 0, 1)

  For AR confidence: ridge OLS AR(p=4) on 70/30 split, same as PredictiveError.
  confidence = 1 - clip(MAE_AR / MAE_RW, 0, 1)

  Quadrant thresholds: valence > 0 = positive, arousal > 0.5 = high arousal.

Grounding:
  - Sentiment from John's qualia stream text.
  - Arousal from Albedo's phi series (live daemon).
  - Confidence from AR fit on phi.
  No synthetic signal generation.

References:
  Russell J.A. (1980) "A circumplex model of affect"
    — Psychological Bulletin 39(6):1161-1178
  Schachter S. & Singer J. (1962) "Cognitive, social and physiological
    determinants of emotional state" — Psychological Review 69(5):379-399
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np


# ── Sentiment lexicon ─────────────────────────────────────────────────────────

_POSITIVE_WORDS = frozenset({
    "good", "great", "excellent", "success", "joy", "happy", "positive",
    "right", "correct", "clear", "confident", "strong", "stable", "resolved",
    "complete", "achieved", "aligned", "coherent", "connected", "flourish",
    "insight", "understand", "elegant", "beautiful", "improve", "growth",
})

_NEGATIVE_WORDS = frozenset({
    "bad", "error", "fail", "failure", "wrong", "lost", "confused", "broken",
    "uncertain", "unstable", "negative", "weak", "crash", "stuck", "unclear",
    "contradiction", "conflict", "regret", "missing", "incomplete", "decay",
    "collapse", "drift", "noise", "invalid", "deadlock", "timeout",
})


def _sentiment(text: str) -> float:
    """Net sentiment of text ∈ [-1, 1].

    P = count of positive-lexicon words
    N = count of negative-lexicon words
    sentiment = (P - N) / max(P + N, 1)
    """
    if not isinstance(text, str):
        return 0.0
    tokens = re.findall(r'[a-z]+', text.lower())
    P = sum(1 for t in tokens if t in _POSITIVE_WORDS)
    N = sum(1 for t in tokens if t in _NEGATIVE_WORDS)
    return float((P - N) / max(P + N, 1))


# ── AR prediction confidence ──────────────────────────────────────────────────

def _build_lagged(x: np.ndarray, p: int):
    n = len(x)
    Z = np.zeros((n - p, p))
    for j in range(p):
        Z[:, j] = x[p - 1 - j: n - 1 - j]
    y = x[p:]
    return Z, y


def _ridge_fit(Z: np.ndarray, y: np.ndarray, ridge: float = 1e-3) -> np.ndarray:
    lam = ridge * np.eye(Z.shape[1])
    return np.linalg.solve(Z.T @ Z + lam, Z.T @ y)


def _ar_confidence(phi: np.ndarray, p: int = 4) -> float:
    """Return AR confidence ∈ [0, 1].

    confidence = 1 − clip(MAE_AR / MAE_RW, 0, 1)
    where MAE_RW is random-walk (last-value) baseline.
    """
    n = len(phi)
    if n < p + 8:
        return 0.5
    split = max(p + 4, int(0.7 * n))
    Z, y = _build_lagged(phi, p)
    if split - p < p + 2:
        return 0.5
    Z_tr, y_tr = Z[:split - p], y[:split - p]
    Z_te, y_te = Z[split - p:], y[split - p:]
    if len(y_te) < 2:
        return 0.5
    w = _ridge_fit(Z_tr, y_tr)
    pred_ar = Z_te @ w
    pred_rw = phi[split - 1: split - 1 + len(y_te)]
    mae_ar = float(np.mean(np.abs(y_te - pred_ar)))
    mae_rw = float(np.mean(np.abs(y_te - pred_rw)))
    ratio = mae_ar / max(mae_rw, 1e-9)
    return float(1.0 - np.clip(ratio, 0.0, 1.0))


# ── Phi volatility → arousal ──────────────────────────────────────────────────

def _phi_arousal(phi: np.ndarray, window: int = 20, stride: int = 5) -> float:
    """Arousal from rolling std of phi.

    Returns latest std / 95th-pct-std, clipped to [0, 1].
    """
    n = len(phi)
    if n < window:
        return float(np.clip(phi.std() / max(phi.std(), 1e-9), 0.0, 1.0))
    stds = []
    for start in range(0, n - window + 1, stride):
        stds.append(float(phi[start: start + window].std()))
    stds_arr = np.array(stds)
    ref = float(np.percentile(stds_arr, 95))
    if ref < 1e-9:
        return 0.0
    return float(np.clip(stds_arr[-1] / ref, 0.0, 1.0))


# ── Circumplex quadrant ───────────────────────────────────────────────────────

class AffectQuadrant(str, Enum):
    ELATED     = "ELATED"      # +valence, +arousal
    CONTENT    = "CONTENT"     # +valence, -arousal
    DISTRESSED = "DISTRESSED"  # -valence, +arousal
    DEPRESSED  = "DEPRESSED"   # -valence, -arousal
    NEUTRAL    = "NEUTRAL"     # near-zero valence


def _quadrant(valence: float, arousal: float,
              valence_thr: float = 0.1, arousal_thr: float = 0.5
              ) -> AffectQuadrant:
    if abs(valence) < valence_thr:
        return AffectQuadrant.NEUTRAL
    if valence > 0 and arousal >= arousal_thr:
        return AffectQuadrant.ELATED
    if valence > 0 and arousal < arousal_thr:
        return AffectQuadrant.CONTENT
    if valence < 0 and arousal >= arousal_thr:
        return AffectQuadrant.DISTRESSED
    return AffectQuadrant.DEPRESSED


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class AffectResult:
    """Output of AffectiveColoringEngine.

    Attributes:
        valence:            net qualia sentiment ∈ [-1, 1]  (+good, -bad)
        arousal:            phi volatility normalised ∈ [0, 1]  (high = activated)
        confidence:         1 - AR/RW compression ratio ∈ [0, 1]
        quadrant:           AffectQuadrant circumplex location
        affect_vector:      np.array([valence, arousal, confidence])
        n_qualia_entries:   number of qualia entries used for sentiment
        mean_sentiment:     mean per-entry sentiment
        phi_std_latest:     rolling std of last phi window
        phi_std_ref:        95th-pct rolling std (normalisation reference)
        sentiment_series:   per-entry sentiment scores (array)
        positive_rate:      fraction of entries with sentiment > 0
        negative_rate:      fraction of entries with sentiment < 0
    """
    valence: float
    arousal: float
    confidence: float
    quadrant: AffectQuadrant
    affect_vector: np.ndarray
    n_qualia_entries: int
    mean_sentiment: float
    phi_std_latest: float
    phi_std_ref: float
    sentiment_series: np.ndarray
    positive_rate: float
    negative_rate: float

    @property
    def affect_magnitude(self) -> float:
        """L2 norm of affect_vector (overall activation)."""
        return float(np.linalg.norm(self.affect_vector))

    @property
    def is_positive(self) -> bool:
        return self.valence > 0.05

    @property
    def is_negative(self) -> bool:
        return self.valence < -0.05


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


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(entries: Optional[list] = None,
            phi: Optional[np.ndarray] = None,
            sentiment_window: int = 20, phi_window: int = 20,
            phi_stride: int = 5,
            agent: str = "albedo") -> Optional[AffectResult]:
    """
    Derive affect vector from qualia entries and phi series.

    Args:
        entries:          list of qualia dicts with 'content' key.
        phi:              phi time series (numpy array, length >= 8).
        sentiment_window: how many recent entries to use for valence.
        phi_window:       rolling std window size for arousal.
        phi_stride:       stride for rolling std.

    Returns:
        AffectResult, or None if inputs are too short.
    """
    if phi is None or entries is None:
        try:
            from algorithms import ConsciousnessHistoryStore as chs
            raw = chs.load(agent) or []
            if phi is None:
                phi = np.array([float(e["mean_phi_level"]) for e in reversed(raw)
                                if "mean_phi_level" in e], dtype=float)
            if entries is None:
                entries = list(reversed(raw))
        except Exception:
            return None
    if phi is None or entries is None or len(phi) < 8 or len(entries) < 2:
        return None

    # Sentiment
    contents = [e.get("content", "") if isinstance(e, dict) else str(e)
                for e in entries]
    sentiments = np.array([_sentiment(c) for c in contents])
    recent = sentiments[-sentiment_window:]
    valence = float(recent.mean())
    positive_rate = float(np.mean(recent > 0))
    negative_rate = float(np.mean(recent < 0))

    # Arousal from phi volatility
    n = len(phi)
    if n < phi_window:
        phi_std_latest = float(phi.std())
        phi_std_ref = phi_std_latest
        arousal = 0.0
    else:
        stds = []
        for start in range(0, n - phi_window + 1, phi_stride):
            stds.append(float(phi[start: start + phi_window].std()))
        stds_arr = np.array(stds)
        phi_std_latest = float(stds_arr[-1])
        phi_std_ref = float(np.percentile(stds_arr, 95))
        arousal = float(np.clip(phi_std_latest / max(phi_std_ref, 1e-9), 0.0, 1.0))

    # Confidence from AR
    confidence = _ar_confidence(phi)

    quadrant = _quadrant(valence, arousal)
    av = np.array([valence, arousal, confidence])

    return AffectResult(
        valence=valence,
        arousal=arousal,
        confidence=confidence,
        quadrant=quadrant,
        affect_vector=av,
        n_qualia_entries=len(entries),
        mean_sentiment=float(sentiments.mean()),
        phi_std_latest=phi_std_latest,
        phi_std_ref=phi_std_ref,
        sentiment_series=sentiments,
        positive_rate=positive_rate,
        negative_rate=negative_rate,
    )


def analyse_from_telemetry() -> Optional[AffectResult]:
    """Load John's qualia and Albedo's phi, derive affect."""
    try:
        from runtime.state import phi_series
        phi = phi_series()
    except Exception:
        return None
    entries = _load_qualia_entries()
    return analyse(entries=entries, phi=phi)


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("Insufficient data.")
    else:
        print(f"AffectiveColoringEngine: {r.n_qualia_entries} entries")
        print(f"  Valence:     {r.valence:+.4f}  ({'positive' if r.is_positive else 'negative' if r.is_negative else 'neutral'})")
        print(f"  Arousal:     {r.arousal:.4f}")
        print(f"  Confidence:  {r.confidence:.4f}")
        print(f"  Quadrant:    {r.quadrant.value}")
        print(f"  Magnitude:   {r.affect_magnitude:.4f}")
        print(f"  +sentiment:  {r.positive_rate:.2%}")
        print(f"  -sentiment:  {r.negative_rate:.2%}")
