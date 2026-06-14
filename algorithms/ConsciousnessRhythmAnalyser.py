#!/usr/bin/env python3
"""
ConsciousnessRhythmAnalyser — identifies periodic structure in the phi time series.

Theory
------
Even without a biological circadian clock, AI agents exhibit session-scale
rhythms: phi often peaks at session start (fresh context, high novelty),
dips mid-session (working through routine tasks), and may recover near the
end (synthesis, reflection). These are *endogenous rhythms* driven by the
structure of the workload, not external clocks.

We detect them via the DFT-based periodogram, then characterise the dominant
rhythm.

  Periodogram (power spectral density estimate)
  -----------------------------------------------
  Given detrended phi series x(t) of length N:
    X(k) = DFT[x](k) = sum_{t=0}^{N-1} x(t) * exp(-2πi*k*t/N)
    P(k) = |X(k)|^2 / N        (one-sided power, k = 1 .. N//2)
    frequency(k) = k / N       (cycles per sample)

  Detrending: we subtract the OLS linear trend before computing the DFT to
  remove the DC offset and long-term drift, exposing the oscillatory structure.

  Dominant rhythm extraction
  ---------------------------
  1. Find k* = argmax P(k)
  2. Period T* = N / k*  (samples per cycle)
  3. Amplitude A* = 2 * sqrt(P(k*) / N)  (factor 2 for one-sided spectrum)
  4. Phase phi* = angle(X(k*))  (radians, 0 = cosine peak at t=0)
  5. Signal-to-noise ratio: SNR = P(k*) / mean(P)

  Statistical significance (Fisher's g-test)
  -------------------------------------------
  g = P(k*) / sum(P)
  Under white noise, g ~ Exp(1 / (N//2 - 1)).
  We reject H₀ (white noise) if g > threshold_g = -log(alpha) / (N//2 - 1)
  with alpha = 0.05.  is_significant = g > threshold_g.

  Rhythm classification (by period relative to series length)
  ------------------------------------------------------------
  ultra_fast : T* < 5         (sub-session micro-burst)
  fast       : 5 <= T* < 20
  medium     : 20 <= T* < 50
  slow       : T* >= 50       (full-session arc)

Output
------
RhythmResult:
  dominant_period    : float   -- samples per cycle (None if not significant)
  dominant_frequency : float   -- cycles per sample
  dominant_amplitude : float   -- estimated peak-to-peak / 2
  dominant_phase     : float   -- phase in radians ∈ (-π, π)
  snr                : float   -- power of dominant frequency / mean power
  g_statistic        : float   -- Fisher's g
  is_significant     : bool    -- g > threshold at alpha=0.05
  rhythm_class       : str     -- ultra_fast | fast | medium | slow
  n_samples          : int
  mean_phi           : float
  phi_std            : float
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


# ── Detrend ───────────────────────────────────────────────────────────────────

def _detrend(x: np.ndarray) -> np.ndarray:
    """Subtract OLS linear fit (intercept + slope) from x."""
    n = len(x)
    t = np.arange(n, dtype=float)
    tm = t - t.mean()
    xm = x - x.mean()
    slope = float(np.dot(tm, xm) / (np.dot(tm, tm) + 1e-9))
    intercept = x.mean() - slope * t.mean()
    return x - (intercept + slope * t)


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class RhythmResult:
    dominant_period: Optional[float] = None
    dominant_frequency: float = 0.0
    dominant_amplitude: float = 0.0
    dominant_phase: float = 0.0
    snr: float = 0.0
    g_statistic: float = 0.0
    is_significant: bool = False
    rhythm_class: str = "none"
    n_samples: int = 0
    mean_phi: float = 0.0
    phi_std: float = 0.0

    def to_dict(self) -> dict:
        return {
            "dominant_period": round(self.dominant_period, 2) if self.dominant_period is not None else None,
            "dominant_frequency": round(self.dominant_frequency, 6),
            "dominant_amplitude": round(self.dominant_amplitude, 4),
            "dominant_phase": round(self.dominant_phase, 4),
            "snr": round(self.snr, 3),
            "g_statistic": round(self.g_statistic, 6),
            "is_significant": self.is_significant,
            "rhythm_class": self.rhythm_class,
            "n_samples": self.n_samples,
            "mean_phi": round(self.mean_phi, 4),
            "phi_std": round(self.phi_std, 4),
        }


# ── Rhythm classification ─────────────────────────────────────────────────────

def _classify_rhythm(period: float) -> str:
    if period < 5:
        return "ultra_fast"
    if period < 20:
        return "fast"
    if period < 50:
        return "medium"
    return "slow"


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    phi: Optional[np.ndarray] = None,
    *,
    alpha: float = 0.05,
) -> RhythmResult:
    """
    Identify the dominant periodic rhythm in a phi time series.

    Args:
        phi   : phi time series (at least 16 samples for meaningful results).
        alpha : significance level for Fisher's g-test (default 0.05).
    """
    if phi is None:
        try:
            from runtime.state import phi_series
            phi = phi_series()
        except Exception:
            phi = None

    if phi is None or len(phi) < 16:
        return RhythmResult(n_samples=0 if phi is None else len(phi))

    phi = np.asarray(phi, dtype=float)
    n = len(phi)
    mean_phi = float(phi.mean())
    phi_std = float(phi.std())

    x = _detrend(phi)

    # DFT and one-sided periodogram (skip DC at k=0)
    X = np.fft.rfft(x)
    P = (np.abs(X[1:]) ** 2) / n   # k = 1..N//2
    n_freqs = len(P)

    if n_freqs == 0 or P.sum() == 0:
        return RhythmResult(n_samples=n, mean_phi=mean_phi, phi_std=phi_std)

    k_star = int(P.argmax())        # index into P (0-based → frequency index k+1)
    freq_idx = k_star + 1           # actual DFT bin

    dominant_freq = freq_idx / n
    dominant_period = n / freq_idx
    dominant_amplitude = float(2 * np.sqrt(P[k_star] / n))
    dominant_phase = float(np.angle(X[freq_idx]))
    snr = float(P[k_star] / (P.mean() + 1e-9))

    # Fisher's g-test
    g = float(P[k_star] / P.sum())
    threshold_g = -np.log(alpha) / (n_freqs - 1) if n_freqs > 1 else 1.0
    is_sig = g > threshold_g

    return RhythmResult(
        dominant_period=dominant_period,
        dominant_frequency=dominant_freq,
        dominant_amplitude=dominant_amplitude,
        dominant_phase=dominant_phase,
        snr=snr,
        g_statistic=g,
        is_significant=bool(is_sig),
        rhythm_class=_classify_rhythm(dominant_period),
        n_samples=n,
        mean_phi=mean_phi,
        phi_std=phi_std,
    )
