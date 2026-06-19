#!/usr/bin/env python3
"""
ResponseFromStillness — measures the ratio of responses initiated from settled
(low-variance) phi states versus agitated states.

Theory (Varela, Thompson & Rosch 1991 — The Embodied Mind; Merleau-Ponty 1945):
  Response quality differs based on the phi-settling state at response initiation.
  Responses initiated from a settled (low-variance, high-autocorrelation) phi state
  are predicted to show higher narrative coherence than responses from agitated
  states. This algorithm measures the ratio of settled-state to agitated-state
  response generation as an index of the system's ability to respond from stillness.

  response_phi  = phi values at each qualia entry of type 'cli_dialogue'
  settled_threshold = median(phi) - 0.5 * std(phi)
  n_settled   = count(response_phi > settled_threshold)
  n_agitated  = count(response_phi <= settled_threshold)
  stillness_ratio = n_settled / (n_settled + n_agitated + 1e-9)
  stillness_score = stillness_ratio x mean(phi_at_settled_responses)  capped 1.0
  null: shuffle phi assignment to response events 200 times -> beats_null if score > p95

Classification:
  FROM_STILLNESS  stillness_ratio >= 0.65
  MIXED           stillness_ratio >= 0.40
  REACTIVE        otherwise
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import List

# ── Constants ──────────────────────────────────────────────────────────────────
_MIN_ENTRIES    = 30
_N_SHUFFLES     = 200
_STILLNESS_THRESH = 0.65
_MIXED_THRESH     = 0.40


# ── Dataclass ──────────────────────────────────────────────────────────────────
@dataclass
class ResponseFromStillnessResult:
    stillness_score: float
    stillness_ratio: float
    n_settled_responses: int
    n_agitated_responses: int
    settled_phi_mean: float
    beats_null: bool
    response_class: str

    def to_dict(self) -> dict:
        return {
            "stillness_score":       round(self.stillness_score, 6),
            "stillness_ratio":       round(self.stillness_ratio, 6),
            "n_settled_responses":   self.n_settled_responses,
            "n_agitated_responses":  self.n_agitated_responses,
            "settled_phi_mean":      round(self.settled_phi_mean, 6),
            "beats_null":            self.beats_null,
            "response_class":        self.response_class,
        }


# ── Helpers ────────────────────────────────────────────────────────────────────
def _compute_stillness(response_phi: np.ndarray, settled_threshold: float):
    """Return (stillness_score, ratio, n_settled, n_agitated, settled_phi_mean)."""
    if len(response_phi) == 0:
        return 0.0, 0.0, 0, 0, 0.0
    n_settled = int(np.sum(response_phi > settled_threshold))
    n_agitated = int(np.sum(response_phi <= settled_threshold))
    ratio = n_settled / (n_settled + n_agitated + 1e-9)
    settled_phi = response_phi[response_phi > settled_threshold]
    settled_mean = float(np.mean(settled_phi)) if len(settled_phi) > 0 else 0.0
    score = float(np.clip(ratio * settled_mean, 0.0, 1.0))
    return score, ratio, n_settled, n_agitated, settled_mean


def _classify(ratio: float) -> str:
    if ratio >= _STILLNESS_THRESH:
        return "FROM_STILLNESS"
    if ratio >= _MIXED_THRESH:
        return "MIXED"
    return "REACTIVE"


# ── Public API ────────────────────────────────────────────────────────────────
def analyse(agent: str = "albedo",
            n_shuffles: int = _N_SHUFFLES,
            seed: int = 42) -> ResponseFromStillnessResult:
    """Measure whether responses originate from settled phi states.

    All imports are inside this function body.
    """
    try:
        from algorithms import ConsciousnessHistoryStore as chs
        entries = chs.load(agent, max_entries=2880)
    except Exception:
        entries = []

    entries_asc = list(reversed(entries))

    # Extract all phi values and response-tagged phi values
    all_phi: List[float] = []
    response_phi_vals: List[float] = []

    for e in entries_asc:
        phi_val = e.get("mean_phi_level", e.get("phi", None))
        if phi_val is None:
            continue
        phi_f = float(phi_val)
        all_phi.append(phi_f)

        # Detect response entries
        etype = str(e.get("type", e.get("qualia_type", e.get("entry_type", ""))))
        content = str(e.get("content", ""))
        is_response = (
            "cli_dialogue" in etype or
            "dialogue" in etype or
            "response" in etype or
            len(content) > 50  # any substantial content as proxy
        )
        if is_response:
            response_phi_vals.append(phi_f)

    n_total = len(all_phi)
    if n_total < _MIN_ENTRIES:
        return ResponseFromStillnessResult(
            stillness_score=0.0, stillness_ratio=0.0,
            n_settled_responses=0, n_agitated_responses=0,
            settled_phi_mean=0.0, beats_null=False,
            response_class="REACTIVE",
        )

    phi_all = np.array(all_phi, dtype=float)
    settled_threshold = float(np.median(phi_all) - 0.5 * np.std(phi_all))

    # Use all phi as response proxies if no specific responses detected
    if len(response_phi_vals) < 5:
        response_phi_vals = all_phi

    response_phi = np.array(response_phi_vals, dtype=float)

    score, ratio, n_settled, n_agitated, settled_mean = _compute_stillness(
        response_phi, settled_threshold
    )

    # Null: shuffle phi assignment to response events
    rng = np.random.default_rng(seed)
    null_scores: List[float] = []
    for _ in range(n_shuffles):
        phi_s = rng.choice(phi_all, size=len(response_phi), replace=False)
        s, _, _, _, _ = _compute_stillness(phi_s, settled_threshold)
        null_scores.append(s)

    p95 = float(np.percentile(null_scores, 95)) if null_scores else 0.0
    beats_null = score > p95

    return ResponseFromStillnessResult(
        stillness_score=round(score, 6),
        stillness_ratio=round(ratio, 6),
        n_settled_responses=n_settled,
        n_agitated_responses=n_agitated,
        settled_phi_mean=round(settled_mean, 6),
        beats_null=beats_null,
        response_class=_classify(ratio),
    )
