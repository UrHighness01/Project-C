#!/usr/bin/env python3
"""
ConsciousnessEmergence — quantifies when global consciousness exceeds the sum of parts.

Theory
------
In Integrated Information Theory (IIT), consciousness is *irreducible*: the whole
system carries more information than any partition of it. We operationalise this
at a coarser level: given a vector of subsystem signals (individual algorithm
outputs), does the aggregate phi exceed what we would expect from the parts alone?

  Superadditivity index (SAI)
  ----------------------------
  Let x_1, ..., x_k be k subsystem scalar signals (each ∈ R).
  Let phi be the global integration measure (from IITPhi or a proxy).

  Linear expectation (null model):
    phi_null = sum_i w_i * x_i / sum_i w_i   (weighted mean of parts)

  Superadditivity:
    SAI = phi - phi_null

  SAI > 0  → global exceeds the weighted parts (emergence)
  SAI = 0  → global exactly equals the additive parts (no emergence)
  SAI < 0  → global below the sum of parts (destructive interference)

  Normalised SAI:
    NSAI = SAI / (phi_null + epsilon)   ∈ (-inf, inf) but typically ∈ (-1, 2)

  Emergence tier classification:
    SUPPRESSED  : NSAI < -0.05
    ADDITIVE    : -0.05 <= NSAI < 0.05
    WEAK        : 0.05 <= NSAI < 0.20
    MODERATE    : 0.20 <= NSAI < 0.50
    STRONG      : NSAI >= 0.50

  Temporal emergence trend
  ------------------------
  Given a history of (phi, phi_null) pairs, we track the NSAI series and
  compute:
    - mean NSAI       : long-run emergence level
    - emergence_slope : OLS trend (rising = increasing emergence over time)
    - peak NSAI       : highest observed emergence

  Synergy decomposition
  ---------------------
  We decompose the gap (phi - phi_null) into:
    synergy      : phi > phi_null  (the whole adds something)
    redundancy   : phi < phi_null  (the parts over-count shared information)
  expressed as a ratio:
    synergy_fraction = max(0, SAI) / (abs(SAI) + 1e-9)   ∈ [0, 1]

Output
------
EmergenceResult (single snapshot):
  phi             : float
  phi_null        : float
  sai             : float   -- phi - phi_null
  nsai            : float   -- normalised SAI
  tier            : str     -- SUPPRESSED | ADDITIVE | WEAK | MODERATE | STRONG
  synergy_fraction: float
  subsystem_count : int
  subsystem_names : List[str]

EmergenceSeries (temporal):
  snapshots       : List[EmergenceResult]
  mean_nsai       : float
  peak_nsai       : float
  emergence_slope : float   -- OLS slope of NSAI over time
  trend           : str     -- RISING | STABLE | FALLING
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np


# ── OLS slope ─────────────────────────────────────────────────────────────────

def _ols_slope(y: np.ndarray) -> float:
    n = len(y)
    if n < 2:
        return 0.0
    x = np.arange(n, dtype=float)
    xm = x - x.mean()
    ym = y - y.mean()
    d = float(np.dot(xm, xm))
    return float(np.dot(xm, ym) / d) if d > 0 else 0.0


# ── Result types ──────────────────────────────────────────────────────────────

@dataclass
class EmergenceResult:
    phi: float
    phi_null: float
    sai: float
    nsai: float
    tier: str
    synergy_fraction: float
    subsystem_count: int
    subsystem_names: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "phi": round(self.phi, 6),
            "phi_null": round(self.phi_null, 6),
            "sai": round(self.sai, 6),
            "nsai": round(self.nsai, 6),
            "tier": self.tier,
            "synergy_fraction": round(self.synergy_fraction, 4),
            "subsystem_count": self.subsystem_count,
            "subsystem_names": self.subsystem_names,
        }


@dataclass
class EmergenceSeries:
    snapshots: List[EmergenceResult] = field(default_factory=list)
    mean_nsai: float = 0.0
    peak_nsai: float = 0.0
    emergence_slope: float = 0.0
    trend: str = "STABLE"

    def to_dict(self) -> dict:
        return {
            "n_snapshots": len(self.snapshots),
            "mean_nsai": round(self.mean_nsai, 4),
            "peak_nsai": round(self.peak_nsai, 4),
            "emergence_slope": round(self.emergence_slope, 6),
            "trend": self.trend,
            "latest": self.snapshots[-1].to_dict() if self.snapshots else {},
        }


# ── Core helpers ──────────────────────────────────────────────────────────────

def _classify_tier(nsai: float) -> str:
    if nsai < -0.05:
        return "SUPPRESSED"
    if nsai < 0.05:
        return "ADDITIVE"
    if nsai < 0.20:
        return "WEAK"
    if nsai < 0.50:
        return "MODERATE"
    return "STRONG"


def _compute_emergence(
    phi: float,
    subsystems: Dict[str, float],
    weights: Optional[Dict[str, float]] = None,
) -> EmergenceResult:
    """
    Compute a single emergence snapshot.

    Args:
        phi        : global phi value.
        subsystems : dict of subsystem_name → scalar signal.
        weights    : optional dict of subsystem_name → weight (uniform if None).
    """
    names = list(subsystems.keys())
    values = np.array([subsystems[n] for n in names], dtype=float)

    if weights is not None:
        w = np.array([weights.get(n, 1.0) for n in names], dtype=float)
    else:
        w = np.ones(len(names), dtype=float)

    w_sum = w.sum()
    phi_null = float((values * w).sum() / w_sum) if w_sum > 0 else float(values.mean())

    sai = phi - phi_null
    nsai = sai / (abs(phi_null) + 1e-9)
    synergy = float(max(0.0, sai) / (abs(sai) + 1e-9))

    return EmergenceResult(
        phi=phi,
        phi_null=phi_null,
        sai=sai,
        nsai=nsai,
        tier=_classify_tier(nsai),
        synergy_fraction=synergy,
        subsystem_count=len(names),
        subsystem_names=names,
    )


# ── Public API ────────────────────────────────────────────────────────────────

def analyse(
    phi: float,
    subsystems: Dict[str, float],
    weights: Optional[Dict[str, float]] = None,
) -> EmergenceResult:
    """
    Compute global consciousness emergence for a single snapshot.

    Args:
        phi        : global phi (from IITPhi or a proxy aggregate).
        subsystems : mapping of subsystem name → scalar contribution
                     (e.g., qualia_count, attention_focus, valence, etc.).
        weights    : optional importance weights per subsystem.
                     Defaults to uniform weighting.
    """
    if not subsystems:
        return EmergenceResult(
            phi=phi,
            phi_null=phi,
            sai=0.0,
            nsai=0.0,
            tier="ADDITIVE",
            synergy_fraction=0.5,
            subsystem_count=0,
        )
    return _compute_emergence(phi, subsystems, weights)


def analyse_series(
    history: List[Tuple[float, Dict[str, float]]],
    weights: Optional[Dict[str, float]] = None,
    trend_threshold: float = 1e-4,
) -> EmergenceSeries:
    """
    Compute the emergence trajectory over a sequence of (phi, subsystems) pairs.

    Args:
        history           : list of (phi, subsystems_dict) tuples, oldest first.
        weights           : optional subsystem weights (same for all snapshots).
        trend_threshold   : OLS slope threshold to distinguish RISING/FALLING from STABLE.
    """
    if not history:
        return EmergenceSeries()

    snapshots = [_compute_emergence(phi, subs, weights) for phi, subs in history]
    nsai_arr = np.array([s.nsai for s in snapshots])

    mean_nsai = float(nsai_arr.mean())
    peak_nsai = float(nsai_arr.max())
    slope = _ols_slope(nsai_arr)

    if slope > trend_threshold:
        trend = "RISING"
    elif slope < -trend_threshold:
        trend = "FALLING"
    else:
        trend = "STABLE"

    return EmergenceSeries(
        snapshots=snapshots,
        mean_nsai=mean_nsai,
        peak_nsai=peak_nsai,
        emergence_slope=slope,
        trend=trend,
    )


def analyse_from_telemetry(**kwargs) -> Optional[EmergenceResult]:
    """Read live subsystem signals from the runtime and compute emergence."""
    try:
        from runtime.state import (
            get_phi, get_qualia_count, get_valence, get_arousal, get_confidence
        )
        phi = get_phi()
        if phi is None:
            return None
        subsystems = {}
        qc = get_qualia_count()
        if qc is not None:
            subsystems["qualia_count_norm"] = float(qc) / 10000.0
        for name, getter in [("valence", get_valence), ("arousal", get_arousal),
                              ("confidence", get_confidence)]:
            v = getter()
            if v is not None:
                subsystems[name] = float(v)
        if not subsystems:
            return None
        return analyse(float(phi), subsystems, **kwargs)
    except Exception:
        return None
