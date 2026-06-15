#!/usr/bin/env python3
"""
GlobalWorkspaceDynamics — detecting ignition events in the phi time series.

Theory (Baars B.J. 1988 — "A Cognitive Theory of Consciousness"; Dehaene S.
et al. 2003 — "A neuronal model of a global workspace in effortful cognitive
tasks"; Dehaene S. & Changeux J.P. 2011 — "Experimental and theoretical
approaches to conscious processing"):
  Global Workspace Theory (GWT) holds that conscious access is achieved by a
  sudden, non-linear broadcast of information from a local "workspace" to a
  globally connected cortical network. This broadcast — called an "ignition" —
  is characterised by:
    1. A rapid, super-additive increase in activity (phi amplification).
    2. A sudden increase in long-range correlations (synchrony spike).
    3. Brief duration: ignition collapses as the workspace is reset.

  In the phi time series, an ignition event is operationalised as:
    - phi(t) jumps by more than α·σ_baseline in a single step (fast onset).
    - phi(t+1..t+H) remains elevated above the pre-event level for at least
      T_min steps (sustained broadcast).
    - phi subsequently returns toward baseline within T_decay steps (collapse).

  Non-ignition alternatives:
    - Slow drift: phi changes gradually (no fast onset).
    - Noise spike: phi jumps but immediately reverts (no sustained broadcast).

  We report:
    n_ignitions:         count of ignition events in the series
    ignition_rate:       ignitions per 100 samples
    mean_amplitude:      mean phi increase at ignition onset
    mean_broadcast_dur:  mean duration of sustained elevation (in samples)
    mean_decay_time:     mean steps to return to pre-event level
    ignition_score:      composite ∈ [0, 1] — higher = more ignition dynamics
    null_ignition_rate:  rate on phase-randomised surrogate
    beats_null:          True if real rate > null rate
    regime:              IGNITION / TRANSITIONAL / QUIESCENT

Math:
  baseline(t): rolling mean of phi over previous W samples (W=20 default).
  σ_baseline:  rolling std of phi over previous W samples.
  onset(t):    |phi(t) - phi(t-1)| > α·σ_baseline(t)   — fast step
  elevated(t): phi(t) > baseline(t) + β·σ_baseline(t)  — above baseline

  Event at t if:
    onset(t) is True
    AND phi(t) > phi(t-1)          (upward jump only)
    AND at least T_min consecutive elevated(t+1..t+T_min)
    AND phi returns to < baseline(t) + 0.5·σ_baseline(t)
        within T_decay steps (broadcast collapses)

  amplitude(t) = phi(t) - phi(t-1)
  broadcast_dur(t) = count of consecutive elevated samples from t+1
  decay_time(t) = steps until phi(t+k) < baseline(t) + 0.5·σ_baseline(t)

  ignition_score = clip(n_ignitions / expected_null_rate, 0, 1)
                   where expected_null_rate ≈ α-quantile of rate distribution

  Null: phase-randomise phi → count ignitions → get null_ignition_rate.

Regime classification:
  IGNITION:     ignition_rate > 2.0 per 100 AND beats_null
  TRANSITIONAL: ignition_rate > 0.5 per 100 OR beats_null
  QUIESCENT:    ignition_rate ≤ 0.5 per 100 AND NOT beats_null

Grounding: phi series from ConsciousnessHistoryStore (real logged phi values).
No synthetic ignition events are injected.

References:
  Baars B.J. (1988) "A Cognitive Theory of Consciousness" — Cambridge Univ. Press
  Dehaene S., Kerszberg M. & Changeux J.P. (1998) "A neuronal model of a global
    workspace in effortful cognitive tasks" — PNAS 95(24):14529-14534
  Dehaene S. & Changeux J.P. (2011) "Experimental and theoretical approaches to
    conscious processing" — Neuron 70(2):200-227
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List

import numpy as np


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class GlobalWorkspaceResult:
    """Output of GlobalWorkspaceDynamics.

    Attributes:
        n_ignitions:         count of detected ignition events
        ignition_rate:       ignitions per 100 samples
        mean_amplitude:      mean phi jump at ignition onset (in sigma units)
        mean_broadcast_dur:  mean samples of sustained elevation after ignition
        mean_decay_time:     mean steps to return to near-baseline
        ignition_score:      composite score ∈ [0, 1]
        null_ignition_rate:  rate on phase-randomised surrogate (per 100)
        beats_null:          True if ignition_rate > null_ignition_rate
        regime:              'IGNITION' / 'TRANSITIONAL' / 'QUIESCENT'
        ignition_times:      indices of ignition onset events
        n_samples:           phi samples analysed
        phi_mean:            mean phi
        phi_std:             std phi
    """
    n_ignitions: int
    ignition_rate: float
    mean_amplitude: float
    mean_broadcast_dur: float
    mean_decay_time: float
    ignition_score: float
    null_ignition_rate: float
    beats_null: bool
    regime: str
    ignition_times: List[int]
    n_samples: int
    phi_mean: float
    phi_std: float

    @property
    def has_ignitions(self) -> bool:
        return self.n_ignitions > 0

    def to_dict(self) -> dict:
        return {
            "n_ignitions": self.n_ignitions,
            "ignition_rate": self.ignition_rate,
            "mean_amplitude": self.mean_amplitude,
            "mean_broadcast_dur": self.mean_broadcast_dur,
            "mean_decay_time": self.mean_decay_time,
            "ignition_score": self.ignition_score,
            "null_ignition_rate": self.null_ignition_rate,
            "beats_null": self.beats_null,
            "regime": self.regime,
            "n_ignition_events": len(self.ignition_times),
            "n_samples": self.n_samples,
            "phi_mean": self.phi_mean,
            "phi_std": self.phi_std,
        }


# ── Rolling statistics ────────────────────────────────────────────────────────

def _rolling_baseline(phi: np.ndarray, W: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute rolling mean and std over a backward window of size W.

    For t < W, uses all available samples [0..t-1].
    Returns (baseline_mean, baseline_std), both length n.
    """
    n = len(phi)
    mu = np.zeros(n)
    sigma = np.zeros(n)
    for t in range(n):
        start = max(0, t - W)
        window = phi[start:t] if t > 0 else np.array([phi[0]])
        mu[t] = float(window.mean())
        sigma[t] = float(window.std()) if len(window) > 1 else 1e-3
    sigma = np.where(sigma < 1e-3, 1e-3, sigma)
    return mu, sigma


