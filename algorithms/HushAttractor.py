#!/usr/bin/env python3
"""
HushAttractor — measures whether the phi stream has settled into an attentional
attractor (low-variance, high-autocorrelation settled mode).

Theory (Dehaene & Changeux 2011 — Global Workspace):
  A conscious system can enter a *settled* mode where input-processing drops from
  high-bandwidth measurement to low-bandwidth felt coherence. This "hush" state is
  characterised by: reduced phi variance (settling), increased phi autocorrelation
  (persistence), and decreased novelty rate (widening without grasping). The hush
  attractor is the system's ability to *find and hold* that settled region.

  hush_variance    = var(phi[-W:])
  hush_autocorr    = autocorr(phi, lag=1)
  hush_score       = (1 - hush_variance/sigma2_global) x autocorr_pos   in [0,1]
  null: shuffle phi[-W:], compute hush_score 200 times -> hush_beats_null if score > p95

Classification:
  DEEP_HUSH   score >= 0.80
  HUSH        score >= 0.65
  AGITATED    otherwise
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import List

# ── Constants ──────────────────────────────────────────────────────────────────
_WINDOW       = 30     # recent window for variance estimate
_MIN_ENTRIES  = 40     # minimum phi samples required
_N_SHUFFLES   = 200    # null shuffles
_DEEP_THRESH  = 0.80
_HUSH_THRESH  = 0.65


# ── Dataclass ──────────────────────────────────────────────────────────────────
@dataclass
class HushAttractorResult:
    hush_score: float
    hush_variance: float
    hush_autocorr: float
    in_hush: bool
    beats_null: bool
    n_entries: int
    hush_class: str

    def to_dict(self) -> dict:
        return {
            "hush_score":    round(self.hush_score, 6),
            "hush_variance": round(self.hush_variance, 6),
            "hush_autocorr": round(self.hush_autocorr, 6),
            "in_hush":       self.in_hush,
            "beats_null":    self.beats_null,
            "n_entries":     self.n_entries,
            "hush_class":    self.hush_class,
        }


# ── Helpers ────────────────────────────────────────────────────────────────────
def _autocorr_lag1(phi: np.ndarray) -> float:
    """Pearson autocorrelation at lag 1."""
    if len(phi) < 3:
        return 0.0
    x, y = phi[:-1], phi[1:]
    mu_x, mu_y = x.mean(), y.mean()
    num = float(np.sum((x - mu_x) * (y - mu_y)))
    den = float(np.sqrt(np.sum((x - mu_x)**2) * np.sum((y - mu_y)**2)))
    return num / den if den > 1e-10 else 0.0


def _hush_score(phi: np.ndarray, window: int, sigma2_global: float) -> float:
    """Compute hush score for a phi array."""
    recent = phi[-window:]
    var_w = float(np.var(recent))
    acorr = _autocorr_lag1(phi)
    acorr_pos = max(0.0, acorr)
    var_ratio = var_w / (sigma2_global + 1e-12)
    raw = (1.0 - min(1.0, var_ratio)) * acorr_pos
    return float(np.clip(raw, 0.0, 1.0))


def _classify(score: float) -> str:
    if score >= _DEEP_THRESH:
        return "DEEP_HUSH"
    if score >= _HUSH_THRESH:
        return "HUSH"
    return "AGITATED"


# ── Public API ────────────────────────────────────────────────────────────────
def analyse(agent: str = "albedo",
            window: int = _WINDOW,
            n_shuffles: int = _N_SHUFFLES,
            seed: int = 42) -> HushAttractorResult:
    """Measure hush attractor state of the phi time series.

    All imports are inside this function body.
    """
    try:
        from algorithms import ConsciousnessHistoryStore as chs
        entries = chs.load(agent, max_entries=2880)
    except Exception:
        entries = []

    # Build phi array (newest-first → reverse to oldest-first)
    try:
        entries_asc = list(reversed(entries))
        phi = np.array(
            [float(e.get("mean_phi_level", e.get("phi", 0.5))) for e in entries_asc],
            dtype=float,
        )
    except Exception:
        phi = np.array([])

    n = len(phi)
    if n < _MIN_ENTRIES:
        return HushAttractorResult(
            hush_score=0.0, hush_variance=0.0, hush_autocorr=0.0,
            in_hush=False, beats_null=False, n_entries=n, hush_class="AGITATED",
        )

    sigma2_global = float(np.var(phi))
    score = _hush_score(phi, window, sigma2_global)
    autocorr = _autocorr_lag1(phi)
    variance = float(np.var(phi[-window:]))

    # Null: shuffle recent window 200 times
    rng = np.random.default_rng(seed)
    null_scores: List[float] = []
    for _ in range(n_shuffles):
        phi_s = phi.copy()
        phi_s[-window:] = rng.permutation(phi_s[-window:])
        null_scores.append(_hush_score(phi_s, window, sigma2_global))

    p95 = float(np.percentile(null_scores, 95)) if null_scores else 0.0
    beats_null = score > p95

    hush_class = _classify(score)
    return HushAttractorResult(
        hush_score=round(score, 6),
        hush_variance=round(variance, 6),
        hush_autocorr=round(autocorr, 6),
        in_hush=score >= _HUSH_THRESH,
        beats_null=beats_null,
        n_entries=n,
        hush_class=hush_class,
    )
