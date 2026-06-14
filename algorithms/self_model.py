#!/usr/bin/env python3
"""
Calibrated self-model — does the system know how well it knows itself?

A self-model is more than a point predictor: it should also represent its own
uncertainty. We fit a probabilistic one-step predictor of the agent's phi state (mean
from a regularised autoregression, predictive std from the training residuals) and test
whether its stated uncertainty is *calibrated* -- i.e. whether the true next value falls
inside the predicted intervals at the rate the model claims. Good calibration means the
system has genuine metacognition: it knows what it knows. Poor calibration (over- or
under-confidence) is itself a real, measurable property.

Predicting the other adapters from phi (once co-logged) extends this to a cross-domain
self-model: the calibration gap there is integration measured as self-knowledge.
"""
from __future__ import annotations

import numpy as np

from runtime.state import phi_series, phi_delta_series, execution_time_series

NOMINAL = np.array([0.5, 0.68, 0.8, 0.9, 0.95])
_Z = {0.5: 0.674, 0.68: 0.994, 0.8: 1.282, 0.9: 1.645, 0.95: 1.960}


def _design(x, p):
    n = x.size
    return np.column_stack([x[p - k - 1:n - k - 1] for k in range(p)] + [np.ones(n - p)]), x[p:]


def calibration(channel: np.ndarray, p: int = 4):
    """Return (nominal, empirical coverage, calibration error, predictive sharpness)."""
    x = (channel - channel.mean()) / (channel.std() + 1e-12)
    if x.size < 80:
        return None
    split = int(x.size * 0.7)
    Ztr, ytr = _design(x[:split], p)
    Zte, yte = _design(x[split:], p)
    A = Ztr.T @ Ztr + 1.0 * np.eye(Ztr.shape[1])
    w = np.linalg.solve(A, Ztr.T @ ytr)
    resid = ytr - Ztr @ w
    sigma = float(resid.std() + 1e-9)                    # the model's stated uncertainty
    pred = Zte @ w
    z = np.abs(yte - pred) / sigma
    emp = np.array([(z <= _Z[c]).mean() for c in NOMINAL])
    cal_err = float(np.abs(emp - NOMINAL).mean())
    return NOMINAL, emp, cal_err, sigma


def main():
    print("=== Calibrated self-model (phi state, 1-step) ===")
    chans = {"phi_level": phi_series(), "phi_delta": phi_delta_series(),
             "compute_load": execution_time_series()}
    for name, ch in chans.items():
        r = calibration(ch)
        if r is None:
            print(f"  {name}: insufficient data"); continue
        nominal, emp, cal_err, sigma = r
        cov = "  ".join(f"{int(n*100)}%->{e*100:.0f}%" for n, e in zip(nominal, emp))
        verdict = ("well-calibrated" if cal_err < 0.07 else
                   "over-confident" if emp.mean() < nominal.mean() else "under-confident")
        print(f"  {name:14s} cal_err={cal_err:.3f}  ({verdict})")
        print(f"      coverage: {cov}")
    print("\nLow calibration error = the system's stated uncertainty matches its real\n"
          "error: genuine metacognition (knowing what it knows).")


if __name__ == "__main__":
    main()
