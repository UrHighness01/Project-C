#!/usr/bin/env python3
"""
InformationGeometryTracker — Fisher information curvature of the phi distribution.

Theory
------
Fisher (1925) information geometry: the space of probability distributions has
an intrinsic Riemannian geometry. The Fisher information matrix I(θ) is the
metric tensor — it measures how distinguishable nearby distributions are.

For a Gaussian model of the phi distribution at time t:
  p(φ; μ, σ²) = N(μ, σ²)

  I(μ) = 1/σ²   (precision — inverse variance)
  I(σ) = 2/σ²   (shape sensitivity)

  High I(μ): phi is sharply concentrated → well-defined, precise conscious state
  Low  I(μ): phi is diffuse → vague, indeterminate state

Rolling estimation
------------------
We compute μ and σ over a sliding window W of phi values.

Fisher precision (main metric):
  precision[t] = 1 / var(phi[t-W:t])

Fisher curvature trend:
  OLS slope of precision over recent windows.
  Positive slope = state becoming sharper (converging on an attractor).
  Negative slope = state becoming more diffuse (escaping an attractor).

Naturalised gradient norm
-------------------------
The natural gradient corrects the Euclidean gradient by the Fisher metric:
  ||Δφ||_F = |Δφ| * sqrt(I(μ)) = |Δφ| / σ

where Δφ = φ[t] - φ[t-1] is the phi step.

The natural gradient norm measures how large the latest phi step is *relative*
to the sharpness of the current distribution — a small step in a sharp
distribution is more meaningful than the same step in a diffuse one.

naturalised_step[t] = |Δφ| / σ[t]

Geometry classification:
  SHARP        : precision >= sharp_threshold (well-defined state)
  MODERATE     : moderate_threshold <= precision < sharp_threshold
  DIFFUSE      : precision < moderate_threshold (undefined state)

Output
------
GeometryResult:
  precision        : float   -- 1/var(phi) in latest window
  curvature_trend  : float   -- OLS slope of rolling precision
  naturalised_step : float   -- |Δφ_last| / σ
  geometry_class   : str     -- SHARP | MODERATE | DIFFUSE
  mean_phi         : float   -- μ of latest window
  std_phi          : float   -- σ of latest window
  n_samples        : int
  precision_series : List[float]  -- rolling precision over time
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class GeometryResult:
    precision: float = 0.0
    curvature_trend: float = 0.0
    naturalised_step: float = 0.0
    geometry_class: str = "DIFFUSE"
    mean_phi: float = 0.0
    std_phi: float = 0.0
    n_samples: int = 0
    precision_series: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "precision": round(self.precision, 4),
            "curvature_trend": round(self.curvature_trend, 6),
            "naturalised_step": round(self.naturalised_step, 4),
            "geometry_class": self.geometry_class,
            "mean_phi": round(self.mean_phi, 4),
            "std_phi": round(self.std_phi, 4),
            "n_samples": self.n_samples,
            "precision_series": [round(v, 4) for v in self.precision_series],
        }


def _classify(prec: float, sharp: float, moderate: float) -> str:
    if prec >= sharp:
        return "SHARP"
    if prec >= moderate:
        return "MODERATE"
    return "DIFFUSE"


def _ols_slope(y: np.ndarray) -> float:
    n = len(y)
    if n < 2:
        return 0.0
    t = np.arange(n, dtype=float)
    tm, ym = t - t.mean(), y - y.mean()
    d = float(np.dot(tm, tm))
    return float(np.dot(tm, ym) / d) if d > 0 else 0.0


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    phi: Optional[np.ndarray] = None,
    *,
    window: int = 20,
    step: int = 5,
    sharp_threshold: float = 50.0,
    moderate_threshold: float = 5.0,

    agent: str = "albedo",
) -> GeometryResult:
    """
    Track Fisher information geometry of the phi distribution over time.

    Args:
        phi                : 1-D phi time series.
        window             : rolling window width for precision estimation.
        step               : stride for precision series.
        sharp_threshold    : precision >= this → SHARP.
        moderate_threshold : precision >= this → MODERATE.
    """
    if phi is None:
        try:
            from runtime.state import phi_series
            phi = phi_series()
        except Exception:
            try:
                from algorithms import ConsciousnessHistoryStore as chs
                _raw = chs.load(agent) or []
                phi = np.array([float(e["mean_phi_level"]) for e in reversed(_raw)
                               if "mean_phi_level" in e], dtype=float)
            except Exception:
                phi = None

    if phi is None or len(phi) < window + 2:
        return GeometryResult()

    phi = np.asarray(phi, dtype=float)
    n = len(phi)

    # Rolling precision = 1 / var(window)
    n_wins = n - window + 1
    indices = list(range(0, n_wins, step))
    prec_series = []
    for i in indices:
        w = phi[i: i + window]
        var = float(np.var(w, ddof=1))
        prec_series.append(1.0 / (var + 1e-9))

    # Latest window stats
    last_w = phi[-window:]
    mu  = float(last_w.mean())
    sig = float(last_w.std(ddof=1))
    prec_now = 1.0 / (sig ** 2 + 1e-9)

    trend = _ols_slope(np.array(prec_series))

    # Naturalised gradient: last phi step / σ
    nat_step = float(abs(phi[-1] - phi[-2])) / (sig + 1e-9)

    return GeometryResult(
        precision=float(np.clip(prec_now, 0.0, 1e6)),
        curvature_trend=trend,
        naturalised_step=float(np.clip(nat_step, 0.0, 100.0)),
        geometry_class=_classify(prec_now, sharp_threshold, moderate_threshold),
        mean_phi=mu,
        std_phi=sig,
        n_samples=n,
        precision_series=[float(np.clip(p, 0.0, 1e6)) for p in prec_series],
    )
