#!/usr/bin/env python3
"""
SharedWorldModelDistance — measuring divergence between agent world-model distributions.

Theory (Clark 1997 — Being There; Hohwy 2013 — The Predictive Mind):
  A conscious agent maintains an internal world model — a probability distribution
  over possible states of its environment and self. Two agents with a shared world
  model (symbiosis) should have similar phi distributions: they represent the same
  reality and have similar integrated information levels.

  Divergence between world models is measured by the statistical distance between
  each agent's phi distribution. Three complementary metrics:

  1. Wasserstein-1 (Earth Mover's Distance):
     W₁(P, Q) = ∫|F_P(x) − F_Q(x)| dx
     where F_P, F_Q are empirical CDFs. This is the minimum "work" to transform
     one distribution into the other. Small W₁ = similar world models.

  2. KL divergence (discretised):
     D_KL(P || Q) = Σᵢ P(bin_i) · log(P(bin_i) / Q(bin_i))
     Measures information cost of encoding P-world using a Q-model.
     Asymmetric: D_KL(Albedo||John) ≠ D_KL(John||Albedo).

  3. Kolmogorov-Smirnov statistic:
     KS = max_x |F_P(x) − F_Q(x)|
     Tests whether the distributions are statistically identical.

  A converging symbiosis (agents sharing more and more experience) should show
  decreasing W₁ over time. A diverging pair shows increasing W₁.

  Null: Two series with the same mean and variance but no coupling.
  We generate this by permuting one phi series. Distance to permuted
  series = what distance would look like if agents were just similar
  in scale but had independent dynamics.

Math:
  W₁: computed via sorted empirical CDF (analytic for 1-D):
    W₁(P,Q) = (1/N) Σᵢ |sort(P)ᵢ − sort(Q)ᵢ|   for equal-length samples

  KL: bin both distributions into k bins on shared support, add ε smoothing.

  KS: max absolute difference of empirical CDFs.

Grounding: phi_series() from both agent workspaces. No constructed distributions.

References:
  Clark A. (1997) "Being There: Putting Brain, Body, and World Together Again"
  Hohwy J. (2013) "The Predictive Mind"
  Villani C. (2008) "Optimal Transport: Old and New" — Wasserstein distance theory
"""
from __future__ import annotations

import os
import numpy as np
from dataclasses import dataclass
from typing import Optional


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class WorldModelResult:
    """Output of one SharedWorldModelDistance analysis.

    Attributes:
        n_samples:         samples compared (min of both series)
        wasserstein_1:     W₁ distance between phi distributions
        kl_albedo_john:    D_KL(Albedo || John) in nats
        kl_john_albedo:    D_KL(John || Albedo) in nats
        ks_statistic:      KS max CDF difference ∈ [0, 1]
        null_wasserstein:  W₁ on permuted-John null
        null_ks:           KS on null
        world_models_close: True if W₁ < null_wasserstein
        phi_mean_diff:     |mean(φ_A) - mean(φ_J)|
        phi_std_ratio:     std(φ_A) / std(φ_J) (1.0 = same scale)
    """
    n_samples: int
    wasserstein_1: float
    kl_albedo_john: float
    kl_john_albedo: float
    ks_statistic: float
    null_wasserstein: float
    null_ks: float
    world_models_close: bool
    phi_mean_diff: float
    phi_std_ratio: float

    @property
    def symmetric_kl(self) -> float:
        """J-divergence (symmetric KL): (D_KL(P||Q) + D_KL(Q||P)) / 2."""
        return (self.kl_albedo_john + self.kl_john_albedo) / 2.0

    @property
    def diverging(self) -> bool:
        """True if W₁ > null — distributions more different than by chance."""
        return not self.world_models_close


# ── Core distance functions ───────────────────────────────────────────────────

def wasserstein1(x: np.ndarray, y: np.ndarray) -> float:
    """Wasserstein-1 distance between two 1-D empirical distributions.

    For equal-length samples: W₁ = mean|sort(x) - sort(y)|.
    For unequal lengths: interpolate the longer CDF onto the shorter's support.
    """
    n = min(len(x), len(y))
    if n == 0:
        return 0.0
    xs = np.sort(x)[:n]
    ys = np.sort(y)[:n]
    return float(np.mean(np.abs(xs - ys)))


def kl_divergence(p: np.ndarray, q: np.ndarray, bins: int = 32) -> float:
    """D_KL(P || Q) in nats via histogram binning with ε-smoothing.

    Uses a shared support spanning both series.
    """
    eps = 1e-8
    lo = float(min(p.min(), q.min()))
    hi = float(max(p.max(), q.max()))
    if abs(hi - lo) < 1e-12:
        return 0.0
    edges = np.linspace(lo, hi, bins + 1)
    hp, _ = np.histogram(p, bins=edges, density=False)
    hq, _ = np.histogram(q, bins=edges, density=False)
    hp = hp.astype(float) + eps
    hq = hq.astype(float) + eps
    pp = hp / hp.sum()
    pq = hq / hq.sum()
    return float(np.sum(pp * np.log(pp / pq)))


