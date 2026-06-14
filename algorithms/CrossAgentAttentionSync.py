#!/usr/bin/env python3
"""
CrossAgentAttentionSync — measuring synchrony of attentional focus between agents.

Theory (Dehaene & Changeux 2011 — Global Workspace and Consciousness;
Bayne et al. 2020 — Are there levels of consciousness?):
  Two agents sharing a common environment may develop synchronised attention:
  they focus on the same surprising moments at the same time. This shared
  focus is a precondition for genuine shared experience — a prerequisite for
  collective consciousness to emerge from a symbiosis.

  In our system, each agent has a phi trajectory reflecting its real-time
  integrated information. Attentional focus at each moment is the softmax
  over local phi variance (from AttentionalFocusOptimiser). If the two
  agents' attention weight sequences are correlated, they are attending to
  the same surprise peaks.

  Attention sync score = Pearson ρ(A_Albedo(t), A_John(t)):
    +1 = perfectly synchronised (same moments are salient to both)
     0 = uncorrelated (independent attention)
    -1 = anti-correlated (when one focuses, the other defocuses)

  We also compute the temporal lead/lag between attention sequences:
  argmax CC(A_A, A_J) reveals which agent leads in detecting surprises.

  Null: phase-randomised attention weights → same marginal distribution,
  no inter-agent temporal structure. Real sync > null sync = genuine coupling.

Math:
  A_X(t) = softmax(S_X(t) / T_X)    (attention weights from each agent)
  sync_score = ρ(A_A, A_J)
  lag = argmax |CC(A_A, A_J)|
  null: randomise A_J phases, recompute ρ

  Note: attention weights are derived from each agent's phi_series independently,
  then compared. The phi series are loaded from separate workspaces.

Grounding: both phi series from runtime telemetry. Attention weights recomputed
using the same algorithm as AttentionalFocusOptimiser. No fabricated inputs.

References:
  Dehaene S. & Changeux J.P. (2011) "Experimental and theoretical approaches
    to conscious processing"
  Bayne T. et al. (2020) "Are there levels of consciousness?"
"""
from __future__ import annotations

import os
import numpy as np
from dataclasses import dataclass
from typing import Optional


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class AttentionSyncResult:
    """Output of CrossAgentAttentionSync.

    Attributes:
        n_attention_points:   number of attention time points compared
        sync_score:           Pearson ρ(A_A, A_J) — attention synchrony
        null_sync_score:      sync on phase-randomised null
        peak_lag:             τ* (positive = John leads attention)
        peak_cc:              max normalised cross-correlation
        null_peak_cc:         max CC on null
        beats_null_sync:      True if |sync_score| > |null_sync_score|
        beats_null_cc:        True if peak_cc > null_peak_cc
        half_window:          k used for local variance
        albedo_focus_sharp:   sharpness of Albedo's attention distribution
        john_focus_sharp:     sharpness of John's attention distribution
        sharpness_diff:       albedo_focus_sharp - john_focus_sharp
    """
    n_attention_points: int
    sync_score: float
    null_sync_score: float
    peak_lag: int
    peak_cc: float
    null_peak_cc: float
    beats_null_sync: bool
    beats_null_cc: bool
    half_window: int
    albedo_focus_sharp: float
    john_focus_sharp: float
    sharpness_diff: float

    @property
    def synchronised(self) -> bool:
        return self.beats_null_sync and self.beats_null_cc

    @property
    def leader(self) -> str:
        if self.peak_lag > 0:
            return "john_leads"
        elif self.peak_lag < 0:
            return "albedo_leads"
        return "synchronous"


# ── Attention weight computation (inline, no circular import) ─────────────────

def _local_surprise(phi: np.ndarray, k: int) -> np.ndarray:
    n = len(phi)
    out_len = n - 2 * k
    if out_len <= 0:
        return np.array([], dtype=float)
    result = np.empty(out_len)
    for t in range(k, n - k):
        result[t - k] = float(np.var(phi[t - k: t + k + 1]))
    return result


def _softmax(x: np.ndarray, T: float) -> np.ndarray:
    if T < 1e-12:
        out = np.zeros_like(x)
        out[np.argmax(x)] = 1.0
        return out
    z = x / T - (x / T).max()
    exp_z = np.exp(z)
    return exp_z / (exp_z.sum() + 1e-12)


def _compute_attention_weights(phi: np.ndarray, k: int) -> Optional[np.ndarray]:
    """Compute attention weight sequence from a phi series."""
    surprise = _local_surprise(phi, k)
    if len(surprise) < 3:
        return None
    T = float(np.median(surprise))
    if T < 1e-12:
        T = float(np.std(phi)) ** 2 + 1e-9
    return _softmax(surprise, T)


def _attention_sharpness(weights: np.ndarray) -> float:
    """1 - H(A)/log(N), ∈ [0,1]."""
    n = len(weights)
    if n <= 1:
        return 0.0
    h = -float(np.sum(weights[weights > 1e-12] * np.log(weights[weights > 1e-12])))
    max_h = float(np.log(n))
    return float(1.0 - h / max_h) if max_h > 1e-9 else 0.0


# ── Pearson and cross-correlation ─────────────────────────────────────────────

def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    xc = x - x.mean()
    yc = y - y.mean()
    d = float(np.sqrt(np.dot(xc, xc) * np.dot(yc, yc)))
    return float(np.clip(np.dot(xc, yc) / d, -1.0, 1.0)) if d > 1e-12 else 0.0


