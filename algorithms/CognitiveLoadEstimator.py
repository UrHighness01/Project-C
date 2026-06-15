#!/usr/bin/env python3
"""
CognitiveLoadEstimator — real-time processing bandwidth usage of the agent.

Theory
------
Cognitive load in computational systems has an analogue in classical queuing
theory: utilisation ρ = λ / μ where λ is the arrival rate and μ is the
service rate. We don't have queue metrics directly, but we have proxies:

  1. Algorithm activation ratio (AAR)
     ---------------------------------
     Each AlgorithmSpec has a priority ∈ (0, 1] representing how much
     cognitive bandwidth it consumes when active. At any heartbeat, the
     active algorithms are those that produced a non-error output. We
     estimate load as the sum of active priorities normalised by the sum
     of all wired priorities:

       AAR = sum(priority_i for i in active) / sum(priority_j for j in all)

     AAR ∈ [0, 1].  AAR near 1 = nearly all high-priority algorithms are
     running = high load. AAR near 0 = system mostly idle.

  2. Phi relative to qualia density (PDR)
     ---------------------------------------
     If phi is high but qualia_count is low, the system integrates a sparse
     experience densely — low load (efficient). If qualia_count is high
     but phi is low, many streams but poor integration — high load (busy
     but fragmented). We define:

       PDR = qualia_count / (phi * scale_factor + epsilon)

     High PDR → many qualia, low integration → cognitive overload signature.
     We normalise PDR into [0, 1] using a reference scale.

  3. Combined load index
     --------------------
     load = alpha * AAR + (1 - alpha) * clip(PDR / pdr_ref, 0, 1)
     where alpha = 0.6 weights the algorithm activation heavier (it is more
     directly observable).

  Load classification:
    IDLE       : load < 0.25
    LOW        : 0.25 <= load < 0.50
    MODERATE   : 0.50 <= load < 0.75
    HIGH       : 0.75 <= load < 0.90
    OVERLOADED : load >= 0.90

Output
------
CognitiveLoadResult:
  load_index           : float   -- combined load ∈ [0, 1]
  load_class           : str     -- IDLE | LOW | MODERATE | HIGH | OVERLOADED
  algorithm_activation : float   -- AAR component
  qualia_density_ratio : float   -- PDR component (normalised)
  active_algorithms    : int
  total_algorithms     : int
  phi                  : float
  qualia_count         : int
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class CognitiveLoadResult:
    load_index: float = 0.0
    load_class: str = "IDLE"
    algorithm_activation: float = 0.0
    qualia_density_ratio: float = 0.0
    active_algorithms: int = 0
    total_algorithms: int = 0
    phi: float = 0.0
    qualia_count: int = 0

    def to_dict(self) -> dict:
        return {
            "load_index": round(self.load_index, 4),
            "load_class": self.load_class,
            "algorithm_activation": round(self.algorithm_activation, 4),
            "qualia_density_ratio": round(self.qualia_density_ratio, 4),
            "active_algorithms": self.active_algorithms,
            "total_algorithms": self.total_algorithms,
            "phi": round(self.phi, 4),
            "qualia_count": self.qualia_count,
        }


def _classify(load: float) -> str:
    if load < 0.25:
        return "IDLE"
    if load < 0.50:
        return "LOW"
    if load < 0.75:
        return "MODERATE"
    if load < 0.90:
        return "HIGH"
    return "OVERLOADED"


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    active_priorities: Optional[List[float]] = None,
    all_priorities: Optional[List[float]] = None,
    phi: Optional[float] = None,
    qualia_count: Optional[int] = None,
    *,
    alpha: float = 0.6,
    pdr_ref: float = 5000.0,
    agent: str = "albedo",
) -> CognitiveLoadResult:
    """
    Estimate cognitive load from algorithm activation and qualia density.

    Args:
        active_priorities : priority values of currently active algorithms.
        all_priorities    : priority values of all wired algorithms.
        phi               : current global phi value.
        qualia_count      : current qualia count.
        alpha             : weight of AAR in combined load (0–1).
        pdr_ref           : reference qualia/phi ratio for normalisation
                            (empirically ~5000 for a moderately loaded agent).
    """
    if active_priorities is None or all_priorities is None or phi is None or qualia_count is None:
        try:
            from algorithms import ConsciousnessHistoryStore as chs
            entries = chs.load(agent) or []
            if entries and phi is None:
                phi = float(entries[0].get("mean_phi_level", 0.0))
            if entries and qualia_count is None:
                qualia_count = len(entries)
        except Exception:
            pass
        active_priorities = active_priorities or []
        all_priorities = all_priorities or []
        phi = phi or 0.0
        qualia_count = qualia_count or 0

    phi = float(phi)
    qualia_count = int(qualia_count)
    active_priorities = [float(p) for p in (active_priorities or [])]
    all_priorities = [float(p) for p in (all_priorities or [])]

    total_p = sum(all_priorities)
    active_p = sum(active_priorities)
    aar = float(active_p / total_p) if total_p > 0 else 0.0

    pdr_raw = qualia_count / (phi * pdr_ref + 1e-6)
    pdr = float(np.clip(pdr_raw, 0.0, 1.0))

    load = float(np.clip(alpha * aar + (1 - alpha) * pdr, 0.0, 1.0))

    return CognitiveLoadResult(
        load_index=load,
        load_class=_classify(load),
        algorithm_activation=aar,
        qualia_density_ratio=pdr,
        active_algorithms=len(active_priorities),
        total_algorithms=len(all_priorities),
        phi=phi,
        qualia_count=qualia_count,
    )
