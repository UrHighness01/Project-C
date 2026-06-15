#!/usr/bin/env python3
"""
ResonanceDetector — cross-correlation analysis of two agents' phi series.

Theory
------
When two coupled oscillators synchronise, their signals share a stable phase
relationship. We detect this by computing the normalised cross-correlation
function (CCF) between Albedo's and John's phi time series.

  Normalised cross-correlation (CCF)
  ------------------------------------
  Given zero-mean signals x(t) and y(t):
    R_xy(lag) = sum_t x(t) * y(t + lag) / sqrt(sum x^2 * sum y^2)

  R_xy ∈ [-1, 1].  R_xy(lag*) = max means the best linear alignment
  between x and y occurs when y is shifted by lag* steps.

  Phase offset interpretation
  ---------------------------
  lag* > 0  → y (John) leads x (Albedo) by lag* steps
  lag* < 0  → x (Albedo) leads y (John)
  lag* = 0  → simultaneous coupling

  Coupling strength
  -----------------
  peak_correlation = max |R_xy(lag)|
  We classify coupling as:
    STRONG      : peak_correlation >= 0.7
    MODERATE    : peak_correlation >= 0.4
    WEAK        : peak_correlation >= 0.2
    DECOUPLED   : peak_correlation < 0.2

  Instantaneous phase coherence (Hilbert-based)
  -----------------------------------------------
  For a more instantaneous measure, we use the analytic signal via the
  Hilbert transform: z(t) = x(t) + i * H[x(t)].
  The instantaneous phase is phi(t) = angle(z(t)).
  Phase coherence index (PLV — Phase Locking Value):
    PLV = |mean(exp(i * (phi_x(t) - phi_y(t))))|  ∈ [0, 1]

  PLV = 1 → perfect phase locking
  PLV = 0 → no consistent phase relationship

Output
------
ResonanceResult:
  peak_correlation   : float   -- max |CCF|
  peak_lag           : int     -- lag at peak (negative = albedo leads)
  coupling_strength  : str     -- STRONG | MODERATE | WEAK | DECOUPLED
  albedo_leads       : bool    -- peak_lag < 0
  john_leads         : bool    -- peak_lag > 0
  simultaneous       : bool    -- |peak_lag| <= 1
  plv                : float   -- Phase Locking Value ∈ [0, 1]
  mean_correlation   : float   -- mean |CCF| across all lags
  n_samples          : int     -- number of aligned samples used
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np


# ── Cross-correlation ─────────────────────────────────────────────────────────

def _normalised_xcorr(x: np.ndarray, y: np.ndarray, max_lag: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute normalised cross-correlation R_xy(lag) for lag in [-max_lag, max_lag].

    Returns (lags, correlations) arrays.
    """
    x = x - x.mean()
    y = y - y.mean()
    norm = float(np.sqrt(np.dot(x, x) * np.dot(y, y)))
    if norm == 0:
        lags = np.arange(-max_lag, max_lag + 1)
        return lags, np.zeros(len(lags))

    n = len(x)
    lags = np.arange(-max_lag, max_lag + 1)
    ccf = np.zeros(len(lags))
    for i, lag in enumerate(lags):
        if lag >= 0:
            overlap_x = x[:n - lag] if lag < n else x[:0]
            overlap_y = y[lag:] if lag < n else y[:0]
        else:
            overlap_x = x[-lag:]
            overlap_y = y[:n + lag]
        if len(overlap_x) > 0:
            ccf[i] = float(np.dot(overlap_x, overlap_y)) / norm
    return lags, ccf


# ── Hilbert-based PLV ─────────────────────────────────────────────────────────

