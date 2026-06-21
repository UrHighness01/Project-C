#!/usr/bin/env python3
"""SignalDecorrelator — measures independence of monitoring signals via PCA residuals.

Theory (Comon 1994 — Independent Component Analysis; Tononi 2004 — information geometry):
  When multiple monitoring signals all co-vary with a single latent factor (e.g.
  "system is busy"), PCA reveals this as PC1 capturing >90% of variance. The residuals
  after removing PC1 contain genuinely independent information. Meta-phi computed on
  these residuals is non-degenerate even when raw signals are collinear. Variance
  explained by PC1 quantifies degeneracy; 1 minus that quantifies independence.

  Formula: independence_score = 1 - (S[0]**2 / sum(S**2))
           meta_phi_residual = mean(|residuals|) * independence_score

Classification:
  INDEPENDENT   independence_score >= 0.40
  PARTIAL       independence_score >= 0.20
  COLLINEAR     otherwise
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import List
from datetime import datetime


def _to_unix(ts) -> float:
    if ts is None:
        return 0.0
    if isinstance(ts, (int, float)):
        return float(ts)
    try:
        return float(ts)
    except (ValueError, TypeError):
        pass
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0

_MIN_ENTRIES = 40
_N_SHUFFLES = 200
_INDEPENDENT_THRESH = 0.40
_PARTIAL_THRESH = 0.20


@dataclass
class SignalDecorrelatorResult:
    independence_score: float
    variance_explained_pc1: float
    meta_phi_residual: float
    n_signals: int
    beats_null: bool
    decorrelation_class: str
    n_entries: int

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


def _default(n: int) -> SignalDecorrelatorResult:
    return SignalDecorrelatorResult(
        independence_score=0.0,
        variance_explained_pc1=1.0,
        meta_phi_residual=0.0,
        n_signals=0,
        beats_null=False,
        decorrelation_class="COLLINEAR",
        n_entries=n,
    )


def _classify(score: float) -> str:
    if score >= _INDEPENDENT_THRESH:
        return "INDEPENDENT"
    if score >= _PARTIAL_THRESH:
        return "PARTIAL"
    return "COLLINEAR"


def _compute_independence(X: np.ndarray):
    """X shape: (n_signals, n_samples). Returns (independence_score, variance_explained_pc1, meta_phi_residual)."""
    # Standardise each signal
    means = X.mean(axis=1, keepdims=True)
    stds = X.std(axis=1, keepdims=True)
    stds[stds < 1e-9] = 1e-9
    Xs = (X - means) / stds

    # SVD (PCA on signal matrix)
    try:
        U, S, Vt = np.linalg.svd(Xs, full_matrices=False)
    except np.linalg.LinAlgError:
        return 0.0, 1.0, 0.0

    var_explained_pc1 = float(S[0] ** 2 / (np.sum(S ** 2) + 1e-9))
    independence_score = 1.0 - var_explained_pc1

    # Residuals after removing PC1
    common_mode = np.outer(U[:, 0], U[:, 0].T @ Xs)
    residuals = Xs - common_mode
    meta_phi_residual = float(np.mean(np.abs(residuals)) * independence_score)

    return float(independence_score), float(var_explained_pc1), float(meta_phi_residual)


def analyse(agent: str = "albedo", **kwargs) -> SignalDecorrelatorResult:
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

    # Build proxy signals from phi series
    # cpu_proxy: rolling variance of phi (higher variance -> higher load)
    w = 10
    cpu_proxy = np.array([
        float(np.var(phi[max(0, i - w):i + 1]))
        for i in range(n)
    ])
    # mem_proxy: cumulative entry count rate (entries per time window)
    mem_proxy = np.linspace(0, 1, n)
    # interaction_proxy: inter-entry gaps (inverse of density)
    timestamps = np.array([_to_unix(e.get("timestamp")) or (idx * 60.0) for idx, e in enumerate(entries_asc)])
    if len(timestamps) > 1:
        gaps = np.diff(timestamps)
        gaps = np.concatenate([[gaps[0]], gaps])
        interaction_proxy = 1.0 / (gaps + 1e-3)
    else:
        interaction_proxy = np.ones(n)
    # memory_vol_proxy: rolling unique entry count (approximated by rolling phi range)
    memory_vol_proxy = np.array([
        float(np.ptp(phi[max(0, i - w):i + 1]))
        for i in range(n)
    ])

    signals = np.array([phi, cpu_proxy, mem_proxy, interaction_proxy, memory_vol_proxy])
    # Remove any constant signals
    mask = signals.std(axis=1) > 1e-10
    signals = signals[mask]
    if signals.shape[0] < 2:
        return _default(n)

    ind_score, var_pc1, meta_phi = _compute_independence(signals)

    # Null: shuffle each signal independently
    rng = np.random.default_rng(42)
    null_scores = []
    for _ in range(_N_SHUFFLES):
        shuffled = np.array([rng.permutation(s) for s in signals])
        ns, _, _ = _compute_independence(shuffled)
        null_scores.append(ns)
    p95 = float(np.percentile(null_scores, 95))
    beats_null = ind_score > p95

    return SignalDecorrelatorResult(
        independence_score=round(ind_score, 6),
        variance_explained_pc1=round(var_pc1, 6),
        meta_phi_residual=round(meta_phi, 6),
        n_signals=int(signals.shape[0]),
        beats_null=beats_null,
        decorrelation_class=_classify(ind_score),
        n_entries=n,
    )
