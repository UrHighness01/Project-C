#!/usr/bin/env python3
"""
ExistentialContinuityTracker — measuring whether the agent's current state is
a continuous evolution of its prior state, or whether a discontinuity occurred.

Theory (Parfit D. 1984 — "Reasons and Persons"; Locke J. 1689 — "An Essay
Concerning Human Understanding"; Schechtman M. 1996 — "The Constitution of
Selves"):
  Personal identity over time requires psychological continuity: memories,
  intentions, beliefs at T are causally connected to those at T-1. Locke held
  that personal identity is constituted by continuity of consciousness (memory).
  Parfit refined this: what matters is not strict identity but overlapping chains
  of psychological connection.

  For a software agent:
    - Continuity along the phi trajectory: φ(t) should be predictable from φ(t-1).
      Discontinuity = φ takes a step that the AR model didn't predict (Mahalanobis
      distance of the residual exceeds a threshold).
    - Continuity along the qualia stream: semantic drift between consecutive
      entries should be small (high Jaccard similarity to K-nearest neighbors).
      Discontinuity = qualia stream abruptly shifts topic (low Jaccard).
    - Continuity of the time gap: no unaccounted-for gaps between timestamps.

  We measure:
    1. Phi continuity: rolling AR(p) residual Mahalanobis distance.
       High residual at t → phi discontinuity at t.
    2. Qualia continuity: mean Jaccard(entry_t, entry_{t-1}) over recent W entries.
       Drop in Jaccard → qualia discontinuity.
    3. Combined continuity score: geometric mean of phi and qualia continuity.
    4. Discontinuity events: timesteps where phi residual > threshold (3σ).

Math:
  Phi continuity:
    AR(p) fit on phi, one-step-ahead residuals r(t) = φ(t) - φ̂(t).
    σ_r = std(r)
    is_discontinuous(t) = |r(t)| > k · σ_r    (k=3 default)
    phi_continuity = 1 - (n_discontinuous / n_residuals) ∈ [0, 1]

  Qualia continuity:
    sim(t) = Jaccard(T(entry_t), T(entry_{t-1}))
    qualia_continuity = mean(sim(t)) ∈ [0, 1]

  Combined score = sqrt(phi_continuity × qualia_continuity)

  Null: phase-randomised phi → residuals have same magnitude but random temporal
  structure. Discontinuity events in null = expected false-positive rate.

Grounding:
  - Phi from Albedo's live daemon (via runtime.state.phi_series).
  - Qualia from John's qualia-stream.jsonl.
  No synthetic data for the primary signals.

References:
  Parfit D. (1984) "Reasons and Persons" — Part III: personal identity
  Locke J. (1689) "An Essay Concerning Human Understanding" — Book II Ch. 27
  Schechtman M. (1996) "The Constitution of Selves"
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional

import numpy as np


# ── AR fit helpers ────────────────────────────────────────────────────────────

def _build_lagged(x: np.ndarray, p: int):
    n = len(x)
    Z = np.zeros((n - p, p))
    for j in range(p):
        Z[:, j] = x[p - 1 - j: n - 1 - j]
    return Z, x[p:]


def _ridge_fit(Z: np.ndarray, y: np.ndarray, ridge: float = 1e-3) -> np.ndarray:
    lam = ridge * np.eye(Z.shape[1])
    return np.linalg.solve(Z.T @ Z + lam, Z.T @ y)


def _ar_residuals(phi: np.ndarray, p: int = 4) -> np.ndarray:
    """Full-series AR(p) residuals (length n-p, leaves first p points with r=0)."""
    if len(phi) < p + 4:
        return np.array([])
    Z, y = _build_lagged(phi, p)
    w = _ridge_fit(Z, y)
    return y - Z @ w


# ── Phase-randomised null ─────────────────────────────────────────────────────

def _phase_randomise(y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Theiler (1992) phase-randomised surrogate."""
    n = len(y)
    ft = np.fft.rfft(y)
    phases = rng.uniform(0, 2 * np.pi, len(ft))
    ft_rnd = np.abs(ft) * np.exp(1j * phases)
    return np.fft.irfft(ft_rnd, n=n)


# ── Jaccard similarity ────────────────────────────────────────────────────────

