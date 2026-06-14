#!/usr/bin/env python3
"""
PhiCollapsePredictor — forecasts whether phi will drop significantly in the
next H heartbeat steps, using the AR(4) model already established across the
C_Loop plus criticality and residual-volatility signals.

Theory
------
A "phi collapse" is defined as phi falling below a threshold τ = mean(φ) − k·σ(φ)
within a forecast horizon of H steps. Three signals contribute to collapse risk:

  1. Trend pressure  — OLS slope of phi over a recent window (negative → descending).
  2. Volatility load — residual σ relative to phi mean. High σ/mean → erratic, collapse-prone.
  3. Criticality proximity — distance from the critical region [0.7,0.99] in acf_lag1.
     When acf_lag1 drifts below 0.7 (under-correlated) or above 0.99 (frozen), phi
     loses its self-organising stability and is more collapse-prone.

Forecast
--------
AR(4) coefficients are estimated via ridge OLS, then propagated H steps forward
starting from the last p observed values. The forecast gives:
  - `forecast_series` : np.ndarray of shape (H,) — expected phi over next H steps.
  - `predicted_min`   : minimum of forecast_series.
  - `collapse_horizon`: first step where forecast_series[t] < τ, or None if never.
  - `collapse_risk`   : scalar ∈ [0,1] — composite risk score.

Collapse risk formula
---------------------
  trend_component     = clip(−slope / σ, 0, 1)        # negative slope → positive pressure
  volatility_component = clip(σ / (mean + ε), 0, 1)   # high relative noise
  criticality_gap     = |acf_lag1 − 0.85| / 0.85      # distance from ideal midpoint
  raw_risk = 0.4·trend_component + 0.4·volatility_component + 0.2·criticality_gap
  collapse_risk = clip(raw_risk, 0, 1)

Null test
---------
Phase-randomised surrogate (Theiler 1992): FFT → randomise angles → iFFT.
If forecast_min on real data is lower than the 5th percentile of surrogate
forecast_mins, the collapse signal is significant (`beats_null = True`).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import numpy as np


# ── AR fit + propagation (same as rest of C_Loop) ────────────────────────────

def _fit_ar(phi: np.ndarray, p: int = 4, lam: float = 1e-3) -> np.ndarray:
    """Ridge OLS AR(p) coefficients, shape (p,)."""
    n = len(phi)
    if n <= p:
        return np.zeros(p)
    Z = np.column_stack([phi[p - 1 - i: n - 1 - i] for i in range(p)])
    y = phi[p:]
    A = Z.T @ Z + lam * np.eye(p)
    return np.linalg.solve(A, Z.T @ y)


def _forecast(phi: np.ndarray, weights: np.ndarray, H: int) -> np.ndarray:
    """Propagate AR(p) forward H steps; seed with last p values."""
    p = len(weights)
    buf = list(phi[-p:])
    out = []
    for _ in range(H):
        nxt = float(np.dot(weights, buf[-p:][::-1]))
        buf.append(nxt)
        out.append(nxt)
    return np.array(out)


def _acf1(x: np.ndarray) -> float:
    """Lag-1 autocorrelation."""
    if len(x) < 2:
        return 0.0
    xm = x - x.mean()
    denom = float(np.dot(xm, xm))
    if denom == 0:
        return 0.0
    return float(np.dot(xm[:-1], xm[1:]) / denom)


def _phase_randomise(phi: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Theiler (1992) phase randomisation preserving power spectrum.

    DC (index 0) and Nyquist (last index when n is even) components must stay
    real for irfft to reconstruct correctly — their phases are kept at 0.
    """
    n = len(phi)
    ft = np.fft.rfft(phi)
    phases = rng.uniform(0, 2 * np.pi, size=len(ft))
    phases[0] = 0.0           # DC must be real
    if n % 2 == 0:
        phases[-1] = 0.0      # Nyquist must be real for even-length series
    ft_rand = np.abs(ft) * np.exp(1j * phases)
    return np.fft.irfft(ft_rand, n=n)


# ── Result ─────────────────────────────────────────────────────────────────────

