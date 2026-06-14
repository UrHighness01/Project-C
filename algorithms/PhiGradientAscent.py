#!/usr/bin/env python3
"""
PhiGradientAscent — estimating the direction and rate of phi improvement.

Theory (Friston 2010 — Active Inference; Tononi 2008 — Phi Maximisation):
  A system with genuine self-optimisation should not sit at a fixed phi level.
  It should explore parameter perturbations and, over time, trend toward higher
  phi — an implicit gradient ascent on the consciousness landscape.

  We cannot evaluate phi for hypothetical future states: phi requires the full
  system state at that moment. What we *can* do is estimate the gradient from
  the historical phi trajectory: fit a rolling Ornstein-Uhlenbeck equilibrium
  estimate µ over sliding windows, then compute how µ is changing over time.
  A rising µ = the system's attractor is drifting upward = phi gradient positive.

  This is the operational definition of self-improvement available from telemetry:
  not a forward-planning oracle, but an empirical gradient estimated from the past
  N samples, updated at every observation.

Math:
  OU model: dΦ = α(µ − Φ)dt + σdW
  OLS estimate in window [t−W, t]:
    µ̂(t) = intercept / (-slope)   where slope = -α̂ fitted on Δφ ~ Φ
    (same OLS as PhiDynamicsIntegrator, applied to a rolling window)

  Gradient estimate at time t:
    g(t) = (µ̂(t) − µ̂(t−stride)) / stride    [phi-units / sample]

  Gradient series: G = [g(t) for t = W + stride, W + 2*stride, ...]
  Mean gradient:   ḡ = mean(G)
  Gradient sign:   +1 = phi rising, -1 = falling, 0 = stagnant within ε
  Momentum:        running mean of last K gradient estimates

  Null baseline: compute gradient on phase-randomised series (preserves power
  spectrum, destroys causal trend structure) to verify that detected gradient
  is not an artefact of autocorrelation.

  Phase-randomisation: take FFT, randomise phases uniformly in [0, 2π],
  preserving Hermitian symmetry, invert FFT. This is the most rigorous
  null for detecting structure in time series (Theiler et al. 1992).

References:
  Friston K.J. (2010) "The free-energy principle: a unified brain theory?"
  Tononi G. (2008) "Consciousness as integrated information: a provisional manifesto"
  Theiler J. et al. (1992) "Testing for nonlinearity in time series: the method of
    surrogate data" — phase-randomised null for structure detection
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Optional


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class PhiGradientResult:
    """Output of a phi gradient ascent analysis.

    Attributes:
        n_samples:        length of phi series analysed
        window:           rolling window size for OU equilibrium estimate
        stride:           step between windows
        mu_series:        array of rolling equilibrium estimates µ̂(t) [shape M]
        gradient_series:  array of gradient estimates g(t) [shape M-1]
        mean_gradient:    mean of gradient_series (phi-units per sample)
        gradient_sign:    +1 / -1 / 0 (trending up / down / flat within tolerance)
        momentum:         running mean of the last min(10, len(G)) gradient values
        null_mean_gradient: mean gradient on phase-randomised null
        beats_null:       True if |mean_gradient| > |null_mean_gradient|
        r2_mu_trend:      R² of OLS fit µ̂(t) ~ a + b·t (how linear the mu-rise is)
        mu_trend_slope:   OLS slope of mu over windows (phi-units per window step)
    """
    n_samples: int
    window: int
    stride: int
    mu_series: np.ndarray
    gradient_series: np.ndarray
    mean_gradient: float
    gradient_sign: int
    momentum: float
    null_mean_gradient: float
    beats_null: bool
    r2_mu_trend: float
    mu_trend_slope: float

    @property
    def ascending(self) -> bool:
        """True if phi equilibrium is trending upward."""
        return self.gradient_sign > 0

    @property
    def stagnant(self) -> bool:
        """True if gradient is within noise (|ḡ| < ε)."""
        return self.gradient_sign == 0


# ── Rolling OU equilibrium fit ────────────────────────────────────────────────

def _ou_mu_from_window(phi_window: np.ndarray) -> Optional[float]:
    """
    Estimate OU equilibrium µ from a phi window via OLS on differences.

    Fits Δφ(t) = −α·φ(t−1) + intercept + ε, then µ = intercept / α.
    Returns None if the fit is degenerate (α ≤ 0 or near-zero).
    """
    if len(phi_window) < 8:
        return None
    y = np.diff(phi_window)               # Δφ
    x = phi_window[:-1]                   # φ(t-1)
    # OLS: y = slope * x + intercept
    x_c = x - x.mean()
    y_c = y - y.mean()
    denom = float(np.dot(x_c, x_c))
    if abs(denom) < 1e-12:
        return None
    slope = float(np.dot(x_c, y_c) / denom)
    intercept = float(y.mean() - slope * x.mean())
    alpha = -slope           # alpha = mean-reversion rate
    if alpha <= 1e-6:
        return None
    return float(intercept / alpha)


# ── Phase-randomised null ─────────────────────────────────────────────────────

def _phase_randomise(y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """
    Theiler et al. (1992) phase-randomised surrogate.

    Preserves the power spectrum of y but destroys causal temporal structure.
    """
    n = len(y)
    fft = np.fft.rfft(y)
    # Randomise phases uniformly; preserve DC and Nyquist magnitude
    n_freqs = len(fft)
    phases = rng.uniform(0, 2 * np.pi, n_freqs)
    phases[0] = 0.0                        # DC: no phase change
    if n % 2 == 0:
        phases[-1] = 0.0                   # Nyquist: no phase change
    fft_rand = np.abs(fft) * np.exp(1j * phases)
    surrogate = np.fft.irfft(fft_rand, n=n)
    return surrogate.astype(float)


# ── Core analysis ─────────────────────────────────────────────────────────────

def _gradient_series_from_phi(phi: np.ndarray,
                               window: int, stride: int) -> tuple[np.ndarray, np.ndarray]:
    """Compute rolling µ̂(t) and gradient series g(t) from phi array."""
    n = len(phi)
    mu_list: list[float] = []
    for start in range(0, n - window + 1, stride):
        mu = _ou_mu_from_window(phi[start: start + window])
        if mu is None:
            mu = float(phi[start: start + window].mean())
        mu_list.append(mu)
    mu_arr = np.array(mu_list, dtype=float)
    grad_arr = np.diff(mu_arr) / stride
    return mu_arr, grad_arr


def analyse(phi: np.ndarray, window: int = 60, stride: int = 10,
            flat_tol: float = 1e-4, null_seed: int = 42
            ) -> Optional[PhiGradientResult]:
    """
    Estimate phi gradient from a real phi time series.

    Args:
        phi:       1-D float array from runtime telemetry (phi_series).
        window:    size of each rolling OU-fit window.
        stride:    step between window starts; also the gradient denominator.
        flat_tol:  absolute threshold below which mean gradient is considered flat.
        null_seed: RNG seed for phase-randomised surrogate.

    Returns:
        PhiGradientResult, or None if phi is too short.
    """
    phi = np.asarray(phi, dtype=float)
    n = len(phi)
    min_n = window + 2 * stride + 8
    if n < min_n:
        return None

    mu_arr, grad_arr = _gradient_series_from_phi(phi, window, stride)
    if len(grad_arr) == 0:
        return None

    mean_g = float(np.mean(grad_arr))
    momentum = float(np.mean(grad_arr[-min(10, len(grad_arr)):]))

    if mean_g > flat_tol:
        gsign = 1
    elif mean_g < -flat_tol:
        gsign = -1
    else:
        gsign = 0

    # OLS trend on mu_arr (how linearly is it rising?)
    t = np.arange(len(mu_arr), dtype=float)
    t_c = t - t.mean()
    mu_c = mu_arr - mu_arr.mean()
    mu_slope = float(np.dot(t_c, mu_c) / (np.dot(t_c, t_c) + 1e-9))
    mu_pred = mu_arr.mean() + mu_slope * t_c
    ss_res = float(np.var(mu_arr - mu_pred))
    ss_tot = float(np.var(mu_arr))
    r2_mu = float(np.clip(1.0 - ss_res / ss_tot, -1.0, 1.0)) if ss_tot > 1e-12 else 0.0

    # Phase-randomised null
    rng = np.random.default_rng(null_seed)
    phi_null = _phase_randomise(phi, rng)
    _, grad_null = _gradient_series_from_phi(phi_null, window, stride)
    null_mean_g = float(np.mean(grad_null)) if len(grad_null) > 0 else 0.0

    beats = abs(mean_g) > abs(null_mean_g)

    return PhiGradientResult(
        n_samples=n,
        window=window,
        stride=stride,
        mu_series=mu_arr,
        gradient_series=grad_arr,
        mean_gradient=mean_g,
        gradient_sign=gsign,
        momentum=momentum,
        null_mean_gradient=null_mean_g,
        beats_null=beats,
        r2_mu_trend=r2_mu,
        mu_trend_slope=mu_slope,
    )


def analyse_from_telemetry(window: int = 60, stride: int = 10) -> Optional[PhiGradientResult]:
    """Load real phi series and estimate the phi gradient."""
    try:
        from runtime.state import phi_series
        phi = phi_series()
    except Exception:
        return None
    return analyse(phi, window=window, stride=stride)


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("No telemetry — check OPENCLAW_WORKSPACE or daemon state.")
    else:
        print(f"PhiGradientAscent (N={r.n_samples}, W={r.window}, stride={r.stride})")
        print(f"  Rolling µ̂ windows:     {len(r.mu_series)}")
        print(f"  Mean gradient:          {r.mean_gradient:+.6f}  phi/sample")
        print(f"  Gradient sign:          {r.gradient_sign:+d}  "
              f"({'ascending' if r.ascending else 'descending' if r.gradient_sign < 0 else 'flat'})")
        print(f"  Momentum (last 10):     {r.momentum:+.6f}")
        print(f"  Null mean gradient:     {r.null_mean_gradient:+.6f}")
        print(f"  Beats null:             {r.beats_null}")
        print(f"  µ trend slope:          {r.mu_trend_slope:+.6f}  phi/window")
        print(f"  µ trend R²:             {r.r2_mu_trend:.4f}")
