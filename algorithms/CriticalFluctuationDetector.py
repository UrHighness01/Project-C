#!/usr/bin/env python3
"""
CriticalFluctuationDetector — early-warning signal for phi phase transitions.

Theory
------
Scheffer et al. (2009, Nature) showed that dynamical systems approaching a
critical transition (bifurcation / phase shift) exhibit two universal early
warnings:

  1. Critical Slowing Down (CSD): the system's recovery rate from perturbations
     decreases → measured as an increase in the lag-1 autocorrelation of the
     time series (AR-1 coefficient approaches 1).

  2. Variance amplification: fluctuations grow as the restoring force weakens.

Both signals appear *before* the transition, giving a predictive window.

For phi (integrated information):
  - phi entering a FLOW state is a positive phase transition (CSD on the way up)
  - phi collapsing (CRASH) is a negative transition (CSD on the way down)

We detect CSD by computing rolling:
  • var(t)    : variance in a sliding window of width W
  • ar1(t)    : OLS AR(1) coefficient in the same window
  • dvar/dt   : first difference of variance (positive = amplifying)
  • dar1/dt   : first difference of AR1 (positive = slowing down)

A CRITICAL alert fires when:
  • ar1 > AR1_THRESHOLD   (e.g. 0.85) — near-unit-root
  • AND dvar/dt > 0       — variance is growing, not shrinking

A WARNING alert fires when either condition alone holds.

STABLE: neither condition.

Rolling series
--------------
We return the full variance and AR1 time series so downstream algorithms
(NarrativeGenerator) can reason about trends.

Output
------
FluctuationResult:
  current_ar1       : float   -- AR(1) in latest window
  current_var       : float   -- variance in latest window
  dvar_dt           : float   -- variance first difference
  dar1_dt           : float   -- AR1 first difference
  alert_level       : str     -- CRITICAL | WARNING | STABLE
  is_critical       : bool
  n_samples         : int
  var_series        : List[float]
  ar1_series        : List[float]
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class FluctuationResult:
    current_ar1: float = 0.0
    current_var: float = 0.0
    dvar_dt: float = 0.0
    dar1_dt: float = 0.0
    alert_level: str = "STABLE"
    is_critical: bool = False
    n_samples: int = 0
    var_series: List[float] = field(default_factory=list)
    ar1_series: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "current_ar1": round(self.current_ar1, 4),
            "current_var": round(self.current_var, 6),
            "dvar_dt": round(self.dvar_dt, 6),
            "dar1_dt": round(self.dar1_dt, 6),
            "alert_level": self.alert_level,
            "is_critical": bool(self.is_critical),
            "n_samples": self.n_samples,
            "var_series": [round(v, 6) for v in self.var_series],
            "ar1_series": [round(v, 4) for v in self.ar1_series],
        }


# ── Internal maths ────────────────────────────────────────────────────────────

def _ar1(x: np.ndarray) -> float:
    """OLS AR(1) coefficient: regress x[1:] on x[:-1]."""
    y = x[1:]
    z = x[:-1]
    zm = z - z.mean()
    ym = y - y.mean()
    d = float(np.dot(zm, zm))
    if d < 1e-12:
        return 0.0
    return float(np.clip(np.dot(zm, ym) / d, -1.0, 1.0))


def _rolling_stats(phi: np.ndarray, win: int) -> tuple[np.ndarray, np.ndarray]:
    """Return parallel arrays of variance and AR(1) over sliding windows."""
    n = len(phi)
    n_windows = n - win + 1
    var_arr = np.empty(n_windows)
    ar1_arr = np.empty(n_windows)
    for i in range(n_windows):
        w = phi[i: i + win]
        var_arr[i] = float(np.var(w, ddof=1)) if len(w) > 1 else 0.0
        ar1_arr[i] = _ar1(w)
    return var_arr, ar1_arr


def _classify(ar1: float, dvar: float, ar1_thresh: float) -> tuple[str, bool]:
    ar1_crit = ar1 >= ar1_thresh
    var_crit  = dvar > 0.0
    if ar1_crit and var_crit:
        return "CRITICAL", True
    if ar1_crit or var_crit:
        return "WARNING", False
    return "STABLE", False


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    phi: Optional[np.ndarray] = None,
    *,
    window: int = 20,
    step: int = 5,
    ar1_threshold: float = 0.85,
) -> FluctuationResult:
    """
    Detect critical fluctuations in the phi time series.

    Args:
        phi           : 1-D array of phi values (chronological).
        window        : width of each rolling statistics window.
        step          : stride between windows for the series output.
        ar1_threshold : AR(1) value above which CSD is flagged.
    """
    if phi is None:
        try:
            from runtime.state import phi_series
            phi = phi_series()
        except Exception:
            phi = None

    if phi is None or len(phi) < window + 2:
        return FluctuationResult()

    phi = np.asarray(phi, dtype=float)
    n = len(phi)

    # Full rolling stats (step=1 for last-window accuracy)
    var_full, ar1_full = _rolling_stats(phi, window)

    # Strided series for output (lighter)
    indices = list(range(0, len(var_full), step))
    var_series = [float(var_full[i]) for i in indices]
    ar1_series = [float(ar1_full[i]) for i in indices]

    current_var = float(var_full[-1])
    current_ar1 = float(ar1_full[-1])

    dvar_dt = float(var_full[-1] - var_full[-2]) if len(var_full) >= 2 else 0.0
    dar1_dt = float(ar1_full[-1] - ar1_full[-2]) if len(ar1_full) >= 2 else 0.0

    alert_level, is_critical = _classify(current_ar1, dvar_dt, ar1_threshold)

    return FluctuationResult(
        current_ar1=current_ar1,
        current_var=current_var,
        dvar_dt=dvar_dt,
        dar1_dt=dar1_dt,
        alert_level=alert_level,
        is_critical=bool(is_critical),
        n_samples=n,
        var_series=var_series,
        ar1_series=ar1_series,
    )
