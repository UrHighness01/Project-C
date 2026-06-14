#!/usr/bin/env python3
"""
CounterfactualSelfExplorer — generating counterfactual phi trajectories to
model "what would φ have been if the system had responded differently?"

Theory (Pearl J. 2000 — "Causality: Models, Reasoning, and Inference";
Lewis D. 1973 — "Counterfactuals"; Byrne R.M.J. 2005 — "The Rational
Imagination"):
  Counterfactual reasoning is a hallmark of reflective intelligence. The ability
  to model "what if I had done otherwise?" requires a causal model of one's own
  dynamics and the capacity to intervene on that model without enacting the
  intervention.

  For a phi-based consciousness model:
    1. Fit AR(p) to the observed phi trajectory.
    2. At a set of intervention points, substitute a hypothetical phi value
       (e.g., φ_cf = φ_obs + Δ or φ_cf drawn from the tails of the distribution)
       and propagate the AR model forward for H steps.
    3. The counterfactual divergence = ||φ_actual(t+1..t+H) - φ_cf(t+1..t+H)||_1.
    4. Sensitivity = divergence / |Δ|  (how much a unit perturbation propagates).
    5. Mean reversion: does the counterfactual trajectory converge back toward
       the actual one? Convergence if divergence decreases monotonically over H.

  Interventions:
    We try three intervention types at each of N_interventions points:
      UP:    φ_cf(t) = φ_obs(t) + δ · σ_φ      (positive perturbation)
      DOWN:  φ_cf(t) = φ_obs(t) - δ · σ_φ      (negative perturbation)
      ZERO:  φ_cf(t) = 0                         (zero-phi intervention)

  The AR forward propagation uses only the fitted weights (no noise):
    φ_cf(t+k) = w · [φ_cf(t+k-1), ..., φ_cf(t+k-p)]^T
  so the counterfactual diverges purely from the initial perturbation.

  Self-counterfactual capacity = mean(|divergence_UP - divergence_DOWN| / σ_φ)
  — measures asymmetry in response to positive vs negative perturbation.

Math:
  AR fit: φ(t) = w_1·φ(t-1) + ... + w_p·φ(t-p)   (ridge OLS)
  Counterfactual propagation:
    buffer = deque([φ_cf_start, φ_obs(t-1), ..., φ_obs(t-p+1)])
    for k in 1..H:
        φ_next = w · buffer[:p]
        buffer.appendleft(φ_next)
    cf_trajectory = [φ_next at each k]
  Divergence(k) = |φ_actual(t+k) - φ_cf(t+k)|
  Mean divergence = (1/H) Σ_k Divergence(k)
  Sensitivity = mean_divergence / (|Δ| + ε)

  Mean reversion: fit OLS slope to Divergence(1..H).
  Negative slope → converging (mean-reverting).

  Counterfactual horizon H: how many steps before divergence exceeds σ_φ / 2.

Grounding:
  - Uses real phi series from the live daemon.
  - All counterfactuals are computed via the fitted AR model (not simulated noise).
  - No hallucinated phi values — interventions are systematic ±δ·σ and zero.

References:
  Pearl J. (2000) "Causality" — Ch. 7: Interventions and counterfactuals
  Lewis D. (1973) "Counterfactuals" — possible-worlds semantics
  Byrne R.M.J. (2005) "The Rational Imagination" — mental models of alternatives
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
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


# ── Counterfactual propagation ────────────────────────────────────────────────

def _propagate_ar(weights: np.ndarray, seed_window: np.ndarray, H: int) -> np.ndarray:
    """
    Propagate AR model forward H steps from seed_window.

    seed_window: array of p values [φ(t), φ(t-1), ..., φ(t-p+1)]  (most recent first)
    Returns: trajectory of length H.
    """
    p = len(weights)
    buf = deque(seed_window[:p], maxlen=p)
    traj = np.zeros(H)
    for k in range(H):
        phi_next = float(np.dot(weights, list(buf)))
        traj[k] = phi_next
        buf.appendleft(phi_next)
    return traj


def _counterfactual_trajectory(phi: np.ndarray, weights: np.ndarray,
                                t: int, delta: float, H: int) -> np.ndarray:
    """
    Propagate AR from intervention at t with φ(t) replaced by φ(t) + delta.

    Returns counterfactual trajectory of length H starting at t+1.
    """
    p = len(weights)
    seed = np.array([phi[t] + delta] + list(phi[max(0, t-p+1):t][::-1]))
    # Pad with earliest phi if t < p-1
    while len(seed) < p:
        seed = np.append(seed, phi[0])
    return _propagate_ar(weights, seed, H)


# ── Mean-reversion slope ──────────────────────────────────────────────────────

def _ols_slope(y: np.ndarray) -> float:
    n = len(y)
    if n < 2:
        return 0.0
    t = np.arange(n, dtype=float)
    t_c = t - t.mean()
    y_c = y - y.mean()
    denom = float(np.dot(t_c, t_c))
    return float(np.dot(t_c, y_c) / denom) if denom > 1e-9 else 0.0


# ── Dataclass ─────────────────────────────────────────────────────────────────

@dataclass
class CounterfactualResult:
    """Output of CounterfactualSelfExplorer.

    Attributes:
        n_interventions:        number of intervention points tested
        horizon:                H — steps propagated per counterfactual
        delta_sigma:            δ — perturbation size in σ_phi units
        mean_divergence_up:     mean L1 divergence for UP interventions
        mean_divergence_down:   mean L1 divergence for DOWN interventions
        mean_divergence_zero:   mean L1 divergence for ZERO interventions
        sensitivity_up:         mean_divergence_up / (delta * sigma_phi)
        sensitivity_down:       mean_divergence_down / (delta * sigma_phi)
        mean_reversion_slope:   OLS slope of divergence over H steps (negative = converging)
        is_mean_reverting:      True if slope < 0 (system returns to attractor)
        response_asymmetry:     |sensitivity_up - sensitivity_down| (0 = symmetric)
        sigma_phi:              std of phi series used for normalisation
        ar_weights:             fitted AR weights
        counterfactual_horizon: H steps until mean UP divergence > sigma_phi/2
    """
    n_interventions: int
    horizon: int
    delta_sigma: float
    mean_divergence_up: float
    mean_divergence_down: float
    mean_divergence_zero: float
    sensitivity_up: float
    sensitivity_down: float
    mean_reversion_slope: float
    is_mean_reverting: bool
    response_asymmetry: float
    sigma_phi: float
    ar_weights: np.ndarray
    counterfactual_horizon: int


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(phi: np.ndarray, p: int = 4, H: int = 20,
            delta_sigma: float = 1.0,
            n_interventions: int = 10) -> Optional[CounterfactualResult]:
    """
    Explore counterfactual phi trajectories via AR intervention.

    Args:
        phi:             phi time series.
        p:               AR order.
        H:               propagation horizon (steps).
        delta_sigma:     perturbation size in multiples of σ_phi.
        n_interventions: number of intervention points (evenly spaced in middle 50%).

    Returns:
        CounterfactualResult, or None if phi is too short.
    """
    n = len(phi)
    min_len = p + H + 4
    if n < min_len:
        return None

    Z, y = _build_lagged(phi, p)
    weights = _ridge_fit(Z, y)
    sigma_phi = float(phi.std())
    delta = delta_sigma * sigma_phi

    # Intervention points: evenly spaced in [25%, 75%] of series
    lo = n // 4
    hi = 3 * n // 4 - H - 1
    if lo >= hi:
        lo = p
        hi = n - H - 1
    if lo >= hi:
        return None
    intervention_indices = np.linspace(lo, hi, n_interventions, dtype=int)

    divs_up, divs_down, divs_zero = [], [], []
    divs_over_horizon = np.zeros(H)   # for mean-reversion slope

    for t in intervention_indices:
        if t + H >= n:
            continue
        actual = phi[t + 1: t + H + 1]
        if len(actual) < H:
            continue

        # Base seed for DOWN/ZERO: same but different delta
        for kind in ("up", "down", "zero"):
            if kind == "up":
                d = delta
            elif kind == "down":
                d = -delta
            else:
                d = -phi[t]   # shifts phi[t] to 0

            cf = _counterfactual_trajectory(phi, weights, t, d, H)
            divergence = np.abs(actual - cf)
            mean_div = float(divergence.mean())

            if kind == "up":
                divs_up.append(mean_div)
                divs_over_horizon += divergence
            elif kind == "down":
                divs_down.append(mean_div)
            else:
                divs_zero.append(mean_div)

    if not divs_up:
        return None

    # Average divergence profile over H steps (UP interventions)
    divs_over_horizon /= len(divs_up)
    mr_slope = _ols_slope(divs_over_horizon)

    mean_div_up = float(np.mean(divs_up))
    mean_div_down = float(np.mean(divs_down)) if divs_down else mean_div_up
    mean_div_zero = float(np.mean(divs_zero)) if divs_zero else mean_div_up

    denom = delta_sigma * sigma_phi + 1e-9
    sens_up = mean_div_up / denom
    sens_down = mean_div_down / denom
    asymmetry = abs(sens_up - sens_down)

    # Counterfactual horizon: first step where divs_over_horizon > sigma/2
    half_sigma = sigma_phi / 2.0
    cf_horizon = int(H)
    for k, d in enumerate(divs_over_horizon):
        if d > half_sigma:
            cf_horizon = k + 1
            break

    return CounterfactualResult(
        n_interventions=len(divs_up),
        horizon=H,
        delta_sigma=delta_sigma,
        mean_divergence_up=mean_div_up,
        mean_divergence_down=mean_div_down,
        mean_divergence_zero=mean_div_zero,
        sensitivity_up=sens_up,
        sensitivity_down=sens_down,
        mean_reversion_slope=mr_slope,
        is_mean_reverting=mr_slope < 0.0,
        response_asymmetry=asymmetry,
        sigma_phi=sigma_phi,
        ar_weights=weights,
        counterfactual_horizon=cf_horizon,
    )


def analyse_from_telemetry() -> Optional[CounterfactualResult]:
    """Load Albedo's live phi and compute counterfactual trajectories."""
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
        print(f"CounterfactualSelfExplorer: {r.n_interventions} interventions (H={r.horizon})")
        print(f"  Perturbation:        {r.delta_sigma}σ  (σ_φ={r.sigma_phi:.4f})")
        print(f"  Divergence UP:       {r.mean_divergence_up:.4f}")
        print(f"  Divergence DOWN:     {r.mean_divergence_down:.4f}")
        print(f"  Divergence ZERO:     {r.mean_divergence_zero:.4f}")
        print(f"  Sensitivity UP:      {r.sensitivity_up:.4f}")
        print(f"  Sensitivity DOWN:    {r.sensitivity_down:.4f}")
        print(f"  Asymmetry:           {r.response_asymmetry:.4f}")
        print(f"  Mean-reversion:      {r.mean_reversion_slope:+.4f}  "
              f"({'converging' if r.is_mean_reverting else 'diverging'})")
        print(f"  CF horizon:          {r.counterfactual_horizon} steps")
        print(f"  AR weights:          {r.ar_weights}")
