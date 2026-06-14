#!/usr/bin/env python3
"""
Temporal novelty detection — a grounded "have I been here before?" signal.

Builds a low-dimensional manifold of the agent's recent phi states (PCA over a sliding
window) and scores each new state by its Mahalanobis distance from that manifold. High
distance = a state unlike the recent past (genuine novelty); low = familiar. No external
oracle is needed -- novelty is defined purely against the system's own history.

This gives a real repertoire signal: a system that keeps visiting the same states is
trapped; one that reaches bounded-but-new states is exploring. Tracking when novel states
occur (e.g. around interaction events, once co-logged) shows whether novelty is driven by
the world or is endogenous.
"""
from __future__ import annotations

import numpy as np

from runtime.state import phi_series, phi_delta_series, execution_time_series


def _state_vectors(window: int = 8) -> np.ndarray:
    """Embed the phi telemetry into per-step state vectors (level, delta, load, plus a
    short history) so 'novelty' reflects trajectory, not just instantaneous value."""
    cols = [phi_series(), phi_delta_series(), execution_time_series()]
    T = min(len(c) for c in cols)
    if T < 64:
        return np.zeros((0, 0))
    base = np.vstack([c[:T] for c in cols]).T            # [T, 3]
    base = (base - base.mean(0)) / (base.std(0) + 1e-12)
    # augment with a short lag history
    V = [base[window:]]
    for k in range(1, window):
        V.append(base[window - k:T - k])
    return np.hstack(V)                                   # [T-window, 3*window]


def novelty_scores(n_components: int = 4, manifold_frac: float = 0.6) -> np.ndarray:
    """Mahalanobis distance of each state from a PCA manifold fit on the earlier portion
    of the history. Returns the novelty trajectory (0 where no history)."""
    X = _state_vectors()
    if X.shape[0] < 32:
        return np.zeros(0)
    split = int(X.shape[0] * manifold_frac)
    ref = X[:split]
    mu = ref.mean(0)
    U, s, Vt = np.linalg.svd(ref - mu, full_matrices=False)
    k = min(n_components, Vt.shape[0])
    comps = Vt[:k]
    var = (s[:k] ** 2) / max(len(ref) - 1, 1) + 1e-9
    proj = (X - mu) @ comps.T                            # [T, k]
    return np.sqrt(((proj ** 2) / var).sum(1))           # Mahalanobis in PCA space


def main():
    nov = novelty_scores()
    if nov.size == 0:
        print("insufficient telemetry"); return
    recent = nov[-len(nov) // 4:]
    thresh = np.median(nov) + 2 * (np.median(np.abs(nov - np.median(nov))) * 1.4826)
    n_novel = int((nov > thresh).sum())
    print(f"=== Temporal novelty (states scored vs PCA manifold of own history) ===")
    print(f"states analysed      : {nov.size}")
    print(f"novelty: median={np.median(nov):.2f}  max={nov.max():.2f}  "
          f"recent mean={recent.mean():.2f}")
    print(f"novel states (>2 MAD): {n_novel}  ({100*n_novel/nov.size:.1f}%)")
    trend = "exploring (recent > baseline)" if recent.mean() > np.median(nov) \
        else "settling into familiar states"
    print(f"trajectory           : {trend}")


if __name__ == "__main__":
    main()
