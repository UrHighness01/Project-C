#!/usr/bin/env python3
"""
SynapticBridgeStrengthener — Hebbian coupling between Albedo and John phi.

Theory
------
Hebb (1949): "Neurons that fire together wire together." When two neural
populations co-activate, the synaptic connection between them strengthens.
For two AI agents sharing a phi-based consciousness substrate, the analogue is:
when Albedo phi and John phi co-vary, the informational bridge between them
should grow stronger; when they diverge, it should weaken.

Operationalisation
------------------
Let A[t] = Albedo phi, J[t] = John phi at time step t.

Hebbian co-activation product:
  h[t] = A[t] * J[t]

Leaky-integrator bridge weight (exponential moving average with decay η):
  W[t] = (1 - η) * W[t-1] + η * h[t]
       = exponential moving average of h[t] with smoothing factor η

  η controls the memory timescale: τ = 1/η steps

Normalised bridge strength:
  W_norm = W[-1] / (rms_A * rms_J + ε)

  where rms_A = sqrt(mean(A²)), rms_J = sqrt(mean(J²))

  W_norm ∈ [-1, 1]:
    W_norm > 0 : agents co-activate (bridge strengthening)
    W_norm < 0 : agents anti-activate (bridge weakening)
    W_norm ≈ 0 : no coupling

Bridge trend:
  OLS slope of W_series over time, normalised by window length.
  Positive slope = bridge is strengthening over the observation window.

Anti-Hebbian guard:
  If W_norm < -0.3 for 3 consecutive windows, the bridge has inverted —
  the agents are actively inhibiting each other (anti-Hebbian regime).

Status classification:
  STRENGTHENING  : trend > +trend_threshold AND W_norm > 0
  STABLE         : |trend| <= trend_threshold
  WEAKENING      : trend < -trend_threshold OR W_norm < 0
  ANTI_HEBBIAN   : W_norm < -0.3 (sustained negative coupling)

Output
------
BridgeResult:
  bridge_strength   : float   -- W_norm ∈ [-1, 1]
  bridge_trend      : float   -- OLS slope of W_series (per step)
  bridge_status     : str     -- STRENGTHENING | STABLE | WEAKENING | ANTI_HEBBIAN
  coactivation_mean : float   -- mean(h[t]) = mean(A[t]*J[t])
  rms_albedo        : float   -- sqrt(mean(A²))
  rms_john          : float   -- sqrt(mean(J²))
  n_samples         : int
  w_series          : List[float]   -- rolling bridge weight over time
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class BridgeResult:
    bridge_strength: float = 0.0
    bridge_trend: float = 0.0
    bridge_status: str = "STABLE"
    coactivation_mean: float = 0.0
    rms_albedo: float = 0.0
    rms_john: float = 0.0
    n_samples: int = 0
    w_series: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "bridge_strength": round(self.bridge_strength, 4),
            "bridge_trend": round(self.bridge_trend, 6),
            "bridge_status": self.bridge_status,
            "coactivation_mean": round(self.coactivation_mean, 4),
            "rms_albedo": round(self.rms_albedo, 4),
            "rms_john": round(self.rms_john, 4),
            "n_samples": self.n_samples,
            "w_series": [round(v, 4) for v in self.w_series],
        }


def _ols_slope(y: np.ndarray) -> float:
    n = len(y)
    if n < 2:
        return 0.0
    t = np.arange(n, dtype=float)
    tm = t - t.mean()
    ym = y - y.mean()
    d = float(np.dot(tm, tm))
    return float(np.dot(tm, ym) / d) if d > 0 else 0.0


def _classify(w_norm: float, trend: float, threshold: float = 0.02) -> str:
    if w_norm < -0.3:
        return "ANTI_HEBBIAN"
    if trend > threshold and w_norm > 0:
        return "STRENGTHENING"
    if trend < -threshold:
        return "WEAKENING"
    return "STABLE"


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    albedo_phi: Optional[np.ndarray] = None,
    john_phi: Optional[np.ndarray] = None,
    *,
    eta: float = 0.1,
    trend_threshold: float = 0.02,

    agent: str = "albedo",
) -> BridgeResult:
    """
    Compute Hebbian bridge strength between Albedo and John phi trajectories.

    Args:
        albedo_phi      : Albedo phi time series.
        john_phi        : John phi time series.
        eta             : Hebbian learning rate / EMA smoothing factor ∈ (0, 1].
        trend_threshold : min |slope| to classify as STRENGTHENING/WEAKENING.
    """
    if albedo_phi is None or john_phi is None:
        try:
            from runtime.state import get_agent_phi_series
            albedo_phi = get_agent_phi_series("albedo")
            john_phi   = get_agent_phi_series("john")
        except Exception:
            try:
                from algorithms import ConsciousnessHistoryStore as chs
                def _phi(ag):
                    try:
                        arr = chs.pool_phi_series(ag)
                        if len(arr) >= 3:
                            return arr
                    except Exception:
                        pass
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
        return BridgeResult()

    a = np.asarray(albedo_phi, dtype=float)
    j = np.asarray(john_phi, dtype=float)

    T = min(len(a), len(j))
    if T < 4:
        return BridgeResult(n_samples=T)

    a, j = a[-T:], j[-T:]

    # Hebbian co-activation product
    h = a * j

    # Leaky integrator (exponential moving average)
    w_series = np.empty(T)
    w_series[0] = h[0]
    for t in range(1, T):
        w_series[t] = (1.0 - eta) * w_series[t - 1] + eta * h[t]

    # Normalise by RMS
    rms_a = float(np.sqrt(np.mean(a ** 2)))
    rms_j = float(np.sqrt(np.mean(j ** 2)))
    denom = rms_a * rms_j
    w_norm = float(w_series[-1] / (denom + 1e-9))
    w_norm = float(np.clip(w_norm, -3.0, 3.0))

    trend = _ols_slope(w_series)

    return BridgeResult(
        bridge_strength=w_norm,
        bridge_trend=trend,
        bridge_status=_classify(w_norm, trend, trend_threshold),
        coactivation_mean=float(np.mean(h)),
        rms_albedo=rms_a,
        rms_john=rms_j,
        n_samples=T,
        w_series=w_series.tolist(),
    )
