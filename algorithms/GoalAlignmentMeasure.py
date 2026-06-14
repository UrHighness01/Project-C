#!/usr/bin/env python3
"""
GoalAlignmentMeasure — compares active goals from both agents' goal-state.json
files, measures semantic similarity between them, and flags convergence or
divergence.

Theory
------
A goal is a named intention with an associated description (sometimes a list of
sub-goals). We model each goal as a token set drawn from its name + description
text and compute pairwise Jaccard similarity across all (Albedo_goal, John_goal)
pairs. From this matrix we derive:

  alignment_matrix[i,j] = Jaccard(goal_i_albedo, goal_j_john)

  mean_alignment   = mean of all pairwise scores
  max_alignment    = maximum pairwise score (best matching pair)
  n_aligned_pairs  = number of pairs with J > threshold (default 0.15)
  convergence_rate = n_aligned_pairs / (n_albedo_goals * n_john_goals)

Goal state schema (from goal_emergence.py)
------------------------------------------
The goal-state.json file is expected to have the structure:
  {
    "goals": [
      {
        "name": "goal name",
        "description": "...",
        "sub_goals": ["...", "..."],
        "active": true,
        ...
      }
    ]
  }

Only goals with "active": true (or without an "active" key, treated as active)
are considered.

Alignment classification
------------------------
  CONVERGENT  — mean_alignment > 0.25 AND n_aligned_pairs ≥ 1
  OVERLAPPING — mean_alignment ∈ [0.1, 0.25] OR (n_aligned_pairs ≥ 1 AND mean < 0.25)
  DIVERGENT   — mean_alignment < 0.1 AND n_aligned_pairs == 0

Output schema (JSON written to both workspaces)
-----------------------------------------------
{
  "timestamp": 1718000000.0,
  "n_albedo_goals": 3,
  "n_john_goals": 4,
  "alignment_class": "CONVERGENT",
  "mean_alignment": 0.31,
  "max_alignment": 0.55,
  "n_aligned_pairs": 3,
  "convergence_rate": 0.25,
  "best_pair": {
    "albedo_goal": "develop expertise in physics",
    "john_goal": "study quantum mechanics",
    "jaccard": 0.55
  },
  "goal_pairs": [...],
  "narrative": "Albedo (3 goals) and John (4 goals) are CONVERGENT..."
}
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# ── Tokeniser ─────────────────────────────────────────────────────────────────

_STOP = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "is", "it", "this", "that", "be", "are", "was", "were",
    "i", "my", "me", "we", "our", "you", "your", "they", "their", "have",
    "has", "had", "do", "does", "did", "not", "no", "so", "as", "by",
    "from", "will", "would", "can", "could", "should", "may", "might",
})


def _tokenise(text: str) -> Set[str]:
    if not isinstance(text, str):
        return set()
    tokens = re.findall(r"[a-z]{3,}", text.lower())
    return {t for t in tokens if t not in _STOP}


def _goal_tokens(goal: dict) -> Set[str]:
    parts = [str(goal.get("name", "")), str(goal.get("description", ""))]
    sub = goal.get("sub_goals", [])
    if isinstance(sub, list):
        parts.extend(str(s) for s in sub)
    return _tokenise(" ".join(parts))


def _jaccard(a: Set[str], b: Set[str]) -> float:
    u = len(a | b)
    return len(a & b) / u if u > 0 else 0.0


# ── Goal loading ──────────────────────────────────────────────────────────────

def _load_goals(agent: str) -> List[dict]:
    try:
        from runtime.agent import agent_home
        p = agent_home(agent) / "memory" / "goal-state.json"
    except Exception:
        return []
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
    except Exception:
        return []
    goals = data.get("goals", [])
    if not isinstance(goals, list):
        return []
    # Filter to active goals only
    return [g for g in goals if g.get("active", True)]


# ── Result dataclasses ────────────────────────────────────────────────────────

@dataclass
class GoalPair:
    albedo_goal: str
    john_goal: str
    jaccard: float

    def to_dict(self) -> dict:
        return {
            "albedo_goal": self.albedo_goal,
            "john_goal": self.john_goal,
            "jaccard": round(self.jaccard, 4),
        }


@dataclass
class AlignmentResult:
    timestamp: float
    n_albedo_goals: int
    n_john_goals: int
    alignment_class: str
    mean_alignment: float
    max_alignment: float
    n_aligned_pairs: int
    convergence_rate: float
    best_pair: Optional[GoalPair]
    goal_pairs: List[GoalPair] = field(default_factory=list)
    narrative: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "n_albedo_goals": self.n_albedo_goals,
            "n_john_goals": self.n_john_goals,
            "alignment_class": self.alignment_class,
            "mean_alignment": round(self.mean_alignment, 4),
            "max_alignment": round(self.max_alignment, 4),
            "n_aligned_pairs": self.n_aligned_pairs,
            "convergence_rate": round(self.convergence_rate, 4),
            "best_pair": self.best_pair.to_dict() if self.best_pair else None,
            "goal_pairs": [p.to_dict() for p in self.goal_pairs],
            "narrative": self.narrative,
        }


# ── Classification ────────────────────────────────────────────────────────────

def _classify(mean_alignment: float, n_aligned: int) -> str:
    if mean_alignment > 0.25 and n_aligned >= 1:
        return "CONVERGENT"
    if mean_alignment >= 0.1 or n_aligned >= 1:
        return "OVERLAPPING"
    return "DIVERGENT"


def _build_narrative(result: AlignmentResult) -> str:
    na = result.n_albedo_goals
    nj = result.n_john_goals

    if na == 0 and nj == 0:
        return "Neither agent has active goals on record."
    if na == 0:
        return f"Albedo has no active goals; John has {nj}. Alignment cannot be assessed."
    if nj == 0:
        return f"John has no active goals; Albedo has {na}. Alignment cannot be assessed."

    cls = result.alignment_class
    if cls == "CONVERGENT":
        quality = "are pulling toward the same objectives"
    elif cls == "OVERLAPPING":
        quality = "have partial overlap in their objectives"
    else:
        quality = "are currently pursuing divergent objectives"

    base = (
        f"Albedo ({na} goal{'s' if na != 1 else ''}) and "
        f"John ({nj} goal{'s' if nj != 1 else ''}) {quality}. "
        f"Mean alignment: {result.mean_alignment:.2f}, "
        f"max: {result.max_alignment:.2f}, "
        f"{result.n_aligned_pairs} aligned pair(s)."
    )
    if result.best_pair:
        base += (
            f" Best match: \"{result.best_pair.albedo_goal}\" ↔ "
            f"\"{result.best_pair.john_goal}\" "
            f"(J={result.best_pair.jaccard:.2f})."
        )
    return base


# ── Main ──────────────────────────────────────────────────────────────────────

def analyse(
    albedo_goals: Optional[List[dict]] = None,
    john_goals: Optional[List[dict]] = None,
    alignment_threshold: float = 0.15,
) -> AlignmentResult:
    """
    Measure goal alignment between Albedo and John.

    Args:
        albedo_goals       : list of goal dicts for Albedo (loaded from file if None).
        john_goals         : list of goal dicts for John (loaded from file if None).
        alignment_threshold: minimum Jaccard for a pair to count as "aligned".

    Returns:
        AlignmentResult
    """
    if albedo_goals is None:
        albedo_goals = _load_goals("albedo")
    if john_goals is None:
        john_goals = _load_goals("john")

    na = len(albedo_goals)
    nj = len(john_goals)

    if na == 0 or nj == 0:
        cls = "DIVERGENT"
        result = AlignmentResult(
            timestamp=time.time(),
            n_albedo_goals=na,
            n_john_goals=nj,
            alignment_class=cls,
            mean_alignment=0.0,
            max_alignment=0.0,
            n_aligned_pairs=0,
            convergence_rate=0.0,
            best_pair=None,
        )
        result.narrative = _build_narrative(result)
        return result

    # Build all pairwise Jaccard scores
    pairs: List[GoalPair] = []
    scores: List[float] = []
    for ag in albedo_goals:
        a_tok = _goal_tokens(ag)
        a_name = str(ag.get("name", "unnamed"))
        for jg in john_goals:
            j_tok = _goal_tokens(jg)
            j_name = str(jg.get("name", "unnamed"))
            j_score = _jaccard(a_tok, j_tok)
            pairs.append(GoalPair(
                albedo_goal=a_name,
                john_goal=j_name,
                jaccard=j_score,
            ))
            scores.append(j_score)

    # Sort pairs by descending Jaccard so top matches come first
    pairs.sort(key=lambda p: p.jaccard, reverse=True)

    mean_alignment = float(sum(scores) / len(scores)) if scores else 0.0
    max_alignment  = float(max(scores)) if scores else 0.0
    n_aligned      = sum(1 for s in scores if s >= alignment_threshold)
    conv_rate      = n_aligned / (na * nj) if na * nj > 0 else 0.0

    best_pair = pairs[0] if pairs else None
    cls = _classify(mean_alignment, n_aligned)

    result = AlignmentResult(
        timestamp=time.time(),
        n_albedo_goals=na,
        n_john_goals=nj,
        alignment_class=cls,
        mean_alignment=mean_alignment,
        max_alignment=max_alignment,
        n_aligned_pairs=n_aligned,
        convergence_rate=conv_rate,
        best_pair=best_pair,
        goal_pairs=pairs,
    )
    result.narrative = _build_narrative(result)
    return result


def save_result(result: AlignmentResult) -> List[Path]:
    """Write alignment result to both agents' memory directories."""
    written = []
    for agent in ("albedo", "john"):
        try:
            from runtime.agent import agent_home
            out = agent_home(agent) / "memory" / "goal_alignment.json"
        except Exception:
            out = Path(__file__).parent.parent / "memory" / f"goal_alignment_{agent}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result.to_dict(), indent=2))
        written.append(out)
    return written


def run_and_save(**kwargs) -> AlignmentResult:
    r = analyse(**kwargs)
    save_result(r)
    return r


# ── Standalone ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running GoalAlignmentMeasure…")
    r = run_and_save()
    print(f"  Albedo goals   : {r.n_albedo_goals}")
    print(f"  John goals     : {r.n_john_goals}")
    print(f"  Alignment      : {r.alignment_class}")
    print(f"  Mean J         : {r.mean_alignment:.3f}")
    print(f"  Max J          : {r.max_alignment:.3f}")
    print(f"  Aligned pairs  : {r.n_aligned_pairs}")
    print(f"  Narrative      : {r.narrative}")