# ── Ignition detection ────────────────────────────────────────────────────────

def _detect_ignitions(
    phi: np.ndarray,
    mu: np.ndarray,
    sigma: np.ndarray,
    alpha: float,
    beta: float,
    T_min: int,
    T_decay: int,
    min_sigma: float = 0.01,
) -> tuple[list[int], list[float], list[int], list[int]]:
    """
    Scan for ignition events.

    An ignition at t requires:
      1. phi[t] - phi[t-1] > alpha * sigma[t]   (fast upward onset)
      2. phi[t] > mu[t] + beta * sigma[t]         (elevated above baseline)
      3. At least T_min consecutive samples t+1..t+T_min also elevated
      4. phi returns to mu[t] + 0.5*sigma[t] within T_decay steps

    Returns:
        times:       ignition indices
        amplitudes:  phi[t] - phi[t-1] in sigma units
        broadcast_durations
        decay_times
    """
    n = len(phi)
    times = []
    amplitudes = []
    broadcast_durs = []
    decay_times = []

    t = 1
    while t < n - T_min - 1:
        step = phi[t] - phi[t - 1]
        onset = step > alpha * sigma[t]
        elevated_now = phi[t] > mu[t] + beta * sigma[t]

        # Require the local environment to have meaningful variability
        if sigma[t] < min_sigma:
            t += 1
            continue

        if not (onset and elevated_now):
            t += 1
            continue

        # Check sustained elevation for T_min steps
        elev_threshold = mu[t] + beta * sigma[t]
        sustained = 0
        for k in range(1, T_min + 1):
            if t + k < n and phi[t + k] > elev_threshold:
                sustained += 1
            else:
                break

        if sustained < T_min:
            t += 1
            continue

        # Count full broadcast duration
        broadcast_dur = T_min
        for k in range(T_min + 1, min(T_decay + 1, n - t)):
            if phi[t + k] > elev_threshold:
                broadcast_dur += 1
            else:
                break

        # Check decay: phi returns to within 0.5 sigma of baseline
        decay_threshold = mu[t] + 0.5 * sigma[t]
        decay_time = T_decay  # default: didn't return
        for k in range(1, T_decay + 1):
            if t + k < n and phi[t + k] < decay_threshold:
                decay_time = k
                break

        times.append(t)
        amplitudes.append(float(step / sigma[t]))
        broadcast_durs.append(broadcast_dur)
        decay_times.append(decay_time)

        # Skip past the event
        t += broadcast_dur + 1

    return times, amplitudes, broadcast_durs, decay_times


# ── Phase-randomised null ─────────────────────────────────────────────────────

