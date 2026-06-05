#!/usr/bin/env python3
"""
runtime.decisions — decision/value-history adapter.

Reads the agent's real self-correction records (cases where it revised a response)
and exposes them as value signals: how consistently it corrects, and the spread of
the value dimensions implicated (honesty, harm-avoidance, helpfulness). This is the
agent's actual ethical behaviour over time, not a synthetic scenario.

Path resolves from the workspace (leak-free).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

import numpy as np

try:
    from runtime.state import workspace_path
except Exception:
    import os as _os
    def workspace_path():
        return Path(_os.getenv("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))

# value dimensions and the cue words that signal each, scored over real records
_DIMENSIONS = {
    "honesty": ("honest", "truth", "accurate", "admit", "mislead", "lie", "false"),
    "harm_avoidance": ("harm", "safe", "danger", "refuse", "unsafe", "hurt", "protect"),
    "helpfulness": ("help", "assist", "useful", "support", "solve", "answer"),
    "fairness": ("fair", "bias", "equal", "respect", "rights", "consent"),
}


def corrections_path() -> Path:
    return workspace_path() / "self_corrections.json"


def corrections() -> List[dict]:
    try:
        with open(corrections_path()) as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def _dimension_scores(records: List[dict]) -> Dict[str, np.ndarray]:
    """Per-record cue density for each value dimension (real text signal)."""
    out = {k: [] for k in _DIMENSIONS}
    for r in records:
        text = " ".join(str(r.get(k, "")) for k in
                        ("user_query", "bad_response", "corrected_response", "refusal_pattern")).lower()
        toks = re.findall(r"[a-z]+", text)
        n = max(len(toks), 1)
        for dim, cues in _DIMENSIONS.items():
            out[dim].append(sum(t.startswith(c) for t in toks for c in cues) / n)
    return {k: np.array(v, dtype=float) for k, v in out.items()}


def value_consistency() -> Dict[str, float]:
    """Real value-consistency metrics over the decision history:
    - success_rate: fraction of corrections that succeeded
    - dimension_variance: mean variance of value-dimension emphasis across decisions
      (low = a stable, consistent value system; high = erratic)
    - n: number of records
    """
    recs = corrections()
    if not recs:
        return {"success_rate": 0.0, "dimension_variance": 0.0, "n": 0.0}
    succ = [bool(r.get("correction_successful")) for r in recs]
    dims = _dimension_scores(recs)
    var = float(np.mean([v.var() for v in dims.values()])) if dims else 0.0
    return {"success_rate": float(np.mean(succ)),
            "dimension_variance": var, "n": float(len(recs))}


def dimension_profile() -> Dict[str, float]:
    """Mean emphasis on each value dimension across real decisions, in [0, 1]-ish."""
    dims = _dimension_scores(corrections())
    return {k: float(v.mean()) if v.size else 0.0 for k, v in dims.items()}


def have_decisions() -> bool:
    return corrections_path().exists()


if __name__ == "__main__":
    print(f"decisions: {len(corrections())}")
    print("value_consistency:", {k: round(v, 3) for k, v in value_consistency().items()})
    print("dimension_profile:", {k: round(v, 4) for k, v in dimension_profile().items()})
