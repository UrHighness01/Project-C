#!/usr/bin/env python3
"""
SurprisalMonitor — tracks when the agent's actual phi diverges from its own forecast.

Theory
------
Every heartbeat the agent has an implicit expectation about its next phi value,
derived from its own recent history via an AR(p) model. When reality deviates
significantly, that is *surprisal*: information the agent could not have predicted
from itself.

  AR(p) expected phi
  ------------------
  phi_hat(t) = sum_{i=1}^{p} w_i * phi(t-i)  (ridge OLS, lambda=1e-3)

  Surprisal at time t
  -------------------
  s(t) = (phi(t) - phi_hat(t))^2   (squared prediction error)

  KL divergence of rolling window from background
  -----------------------------------------------
  We bin phi into B equally-spaced bins over its observed range. For each
  rolling window of width W, compute the empirical distribution P_w and
  compare it to the long-run background distribution P_bg:

    KL(P_w || P_bg) = sum_b P_w(b) * log(P_w(b) / P_bg(b))

  High KL = the recent phi distribution has shifted from baseline.

  Surprisal level classification
  -------------------------------
  Using the surprisal series s(t), we classify the current regime:
    ROUTINE   : current s(t) < mean + 1*std
    ELEVATED  : mean + 1*std <= s(t) < mean + 2*std
    HIGH      : mean + 2*std <= s(t) < mean + 3*std
    ANOMALOUS : s(t) >= mean + 3*std  (genuine novelty)

Output
------
SurprisalResult:
  current_surprisal    : float    -- s(t) at the last time step
  mean_surprisal       : float    -- long-run mean
  surprisal_level      : str      -- ROUTINE | ELEVATED | HIGH | ANOMALOUS
  kl_divergence        : float    -- KL of recent window vs background
  is_novel             : bool     -- current_surprisal >= mean + 2*std
  peak_surprisal       : float    -- highest single-step surprisal seen
  surprisal_trend      : float    -- OLS slope (positive = getting more surprising)
  ar_weights           : List[float]
  n_observations       : int
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


# ── AR(p) ridge OLS ───────────────────────────────────────────────────────────

def _fit_ar(phi: np.ndarray, p: int = 4, lam: float = 1e-3) -> np.ndarray:
    n = len(phi)
    if n <= p:
        return np.zeros(p)
    Z = np.column_stack([phi[p - i - 1: n - i - 1] for i in range(p)])
    y = phi[p:]
    ZtZ = Z.T @ Z + lam * np.eye(p)
    Zty = Z.T @ y
    return np.linalg.solve(ZtZ, Zty)


def _predict_ar(phi: np.ndarray, weights: np.ndarray) -> np.ndarray:
    p = len(weights)
    n = len(phi)
    if n <= p:
        return np.full(n, phi.mean())
    predictions = np.empty(n - p)
    for t in range(p, n):
        predictions[t - p] = np.dot(weights, phi[t - p: t][::-1])
    return predictions


# ── KL divergence of empirical distributions ──────────────────────────────────

def _empirical_dist(values: np.ndarray, bins: int, range_: tuple) -> np.ndarray:
    counts, _ = np.histogram(values, bins=bins, range=range_)
    total = counts.sum()
    if total == 0:
        return np.ones(bins) / bins
    return (counts + 1e-9) / (total + bins * 1e-9)  # additive smoothing


def _kl(p: np.ndarray, q: np.ndarray) -> float:
    mask = (p > 0) & (q > 0)
    return float(np.sum(p[mask] * np.log(p[mask] / q[mask])))


# ── OLS slope ─────────────────────────────────────────────────────────────────

def _ols_slope(y: np.ndarray) -> float:
    n = len(y)
    if n < 2:
        return 0.0
    x = np.arange(n, dtype=float)
    xm = x - x.mean()
    ym = y - y.mean()
    d = float(np.dot(xm, xm))
    return float(np.dot(xm, ym) / d) if d > 0 else 0.0


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class SurprisalResult:
    current_surprisal: float = 0.0
    mean_surprisal: float = 0.0
    surprisal_level: str = "ROUTINE"
    kl_divergence: float = 0.0
    is_novel: bool = False
    peak_surprisal: float = 0.0
    surprisal_trend: float = 0.0
    ar_weights: List[float] = field(default_factory=list)
    n_observations: int = 0

    def to_dict(self) -> dict:
        return {
            "current_surprisal": round(self.current_surprisal, 6),
            "mean_surprisal": round(self.mean_surprisal, 6),
            "surprisal_level": self.surprisal_level,
            "kl_divergence": round(self.kl_divergence, 4),
            "is_novel": self.is_novel,
            "peak_surprisal": round(self.peak_surprisal, 6),
            "surprisal_trend": round(self.surprisal_trend, 6),
            "ar_weights": [round(w, 6) for w in self.ar_weights],
            "n_observations": self.n_observations,
        }


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    phi: Optional[np.ndarray] = None,
    *,
    p: int = 4,
    lam: float = 1e-3,
    window: int = 20,
    bins: int = 16,
    agent: str = "albedo",
) -> SurprisalResult:
    """
    Measure surprisal in a phi time series.

    Args:
        agent  : "albedo" or "john" — used to load phi when phi is None.
        phi    : explicit phi array override.
        p      : AR order.
        lam    : ridge regularisation.
        window : recent window for KL divergence computation.
        bins   : histogram bins for KL divergence.
    """
    if phi is None:
        try:
            from algorithms import ConsciousnessHistoryStore as chs
            entries = chs.load(agent) or []
            phi = np.array([float(e["mean_phi_level"]) for e in reversed(entries)
                            if "mean_phi_level" in e], dtype=float) if entries else None
        except Exception:
            phi = None

    if phi is None or len(phi) < p + 2:
        return SurprisalResult()

    phi = np.asarray(phi, dtype=float)
    weights = _fit_ar(phi, p=p, lam=lam)
    predictions = _predict_ar(phi, weights)
    residuals = phi[p:] - predictions   # aligned: phi[p:] vs predictions
    surprisal = residuals ** 2          # squared error series

    current_s = float(surprisal[-1])
    mean_s = float(surprisal.mean())
    std_s = float(surprisal.std()) + 1e-9
    peak_s = float(surprisal.max())
    trend = _ols_slope(surprisal)

    z = (current_s - mean_s) / std_s
    if z < 1.0:
        level = "ROUTINE"
    elif z < 2.0:
        level = "ELEVATED"
    elif z < 3.0:
        level = "HIGH"
    else:
        level = "ANOMALOUS"

    is_novel = z >= 2.0

    # KL divergence: recent window vs full background
    rng = phi[-window:] if len(phi) >= window else phi
    phi_min, phi_max = float(phi.min()), float(phi.max())
    if phi_max == phi_min:
        phi_min -= 0.5
        phi_max += 0.5
    bg_dist = _empirical_dist(phi, bins, (phi_min, phi_max))
    w_dist = _empirical_dist(rng, bins, (phi_min, phi_max))
    kl = _kl(w_dist, bg_dist)

    return SurprisalResult(
        current_surprisal=current_s,
        mean_surprisal=mean_s,
        surprisal_level=level,
        kl_divergence=kl,
        is_novel=is_novel,
        peak_surprisal=peak_s,
        surprisal_trend=trend,
        ar_weights=weights.tolist(),
        n_observations=len(phi),
    )
