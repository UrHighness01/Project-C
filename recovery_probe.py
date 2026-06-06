#!/usr/bin/env python3
"""
Recovery-time-after-perturbation probe.

Resilience is a property of a genuinely integrated system: after a disturbance it should
return to its operating point rather than drift or destabilise. We inject a *bounded,
self-terminating* CPU load (never a fork bomb -- a fixed number of workers for a fixed
duration), sample the substrate's real resource state at high frequency, and measure how
long it takes to return to baseline. This is a safe, grounded resilience figure.

  python3 recovery_probe.py            # default: half the cores, 4s load
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import time

import numpy as np

from runtime.resources import resource_sample


def _burn(stop_t: float):
    x = 0.0
    while time.time() < stop_t:
        x += sum(i * i for i in range(2000))


def _sample_cpu(duration: float, dt: float = 0.1):
    out = []
    end = time.time() + duration
    while time.time() < end:
        out.append((time.time(), resource_sample().get("cpu_percent", 0.0)))
        time.sleep(dt)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    ap.add_argument("--load_s", type=float, default=4.0)
    ap.add_argument("--settle_s", type=float, default=8.0)
    a = ap.parse_args()

    resource_sample()                                    # prime psutil's interval
    base = np.array([c for _, c in _sample_cpu(2.0)])
    baseline = float(np.median(base))
    margin = max(5.0, base.std() * 2)
    print(f"baseline cpu = {baseline:.1f}% (+/- {base.std():.1f}); "
          f"injecting {a.workers} worker(s) for {a.load_s:.0f}s")

    stop_t = time.time() + a.load_s
    procs = [mp.Process(target=_burn, args=(stop_t,)) for _ in range(a.workers)]
    for p in procs:
        p.start()
    load = _sample_cpu(a.load_s)                          # during load
    for p in procs:
        p.join()
    settle = _sample_cpu(a.settle_s)                      # after load
    peak = max(c for _, c in load)

    # recovery time: first post-load moment cpu returns within baseline+margin and stays
    t_release = settle[0][0]
    recovery = None
    for t, c in settle:
        if c <= baseline + margin:
            recovery = t - t_release
            break

    print(f"peak cpu during load = {peak:.1f}%")
    if recovery is not None:
        print(f"RECOVERY TIME to baseline = {recovery:.2f}s "
              f"({'resilient (fast return)' if recovery < a.settle_s / 2 else 'slow return'})")
    else:
        print(f"did not return to baseline within {a.settle_s:.0f}s of settle window")

    # honest note on whether the integration substrate (phi/heartbeat) even registers it
    print("note: this measures compute-substrate recovery; the heartbeat samples phi only\n"
          "every ~36s, so a few-second perturbation is mostly invisible to phi itself.")


if __name__ == "__main__":
    main()
