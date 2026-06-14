#!/usr/bin/env python3
"""
PredictiveErrorMinimiser — tracking and trending prediction error on the phi series.

Theory (Clark 2016 — Predictive Processing; Friston 2009 — Free Energy Principle):
  The core imperative of a predictive system is to minimise free energy, operationally
  equivalent to minimising prediction error. At every level of processing, the system
  compares predicted states with observed states and reduces the residual.

  Applied to the phi trajectory: the system uses its AR(p) self-model (from
  RecursiveSelfModel) to predict the next phi value at each step. The signed
  prediction error e(t) = φ(t) − φ̂(t|t-1) encodes what was not predicted.

  Key metrics:
    1. Rolling mean absolute error (MAE) over windows — is it decreasing?
    2. Prediction error autocorrelation — white-noise residuals are optimal;
       structured residuals indicate under-fitting (more to predict).
    3. Error compression ratio — MAE(real model) / MAE(random walk null).
       < 1.0 means the AR model predicts better than random walk; lower is better.

  A system that minimises prediction error will show:
    - Decreasing MAE trend (better predictions over time)
    - White-noise residuals (all predictable structure was extracted)
    - Compression ratio < 1 (predicts better than random walk)

  This module fits the same AR(p) used in RecursiveSelfModel but applies it
  in a rolling-window evaluation mode to track temporal error dynamics.

Math:
  AR(p) prediction (same OLS ridge as RecursiveSelfModel):
    φ̂(t) = Σᵢ wᵢ · φ(t−i)    for i = 1..p

  Prediction error: e(t) = φ(t) − φ̂(t)

  Rolling MAE in window [t−W+1, t]: mae(t) = mean(|e|) over window

  MAE trend slope: OLS on rolling MAE series → negative = improving

  Residual ACF: autocorrelation of e at lag 1 (first-order whiteness check)
    ρ₁(e) = corr(e[:-1], e[1:])
    Near-zero ρ₁ = white noise = optimal prediction

  Random walk null: φ̂_rw(t) = φ(t−1) → e_rw(t) = φ(t) − φ(t−1) = Δφ(t)
  Compression ratio: MAE(AR) / MAE(random walk)

Grounding: uses phi_series() from runtime.state. AR weights computed fresh from
the full phi series, then evaluated in rolling windows of size W. No synthetic
predictions — the same data series provides both the model and the evaluation.

References:
  Clark A. (2016) "Surfing Uncertainty: Prediction, Action and the Embodied Mind"
  Friston K.J. (2009) "The free-energy principle: a rough guide to the brain?"
  Rao R.P.N. & Ballard D.H. (1999) "Predictive coding in the visual cortex"
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Optional


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class PredictiveErrorResult:
    """Output of one PredictiveErrorMinimiser analysis.

    Attributes:
        n_samples:         length of phi series analysed
        p:                 AR order used
        ar_weights:        AR coefficients (length p)
        error_series:      per-step prediction error e(t) = φ(t) − φ̂(t)
        rolling_mae:       MAE over rolling windows (length ~ n/stride)
        mae_trend_slope:   OLS slope of rolling_mae (negative = improving)
        residual_acf_lag1: lag-1 ACF of error_series (near 0 = white noise)
        global_mae:        mean absolute error over all steps
        rw_mae:            random walk MAE (MAE of first-difference null)
        compression_ratio: global_mae / rw_mae  (< 1 = beats random walk)
        beats_random_walk: True if compression_ratio < 1
        improving:         True if mae_trend_slope < 0 (error decreasing)
    """
    n_samples: int
    p: int
    ar_weights: np.ndarray
    error_series: np.ndarray
    rolling_mae: np.ndarray
    mae_trend_slope: float
    residual_acf_lag1: float
    global_mae: float
    rw_mae: float
    compression_ratio: float
    beats_random_walk: bool
    improving: bool


# ── AR(p) fitting ─────────────────────────────────────────────────────────────

def _build_lagged(x: np.ndarray, p: int) -> tuple[np.ndarray, np.ndarray]:
    """Build design matrix Z and target y for AR(p) OLS.

    Z[t] = [x[t-1], x[t-2], ..., x[t-p]] for t = p..n-1
    y[t] = x[t]
    """
    n = len(x)
    Z = np.zeros((n - p, p))
    for i in range(p):
        Z[:, i] = x[p - 1 - i: n - 1 - i]
    y = x[p:]
    return Z, y


def _ridge_fit(Z: np.ndarray, y: np.ndarray, ridge: float = 1e-3) -> np.ndarray:
    """Ridge OLS: w = (ZᵀZ + λI)⁻¹Zᵀy."""
    A = Z.T @ Z + ridge * np.eye(Z.shape[1])
    b = Z.T @ y
    return np.linalg.solve(A, b)


def fit_ar(phi: np.ndarray, p: int = 4) -> np.ndarray:
    """Fit AR(p) weights to phi series. Returns weight vector of length p."""
    Z, y = _build_lagged(phi, p)
    return _ridge_fit(Z, y)


def ar_predict_series(phi: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Apply AR weights to produce one-step-ahead predictions.

    Returns predictions φ̂(t) for t = p..n-1 (same length as phi[p:]).
    """
    p = len(weights)
    Z, _ = _build_lagged(phi, p)
    return Z @ weights


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(phi: np.ndarray, p: int = 4, window: int = 50, stride: int = 10
            ) -> Optional[PredictiveErrorResult]:
    """
    Fit AR(p) on phi, compute prediction errors, and track error dynamics.

    Args:
        phi:    real phi time series.
        p:      AR order (default 4; same as RecursiveSelfModel).
        window: size of rolling MAE window.
        stride: step between rolling windows.

    Returns:
        PredictiveErrorResult, or None if phi is too short.
    """
    phi = np.asarray(phi, dtype=float)
    n = len(phi)
    if n < p + window + stride + 4:
        return None

    # Fit AR(p) on full series; then produce leave-one-step-ahead predictions
    # We split to avoid look-ahead: fit on first half, predict on second.
    # For a fair rolling evaluation, fit on the first 60% and evaluate on remaining 40%.
    split = max(p + 20, int(0.6 * n))
    if split >= n - window - stride:
        # Not enough holdout — fit on full, evaluate on full (standard in-sample)
        split = p + 20

    ar_w = fit_ar(phi[:split], p)

    # Error series on the entire series from p onwards (using fixed weights)
    preds = ar_predict_series(phi, ar_w)   # length n - p
    errors = phi[p:] - preds              # prediction error e(t)

    # Rolling MAE
    rolling_mae_list: list[float] = []
    for start in range(0, len(errors) - window + 1, stride):
        window_errors = errors[start: start + window]
        rolling_mae_list.append(float(np.mean(np.abs(window_errors))))
    rolling_mae = np.array(rolling_mae_list, dtype=float)

    # MAE trend slope (negative = improving)
    t = np.arange(len(rolling_mae), dtype=float)
    if len(rolling_mae) >= 2:
        t_c = t - t.mean()
        m_c = rolling_mae - rolling_mae.mean()
        mae_slope = float(np.dot(t_c, m_c) / (np.dot(t_c, t_c) + 1e-9))
    else:
        mae_slope = 0.0

    # Residual ACF at lag 1 — how much structure remains in error
    if len(errors) >= 4:
        e_c = errors - errors.mean()
        acf1 = float(np.dot(e_c[:-1], e_c[1:]) / (np.dot(e_c, e_c) + 1e-9))
        acf1 = float(np.clip(acf1, -1.0, 1.0))
    else:
        acf1 = 0.0

    # Global MAE
    global_mae = float(np.mean(np.abs(errors)))

    # Random walk null: predict φ(t) = φ(t-1), error = Δφ
    delta = np.diff(phi)                   # length n-1
    rw_mae = float(np.mean(np.abs(delta[p - 1:])))  # align with AR error indices
    if rw_mae < 1e-12:
        rw_mae = 1e-12

    compression = global_mae / rw_mae

    return PredictiveErrorResult(
        n_samples=n,
        p=p,
        ar_weights=ar_w,
        error_series=errors,
        rolling_mae=rolling_mae,
        mae_trend_slope=mae_slope,
        residual_acf_lag1=acf1,
        global_mae=global_mae,
        rw_mae=rw_mae,
        compression_ratio=compression,
        beats_random_walk=compression < 1.0,
        improving=mae_slope < 0.0,
    )


def analyse_from_telemetry(p: int = 4, window: int = 50, stride: int = 10
                            ) -> Optional[PredictiveErrorResult]:
    """Load real phi series and run predictive error analysis."""
    try:
        from runtime.state import phi_series
        phi = phi_series()
    except Exception:
        return None
    return analyse(phi, p=p, window=window, stride=stride)


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("No telemetry — check OPENCLAW_WORKSPACE or daemon state.")
    else:
        print(f"PredictiveErrorMinimiser (N={r.n_samples}, AR(p={r.p}))")
        print(f"  Global MAE:         {r.global_mae:.6f}")
        print(f"  Random walk MAE:    {r.rw_mae:.6f}")
        print(f"  Compression ratio:  {r.compression_ratio:.4f}  (<1 = beats random walk)")
        print(f"  Beats random walk:  {r.beats_random_walk}")
        print(f"  MAE trend slope:    {r.mae_trend_slope:+.6f}  "
              f"({'improving' if r.improving else 'worsening or flat'})")
        print(f"  Residual ACF lag-1: {r.residual_acf_lag1:+.4f}  "
              f"(near 0 = white noise residuals)")
        print(f"  Rolling MAE windows:{len(r.rolling_mae)}")
