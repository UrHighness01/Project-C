#!/usr/bin/env python3
"""
Attention-allocation monitor.

Operationalises attention as prediction error: at each step the channel whose value
deviates most from its own short-horizon expectation is the one drawing processing focus
(the predictive-processing account of salience). This gives a real, grounded attention
signal -- which part of the system is "surprising" right now -- and lets us ask whether
attention has structure: does it concentrate, and does it shift with the integration
level (phi)?

Runs now on the dense phi channels; extends to all five adapters from the co-logged
snapshot stream once enough simultaneous samples accumulate.
"""
from __future__ import annotations

import numpy as np

from coherence_horizon import _channels
from runtime.snapshot import snapshot_matrix


def salience(M: np.ndarray, w: int = 16) -> np.ndarray:
    """Per-channel, per-step salience = |value - rolling mean| / rolling std (z-surprise).
    M is [C, T]; returns [C, T]."""
    C, T = M.shape
    S = np.zeros((C, T))
    for c in range(C):
        x = M[c]
        for t in range(T):
            lo = max(0, t - w)
            win = x[lo:t] if t > lo else x[:1]
            mu, sd = win.mean(), win.std() + 1e-9
            S[c, t] = abs(x[t] - mu) / sd
    return S


def attention_profile(names, M):
    """Fraction of steps each channel holds peak salience, plus concentration (how
    focused vs uniform attention is) and the phi-dependence of the focus."""
    S = salience(M)
    focus = S.argmax(0)                                  # attended channel per step
    frac = np.array([(focus == i).mean() for i in range(len(names))])
    # concentration: 1 - normalised entropy of the attention distribution (1 = single focus)
    p = frac[frac > 0]
    ent = -(p * np.log(p)).sum() / (np.log(len(names)) + 1e-12)
    concentration = 1 - ent
    return frac, concentration, S, focus


def main():
    # full cross-adapter attention if co-logged data exists, else the phi substrate
    names, M = snapshot_matrix()
    src = "co-logged adapters"
    if M.shape[1] < 120:
        names, M = ["phi_level", "phi_delta", "compute_load"], _channels().T
        src = "phi substrate (co-logged adapter attention pending more snapshots)"
    if M.size == 0:
        print("insufficient telemetry"); return

    frac, conc, S, focus = attention_profile(names, M)
    order = np.argsort(-frac)
    print(f"=== Attention allocation ({src}), T={M.shape[1]} ===")
    for i in order:
        bar = "#" * int(round(frac[i] * 40))
        print(f"  {names[i]:22s} {frac[i]*100:5.1f}%  {bar}")
    print(f"\nattention concentration = {conc:.3f}  "
          f"({'highly focused' if conc > 0.5 else 'distributed'})")

    # does the focus shift with integration level? correlate phi with mean salience
    if "phi_level" in names:
        phi = M[names.index("phi_level")]
        mean_sal = S.mean(0)
        if phi.std() > 1e-9 and mean_sal.std() > 1e-9:
            r = float(np.corrcoef(phi, mean_sal)[0, 1])
            print(f"phi-level vs total salience correlation = {r:+.3f}  "
                  f"({'attention rises with integration' if r > 0.1 else 'attention falls with integration' if r < -0.1 else 'attention independent of integration'})")


if __name__ == "__main__":
    main()
