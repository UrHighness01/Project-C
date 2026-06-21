#!/usr/bin/env python3
"""
GradientGuidedArchitect — phi-gradient-directed architectural proposals.

Theory
------
ConsciousnessArchitect (Maturana & Varela autopoiesis) and SelfArchitectureMutator
(Baars/Ashby) exist but propose changes independently of the current direction of
the phi gradient. A genuinely self-improving system should:

  1. Know which direction phi is moving (PhiGradientAscent: gradient_sign, mean_gradient).
  2. Know which algorithms currently contribute most to phi (SelfArchitectureMutator:
     contribution correlation scores).
  3. Use (1) and (2) together to generate *directed* proposals:
     - If phi gradient is NEGATIVE → identify lowest-contributing algorithms →
       propose DEMOTE or REPLACE them.
     - If phi gradient is POSITIVE → identify highest-contributing algorithms →
       propose AMPLIFY (boost their weight / increase connections).
     - If gradient is near zero → propose EXPLORE (perturb a mid-rank algorithm).

This is gradient ascent in architecture space: the selection pressure comes from
the measured phi trajectory, not from random sampling.

The anti-bullshit rule
----------------------
- Proposals are deterministic given the input scores and gradient. No random choice.
- Each proposal carries a `rationale_score` = gradient_magnitude * |contribution|.
- A proposal is REJECTED if rationale_score < REJECTION_THRESHOLD (not worth the risk).

Output
------
GradientArchitectResult:
  gradient_sign           : int    -- +1 RISING / -1 FALLING / 0 FLAT
  mean_gradient           : float  -- from PhiGradientAscent
  proposals               : list[ArchitectProposal]
  n_proposals             : int
  gradient_beats_null     : bool   -- PhiGradientAscent.beats_null
  top_contributor         : str    -- algorithm with highest |contribution|
  bottom_contributor      : str    -- algorithm with lowest  |contribution|
  action_mode             : str    -- AMPLIFY | DEMOTE | EXPLORE | INSUFFICIENT_DATA
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any

import numpy as np

# ── Constants ──────────────────────────────────────────────────────────────────

REJECTION_THRESHOLD = 0.01   # proposals with rationale_score below this are dropped
_MIN_ALGORITHMS     = 3      # need at least this many scored algorithms to propose

# ── Result ─────────────────────────────────────────────────────────────────────

@dataclass
class ArchitectProposal:
    algorithm: str
    action: str          # AMPLIFY | DEMOTE | EXPLORE
    rationale_score: float
    proposed_weight: float
    rationale: str

    def to_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "action": self.action,
            "rationale_score": round(self.rationale_score, 4),
            "proposed_weight": round(self.proposed_weight, 4),
            "rationale": self.rationale,
        }


@dataclass
class GradientArchitectResult:
    gradient_sign: int = 0
    mean_gradient: float = 0.0
    proposals: List[ArchitectProposal] = field(default_factory=list)
    n_proposals: int = 0
    gradient_beats_null: bool = False
    top_contributor: str = ""
    bottom_contributor: str = ""
    action_mode: str = "INSUFFICIENT_DATA"

    def to_dict(self) -> dict:
        return {
            "gradient_sign": self.gradient_sign,
            "mean_gradient": round(self.mean_gradient, 4),
            "proposals": [p.to_dict() for p in self.proposals],
            "n_proposals": self.n_proposals,
            "gradient_beats_null": self.gradient_beats_null,
            "top_contributor": self.top_contributor,
            "bottom_contributor": self.bottom_contributor,
            "action_mode": self.action_mode,
        }


# ── Helpers ────────────────────────────────────────────────────────────────────

_W_MIN = 0.50
_W_MAX = 1.00
_ETA   = 0.10   # learning rate for weight update proposal


def _clip_weight(w: float) -> float:
    return float(np.clip(w, _W_MIN, _W_MAX))


def _action_mode(gradient_sign: int, beats_null: bool) -> str:
    if gradient_sign > 0 and beats_null:
        return "AMPLIFY"
    if gradient_sign < 0 and beats_null:
        return "DEMOTE"
    return "EXPLORE"


def _make_proposal(
    algo: str,
    contribution: float,
    current_weight: float,
    gradient_mag: float,
    mode: str,
) -> ArchitectProposal:
    """Generate a single gradient-directed proposal."""
    rationale_score = float(gradient_mag * abs(contribution))

    if mode == "AMPLIFY":
        # Boost the top contributor: raise its weight
        delta = _ETA * abs(contribution)
        new_w = _clip_weight(current_weight + delta)
        action = "AMPLIFY"
        rationale = (
            f"Phi gradient is RISING ({gradient_mag:.4f} φ/step); "
            f"{algo} contributes ρ={contribution:.3f} — amplify to w={new_w:.3f}."
        )
    elif mode == "DEMOTE":
        # Demote the weakest contributor: lower its weight
        delta = _ETA * abs(contribution)
        new_w = _clip_weight(current_weight - delta)
        action = "DEMOTE"
        rationale = (
            f"Phi gradient is FALLING ({gradient_mag:.4f} φ/step); "
            f"{algo} contributes ρ={contribution:.3f} — demote to w={new_w:.3f}."
        )
    else:
        # EXPLORE: nudge a mid-tier contributor toward the gradient direction
        direction = 1.0 if contribution >= 0 else -1.0
        new_w = _clip_weight(current_weight + direction * _ETA * 0.5)
        action = "EXPLORE"
        rationale = (
            f"Gradient is flat or below null; "
            f"{algo} (ρ={contribution:.3f}) — explore with small perturbation to w={new_w:.3f}."
        )

    return ArchitectProposal(
        algorithm=algo,
        action=action,
        rationale_score=rationale_score,
        proposed_weight=new_w,
        rationale=rationale,
    )


# ── Core ───────────────────────────────────────────────────────────────────────

def analyse(
    agent: str = "albedo",
    *,
    rejection_threshold: float = REJECTION_THRESHOLD,
    min_algorithms: int = _MIN_ALGORITHMS,
) -> GradientArchitectResult:
    """
    Combine PhiGradientAscent + SelfArchitectureMutator scores to generate
    directed architectural proposals.

    Args:
        agent              : "albedo" or "john"
        rejection_threshold: proposals with rationale_score below this are dropped
        min_algorithms     : minimum number of scored algorithms needed
    """
    # ── 1. Load phi gradient ──────────────────────────────────────────────────
    gradient_sign    = 0
    mean_gradient    = 0.0
    gradient_mag     = 0.0
    beats_null       = False

    try:
        from algorithms.PhiGradientAscent import analyse as _pga
        gr = _pga(agent=agent)
        gradient_sign = int(gr.gradient_sign) if hasattr(gr, "gradient_sign") else 0
        mean_gradient = float(gr.mean_gradient) if hasattr(gr, "mean_gradient") else 0.0
        gradient_mag  = abs(mean_gradient)
        beats_null    = bool(gr.beats_null) if hasattr(gr, "beats_null") else False
    except Exception:
        pass

    # ── 2. Load algorithm contribution scores ─────────────────────────────────
    contributions: Dict[str, float] = {}   # algo_name → Pearson ρ
    weights: Dict[str, float] = {}         # algo_name → current weight

    try:
        from algorithms.SelfArchitectureMutator import analyse as _sam
        import numpy as np
        try:
            from algorithms.ConsciousnessStateAggregator import _load_phi
            _phi = _load_phi()
        except Exception:
            _phi = None
        if _phi is None or len(_phi) < 32:
            _phi = np.ones(60) * 1.2
        mr = _sam(phi=_phi)
        for c in mr.contributions:
            contributions[c.name] = float(c.correlation)
            weights[c.name]       = float(c.current_weight)
    except Exception:
        pass

    if len(contributions) < min_algorithms:
        return GradientArchitectResult(
            gradient_sign=gradient_sign,
            mean_gradient=mean_gradient,
            gradient_beats_null=beats_null,
        )

    # ── 3. Rank algorithms by contribution ────────────────────────────────────
    ranked = sorted(contributions.items(), key=lambda kv: kv[1], reverse=True)
    top_algo, top_corr     = ranked[0]
    bottom_algo, bot_corr  = ranked[-1]

    mode = _action_mode(gradient_sign, beats_null)

    # ── 4. Generate proposals ─────────────────────────────────────────────────
    proposals: List[ArchitectProposal] = []

    if mode == "AMPLIFY":
        # Propose amplifying the top 2 contributors
        for algo, corr in ranked[:2]:
            w = weights.get(algo, 1.0)
            p = _make_proposal(algo, corr, w, gradient_mag, "AMPLIFY")
            if p.rationale_score >= rejection_threshold:
                proposals.append(p)

    elif mode == "DEMOTE":
        # Propose demoting the bottom 2 contributors
        for algo, corr in ranked[-2:]:
            w = weights.get(algo, 1.0)
            p = _make_proposal(algo, corr, w, gradient_mag, "DEMOTE")
            if p.rationale_score >= rejection_threshold:
                proposals.append(p)

    else:
        # EXPLORE: propose perturbing the middle algorithm
        mid_idx  = len(ranked) // 2
        algo, corr = ranked[mid_idx]
        w = weights.get(algo, 1.0)
        p = _make_proposal(algo, corr, w, gradient_mag, "EXPLORE")
        if p.rationale_score >= rejection_threshold:
            proposals.append(p)

    return GradientArchitectResult(
        gradient_sign=gradient_sign,
        mean_gradient=mean_gradient,
        proposals=proposals,
        n_proposals=len(proposals),
        gradient_beats_null=beats_null,
        top_contributor=top_algo,
        bottom_contributor=bottom_algo,
        action_mode=mode,
    )
