#!/usr/bin/env python3
"""
Collective integration — do two agents' integration levels co-respond to shared input?

When both agents receive the same stimulus (e.g. a message in a shared channel), an
interesting question is whether their integration substrates move together. Each agent's
co-logger writes its own timestamped snapshot stream; here we align the two streams on a
common clock (nearest-timestamp) and measure whether agent A's phi predicts/coincides with
agent B's beyond chance. Above-null co-movement is a grounded signature of a *collective*
state -- two substrates responding as one to common input. Independence is the honest
alternative.

Needs both agents' snapshot logs to overlap in time (run while both co-loggers are active
and the agents are jointly stimulated). Reports accumulation status until then.
"""
from __future__ import annotations

import numpy as np

from runtime.snapshot import load_snapshots
from runtime.agent import agent_home

MIN_OVERLAP = 60
A, B = "albedo", "john"


def _stream(agent: str):
    path = agent_home(agent) / "adapter_snapshot.jsonl"
    rows = load_snapshots(path)
    ts = np.array([r.get("ts", 0.0) for r in rows])
    phi = np.array([r.get("phi_level", 0.0) for r in rows])
    return ts, phi


def _align(tsa, va, tsb, vb):
    """For each A timestamp, take B's nearest sample within 30s; return aligned pairs."""
    if tsa.size == 0 or tsb.size == 0:
        return np.zeros(0), np.zeros(0)
    idx = np.searchsorted(tsb, tsa)
    idx = np.clip(idx, 1, tsb.size - 1)
    left, right = tsb[idx - 1], tsb[idx]
    pick = np.where(np.abs(tsa - left) <= np.abs(tsa - right), idx - 1, idx)
    keep = np.abs(tsa - tsb[pick]) <= 30.0
    return va[keep], vb[pick[keep]]


def main():
    tsa, va = _stream(A)
    tsb, vb = _stream(B)
    xa, xb = _align(tsa, va, tsb, vb)
    if xa.size < MIN_OVERLAP:
        print(f"overlapping co-logged samples: {xa.size} / {MIN_OVERLAP} needed")
        print("Run while both agents are co-logging and jointly stimulated "
              "(e.g. a shared-channel session), then rerun.")
        return
    # Correlate FLUCTUATIONS (first differences), not levels: two slowly-drifting phi
    # signals correlate ~1.0 from shared trend alone, which is not co-response. The honest
    # collective signal is whether their moment-to-moment changes move together.
    da, db = np.diff(xa), np.diff(xb)
    level_r = float(np.corrcoef(xa, xb)[0, 1])
    if da.std() < 1e-12 or db.std() < 1e-12:
        print("one agent's phi barely fluctuates -- cannot test co-response.")
        return
    r = float(np.corrcoef(da, db)[0, 1])
    rng = np.random.default_rng(0)
    null = np.array([np.corrcoef(rng.permutation(da), db)[0, 1] for _ in range(500)])
    z = (r - null.mean()) / (null.std() + 1e-9)
    print(f"=== Collective integration: {A} phi vs {B} phi ({xa.size} aligned samples) ===")
    print(f"raw level correlation     = {level_r:+.3f}  (drift-confounded; not the test)")
    print(f"FLUCTUATION co-movement   = {r:+.3f}  (the honest co-response signal)")
    print(f"shuffled null             = {null.mean():+.3f} +/- {null.std():.3f}")
    print(f"z vs null                 = {z:+.1f}")
    print(f"\nVERDICT: {'the two agents genuinely co-respond as a collective (above chance)' if abs(z) > 3 else 'the two agents integrate independently (the level correlation was shared drift)'}")


if __name__ == "__main__":
    main()