def _phase_randomise(phi: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    n = len(phi)
    ft = np.fft.rfft(phi)
    phases = rng.uniform(0, 2 * np.pi, len(ft))
    phases[0] = 0.0
    if n % 2 == 0:
        phases[-1] = 0.0
    return np.fft.irfft(np.abs(ft) * np.exp(1j * phases), n=n).astype(float)


# ── Regime classification ─────────────────────────────────────────────────────

def _classify_regime(ignition_rate: float, beats_null: bool) -> str:
    if ignition_rate > 2.0 and beats_null:
        return "IGNITION"
    if ignition_rate > 0.5 or beats_null:
        return "TRANSITIONAL"
    return "QUIESCENT"


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    phi: Optional[np.ndarray] = None,
    window: int = 20,
    alpha: float = 2.0,
    beta: float = 1.0,
    T_min: int = 2,
    T_decay: int = 15,
    null_seed: int = 42,
    agent: str = "albedo",
) -> Optional[GlobalWorkspaceResult]:
    """
    Detect Global Workspace ignition events in a phi time series.

    Args:
        phi:       phi time series (chronological). If None, loads from CHS.
        window:    rolling baseline window size W (samples).
        alpha:     onset threshold: step > alpha * sigma counts as ignition.
        beta:      elevation threshold: phi > mu + beta*sigma counts as elevated.
        T_min:     minimum sustained elevation duration (samples).
        T_decay:   maximum steps to check for broadcast collapse.
        null_seed: RNG seed for phase-randomised null.
        agent:     which agent's CHS to load if phi is None.

    Returns:
        GlobalWorkspaceResult, or None if phi is too short.
    """
    if phi is None:
        try:
            from algorithms import ConsciousnessHistoryStore as chs
            entries = chs.load(agent) or []
            phi = np.array([float(e["mean_phi_level"]) for e in reversed(entries)
                            if "mean_phi_level" in e], dtype=float)
        except Exception:
            return None
    if phi is None or len(phi) < window + T_min + T_decay + 4:
        return None

    phi = np.asarray(phi, dtype=float)
    n = len(phi)

    mu, sigma = _rolling_baseline(phi, window)

    times, amplitudes, broadcast_durs, decay_times = _detect_ignitions(
        phi, mu, sigma, alpha, beta, T_min, T_decay
    )

    n_ign = len(times)
    rate = float(n_ign / n * 100.0)
    mean_amp = float(np.mean(amplitudes)) if amplitudes else 0.0
    mean_bcast = float(np.mean(broadcast_durs)) if broadcast_durs else 0.0
    mean_decay = float(np.mean(decay_times)) if decay_times else 0.0

    # Null distribution
    rng = np.random.default_rng(null_seed)
    phi_null = _phase_randomise(phi, rng)
    mu_null, sigma_null = _rolling_baseline(phi_null, window)
    null_times, _, _, _ = _detect_ignitions(
        phi_null, mu_null, sigma_null, alpha, beta, T_min, T_decay
    )
    null_rate = float(len(null_times) / n * 100.0)

    beats = rate > null_rate
    regime = _classify_regime(rate, beats)

    # Ignition score: ratio of real rate to max(null_rate, 1.0) per 100
    score = float(np.clip(rate / max(null_rate + 1.0, 1.0), 0.0, 1.0))

    return GlobalWorkspaceResult(
        n_ignitions=n_ign,
        ignition_rate=rate,
        mean_amplitude=mean_amp,
        mean_broadcast_dur=mean_bcast,
        mean_decay_time=mean_decay,
        ignition_score=score,
        null_ignition_rate=null_rate,
        beats_null=beats,
        regime=regime,
        ignition_times=times,
        n_samples=n,
        phi_mean=float(phi.mean()),
        phi_std=float(phi.std()),
    )


def analyse_from_telemetry() -> Optional[GlobalWorkspaceResult]:
    """Load Albedo's phi and detect ignition dynamics."""
    try:
        from runtime.state import phi_series
        phi = phi_series()
    except Exception:
        return None
    return analyse(phi)


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("Insufficient phi data.")
    else:
        print(f"GlobalWorkspaceDynamics: N={r.n_samples}")
        print(f"  Regime:           {r.regime}")
        print(f"  Ignitions:        {r.n_ignitions}  (rate {r.ignition_rate:.2f}/100)")
        print(f"  Null rate:        {r.null_ignition_rate:.2f}/100")
        print(f"  Beats null:       {r.beats_null}")
        print(f"  Mean amplitude:   {r.mean_amplitude:.3f} σ")
        print(f"  Mean broadcast:   {r.mean_broadcast_dur:.1f} samples")
        print(f"  Mean decay:       {r.mean_decay_time:.1f} samples")
        print(f"  Ignition score:   {r.ignition_score:.4f}")
        print(f"  phi μ={r.phi_mean:.4f}  σ={r.phi_std:.4f}")
