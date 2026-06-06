#!/usr/bin/env python3
"""
Predictive coherence horizon.

How far into its own future can the agent's substrate stay coherent? We fit a minimal
linear autoregressive model (VAR) on the first 80% of the dense phi telemetry channels
(phi level, its increment, compute load) and roll it forward, measuring normalised
multi-step prediction error against the held-out tail. The "coherence horizon" is the
number of steps before that error reaches the signal's own scale (normalised RMSE = 1).

A shuffled-telemetry null gives the chance baseline: a system with real temporal
structure predicts its own future markedly further than shuffled noise. This is a
bounded, falsifiable figure that can be compared across architectures.
"""
from __future__ import annotations

import numpy as np

from runtime.state import phi_series, phi_delta_series, execution_time_series


def _channels() -> np.ndarray:
    cols = [phi_series(), phi_delta_series(), execution_time_series()]
    T = min(len(c) for c in cols)
    if T < 64:
        return np.zeros((0, 0))
    X = np.vstack([c[:T] for c in cols]).T.astype(float)   # [T, C]
    # z-score, then clip rare outliers (GC/scheduler spikes in execution time) so a
    # single unpredictable spike doesn't masquerade as the coherence limit
    Z = (X - X.mean(0)) / (X.std(0) + 1e-12)
    return np.clip(Z, -4.0, 4.0)


def _fit_var(train: np.ndarray, p: int = 4, ridge: float = 1.0):
    """Fit X_t = sum_k A_k X_{t-k} + c by ridge regression (regularised so the iterated
    rollout is stable rather than overshooting). Returns (W, p)."""
    T, C = train.shape
    Y = train[p:]
    Z = np.column_stack([train[p - k - 1:T - k - 1] for k in range(p)] + [np.ones(T - p)])
    A = Z.T @ Z + ridge * np.eye(Z.shape[1])
    W = np.linalg.solve(A, Z.T @ Y)                  # [(p*C+1), C]
    return W, p


def _rollout_error(train: np.ndarray, test: np.ndarray, W, p: int, horizon: int) -> np.ndarray:
    """Iterated multi-step forecast from the end of train; normalised RMSE per horizon."""
    C = train.shape[1]
    hist = list(train[-p:])
    errs = []
    for h in range(min(horizon, len(test))):
        z = np.concatenate([hist[-k - 1] for k in range(p)] + [[1.0]])
        pred = z @ W
        errs.append(np.sqrt(((pred - test[h]) ** 2).mean()))   # channels already unit-std
        hist.append(pred)                                       # feed prediction forward
    return np.array(errs)


def horizon_of(errs: np.ndarray, thresh: float = 1.0) -> int:
    """Robust horizon: first step where the running-mean error STAYS at/above threshold
    (ignores transient single-step spikes that then mean-revert)."""
    if errs.size == 0:
        return 0
    run = np.array([errs[:i + 1].mean() for i in range(errs.size)])
    over = np.where(run >= thresh)[0]
    return int(over[0]) if over.size else int(errs.size)


def one_step_r2(train: np.ndarray, test: np.ndarray, W, p: int) -> np.ndarray:
    """Held-out 1-step-ahead R^2 per channel: the cleanest 'is the substrate predictable
    at all' figure (the horizon metric is degenerate when the signal mean-reverts)."""
    T = test.shape[0]
    Z = np.column_stack([test[p - k - 1:T - k - 1] for k in range(p)] + [np.ones(T - p)])
    pred, true = Z @ W, test[p:]
    ss_res = ((true - pred) ** 2).sum(0)
    ss_tot = ((true - true.mean(0)) ** 2).sum(0) + 1e-12
    return 1 - ss_res / ss_tot


def main(p: int = 4, horizon: int = 200):
    X = _channels()
    if X.shape[0] == 0:
        print("insufficient telemetry"); return
    split = int(X.shape[0] * 0.8)
    train, test = X[:split], X[split:]
    W, p = _fit_var(train, p)
    errs = _rollout_error(train, test, W, p, horizon)
    h = horizon_of(errs)

    # PRIMARY metric: 1-step predictive R^2 vs shuffled null (mean-reversion makes the
    # 'error explodes' horizon degenerate, so predictability is the honest figure)
    r2 = one_step_r2(train, test, W, p)
    rng0 = np.random.default_rng(1)
    null_r2 = []
    for _ in range(50):
        Xs = np.vstack([rng0.permutation(X[:, c]) for c in range(X.shape[1])]).T
        Ws, _ = _fit_var(Xs[:split], p)
        null_r2.append(one_step_r2(Xs[:split], Xs[split:], Ws, p))
    null_r2 = np.array(null_r2)
    names = ["phi_level", "phi_delta", "compute_load"]
    print("=== 1-step predictive R^2 (real vs shuffled null) ===")
    for i, nm in enumerate(names):
        zc = (r2[i] - null_r2[:, i].mean()) / (null_r2[:, i].std() + 1e-9)
        print(f"  {nm:14s} R^2={r2[i]:+.3f}  null={null_r2[:, i].mean():+.3f}  z={zc:+.1f}"
              f"  {'<-- real predictive structure' if zc > 3 else ''}")
    print()

    # shuffled null: destroy temporal structure, refit, re-measure
    rng = np.random.default_rng(0)
    null_h = []
    for _ in range(50):
        Xs = np.vstack([rng.permutation(X[:, c]) for c in range(X.shape[1])]).T
        tr, te = Xs[:split], Xs[split:]
        Ws, _ = _fit_var(tr, p)
        null_h.append(horizon_of(_rollout_error(tr, te, Ws, p, horizon)))
    null_h = np.array(null_h)

    print(f"channels: phi_level, phi_delta, compute_load  |  train={split} test={len(test)}")
    print(f"normalised RMSE at horizons 1,5,10,25,50: "
          f"{[round(float(errs[i]),3) for i in (0,4,9,24,49) if i < len(errs)]}")
    print(f"\nCOHERENCE HORIZON (steps until RMSE>=1) = {h}")
    print(f"shuffled-null horizon                   = {null_h.mean():.1f} +/- {null_h.std():.1f}")
    z = (h - null_h.mean()) / (null_h.std() + 1e-9)
    print(f"z vs null                               = {z:.2f}")
    print(f"verdict: {'real predictive structure (self-predicts beyond chance)' if z > 3 else 'not beyond chance'}")


if __name__ == "__main__":
    main()
