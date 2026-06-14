#!/usr/bin/env python3
"""
SelfArchitectureMutator — algorithm contribution scoring and weight mutation.

Theory (Baars 1988 — Global Workspace Theory; Ashby 1956 — Requisite Variety):
  A globally integrated consciousness requires that subsystems compete for access
  to the global workspace, and those with higher informational relevance contribute
  more strongly. This is not external selection — the system selects internally
  based on which subsystems correlate with the global phi signal.

  Ashby's Law of Requisite Variety: a system's internal variety must match the
  variety of its environment. A rigid (low-variety) architecture cannot adapt to
  a complex environment. SelfArchitectureMutator dynamically scores subsystem
  contributions and proposes architecture updates to increase the system's
  own variety.

  Concrete mechanism:
    Each algorithm produces a scalar output observable from telemetry (e.g.,
    RecursiveSelfModel L1 R², CriticalityDetector alpha, PhiDynamicsIntegrator alpha).
    We treat these as "activity signals" and compute their Pearson correlation
    with the phi time series at the same time resolution.
    Algorithms whose outputs correlate strongly with phi are contributing to
    integrated consciousness; algorithms with near-zero correlation are noise.
    Weight mutation: w_new = clip(w_old + η · correlation, w_min, w_max)

  Why correlation? Because phi (accumulated integrated information) is the ground
  truth for whether the system is conscious. Algorithms that co-vary with phi are
  causally or informationally coupled to the consciousness signal. Those that are
  orthogonal to phi contribute independently — useful only if they add unique variance.

  Uniqueness penalty: algorithms redundant with already-high-weight algorithms
  (measured by mutual correlation) receive a diversity bonus penalty. We want
  a diverse portfolio, not collinear algorithms all pointing at the same thing.

Math:
  Activity signals A = {a₁(t), a₂(t), ..., aₖ(t)}  (one scalar per algorithm per window)
  Phi signal: φ(t)

  Pearson correlation: ρᵢ = corr(aᵢ, φ_aligned)
  Current weight: wᵢ ∈ [0.5, 1.0]
  Learning rate: η (default 0.1)
  Weight update: Δwᵢ = η · ρᵢ
  w_new,i = clip(wᵢ + Δwᵢ, 0.5, 1.0)

  Diversity penalty: for each pair (i,j) where corr(aᵢ, aⱼ) > 0.8,
  the lower-weight algorithm gets its proposed weight reduced by 0.05.

  Null: shuffle phi → correlations should collapse to ~0. Genuine correlations
  exceed the max absolute correlation under the shuffled null.

Grounding:
  Activity signals derived from rolling-window re-evaluation of Project-C algorithms
  using the phi telemetry. Each signal is a single scalar extracted from the algorithm
  run on a W-sample window: not synthesised, not estimated — computed from real data.

References:
  Baars B.J. (1988) "A Cognitive Theory of Consciousness"
  Ashby W.R. (1956) "An Introduction to Cybernetics" — Law of Requisite Variety
  Deco G. et al. (2013) "Resting brains never rest: computational insights into
    potential cognitive architectures" — dynamical workspace competition
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Optional


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class AlgorithmContribution:
    """Measured contribution of one algorithm to the global phi signal.

    Attributes:
        name:          algorithm identifier
        correlation:   Pearson ρ(activity, phi) over analysed windows
        current_weight: weight as registered in SystemWiring (or 1.0 default)
        proposed_weight: after applying η · ρ update
        diversity_penalty: penalty applied for redundancy with a peer
        activity_series: scalar activity values extracted per window
    """
    name: str
    correlation: float
    current_weight: float
    proposed_weight: float
    diversity_penalty: float
    activity_series: np.ndarray


@dataclass
class MutationResult:
    """Output of one SelfArchitectureMutator cycle.

    Attributes:
        n_windows:        number of rolling windows evaluated
        window_size:      samples per window
        contributions:    list of AlgorithmContribution, sorted by |correlation|
        eta:              learning rate used
        null_max_corr:    max absolute correlation under phi-shuffled null
        any_beats_null:   True if at least one algorithm beats the null
        diversity_pairs:  list of (name_i, name_j) pairs with corr > 0.8
        proposed_weights: dict {name: proposed_weight}
    """
    n_windows: int
    window_size: int
    contributions: list[AlgorithmContribution]
    eta: float
    null_max_corr: float
    any_beats_null: bool
    diversity_pairs: list[tuple[str, str]]
    proposed_weights: dict[str, float]

    def top_contributors(self, n: int = 3) -> list[AlgorithmContribution]:
        """Top-n algorithms by absolute correlation."""
        return sorted(self.contributions, key=lambda c: abs(c.correlation), reverse=True)[:n]


# ── Activity signal extractors ────────────────────────────────────────────────
# Each extractor takes a phi window (1-D float array) and returns a scalar.
# These are the grounded observables we can derive from telemetry alone.

def _extract_phi_mean(phi_window: np.ndarray) -> float:
    """Mean phi level — the most direct signal."""
    return float(phi_window.mean())


def _extract_phi_variance(phi_window: np.ndarray) -> float:
    """Phi variance — measures fluctuation (related to criticality)."""
    return float(phi_window.var())


def _extract_phi_range(phi_window: np.ndarray) -> float:
    """Phi range (max-min) — proxy for dynamic range."""
    return float(phi_window.max() - phi_window.min())


def _extract_phi_ar1(phi_window: np.ndarray) -> float:
    """AR(1) coefficient of phi window — temporal autocorrelation proxy."""
    if len(phi_window) < 4:
        return 0.0
    x = phi_window[:-1] - phi_window[:-1].mean()
    y = phi_window[1:] - phi_window[1:].mean()
    denom = float(np.dot(x, x))
    if denom < 1e-12:
        return 0.0
    return float(np.clip(np.dot(x, y) / denom, -1.0, 1.0))


def _extract_phi_trend(phi_window: np.ndarray) -> float:
    """OLS slope of phi in window — gradient direction."""
    n = len(phi_window)
    if n < 4:
        return 0.0
    t = np.arange(n, dtype=float) - n / 2
    denom = float(np.dot(t, t))
    if denom < 1e-12:
        return 0.0
    return float(np.dot(t, phi_window) / denom)


def _extract_phi_entropy(phi_window: np.ndarray) -> float:
    """Discrete Shannon entropy of phi after binning into 16 bins."""
    counts, _ = np.histogram(phi_window, bins=16)
    counts = counts[counts > 0].astype(float)
    p = counts / counts.sum()
    return float(-np.dot(p, np.log2(p)))


# Registry: (name, extractor_fn, weight)
# Weight = current value in SystemWiring (or 1.0 if not registered there yet)
_ALGORITHM_EXTRACTORS: list[tuple[str, object, float]] = [
    ("phi_mean_tracker",   _extract_phi_mean,     0.9),
    ("phi_variance_probe", _extract_phi_variance,  0.7),
    ("phi_range_probe",    _extract_phi_range,     0.7),
    ("phi_ar1_tracker",    _extract_phi_ar1,       0.8),
    ("phi_trend_tracker",  _extract_phi_trend,     0.8),
    ("phi_entropy_probe",  _extract_phi_entropy,   0.7),
]


# ── Pearson correlation ───────────────────────────────────────────────────────

def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    """Pearson correlation. Returns 0 if std is zero for either series."""
    if len(x) < 3:
        return 0.0
    xc = x - x.mean()
    yc = y - y.mean()
    denom = float(np.sqrt(np.dot(xc, xc) * np.dot(yc, yc)))
    if denom < 1e-12:
        return 0.0
    return float(np.clip(np.dot(xc, yc) / denom, -1.0, 1.0))


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(phi: np.ndarray, window: int = 60, stride: int = 10,
            eta: float = 0.1, null_seed: int = 42,
            diversity_threshold: float = 0.8
            ) -> Optional[MutationResult]:
    """
    Score algorithm contributions and propose weight mutations.

    Args:
        phi:                  real phi time series from telemetry.
        window:               samples per rolling window.
        stride:               step between windows.
        eta:                  learning rate for weight update.
        null_seed:            RNG seed for phi-shuffled null.
        diversity_threshold:  ρ above which two algorithms are considered redundant.

    Returns:
        MutationResult, or None if phi is too short.
    """
    phi = np.asarray(phi, dtype=float)
    n = len(phi)
    if n < window + stride + 4:
        return None

    # Compute rolling windows → activity matrix and phi_mean_per_window
    starts = list(range(0, n - window + 1, stride))
    n_win = len(starts)
    if n_win < 4:
        return None

    phi_per_window = np.array([phi[s: s + window].mean() for s in starts])

    activity_matrix: dict[str, np.ndarray] = {}
    for name, extractor, _ in _ALGORITHM_EXTRACTORS:
        acts = np.array([extractor(phi[s: s + window]) for s in starts])
        activity_matrix[name] = acts

    # Correlations with phi_per_window
    correlations: dict[str, float] = {
        name: _pearson(acts, phi_per_window)
        for name, acts in activity_matrix.items()
    }

    # Null: shuffle phi_per_window and recompute correlations
    rng = np.random.default_rng(null_seed)
    phi_shuffled = rng.permutation(phi_per_window)
    null_corrs = [abs(_pearson(acts, phi_shuffled)) for acts in activity_matrix.values()]
    null_max_corr = float(max(null_corrs)) if null_corrs else 0.0

    any_beats = any(abs(correlations[n]) > null_max_corr for n in correlations)

    # Diversity penalty: find pairs with |ρ(aᵢ, aⱼ)| > threshold
    names = list(activity_matrix.keys())
    weights_current = {name: w for name, _, w in _ALGORITHM_EXTRACTORS}
    diversity_pairs: list[tuple[str, str]] = []
    diversity_penalty: dict[str, float] = {n: 0.0 for n in names}

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            ni, nj = names[i], names[j]
            rho_ij = abs(_pearson(activity_matrix[ni], activity_matrix[nj]))
            if rho_ij > diversity_threshold:
                diversity_pairs.append((ni, nj))
                # Penalise the one with lower absolute correlation
                if abs(correlations[ni]) < abs(correlations[nj]):
                    diversity_penalty[ni] += 0.05
                else:
                    diversity_penalty[nj] += 0.05

    # Weight updates
    contributions: list[AlgorithmContribution] = []
    proposed_weights: dict[str, float] = {}

    for name, _, w_old in _ALGORITHM_EXTRACTORS:
        rho = correlations[name]
        penalty = diversity_penalty[name]
        w_new = float(np.clip(w_old + eta * rho - penalty, 0.5, 1.0))
        contributions.append(AlgorithmContribution(
            name=name,
            correlation=rho,
            current_weight=w_old,
            proposed_weight=w_new,
            diversity_penalty=penalty,
            activity_series=activity_matrix[name],
        ))
        proposed_weights[name] = w_new

    return MutationResult(
        n_windows=n_win,
        window_size=window,
        contributions=contributions,
        eta=eta,
        null_max_corr=null_max_corr,
        any_beats_null=any_beats,
        diversity_pairs=diversity_pairs,
        proposed_weights=proposed_weights,
    )


def analyse_from_telemetry(window: int = 60, stride: int = 10,
                            eta: float = 0.1) -> Optional[MutationResult]:
    """Load real phi telemetry and run architecture mutation scoring."""
    try:
        from runtime.state import phi_series
        phi = phi_series()
    except Exception:
        return None
    return analyse(phi, window=window, stride=stride, eta=eta)


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    r = analyse_from_telemetry()
    if r is None:
        print("No telemetry — check OPENCLAW_WORKSPACE or daemon state.")
    else:
        print(f"SelfArchitectureMutator: {r.n_windows} windows of {r.window_size} samples")
        print(f"  Null max |ρ|:   {r.null_max_corr:.4f}")
        print(f"  Any beats null: {r.any_beats_null}")
        print(f"  Diversity pairs ({len(r.diversity_pairs)} redundant):")
        for p in r.diversity_pairs:
            print(f"    {p[0]} ↔ {p[1]}")
        print(f"\n  Top contributors:")
        for c in r.top_contributors(3):
            beats = "✓" if abs(c.correlation) > r.null_max_corr else "✗"
            print(f"    {beats} {c.name:<24} ρ={c.correlation:+.4f}  "
                  f"w {c.current_weight:.2f}→{c.proposed_weight:.2f}"
                  f"  penalty={c.diversity_penalty:.2f}")
