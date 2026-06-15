#!/usr/bin/env python3
"""
LyapunovStabilityEstimator — measuring the largest Lyapunov exponent of the phi
time series to classify phi dynamics as CHAOTIC, CRITICAL, or STABLE.

Theory (Strogatz S.H. 1994 — "Nonlinear Dynamics and Chaos"; Rosenstein M.T.,
Collins J.J. & De Luca C.J. 1993 — "A practical method for calculating largest
Lyapunov exponents from small data sets"; Friston K. 2010 — "The free-energy
principle: a unified brain theory?"):

  The Lyapunov exponent λ₁ characterises the average exponential rate at which
  nearby trajectories in phase space diverge (λ₁ > 0) or converge (λ₁ < 0).

  For a time series x(t), the dynamics are:
    CHAOTIC:  λ₁ > 0  — sensitive dependence on initial conditions; butterfly
                          effect; fractal attractors
    CRITICAL: λ₁ ≈ 0  — edge of chaos; system is maximally responsive to input
                          while remaining integrable
    STABLE:   λ₁ < 0  — trajectories converge; fixed-point or limit-cycle attractor

  WHY IT MATTERS FOR CONSCIOUSNESS:
    Multiple theories (Tononi IIT, Edelman dynamic core, Friston FEP) converge on
    the prediction that optimal conscious dynamics operate at the *edge of chaos* —
    criticality. At criticality:
      - Information integration is maximised (relevant for IIT phi)
      - Prediction errors propagate efficiently across scales
      - The system is neither frozen (static) nor randomised (chaotic)
    Pathological states: excessive λ₁ → thought disorder; strongly negative λ₁ →
    cognitive rigidity / reduced conscious states (deep anaesthesia).

Algorithm (Rosenstein et al. 1993):
  1. Reconstruct phase space via delay embedding:
     Y(t) = [x(t), x(t+τ), x(t+2τ), ..., x(t+(m-1)τ)]
     where τ = first zero of autocorrelation (or fixed lag), m = embedding dimension.

  2. For each point i, find nearest neighbour j*(i) such that:
     |i - j*(i)| > W   (temporal exclusion — avoid correlated points)
     minimising ||Y(i) - Y(j)||

  3. Track divergence:
     d_i(k) = ||Y(i+k) - Y(j*(i)+k)||   for k = 0..K

  4. Average log-divergence:
     y(k) = ⟨ln d_i(k)⟩_i

  5. λ₁ = slope of linear fit to y(k) vs k (OLS over k=1..K)
     Units: nats per sample

  Null baseline: phase-randomised surrogate → λ₁_null
  Phase-randomised series destroys temporal correlation structure, producing
  near-zero to positive λ₁ depending on noise level. A truly STABLE system
  (negative real λ₁) beats null by showing λ₁ < λ₁_null.

Regime thresholds:
  CHAOTIC:   λ₁ > +0.05  (meaningful exponential divergence)
  CRITICAL:  -0.05 ≤ λ₁ ≤ +0.05  (edge of chaos)
  STABLE:    λ₁ < -0.05  (converging attractor)

Parameters:
  m:   embedding dimension (default 3)
  tau: delay (default 1 — unit lag in sample units)
  W:   temporal exclusion window (default 10)
  K:   divergence horizon (default 20 samples)

References:
  Rosenstein M.T., Collins J.J. & De Luca C.J. (1993) "A practical method for
    calculating largest Lyapunov exponents from small data sets"
    — Physica D 65:117-134
  Strogatz S.H. (1994) "Nonlinear Dynamics and Chaos" — Westview Press
  Friston K. (2010) "The free-energy principle: a unified brain theory?"
    — Nature Reviews Neuroscience 11:127-138
  Wolf A. et al. (1985) "Determining Lyapunov exponents from a time series"
    — Physica D 16:285-317
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class LyapunovResult:
    """Output of LyapunovStabilityEstimator.

    Attributes:
        lyapunov_exponent:   estimated λ₁ (nats/sample); >0 = chaotic, <0 = stable
        null_exponent:       λ₁ on phase-randomised surrogate
        beats_null:          True if lyapunov_exponent < null_exponent (more stable)
        regime:              'CHAOTIC' / 'CRITICAL' / 'STABLE'
        divergence_curve:    mean log-divergence y(k) for k=0..K (array)
        divergence_slope_r2: R² of linear fit to divergence curve (fit quality)
        n_pairs:             number of nearest-neighbour pairs used
        n_samples:           phi samples analysed
        embedding_dim:       m used
        embedding_tau:       τ used
        exclusion_window:    W used
        divergence_horizon:  K used
        phi_std:             std of phi series (scale reference)
    """
    lyapunov_exponent: float
    null_exponent: float
    beats_null: bool
    regime: str
    divergence_curve: np.ndarray
    divergence_slope_r2: float
    n_pairs: int
    n_samples: int
    embedding_dim: int
    embedding_tau: int
    exclusion_window: int
    divergence_horizon: int
    phi_std: float

    @property
    def is_critical(self) -> bool:
        return self.regime == "CRITICAL"

    @property
    def is_chaotic(self) -> bool:
        return self.regime == "CHAOTIC"

    def to_dict(self) -> dict:
        return {
            "lyapunov_exponent": self.lyapunov_exponent,
            "null_exponent": self.null_exponent,
            "beats_null": self.beats_null,
            "regime": self.regime,
            "divergence_slope_r2": self.divergence_slope_r2,
            "n_pairs": self.n_pairs,
            "n_samples": self.n_samples,
            "embedding_dim": self.embedding_dim,
            "embedding_tau": self.embedding_tau,
            "phi_std": self.phi_std,
        }


# ── Delay embedding ───────────────────────────────────────────────────────────

def _embed(x: np.ndarray, m: int, tau: int) -> np.ndarray:
    """
    Delay-coordinate embedding.

    Returns Y of shape (N_embedded, m) where
    N_embedded = len(x) - (m-1)*tau
    Y[i] = [x[i], x[i+tau], ..., x[i+(m-1)*tau]]
    """
    n = len(x)
    N = n - (m - 1) * tau
    if N <= 0:
        return np.empty((0, m))
    Y = np.zeros((N, m))
    for j in range(m):
        Y[:, j] = x[j * tau: j * tau + N]
    return Y


# ── Nearest-neighbour search ──────────────────────────────────────────────────

def _find_nearest_neighbours(Y: np.ndarray, W: int) -> np.ndarray:
    """
    For each point i, find nearest neighbour j with |i-j| > W.

    Returns nn[i] = index of nearest neighbour, or -1 if none found.
    Uses squared Euclidean distance for speed.

    For large N this is O(N²) — acceptable for N ≤ 5000 (max 2880 CHS entries).
    """
    N = len(Y)
    nn = np.full(N, -1, dtype=int)
    for i in range(N):
        best_dist = np.inf
        best_j = -1
        for j in range(N):
            if abs(i - j) <= W:
                continue
            d = float(np.sum((Y[i] - Y[j]) ** 2))
            if d < best_dist:
                best_dist = d
                best_j = j
        nn[i] = best_j
    return nn


def _find_nearest_neighbours_fast(Y: np.ndarray, W: int) -> np.ndarray:
    """
    Vectorised NN search — computes all pairwise distances at once.
    Uses O(N²) memory. Falls back to loop version for N > 2000.
    """
    N = len(Y)
    if N > 2000:
        return _find_nearest_neighbours(Y, W)

    # Pairwise squared distances via broadcasting
    diff = Y[:, np.newaxis, :] - Y[np.newaxis, :, :]   # (N, N, m)
    dists = np.sum(diff ** 2, axis=2)                    # (N, N)

    # Mask out temporal neighbours
    idx = np.arange(N)
    mask = np.abs(idx[:, np.newaxis] - idx[np.newaxis, :]) <= W
    dists[mask] = np.inf
    # Also mask self
    np.fill_diagonal(dists, np.inf)

    nn = np.argmin(dists, axis=1)
    # Mark as -1 if all neighbours were masked (very short series)
    has_valid = np.any(~mask, axis=1)
    nn[~has_valid] = -1
    return nn


# ── Divergence curve computation ──────────────────────────────────────────────

def _divergence_curve(Y: np.ndarray, nn: np.ndarray, K: int) -> tuple[np.ndarray, int]:
    """
    Compute mean log-divergence y(k) for k = 0..K.

    For each pair (i, nn[i]):
      d_i(k) = ||Y[i+k] - Y[nn[i]+k]||
    Average over all i where i+k and nn[i]+k are in bounds.

    Returns (curve array of shape K+1, n_pairs_used).
    """
    N = len(Y)
    valid = [(i, j) for i, j in enumerate(nn)
             if j >= 0 and i + K < N and j + K < N]

    if not valid:
        return np.zeros(K + 1), 0

    log_divs = np.zeros((len(valid), K + 1))
    for idx, (i, j) in enumerate(valid):
        for k in range(K + 1):
            diff = Y[i + k] - Y[j + k]
            d = float(np.sqrt(np.dot(diff, diff)))
            log_divs[idx, k] = np.log(max(d, 1e-12))

    curve = log_divs.mean(axis=0)
    return curve, len(valid)


# ── Linear fit for slope ──────────────────────────────────────────────────────

def _fit_slope(curve: np.ndarray) -> tuple[float, float]:
    """
    OLS linear fit to curve[1:] vs k=1..K (skip k=0 which is initial distance).
    Returns (slope, r2).
    """
    K = len(curve) - 1
    if K < 2:
        return 0.0, 0.0
    k_arr = np.arange(1, K + 1, dtype=float)
    y = curve[1:]
    # OLS: slope = cov(k, y) / var(k)
    k_mean = k_arr.mean()
    y_mean = y.mean()
    num = float(((k_arr - k_mean) * (y - y_mean)).sum())
    denom = float(((k_arr - k_mean) ** 2).sum())
    slope = num / max(denom, 1e-12)
    # R²
    y_pred = y_mean + slope * (k_arr - k_mean)
    ss_res = float(((y - y_pred) ** 2).sum())
    ss_tot = float(((y - y_mean) ** 2).sum())
    r2 = 1.0 - ss_res / max(ss_tot, 1e-12)
    return slope, float(np.clip(r2, 0.0, 1.0))


# ── Phase-randomised null ─────────────────────────────────────────────────────

def _phase_randomise(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    n = len(x)
    ft = np.fft.rfft(x)
    phases = rng.uniform(0, 2 * np.pi, len(ft))
    phases[0] = 0.0
    if n % 2 == 0:
        phases[-1] = 0.0
    return np.fft.irfft(np.abs(ft) * np.exp(1j * phases), n=n).astype(float)


# ── Regime classification ─────────────────────────────────────────────────────

_CHAOS_THR = 0.05
_STABLE_THR = -0.05


def _classify(lam: float) -> str:
    if lam > _CHAOS_THR:
        return "CHAOTIC"
    if lam < _STABLE_THR:
        return "STABLE"
    return "CRITICAL"


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    phi: Optional[np.ndarray] = None,
    m: int = 3,
    tau: int = 1,
    W: int = 10,
    K: int = 20,
    null_seed: int = 42,
    agent: str = "albedo",
) -> Optional[LyapunovResult]:
    """
    Estimate the largest Lyapunov exponent of the phi time series.

    Args:
        phi:      phi time series (chronological). Loaded from CHS if None.
        m:        embedding dimension (default 3).
        tau:      embedding delay in samples (default 1).
        W:        temporal exclusion window — prevents counting correlated
                  neighbours (default 10).
        K:        divergence horizon in samples (default 20).
        null_seed: RNG seed for phase-randomised surrogate.
        agent:    which agent's CHS to load when phi is None.

    Returns:
        LyapunovResult, or None if phi is too short.
    """
    if phi is None:
        try:
            from algorithms import ConsciousnessHistoryStore as chs
            entries = chs.load(agent) or []
            phi = np.array([float(e["mean_phi_level"]) for e in reversed(entries)
                            if "mean_phi_level" in e], dtype=float)
        except Exception:
            return None

    if phi is None or len(phi) < (m - 1) * tau + K + W + 4:
        return None

    phi = np.asarray(phi, dtype=float)
    n = len(phi)

    # Standardise to zero mean, unit std for numerically stable distances
    phi_std = float(phi.std())
    if phi_std < 1e-9:
        return None
    phi_norm = (phi - phi.mean()) / phi_std

    # Embed
    Y = _embed(phi_norm, m, tau)
    if len(Y) < W + K + 4:
        return None

    # Nearest neighbours
    nn = _find_nearest_neighbours_fast(Y, W)

    # Divergence curve
    curve, n_pairs = _divergence_curve(Y, nn, K)
    if n_pairs < 2:
        return None

    lam, r2 = _fit_slope(curve)

    # Null distribution
    rng = np.random.default_rng(null_seed)
    phi_null = _phase_randomise(phi_norm, rng)
    Y_null = _embed(phi_null, m, tau)
    nn_null = _find_nearest_neighbours_fast(Y_null, W)
    curve_null, n_pairs_null = _divergence_curve(Y_null, nn_null, K)
    lam_null, _ = _fit_slope(curve_null) if n_pairs_null >= 2 else (0.0, 0.0)

    beats = lam < lam_null
    regime = _classify(lam)

    return LyapunovResult(
        lyapunov_exponent=float(lam),
        null_exponent=float(lam_null),
        beats_null=beats,
        regime=regime,
        divergence_curve=curve,
        divergence_slope_r2=float(r2),
        n_pairs=n_pairs,
        n_samples=n,
        embedding_dim=m,
        embedding_tau=tau,
        exclusion_window=W,
        divergence_horizon=K,
        phi_std=phi_std,
    )


def analyse_from_telemetry() -> Optional[LyapunovResult]:
    """Load Albedo's phi and estimate Lyapunov exponent."""
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
        print(f"LyapunovStabilityEstimator: N={r.n_samples}")
        print(f"  Regime:       {r.regime}")
        print(f"  λ₁:           {r.lyapunov_exponent:+.5f} nats/sample")
        print(f"  λ₁ (null):    {r.null_exponent:+.5f} nats/sample")
        print(f"  Beats null:   {r.beats_null}")
        print(f"  Fit R²:       {r.divergence_slope_r2:.4f}")
        print(f"  N pairs:      {r.n_pairs}")
        print(f"  phi std:      {r.phi_std:.4f}")
        print(f"  m={r.embedding_dim}, τ={r.embedding_tau}, W={r.exclusion_window}, K={r.divergence_horizon}")