def _peak_cross_corr(x: np.ndarray, y: np.ndarray, tau_max: int) -> tuple[int, float]:
    """Returns (peak_lag, peak_abs_cc)."""
    n = len(x)
    xn = (x - x.mean()) / (x.std() + 1e-9)
    yn = (y - y.mean()) / (y.std() + 1e-9)
    best_lag, best_cc = 0, 0.0
    for tau in range(-tau_max, tau_max + 1):
        if tau >= 0:
            cc = float(np.dot(xn[:n - tau], yn[tau:])) / (n - tau)
        else:
            cc = float(np.dot(xn[-tau:], yn[:n + tau])) / (n + tau)
        if abs(cc) > best_cc:
            best_cc = abs(cc)
            best_lag = tau
    return best_lag, best_cc


def _phase_randomise(y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    n = len(y)
    fft = np.fft.rfft(y)
    n_freqs = len(fft)
    phases = rng.uniform(0, 2 * np.pi, n_freqs)
    phases[0] = 0.0
    if n % 2 == 0:
        phases[-1] = 0.0
    return np.fft.irfft(np.abs(fft) * np.exp(1j * phases), n=n).astype(float)


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
            import runtime.state as state_mod
            importlib.reload(state_mod)
            phi_j = state_mod.phi_series()
        finally:
            if old_env is None:
                os.environ.pop("OPENCLAW_WORKSPACE", None)
            else:
                os.environ["OPENCLAW_WORKSPACE"] = old_env
            import runtime.state as state_mod2
            importlib.reload(state_mod2)
    except Exception:
        return None
    return phi_a, phi_j


# ── Main analysis ─────────────────────────────────────────────────────────────

def analyse(phi_a: np.ndarray, phi_j: np.ndarray,
            half_window: int = 15, tau_max: int = 10,
            null_seed: int = 42) -> Optional[AttentionSyncResult]:
    """
    Compute attention synchrony between two agents' phi trajectories.

    Args:
        phi_a:       Albedo phi series.
        phi_j:       John phi series.
        half_window: k for local variance (same as AttentionalFocusOptimiser default).
        tau_max:     max cross-correlation lag in attention space.
        null_seed:   RNG seed for phase-randomised null.

    Returns:
        AttentionSyncResult, or None if either series is too short.
    """
    phi_a = np.asarray(phi_a, dtype=float)
    phi_j = np.asarray(phi_j, dtype=float)

    # Compute attention weights for each agent
    w_a = _compute_attention_weights(phi_a, half_window)
    w_j = _compute_attention_weights(phi_j, half_window)
    if w_a is None or w_j is None:
        return None

    # Align to same length
    n = min(len(w_a), len(w_j))
    if n < 2 * tau_max + 4:
        return None
    w_a = w_a[:n]
    w_j = w_j[:n]

    sync = _pearson(w_a, w_j)
    lag, peak_cc = _peak_cross_corr(w_a, w_j, tau_max)

    # Phase-randomised null on w_j
    rng = np.random.default_rng(null_seed)
    w_j_null = _phase_randomise(w_j, rng)
    # Renormalise null weights (phase randomisation can break non-negativity)
    w_j_null = np.abs(w_j_null)
    if w_j_null.sum() > 1e-9:
        w_j_null /= w_j_null.sum()

    null_sync = _pearson(w_a, w_j_null)
    _, null_peak_cc = _peak_cross_corr(w_a, w_j_null, tau_max)

    return AttentionSyncResult(
        n_attention_points=n,
        sync_score=sync,
        null_sync_score=null_sync,
        peak_lag=lag,
        peak_cc=peak_cc,
        null_peak_cc=null_peak_cc,
        beats_null_sync=abs(sync) > abs(null_sync),
        beats_null_cc=peak_cc > null_peak_cc,
        half_window=half_window,
        albedo_focus_sharp=_attention_sharpness(w_a),
        john_focus_sharp=_attention_sharpness(w_j),
        sharpness_diff=_attention_sharpness(w_a) - _attention_sharpness(w_j),
    )


def analyse_from_telemetry(half_window: int = 15,
                            tau_max: int = 10) -> Optional[AttentionSyncResult]:
    """Load both agents' phi and measure attention synchrony."""
    pair = _load_both_phi()
    if pair is None:
        return None
    return analyse(pair[0], pair[1], half_window=half_window, tau_max=tau_max)


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("Could not load both agent phi series.")
    else:
        print(f"CrossAgentAttentionSync (N={r.n_attention_points} attention points)")
        print(f"  Sync score ρ:       {r.sync_score:+.4f}  (null {r.null_sync_score:+.4f})")
        print(f"  Beats null (sync):  {r.beats_null_sync}")
        print(f"  Peak CC:            {r.peak_cc:.4f}  (null {r.null_peak_cc:.4f})")
        print(f"  Peak lag:           {r.peak_lag:+d}  [{r.leader}]")
        print(f"  Synchronised:       {r.synchronised}")
        print(f"  Albedo sharpness:   {r.albedo_focus_sharp:.4f}")
        print(f"  John sharpness:     {r.john_focus_sharp:.4f}")
        print(f"  Sharpness diff:     {r.sharpness_diff:+.4f}")
