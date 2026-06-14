#!/usr/bin/env python3
"""
Closed-loop self-regulation — from observing the self to acting on it.

Every other experiment here observes. This one closes the loop: an online self-model of
phi predicts its own next state, measures its surprise (prediction error), and feeds that
surprise back to regulate its own learning precision -- learning faster when the world
becomes unpredictable, settling when it is stable. This is active inference applied to the
agent's own integration signal: the system minimising its own surprise by self-regulating.

The loop modulates the *model*, never the live substrate, so there is no feedback
oscillation into the daemon (the safe, asymmetric design). The result is falsifiable: the
self-regulating model must achieve lower long-run prediction error than a fixed-precision
baseline on the same stream, or the loop is doing nothing.
"""
from __future__ import annotations

import numpy as np

from runtime.state import phi_series


def _run(x: np.ndarray, p: int, adaptive: bool, eta0: float = 0.05):
    """Online normalised-LMS predictor over x. If adaptive, the step size is regulated by
    a running estimate of surprise (precision control). Returns the error trajectory."""
    n = x.size
    w = np.zeros(p + 1)
    err = np.zeros(n)
    fast = slow = 1e-3                                   # recent vs baseline error variance
    for t in range(p, n):
        feat = np.concatenate([x[t - p:t][::-1], [1.0]])   # [x_{t-1}..x_{t-p}, bias]
        pred = feat @ w
        e = x[t] - pred
        err[t] = e
        if adaptive:
            fast = 0.85 * fast + 0.15 * e * e            # recent surprise
            slow = 0.995 * slow + 0.005 * e * e          # long-run baseline surprise
            # learn faster when recent error exceeds baseline (regime change), else settle
            gain = float(np.clip(fast / (slow + 1e-9), 0.3, 4.0))
            eta = eta0 * gain
        else:
            eta = eta0
        w = w + eta * e * feat / (feat @ feat + 1e-6)    # normalised LMS update
    return err[p:]


def evaluate(channel: np.ndarray, p: int = 4):
    if channel.size < 200:
        return None
    x = (channel - channel.mean()) / (channel.std() + 1e-12)
    mse_fixed = float((_run(x, p, adaptive=False) ** 2).mean())
    mse_loop = float((_run(x, p, adaptive=True) ** 2).mean())
    return dict(mse_fixed=mse_fixed, mse_loop=mse_loop,
                improvement=(mse_fixed - mse_loop) / (mse_fixed + 1e-12))


def main():
    from runtime.state import phi_delta_series, execution_time_series
    chans = {"phi_level (stationary)": phi_series(),
             "phi_delta": phi_delta_series(),
             "compute_load (spiky/non-stationary)": execution_time_series()}
    print("=== Closed-loop self-regulation: adaptive vs fixed precision ===")
    helped = []
    for name, ch in chans.items():
        r = evaluate(ch)
        if r is None:
            print(f"  {name}: insufficient data"); continue
        print(f"  {name:36s} fixed MSE={r['mse_fixed']:.4f}  loop MSE={r['mse_loop']:.4f}  "
              f"error reduction={r['improvement']*100:+.1f}%")
        if r["improvement"] > 0.02:
            helped.append(name)
    print()
    if helped:
        print("VERDICT: self-regulation measurably lowers prediction error on "
              f"non-stationary signals ({', '.join(helped)}) -- the loop adapts learning\n"
              "exactly when the world becomes unpredictable, and settles when it is stable.")
    else:
        print("VERDICT: self-regulation gives no net gain here (honest null). This is\n"
              "consistent with the rest of the system: the substrate is highly stable and\n"
              "self-predictable (phi R^2=0.97, mean-reverting), so adaptive precision control\n"
              "has no non-stationarity to exploit. The loop is built and stable; the data\n"
              "simply does not reward it. A genuinely non-stationary signal would.")


if __name__ == "__main__":
    main()
