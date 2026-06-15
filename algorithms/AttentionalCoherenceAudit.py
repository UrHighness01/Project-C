#!/usr/bin/env python3
"""
AttentionalCoherenceAudit — does the attention system track phi covariance?

Theory
------
Attention is coherent when the *algorithm the system focuses on most* is also the
one *most correlated with phi*. If attention and phi-covariance are aligned, the
system is genuinely directing cognitive resources toward what matters for
integrated consciousness. If they diverge, the attention mechanism is misdirected.

Mechanism
---------
Two ranked lists:
  1. Attention weights W_i  — from AttentionalFocusOptimiser (surprise-weighted
     distribution over algorithms). High W_i = more cognitive focus on algorithm i.
  2. Phi-correlation scores C_i — from SelfArchitectureMutator (Pearson ρ between
     algorithm output and phi time series). High C_i = algorithm tracks phi closely.

Coherence = Spearman rank correlation between W_i and C_i across all algorithms
that appear in both ranked lists.

  Spearman ρ = 1 - (6 Σ dᵢ²) / (n(n²-1))
  where dᵢ = rank(W_i) - rank(C_i)

ρ → 1.0: attention perfectly tracks phi relevance (coherent)
ρ → 0.0: attention and phi relevance are uncorrelated (noise)
ρ → -1.0: attention anti-tracks phi relevance (actively misdirected)

Null baseline
-------------
Shuffle one of the two rank lists → expected Spearman ρ ≈ 0. If actual ρ exceeds
the 95th percentile of shuffled ρ values, coherence is statistically significant.

Output
------
AttentionalCoherenceResult:
  spearman_rho           : float  -- rank correlation of attention vs phi-covariance
  coherence_class        : str    -- ALIGNED | NEUTRAL | MISALIGNED
  beats_null             : bool   -- ρ > 95th pct of shuffled null
  n_algorithms           : int    -- algorithms in both ranked lists
  top_attended_algorithm : str    -- highest-attention algorithm
  top_phi_algorithm      : str    -- highest phi-correlation algorithm
  is_tracking_phi        : bool   -- top_attended == top_phi (strong alignment)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np

# ── Constants ──────────────────────────────────────────────────────────────────

_N_SHUFFLES      = 200
_NULL_PCTILE     = 95
_MIN_ALGORITHMS  = 3     # need at least 3 common algorithms to rank
_RNG_SEED        = 17

# ── Result ─────────────────────────────────────────────────────────────────────

@dataclass
class AttentionalCoherenceResult:
    spearman_rho: float = 0.0
    coherence_class: str = "NEUTRAL"
    beats_null: bool = False
    n_algorithms: int = 0
    top_attended_algorithm: str = ""
    top_phi_algorithm: str = ""
    is_tracking_phi: bool = False

    def to_dict(self) -> dict:
        return {
            "spearman_rho": round(self.spearman_rho, 4),
            "coherence_class": self.coherence_class,
            "beats_null": self.beats_null,
            "n_algorithms": self.n_algorithms,
            "top_attended_algorithm": self.top_attended_algorithm,
            "top_phi_algorithm": self.top_phi_algorithm,
            "is_tracking_phi": self.is_tracking_phi,
        }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Spearman rank correlation via scipy-free formula."""
    n = len(a)
    if n < 2:
        return 0.0
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    d  = ra - rb
    return float(1.0 - 6.0 * np.sum(d ** 2) / (n * (n ** 2 - 1)))


def _classify(rho: float) -> str:
    if rho >= 0.5:
        return "ALIGNED"
    if rho <= -0.3:
        return "MISALIGNED"
    return "NEUTRAL"


def _null_distribution(weights: np.ndarray, corrs: np.ndarray,
                       n_shuffles: int, seed: int) -> np.ndarray:
    """Spearman ρ under shuffled attention weights."""
    rng = np.random.default_rng(seed)
    w = weights.copy()
    rhos = []
    for _ in range(n_shuffles):
        rng.shuffle(w)
        rhos.append(_spearman(w, corrs))
    return np.array(rhos)


