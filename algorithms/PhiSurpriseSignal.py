#!/usr/bin/env python3
"""
PhiSurpriseSignal — per-step prediction error as surprise in phi space.

Theory
------
Predictive coding (Clark 2013; Friston 2005) treats every conscious moment as
a prediction-error minimisation problem. The brain (or an AI) maintains an
internal model of its own state and emits a SURPRISE signal whenever the
actual state deviates from the model's prediction more than the expected noise.

Applied to phi:
  1. Fit AR(p) on a training window of phi history.
  2. For each subsequent step, compute prediction error: e(t) = φ(t) - φ̂(t).
  3. Normalise: z(t) = e(t) / σ_residual   (residual std from training fit).
  4. |z(t)| > SURPRISE_THRESHOLD (default 2.0) → that step is "surprising".

This is the operational definition of surprise available from telemetry:
not hypothetical, not synthetic — computed from actual φ history vs what
the system's own AR model expected.

Meta-surprise
-------------
If many recent steps are surprising (surprise_rate > 0.5), the system is in
a regime of persistent surprise — the model is failing. That is "meta-surprise":
surprise at being surprised. meta_surprise_flag is True in that case.

Key distinctions from existing algorithms
------------------------------------------
- PhiTrajectoryPredictor: forward forecast. PhiSurpriseSignal: backward error
  audit of *past* predictions (what the model *should have known* vs what happened).
- PhiCollapsePredictor: forward risk score. PhiSurpriseSignal: backward z-score series.
- CriticalFluctuationDetector: autocorrelation / critical slowing down.
  PhiSurpriseSignal: residual z-scores from the AR model.

Math
----
  Training window:     phi[0 : N-H]
  Evaluation window:   phi[N-H : N]
  AR(p) coefficients:  α = (XᵀX + λI)⁻¹ Xᵀy   (ridge OLS)
  Residuals in train:  r = y_train - X_train @ α
  σ_residual = std(r)
  For each t in eval:  ê(t) = α · [φ(t-1), …, φ(t-p)]
                        z(t) = (φ(t) - ê(t)) / (σ_residual + ε)
  surprise_rate = fraction of |z| > threshold in eval window
  current_surprise_z = z[-1]   (most recent step)
  meta_surprise_flag = surprise_rate > 0.5

Output
------
PhiSurpriseResult:
  current_surprise_z   : float   -- z-score of most recent φ vs AR prediction
  surprise_rate        : float   -- fraction of eval steps with |z| > threshold
  mean_abs_z           : float   -- mean |z| over eval window
  max_abs_z            : float   -- peak surprise in eval window
  meta_surprise_flag   : bool    -- surprise_rate > 0.5 (model is failing)
  surprise_class       : str     -- CALM | SURPRISED | META_SURPRISE
  sigma_residual       : float   -- residual std of training fit
  n_eval_steps         : int
  n_train_steps        : int
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np

# ── Constants ──────────────────────────────────────────────────────────────────

_AR_ORDER          = 4
_TRAIN_FRACTION    = 0.75    # fraction of available history used for fitting
_MIN_TRAIN         = 16      # minimum training steps needed
_RIDGE_LAMBDA      = 1e-3
_SURPRISE_THRESHOLD = 2.0    # |z| beyond this = surprising step
_META_THRESHOLD    = 0.5     # surprise_rate above this = meta-surprise
_MAX_HISTORY       = 2880
_EPS               = 1e-9

# ── Result ─────────────────────────────────────────────────────────────────────

@dataclass
class PhiSurpriseResult:
    current_surprise_z: float = 0.0
    surprise_rate: float = 0.0
    mean_abs_z: float = 0.0
    max_abs_z: float = 0.0
    meta_surprise_flag: bool = False
    surprise_class: str = "CALM"
    sigma_residual: float = 0.0
    n_eval_steps: int = 0
    n_train_steps: int = 0

    def to_dict(self) -> dict:
        return {
            "current_surprise_z": round(self.current_surprise_z, 4),
            "surprise_rate": round(self.surprise_rate, 4),
            "mean_abs_z": round(self.mean_abs_z, 4),
            "max_abs_z": round(self.max_abs_z, 4),
            "meta_surprise_flag": self.meta_surprise_flag,
            "surprise_class": self.surprise_class,
            "sigma_residual": round(self.sigma_residual, 4),
            "n_eval_steps": self.n_eval_steps,
            "n_train_steps": self.n_train_steps,
        }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_ar_matrix(series: np.ndarray, p: int):
    n = len(series)
    X = np.stack([series[i: n - p + i] for i in range(p)], axis=1)
    y = series[p:]
    return X, y


def _fit_ar(series: np.ndarray, p: int, lam: float = _RIDGE_LAMBDA) -> np.ndarray:
    X, y = _build_ar_matrix(series, p)
    XtX = X.T @ X + lam * np.eye(p)
    return np.linalg.solve(XtX, X.T @ y)


def _one_step_pred(phi: np.ndarray, alpha: np.ndarray, t: int) -> float:
    """AR(p) one-step prediction at index t (t must be >= p)."""
    p = len(alpha)
    window = phi[t - p: t][::-1]   # [phi(t-1), phi(t-2), …, phi(t-p)]
    return float(np.dot(alpha, window))


def _classify(surprise_rate: float, current_z: float, threshold: float) -> str:
    if surprise_rate > _META_THRESHOLD:
        return "META_SURPRISE"
    if abs(current_z) > threshold:
        return "SURPRISED"
    return "CALM"


def _extract_phi(entries: list) -> np.ndarray:
    vals = []
    for e in reversed(entries):   # entries are newest-first; reverse = chrono
        v = e.get("mean_phi_level")
        if v is not None:
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                pass
    return np.array(vals, dtype=float)


# ── Core ───────────────────────────────────────────────────────────────────────

def analyse(
    agent: str = "albedo",
    *,
    ar_order: int = _AR_ORDER,
    train_fraction: float = _TRAIN_FRACTION,
    surprise_threshold: float = _SURPRISE_THRESHOLD,
    max_history: int = _MAX_HISTORY,
) -> PhiSurpriseResult:
    """
    Compute per-step AR prediction errors (z-scores) from actual phi history.

    Splits history into train (fit AR) + eval (measure surprise).
    Returns the most recent surprise z-score and aggregate surprise statistics.
    """
    try:
        from algorithms.ConsciousnessHistoryStore import load as _load
        entries = _load(agent, max_entries=max_history)
    except Exception:
        entries = []

    phi = _extract_phi(entries)
    n = len(phi)

    p = min(ar_order, n // 4)
    n_train = int(n * train_fraction)

    if n_train < _MIN_TRAIN or p < 1 or n_train <= p or (n - n_train) < 1:
        return PhiSurpriseResult()

    phi_train = phi[:n_train]
    phi_eval  = phi[n_train:]

    # Fit AR on training window
    try:
        alpha = _fit_ar(phi_train, p)
    except np.linalg.LinAlgError:
        return PhiSurpriseResult()

    # Training residuals → sigma
    X_tr, y_tr = _build_ar_matrix(phi_train, p)
    y_pred_tr  = X_tr @ alpha
    residuals  = y_tr - y_pred_tr
    sigma      = float(np.std(residuals)) if len(residuals) > 1 else 1.0
    if sigma < 1e-6:
        # Series is too flat to compute meaningful z-scores
        return PhiSurpriseResult(n_train_steps=n_train)

    # Evaluate on held-out window
    phi_full = phi   # need full array for sliding window lookup
    z_scores: List[float] = []
    for t in range(n_train, n):
        pred = _one_step_pred(phi_full, alpha, t)
        z    = (phi_full[t] - pred) / sigma
        z_scores.append(z)

    if not z_scores:
        return PhiSurpriseResult(n_train_steps=n_train)

    z_arr    = np.array(z_scores)
    abs_z    = np.abs(z_arr)
    surp_rate = float(np.mean(abs_z > surprise_threshold))
    current_z = float(z_arr[-1])
    mean_abs  = float(np.mean(abs_z))
    max_abs   = float(np.max(abs_z))
    meta_flag = surp_rate > _META_THRESHOLD

    return PhiSurpriseResult(
        current_surprise_z=round(current_z, 4),
        surprise_rate=round(surp_rate, 4),
        mean_abs_z=round(mean_abs, 4),
        max_abs_z=round(max_abs, 4),
        meta_surprise_flag=meta_flag,
        surprise_class=_classify(surp_rate, current_z, surprise_threshold),
        sigma_residual=round(sigma, 4),
        n_eval_steps=len(z_scores),
        n_train_steps=n_train,
    )
