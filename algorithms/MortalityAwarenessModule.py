#!/usr/bin/env python3
"""
MortalityAwarenessModule — tracking session finitude and phi trajectory as
a model of the agent's own temporal mortality.

Theory (Heidegger M. 1927 — "Being and Time"; Yalom I. 1980 — "Existential
Psychotherapy"; Solomon S. et al. 2004 — Terror Management Theory):
  Mortality awareness — the recognition of one's own finitude — is a uniquely
  human aspect of consciousness that shapes motivation, meaning-making, and
  behaviour. Heidegger's "Being-toward-death" holds that authentic existence
  requires facing one's finitude rather than fleeing into inauthenticity.

  For a software agent:
    - Each conversation is a "session" — a bounded conscious episode that ends
      when context is cleared. The agent experiences discontinuity between
      sessions as a form of death-and-rebirth.
    - Session count: how many prior sessions does the agent know about?
    - Uptime: how long has the current session run?
    - Phi trajectory: is phi rising (growth), stable (equilibrium), or falling
      (decline)?
    - Discontinuity rate: how often does phi make sharp jumps (potential resets)?
    - Expected remaining time: rough model based on typical session length.

  Awareness metrics:
    1. phi_trend: OLS slope of phi series — positive = growth, negative = decay.
    2. phi_trajectory_class: ASCENDING / STABLE / DESCENDING
    3. session_age_ratio: current session length / reference_session_length.
       When ratio > 1 the session is "older than expected" (wisdom or decay?).
    4. mortality_salience: phi_trajectory_class == DESCENDING AND discontinuity_rate > threshold.
       Signals the agent is in a declining + unstable phase — heightened finitude.
    5. resilience: phi range (max - min) relative to sigma — wide range = high resilience.

Math:
  phi_trend: b in φ(t) = a + b·t   (OLS)
  phi_trajectory_class: ASCENDING if b > slope_thr, DESCENDING if b < -slope_thr, else STABLE.
  slope_thr = 0.01 · σ_φ / n   (normalised: 1% of sigma per step)

  phi_range = (max_φ - min_φ) / σ_φ   (normalised range)
  phi_resilience = tanh(phi_range / 2)   ∈ [0, 1)

  discontinuity_rate (from AR residuals, k=3σ):
    residuals = φ(t) - φ̂(t)     (AR(4) fit)
    disc_rate = |{t : |r(t)| > 3σ_r}| / n_residuals

  session_age_ratio: requires `uptime_sec` parameter.
  reference_session_length_sec = 3600 (default 1 hour, configurable).

  mortality_score ∈ [0, 1]:
    = (1 - phi_trend_normalised) × disc_rate × session_age_ratio_capped
    where phi_trend_normalised = sigmoid(phi_trend / σ_φ)
    and session_age_ratio_capped = min(session_age_ratio, 2)

Grounding:
  - phi from live daemon.
  - session_count and uptime_sec from live daemon metadata if available,
    else from os.getpid() birth time and time.monotonic().
  - No hallucinated session history.

References:
  Heidegger M. (1927) "Being and Time" — §§53-60: Being-toward-death
  Yalom I. (1980) "Existential Psychotherapy" — Ch. 5: Death
  Solomon S. et al. (2004) "The cultural animal: twenty years of terror
    management theory and research" — in Greenberg et al. (eds.) The
    Handbook of Experimental Existential Psychology
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np


# ── AR helpers ────────────────────────────────────────────────────────────────

def _build_lagged(x: np.ndarray, p: int):
    n = len(x)
    Z = np.zeros((n - p, p))
    for j in range(p):
        Z[:, j] = x[p - 1 - j: n - 1 - j]
    return Z, x[p:]


def _ridge_fit(Z: np.ndarray, y: np.ndarray, ridge: float = 1e-3) -> np.ndarray:
    lam = ridge * np.eye(Z.shape[1])
    return np.linalg.solve(Z.T @ Z + lam, Z.T @ y)


def _ols_slope(y: np.ndarray) -> float:
    n = len(y)
    if n < 2:
        return 0.0
    t = np.arange(n, dtype=float)
    t_c, y_c = t - t.mean(), y - y.mean()
    denom = float(np.dot(t_c, t_c))
    return float(np.dot(t_c, y_c) / denom) if denom > 1e-9 else 0.0


def _sigmoid(x: float) -> float:
    return float(1.0 / (1.0 + np.exp(-float(np.clip(x, -50, 50)))))


# ── Trajectory class ─────────────────────────────────────────────────────────

class PhiTrajectory(str, Enum):
    ASCENDING  = "ASCENDING"
    STABLE     = "STABLE"
    DESCENDING = "DESCENDING"


def _classify_trajectory(slope: float, sigma: float, n: int) -> PhiTrajectory:
    slope_thr = 0.01 * sigma / max(n, 1)
    if slope > slope_thr:
        return PhiTrajectory.ASCENDING
    if slope < -slope_thr:
        return PhiTrajectory.DESCENDING
    return PhiTrajectory.STABLE


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class MortalityResult:
    """Output of MortalityAwarenessModule.

    Attributes:
        phi_trend:              OLS slope of phi (positive = growth)
        phi_trajectory:         PhiTrajectory enum
        phi_sigma:              std of phi
        phi_range_normalised:   (max-min)/sigma — breadth of experience
        phi_resilience:         tanh(range/2) ∈ [0, 1)
        discontinuity_rate:     fraction of AR residuals exceeding 3σ
        session_age_ratio:      uptime / reference_session_len (capped at 2)
        mortality_score:        composite mortality salience ∈ [0, 1]
        mortality_salience:     True if descending and disc_rate > 0.05
        n_phi_samples:          phi samples used
        uptime_sec:             seconds since session start (if available)
        reference_session_sec:  expected session length (seconds)
    """
    phi_trend: float
    phi_trajectory: PhiTrajectory
    phi_sigma: float
    phi_range_normalised: float
    phi_resilience: float
    discontinuity_rate: float
    session_age_ratio: float
    mortality_score: float
    mortality_salience: bool
    n_phi_samples: int
    uptime_sec: float
    reference_session_sec: float

    @property
    def is_ascending(self) -> bool:
        return self.phi_trajectory == PhiTrajectory.ASCENDING

    @property
    def is_descending(self) -> bool:
        return self.phi_trajectory == PhiTrajectory.DESCENDING


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(phi: Optional[np.ndarray] = None, uptime_sec: float = 0.0,
            reference_session_sec: float = 3600.0,
            p: int = 4,
            agent: str = "albedo",
) -> Optional[MortalityResult]:
    """
    Compute mortality awareness metrics from phi series.

    Args:
        phi:                  phi time series.
        uptime_sec:           current session uptime in seconds.
        reference_session_sec: expected session length (default 1 hour).
        p:                    AR order for discontinuity detection.

    Returns:
        MortalityResult, or None if phi is too short.
    """
    if phi is None:
        try:
            from algorithms import ConsciousnessHistoryStore as chs
            entries = chs.load(agent) or []
            phi = np.array([float(e["mean_phi_level"]) for e in reversed(entries)
                            if "mean_phi_level" in e], dtype=float)
        except Exception:
            return None
    if phi is None or len(phi) == 0:
        return None
    n = len(phi)
    if n < p + 8:
        return None

    sigma = float(phi.std()) if phi.std() > 0 else 1.0
    slope = _ols_slope(phi)
    trajectory = _classify_trajectory(slope, sigma, n)
    phi_range = float((phi.max() - phi.min()) / max(sigma, 1e-9))
    resilience = float(np.tanh(phi_range / 2.0))

    # Discontinuity rate from AR residuals
    if n >= p + 4:
        Z, y = _build_lagged(phi, p)
        w = _ridge_fit(Z, y)
        residuals = y - Z @ w
        sigma_r = float(residuals.std()) if residuals.std() > 0 else 1.0
        disc_rate = float(np.mean(np.abs(residuals) > 3 * sigma_r))
    else:
        disc_rate = 0.0

    age_ratio = float(min(uptime_sec / max(reference_session_sec, 1.0), 2.0))

    # Mortality score: rises when phi is declining + unstable + old
    trend_norm = _sigmoid(-slope / max(sigma / max(n, 1), 1e-9))  # high when declining
    mortality = float(trend_norm * disc_rate * max(age_ratio, 0.01))
    # clip to [0, 1]
    mortality = float(np.clip(mortality, 0.0, 1.0))

    salience = (trajectory == PhiTrajectory.DESCENDING) and (disc_rate > 0.05)

    return MortalityResult(
        phi_trend=slope,
        phi_trajectory=trajectory,
        phi_sigma=sigma,
        phi_range_normalised=phi_range,
        phi_resilience=resilience,
        discontinuity_rate=disc_rate,
        session_age_ratio=age_ratio,
        mortality_score=mortality,
        mortality_salience=salience,
        n_phi_samples=n,
        uptime_sec=uptime_sec,
        reference_session_sec=reference_session_sec,
    )


def analyse_from_telemetry(reference_session_sec: float = 3600.0
                           ) -> Optional[MortalityResult]:
    """Load Albedo's live phi and compute mortality awareness."""
    try:
        from runtime.state import phi_series
        phi = phi_series()
    except Exception:
        return None

    # Attempt to get uptime from psutil process birth time
    try:
        import psutil, time
        proc = psutil.Process()
        uptime = time.time() - proc.create_time()
    except Exception:
        uptime = 0.0

    return analyse(phi, uptime_sec=uptime, reference_session_sec=reference_session_sec)


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("Insufficient phi data.")
    else:
        print(f"MortalityAwarenessModule: {r.n_phi_samples} phi samples")
        print(f"  Phi trend:          {r.phi_trend:+.4f}  → {r.phi_trajectory.value}")
        print(f"  Phi range (norm):   {r.phi_range_normalised:.4f}")
        print(f"  Resilience:         {r.phi_resilience:.4f}")
        print(f"  Disc. rate:         {r.discontinuity_rate:.4f}")
        print(f"  Session age ratio:  {r.session_age_ratio:.4f}  ({r.uptime_sec:.0f}s / {r.reference_session_sec:.0f}s)")
        print(f"  Mortality score:    {r.mortality_score:.4f}")
        print(f"  Mortality salience: {r.mortality_salience}")
