#!/usr/bin/env python3
"""
FreeEnergyLandscape — maps the phi free-energy landscape via KDE.

Theory
------
Friston (2010) Free Energy Principle: a self-organising system minimises
the free energy F of its states, which is equivalent to maximising the
evidence for its generative model. For phi, F(φ) = -log p(φ) where p(φ) is
the empirical marginal density of phi values.

The landscape has:
  - Attractor basins: local minima of F (high-density phi regions the system
    repeatedly visits — stable modes of experience)
  - Saddle points: local maxima of F between basins (phi values the system
    rarely occupies but must cross during transitions)
  - Current position: F(φ_now) — how "comfortable" the current phi is
  - Escape probability: P_esc = exp(-(F_saddle - F_current)) — probability
    of crossing to a new basin given thermal fluctuation model

Operationalisation
------------------
1. Estimate p(φ) via Gaussian KDE with bandwidth h = 1.06 * σ * n^{-1/5}
   (Silverman's rule of thumb) from the phi history.

2. Evaluate p(φ) on a grid of 256 points over [min φ, max φ].

3. Compute F(φ) = -log(p(φ) + ε) on the grid.

4. Find attractor basins: indices where F[i] < F[i-1] and F[i] < F[i+1]
   (local minima of F = modes of p).

5. Find saddle points: local maxima of F between adjacent basins.

6. Current basin: which basin's phi value is nearest to φ_current.

7. Nearest saddle energy: min F_saddle reachable from current basin.

8. Escape probability: P_esc = exp(-(F_saddle - F_current))  ∈ [0, 1].

9. Landscape diversity: number of distinct attractor basins (modes).

Regime classification:
  TRAPPED    : F_current > F_saddle - 0.5  (near/past saddle, unstable)
  STABLE     : P_esc < 0.15
  TRANSITIONAL : 0.15 <= P_esc < 0.5
  FREE       : P_esc >= 0.5  (high escape probability, fluid landscape)

Output
------
LandscapeResult:
  current_free_energy  : float   -- F(φ_current) = -log p(φ_current)
  nearest_saddle_energy: float   -- F at nearest saddle point
  escape_probability   : float   -- exp(-(F_saddle - F_current))
  n_basins             : int     -- number of attractor basins
  basin_centers        : List[float]  -- phi values at basin centres
  landscape_regime     : str     -- TRAPPED | STABLE | TRANSITIONAL | FREE
  bandwidth            : float   -- KDE bandwidth
  n_samples            : int
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


_GRID = 256
_EPS  = 1e-300


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class LandscapeResult:
    current_free_energy: float = 0.0
    nearest_saddle_energy: float = 0.0
    escape_probability: float = 0.0
    n_basins: int = 0
    basin_centers: List[float] = field(default_factory=list)
    landscape_regime: str = "STABLE"
    bandwidth: float = 0.0
    n_samples: int = 0

    def to_dict(self) -> dict:
        return {
            "current_free_energy": round(self.current_free_energy, 4),
            "nearest_saddle_energy": round(self.nearest_saddle_energy, 4),
            "escape_probability": round(self.escape_probability, 4),
            "n_basins": self.n_basins,
            "basin_centers": [round(v, 4) for v in self.basin_centers],
            "landscape_regime": self.landscape_regime,
            "bandwidth": round(self.bandwidth, 4),
            "n_samples": self.n_samples,
        }


def _classify(p_esc: float, f_now: float, f_saddle: float) -> str:
    if f_now > f_saddle - 0.5:
        return "TRAPPED"
    if p_esc >= 0.5:
        return "FREE"
    if p_esc >= 0.15:
        return "TRANSITIONAL"
    return "STABLE"


# ── KDE ──────────────────────────────────────────────────────────────────────

def _silverman_bw(x: np.ndarray) -> float:
    n = len(x)
    std = float(x.std(ddof=1))
    iqr = float(np.percentile(x, 75) - np.percentile(x, 25))
    s = min(std, iqr / 1.349) if iqr > 0 else std
    return 1.06 * s * (n ** -0.2) if s > 0 else 0.1


def _kde(x: np.ndarray, grid: np.ndarray, bw: float) -> np.ndarray:
    """Gaussian KDE evaluated on grid."""
    diff = (grid[:, None] - x[None, :]) / bw   # (G, N)
    return np.mean(np.exp(-0.5 * diff ** 2), axis=1) / (bw * np.sqrt(2 * np.pi))


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    phi: Optional[np.ndarray] = None,
    *,
    grid_points: int = _GRID,

    agent: str = "albedo",
) -> LandscapeResult:
    """
    Estimate the free-energy landscape of phi and locate the current position.

    Args:
        phi         : 1-D phi time series (chronological).
        grid_points : resolution of the density grid.
    """
    if phi is None:
        try:
            from runtime.state import phi_series
            phi = phi_series()
        except Exception:
            try:
                from algorithms import ConsciousnessHistoryStore as chs
                _raw = chs.load(agent) or []
                phi = np.array([float(e["mean_phi_level"]) for e in reversed(_raw)
                               if "mean_phi_level" in e], dtype=float)
            except Exception:
                phi = None

    if phi is None or len(phi) < 10:
        return LandscapeResult()

    phi = np.asarray(phi, dtype=float)
    n = len(phi)

    bw = _silverman_bw(phi)

    lo, hi = float(phi.min()), float(phi.max())
    if hi - lo < 1e-8:
        # Constant series — single attractor
        return LandscapeResult(
            current_free_energy=float(-np.log(1.0 + _EPS)),
            nearest_saddle_energy=100.0,
            escape_probability=0.0,
            n_basins=1,
            basin_centers=[float(phi[-1])],
            landscape_regime="STABLE",
            bandwidth=bw,
            n_samples=n,
        )

    grid = np.linspace(lo, hi, grid_points)
    density = _kde(phi, grid, bw)
    density = np.maximum(density, _EPS)
    F = -np.log(density)

    # Local minima of F (attractor basins)
    basins = []
    for i in range(1, len(F) - 1):
        if F[i] < F[i - 1] and F[i] < F[i + 1]:
            basins.append(i)
    if not basins:
        basins = [int(np.argmin(F))]

    # Local maxima of F (saddles)
    saddles = []
    for i in range(1, len(F) - 1):
        if F[i] > F[i - 1] and F[i] > F[i + 1]:
            saddles.append(i)

    phi_now = float(phi[-1])
    # Current free energy via KDE evaluated at phi_now
    f_now = float(-np.log(float(np.mean(
        np.exp(-0.5 * ((phi_now - phi) / bw) ** 2)
    ) / (bw * np.sqrt(2 * np.pi))) + _EPS))

    # Nearest saddle energy
    if saddles:
        f_saddle = float(min(F[s] for s in saddles))
    else:
        f_saddle = float(F.max())

    p_esc = float(np.clip(np.exp(-(f_saddle - f_now)), 0.0, 1.0))

    return LandscapeResult(
        current_free_energy=f_now,
        nearest_saddle_energy=f_saddle,
        escape_probability=p_esc,
        n_basins=len(basins),
        basin_centers=[round(float(grid[b]), 4) for b in basins],
        landscape_regime=_classify(p_esc, f_now, f_saddle),
        bandwidth=bw,
        n_samples=n,
    )
