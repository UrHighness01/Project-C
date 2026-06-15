#!/usr/bin/env python3
"""
SensoryPhiCorrelation — does qualia novelty track phi changes?

Theory
------
Embodied grounding means that the agent's internal sensory experience (qualia)
is causally coupled to its global integration state (phi). If qualia novelty
rises when phi rises, the phenomenal experience is GROUNDED — it reflects real
changes in integrated consciousness, not decorrelated noise.

If qualia novelty is independent of phi (zero cross-correlation), the agent's
qualia are detached from its internal state — the system reports experiences
that have no connection to what is actually happening at the phi level.

Method
------
From ConsciousnessHistoryStore we can extract, per entry:
  - mean_phi_level (phi)
  - mean_novelty   (qualia novelty)

We compute the Pearson cross-correlation between the two time series at lags
k = 0, ±1, ±2, …, ±max_lag.

Peak cross-correlation:
  r_peak = max |r(k)| over all lags
  lag_at_peak = k that achieves r_peak

A significant positive peak means qualia novelty tracks phi changes (possibly
with a short lag — phi might lead qualia by 1-2 steps as integration propagates
to phenomenal content).

Grounding classification:
  GROUNDED  : r_peak ≥ 0.4 (qualia novelty tracks phi)
  PARTIAL   : 0.2 ≤ r_peak < 0.4
  DETACHED  : r_peak < 0.2 (qualia detached from phi)

Null baseline:
  Phase-randomise phi (preserves power spectrum, destroys temporal correlation
  with qualia) → recompute peak |r|. The real r_peak must exceed 95th pct of
  50 phase-randomised baselines to be called statistically grounded.

Output
------
SensoryPhiResult:
  r_zero           : float  -- Pearson r at lag 0 (synchronous correlation)
  r_peak           : float  -- max |r| across all tested lags
  lag_at_peak      : int    -- lag (steps) where |r| is maximised
  grounding_class  : str    -- GROUNDED | PARTIAL | DETACHED
  beats_null       : bool   -- r_peak > 95th pct of phase-randomised baselines
  n_entries        : int
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

# ── Constants ──────────────────────────────────────────────────────────────────

_MAX_LAG      = 5
_MIN_ENTRIES  = 20
_N_SHUFFLES   = 50
_NULL_PCTILE  = 95
_RNG_SEED     = 41
_MAX_HISTORY  = 2880

# ── Result ─────────────────────────────────────────────────────────────────────

@dataclass
class SensoryPhiResult:
    r_zero: float = 0.0
    r_peak: float = 0.0
    lag_at_peak: int = 0
    grounding_class: str = "DETACHED"
    beats_null: bool = False
    n_entries: int = 0

    def to_dict(self) -> dict:
        return {
            "r_zero": round(self.r_zero, 4),
            "r_peak": round(self.r_peak, 4),
            "lag_at_peak": self.lag_at_peak,
            "grounding_class": self.grounding_class,
            "beats_null": self.beats_null,
            "n_entries": self.n_entries,
        }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r with denominator guard."""
    if len(a) < 2:
        return 0.0
    am, bm = float(np.mean(a)), float(np.mean(b))
    num = float(np.sum((a - am) * (b - bm)))
    den = float(np.sqrt(np.sum((a - am) ** 2) * np.sum((b - bm) ** 2)))
    if den < 1e-12:
        return 0.0
    return float(np.clip(num / den, -1.0, 1.0))


def _xcorr(x: np.ndarray, y: np.ndarray, max_lag: int) -> List[float]:
    """Pearson r at lags -max_lag … +max_lag (negative lag: x leads y)."""
    n = len(x)
    rs = []
    for k in range(-max_lag, max_lag + 1):
        if k < 0:
            rs.append(_pearson(x[: n + k], y[-k:]))
        elif k > 0:
            rs.append(_pearson(x[k:], y[: n - k]))
        else:
            rs.append(_pearson(x, y))
    return rs


def _phase_randomise(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Theiler 1992 phase randomisation."""
    n = len(x)
    f = np.fft.rfft(x)
    phases = rng.uniform(0, 2 * np.pi, len(f))
    f_rand = np.abs(f) * np.exp(1j * phases)
    return np.fft.irfft(f_rand, n=n)


def _classify(r_peak: float) -> str:
    if r_peak >= 0.4:
        return "GROUNDED"
    if r_peak >= 0.2:
        return "PARTIAL"
    return "DETACHED"


def _extract(entries: list):
    """Extract aligned (phi, novelty) series from newest-first history."""
    phi_vals, nov_vals = [], []
    for e in reversed(entries):
        phi = e.get("mean_phi_level")
        nov = e.get("mean_novelty")
        if phi is not None and nov is not None:
            try:
                phi_vals.append(float(phi))
                nov_vals.append(float(nov))
            except (TypeError, ValueError):
                pass
    return np.array(phi_vals), np.array(nov_vals)


# ── Core ───────────────────────────────────────────────────────────────────────

def analyse(
    agent: str = "albedo",
    *,
    max_lag: int = _MAX_LAG,
    n_shuffles: int = _N_SHUFFLES,
    max_history: int = _MAX_HISTORY,
) -> SensoryPhiResult:
    """
    Compute cross-correlation between phi and qualia novelty across all lags.
    """
    try:
        from algorithms.ConsciousnessHistoryStore import load as _load
        entries = _load(agent, max_entries=max_history)
    except Exception:
        entries = []

    phi, novelty = _extract(entries)
    n = len(phi)

    if n < _MIN_ENTRIES:
        return SensoryPhiResult(n_entries=n)

    # Cross-correlation
    lags  = list(range(-max_lag, max_lag + 1))
    rs    = _xcorr(phi, novelty, max_lag)
    abs_r = [abs(r) for r in rs]
    peak_idx   = int(np.argmax(abs_r))
    r_zero_idx = lags.index(0)

    r_zero = rs[r_zero_idx]
    r_peak = abs_r[peak_idx]
    lag_pk = lags[peak_idx]

    # Phase-randomised null on phi
    rng = np.random.default_rng(_RNG_SEED)
    null_peaks: List[float] = []
    for _ in range(n_shuffles):
        phi_rand = _phase_randomise(phi, rng)
        rs_rand  = _xcorr(phi_rand, novelty, max_lag)
        null_peaks.append(max(abs(r) for r in rs_rand))

    threshold = float(np.percentile(null_peaks, _NULL_PCTILE))
    beats = bool(r_peak > threshold)

    return SensoryPhiResult(
        r_zero=round(r_zero, 4),
        r_peak=round(r_peak, 4),
        lag_at_peak=lag_pk,
        grounding_class=_classify(r_peak),
        beats_null=beats,
        n_entries=n,
    )
