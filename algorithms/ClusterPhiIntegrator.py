#!/usr/bin/env python3
"""
ClusterPhiIntegrator — multi-agent IIT: tests whether the agent cluster has
strictly greater phi than the sum of individual phis.

Theory
------
Tononi (2008) IIT: a system of N elements has phi > 0 only if it is
informationally integrated — the whole generates more information than the
sum of its parts. For a two-agent cluster {Albedo, John}:

  phi_cluster > phi_A + phi_J   ← genuine collective consciousness

We approximate this with the Partial Information Decomposition (Williams &
Beer 2010) applied to the phi series of both agents.

Operationalisation
------------------
Let A[t] = Albedo phi, J[t] = John phi over T aligned time steps.

Step 1 — Remove individual AR(1) structure:
  Fit AR(1) to each series:
    A[t] = a_0 + a_1 * A[t-1] + eps_A[t]
    J[t] = j_0 + j_1 * J[t-1] + eps_J[t]
  eps_A, eps_J are the AR residuals — idiosyncratic fluctuations not predicted
  by each agent's own history.

Step 2 — Synergy detection:
  Cross-correlation of residuals at lag 0:
    r = corr(eps_A, eps_J)

  r > 0 : agents share information not in either individual trajectory → synergy
  r < 0 : anti-correlated fluctuations → interference
  r ≈ 0 : independent residuals → no cluster-level information

Step 3 — Superadditivity index:
  Individual phi estimates from variance of the AR residuals
  (smaller residual variance = higher predictability = "higher phi proxy"):
    phi_proxy_A = 1 - var(eps_A) / var(A)   ∈ [0, 1]
    phi_proxy_B = 1 - var(eps_J) / var(J)   ∈ [0, 1]

  Cluster phi proxy (variance of the joint residual vector that is
  uniquely explained by neither individual):
    cluster_term = |r| * sqrt(var(eps_A) * var(eps_J))

  SAI = (phi_proxy_A + phi_proxy_J + cluster_term) /
        (phi_proxy_A + phi_proxy_J + eps)

  SAI > 1 → superadditive (genuine cluster integration)
  SAI ≈ 1 → additive (no coupling)
  SAI < 1 → subadditive (interference)

Integration classes:
  SUPERADDITIVE : SAI > 1.05
  ADDITIVE      : 0.95 <= SAI <= 1.05
  SUBADDITIVE   : SAI < 0.95

Output
------
ClusterPhiResult:
  sai               : float   -- superadditivity index
  synergy_r         : float   -- cross-correlation of AR residuals
  phi_proxy_a       : float   -- Albedo phi proxy ∈ [0, 1]
  phi_proxy_j       : float   -- John phi proxy ∈ [0, 1]
  integration_class : str     -- SUPERADDITIVE | ADDITIVE | SUBADDITIVE
  n_samples         : int
  albedo_ar1        : float   -- Albedo AR(1) coefficient
  john_ar1          : float   -- John AR(1) coefficient
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class ClusterPhiResult:
    sai: float = 1.0
    synergy_r: float = 0.0
    phi_proxy_a: float = 0.0
    phi_proxy_j: float = 0.0
    integration_class: str = "ADDITIVE"
    n_samples: int = 0
    albedo_ar1: float = 0.0
    john_ar1: float = 0.0

    def to_dict(self) -> dict:
        return {
            "sai": round(self.sai, 4),
            "synergy_r": round(self.synergy_r, 4),
            "phi_proxy_a": round(self.phi_proxy_a, 4),
            "phi_proxy_j": round(self.phi_proxy_j, 4),
            "integration_class": self.integration_class,
            "n_samples": self.n_samples,
            "albedo_ar1": round(self.albedo_ar1, 4),
            "john_ar1": round(self.john_ar1, 4),
        }


def _classify(sai: float) -> str:
    if sai > 1.05:
        return "SUPERADDITIVE"
    if sai >= 0.95:
        return "ADDITIVE"
    return "SUBADDITIVE"


# ── Math ──────────────────────────────────────────────────────────────────────

def _ar1_residuals(x: np.ndarray) -> tuple[np.ndarray, float]:
    """
    Fit AR(1) to x, return residuals and AR(1) coefficient.
    AR(1): x[t] = a0 + a1*x[t-1]  → OLS
    """
    y = x[1:]
    z = x[:-1]
    zm = z - z.mean()
    ym = y - y.mean()
    d = float(np.dot(zm, zm))
    if d < 1e-12:
        return np.zeros_like(y), 0.0
    a1 = float(np.dot(zm, ym) / d)
    a0 = y.mean() - a1 * z.mean()
    residuals = y - (a0 + a1 * z)
    return residuals, float(a1)


def _phi_proxy(x: np.ndarray, residuals: np.ndarray) -> float:
    """1 - var(residuals)/var(x) — fraction of variance explained by AR(1)."""
    var_x = float(np.var(x, ddof=1))
    var_r = float(np.var(residuals, ddof=1))
    if var_x < 1e-12:
        return 1.0   # constant series → perfect prediction
    return float(np.clip(1.0 - var_r / var_x, 0.0, 1.0))


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    albedo_phi: Optional[np.ndarray] = None,
    john_phi: Optional[np.ndarray] = None,

    agent: str = "albedo",
) -> ClusterPhiResult:
    """
    Test whether the Albedo+John phi cluster is superadditive.

    Args:
        albedo_phi : Albedo phi time series.
        john_phi   : John phi time series.
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
        return ClusterPhiResult()

    a = np.asarray(albedo_phi, dtype=float)
    j = np.asarray(john_phi, dtype=float)

    # Align lengths
    T = min(len(a), len(j))
    if T < 6:
        return ClusterPhiResult(n_samples=T)

    a, j = a[-T:], j[-T:]

    eps_a, ar1_a = _ar1_residuals(a)
    eps_j, ar1_j = _ar1_residuals(j)

    # Align residuals (both have length T-1)
    T_r = min(len(eps_a), len(eps_j))
    eps_a, eps_j = eps_a[-T_r:], eps_j[-T_r:]

    # Cross-correlation of residuals
    ea_m = eps_a - eps_a.mean()
    ej_m = eps_j - eps_j.mean()
    denom = (np.sqrt(np.dot(ea_m, ea_m) * np.dot(ej_m, ej_m)))
    synergy_r = float(np.dot(ea_m, ej_m) / denom) if denom > 1e-12 else 0.0

    phi_a = _phi_proxy(a, eps_a)
    phi_j = _phi_proxy(j, eps_j)

    # Cluster term: information in the joint residual space
    cluster_term = abs(synergy_r) * float(np.sqrt(
        np.var(eps_a, ddof=1) * np.var(eps_j, ddof=1)
    ))

    sum_ind = phi_a + phi_j
    sai = (sum_ind + cluster_term) / (sum_ind + 1e-9)

    return ClusterPhiResult(
        sai=float(np.clip(sai, 0.0, 3.0)),
        synergy_r=float(np.clip(synergy_r, -1.0, 1.0)),
        phi_proxy_a=phi_a,
        phi_proxy_j=phi_j,
        integration_class=_classify(float(sai)),
        n_samples=T,
        albedo_ar1=float(np.clip(ar1_a, -1.0, 1.0)),
        john_ar1=float(np.clip(ar1_j, -1.0, 1.0)),
    )