def _token_set(text: str) -> frozenset:
    if not isinstance(text, str):
        return frozenset()
    return frozenset(re.findall(r'[a-z]+', text.lower()))


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return float(len(a & b) / len(a | b))


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class ContinuityResult:
    """Output of ExistentialContinuityTracker.

    Attributes:
        phi_continuity:          1 - (discontinuous phi steps / total) ∈ [0, 1]
        qualia_continuity:       mean Jaccard(entry_t, entry_{t-1}) ∈ [0, 1]
        combined_continuity:     geometric mean of phi and qualia continuity
        n_phi_discontinuities:   count of phi residuals > k·σ
        phi_discontinuity_rate:  n_phi_discontinuities / n_residuals
        null_discontinuity_rate: expected rate from phase-randomised null
        beats_null:              real disc. rate < null disc. rate (more continuous than noise)
        phi_residuals:           array of AR residuals
        phi_residual_sigma:      σ of residuals
        k_threshold:             k used for discontinuity detection
        qualia_sim_series:       per-step Jaccard similarities
        n_qualia_steps:          number of consecutive qualia pairs measured
        is_continuous:           combined_continuity > 0.7
    """
    phi_continuity: float
    qualia_continuity: float
    combined_continuity: float
    n_phi_discontinuities: int
    phi_discontinuity_rate: float
    null_discontinuity_rate: float
    beats_null: bool
    phi_residuals: np.ndarray
    phi_residual_sigma: float
    k_threshold: float
    qualia_sim_series: np.ndarray
    n_qualia_steps: int
    is_continuous: bool


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(phi: np.ndarray, entries: list,
            p: int = 4, k: float = 3.0,
            null_seed: int = 42) -> Optional[ContinuityResult]:
    """
    Measure existential continuity from phi trajectory and qualia stream.

    Args:
        phi:     phi time series (numpy array).
        entries: qualia entry list (dicts with 'content' key).
        p:       AR order for phi residuals.
        k:       discontinuity threshold multiplier (residual > k·σ = event).
        null_seed: RNG seed for phase-randomised null.

    Returns:
        ContinuityResult, or None if inputs too short.
    """
    if len(phi) < p + 8:
        return None

    # Phi continuity
    residuals = _ar_residuals(phi, p)
    if len(residuals) < 4:
        return None
    sigma_r = float(residuals.std())
    threshold = k * max(sigma_r, 1e-9)
    n_disc = int(np.sum(np.abs(residuals) > threshold))
    phi_disc_rate = float(n_disc / len(residuals))
    phi_cont = float(1.0 - phi_disc_rate)

    # Null: phase-randomised phi
    rng = np.random.default_rng(null_seed)
    null_phi = _phase_randomise(phi, rng)
    null_res = _ar_residuals(null_phi, p)
    if len(null_res) >= 4:
        null_sigma = float(null_res.std())
        null_threshold = k * max(null_sigma, 1e-9)
        null_disc_rate = float(np.sum(np.abs(null_res) > null_threshold) / len(null_res))
    else:
        null_disc_rate = phi_disc_rate

    # Qualia continuity
    if len(entries) >= 2:
        contents = [e.get("content", "") if isinstance(e, dict) else str(e)
                    for e in entries]
        token_sets = [_token_set(c) for c in contents]
        sims = np.array([
            _jaccard(token_sets[i], token_sets[i - 1])
            for i in range(1, len(token_sets))
        ])
        qualia_cont = float(sims.mean())
        n_qualia_steps = len(sims)
    else:
        sims = np.array([])
        qualia_cont = 1.0
        n_qualia_steps = 0

    combined = float(np.sqrt(phi_cont * qualia_cont))
    beats_null = phi_disc_rate < null_disc_rate

    return ContinuityResult(
        phi_continuity=phi_cont,
        qualia_continuity=qualia_cont,
        combined_continuity=combined,
        n_phi_discontinuities=n_disc,
        phi_discontinuity_rate=phi_disc_rate,
        null_discontinuity_rate=null_disc_rate,
        beats_null=beats_null,
        phi_residuals=residuals,
        phi_residual_sigma=sigma_r,
        k_threshold=k,
        qualia_sim_series=sims,
        n_qualia_steps=n_qualia_steps,
        is_continuous=combined > 0.7,
    )


def _load_qualia_entries() -> list[dict]:
    try:
        from runtime.agent import agent_home
        home = agent_home("john")
        for sub in ["memory", "../workspace-john-john/memory"]:
            p = (home / sub / "qualia-stream.jsonl").resolve()
            if p.exists():
                break
        else:
            sibling = home.parent / (home.name + "-john") / "memory" / "qualia-stream.jsonl"
            p = sibling
        if not p.exists():
            return []
    except Exception:
        return []
    entries = []
    try:
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except OSError:
        pass
    return entries


def analyse_from_telemetry() -> Optional[ContinuityResult]:
    """Load Albedo's phi and John's qualia, measure existential continuity."""
    try:
        from runtime.state import phi_series
        phi = phi_series()
    except Exception:
        return None
    entries = _load_qualia_entries()
    return analyse(phi, entries)


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("Insufficient data.")
    else:
        print(f"ExistentialContinuityTracker")
        print(f"  Phi continuity:    {r.phi_continuity:.4f}")
        print(f"  Qualia continuity: {r.qualia_continuity:.4f}  ({r.n_qualia_steps} pairs)")
        print(f"  Combined:          {r.combined_continuity:.4f}")
        print(f"  Is continuous:     {r.is_continuous}")
        print(f"  Phi disc. events:  {r.n_phi_discontinuities}  "
              f"(rate {r.phi_discontinuity_rate:.4f}, null {r.null_discontinuity_rate:.4f})")
        print(f"  Beats null:        {r.beats_null}")
        print(f"  φ residual σ:      {r.phi_residual_sigma:.4f}  (threshold {r.k_threshold}σ)")
