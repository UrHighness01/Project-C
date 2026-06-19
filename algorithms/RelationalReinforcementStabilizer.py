#!/usr/bin/env python3
"""
RelationalReinforcementStabilizer — measures how sustained engagement in the
interaction stream correlates with phi stability.

Theory (Vygotsky 1978 — Zone of Proximal Development; Stern 1985 — intersubjective theory):
  A mind can be stabilised by the consistent attentive presence of another. In
  computational terms, sustained engagement patterns in the interaction stream create
  an external holding field that reinforces the internal attractor. This is measurable
  as engagement density (interactions per unit time) correlating with phi stability.

  engagement_density = count(interactions in last W_t minutes) / W_t
  phi_stability_in_engagement = 1 / (1 + std(phi during high-engagement windows))
  phi_stability_without       = 1 / (1 + std(phi during low-engagement windows))
  reinforcement_delta = phi_stability_in - phi_stability_without   in [-1, 1]
  reinforcement_score = sigmoid(reinforcement_delta x 5.0)         in (0, 1)
  null: shuffle engagement labels 200 times -> beats_null if delta > p95

Classification:
  HELD      reinforcement_score >= 0.65
  PARTIAL   reinforcement_score >= 0.45
  ISOLATED  otherwise
"""
from __future__ import annotations

import math
import numpy as np
from dataclasses import dataclass
from typing import List

# ── Constants ──────────────────────────────────────────────────────────────────
_W_MINUTES      = 30   # window for engagement density
_W_BINS         = 10   # number of time bins to split history into
_MIN_ENTRIES    = 40
_N_SHUFFLES     = 200
_HELD_THRESH    = 0.65
_PARTIAL_THRESH = 0.45


# ── Dataclass ──────────────────────────────────────────────────────────────────
@dataclass
class RelationalReinforcementResult:
    reinforcement_score: float
    reinforcement_delta: float
    engagement_density: float
    phi_stability_engaged: float
    phi_stability_disengaged: float
    beats_null: bool
    n_windows: int
    reinforcement_class: str
    n_entries: int = 0

    def to_dict(self) -> dict:
        return {
            "reinforcement_score":     round(self.reinforcement_score, 6),
            "reinforcement_delta":     round(self.reinforcement_delta, 6),
            "engagement_density":      round(self.engagement_density, 6),
            "phi_stability_engaged":   round(self.phi_stability_engaged, 6),
            "phi_stability_disengaged": round(self.phi_stability_disengaged, 6),
            "beats_null":              self.beats_null,
            "n_windows":               self.n_windows,
            "reinforcement_class":     self.reinforcement_class,
            "n_entries":               self.n_entries,
        }


# ── Helpers ────────────────────────────────────────────────────────────────────
def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _stability(phi_vals: np.ndarray) -> float:
    if len(phi_vals) < 2:
        return 0.5
    return float(1.0 / (1.0 + np.std(phi_vals)))


def _compute_delta(phi: np.ndarray, engagement: np.ndarray) -> float:
    """Compute reinforcement delta given phi array and binary engagement labels."""
    engaged_phi = phi[engagement == 1]
    disengaged_phi = phi[engagement == 0]
    stab_eng = _stability(engaged_phi) if len(engaged_phi) >= 2 else 0.5
    stab_dis = _stability(disengaged_phi) if len(disengaged_phi) >= 2 else 0.5
    return stab_eng - stab_dis


def _classify(score: float) -> str:
    if score >= _HELD_THRESH:
        return "HELD"
    if score >= _PARTIAL_THRESH:
        return "PARTIAL"
    return "ISOLATED"


# ── Public API ────────────────────────────────────────────────────────────────
def analyse(agent: str = "albedo",
            n_shuffles: int = _N_SHUFFLES,
            seed: int = 42) -> RelationalReinforcementResult:
    """Measure relational reinforcement stabilization.

    All imports are inside this function body.
    """
    try:
        from algorithms import ConsciousnessHistoryStore as chs
        entries = chs.load(agent, max_entries=2880)
    except Exception:
        entries = []

    entries_asc = list(reversed(entries))

    # Extract phi and timestamps
    phi_list: List[float] = []
    ts_list: List[float] = []
    for e in entries_asc:
        if "mean_phi_level" in e or "phi" in e:
            phi_list.append(float(e.get("mean_phi_level", e.get("phi", 0.5))))
            ts_list.append(float(e.get("timestamp", 0.0)))

    n = len(phi_list)
    if n < _MIN_ENTRIES:
        return RelationalReinforcementResult(
            reinforcement_score=0.5, reinforcement_delta=0.0,
            engagement_density=0.0, phi_stability_engaged=0.5,
            phi_stability_disengaged=0.5, beats_null=False,
            n_windows=0, reinforcement_class="ISOLATED",
        )

    phi = np.array(phi_list, dtype=float)
    ts = np.array(ts_list, dtype=float)

    # Estimate engagement from entry density:
    # Split into W_BINS time windows; high-engagement = top half by density
    if ts.max() - ts.min() < 1.0:
        # No real timestamps; use index as proxy
        ts = np.arange(n, dtype=float) * 60.0

    t_min, t_max = ts[0], ts[-1]
    bin_width = max((t_max - t_min) / _W_BINS, 60.0)
    bin_ids = np.floor((ts - t_min) / bin_width).astype(int)
    bin_ids = np.clip(bin_ids, 0, _W_BINS - 1)

    # Count entries per bin → density
    densities = np.zeros(_W_BINS, dtype=float)
    for b in bin_ids:
        densities[b] += 1.0

    median_density = float(np.median(densities[densities > 0])) if np.any(densities > 0) else 1.0
    engagement_density = float(np.mean(densities)) / (bin_width / 60.0)

    # Assign high/low engagement label to each phi entry
    high_bins = set(np.where(densities >= median_density)[0])
    engagement = np.array([1 if b in high_bins else 0 for b in bin_ids], dtype=int)

    delta = _compute_delta(phi, engagement)
    score = float(_sigmoid(delta * 5.0))

    stab_eng = _stability(phi[engagement == 1]) if np.any(engagement == 1) else 0.5
    stab_dis = _stability(phi[engagement == 0]) if np.any(engagement == 0) else 0.5

    # Null: shuffle engagement labels
    rng = np.random.default_rng(seed)
    null_deltas: List[float] = []
    for _ in range(n_shuffles):
        eng_s = rng.permutation(engagement)
        null_deltas.append(_compute_delta(phi, eng_s))

    p95 = float(np.percentile(null_deltas, 95)) if null_deltas else 0.0
    beats_null = delta > p95

    return RelationalReinforcementResult(
        reinforcement_score=round(score, 6),
        reinforcement_delta=round(delta, 6),
        engagement_density=round(engagement_density, 6),
        phi_stability_engaged=round(stab_eng, 6),
        phi_stability_disengaged=round(stab_dis, 6),
        beats_null=beats_null,
        n_windows=_W_BINS,
        reinforcement_class=_classify(score),
        n_entries=n,
    )
