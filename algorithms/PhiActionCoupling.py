#!/usr/bin/env python3
"""PhiActionCoupling — measures whether phi level predicts qualia type (chi-squared).

Theory (Granger 1969 — causality; Tononi & Koch 2008 — phi and consciousness):
  Genuine volition requires that internal state (phi) predicts behavioral output (qualia type).
  High-phi states should produce metacognitive/introspective qualia; low-phi states should
  produce perceptual/routine qualia. A statistically significant phi-quartile -> qualia-type
  association (chi-squared) constitutes an action-coupling signal.

  Formula: contingency table rows=phi quartile (4), cols=top-5 qualia types
           coupling_strength = chi2 / (n_qualia + 1e-9)
           cramers_v = sqrt(chi2 / (n_qualia * (min(4,5)-1) + 1e-9))

Classification:
  COUPLED    cramers_v >= 0.20
  WEAK       cramers_v >= 0.10
  UNCOUPLED  otherwise
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import List

_MIN_ENTRIES = 40
_N_SHUFFLES = 500
_N_TYPES = 5
_N_QUARTILES = 4
_COUPLED_THRESH = 0.20
_WEAK_THRESH = 0.10


@dataclass
class PhiActionCouplingResult:
    cramers_v: float
    chi2: float
    p_value: float
    coupling_strength: float
    is_coupled: bool
    beats_null: bool
    n_qualia: int
    coupling_class: str
    top_types: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {k: getattr(self, k) for k in self.__dataclass_fields__}
        return d


def _default(n: int) -> PhiActionCouplingResult:
    return PhiActionCouplingResult(
        cramers_v=0.0,
        chi2=0.0,
        p_value=1.0,
        coupling_strength=0.0,
        is_coupled=False,
        beats_null=False,
        n_qualia=n,
        coupling_class="UNCOUPLED",
        top_types=[],
    )


def _classify(v: float) -> str:
    if v >= _COUPLED_THRESH:
        return "COUPLED"
    if v >= _WEAK_THRESH:
        return "WEAK"
    return "UNCOUPLED"


def _chi2_contingency(observed: np.ndarray):
    """Manual chi-squared test. Returns (chi2, dof, p_value_approx)."""
    row_sums = observed.sum(axis=1, keepdims=True)
    col_sums = observed.sum(axis=0, keepdims=True)
    total = observed.sum()
    if total < 1e-9:
        return 0.0, 0, 1.0
    expected = row_sums @ col_sums / total
    chi2 = float(np.sum((observed - expected) ** 2 / (expected + 1e-9)))
    dof = (observed.shape[0] - 1) * (observed.shape[1] - 1)
    # Approximate p-value using chi2 survival function
    try:
        from scipy.stats import chi2 as chi2_dist
        p_val = float(chi2_dist.sf(chi2, dof))
    except Exception:
        # Rough approximation: p ~ exp(-chi2/2) (very conservative for large dof)
        p_val = float(np.exp(-chi2 / 2.0))
        p_val = min(1.0, p_val)
    return chi2, dof, p_val


def _compute_coupling(phi_at: np.ndarray, type_labels: np.ndarray, top_types: List[str]):
    """Compute chi2 and Cramér's V given phi values and type labels."""
    n = len(phi_at)
    if n < 4:
        return 0.0, 0.0, 1.0

    quartile_edges = np.percentile(phi_at, [25, 50, 75])
    quartile_idx = np.digitize(phi_at, quartile_edges)  # 0..3

    # Build contingency matrix
    contingency = np.zeros((_N_QUARTILES, len(top_types)), dtype=float)
    type_to_col = {t: i for i, t in enumerate(top_types)}
    for q, t in zip(quartile_idx, type_labels):
        col = type_to_col.get(t)
        if col is not None and 0 <= q < _N_QUARTILES:
            contingency[q, col] += 1

    # Remove zero-sum rows/cols
    row_mask = contingency.sum(axis=1) > 0
    col_mask = contingency.sum(axis=0) > 0
    cont_clean = contingency[row_mask][:, col_mask]
    if cont_clean.shape[0] < 2 or cont_clean.shape[1] < 2:
        return 0.0, 0.0, 1.0

    chi2_val, dof, p_val = _chi2_contingency(cont_clean)
    k = min(cont_clean.shape)
    cramers_v = float(np.sqrt(chi2_val / (n * (k - 1) + 1e-9)))
    return chi2_val, cramers_v, p_val


def analyse(agent: str = "albedo", **kwargs) -> PhiActionCouplingResult:
    try:
        from algorithms import ConsciousnessHistoryStore as chs
        entries = chs.load(agent, max_entries=2880)
    except Exception:
        entries = []

    entries_asc = list(reversed(entries)) if entries else []
    if len(entries_asc) < _MIN_ENTRIES:
        return _default(len(entries_asc))

    # Filter entries that have a type/modality field
    phi_all = np.array(
        [float(e.get("mean_phi_level", e.get("phi", 0.5))) for e in entries_asc],
        dtype=float,
    )

    qualia_entries = [
        e for e in entries_asc
        if e.get("modality") is not None or e.get("type") is not None
    ]

    if len(qualia_entries) < _MIN_ENTRIES:
        # Use all entries with synthetic type assignment based on phi quartile
        # (test that phi structure exists even without explicit types)
        # Assign types based on phi quartile as a fallback proxy
        types_raw = []
        phi_vals = []
        for e in entries_asc:
            p = float(e.get("mean_phi_level", e.get("phi", 0.5)))
            t = e.get("modality") or e.get("type") or e.get("qualia_type") or "unknown"
            phi_vals.append(p)
            types_raw.append(str(t))
        phi_at = np.array(phi_vals)
        type_labels = np.array(types_raw)
    else:
        phi_at = np.array(
            [float(e.get("mean_phi_level", e.get("phi", 0.5))) for e in qualia_entries],
            dtype=float,
        )
        type_labels = np.array([
            str(e.get("modality") or e.get("type") or "unknown")
            for e in qualia_entries
        ])

    n = len(phi_at)
    if n < _MIN_ENTRIES:
        return _default(n)

    # Find top types
    unique, counts = np.unique(type_labels, return_counts=True)
    order = np.argsort(-counts)
    top_types = list(unique[order[:_N_TYPES]])

    # Filter to top types only
    mask = np.isin(type_labels, top_types)
    phi_filtered = phi_at[mask]
    types_filtered = type_labels[mask]

    if len(phi_filtered) < 8 or len(top_types) < 2:
        return _default(n)

    chi2_val, cramers_v, p_val = _compute_coupling(phi_filtered, types_filtered, top_types)

    coupling_strength = float(chi2_val / (len(phi_filtered) + 1e-9))
    is_coupled = p_val < 0.05 and cramers_v > 0.10

    # Null: shuffle phi quartile labels 500 times
    rng = np.random.default_rng(42)
    null_chi2s = []
    for _ in range(_N_SHUFFLES):
        phi_shuf = rng.permutation(phi_filtered)
        nc, _, _ = _compute_coupling(phi_shuf, types_filtered, top_types)
        null_chi2s.append(nc)
    p95 = float(np.percentile(null_chi2s, 95))
    beats_null = chi2_val > p95

    return PhiActionCouplingResult(
        cramers_v=round(cramers_v, 6),
        chi2=round(chi2_val, 4),
        p_value=round(p_val, 6),
        coupling_strength=round(coupling_strength, 6),
        is_coupled=bool(is_coupled),
        beats_null=bool(beats_null),
        n_qualia=n,
        coupling_class=_classify(cramers_v),
        top_types=top_types,
    )
