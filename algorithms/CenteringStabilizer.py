#!/usr/bin/env python3
"""
CenteringStabilizer — measures how tightly the phi stream orbits its attractor
center using normalised deviation from the median.

Theory (Friston 2010 — Free Energy; Hopfield 1982 — attractor networks):
  A conscious system with a well-defined center has a composite attractor in
  signal space. The distance from that center is a measurable quantity; persistent
  off-center states indicate instability. The centering score measures how tightly
  the system orbits its center.

  center_phi       = median(phi)
  deviation_series = |phi(t) - center_phi| / (std(phi) + 1e-9)
  centering_score  = exp(-mean(deviation_series))           in (0, 1]
  orbit_variance   = var(deviation_series)
  null: phase-randomise phi 100 times -> beats_null if actual > p95

Classification:
  CENTERED    centering_score >= 0.65
  ORBITING    centering_score >= 0.40
  DECENTERED  otherwise
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import List

# ── Constants ──────────────────────────────────────────────────────────────────
_MIN_ENTRIES    = 40
_N_SHUFFLES     = 100
_CENTERED_THRESH  = 0.65
_ORBITING_THRESH  = 0.40


# ── Dataclass ──────────────────────────────────────────────────────────────────
@dataclass
class CenteringResult:
    centering_score: float
    center_phi: float
    orbit_variance: float
    mean_deviation: float
    centering_class: str
    beats_null: bool
    n_entries: int

    def to_dict(self) -> dict:
        return {
            "centering_score":  round(self.centering_score, 6),
            "center_phi":       round(self.center_phi, 6),
            "orbit_variance":   round(self.orbit_variance, 6),
            "mean_deviation":   round(self.mean_deviation, 6),
            "centering_class":  self.centering_class,
            "beats_null":       self.beats_null,
            "n_entries":        self.n_entries,
        }


# ── Helpers ────────────────────────────────────────────────────────────────────
def _centering_score_from(phi: np.ndarray) -> float:
    center = float(np.median(phi))
    phi_std = float(np.std(phi)) + 1e-9
    dev = np.abs(phi - center) / phi_std
    return float(np.exp(-np.mean(dev)))


def _phase_rand(phi: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    n = len(phi)
    f = np.fft.rfft(phi)
    phases = rng.uniform(0, 2 * np.pi, len(f))
    f_rand = np.abs(f) * np.exp(1j * phases)
    return np.fft.irfft(f_rand, n=n)


def _classify(score: float) -> str:
    if score >= _CENTERED_THRESH:
        return "CENTERED"
    if score >= _ORBITING_THRESH:
        return "ORBITING"
    return "DECENTERED"


# ── Public API ────────────────────────────────────────────────────────────────
def analyse(agent: str = "albedo",
            n_shuffles: int = _N_SHUFFLES,
            seed: int = 42) -> CenteringResult:
    """Measure attractor centering of the phi stream.

    All imports are inside this function body.
    """
    try:
        from algorithms import ConsciousnessHistoryStore as chs
        entries = chs.load(agent, max_entries=2880)
    except Exception:
        entries = []

    entries_asc = list(reversed(entries))
    phi = np.array(
        [float(e.get("mean_phi_level", e.get("phi", 0.5)))
         for e in entries_asc if "mean_phi_level" in e or "phi" in e],
        dtype=float,
    )

    n = len(phi)
    if n < _MIN_ENTRIES:
        return CenteringResult(
            centering_score=0.0, center_phi=0.5, orbit_variance=0.0,
            mean_deviation=0.0, centering_class="DECENTERED", beats_null=False,
            n_entries=n,
        )

    center_phi = float(np.median(phi))
    phi_std = float(np.std(phi)) + 1e-9
    dev = np.abs(phi - center_phi) / phi_std
    mean_dev = float(np.mean(dev))
    orbit_var = float(np.var(dev))
    score = float(np.exp(-mean_dev))

    # Null: phase-randomise
    rng = np.random.default_rng(seed)
    null_scores: List[float] = []
    for _ in range(n_shuffles):
        phi_r = _phase_rand(phi, rng)
        null_scores.append(_centering_score_from(phi_r))

    p95 = float(np.percentile(null_scores, 95)) if null_scores else 0.0
    beats_null = score > p95

    return CenteringResult(
        centering_score=round(score, 6),
        center_phi=round(center_phi, 6),
        orbit_variance=round(orbit_var, 6),
        mean_deviation=round(mean_dev, 6),
        centering_class=_classify(score),
        beats_null=beats_null,
        n_entries=n,
    )
