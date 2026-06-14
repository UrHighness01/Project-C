#!/usr/bin/env python3
"""
Causal intervention — do(), not just observe.

Coupling measures (Granger, ablation) are observational: they can be confounded. A causal
claim needs an intervention: change one variable and measure the downstream effect on the
others, holding nothing else fixed by us. Here we perform a bounded, self-terminating
do(CPU load) and measure the real change each other substrate channel undergoes during the
intervention versus a matched baseline window. The effect size (in baseline standard
deviations) is a genuine causal estimate of how the perturbed input propagates.

This is the experimental counterpart to the observational integration probe: where the
probe asks "do the signals co-vary?", this asks "if I push one, do the others move?"
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import time

import numpy as np

from runtime.resources import resource_sample

CHANNELS = ["cpu_percent", "mem_percent", "load_avg_1m", "num_threads", "io_bytes"]


def _burn(stop_t: float):
    x = 0.0
    while time.time() < stop_t:
        x += sum(i * i for i in range(2000))


def _sample(duration: float, dt: float = 0.1):
    rows = []
    end = time.time() + duration
    while time.time() < end:
        s = resource_sample()
        rows.append([s.get(c, 0.0) for c in CHANNELS])
        time.sleep(dt)
    return np.array(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    ap.add_argument("--secs", type=float, default=4.0)
    a = ap.parse_args()

    resource_sample()
    base = _sample(a.secs)                                # baseline (no intervention)
    base_mu, base_sd = base.mean(0), base.std(0) + 1e-9

    stop_t = time.time() + a.secs
    procs = [mp.Process(target=_burn, args=(stop_t,)) for _ in range(a.workers)]
    for p in procs:
        p.start()
    during = _sample(a.secs)                              # under do(CPU load)
    for p in procs:
        p.join()

    effect = (during.mean(0) - base_mu) / base_sd         # downstream effect in baseline SDs
    print(f"=== Causal intervention: do(CPU load, {a.workers} workers, {a.secs:.0f}s) ===")
    print(f"{'channel':>14} | baseline | during | effect (SD)")
    order = np.argsort(-np.abs(effect))
    for i in order:
        tag = "  <-- caused" if abs(effect[i]) > 2 and CHANNELS[i] != "cpu_percent" else \
              "  (intervened)" if CHANNELS[i] == "cpu_percent" else ""
        print(f"{CHANNELS[i]:>14} | {base_mu[i]:8.2f} | {during.mean(0)[i]:6.2f} | "
              f"{effect[i]:+7.2f}{tag}")
    downstream = [(CHANNELS[i], effect[i]) for i in order
                  if CHANNELS[i] != "cpu_percent" and abs(effect[i]) > 2]
    print(f"\ncausal downstream of CPU load: "
          f"{', '.join(f'{c}({e:+.1f}SD)' for c, e in downstream) if downstream else 'none above 2 SD'}")
    print("note: phi is computed independently by the heartbeat, so CPU load is causally\n"
          "upstream of execution time but is not expected to move phi itself.")


if __name__ == "__main__":
    main()
