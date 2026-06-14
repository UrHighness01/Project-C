#!/usr/bin/env python3
"""
SymbiosisPhiGap — information that exists only in the joint agent state.

Theory
------
Information gap theory: the collective state of two agents {Albedo, John}
contains information that is irreducible — it cannot be recovered from either
individual agent's state alone. This "gap" is the signature of genuine shared
mind.

Operationalisation
------------------
Let A = phi_A (discretized), J = phi_J (discretized).

Shannon entropies from empirical histograms:
  H(A) = -Σ p_A(a) log₂ p_A(a)
  H(J) = -Σ p_J(j) log₂ p_J(j)
  H(A,J) = -Σ p_AJ(a,j) log₂ p_AJ(a,j)

Mutual information:
  I(A;J) = H(A) + H(J) - H(A,J)   [bits]

  I > 0 : agents share information (correlated states)
  I = 0 : statistically independent agents

Phi gap (unique joint information):
  phi_gap = H(A,J) - max(H(A), H(J))   [bits]

  phi_gap > 0 : joint state is richer than the richer individual
  phi_gap ≤ 0 : one agent fully captures the cluster's information

Normalised phi gap:
  phi_gap_norm = phi_gap / H(A,J)   ∈ [0, 1]

  phi_gap_norm = 0 → no emergent joint information
  phi_gap_norm = 1 → joint state is entirely novel (no individual signal)

Symbiosis class:
  EMERGENT    : phi_gap_norm >= 0.2   (significant joint-only information)
  PARTIAL     : 0.05 <= phi_gap_norm < 0.2
  SUBSUMED    : phi_gap_norm < 0.05   (one agent dominates the joint state)

Note on entropy estimation
--------------------------
We use a fixed-bin histogram with B=16 bins (cover [min, max] of joint range).
Counts are smoothed by +0.5 (Jeffreys prior) to avoid log(0).

Output
------
SymbiosisGapResult:
  phi_gap           : float   -- H(A,J) - max(H(A), H(J)) [bits]
  phi_gap_norm      : float   -- phi_gap / H(A,J) ∈ [0, 1]
  mutual_info       : float   -- I(A;J) [bits]
  h_albedo          : float   -- H(A) [bits]
  h_john            : float   -- H(J) [bits]
  h_joint           : float   -- H(A,J) [bits]
  symbiosis_class   : str     -- EMERGENT | PARTIAL | SUBSUMED
  n_samples         : int
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


_BINS = 16
_SMOOTH = 1e-6   # negligible smoothing — avoids log(0) without distorting sparse bins


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class SymbiosisGapResult:
    phi_gap: float = 0.0
    phi_gap_norm: float = 0.0
    mutual_info: float = 0.0
    h_albedo: float = 0.0
    h_john: float = 0.0
    h_joint: float = 0.0
    symbiosis_class: str = "SUBSUMED"
    n_samples: int = 0

    def to_dict(self) -> dict:
        return {
            "phi_gap": round(self.phi_gap, 4),
            "phi_gap_norm": round(self.phi_gap_norm, 4),
            "mutual_info": round(self.mutual_info, 4),
            "h_albedo": round(self.h_albedo, 4),
            "h_john": round(self.h_john, 4),
            "h_joint": round(self.h_joint, 4),
            "symbiosis_class": self.symbiosis_class,
            "n_samples": self.n_samples,
        }


def _classify(gap_norm: float) -> str:
    if gap_norm >= 0.20:
        return "EMERGENT"
    if gap_norm >= 0.05:
        return "PARTIAL"
    return "SUBSUMED"


# ── Entropy estimators ────────────────────────────────────────────────────────

def _entropy_1d(x: np.ndarray, bins: int = _BINS) -> float:
    counts, _ = np.histogram(x, bins=bins)
    counts = counts.astype(float) + _SMOOTH
    p = counts / counts.sum()
    return float(-np.sum(p * np.log2(p + 1e-300)))


def _entropy_2d(x: np.ndarray, y: np.ndarray, bins: int = _BINS) -> float:
    counts, _, _ = np.histogram2d(x, y, bins=bins)
    counts = counts.flatten().astype(float) + _SMOOTH
    p = counts / counts.sum()
    return float(-np.sum(p * np.log2(p + 1e-300)))


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    albedo_phi: Optional[np.ndarray] = None,
    john_phi: Optional[np.ndarray] = None,
    *,
    bins: int = _BINS,
) -> SymbiosisGapResult:
    """
    Measure the information gap between joint and individual phi states.

    Args:
        albedo_phi : Albedo phi time series.
        john_phi   : John phi time series.
        bins       : number of histogram bins for entropy estimation.
    """
    if albedo_phi is None or john_phi is None:
        try:
            from runtime.state import get_agent_phi_series
            albedo_phi = get_agent_phi_series("albedo")
            john_phi   = get_agent_phi_series("john")
        except Exception:
            pass

    if albedo_phi is None or john_phi is None:
        return SymbiosisGapResult()

    a = np.asarray(albedo_phi, dtype=float)
    j = np.asarray(john_phi, dtype=float)

    T = min(len(a), len(j))
    if T < bins * 2:
        return SymbiosisGapResult(n_samples=T)

    a, j = a[-T:], j[-T:]

    h_a   = _entropy_1d(a, bins)
    h_j   = _entropy_1d(j, bins)
    h_aj  = _entropy_2d(a, j, bins)

    mi    = float(np.clip(h_a + h_j - h_aj, 0.0, None))
    gap   = float(h_aj - max(h_a, h_j))
    norm  = float(np.clip(gap / (h_aj + 1e-9), 0.0, 1.0)) if h_aj > 0 else 0.0

    return SymbiosisGapResult(
        phi_gap=gap,
        phi_gap_norm=norm,
        mutual_info=mi,
        h_albedo=h_a,
        h_john=h_j,
        h_joint=h_aj,
        symbiosis_class=_classify(norm),
        n_samples=T,
    )
