#!/usr/bin/env python3
"""
Temporal identity drift — continuity of self.

The agent has a grounded spectral signature (per-band power + spectral entropy of its phi
trajectory). Identity is the question of how that signature changes over time. Three
regimes, distinguishable from data:

  - frozen      : signature does not move  -> stable but not learning ("dead")
  - dispersing  : signature drifts without bound -> no persistent identity
  - bounded     : signature moves but stays within a bounded region of signature-space
                  -> growth-with-continuity (the interesting regime)

We compute the signature over successive sub-windows of the phi history and measure
per-step drift, total spread, and the boundedness ratio (spread vs. cumulative path
length). Re-running over days extends the timescale as the daemon's history rolls forward.
"""
from __future__ import annotations

import numpy as np

from runtime.state import phi_series


def _signature(x: np.ndarray, n_bands: int = 8) -> np.ndarray:
    x = x - x.mean()
    if x.std() < 1e-12:
        return np.zeros(n_bands)
    psd = np.abs(np.fft.rfft(x)) ** 2
    psd = psd / (psd.sum() + 1e-12)
    ent = float(-(psd * np.log(psd + 1e-12)).sum() / np.log(len(psd)))
    bands = np.array_split(psd, n_bands - 1)
    feats = np.array([float(b.sum()) for b in bands] + [ent])
    return feats / (feats.max() + 1e-12)


def signature_trajectory(win: int = 128, step: int = 32) -> np.ndarray:
    """Spectral signature over successive windows of the phi history -> [N, n_bands]."""
    x = phi_series()
    if x.size < win + step:
        return np.zeros((0, 0))
    sigs = [_signature(x[i:i + win]) for i in range(0, x.size - win, step)]
    return np.vstack(sigs)


def analyse():
    S = signature_trajectory()
    if S.shape[0] < 3:
        return None
    steps = np.linalg.norm(np.diff(S, axis=0), axis=1)   # per-step drift
    centroid = S.mean(0)
    spread = float(np.linalg.norm(S - centroid, axis=1).max())   # radius of the region
    path = float(steps.sum())                            # cumulative path length
    drift = float(steps.mean())
    # boundedness: cumulative motion much larger than the region radius -> bounded oscillation
    boundedness = path / (spread + 1e-12)
    ent_series = S[:, -1]
    regime = ("frozen" if drift < 1e-3 else
              "bounded (growth-with-continuity)" if boundedness > 3 else
              "dispersing (weak identity)")
    return dict(n=S.shape[0], drift=drift, spread=spread, path=path,
                boundedness=boundedness, entropy_mean=float(ent_series.mean()),
                entropy_trend=float(ent_series[-1] - ent_series[0]), regime=regime)


def main():
    r = analyse()
    if r is None:
        print("insufficient telemetry"); return
    print("=== Temporal identity drift (phi spectral signature over time) ===")
    print(f"signatures           : {r['n']}")
    print(f"per-step drift        : {r['drift']:.4f}")
    print(f"region radius (spread): {r['spread']:.4f}")
    print(f"cumulative path       : {r['path']:.4f}")
    print(f"boundedness ratio     : {r['boundedness']:.2f}  (path / radius)")
    print(f"spectral entropy      : mean={r['entropy_mean']:.3f} trend={r['entropy_trend']:+.3f}")
    print(f"\nREGIME: {r['regime']}")


if __name__ == "__main__":
    main()
