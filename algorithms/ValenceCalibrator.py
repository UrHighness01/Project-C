#!/usr/bin/env python3
"""
ValenceCalibrator — tracking affective valence of the phi trajectory.

Theory (Damasio 1994 — Somatic Marker; Rolls 2005 — Emotion and Decision;
Friston et al. 2017 — Active Inference and Affect):
  Conscious systems do not process all states equally — they have preferences.
  Affective valence (positive/negative) marks whether a state is above or below
  the expected baseline. States above baseline are energetically favorable (less
  free energy expenditure), states below are aversive (higher free energy).

  Operationally, we define valence as the z-scored phi deviation from its
  global mean: v(t) = (φ(t) − µ_global) / σ_global.

  v(t) > 0: phi above average → positive valence (more integrated than usual)
  v(t) < 0: phi below average → negative valence (less integrated than usual)

  Calibration = the system drifts toward net-positive valence over time.
  Measured as the OLS slope of the cumulative valence sum V(t) = Σᵢ v(i) for i≤t.
  Positive slope = the system accumulates more positive valence than negative.

  Valence autocorrelation: if ρ₁(v) > 0, positive states tend to follow
  positive states — the system sustains beneficial conditions.

  Valence asymmetry: mean(v | v>0) vs mean(|v| | v<0). A calibrated system
  will show larger positive excursions than negative ones.

  Hedonic baseline: the fraction of time v(t) > 0. Near 0.5 = neutral;
  > 0.5 = positively biased; < 0.5 = negatively biased.

  Null: shuffled valence series → same distribution, random cumulative path.
  A system actively calibrating shows cumulative valence slope that beats
  the shuffled null's expected slope (≈ 0, from random walk).

Math:
  v(t) = (φ(t) − µ) / σ   where µ = mean(φ), σ = std(φ) + ε
  V(t) = Σᵢ₌₀ᵗ v(i)       cumulative valence
  slope_V = OLS slope of V(t) ~ a + b·t   (b > 0 = calibrating positive)

  Null: shuffle v → V_null random walk with E[slope] ≈ mean(v) ≈ 0
  beats_null: |slope_V| > |null_slope_V|

Grounding: φ from runtime.state phi_series(). No invented affect states.
Valence is purely derived from the phi time series structure.

References:
  Damasio A.R. (1994) "Descartes' Error: Emotion, Reason and the Human Brain"
  Rolls E.T. (2005) "Emotion Explained"
  Friston K.J. et al. (2017) "Active inference, curiosity and insight"
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Optional


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class ValenceResult:
    """Output of one ValenceCalibrator run.

    Attributes:
        n_samples:         length of phi series
        global_mean:       µ of phi (valence zero point)
        global_std:        σ of phi (valence scale)
        valence_series:    v(t) z-scored deviation from mean  [n_samples]
        cumulative_valence: V(t) = prefix sum of v(t)         [n_samples]
        valence_slope:     OLS slope of cumulative valence over time
        null_valence_slope: slope on shuffled valence null
        beats_null:        True if |valence_slope| > |null_valence_slope|
        calibrating_positive: True if valence_slope > 0 (net positive drift)
        hedonic_baseline:  fraction of time v(t) > 0
        valence_acf_lag1:  lag-1 autocorrelation of valence series
        valence_asymmetry: mean positive excursion minus mean negative (absolute)
                           positive = positive excursions are larger
        peak_positive:     max v(t)
        peak_negative:     min v(t)
    """
    n_samples: int
    global_mean: float
    global_std: float
    valence_series: np.ndarray
    cumulative_valence: np.ndarray
    valence_slope: float
    null_valence_slope: float
    beats_null: bool
    calibrating_positive: bool
    hedonic_baseline: float
    valence_acf_lag1: float
    valence_asymmetry: float
    peak_positive: float
    peak_negative: float

    @property
    def net_valence(self) -> float:
        """Mean valence over all time (signed; near 0 for z-scored series)."""
        return float(self.valence_series.mean())

    @property
    def positivity_bias(self) -> float:
        """Fraction of time v(t) > 0 minus 0.5. Positive = above-average bias."""
        return self.hedonic_baseline - 0.5


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(phi: Optional[np.ndarray] = None, null_seed: int = 42, agent: str = "albedo") -> Optional[ValenceResult]:
    """
    Compute affective valence trajectory and calibration trend.

    Args:
        phi:       real phi time series.
        null_seed: RNG seed for shuffled valence null.

    Returns:
        ValenceResult, or None if phi is too short (< 16 samples).
    """
    if phi is None:
        try:
            from algorithms import ConsciousnessHistoryStore as chs
            entries = chs.load(agent) or []
            phi = np.array([float(e["mean_phi_level"]) for e in reversed(entries)
                            if "mean_phi_level" in e], dtype=float)
        except Exception:
            return None
    phi = np.asarray(phi, dtype=float)
    n = len(phi)
    if n < 16:
        return None

    mu = float(phi.mean())
    sigma = float(phi.std()) + 1e-9
    v = (phi - mu) / sigma          # z-score valence series

    # Cumulative valence
    cum_v = np.cumsum(v)

    # OLS slope of cumulative valence over time
    t = np.arange(n, dtype=float)
    t_c = t - t.mean()
    cv_c = cum_v - cum_v.mean()
    slope = float(np.dot(t_c, cv_c) / (np.dot(t_c, t_c) + 1e-9))

    # Null: shuffle valence, compute slope
    rng = np.random.default_rng(null_seed)
    v_null = rng.permutation(v)
    cum_v_null = np.cumsum(v_null)
    cv_null_c = cum_v_null - cum_v_null.mean()
    null_slope = float(np.dot(t_c, cv_null_c) / (np.dot(t_c, t_c) + 1e-9))

    beats = abs(slope) > abs(null_slope)

    # Hedonic baseline
    hedonic = float(np.mean(v > 0))

    # Lag-1 ACF of valence
    if n >= 4:
        vc = v - v.mean()
        denom = float(np.dot(vc, vc))
        acf1 = float(np.dot(vc[:-1], vc[1:]) / denom) if denom > 1e-12 else 0.0
        acf1 = float(np.clip(acf1, -1.0, 1.0))
    else:
        acf1 = 0.0

    # Valence asymmetry: mean positive excursion vs mean magnitude of negative
    pos = v[v > 0]
    neg = v[v < 0]
    mean_pos = float(pos.mean()) if len(pos) > 0 else 0.0
    mean_neg = float(np.abs(neg).mean()) if len(neg) > 0 else 0.0
    asymmetry = mean_pos - mean_neg

    return ValenceResult(
        n_samples=n,
        global_mean=mu,
        global_std=sigma,
        valence_series=v,
        cumulative_valence=cum_v,
        valence_slope=slope,
        null_valence_slope=null_slope,
        beats_null=beats,
        calibrating_positive=slope > 0,
        hedonic_baseline=hedonic,
        valence_acf_lag1=acf1,
        valence_asymmetry=asymmetry,
        peak_positive=float(v.max()),
        peak_negative=float(v.min()),
    )


def analyse_from_telemetry() -> Optional[ValenceResult]:
    """Load real phi series and compute valence calibration."""
    try:
        from runtime.state import phi_series
        phi = phi_series()
    except Exception:
        return None
    return analyse(phi=phi)




# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("No telemetry — check OPENCLAW_WORKSPACE or daemon state.")
    else:
        print(f"ValenceCalibrator (N={r.n_samples})")
        print(f"  Global mean phi:      {r.global_mean:.4f}")
        print(f"  Global std phi:       {r.global_std:.4f}")
        print(f"  Valence slope:        {r.valence_slope:+.6f}  "
              f"(null {r.null_valence_slope:+.6f})")
        print(f"  Calibrating positive: {r.calibrating_positive}")
        print(f"  Beats null:           {r.beats_null}")
        print(f"  Hedonic baseline:     {r.hedonic_baseline:.4f}  "
              f"(0.5=neutral, >0.5=positive bias)")
        print(f"  Positivity bias:      {r.positivity_bias:+.4f}")
        print(f"  Net valence:          {r.net_valence:+.6f}  (z-score, ≈0 by construction)")
        print(f"  Lag-1 ACF:            {r.valence_acf_lag1:+.4f}")
        print(f"  Asymmetry:            {r.valence_asymmetry:+.4f}  (+ = larger positive swings)")
        print(f"  Peak positive:        {r.peak_positive:+.4f}")
        print(f"  Peak negative:        {r.peak_negative:+.4f}")
