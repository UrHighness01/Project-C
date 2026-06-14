#!/usr/bin/env python3
"""
Information bottleneck — what the system keeps when it compresses its inputs.

A genuinely integrated system does not weight all inputs equally: some carry predictive
signal about its future and survive compression, others are discarded. We approximate the
information-bottleneck objective with reduced-rank regression: predict the next state of
every channel from the recent past of every channel, but force the mapping through a
low-rank bottleneck. A channel's *retention* is how much of its input contribution
survives that bottleneck. Channels with high retention are what the system treats as
relevant; near-zero retention means an input is effectively ignored.

Runs on the dense phi channels now; on the full five-adapter co-logged stream it answers
"which of memory / interactions / decisions / resources does the integrated state keep?"
"""
from __future__ import annotations

import numpy as np

from algorithms.coherence_horizon import _channels
from runtime.snapshot import snapshot_matrix


def _lagged(M: np.ndarray, p: int = 3):
    """M is [C, T]; return (X past [n, C*p], Y next [n, C])."""
    C, T = M.shape
    Z = (M - M.mean(1, keepdims=True)) / (M.std(1, keepdims=True) + 1e-12)
    Y = Z[:, p:].T
    X = np.column_stack([Z[:, p - k - 1:T - k - 1].T for k in range(p)])
    return X, Y, C, p


def retention(M: np.ndarray, rank: int = 1, p: int = 3) -> np.ndarray:
    """Per-input-channel retention through a rank-`rank` predictive bottleneck."""
    X, Y, C, p = _lagged(M, p)
    if X.shape[0] < C * p + 10:
        return np.zeros(C)
    # OLS then truncate the prediction to `rank` -> reduced-rank weight B [C*p, C]
    B_ols = np.linalg.solve(X.T @ X + 1e-3 * np.eye(X.shape[1]), X.T @ Y)
    Yhat = X @ B_ols
    _, _, Vt = np.linalg.svd(Yhat - Yhat.mean(0), full_matrices=False)
    P = Vt[:rank].T @ Vt[:rank]                          # project outputs onto top-`rank`
    B = B_ols @ P                                        # rank-constrained weights
    # a channel's retention = norm of its (lagged) input rows in B, summed over lags
    ret = np.zeros(C)
    for c in range(C):
        rows = [c + k * C for k in range(p)]
        ret[c] = float(np.linalg.norm(B[rows]))
    return ret / (ret.sum() + 1e-12)


def main():
    names, M = snapshot_matrix()
    src = "co-logged adapters"
    if M.shape[1] < 120:
        names, M = ["phi_level", "phi_delta", "compute_load"], _channels().T
        src = "phi substrate (full-adapter bottleneck pending more snapshots)"
    if M.size == 0:
        print("insufficient telemetry"); return
    M = np.asarray(M)
    if M.shape[0] > M.shape[1]:        # ensure [C, T]
        M = M.T
    ret = retention(M, rank=max(1, min(2, M.shape[0] - 1)))
    order = np.argsort(-ret)
    print(f"=== Information bottleneck: input retention ({src}), C={M.shape[0]} ===")
    for i in order:
        bar = "#" * int(round(ret[i] * 40))
        kept = "kept" if ret[i] > 1.0 / len(ret) else "discarded"
        print(f"  {names[i]:22s} {ret[i]*100:5.1f}%  {bar:<40} {kept}")
    print("\nHigh retention = the integrated state keeps this input; near-zero = ignored.")


if __name__ == "__main__":
    main()