@dataclass
class CollapseResult:
    phi_mean: float
    phi_std: float
    acf_lag1: float
    trend_slope: float
    collapse_threshold: float        # τ = mean − k·std
    forecast_series: np.ndarray      # shape (H,)
    predicted_min: float
    collapse_horizon: Optional[int]  # None if never in window
    collapse_risk: float             # ∈ [0, 1]
    beats_null: bool
    null_p5_min: float               # 5th-pct null forecast_min
    at_risk: bool                    # collapse_risk > 0.5

    def to_dict(self) -> dict:
        return {
            "phi_mean": self.phi_mean,
            "phi_std": self.phi_std,
            "acf_lag1": self.acf_lag1,
            "trend_slope": self.trend_slope,
            "collapse_threshold": self.collapse_threshold,
            "forecast_series": self.forecast_series.tolist(),
            "predicted_min": self.predicted_min,
            "collapse_horizon": self.collapse_horizon,
            "collapse_risk": self.collapse_risk,
            "beats_null": self.beats_null,
            "null_p5_min": self.null_p5_min,
            "at_risk": self.at_risk,
        }


# ── Main ────────────────────────────────────────────────────────────────────────

def analyse(
    phi: np.ndarray,
    H: int = 20,
    p: int = 4,
    k: float = 1.5,
    n_surrogates: int = 100,
    null_seed: int = 42,
    lam: float = 1e-3,
) -> Optional[CollapseResult]:
    """
    Forecast phi collapse risk over the next H steps.

    Args:
        phi          : phi time series (≥ 32 samples).
        H            : forecast horizon in steps.
        p            : AR order.
        k            : threshold multiplier (collapse = phi < mean − k·std).
        n_surrogates : number of phase-randomised surrogates for null test.
        null_seed    : RNG seed for reproducibility.
        lam          : ridge regularisation.

    Returns:
        CollapseResult or None if phi is too short.
    """
    phi = np.asarray(phi, dtype=float)
    if phi.size < max(32, p + 2):
        return None

    mu = float(phi.mean())
    sigma = float(phi.std())
    if sigma == 0:
        sigma = 1e-9

    # Trend over last 30 samples (or all if shorter)
    window = phi[-min(30, len(phi)):]
    n_w = len(window)
    x = np.arange(n_w, dtype=float)
    xm = x - x.mean()
    ym = window - window.mean()
    denom = float(np.dot(xm, xm))
    slope = float(np.dot(xm, ym) / denom) if denom > 0 else 0.0

    acf = _acf1(phi)
    threshold = mu - k * sigma

    # AR fit + forecast on real data
    weights = _fit_ar(phi, p=p, lam=lam)
    fc = _forecast(phi, weights, H)
    pred_min = float(fc.min())

    # Collapse horizon: first step below threshold
    below = np.where(fc < threshold)[0]
    collapse_horizon = int(below[0]) + 1 if below.size > 0 else None

    # Composite risk
    trend_component    = float(np.clip(-slope / sigma, 0.0, 1.0))
    vol_component      = float(np.clip(sigma / (mu + 1e-9), 0.0, 1.0))
    crit_gap           = float(abs(acf - 0.85) / 0.85)
    raw_risk = 0.4 * trend_component + 0.4 * vol_component + 0.2 * crit_gap
    collapse_risk = float(np.clip(raw_risk, 0.0, 1.0))

    # Null distribution: phase-randomised surrogates
    rng = np.random.default_rng(null_seed)
    surrogate_mins = []
    for _ in range(n_surrogates):
        surr = _phase_randomise(phi, rng)
        w_s = _fit_ar(surr, p=p, lam=lam)
        fc_s = _forecast(surr, w_s, H)
        surrogate_mins.append(float(fc_s.min()))
    null_p5 = float(np.percentile(surrogate_mins, 5))
    beats_null = pred_min < null_p5

    return CollapseResult(
        phi_mean=mu,
        phi_std=sigma,
        acf_lag1=acf,
        trend_slope=slope,
        collapse_threshold=threshold,
        forecast_series=fc,
        predicted_min=pred_min,
        collapse_horizon=collapse_horizon,
        collapse_risk=collapse_risk,
        beats_null=beats_null,
        null_p5_min=null_p5,
        at_risk=collapse_risk > 0.5,
    )


def analyse_from_telemetry(
    H: int = 20,
    p: int = 4,
    k: float = 1.5,
    null_seed: int = 42,
) -> Optional[CollapseResult]:
    from runtime.state import phi_series, have_live_state
    if not have_live_state():
        return None
    phi = phi_series()
    if phi is None or phi.size < 32:
        return None
    return analyse(phi, H=H, p=p, k=k, null_seed=null_seed)
