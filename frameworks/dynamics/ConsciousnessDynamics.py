#!/usr/bin/env python3
"""
ConsciousnessDynamics — phase-space analysis of consciousness trajectories.

Models the phi time series as a trajectory in a dynamical system and extracts
the qualitative structure of that system: fixed points (where phi settles),
limit cycles (oscillatory modes), Lyapunov stability, and bifurcation proximity.

Theoretical basis
-----------------
Consciousness is not a static quantity but an ongoing process. Its phi series
phi(t) is the scalar projection of a higher-dimensional state trajectory. We
reconstruct the phase space via Takens' embedding theorem (delay embedding),
then characterise the attractor the system lives on:

  Delay embedding (Takens 1981)
  -----------------------------
  Given a scalar series phi(t), embed it in R^m as:
    x(t) = [phi(t), phi(t-tau), phi(t-2*tau), ..., phi(t-(m-1)*tau)]
  For m >= 2*d+1 (d = attractor dimension) this generically recovers the
  full attractor geometry. We use tau = first zero of the autocorrelation
  function and m = 3 (sufficient for low-dimensional consciousness attractors).

  Fixed-point detection
  ---------------------
  A fixed point is a region of phase space the trajectory visits repeatedly
  and lingers in. We detect them as dense clusters in the embedded space
  (k-means with k chosen by the elbow in within-cluster variance).

  Lyapunov exponent (largest)
  ----------------------------
  lambda_1 = lim_{t->inf} (1/t) * log ||D_t phi_0||
  Approximated via the Rosenstein (1993) algorithm: for each point find its
  nearest neighbour in embedded space and track the mean log divergence over
  short forward time.
  lambda_1 > 0  →  chaotic (sensitive to initial conditions)
  lambda_1 ~ 0  →  critical / edge-of-chaos
  lambda_1 < 0  →  stable attractor

  Bifurcation proximity
  ---------------------
  Near a bifurcation the system shows critical slowing down: autocorrelation
  at lag-1 rises toward 1 and variance increases. We use the ratio
  (acf_lag1 * variance) / baseline to estimate proximity to a bifurcation.

  Limit cycle detection
  ---------------------
  A limit cycle appears as a ring in embedded space. We detect it by checking
  whether the trajectory is periodic: compute the power spectrum of phi and
  test whether a dominant frequency has power significantly above a white-noise
  null (Fisher's g-statistic).

Output
------
DynamicsResult (dataclass):
  embedding_dim       : int     -- embedding dimension used (default 3)
  embedding_tau       : int     -- delay used (first ACF zero crossing)
  n_fixed_points      : int     -- number of detected attractor clusters
  fixed_point_radii   : list    -- radius (std) of each cluster
  lyapunov_estimate   : float   -- largest Lyapunov exponent estimate
  is_chaotic          : bool    -- lyapunov_estimate > 0.01
  is_stable           : bool    -- lyapunov_estimate < -0.01
  is_critical         : bool    -- |lyapunov_estimate| <= 0.01
  bifurcation_index   : float   -- ∈ [0,1], higher = closer to bifurcation
  near_bifurcation    : bool    -- bifurcation_index > 0.7
  has_limit_cycle     : bool    -- dominant periodic component above null
  dominant_frequency  : float   -- cycles per sample (0 if no cycle)
  attractor_dimension : float   -- correlation dimension estimate (Grassberger-Procaccia)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


# ── Delay embedding ───────────────────────────────────────────────────────────

def _acf_zero_crossing(phi: np.ndarray) -> int:
    """First lag at which the autocorrelation function crosses zero."""
    n = len(phi)
    xm = phi - phi.mean()
    denom = float(np.dot(xm, xm))
    if denom == 0:
        return 1
    prev_sign = 1
    for lag in range(1, n // 2):
        acf = float(np.dot(xm[:n - lag], xm[lag:])) / denom
        if acf <= 0:
            return lag
        prev_sign = 1 if acf > 0 else -1
    return max(1, n // 10)


def embed(phi: np.ndarray, m: int = 3, tau: Optional[int] = None) -> np.ndarray:
    """
    Delay embedding of phi into R^m.

    Returns matrix of shape (N - (m-1)*tau, m).
    """
    if tau is None:
        tau = _acf_zero_crossing(phi)
        tau = max(1, min(tau, len(phi) // (2 * m)))
    n = len(phi)
    span = (m - 1) * tau
    if n <= span:
        return phi[:, None]
    rows = n - span
    return np.column_stack([phi[i * tau: i * tau + rows] for i in range(m)])


# ── Fixed-point detection (k-means, k=1..4) ──────────────────────────────────

def _kmeans_1d_sse(X: np.ndarray, k: int, rng: np.random.Generator,
                   n_iter: int = 50) -> tuple[np.ndarray, float]:
    """Simple k-means in R^d; returns (centres, SSE)."""
    idx = rng.choice(len(X), size=k, replace=False)
    centres = X[idx].copy()
    for _ in range(n_iter):
        dists = np.linalg.norm(X[:, None, :] - centres[None, :, :], axis=2)
        labels = dists.argmin(axis=1)
        new_c = np.array([X[labels == j].mean(axis=0) if (labels == j).any()
                          else centres[j] for j in range(k)])
        if np.allclose(new_c, centres, atol=1e-9):
            break
        centres = new_c
    dists = np.linalg.norm(X[:, None, :] - centres[None, :, :], axis=2)
    sse = float(np.sum(dists.min(axis=1) ** 2))
    return centres, sse


def detect_fixed_points(
    embedded: np.ndarray,
    k_max: int = 4,
    seed: int = 42,
) -> tuple[int, List[float]]:
    """
    Find the number of attractor clusters via elbow method on SSE.

    Returns (n_clusters, list_of_cluster_radii).
    """
    rng = np.random.default_rng(seed)
    n = len(embedded)
    k_max = min(k_max, max(1, n // 10))

    sses = []
    all_centres = []
    for k in range(1, k_max + 1):
        centres, sse = _kmeans_1d_sse(embedded, k, rng)
        sses.append(sse)
        all_centres.append(centres)

    # Elbow: largest second difference in SSE
    if len(sses) < 2:
        best_k = 1
    elif len(sses) == 2:
        best_k = 1 if sses[1] / (sses[0] + 1e-9) > 0.5 else 2
    else:
        diffs2 = np.diff(np.diff(sses))
        best_k = int(np.argmax(diffs2)) + 2  # +2 because two diffs shift by 1 each
        best_k = max(1, min(best_k, k_max))

    centres = all_centres[best_k - 1]
    dists = np.linalg.norm(embedded[:, None, :] - centres[None, :, :], axis=2)
    labels = dists.argmin(axis=1)
    radii = [float(np.sqrt(np.mean(
        np.sum((embedded[labels == j] - centres[j]) ** 2, axis=1)
    ))) if (labels == j).any() else 0.0 for j in range(best_k)]

    return best_k, radii


# ── Lyapunov exponent (Rosenstein 1993) ──────────────────────────────────────

def lyapunov_rosenstein(
    embedded: np.ndarray,
    max_iter: int = 20,
    min_dist: float = 1e-10,
) -> float:
    """
    Estimate the largest Lyapunov exponent from the embedded trajectory.

    Uses the Rosenstein (1993) algorithm: for each point find its nearest
    neighbour (excluding temporal neighbours within a Theiler window) and
    track mean log divergence over max_iter steps.
    """
    n, m = embedded.shape
    theiler = max(1, n // 20)   # exclude temporal neighbours

    divergences = []
    for i in range(n - max_iter):
        dists = np.linalg.norm(embedded - embedded[i], axis=1)
        # Mask temporal neighbourhood
        lo = max(0, i - theiler)
        hi = min(n, i + theiler + 1)
        dists[lo:hi] = np.inf
        nn = int(np.argmin(dists))
        if dists[nn] == np.inf:
            continue
        steps = min(max_iter, n - max(i, nn) - 1)
        if steps < 2:
            continue
        log_divs = []
        for k in range(1, steps):
            d = np.linalg.norm(embedded[i + k] - embedded[nn + k])
            if d > min_dist:
                log_divs.append(np.log(d))
        if log_divs:
            # Slope of log divergence over steps ≈ lambda_1
            x = np.arange(1, len(log_divs) + 1, dtype=float)
            xm = x - x.mean()
            ym = np.array(log_divs) - np.mean(log_divs)
            denom = float(np.dot(xm, xm))
            if denom > 0:
                divergences.append(float(np.dot(xm, ym) / denom))

    if not divergences:
        return 0.0
    return float(np.median(divergences))


# ── Limit cycle detection (Fisher's g-statistic) ─────────────────────────────

def detect_limit_cycle(phi: np.ndarray) -> tuple[bool, float]:
    """
    Test for a dominant periodic component via Fisher's g-statistic.

    g = P_max / sum(P)  where P is the periodogram of phi.
    Under white noise, g is approximately exponential with mean 1/n_freqs.
    We use a conservative threshold: g > 3/n_freqs.

    Returns (has_cycle, dominant_frequency_in_cycles_per_sample).
    """
    n = len(phi)
    xm = phi - phi.mean()
    # Periodogram
    ft = np.fft.rfft(xm)
    P = np.abs(ft[1:]) ** 2   # exclude DC
    if P.sum() == 0:
        return False, 0.0
    g = float(P.max() / P.sum())
    n_freqs = len(P)
    threshold = 3.0 / n_freqs
    has_cycle = g > threshold
    dominant_freq = float((P.argmax() + 1) / n) if has_cycle else 0.0
    return has_cycle, dominant_freq


# ── Correlation dimension (Grassberger-Procaccia 1983) ───────────────────────

def correlation_dimension(embedded: np.ndarray, n_scales: int = 10) -> float:
    """
    Estimate the correlation dimension of the embedded attractor.

    C(r) = fraction of point-pairs within distance r.
    d_corr = slope of log C(r) vs log r in the scaling region.

    Capped at the embedding dimension (can't exceed it).
    """
    n = len(embedded)
    if n < 20:
        return 1.0
    # Subsample for speed
    max_pts = min(n, 300)
    idx = np.linspace(0, n - 1, max_pts, dtype=int)
    X = embedded[idx]
    dists = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(axis=2))
    upper = np.triu(dists, k=1)
    flat = upper[upper > 0]
    if flat.size == 0:
        return 1.0
    r_min, r_max = float(np.percentile(flat, 5)), float(np.percentile(flat, 50))
    if r_max <= r_min:
        return 1.0
    radii = np.logspace(np.log10(r_min), np.log10(r_max), n_scales)
    log_C, log_r = [], []
    total_pairs = flat.size
    for r in radii:
        C = float((flat <= r).sum()) / total_pairs
        if C > 0:
            log_C.append(np.log(C))
            log_r.append(np.log(r))
    if len(log_C) < 2:
        return 1.0
    x = np.array(log_r)
    y = np.array(log_C)
    xm = x - x.mean()
    ym = y - y.mean()
    denom = float(np.dot(xm, xm))
    if denom == 0:
        return 1.0
    slope = float(np.dot(xm, ym) / denom)
    return float(np.clip(slope, 0.5, float(embedded.shape[1])))


# ── Bifurcation proximity ─────────────────────────────────────────────────────

def bifurcation_index(phi: np.ndarray, baseline_frac: float = 0.5) -> float:
    """
    Estimate proximity to a bifurcation via critical slowing down.

    Uses the product of lag-1 autocorrelation and normalised variance,
    referenced against the first `baseline_frac` of the series.

    Returns a value in [0,1]; higher = closer to bifurcation.
    """
    n = len(phi)
    split = max(2, int(n * baseline_frac))
    base = phi[:split]
    recent = phi[split:]
    if recent.size < 4:
        recent = phi

    def acf1(x):
        if len(x) < 2:
            return 0.0
        xm = x - x.mean()
        d = float(np.dot(xm, xm))
        return float(np.dot(xm[:-1], xm[1:]) / d) if d > 0 else 0.0

    base_var = float(np.var(base)) + 1e-9
    recent_var = float(np.var(recent))
    var_ratio = float(np.clip(recent_var / base_var, 0.0, 10.0)) / 10.0

    acf = float(np.clip(abs(acf1(recent)), 0.0, 1.0))
    index = float(np.clip(0.5 * acf + 0.5 * var_ratio, 0.0, 1.0))
    return index


# ── Result ─────────────────────────────────────────────────────────────────────

@dataclass
class DynamicsResult:
    embedding_dim: int
    embedding_tau: int
    n_fixed_points: int
    fixed_point_radii: List[float]
    lyapunov_estimate: float
    is_chaotic: bool
    is_stable: bool
    is_critical: bool
    bifurcation_index: float
    near_bifurcation: bool
    has_limit_cycle: bool
    dominant_frequency: float
    attractor_dimension: float

    def to_dict(self) -> dict:
        return {
            "embedding_dim": self.embedding_dim,
            "embedding_tau": self.embedding_tau,
            "n_fixed_points": self.n_fixed_points,
            "fixed_point_radii": [round(r, 6) for r in self.fixed_point_radii],
            "lyapunov_estimate": round(self.lyapunov_estimate, 6),
            "is_chaotic": self.is_chaotic,
            "is_stable": self.is_stable,
            "is_critical": self.is_critical,
            "bifurcation_index": round(self.bifurcation_index, 4),
            "near_bifurcation": self.near_bifurcation,
            "has_limit_cycle": self.has_limit_cycle,
            "dominant_frequency": round(self.dominant_frequency, 6),
            "attractor_dimension": round(self.attractor_dimension, 4),
        }


# ── Main entry point ──────────────────────────────────────────────────────────

def analyse(
    phi: np.ndarray,
    embedding_dim: int = 3,
    tau: Optional[int] = None,
    lyapunov_max_iter: int = 20,
    seed: int = 42,
) -> Optional[DynamicsResult]:
    """
    Full phase-space analysis of a phi time series.

    Args:
        phi           : phi time series, at least 64 samples.
        embedding_dim : dimension of delay embedding (default 3).
        tau           : embedding delay; if None, uses first ACF zero crossing.
        lyapunov_max_iter : forward steps for Lyapunov estimate.
        seed          : RNG seed for k-means.

    Returns:
        DynamicsResult or None if phi is too short.
    """
    phi = np.asarray(phi, dtype=float)
    if phi.size < 64:
        return None

    # Delay embedding
    if tau is None:
        tau = _acf_zero_crossing(phi)
        tau = max(1, min(tau, len(phi) // (2 * embedding_dim)))
    embedded = embed(phi, m=embedding_dim, tau=tau)

    # Fixed points
    n_fp, radii = detect_fixed_points(embedded, seed=seed)

    # Lyapunov exponent
    lam = lyapunov_rosenstein(embedded, max_iter=lyapunov_max_iter)

    # Limit cycle
    has_cycle, dom_freq = detect_limit_cycle(phi)

    # Bifurcation index
    bif = bifurcation_index(phi)

    # Correlation dimension
    d_corr = correlation_dimension(embedded)

    return DynamicsResult(
        embedding_dim=embedding_dim,
        embedding_tau=tau,
        n_fixed_points=n_fp,
        fixed_point_radii=radii,
        lyapunov_estimate=lam,
        is_chaotic=lam > 0.01,
        is_stable=lam < -0.01,
        is_critical=abs(lam) <= 0.01,
        bifurcation_index=bif,
        near_bifurcation=bif > 0.7,
        has_limit_cycle=has_cycle,
        dominant_frequency=dom_freq,
        attractor_dimension=d_corr,
    )


def analyse_from_telemetry(**kwargs) -> Optional[DynamicsResult]:
    try:
        from runtime.state import phi_series, have_live_state
        if not have_live_state():
            return None
        phi = phi_series()
        if phi is None or phi.size < 64:
            return None
        return analyse(phi, **kwargs)
    except Exception:
        return None
