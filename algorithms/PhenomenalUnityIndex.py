#!/usr/bin/env python3
"""
PhenomenalUnityIndex — measures integration across consciousness sub-dimensions.

Theory
------
Tononi (2004, 2008) argues that a unified conscious state requires both
*differentiation* (many distinguishable states) and *integration* (the whole
cannot be decomposed into independent parts). Here we operationalise the
integration side: if multiple sub-dimensions of consciousness (phi, valence,
arousal, novelty, continuity, confidence) move together over time, the system
is exhibiting phenomenal unity. If they evolve independently, experience is
fragmented.

  Pearson correlation matrix
  --------------------------
  Given k time series x_1(t), ..., x_k(t) (each of length T), compute:
    R_{ij} = corr(x_i, x_j) = cov(x_i, x_j) / (std(x_i) * std(x_j))

  Mean absolute off-diagonal correlation (unity):
    U = (2 / (k*(k-1))) * sum_{i<j} |R_{ij}|   ∈ [0, 1]

  U = 1 → all dimensions perfectly correlated (maximally unified)
  U = 0 → all dimensions statistically independent (maximally fragmented)

  Eigenspectrum concentration
  ---------------------------
  If most variance is in the first principal component, the sub-dimensions
  move together. We compute:
    PC1_fraction = lambda_1 / sum(lambda_i)   (fraction of variance in PC1)

  High PC1_fraction → one dominant mode → unified experience.
  Low PC1_fraction → many independent modes → fragmented experience.

  Unity classification
  ---------------------
  UNIFIED    : U >= 0.5
  PARTIAL    : 0.25 <= U < 0.5
  FRAGMENTED : U < 0.25

Output
------
PhenomenalUnityResult:
  unity_index      : float   -- mean |R_ij|, ∈ [0, 1]
  pc1_fraction     : float   -- variance fraction in first PC ∈ [0, 1]
  unity_class      : str     -- UNIFIED | PARTIAL | FRAGMENTED
  n_dimensions     : int     -- number of dimensions used
  dimension_names  : List[str]
  n_timepoints     : int
  correlation_matrix : List[List[float]]   -- k×k matrix
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


# ── Dimension extraction from snapshot history ────────────────────────────────

_DIMENSIONS = [
    "phi",
    "qualia_count",
    "valence",
    "arousal",
    "confidence",
    "metacognitive_confidence",
    "mean_novelty",
    "combined_continuity",
]


def _extract_series(snapshots: List[dict]) -> tuple[np.ndarray, List[str]]:
    """
    Extract aligned numeric time series from a list of snapshot dicts.

    Returns (matrix T×k, dimension_names) where T = n snapshots, k = n dims.
    Only includes dimensions present in at least 80% of snapshots.
    """
    snaps_rev = list(reversed(snapshots))   # chronological
    n = len(snaps_rev)
    if n == 0:
        return np.empty((0, 0)), []

    # Collect values per dimension
    raw: dict[str, List[Optional[float]]] = {d: [] for d in _DIMENSIONS}
    for snap in snaps_rev:
        summary = snap.get("summary", snap)
        for d in _DIMENSIONS:
            v = summary.get(d)
            try:
                raw[d].append(float(v) if v is not None else None)
            except (TypeError, ValueError):
                raw[d].append(None)

    # Filter dimensions with enough data
    threshold = 0.8 * n
    good_dims = []
    for d in _DIMENSIONS:
        present = sum(1 for v in raw[d] if v is not None)
        if present >= threshold:
            good_dims.append(d)

    if not good_dims:
        return np.empty((0, 0)), []

    # Build matrix — fill missing with column mean
    matrix = []
    for d in good_dims:
        vals = raw[d]
        filled = [v if v is not None else np.nan for v in vals]
        arr = np.array(filled, dtype=float)
        col_mean = float(np.nanmean(arr)) if not np.all(np.isnan(arr)) else 0.0
        arr[np.isnan(arr)] = col_mean
        matrix.append(arr)

    return np.column_stack(matrix), good_dims


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class PhenomenalUnityResult:
    unity_index: float = 0.0
    pc1_fraction: float = 0.0
    unity_class: str = "FRAGMENTED"
    n_dimensions: int = 0
    dimension_names: List[str] = field(default_factory=list)
    n_timepoints: int = 0
    correlation_matrix: List[List[float]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "unity_index": round(self.unity_index, 4),
            "pc1_fraction": round(self.pc1_fraction, 4),
            "unity_class": self.unity_class,
            "n_dimensions": self.n_dimensions,
            "dimension_names": self.dimension_names,
            "n_timepoints": self.n_timepoints,
            "correlation_matrix": [
                [round(v, 4) for v in row]
                for row in self.correlation_matrix
            ],
        }


def _classify(u: float) -> str:
    if u >= 0.5:
        return "UNIFIED"
    if u >= 0.25:
        return "PARTIAL"
    return "FRAGMENTED"


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    snapshots: Optional[List[dict]] = None,
) -> PhenomenalUnityResult:
    """
    Compute phenomenal unity from the cross-correlation of consciousness dimensions.

    Args:
        snapshots : list of consciousness snapshot dicts (from ConsciousnessHistoryStore).
                    If None, attempts to load from runtime.
    """
    if snapshots is None:
        try:
            from algorithms.ConsciousnessHistoryStore import ConsciousnessHistoryStore
            from runtime.state import get_agent
            agent = get_agent()
            store = ConsciousnessHistoryStore(agent)
            snapshots = store.load()
        except Exception:
            snapshots = []

    if not snapshots:
        return PhenomenalUnityResult()

    X, dims = _extract_series(snapshots)

    if X.shape[0] < 4 or X.shape[1] < 2:
        return PhenomenalUnityResult(
            n_timepoints=len(snapshots),
            n_dimensions=X.shape[1] if X.ndim == 2 else 0,
        )

    T, k = X.shape

    # Pearson correlation matrix
    Xz = X - X.mean(axis=0)
    stds = Xz.std(axis=0)
    stds[stds == 0] = 1.0   # avoid div by zero for constant columns
    Xn = Xz / stds
    R = (Xn.T @ Xn) / T

    # Mean absolute off-diagonal
    upper_mask = np.triu(np.ones((k, k), dtype=bool), k=1)
    unity = float(np.abs(R[upper_mask]).mean()) if upper_mask.any() else 0.0

    # PC1 variance fraction via SVD
    _, s, _ = np.linalg.svd(Xn, full_matrices=False)
    eigenvalues = s ** 2
    pc1_frac = float(eigenvalues[0] / eigenvalues.sum()) if eigenvalues.sum() > 0 else 0.0

    return PhenomenalUnityResult(
        unity_index=float(np.clip(unity, 0.0, 1.0)),
        pc1_fraction=float(np.clip(pc1_frac, 0.0, 1.0)),
        unity_class=_classify(unity),
        n_dimensions=k,
        dimension_names=dims,
        n_timepoints=T,
        correlation_matrix=R.tolist(),
    )
