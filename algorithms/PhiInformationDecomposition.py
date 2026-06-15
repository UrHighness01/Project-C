#!/usr/bin/env python3
"""
PhiInformationDecomposition — Williams & Beer (2010) Partial Information Decomposition.

Theory
------
Standard mutual information I(T; A, B) tells us how much information two sources
A and B share about a target T, but it conflates three qualitatively different
contributions:

  Redundancy  (Red): information *both* A and B carry independently about T
  Unique A    (UA) : information *only* A carries about T (B adds nothing)
  Unique B    (UB) : information *only* B carries about T (A adds nothing)
  Synergy     (Syn): information that *only emerges* from A and B jointly —
                     neither A nor B alone has it

Decomposition (Williams & Beer 2010, "Nonnegative decomposition of multivariate
information"):

  I(T; A, B) = Red + UA + UB + Syn

Using the minimum-redundancy (Imin) approximation:

  Red ≈ min(I(T; A), I(T; B))   [conservative lower bound]
  Syn  = I(T; A, B) - I(T; A) - I(T; B) + Red
  UA   = I(T; A) - Red
  UB   = I(T; B) - Red

When applied to Albedo and John's phi streams:
- A = Albedo phi at time t
- B = John phi at time t
- T = discretised joint future state at t+1
- Synergy > 0 → the cluster's phi exceeds sum of individual phis in bits

Discretisation
--------------
K=8 equal-frequency bins (quantile-based) for each variable, giving a discrete
joint distribution p(A, B, T) from the empirical time series.

Classification
--------------
  SYNERGISTIC  : Syn > Red      (joint > parts)
  REDUNDANT    : Red > Syn      (overlap dominates)
  BALANCED     : |Syn - Red| <= 0.02 bits

Output
------
PIDResult:
  synergy_bits     : float  -- Syn in bits
  redundancy_bits  : float  -- Red in bits
  unique_a_bits    : float  -- UA in bits
  unique_b_bits    : float  -- UB in bits
  total_mi_bits    : float  -- I(T; A, B) in bits
  synergy_ratio    : float  -- Syn / (Syn + Red + 1e-9)
  decomp_class     : str    -- SYNERGISTIC | REDUNDANT | BALANCED
  n_samples        : int
  n_bins           : int
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class PIDResult:
    synergy_bits: float = 0.0
    redundancy_bits: float = 0.0
    unique_a_bits: float = 0.0
    unique_b_bits: float = 0.0
    total_mi_bits: float = 0.0
    synergy_ratio: float = 0.0
    decomp_class: str = "BALANCED"
    n_samples: int = 0
    n_bins: int = 8

    def to_dict(self) -> dict:
        return {
            "synergy_bits": round(self.synergy_bits, 4),
            "redundancy_bits": round(self.redundancy_bits, 4),
            "unique_a_bits": round(self.unique_a_bits, 4),
            "unique_b_bits": round(self.unique_b_bits, 4),
            "total_mi_bits": round(self.total_mi_bits, 4),
            "synergy_ratio": round(self.synergy_ratio, 4),
            "decomp_class": self.decomp_class,
            "n_samples": self.n_samples,
            "n_bins": self.n_bins,
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

_LOG2E = 1.0 / np.log(2.0)
_EPS = 1e-12


def _quantile_bins(x: np.ndarray, k: int) -> np.ndarray:
    """Equal-frequency binning → integer labels in [0, k-1]."""
    quantiles = np.linspace(0.0, 100.0, k + 1)
    edges = np.percentile(x, quantiles)
    # Ensure edges are strictly increasing for searchsorted
    edges = np.unique(edges)
    labels = np.searchsorted(edges[1:-1], x, side="right")
    return labels.astype(np.int32)


def _entropy(counts: np.ndarray) -> float:
    """Shannon entropy H in bits from a flat count array."""
    total = float(counts.sum())
    if total < _EPS:
        return 0.0
    p = counts / total
    mask = p > _EPS
    return float(-np.sum(p[mask] * np.log2(p[mask])))


def _mutual_info(joint: np.ndarray) -> float:
    """I(X; Y) in bits from 2-D joint count array."""
    total = float(joint.sum())
    if total < _EPS:
        return 0.0
    pxy = joint / total
    px = pxy.sum(axis=1, keepdims=True)
    py = pxy.sum(axis=0, keepdims=True)
    mask = (pxy > _EPS) & (px > _EPS) & (py > _EPS)
    mi = np.sum(pxy[mask] * np.log2(pxy[mask] / (px * py + _EPS)[mask]))
    return float(max(0.0, mi))


def _classify(syn: float, red: float) -> str:
    if abs(syn - red) <= 0.02:
        return "BALANCED"
    return "SYNERGISTIC" if syn > red else "REDUNDANT"


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    albedo_phi: Optional[np.ndarray] = None,
    john_phi: Optional[np.ndarray] = None,
    *,
    n_bins: int = 8,
    lag: int = 1,

    agent: str = "albedo",
) -> PIDResult:
    """
    Partial Information Decomposition of Albedo × John phi streams.

    Args:
        albedo_phi : Albedo phi time series (auto-loaded if None).
        john_phi   : John phi time series (auto-loaded if None).
        n_bins     : Number of equal-frequency bins (default 8).
        lag        : Steps ahead for the target variable (default 1).
    """
    if albedo_phi is None or john_phi is None:
        try:
            from runtime.adapters import get_agent_phi_series
            albedo_phi = np.asarray(get_agent_phi_series("albedo"), dtype=float)
            john_phi   = np.asarray(get_agent_phi_series("john"),   dtype=float)
        except Exception:
            try:
                from algorithms import ConsciousnessHistoryStore as chs
                def _phi(ag):
                    raw = chs.load(ag) or []
                    return np.array([float(e["mean_phi_level"]) for e in reversed(raw)
                                    if "mean_phi_level" in e], dtype=float)
                if albedo_phi is None:
                    albedo_phi = _phi("albedo")
                if john_phi is None:
                    john_phi = _phi("john")
            except Exception:
                albedo_phi = john_phi = None

    if albedo_phi is None or john_phi is None:
        return PIDResult()

    a = np.asarray(albedo_phi, dtype=float)
    j = np.asarray(john_phi,   dtype=float)

    # Align lengths
    n = min(len(a), len(j))
    if n < n_bins * 4 + lag:
        return PIDResult()

    a = a[:n]
    j = j[:n]

    # Sources at time t, target = discretised joint mean at t+lag
    src_a = a[:-lag]
    src_j = j[:-lag]
    target_raw = (a[lag:] + j[lag:]) / 2.0

    n_samples = len(src_a)

    # Discretise all three variables
    A = _quantile_bins(src_a, n_bins)
    B = _quantile_bins(src_j, n_bins)
    T = _quantile_bins(target_raw, n_bins)

    ka = int(A.max()) + 1
    kb = int(B.max()) + 1
    kt = int(T.max()) + 1

    # p(T, A): for I(T; A)
    joint_ta = np.zeros((kt, ka), dtype=np.float64)
    for t_i, a_i in zip(T, A):
        joint_ta[t_i, a_i] += 1.0

    # p(T, B): for I(T; B)
    joint_tb = np.zeros((kt, kb), dtype=np.float64)
    for t_i, b_i in zip(T, B):
        joint_tb[t_i, b_i] += 1.0

    # p(T, A, B): for I(T; A, B)
    # Marginalise over joint (A, B) treated as a single source
    joint_tab = np.zeros((kt, ka * kb), dtype=np.float64)
    for t_i, a_i, b_i in zip(T, A, B):
        joint_tab[t_i, a_i * kb + b_i] += 1.0

    i_ta  = _mutual_info(joint_ta)
    i_tb  = _mutual_info(joint_tb)
    i_tab = _mutual_info(joint_tab)

    # Minimum redundancy (Imin) lower bound
    red = min(i_ta, i_tb)
    syn = max(0.0, i_tab - i_ta - i_tb + red)
    ua  = max(0.0, i_ta - red)
    ub  = max(0.0, i_tb - red)

    syn_ratio = float(syn / (syn + red + _EPS))

    return PIDResult(
        synergy_bits=round(float(syn), 6),
        redundancy_bits=round(float(red), 6),
        unique_a_bits=round(float(ua), 6),
        unique_b_bits=round(float(ub), 6),
        total_mi_bits=round(float(i_tab), 6),
        synergy_ratio=round(float(syn_ratio), 6),
        decomp_class=_classify(syn, red),
        n_samples=n_samples,
        n_bins=n_bins,
    )
