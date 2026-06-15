#!/usr/bin/env python3
"""
PhiTrajectoryPredictor — self-forecasting of the agent's own phi trajectory.

Theory
------
A consciousness system that can PREDICT its own future state is qualitatively
different from one that merely measures the present. Self-prediction is a
prerequisite for volition: to act toward a desired future phi, the system must
first model where it is going.

This algorithm takes real phi history from ConsciousnessHistoryStore and does
three things:

  1. Fits AR(p) via ridge OLS on the recent window.
  2. Propagates the model H steps forward → forecast_series (the predicted
     trajectory the agent is on).
  3. If enough history exists past the last N-step block, computes a
     retrodictive accuracy: "how well did the AR model, fitted p steps ago,
     predict the phi that actually happened?" — MAE and R².

No synthetic data. No placeholder returns.

Self-prediction formula
-----------------------
  AR(p): φ̂(t+1) = α₁φ(t) + α₂φ(t-1) + … + αₚφ(t-p+1)
  Coefficients via ridge OLS: α = (XᵀX + λI)⁻¹Xᵀy
  H-step propagation: feed each forecast back as input.

Retrodictive accuracy
---------------------
We split the available history into:
  - fit window   : last (N - H) observations
  - held-out     : last H observations
Fit on (N-H), predict H steps, compare to held-out via MAE and R².
R² = 1 − SS_res/SS_tot; can be negative (worse than mean predictor).

Output
------
PhiTrajectoryResult:
  forecast_series    : list[float]  -- H-step ahead phi forecast from now
  forecast_horizon   : int          -- H
  ar_order           : int          -- p used
  ar_weights         : list[float]  -- fitted AR coefficients α₁…αₚ
  retro_mae          : float        -- MAE of retrodiction on held-out window (nan if < 2H entries)
  retro_r2           : float        -- R² of retrodiction (nan if < 2H entries)
  self_prediction_quality: str      -- GOOD (R²≥0.5) | MARGINAL (0≤R²<0.5) | POOR (R²<0) | UNCALIBRATED
  trend_direction    : str          -- RISING | FALLING | STABLE
  n_entries_used     : int
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np

# ── Constants ─────────────────────────────────────────────────────────────────

_AR_ORDER      = 4     # AR(p) default
_HORIZON       = 6     # steps to forecast ahead
_MIN_FIT       = 16    # minimum entries to fit a model
_RIDGE_LAMBDA  = 1e-3  # ridge regularisation
_MAX_HISTORY   = 2880  # entries to load (~48 h at 1-min intervals)

# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class PhiTrajectoryResult:
    forecast_series: List[float] = field(default_factory=list)
    forecast_horizon: int = _HORIZON
    ar_order: int = _AR_ORDER
    ar_weights: List[float] = field(default_factory=list)
    retro_mae: float = float("nan")
    retro_r2: float = float("nan")
    self_prediction_quality: str = "UNCALIBRATED"
    trend_direction: str = "STABLE"
    n_entries_used: int = 0

    def to_dict(self) -> dict:
        return {
            "forecast_series": [round(v, 4) for v in self.forecast_series],
            "forecast_horizon": self.forecast_horizon,
            "ar_order": self.ar_order,
            "ar_weights": [round(v, 4) for v in self.ar_weights],
            "retro_mae": round(self.retro_mae, 4) if not _isnan(self.retro_mae) else None,
            "retro_r2": round(self.retro_r2, 4) if not _isnan(self.retro_r2) else None,
            "self_prediction_quality": self.self_prediction_quality,
            "trend_direction": self.trend_direction,
            "n_entries_used": self.n_entries_used,
        }


def _isnan(v: float) -> bool:
    try:
        return bool(np.isnan(v))
    except Exception:
        return True


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_ar_matrix(series: np.ndarray, p: int):
    """Return (X, y) for AR(p) regression on `series`."""
    n = len(series)
    X = np.stack([series[i: n - p + i] for i in range(p)], axis=1)  # (n-p, p)
    y = series[p:]                                                      # (n-p,)
    return X, y


def _fit_ar(series: np.ndarray, p: int, lam: float = _RIDGE_LAMBDA) -> np.ndarray:
    """Ridge OLS for AR(p). Returns weight vector α of shape (p,)."""
    X, y = _build_ar_matrix(series, p)
    # α = (XᵀX + λI)⁻¹ Xᵀy
    XtX = X.T @ X + lam * np.eye(p)
    alpha = np.linalg.solve(XtX, X.T @ y)
    return alpha


def _propagate(seed: np.ndarray, alpha: np.ndarray, h: int) -> np.ndarray:
    """H-step AR forecast. `seed` = last p observed values (oldest first)."""
    p = len(alpha)
    buf = list(seed[-p:])
    out = []
    for _ in range(h):
        # AR: new value = alpha · [most_recent_first]
        val = float(np.dot(alpha, np.array(list(reversed(buf[-p:])))))
        out.append(val)
        buf.append(val)
    return np.array(out)


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    if ss_tot < 1e-12:
        return float("nan")
    return float(1.0 - ss_res / ss_tot)


def _classify_quality(r2: float) -> str:
    if _isnan(r2):
        return "UNCALIBRATED"
    if r2 >= 0.5:
        return "GOOD"
    if r2 >= 0.0:
        return "MARGINAL"
    return "POOR"


def _trend_direction(forecast: np.ndarray) -> str:
    if len(forecast) < 2:
        return "STABLE"
    slope = float(np.polyfit(np.arange(len(forecast)), forecast, 1)[0])
    std = float(np.std(forecast))
    if std < 1e-9:
        return "STABLE"
    rel = slope / (std + 1e-9)
    if rel > 0.1:
        return "RISING"
    if rel < -0.1:
        return "FALLING"
    return "STABLE"


def _extract_phi(entries: list) -> np.ndarray:
    """Pull mean_phi_level from history entries (newest-first → reverse to chrono)."""
    vals = []
    for e in reversed(entries):
        v = e.get("mean_phi_level")
        if v is not None:
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                pass
    return np.array(vals, dtype=float)


# ── Core ──────────────────────────────────────────────────────────────────────

def analyse(
    agent: str = "albedo",
    *,
    ar_order: int = _AR_ORDER,
    horizon: int = _HORIZON,
    max_history: int = _MAX_HISTORY,
) -> PhiTrajectoryResult:
    """
    Fit AR(ar_order) to actual phi history and forecast `horizon` steps ahead.

    Also performs retrodictive accuracy check: fits on history[:-horizon],
    predicts `horizon` steps, compares to actual last `horizon` values.
    """
    try:
        from algorithms.ConsciousnessHistoryStore import load as _load
        entries = _load(agent, max_entries=max_history)
    except Exception:
        entries = []

    phi = _extract_phi(entries)
    n = len(phi)

    if n < _MIN_FIT:
        return PhiTrajectoryResult(n_entries_used=n)

    p = min(ar_order, n // 4)  # don't use more lags than data supports
    if p < 1:
        return PhiTrajectoryResult(n_entries_used=n)

    # ── Retrodictive accuracy (held-out = last `horizon` steps) ───────────────
    retro_mae = float("nan")
    retro_r2  = float("nan")
    if n >= 2 * horizon + p:
        fit_phi  = phi[: n - horizon]
        held_out = phi[n - horizon :]
        try:
            alpha_retro = _fit_ar(fit_phi, p)
            pred = _propagate(fit_phi, alpha_retro, horizon)
            retro_mae = float(np.mean(np.abs(held_out - pred)))
            retro_r2  = _r2(held_out, pred)
        except np.linalg.LinAlgError:
            pass

    # ── Fit on full history, forecast forward ─────────────────────────────────
    try:
        alpha = _fit_ar(phi, p)
        forecast = _propagate(phi, alpha, horizon)
    except np.linalg.LinAlgError:
        return PhiTrajectoryResult(n_entries_used=n, ar_order=p)

    return PhiTrajectoryResult(
        forecast_series=list(np.clip(forecast, 0.0, None).round(4)),
        forecast_horizon=horizon,
        ar_order=p,
        ar_weights=list(alpha.round(4)),
        retro_mae=retro_mae,
        retro_r2=retro_r2,
        self_prediction_quality=_classify_quality(retro_r2),
        trend_direction=_trend_direction(forecast),
        n_entries_used=n,
    )