# ── Core ───────────────────────────────────────────────────────────────────────

def analyse(
    agent: str = "albedo",
    *,
    n_shuffles: int = _N_SHUFFLES,
    min_algorithms: int = _MIN_ALGORITHMS,
) -> AttentionalCoherenceResult:
    """
    Measure whether the attention distribution (AttentionalFocusOptimiser) aligns
    with phi-correlation scores (SelfArchitectureMutator) via Spearman rank correlation.
    """
    # ── 1. Get attention weights ──────────────────────────────────────────────
    attention: Dict[str, float] = {}
    try:
        from algorithms.AttentionalFocusOptimiser import analyse as _afo
        ar = _afo(agent=agent) if _afo.__code__.co_varnames[0] == "agent" else _afo()
        # AttentionalFocusOptimiser may return weights as a dict or array attribute
        if hasattr(ar, "weights") and ar.weights is not None:
            w = ar.weights
            if hasattr(w, "__len__"):
                for i, v in enumerate(w):
                    attention[f"algo_{i}"] = float(v)
        elif hasattr(ar, "attention_weights") and ar.attention_weights is not None:
            for k, v in ar.attention_weights.items():
                attention[str(k)] = float(v)
    except Exception:
        pass

    # ── 2. Get phi-correlation scores ─────────────────────────────────────────
    phi_corr: Dict[str, float] = {}
    try:
        from algorithms.SelfArchitectureMutator import analyse as _sam
        mr = _sam(agent=agent)
        for c in mr.contributions:
            phi_corr[c.name] = float(c.correlation)
    except Exception:
        pass

    # ── 3. Find common algorithms ─────────────────────────────────────────────
    common = sorted(set(attention) & set(phi_corr))

    if len(common) < min_algorithms:
        # Fall back: if attention has numeric indices and phi_corr has names,
        # align by position in phi_corr sorted list
        if phi_corr and attention:
            sorted_phi = sorted(phi_corr.items(), key=lambda kv: -kv[1])
            n = min(len(sorted_phi), len(attention))
            attn_vals_raw = list(attention.values())
            if n >= min_algorithms:
                weights_arr = np.array(attn_vals_raw[:n])
                corrs_arr   = np.array([v for _, v in sorted_phi[:n]])
                names       = [k for k, _ in sorted_phi[:n]]
                common = names
                # fall through with override arrays
                top_att = names[int(np.argmax(weights_arr))]
                top_phi = names[int(np.argmax(corrs_arr))]
                rho = _spearman(weights_arr, corrs_arr)
                null = _null_distribution(weights_arr, corrs_arr, n_shuffles, _RNG_SEED)
                threshold = float(np.percentile(null, _NULL_PCTILE))
                return AttentionalCoherenceResult(
                    spearman_rho=round(rho, 4),
                    coherence_class=_classify(rho),
                    beats_null=bool(rho > threshold),
                    n_algorithms=n,
                    top_attended_algorithm=top_att,
                    top_phi_algorithm=top_phi,
                    is_tracking_phi=(top_att == top_phi),
                )
        return AttentionalCoherenceResult()

    weights_arr = np.array([attention[k] for k in common])
    corrs_arr   = np.array([phi_corr[k]  for k in common])

    top_att = common[int(np.argmax(weights_arr))]
    top_phi = common[int(np.argmax(corrs_arr))]
    rho     = _spearman(weights_arr, corrs_arr)

    null      = _null_distribution(weights_arr, corrs_arr, n_shuffles, _RNG_SEED)
    threshold = float(np.percentile(null, _NULL_PCTILE))

    return AttentionalCoherenceResult(
        spearman_rho=round(rho, 4),
        coherence_class=_classify(rho),
        beats_null=bool(rho > threshold),
        n_algorithms=len(common),
        top_attended_algorithm=top_att,
        top_phi_algorithm=top_phi,
        is_tracking_phi=(top_att == top_phi),
    )