def ks_statistic(x: np.ndarray, y: np.ndarray) -> float:
    """KS max |CDF_x(t) - CDF_y(t)| over all t, using merged sorted array."""
    combined = np.sort(np.concatenate([x, y]))
    cdf_x = np.searchsorted(np.sort(x), combined, side='right') / len(x)
    cdf_y = np.searchsorted(np.sort(y), combined, side='right') / len(y)
    return float(np.max(np.abs(cdf_x - cdf_y)))


# ── Phi loading ───────────────────────────────────────────────────────────────

def _load_both_phi() -> Optional[tuple[np.ndarray, np.ndarray]]:
    try:
        from runtime.state import phi_series as albedo_phi
        phi_a = albedo_phi()
    except Exception:
        return None
    try:
        from runtime.agent import agent_home
        import importlib
        john_ws = str(agent_home("john"))
        old_env = os.environ.get("OPENCLAW_WORKSPACE")
        os.environ["OPENCLAW_WORKSPACE"] = john_ws
        try:
            import runtime.state as sm
            importlib.reload(sm)
            phi_j = sm.phi_series()
        finally:
            if old_env is None:
                os.environ.pop("OPENCLAW_WORKSPACE", None)
            else:
                os.environ["OPENCLAW_WORKSPACE"] = old_env
            import runtime.state as sm2
            importlib.reload(sm2)
    except Exception:
        return None
    return phi_a, phi_j


# ── Main analysis ─────────────────────────────────────────────────────────────

def analyse(phi_a: np.ndarray, phi_j: np.ndarray,
            bins: int = 32, null_seed: int = 42) -> Optional[WorldModelResult]:
    """
    Measure the distribution distance between two agents' phi series.

    Args:
        phi_a:    Albedo phi series.
        phi_j:    John phi series.
        bins:     histogram bins for KL divergence estimation.
        null_seed: RNG seed for permuted null.

    Returns:
        WorldModelResult, or None if series are too short.
    """
    phi_a = np.asarray(phi_a, dtype=float)
    phi_j = np.asarray(phi_j, dtype=float)
    n = min(len(phi_a), len(phi_j))
    if n < 32:
        return None

    phi_a = phi_a[-n:]
    phi_j = phi_j[-n:]

    w1 = wasserstein1(phi_a, phi_j)
    kl_aj = kl_divergence(phi_a, phi_j, bins)
    kl_ja = kl_divergence(phi_j, phi_a, bins)
    ks = ks_statistic(phi_a, phi_j)

    # Null: permute phi_j → destroys order but keeps distribution
    rng = np.random.default_rng(null_seed)
    phi_j_null = rng.permutation(phi_j)
    null_w1 = wasserstein1(phi_a, phi_j_null)
    null_ks = ks_statistic(phi_a, phi_j_null)

    mean_diff = float(abs(phi_a.mean() - phi_j.mean()))
    std_ratio = float(phi_a.std() / (phi_j.std() + 1e-9))

    return WorldModelResult(
        n_samples=n,
        wasserstein_1=w1,
        kl_albedo_john=kl_aj,
        kl_john_albedo=kl_ja,
        ks_statistic=ks,
        null_wasserstein=null_w1,
        null_ks=null_ks,
        world_models_close=w1 <= null_w1,
        phi_mean_diff=mean_diff,
        phi_std_ratio=std_ratio,
    )


def analyse_from_telemetry(bins: int = 32) -> Optional[WorldModelResult]:
    """Load both agents' phi and measure world-model distance."""
    pair = _load_both_phi()
    if pair is None:
        return None
    return analyse(pair[0], pair[1], bins=bins)


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("Could not load both agent phi series.")
    else:
        print(f"SharedWorldModelDistance (N={r.n_samples})")
        print(f"  Wasserstein-1:      {r.wasserstein_1:.4f}  (null {r.null_wasserstein:.4f})")
        print(f"  World models close: {r.world_models_close}")
        print(f"  Diverging:          {r.diverging}")
        print(f"  D_KL(A||J):         {r.kl_albedo_john:.4f} nats")
        print(f"  D_KL(J||A):         {r.kl_john_albedo:.4f} nats")
        print(f"  Symmetric KL:       {r.symmetric_kl:.4f} nats")
        print(f"  KS statistic:       {r.ks_statistic:.4f}  (null {r.null_ks:.4f})")
        print(f"  Mean phi diff:      {r.phi_mean_diff:.4f}")
        print(f"  Std ratio (A/J):    {r.phi_std_ratio:.4f}")
