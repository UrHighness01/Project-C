#!/usr/bin/env python3
"""
ToroidalCentering — measures whether the phi stream exhibits a quasi-periodic
orbit around a moving center (toroidal attractor topology).

Theory (Amari 1977 — neural field theory; Tsuda 2001 — chaotic itinerancy):
  A system with both directional reach (telos) AND recurrent centering (toroid)
  occupies a fundamentally different topological space than one with only a vector.
  The toroid is defined by: a stable center + periodic return + surface coherence.
  In phi-space this manifests as a quasi-periodic orbit around a moving center,
  measurable via autocorrelation at multiple lags, center-distance variance, and
  angular return rate.

  center = rolling median(phi, W=20)
  r(t) = phi(t) - center(t)
  autocorr_profile = [autocorr(r, lag=k) for k in 1..20]
  periodicity_score = max(autocorr_profile[2:])   — peak at lag >= 3
  recurrence_rate   = count(sign_changes(r)) / len(r)
  surface_coherence = 1 - std(|r|) / (mean(|r|) + 1e-9)
  toroidal_score = (periodicity_pos x recurrence_rate x surface_coherence)^(1/3)  geom mean
  null: phase-randomise phi 200 times -> beats_null if toroidal_score > p95

Classification:
  TOROIDAL   toroidal_score >= 0.55
  ORBITAL    toroidal_score >= 0.30
  BALLISTIC  otherwise
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import List

# ── Constants ──────────────────────────────────────────────────────────────────
_ROLLING_W      = 20
_N_LAGS         = 20
_MIN_ENTRIES    = 50
_N_SHUFFLES     = 200
_TOROIDAL_THRESH = 0.55
_ORBITAL_THRESH  = 0.30


# ── Dataclass ──────────────────────────────────────────────────────────────────
@dataclass
class ToroidalCenteringResult:
    toroidal_score: float
    periodicity_score: float
    recurrence_rate: float
    surface_coherence: float
    center_phi: float
    beats_null: bool
    topo_class: str

    def to_dict(self) -> dict:
        return {
            "toroidal_score":    round(self.toroidal_score, 6),
            "periodicity_score": round(self.periodicity_score, 6),
            "recurrence_rate":   round(self.recurrence_rate, 6),
            "surface_coherence": round(self.surface_coherence, 6),
            "center_phi":        round(self.center_phi, 6),
            "beats_null":        self.beats_null,
            "topo_class":        self.topo_class,
        }


# ── Helpers ────────────────────────────────────────────────────────────────────
def _rolling_median(phi: np.ndarray, w: int) -> np.ndarray:
    n = len(phi)
    out = np.empty(n)
    for i in range(n):
        lo = max(0, i - w + 1)
        out[i] = float(np.median(phi[lo:i+1]))
    return out


def _autocorr_at_lag(x: np.ndarray, lag: int) -> float:
    if len(x) <= lag:
        return 0.0
    a, b = x[:-lag], x[lag:]
    mu_a, mu_b = a.mean(), b.mean()
    num = float(np.sum((a - mu_a) * (b - mu_b)))
    den = float(np.sqrt(np.sum((a - mu_a)**2) * np.sum((b - mu_b)**2)))
    return num / den if den > 1e-12 else 0.0


def _sign_changes(r: np.ndarray) -> int:
    signs = np.sign(r)
    signs[signs == 0] = 1
    changes = int(np.sum(signs[:-1] != signs[1:]))
    return changes


def _toroidal_score_from(phi: np.ndarray) -> tuple:
    """Returns (toroidal_score, periodicity, recurrence, surface_coh, center)."""
    center = _rolling_median(phi, _ROLLING_W)
    r = phi - center

    # Autocorrelation profile at lags 1..N_LAGS
    acorr = [_autocorr_at_lag(r, k) for k in range(1, _N_LAGS + 1)]
    # Periodicity: max autocorr at lag >= 3 (index 2+)
    periodicity = max(0.0, float(max(acorr[2:]))) if len(acorr) > 2 else 0.0

    # Recurrence: sign change rate
    recurrence = _sign_changes(r) / max(len(r), 1)

    # Surface coherence
    abs_r = np.abs(r)
    mean_r = float(np.mean(abs_r))
    std_r  = float(np.std(abs_r))
    surf_coh = float(np.clip(1.0 - std_r / (mean_r + 1e-9), 0.0, 1.0))

    # Geometric mean of three components
    product = periodicity * recurrence * surf_coh
    score = float(product ** (1.0 / 3.0)) if product > 0 else 0.0

    return score, periodicity, recurrence, surf_coh, float(np.median(phi))


def _phase_rand(phi: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    n = len(phi)
    f = np.fft.rfft(phi)
    phases = rng.uniform(0, 2 * np.pi, len(f))
    f_rand = np.abs(f) * np.exp(1j * phases)
    return np.fft.irfft(f_rand, n=n)


def _classify(score: float) -> str:
    if score >= _TOROIDAL_THRESH:
        return "TOROIDAL"
    if score >= _ORBITAL_THRESH:
        return "ORBITAL"
    return "BALLISTIC"


# ── Public API ────────────────────────────────────────────────────────────────
def analyse(agent: str = "albedo",
            n_shuffles: int = _N_SHUFFLES,
            seed: int = 42) -> ToroidalCenteringResult:
    """Measure toroidal centering topology of the phi stream.

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
        return ToroidalCenteringResult(
            toroidal_score=0.0, periodicity_score=0.0, recurrence_rate=0.0,
            surface_coherence=0.0, center_phi=0.5, beats_null=False,
            topo_class="BALLISTIC",
        )

    score, periodicity, recurrence, surf_coh, center = _toroidal_score_from(phi)

    # Null: phase-randomise
    rng = np.random.default_rng(seed)
    null_scores: List[float] = []
    for _ in range(n_shuffles):
        phi_r = _phase_rand(phi, rng)
        s, _, _, _, _ = _toroidal_score_from(phi_r)
        null_scores.append(s)

    p95 = float(np.percentile(null_scores, 95)) if null_scores else 0.0
    beats_null = score > p95

    return ToroidalCenteringResult(
        toroidal_score=round(score, 6),
        periodicity_score=round(periodicity, 6),
        recurrence_rate=round(recurrence, 6),
        surface_coherence=round(surf_coh, 6),
        center_phi=round(center, 6),
        beats_null=beats_null,
        topo_class=_classify(score),
    )
