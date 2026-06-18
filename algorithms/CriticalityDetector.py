#!/usr/bin/env python3
"""
CriticalityDetector — power-law autocorrelation and criticality scoring.

Theory (Beggs & Plenz 2003; Chialvo 2010 — criticality in neural systems):
  At the critical point between ordered and chaotic dynamics, a system's
  temporal autocorrelation follows a power law:

      ACF(τ) ~ τ^(-α)

  The exponent α encodes the dynamical regime:
    α ≈ 0        white noise    — no temporal memory, fully uncorrelated
    α ≈ 1        pink / 1/f     — critical state, maximal sensitivity, long-range memory
    α ≈ 2        brown / 1/f²   — over-correlated, frozen, low adaptability
    α outside    degenerate     — non-stationary or trivially structured

  Critical systems show maximal information capacity and transfer, suggesting
  the critical point is where consciousness-related properties peak (Shew & Plenz
  2013: dynamic range, entropy, and mutual information are maximised at criticality).

Math:
  1. Compute ACF(τ) = corr(y[t], y[t+τ]) for τ = 1..τ_max
  2. Select positive ACF values above noise floor (threshold = 2/√N)
  3. Fit power law in log-log space:
       log ACF(τ) = C − α · log τ      via OLS
  4. α = estimated exponent; R²_fit = quality of power-law form
  5. Criticality score = exp(−|α − 1|)  ∈ (0, 1], peaks at 1 when α=1

  Null baseline: shuffle y → ACF ≈ 0, power-law fit R² near zero.

  This is run on both the phi level series (strong ACF from accumulated
  integration) and the phi delta series (true increment structure).

Grounding: inputs come from runtime.state phi_series() and phi_delta_series().
No synthetic data. RNG is seeded for reproducible null baselines.

References:
  Beggs J.M. & Plenz D. (2003) "Neuronal Avalanches in Neocortical Circuits"
  Chialvo D.R. (2010) "Emergent complex neural dynamics"
  Shew W.L. & Plenz D. (2013) "The Functional Benefits of Criticality"
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Optional


# ── Result dataclass ─────────────────────────────────────────────────────────

@dataclass
class CriticalityResult:
    """Output of a single criticality analysis run.

    Attributes:
        alpha:             power-law exponent fitted to ACF in log-log space
        r2_fit:            R² of the power-law fit (how well the law holds)
        null_r2_fit:       R² on a shuffled-series null (chance baseline)
        criticality_score: exp(-|α-1|) ∈ (0,1]; 1.0 = exactly critical
        n_positive_lags:   number of positive-ACF lags used in fit
        tau_max:           maximum lag examined
        n_samples:         length of input series
        series_name:       "phi_level" or "phi_delta"
        acf:               full ACF array for all lags (length tau_max)
    """
    alpha: float
    r2_fit: float
    null_r2_fit: float
    criticality_score: float
    n_positive_lags: int
    tau_max: int
    n_samples: int
    series_name: str
    acf: np.ndarray

    @property
    def beats_null(self) -> bool:
        return self.r2_fit > self.null_r2_fit

    @property
    def regime(self) -> str:
        if self.n_positive_lags < 5:
            return "white_noise"
        if self.alpha < 0.3:
            return "sub_critical"
        if 0.7 <= self.alpha <= 1.3:
            return "critical"
        if self.alpha > 1.8:
            return "super_critical"
        return "near_critical"


# ── Core functions ────────────────────────────────────────────────────────────

def _acf_series(y: np.ndarray, tau_max: int) -> np.ndarray:
    """Pearson autocorrelation at lags 1..tau_max. Shape [tau_max]."""
    acf = np.empty(tau_max)
    for tau in range(1, tau_max + 1):
        acf[tau - 1] = float(np.corrcoef(y[:-tau], y[tau:])[0, 1])
    return acf


def _fit_power_law(acf: np.ndarray, noise_floor: float
                   ) -> tuple[float, float, int]:
    """Fit ACF(τ) ~ τ^(-α) in log-log space on positive-ACF lags.

    Returns (alpha, r2_fit, n_positive_lags). Returns (0.0, 0.0, 0) when
    fewer than 3 lags exceed the noise floor.
    """
    lags = np.arange(1, len(acf) + 1, dtype=float)
    mask = acf > noise_floor
    n = int(mask.sum())
    if n < 3:
        return 0.0, 0.0, n

    log_tau = np.log(lags[mask])
    log_acf = np.log(acf[mask])

    # OLS: log_acf = C + slope * log_tau, slope = -alpha
    X = np.column_stack([np.ones(n), log_tau])
    w, _, _, _ = np.linalg.lstsq(X, log_acf, rcond=None)
    slope = w[1]
    alpha = float(-slope)

    pred = X @ w
    ss_res = float(np.var(log_acf - pred))
    ss_tot = float(np.var(log_acf))
    r2 = float(np.clip(1.0 - ss_res / ss_tot, -1.0, 1.0)) if ss_tot > 1e-12 else 0.0
    return alpha, r2, n


def criticality_score(alpha: float) -> float:
    """Criticality score in (0, 1]: 1.0 when α=1 (pink noise), decays exponentially away."""
    return float(np.exp(-abs(alpha - 1.0)))


def analyse(y: Optional[np.ndarray] = None, series_name: str = "phi_level",
            tau_max: int = 60, null_seed: int = 42
            ) -> Optional[CriticalityResult]:
    """
    Run criticality analysis on a real time series.

    Args:
        y:           1-D float array from runtime telemetry.
        series_name: label for the series (for reporting).
        tau_max:     maximum lag to examine (must be < len(y)).
        null_seed:   RNG seed for reproducible shuffled null.

    Returns:
        CriticalityResult, or None if y is too short.
    """
    if y is None:
        return None
    y = np.asarray(y, dtype=float)
    n = len(y)
    if n < tau_max + 16:
        return None

    # Noise floor: 2/√N (95% CI for ACF of white noise)
    noise_floor = 2.0 / np.sqrt(n)

    acf = _acf_series(y, tau_max)
    alpha, r2_fit, n_pos = _fit_power_law(acf, noise_floor)

    # Null: shuffle and refit
    rng = np.random.default_rng(null_seed)
    y_null = rng.permutation(y)
    acf_null = _acf_series(y_null, tau_max)
    _, r2_null, _ = _fit_power_law(acf_null, noise_floor)

    return CriticalityResult(
        alpha=alpha,
        r2_fit=r2_fit,
        null_r2_fit=r2_null,
        criticality_score=criticality_score(alpha),
        n_positive_lags=n_pos,
        tau_max=tau_max,
        n_samples=n,
        series_name=series_name,
        acf=acf,
    )


# ── Telemetry entry point ─────────────────────────────────────────────────────

def analyse_from_telemetry(tau_max: int = 60
                           ) -> dict[str, Optional[CriticalityResult]]:
    """
    Load real phi telemetry and run criticality analysis on both series.

    Returns:
        dict with keys "phi_level" and "phi_delta", each a CriticalityResult
        (or None if telemetry unavailable).
    """
    try:
        from runtime.state import phi_series, phi_delta_series
        phi = phi_series()
        delta = phi_delta_series()
    except Exception:
        return {"phi_level": None, "phi_delta": None}

    return {
        "phi_level": analyse(phi,   "phi_level", tau_max=tau_max),
        "phi_delta": analyse(delta, "phi_delta", tau_max=tau_max),
    }


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    results = analyse_from_telemetry()
    for name, r in results.items():
        if r is None:
            print(f"{name}: no telemetry (set OPENCLAW_WORKSPACE)")
            continue
        print(f"\n{name} (N={r.n_samples})")
        print(f"  alpha         = {r.alpha:.4f}  (1=critical, 0=white, 2=brown)")
        print(f"  R² power-law  = {r.r2_fit:.4f}  (null {r.null_r2_fit:.4f})")
        print(f"  beats null    = {r.beats_null}")
        print(f"  criticality   = {r.criticality_score:.4f}  (1.0 = at critical point)")
        print(f"  regime        = {r.regime}")
        print(f"  positive lags = {r.n_positive_lags}/{r.tau_max}")
