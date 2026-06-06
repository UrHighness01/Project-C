#!/usr/bin/env python3
"""
Cross-modal prediction — the real integration test.

Self-prediction (the agent's phi predicts its own future) shows structure, not
integration. The decisive question is whether one domain predicts ANOTHER: e.g. does the
integration level (phi) predict interaction sentiment, or memory growth, beyond chance?
If yes, the adapters form one coupled system; if no, each lives in its own silo.

Operates on the co-logged snapshot stream (runtime.snapshot / scripts/snapshot_daemon).
For every ordered cross-adapter channel pair, it measures the held-out R^2 *gain* from
adding the source channel's lagged history to a predictor of the target that already has
the target's own past -- the directed cross-domain predictive power -- against a shuffled
null. Needs enough simultaneous samples; reports accumulation status until then.
"""
from __future__ import annotations

import numpy as np

from runtime.snapshot import snapshot_matrix

# which adapter each snapshot channel belongs to (cross-modal = different adapters)
ADAPTER = {
    "phi_level": "telemetry", "phi_delta": "telemetry", "compute_load": "telemetry",
    "cpu_percent": "resources", "mem_percent": "resources",
    "memory_volume": "memory",
    "interaction_latency": "interactions", "interaction_sentiment": "interactions",
    "decision_count": "decisions",
}
MIN_SAMPLES = 240          # ~2h at 30s; 1000+ (~8h) preferred for a stable read


def _gain(src: np.ndarray, tgt: np.ndarray, p: int = 3) -> float:
    """Held-out R^2 gain on tgt[t] from adding src's past to tgt's own past (ridge)."""
    n = tgt.size
    if n <= p + 20:
        return 0.0
    def z(a):
        return (a - a.mean()) / (a.std() + 1e-12)
    src, tgt = z(src), z(tgt)
    Y = tgt[p:]
    tp = np.column_stack([tgt[p - k - 1:n - k - 1] for k in range(p)])
    sp = np.column_stack([src[p - k - 1:n - k - 1] for k in range(p)])
    split = int(len(Y) * 0.7)
    def r2(X):
        Xtr, ytr, Xte, yte = X[:split], Y[:split], X[split:], Y[split:]
        D = np.column_stack([np.ones(len(Xtr)), Xtr])
        w = np.linalg.solve(D.T @ D + 1.0 * np.eye(D.shape[1]), D.T @ ytr)
        Dte = np.column_stack([np.ones(len(Xte)), Xte])
        pred = Dte @ w
        return 1 - ((yte - pred) ** 2).sum() / (((yte - yte.mean()) ** 2).sum() + 1e-12)
    return r2(np.column_stack([tp, sp])) - r2(tp)


def main():
    names, M = snapshot_matrix()
    T = M.shape[1] if M.size else 0
    if T < MIN_SAMPLES:
        print(f"co-logged samples: {T} / {MIN_SAMPLES} needed "
              f"(~{max(0, (MIN_SAMPLES - T) * 30) // 60} min more at 30s cadence)")
        print("The snapshot service is accumulating; rerun once enough data exists.")
        return
    idx = {n: i for i, n in enumerate(names)}
    usable = [n for n in names if n in ADAPTER and M[idx[n]].std() > 1e-9]
    rng = np.random.default_rng(0)
    print(f"=== Cross-modal predictive gain (source -> target, different adapters), T={T} ===")
    results = []
    for s in usable:
        for t in usable:
            if ADAPTER[s] == ADAPTER[t]:
                continue
            g = _gain(M[idx[s]], M[idx[t]])
            null = np.array([_gain(rng.permutation(M[idx[s]]), M[idx[t]]) for _ in range(30)])
            zc = (g - null.mean()) / (null.std() + 1e-9)
            results.append((zc, g, s, t))
    results.sort(reverse=True)
    for zc, g, s, t in results[:10]:
        flag = "  <-- real cross-domain integration" if zc > 3 and g > 0.01 else ""
        print(f"  {s:22s} -> {t:22s}  gain R^2={g:+.3f}  z={zc:+.1f}{flag}")
    strong = [r for r in results if r[0] > 3 and r[1] > 0.01]
    print(f"\n{len(strong)} cross-adapter link(s) above chance -> "
          f"{'the system is genuinely integrated' if strong else 'adapters behave as independent silos (so far)'}")


if __name__ == "__main__":
    main()
