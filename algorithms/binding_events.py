#!/usr/bin/env python3
"""
Cross-modal binding events — moments the system acts as a whole.

Integration, if real, should show up as binding events: brief windows where several
different adapters become salient at once (e.g. a phi shift AND a memory write AND a CPU
change within a couple of heartbeats). A system of independent silos almost never does
this; an integrated one does it more than chance. We detect events where >=3 channels
from >=3 distinct adapters simultaneously exceed their salience threshold, count them,
measure their duration, and compare the rate to a shuffled null (which destroys the
simultaneity). An above-null event rate is a grounded signature of global state changes.

Operates on the co-logged snapshot stream; reports accumulation status until enough
simultaneous samples exist.
"""
from __future__ import annotations

import numpy as np

from runtime.snapshot import snapshot_matrix
from algorithms.attention_monitor import salience
from algorithms.cross_modal import ADAPTER

MIN_SAMPLES = 200
THRESH = 1.5            # salience (z-surprise) threshold for a channel to count as active
MIN_ADAPTERS = 3       # distinct adapters co-active to call it a binding event
WINDOW = 2             # heartbeats over which co-activation must occur


def detect(names, M):
    """Return (event_mask over time, count, mean_duration)."""
    S = salience(M)                                       # [C, T]
    active = S > THRESH
    adapters = [ADAPTER.get(n, n) for n in names]
    T = M.shape[1]
    # per-step set of distinct active adapters within a +/-WINDOW window
    n_distinct = np.zeros(T, dtype=int)
    for t in range(T):
        lo, hi = max(0, t - WINDOW + 1), t + 1
        seen = set()
        for c in range(len(names)):
            if active[c, lo:hi].any():
                seen.add(adapters[c])
        n_distinct[t] = len(seen)
    event = n_distinct >= MIN_ADAPTERS
    # contiguous events -> durations
    durations, run = [], 0
    for e in event:
        if e:
            run += 1
        elif run:
            durations.append(run); run = 0
    if run:
        durations.append(run)
    return event, len(durations), (float(np.mean(durations)) if durations else 0.0)


def main():
    names, M = snapshot_matrix()
    T = M.shape[1] if M.size else 0
    if T < MIN_SAMPLES:
        print(f"co-logged samples: {T} / {MIN_SAMPLES} needed "
              f"(~{max(0,(MIN_SAMPLES-T)*30)//60} min more at 30s cadence)")
        print("Binding-event detection runs once enough simultaneous data exists.")
        return
    usable = [i for i, n in enumerate(names) if n in ADAPTER and M[i].std() > 1e-9]
    names = [names[i] for i in usable]; M = M[usable]
    _, n_events, dur = detect(names, M)
    rate = n_events / T
    # shuffled null: break simultaneity by permuting each channel independently
    rng = np.random.default_rng(0)
    null = []
    for _ in range(100):
        Ms = np.vstack([rng.permutation(M[i]) for i in range(M.shape[0])])
        null.append(detect(names, Ms)[1] / T)
    null = np.array(null)
    z = (rate - null.mean()) / (null.std() + 1e-9)
    print(f"=== Cross-modal binding events (T={T}, adapters={len(set(ADAPTER[n] for n in names))}) ===")
    print(f"binding events       : {n_events}  (rate {rate*100:.2f}% of steps)")
    print(f"mean duration        : {dur:.1f} steps")
    print(f"shuffled-null rate   : {null.mean()*100:.2f}% +/- {null.std()*100:.2f}%")
    print(f"z vs null            : {z:+.1f}")
    print(f"\nVERDICT: {'genuine integration events (above chance) -- the system changes '
          'state as a whole' if z > 3 else 'binding not above chance -- adapters behave '
          'independently (so far)'}")


if __name__ == "__main__":
    main()