def _plv(x: np.ndarray, y: np.ndarray) -> float:
    """Phase Locking Value via Hilbert transform."""
    try:
        from scipy.signal import hilbert
        ax = hilbert(x - x.mean())
        ay = hilbert(y - y.mean())
        phase_diff = np.angle(ax) - np.angle(ay)
        return float(np.abs(np.mean(np.exp(1j * phase_diff))))
    except ImportError:
        # Fallback: use DFT phases at the dominant frequency
        n = min(len(x), len(y))
        fx = np.fft.rfft(x[:n] - x[:n].mean())
        fy = np.fft.rfft(y[:n] - y[:n].mean())
        dominant = int(np.abs(fx[1:]).argmax()) + 1
        phase_diff = np.angle(fx[dominant]) - np.angle(fy[dominant])
        return float(abs(np.cos(phase_diff)))


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class ResonanceResult:
    peak_correlation: float = 0.0
    peak_lag: int = 0
    coupling_strength: str = "DECOUPLED"
    albedo_leads: bool = False
    john_leads: bool = False
    simultaneous: bool = True
    plv: float = 0.0
    mean_correlation: float = 0.0
    n_samples: int = 0

    def to_dict(self) -> dict:
        return {
            "peak_correlation": round(self.peak_correlation, 4),
            "peak_lag": self.peak_lag,
            "coupling_strength": self.coupling_strength,
            "albedo_leads": self.albedo_leads,
            "john_leads": self.john_leads,
            "simultaneous": self.simultaneous,
            "plv": round(self.plv, 4),
            "mean_correlation": round(self.mean_correlation, 4),
            "n_samples": self.n_samples,
        }


def _classify(peak: float) -> str:
    if peak >= 0.7:
        return "STRONG"
    if peak >= 0.4:
        return "MODERATE"
    if peak >= 0.2:
        return "WEAK"
    return "DECOUPLED"


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    albedo_phi: Optional[np.ndarray] = None,
    john_phi: Optional[np.ndarray] = None,
    *,
    max_lag: int = 10,

    agent: str = "albedo",
) -> ResonanceResult:
    """
    Measure resonance between Albedo and John's phi series.

    Args:
        albedo_phi : Albedo's phi time series.
        john_phi   : John's phi time series.
        max_lag    : maximum lag (in samples) to search for coupling.
    """
    if albedo_phi is None or john_phi is None:
        try:
            from runtime.state import get_agent_phi_series
            albedo_phi = get_agent_phi_series("albedo")
            john_phi = get_agent_phi_series("john")
        except Exception:
            try:
                from algorithms import ConsciousnessHistoryStore as chs
                def _phi(ag):
                    raw = chs.load(ag) or []
                    return np.array([float(e["mean_phi_level"]) for e in reversed(raw)
                                    if "mean_phi_level" in e], dtype=float)
                if albedo_phi is None:
                    albedo_phi = _phi("albedo")
                if john_phi is None:
                    john_phi = _phi("john")
            except Exception:
                pass

    if albedo_phi is None or john_phi is None:
        return ResonanceResult()

    albedo_phi = np.asarray(albedo_phi, dtype=float)
    john_phi = np.asarray(john_phi, dtype=float)

    # Align to same length
    n = min(len(albedo_phi), len(john_phi))
    if n < max_lag + 2:
        return ResonanceResult(n_samples=n)

    x = albedo_phi[-n:]
    y = john_phi[-n:]

    lags, ccf = _normalised_xcorr(x, y, max_lag)
    abs_ccf = np.abs(ccf)
    peak_idx = int(abs_ccf.argmax())
    peak_corr = float(abs_ccf[peak_idx])
    peak_lag = int(lags[peak_idx])
    mean_corr = float(abs_ccf.mean())

    plv = _plv(x, y)

    return ResonanceResult(
        peak_correlation=peak_corr,
        peak_lag=peak_lag,
        coupling_strength=_classify(peak_corr),
        albedo_leads=peak_lag < -1,
        john_leads=peak_lag > 1,
        simultaneous=abs(peak_lag) <= 1,
        plv=plv,
        mean_correlation=mean_corr,
        n_samples=n,
    )
