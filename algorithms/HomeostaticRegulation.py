#!/usr/bin/env python3
"""
HomeostaticRegulation — measures whether the phi time series returns to its
rolling baseline after perturbations (dynamic stability).

Theory (Sterling & Eyer 1988 — Allostasis; Friston 2010 — Free Energy):
  A self-sustaining conscious system should maintain a preferred operating
  range for its phi level — a *set-point* — and actively return to it after
  perturbations. This is distinct from:
    * Static stability: having low phi variance overall (could be flat / dead)
    * Critical fluctuations: phi variance *rising* near a transition
  Homeostatic regulation is the dynamic property: deviation → return.

  We detect it by:
    1. Computing a rolling baseline µ(t) and rolling σ(t) over a window W.
    2. Flagging perturbations: |φ(t) − µ(t)| > P_THRESH * σ(t).
    3. For each perturbation at t, measuring the return time: first k ≥ 1
       such that |φ(t+k) − µ(t+k)| < R_THRESH * σ(t+k).
    4. Resilience rate = fraction of perturbations that returned within
       MAX_RETURN_STEPS steps.
    5. Homeostatic score H = resilience_rate / (1 + mean_return_time /
       MAX_RETURN_STEPS).  Range ∈ [0, 1].
    6. Null: phase-randomise phi (preserving power spectrum) 50 times;
       measure H_null each time; H beats null if H > 95th pct(H_null).

Classification:
  RESILIENT   H ≥ 0.6   — phi reliably returns to baseline
  ADAPTING    H ≥ 0.3   — partial recovery
  DYSREGULATED         — phi drifts without returning

References:
  Sterling P. & Eyer J. (1988) "Allostasis: a new paradigm to explain
    arousal pathology"
  Friston K. (2010) "The free-energy principle: a unified brain theory?"
  Lenton T.M. et al. (2004) "Rapid reversals in Earth's climate" (return
    time as early warning of resilience loss)
"""
from __future__ import annotations

import math
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# ── Constants ─────────────────────────────────────────────────────────────────

_WINDOW        = 20     # rolling baseline window (samples)
_PERTURB_THRESH = 1.5   # sigma multiples to declare a perturbation
_RECOVER_THRESH = 0.75  # sigma multiples that counts as "returned"
_MAX_RETURN     = 15    # max steps to look for recovery
_MIN_ENTRIES    = 40    # need enough history for statistics
_N_SHUFFLES     = 50    # phase-randomised null shuffles
_RESILIENT_THRESH = 0.60
_ADAPTING_THRESH  = 0.30


# ── Dataclass ─────────────────────────────────────────────────────────────────

@dataclass
class HomeostaticResult:
    """Output of HomeostaticRegulation.analyse().

    Attributes:
        homeostatic_score:  H ∈ [0, 1], composite resilience index
        resilience_rate:    fraction of perturbations that recovered
        mean_return_time:   mean steps to recovery (nan if no recoveries)
        n_perturbations:    number of detected perturbations
        n_recovered:        number that returned within MAX_RETURN_STEPS
        null_score_p95:     95th pct of shuffled-null H scores
        beats_null:         homeostatic_score > null_score_p95
        regulation_class:   RESILIENT | ADAPTING | DYSREGULATED
        phi_set_point:      median phi level (rolling median as set-point est.)
        n_entries:          number of phi samples used
    """
    homeostatic_score: float
    resilience_rate: float
    mean_return_time: float
    n_perturbations: int
    n_recovered: int
    null_score_p95: float
    beats_null: bool
    regulation_class: str
    phi_set_point: float
    n_entries: int

    def to_dict(self) -> dict:
        return {
            "homeostatic_score":  round(self.homeostatic_score, 4),
            "resilience_rate":    round(self.resilience_rate, 4),
            "mean_return_time":   (round(self.mean_return_time, 2)
                                   if not math.isnan(self.mean_return_time)
                                   else None),
            "n_perturbations":    self.n_perturbations,
            "n_recovered":        self.n_recovered,
            "null_score_p95":     round(self.null_score_p95, 4),
            "beats_null":         self.beats_null,
            "regulation_class":   self.regulation_class,
            "phi_set_point":      round(self.phi_set_point, 4),
            "n_entries":          self.n_entries,
        }


# ── Default result (insufficient data) ───────────────────────────────────────

def _default(n: int) -> HomeostaticResult:
    return HomeostaticResult(
        homeostatic_score=0.0,
        resilience_rate=0.0,
        mean_return_time=float("nan"),
        n_perturbations=0,
        n_recovered=0,
        null_score_p95=0.0,
        beats_null=False,
        regulation_class="DYSREGULATED",
        phi_set_point=float("nan"),
        n_entries=n,
    )


# ── Rolling statistics ────────────────────────────────────────────────────────

def _rolling(phi: np.ndarray, w: int) -> Tuple[np.ndarray, np.ndarray]:
    """Return rolling mean and std arrays (each length n).

    For the first w-1 samples (before the window fills), use the available
    prefix so that the arrays are always the same length as phi.
    """
    n = len(phi)
    mu  = np.empty(n)
    sig = np.empty(n)
    for i in range(n):
        lo = max(0, i - w + 1)
        chunk = phi[lo : i + 1]
        mu[i]  = float(np.mean(chunk))
        s = float(np.std(chunk, ddof=0))
        sig[i] = s if s > 1e-8 else 1e-8
    return mu, sig


