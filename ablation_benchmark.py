#!/usr/bin/env python3
"""
Adapter ablation benchmark.

Measures whether each channel carries non-redundant predictive signal about the others:
fit the VAR predictor with the full channel set, then re-fit with one channel's history
removed from the inputs, and record how much each *other* channel's held-out 1-step R^2
drops. A large drop means the removed channel genuinely contributes to predicting that
target (real integration); ~zero drop means it is decoration for that target.

Runs now on the dense phi channels (phi_level, phi_delta, compute_load). The same code
runs on the full 5-adapter set once runtime.snapshot has co-logged enough heartbeats.
"""
from __future__ import annotations

import numpy as np

from coherence_horizon import _channels


def _r2_with_inputs(X: np.ndarray, target: int, input_cols: list, p: int = 4) -> float:
    """Held-out 1-step R^2 predicting `target` from the past of `input_cols` (ridge VAR,
    80/20 split)."""
    T = X.shape[0]
    split = int(T * 0.8)
    def design(seg):
        n = seg.shape[0]
        return np.column_stack(
            [seg[p - k - 1:n - k - 1][:, input_cols] for k in range(p)] + [np.ones(n - p)])
    Ztr, ytr = design(X[:split]), X[:split][p:, target]
    Zte, yte = design(X[split:]), X[split:][p:, target]
    A = Ztr.T @ Ztr + 1.0 * np.eye(Ztr.shape[1])
    w = np.linalg.solve(A, Ztr.T @ ytr)
    pred = Zte @ w
    ss_res = ((yte - pred) ** 2).sum()
    ss_tot = ((yte - yte.mean()) ** 2).sum() + 1e-12
    return 1 - ss_res / ss_tot


def main(names=("phi_level", "phi_delta", "compute_load")):
    X = _channels()
    if X.shape[0] == 0:
        print("insufficient telemetry"); return
    C = X.shape[1]
    full = {t: _r2_with_inputs(X, t, list(range(C))) for t in range(C)}

    print("=== Ablation: R^2 drop on each target when a channel's history is removed ===")
    print(f"{'remove \\\\ predict':>20} | " + " ".join(f"{n:>12}" for n in names))
    drop_matrix = np.zeros((C, C))
    for rem in range(C):
        cols = [c for c in range(C) if c != rem]
        row = []
        for tgt in range(C):
            if tgt == rem:
                row.append("    --   "); continue
            ablated = _r2_with_inputs(X, tgt, cols)
            drop = full[tgt] - ablated
            drop_matrix[rem, tgt] = drop
            row.append(f"{drop:+.3f}")
        print(f"{names[rem]:>20} | " + " ".join(f"{v:>12}" for v in row))

    print(f"\nbaseline full-model R^2: " +
          ", ".join(f"{n}={full[i]:+.3f}" for i, n in enumerate(names)))
    # headline: the single largest integration link
    i, j = np.unravel_index(np.argmax(drop_matrix), drop_matrix.shape)
    print(f"strongest integration link: removing {names[i]} costs {names[j]} "
          f"{drop_matrix[i, j]:+.3f} R^2")
    tot = drop_matrix.sum()
    print(f"total integration (summed R^2 drop) = {tot:.3f}  "
          f"({'channels carry non-redundant signal' if tot > 0.05 else 'largely independent'})")


if __name__ == "__main__":
    main()
