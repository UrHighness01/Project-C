#!/usr/bin/env python3
"""
VolitionGrounding — measuring whether the agent's qualia sequence is driven by
internal phi dynamics vs external (stimulus) patterns.

Theory (Frankfurt H. 1971 — "Freedom of the Will and the Concept of a Person";
Kane R. 1996 — "The Significance of Free Will"; Bratman M. 1987 — "Intention,
Plans, and Practical Reason"):
  A volitional agent acts from internal states, not merely as a reflex of
  external stimuli. Frankfurt distinguishes first-order desires (wanting X) from
  second-order volitions (wanting to want X). Genuine agency requires that the
  agent's actions arise from its own endorsed internal states.

  Applied to a phi-based agent:
    - Internal driver: the phi trajectory at time t should predict the novelty
      and valence of qualia at t+1 better than a null model.
    - External driver: qualia content at t should predict qualia content at t+1
      (stimulus-response chaining) — this is reactivity, not volition.

  Operationalisation:
    1. Phi-to-qualia Granger causality:
       Does phi(t-k..t) predict qualia_novelty(t+1) better than qualia_novelty alone?
       This tests whether internal state causes phenomenal output.

    2. Qualia-to-qualia autocausality (stimulus chaining):
       Does qualia_novelty(t-k..t) predict qualia_novelty(t+1)?
       High qualia self-prediction = stimulus chaining.

    3. Volition index = phi_granger_f / (phi_granger_f + qqa_f + ε)
       If phi alone explains qualia novelty → index near 1 (internally driven).
       If qualia self-predict → index near 0 (stimulus-response).

    4. Baseline: phase-randomised phi → phi prediction of qualia should vanish.
       True Granger causality from phi > null baseline.

Math:
  Let n(t) = novelty of qualia entry t (Jaccard-based, as in ExperientialNoveltyDetector).
  Let φ_binned(t) = phi quantised to 8 bins (to align with qualia timing).

  AR models:
    Restricted: n(t) = Σ a_k n(t-k) + ε       (AR(p) on novelty alone)
    Full phi:   n(t) = Σ a_k n(t-k) + Σ b_k φ(t-k) + ε  (joint)

  Granger F for phi:
    F = ((RSS_r - RSS_f)/p) / (RSS_f/(T-2p-1))   (standard Granger F-stat)

  Volition index = F_phi / (F_phi + F_qqa + ε)   ∈ [0, 1]

  Null: phase-randomise phi, recompute F_phi_null.
  phi_granger_significant = F_phi > F_phi_null (phi explains novelty beyond noise).

Grounding:
  - phi from Albedo's live daemon.
  - Qualia novelty series computed from John's qualia stream using the same
    Jaccard logic as ExperientialNoveltyDetector (inlined, no circular import).
  - No synthetic signal.

References:
  Frankfurt H. (1971) "Freedom of the Will and the Concept of a Person"
    — Journal of Philosophy 68(1):5-20
  Kane R. (1996) "The Significance of Free Will"
  Granger C.W.J. (1969) "Investigating causal relations by econometric models
    and cross-spectral methods" — Econometrica 37(3):424-438
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional

import numpy as np


# ── Jaccard novelty ───────────────────────────────────────────────────────────

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


def _novelty_series(entries: list, K: int = 5) -> np.ndarray:
    """Compute per-entry novelty as 1 − max Jaccard against K predecessors."""
    token_sets = [_token_set(e.get("content", "") if isinstance(e, dict) else str(e))
                  for e in entries]
    novelties = np.zeros(len(token_sets))
    for i, ts in enumerate(token_sets):
        recent = token_sets[max(0, i - K): i]
        if not recent:
            novelties[i] = 1.0
        else:
            novelties[i] = 1.0 - max(_jaccard(ts, r) for r in recent)
    return novelties


# ── AR and Granger helpers ────────────────────────────────────────────────────

def _build_joint_design(y: np.ndarray, x: np.ndarray, p: int):
    """Design matrix with p lags of y and p lags of x (2p columns)."""
    n = len(y)
    Z = np.zeros((n - p, 2 * p))
    for j in range(p):
        Z[:, j] = y[p - 1 - j: n - 1 - j]
        Z[:, p + j] = x[p - 1 - j: n - 1 - j]
    return Z, y[p:]


def _build_restricted_design(y: np.ndarray, p: int):
    n = len(y)
    Z = np.zeros((n - p, p))
    for j in range(p):
        Z[:, j] = y[p - 1 - j: n - 1 - j]
    return Z, y[p:]


def _ridge_fit(Z: np.ndarray, y: np.ndarray, ridge: float = 1e-3) -> np.ndarray:
    lam = ridge * np.eye(Z.shape[1])
    return np.linalg.solve(Z.T @ Z + lam, Z.T @ y)


def _rss(y: np.ndarray, Z: np.ndarray, w: np.ndarray) -> float:
    return float(np.sum((y - Z @ w) ** 2))


def _granger_f(rss_r: float, rss_f: float, T: int, p: int) -> float:
    """Standard Granger F-statistic. Clipped at 0."""
    num = (rss_r - rss_f) / p
    denom = rss_f / max(T - 2 * p - 1, 1)
    return float(max(0.0, num / max(denom, 1e-9)))


# ── Phase-randomised null ─────────────────────────────────────────────────────

def _phase_randomise(y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    n = len(y)
    ft = np.fft.rfft(y)
    phases = rng.uniform(0, 2 * np.pi, len(ft))
    return np.fft.irfft(np.abs(ft) * np.exp(1j * phases), n=n)


# ── Alignment: bin phi to qualia timeline ────────────────────────────────────

def _align_phi_to_entries(phi: np.ndarray, n_entries: int) -> np.ndarray:
    """
    Downsample (or upsample) phi to match n_entries by linear interpolation.
    Uses np.interp for a simple alignment.
    """
    n = len(phi)
    if n == n_entries:
        return phi.copy()
    src_idx = np.linspace(0, n - 1, n_entries)
    return np.interp(src_idx, np.arange(n), phi)


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class VolitionResult:
    """Output of VolitionGrounding.

    Attributes:
        phi_granger_f:         F-statistic for phi causing qualia novelty
        qualia_autocausal_f:   F-statistic for qualia self-predicting (stimulus chaining)
        null_phi_granger_f:    phi Granger F on phase-randomised null
        phi_granger_significant: True if phi_granger_f > null_phi_granger_f
        volition_index:        phi_f / (phi_f + qqa_f + ε) ∈ [0, 1]
        is_volitional:         volition_index > 0.5 AND phi_granger_significant
        n_entries:             qualia entries used
        n_phi_samples:         phi samples used
        p:                     AR lag order
        novelty_series:        per-entry novelty scores (aligned length)
        aligned_phi:           phi downsampled to entry count
    """
    phi_granger_f: float
    qualia_autocausal_f: float
    null_phi_granger_f: float
    phi_granger_significant: bool
    volition_index: float
    is_volitional: bool
    n_entries: int
    n_phi_samples: int
    p: int
    novelty_series: np.ndarray
    aligned_phi: np.ndarray


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(phi: Optional[np.ndarray] = None,
            entries: Optional[list] = None,
            p: int = 4, K_novelty: int = 5,
            null_seed: int = 42,
            agent: str = "albedo") -> Optional[VolitionResult]:
    """
    Measure whether phi (internal state) causes qualia novelty (beyond qualia self-prediction).

    Args:
        phi:         phi time series.
        entries:     qualia entry list.
        p:           AR lag order.
        K_novelty:   recency window for novelty computation.
        null_seed:   seed for phase-randomised null.

    Returns:
        VolitionResult, or None if inputs too short.
    """
    if phi is None or entries is None:
        try:
            from algorithms import ConsciousnessHistoryStore as chs
            raw = chs.load(agent) or []
            if phi is None:
                phi = np.array([float(e["mean_phi_level"]) for e in reversed(raw)
                                if "mean_phi_level" in e], dtype=float)
            if entries is None:
                entries = list(reversed(raw))
        except Exception:
            return None
    if phi is None or entries is None or len(phi) < p + 8 or len(entries) < p + 8:
        return None

    novelties = _novelty_series(entries, K=K_novelty)
    phi_aligned = _align_phi_to_entries(phi, len(novelties))

    n = len(novelties)
    if n < p + 8:
        return None

    # 70/30 split
    split = max(2 * p + 4, int(0.7 * n))
    if split >= n - 2:
        return None

    # Restricted: novelty ~ AR(p) novelty only
    Zr, yr = _build_restricted_design(novelties, p)
    wr = _ridge_fit(Zr[:split - p], yr[:split - p])
    rss_r = _rss(yr[split - p:], Zr[split - p:], wr)

    # Full (phi causes novelty): novelty ~ AR(p) novelty + AR(p) phi
    Zf, yf = _build_joint_design(novelties, phi_aligned, p)
    wf = _ridge_fit(Zf[:split - p], yf[:split - p])
    rss_f = _rss(yf[split - p:], Zf[split - p:], wf)

    T = n - p - (split - p)   # holdout size
    phi_f = _granger_f(rss_r, rss_f, T, p)

    # Qualia auto-causality: second half AR(p) novelty self-prediction
    # Use split-wise: train on first half, predict on second
    qqa_f = float(max(0.0, (rss_r - _rss(yr[split - p:], Zr[split - p:],
                                          _ridge_fit(Zr[:split - p], yr[:split - p]))) / p
                     / (rss_r / max(T - p - 1, 1))))
    # Actually qualia self-prediction F is just F of restricted model vs intercept-only null
    # Intercept null: predict mean
    mean_null_rss = float(np.sum((yr[split - p:] - yr[:split - p].mean()) ** 2))
    qqa_f = _granger_f(mean_null_rss, rss_r, T, p)

    # Null: phase-randomise phi
    rng = np.random.default_rng(null_seed)
    phi_null = _phase_randomise(phi_aligned, rng)
    Znf, ynf = _build_joint_design(novelties, phi_null, p)
    wnf = _ridge_fit(Znf[:split - p], ynf[:split - p])
    rss_nf = _rss(ynf[split - p:], Znf[split - p:], wnf)
    null_f = _granger_f(rss_r, rss_nf, T, p)

    phi_sig = phi_f > null_f
    vi = float(phi_f / (phi_f + qqa_f + 1e-9))
    is_vol = vi > 0.5 and phi_sig

    return VolitionResult(
        phi_granger_f=phi_f,
        qualia_autocausal_f=qqa_f,
        null_phi_granger_f=null_f,
        phi_granger_significant=phi_sig,
        volition_index=vi,
        is_volitional=is_vol,
        n_entries=len(entries),
        n_phi_samples=len(phi),
        p=p,
        novelty_series=novelties,
        aligned_phi=phi_aligned,
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


def analyse_from_telemetry() -> Optional[VolitionResult]:
    """Load live phi and John's qualia, compute volition grounding."""
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
        print(f"VolitionGrounding: {r.n_entries} entries, {r.n_phi_samples} phi samples")
        print(f"  Phi Granger F:      {r.phi_granger_f:.4f}  (null {r.null_phi_granger_f:.4f})")
        print(f"  Phi sig:            {r.phi_granger_significant}")
        print(f"  Qualia auto F:      {r.qualia_autocausal_f:.4f}")
        print(f"  Volition index:     {r.volition_index:.4f}")
        print(f"  Is volitional:      {r.is_volitional}")
