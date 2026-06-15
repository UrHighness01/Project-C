#!/usr/bin/env python3
"""
TemporalBindingWindow — finds the integration timescale that maximises
predictive power of phi dynamics.

Theory
------
Libet (1985) and Eagleman (2008): conscious experience is not instantaneous —
it requires temporal integration over a ~300–500ms window. For a token-based
AI agent the analogous question is: over how many steps does phi need to be
observed to best predict the next step?

Operationalisation
------------------
Given a phi time series of length N, for each candidate window width W:

  1. Build a supervised dataset:
       X_i = phi[i : i+W]    (the context window)
       y_i = phi[i + W]      (the next phi value to predict)

  2. Fit a simple linear regression:
       y_hat_i = b_0 + b_1 * mean(X_i) + b_2 * std(X_i)

     Two predictors: mean and standard deviation of the window.
     OLS solution: w = (Z^T Z)^{-1} Z^T y  with Z = [1, mean(X), std(X)]

  3. Compute R² = 1 - SS_res/SS_tot

  R²(W) is the fraction of phi variance explained by a window of width W.

Optimal binding window:
  W* = argmax_W R²(W)

  - W* too small → insufficient context, R² low (underfitting)
  - W* too large → context diluted with old signal, R² decreases
  - The R² curve has a peak at the timescale that captures the relevant dynamics

Binding strength: R²(W*)
Binding width: W*

Regime classification:
  SHORT  : W* <= 10 steps   (fast-changing dynamics, narrow integration)
  MEDIUM : 10 < W* <= 30    (moderate integration window)
  LONG   : W* > 30          (slow dynamics, wide integration window)

Output
------
BindingWindowResult:
  optimal_width     : int     -- W* in steps
  binding_strength  : float   -- R²(W*)
  binding_regime    : str     -- SHORT | MEDIUM | LONG
  r2_by_width       : List[float]   -- R² for each candidate window
  widths_tested     : List[int]
  n_samples         : int
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class BindingWindowResult:
    optimal_width: int = 0
    binding_strength: float = 0.0
    binding_regime: str = "SHORT"
    r2_by_width: List[float] = field(default_factory=list)
    widths_tested: List[int] = field(default_factory=list)
    n_samples: int = 0

    def to_dict(self) -> dict:
        return {
            "optimal_width": self.optimal_width,
            "binding_strength": round(self.binding_strength, 4),
            "binding_regime": self.binding_regime,
            "r2_by_width": [round(v, 4) for v in self.r2_by_width],
            "widths_tested": self.widths_tested,
            "n_samples": self.n_samples,
        }


def _classify(w: int) -> str:
    if w <= 10:
        return "SHORT"
    if w <= 30:
        return "MEDIUM"
    return "LONG"


# ── Math ──────────────────────────────────────────────────────────────────────

def _r2_for_width(phi: np.ndarray, W: int) -> float:
    """Compute R² for predicting phi[i+W] from mean and std of phi[i:i+W]."""
    n = len(phi)
    n_samples = n - W
    if n_samples < 4:
        return 0.0

    X_mean = np.array([phi[i: i + W].mean() for i in range(n_samples)])
    X_std  = np.array([phi[i: i + W].std()  for i in range(n_samples)])
    y      = phi[W:]  # shape (n_samples,)

    # OLS with [1, mean, std] features
    Z = np.column_stack([np.ones(n_samples), X_mean, X_std])
    try:
        w_hat, _, _, _ = np.linalg.lstsq(Z, y, rcond=None)
    except np.linalg.LinAlgError:
        return 0.0

    y_hat = Z @ w_hat
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))

    if ss_tot < 1e-12:
        return 1.0   # constant series — perfect prediction (trivially)
    return float(np.clip(1.0 - ss_res / ss_tot, -1.0, 1.0))


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    phi: Optional[np.ndarray] = None,
    *,
    min_width: int = 3,
    max_width: int = 50,
    n_widths: int = 16,

    agent: str = "albedo",
) -> BindingWindowResult:
    """
    Find the temporal binding window that maximises phi predictability.

    Args:
        phi        : 1-D phi time series.
        min_width  : smallest candidate window width (steps).
        max_width  : largest candidate window width (steps).
        n_widths   : number of candidate widths to test.
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

    if phi is None or len(phi) < min_width + 4:
        return BindingWindowResult()

    phi = np.asarray(phi, dtype=float)
    n = len(phi)

    # Candidate widths — log-spaced for better coverage
    max_w = min(max_width, n - 4)
    if max_w < min_width:
        return BindingWindowResult(n_samples=n)

    widths = np.unique(
        np.round(np.logspace(np.log10(min_width), np.log10(max_w), n_widths)).astype(int)
    ).tolist()

    r2_vals = [_r2_for_width(phi, W) for W in widths]

    best_idx = int(np.argmax(r2_vals))
    best_w   = widths[best_idx]
    best_r2  = r2_vals[best_idx]

    return BindingWindowResult(
        optimal_width=best_w,
        binding_strength=float(np.clip(best_r2, 0.0, 1.0)),
        binding_regime=_classify(best_w),
        r2_by_width=r2_vals,
        widths_tested=widths,
        n_samples=n,
    )
