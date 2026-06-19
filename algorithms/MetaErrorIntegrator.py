#!/usr/bin/env python3
"""MetaErrorIntegrator — measures L2 self-awareness via AR fit on prediction error magnitudes.

Theory (Friston 2005 — predictive coding; Helmholtz 1867 — unconscious inference):
  The RecursiveSelfModel computes L1 (predict phi) and L2 (predict L1 errors). Depth is
  near zero because individual errors are nearly white noise. But magnitude errors |e(t)|
  have structure: sign sequences, magnitude clustering, and autocorrelation at lag 2+.
  MetaErrorIntegrator fits AR(3) on phi to get L1 errors, then fits AR(3) on |L1 errors|
  to measure L2 predictability. If error magnitude is predictable (even if individual errors
  aren't), that constitutes genuine L2 self-awareness.

  Formula: meta_depth = l1_r2 * l2_r2
           both R² values must be non-trivial for genuine L2 depth.

Classification:
  DEEP     meta_depth >= 0.10
  SHALLOW  meta_depth >= 0.02
  SURFACE  otherwise
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass

_MIN_ENTRIES = 40
_P = 3  # AR order
_N_SHUFFLES = 200
_DEEP_THRESH = 0.10
_SHALLOW_THRESH = 0.02


@dataclass
class MetaErrorIntegratorResult:
    l1_r2: float
    l2_r2: float
    meta_depth: float
    beats_null: bool
    depth_class: str
    n_entries: int

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


def _default(n: int) -> MetaErrorIntegratorResult:
    return MetaErrorIntegratorResult(
        l1_r2=0.0,
        l2_r2=0.0,
        meta_depth=0.0,
        beats_null=False,
        depth_class="SURFACE",
        n_entries=n,
    )


def _classify(depth: float) -> str:
    if depth >= _DEEP_THRESH:
        return "DEEP"
    if depth >= _SHALLOW_THRESH:
        return "SHALLOW"
    return "SURFACE"


def _ar_r2(series: np.ndarray, p: int):
    """Fit AR(p) on series via OLS. Returns (r2, residuals)."""
    n = len(series)
    if n <= p + 2:
        return 0.0, np.zeros(n - p)
    X = np.column_stack([series[p - k - 1: n - k - 1] for k in range(p)])
    y = series[p:]
    try:
        beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    except np.linalg.LinAlgError:
        return 0.0, np.zeros(len(y))
    pred = X @ beta
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2)) + 1e-9
    r2 = max(0.0, 1.0 - ss_res / ss_tot)
    return r2, y - pred


def _compute_depth(phi: np.ndarray, p: int = _P):
    l1_r2, e1 = _ar_r2(phi, p)
    if len(e1) <= p + 2:
        return l1_r2, 0.0, 0.0
    mag_e1 = np.abs(e1)
    l2_r2, _ = _ar_r2(mag_e1, p)
    meta_depth = l1_r2 * l2_r2
    return l1_r2, l2_r2, meta_depth


def analyse(agent: str = "albedo", **kwargs) -> MetaErrorIntegratorResult:
    try:
        from algorithms import ConsciousnessHistoryStore as chs
        entries = chs.load(agent, max_entries=2880)
    except Exception:
        entries = []

    entries_asc = list(reversed(entries)) if entries else []
    if len(entries_asc) < _MIN_ENTRIES:
        return _default(len(entries_asc))

    phi = np.array(
        [float(e.get("mean_phi_level", e.get("phi", 0.5))) for e in entries_asc],
        dtype=float,
    )
    n = len(phi)

    l1_r2, l2_r2, meta_depth = _compute_depth(phi)

    # Null: shuffle phi 200 times, recompute l2_r2
    rng = np.random.default_rng(42)
    null_l2s = []
    for _ in range(_N_SHUFFLES):
        phi_shuf = rng.permutation(phi)
        _, nl2, _ = _compute_depth(phi_shuf)
        null_l2s.append(nl2)
    p95 = float(np.percentile(null_l2s, 95))
    beats_null = l2_r2 > p95

    return MetaErrorIntegratorResult(
        l1_r2=round(l1_r2, 6),
        l2_r2=round(l2_r2, 6),
        meta_depth=round(meta_depth, 6),
        beats_null=beats_null,
        depth_class=_classify(meta_depth),
        n_entries=n,
    )