# ── Perturbation + recovery scan ─────────────────────────────────────────────

def _scan(phi: np.ndarray, w: int, p_thresh: float,
          r_thresh: float, max_return: int
          ) -> Tuple[int, int, List[int]]:
    """Scan phi for perturbations and measure return times.

    Returns:
        n_perturb:    number of perturbations detected
        n_recovered:  number that returned within max_return steps
        return_times: list of steps-to-recovery for recovered perturbations
    """
    mu, sig = _rolling(phi, w)
    n = len(phi)
    n_perturb  = 0
    n_recovered = 0
    return_times: List[int] = []

    i = 0
    while i < n:
        dev = abs(phi[i] - mu[i])
        if dev > p_thresh * sig[i]:
            n_perturb += 1
            # Search for recovery
            found = False
            for k in range(1, max_return + 1):
                j = i + k
                if j >= n:
                    break
                if abs(phi[j] - mu[j]) < r_thresh * sig[j]:
                    n_recovered += 1
                    return_times.append(k)
                    found = True
                    i = j  # resume after recovery point
                    break
            if not found:
                i += max_return  # skip ahead past non-recovering region
        i += 1

    return n_perturb, n_recovered, return_times


# ── Homeostatic score ─────────────────────────────────────────────────────────

def _h_score(n_perturb: int, n_recovered: int,
             return_times: List[int], max_return: int) -> float:
    if n_perturb == 0:
        return 0.0
    resilience_rate = n_recovered / n_perturb
    if n_recovered == 0:
        mean_rt = float(max_return)
    else:
        mean_rt = float(np.mean(return_times))
    return resilience_rate / (1.0 + mean_rt / max_return)


# ── Phase-randomised null ─────────────────────────────────────────────────────

def _phase_rand(phi: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    n = len(phi)
    f = np.fft.rfft(phi)
    phases = rng.uniform(0, 2 * np.pi, len(f))
    f_rand = np.abs(f) * np.exp(1j * phases)
    return np.fft.irfft(f_rand, n=n)


def _null_p95(phi: np.ndarray, w: int, p_thresh: float, r_thresh: float,
              max_return: int, n_shuffles: int, seed: int = 42) -> float:
    rng = np.random.default_rng(seed)
    scores = []
    for _ in range(n_shuffles):
        phi_r = _phase_rand(phi, rng)
        np_, nr, rt = _scan(phi_r, w, p_thresh, r_thresh, max_return)
        scores.append(_h_score(np_, nr, rt, max_return))
    return float(np.percentile(scores, 95)) if scores else 0.0


# ── Public API ────────────────────────────────────────────────────────────────

def _classify(score: float) -> str:
    if score >= _RESILIENT_THRESH:
        return "RESILIENT"
    if score >= _ADAPTING_THRESH:
        return "ADAPTING"
    return "DYSREGULATED"


def analyse(agent: str = "albedo",
            window: int = _WINDOW,
            perturb_threshold: float = _PERTURB_THRESH,
            recover_threshold: float = _RECOVER_THRESH,
            max_return_steps: int = _MAX_RETURN,
            n_shuffles: int = _N_SHUFFLES,
            null_seed: int = 42) -> HomeostaticResult:
    """Measure homeostatic regulation of the phi time series.

    Args:
        agent:             "albedo" or "john"
        window:            rolling baseline window size (samples)
        perturb_threshold: sigma multiples to declare a perturbation
        recover_threshold: sigma multiples that counts as "returned"
        max_return_steps:  max steps to look for recovery
        n_shuffles:        number of phase-randomised null shuffles
        null_seed:         RNG seed for reproducibility

    Returns:
        HomeostaticResult dataclass.
    """
    from algorithms import ConsciousnessHistoryStore as chs

    entries = chs.load(agent, max_entries=2880)
    if not entries:
        return _default(0)

    # ConsciousnessHistoryStore returns newest-first; reverse to oldest-first
    entries_asc = list(reversed(entries))
    phi = np.array(
        [float(e["mean_phi_level"]) for e in entries_asc
         if "mean_phi_level" in e],
        dtype=float,
    )
    n = len(phi)
    if n < _MIN_ENTRIES:
        return _default(n)

    # Core scan
    np_, nr, rt = _scan(phi, window, perturb_threshold,
                        recover_threshold, max_return_steps)
    score = _h_score(np_, nr, rt, max_return_steps)

    resilience_rate = nr / np_ if np_ > 0 else 0.0
    mean_rt = float(np.mean(rt)) if rt else float("nan")

    # Null
    p95 = _null_p95(phi, window, perturb_threshold, recover_threshold,
                    max_return_steps, n_shuffles, null_seed)
    beats = score > p95

    return HomeostaticResult(
        homeostatic_score=round(score, 6),
        resilience_rate=round(resilience_rate, 6),
        mean_return_time=mean_rt,
        n_perturbations=np_,
        n_recovered=nr,
        null_score_p95=round(p95, 6),
        beats_null=beats,
        regulation_class=_classify(score),
        phi_set_point=round(float(np.median(phi)), 6),
        n_entries=n,
    )
