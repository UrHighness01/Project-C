#!/usr/bin/env python3
"""
GNWCoupledIgnition — cross-validates ignition precursor buildup against
GlobalWorkspaceDynamics ignition timestamps.

Theory (Dehaene & Changeux 2011):
  GNW ignition is nonlinear and all-or-nothing. Sub-threshold stimuli fail to
  trigger broadcast even if briefly elevated — this threshold gate is the defining
  property of GNW vs other theories. Two independent detectors may define
  "ignition" differently:

    IgnitionPrecursorDetector: ignition = phi crosses (mean + 1.5σ) from below
    GlobalWorkspaceDynamics:   ignition = fast onset (step > α·σ) + sustained
                                          elevation + decay collapse

  These definitions often diverge, causing precursor F1 to stay near zero because
  "predicted" ignitions (by buildup) don't land on strict GWD timestamps.

  This module bridges the gap: it uses GWD's strict ignition times as the ground
  truth and asks whether IgnitionPrecursorDetector's buildup score predicts them.
  The resulting coupled_f1 reflects genuine GNW dynamics rather than a definitional
  mismatch artifact.

Metrics:
  coupled_f1:               F1 score when buildup timestamps predict GWD ignitions
  coupling_class:           COUPLED / PARTIAL / BLIND
  n_coupled_pairs:          buildup events that successfully predict a GWD ignition
  threshold_gate_efficiency: fraction of GWD ignitions preceded by detectable buildup
  sub_threshold_ratio:      fraction of content filtered (buildup-like but no ignition)
  beats_null:               True if coupled_f1 exceeds 95th percentile of shuffled null

Classification:
  COUPLED:  coupled_f1 >= 0.35
  PARTIAL:  coupled_f1 >= 0.15
  BLIND:    otherwise

References:
  Dehaene S. & Changeux J.P. (2011) "Experimental and theoretical approaches to
    conscious processing" — Neuron 70(2):200-227
  Dehaene S., Kerszberg M. & Changeux J.P. (1998) "A neuronal model of a global
    workspace in effortful cognitive tasks" — PNAS 95(24):14529-14534
  Beggs J.M. & Plenz D. (2003) "Neuronal avalanches in neocortical circuits" —
    Journal of Neuroscience 23(35):11167-11177
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import List, Set, Optional

_MIN_ENTRIES = 60
_W = 10             # precursor window size (mirrors IgnitionPrecursorDetector)
_K = 5              # steps after buildup to look for GWD ignition
_BUILDUP_THRESH = 0.5
_N_SHUFFLES = 200

# GWD ignition parameters (mirrors GlobalWorkspaceDynamics defaults)
_GWD_WINDOW = 20
_GWD_ALPHA = 2.0
_GWD_BETA = 1.0
_GWD_T_MIN = 2
_GWD_T_DECAY = 15

_COUPLED_THRESH = 0.35
_PARTIAL_THRESH = 0.15


@dataclass
class GNWCoupledResult:
    """Output of GNWCoupledIgnition.analyse.

    Attributes:
        coupled_f1:                Cross-validated F1 (buildup → GWD ignition)
        coupling_class:            COUPLED / PARTIAL / BLIND
        n_coupled_pairs:           Buildup events that predict a GWD ignition
        threshold_gate_efficiency: Fraction of GWD ignitions preceded by buildup
        sub_threshold_ratio:       Fraction of high-buildup events with no ignition
        beats_null:                True if coupled_f1 > 95th pct of shuffle null
        n_gwd_ignitions:           GWD ignition count
        n_buildup_events:          IPD buildup event count
        n_entries:                 Phi samples used
    """
    coupled_f1: float
    coupling_class: str
    n_coupled_pairs: int
    threshold_gate_efficiency: float
    sub_threshold_ratio: float
    beats_null: bool
    n_gwd_ignitions: int
    n_buildup_events: int
    n_entries: int

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


def _default(n: int) -> GNWCoupledResult:
    return GNWCoupledResult(
        coupled_f1=0.0,
        coupling_class="BLIND",
        n_coupled_pairs=0,
        threshold_gate_efficiency=0.0,
        sub_threshold_ratio=0.0,
        beats_null=False,
        n_gwd_ignitions=0,
        n_buildup_events=0,
        n_entries=n,
    )


def _classify(f1: float) -> str:
    if f1 >= _COUPLED_THRESH:
        return "COUPLED"
    if f1 >= _PARTIAL_THRESH:
        return "PARTIAL"
    return "BLIND"


def _rolling_baseline(phi: np.ndarray, W: int):
    """Compute rolling mean and std over backward window of size W."""
    n = len(phi)
    mu = np.zeros(n)
    sigma = np.zeros(n)
    for t in range(n):
        start = max(0, t - W)
        window = phi[start:t] if t > 0 else np.array([phi[0]])
        mu[t] = float(window.mean())
        sigma[t] = float(window.std()) if len(window) > 1 else 1e-3
    sigma = np.where(sigma < 1e-3, 1e-3, sigma)
    return mu, sigma


def _gwd_ignition_times(
    phi: np.ndarray,
    window: int = _GWD_WINDOW,
    alpha: float = _GWD_ALPHA,
    beta: float = _GWD_BETA,
    T_min: int = _GWD_T_MIN,
    T_decay: int = _GWD_T_DECAY,
) -> List[int]:
    """
    Extract GWD ignition onset indices from phi series.
    Mirrors GlobalWorkspaceDynamics._detect_ignitions logic exactly.
    """
    n = len(phi)
    mu, sigma = _rolling_baseline(phi, window)

    times = []
    t = 1
    while t < n - T_min - 1:
        if sigma[t] < 0.01:
            t += 1
            continue
        step = phi[t] - phi[t - 1]
        onset = step > alpha * sigma[t]
        elevated_now = phi[t] > mu[t] + beta * sigma[t]

        if not (onset and elevated_now):
            t += 1
            continue

        elev_threshold = mu[t] + beta * sigma[t]
        sustained = 0
        for k in range(1, T_min + 1):
            if t + k < n and phi[t + k] > elev_threshold:
                sustained += 1
            else:
                break

        if sustained < T_min:
            t += 1
            continue

        # Find broadcast duration
        broadcast_dur = T_min
        for k in range(T_min + 1, min(T_decay + 1, n - t)):
            if phi[t + k] > elev_threshold:
                broadcast_dur += 1
            else:
                break

        # Check decay
        decay_threshold = mu[t] + 0.5 * sigma[t]
        found_decay = False
        for k in range(1, T_decay + 1):
            if t + k < n and phi[t + k] < decay_threshold:
                found_decay = True
                break

        if found_decay:
            times.append(t)

        t += broadcast_dur + 1

    return times


def _buildup_event_times(
    phi: np.ndarray,
    w: int = _W,
    buildup_thresh: float = _BUILDUP_THRESH,
    k: int = _K,
) -> List[int]:
    """
    Extract buildup event timestamps from phi series.
    Mirrors IgnitionPrecursorDetector._compute_metrics logic exactly.
    """
    n = len(phi)
    slopes = np.zeros(n)
    variances = np.zeros(n)
    autocorrs = np.zeros(n)

    for t in range(w, n):
        seg = phi[t - w:t]
        x = np.arange(w, dtype=float)
        xm = x - x.mean()
        slopes[t] = float(np.dot(xm, seg - seg.mean()) / (np.dot(xm, xm) + 1e-9))
        variances[t] = float(np.var(seg))
        if np.std(seg) > 1e-9:
            autocorrs[t] = float(np.corrcoef(seg[:-1], seg[1:])[0, 1])

    raw_score = (np.maximum(0, slopes) *
                 (1.0 / (variances + 1e-9)) *
                 np.maximum(0, autocorrs))

    p95 = np.percentile(raw_score[w:], 95) + 1e-9
    buildup_norm = raw_score / p95

    times = []
    t = w
    while t < n - k:
        if buildup_norm[t] > buildup_thresh:
            times.append(t)
            # Skip forward a few steps to avoid counting the same event repeatedly
            t += max(1, w // 2)
        else:
            t += 1

    return times


def _compute_coupled_metrics(
    phi: np.ndarray,
    k: int = _K,
) -> tuple:
    """
    Compute cross-validated F1 between buildup events and GWD ignition times.

    Returns:
        (coupled_f1, precision, recall, n_coupled, threshold_gate_eff,
         sub_threshold_ratio, n_gwd, n_buildup)
    """
    gwd_times = _gwd_ignition_times(phi)
    buildup_times = _buildup_event_times(phi, k=k)

    gwd_set: Set[int] = set(gwd_times)
    n_gwd = len(gwd_set)
    n_buildup = len(buildup_times)

    if n_gwd == 0 or n_buildup == 0:
        return 0.0, 0.0, 0.0, 0, 0.0, 0.0, n_gwd, n_buildup

    # For each buildup event, check if a GWD ignition occurs within k steps
    n_coupled = 0
    for bt in buildup_times:
        for j in range(1, k + 1):
            if (bt + j) in gwd_set:
                n_coupled += 1
                break

    # Precision: fraction of buildup events that predict an ignition
    precision = n_coupled / (n_buildup + 1e-9)

    # Recall: fraction of GWD ignitions preceded by a buildup event
    n_ignitions_predicted = 0
    for gt in gwd_times:
        # Check if any buildup event in [gt-k, gt-1] predicts this ignition
        for bt in buildup_times:
            if 1 <= (gt - bt) <= k:
                n_ignitions_predicted += 1
                break

    recall = n_ignitions_predicted / (n_gwd + 1e-9)
    f1 = 2 * precision * recall / (precision + recall + 1e-9)

    # Threshold gate efficiency: fraction of GWD ignitions with a preceding buildup
    threshold_gate_eff = recall  # same as recall by definition

    # Sub-threshold ratio: buildup events that do NOT trigger ignition
    # Models GNW's all-or-nothing gate — high buildup that fails to cross threshold
    n_sub_threshold = n_buildup - n_coupled
    sub_threshold_ratio = n_sub_threshold / (n_buildup + 1e-9)

    return (
        float(f1),
        float(precision),
        float(recall),
        int(n_coupled),
        float(threshold_gate_eff),
        float(sub_threshold_ratio),
        int(n_gwd),
        int(n_buildup),
    )


def analyse(agent: str = "albedo", k: int = _K) -> GNWCoupledResult:
    """
    Cross-validate ignition precursor buildup against GWD ignition timestamps.

    Args:
        agent: which agent's ConsciousnessHistoryStore to load
        k:     lookahead window — buildup at t predicts ignition within k steps

    Returns:
        GNWCoupledResult with coupled_f1, coupling_class, and GNW gate metrics.
        Returns default BLIND result if phi data is insufficient (< 60 entries).
    """
    try:
        from algorithms import ConsciousnessHistoryStore as chs
        entries = chs.load(agent, max_entries=2880)
    except Exception:
        entries = []

    entries_asc = list(reversed(entries)) if entries else []
    if len(entries_asc) < _MIN_ENTRIES:
        return _default(len(entries_asc))

    phi = np.array(
        [float(e.get("mean_phi_level", e.get("phi", 0.5))) for e in entries_asc],
        dtype=float,
    )
    n = len(phi)

    (f1, prec, rec, n_coupled, gate_eff, sub_thresh_ratio,
     n_gwd, n_buildup) = _compute_coupled_metrics(phi, k=k)

    # Null distribution: shuffle phi, recompute coupled_f1
    rng = np.random.default_rng(42)
    null_f1s = []
    for _ in range(_N_SHUFFLES):
        phi_shuf = rng.permutation(phi)
        nf1, *_ = _compute_coupled_metrics(phi_shuf, k=k)
        null_f1s.append(nf1)
    p95_null = float(np.percentile(null_f1s, 95))
    beats_null = f1 > p95_null

    return GNWCoupledResult(
        coupled_f1=round(f1, 6),
        coupling_class=_classify(f1),
        n_coupled_pairs=n_coupled,
        threshold_gate_efficiency=round(gate_eff, 6),
        sub_threshold_ratio=round(sub_thresh_ratio, 6),
        beats_null=beats_null,
        n_gwd_ignitions=n_gwd,
        n_buildup_events=n_buildup,
        n_entries=n,
    )


if __name__ == "__main__":
    r = analyse("albedo")
    print(f"GNWCoupledIgnition:")
    print(f"  coupling_class:            {r.coupling_class}")
    print(f"  coupled_f1:                {r.coupled_f1:.4f}")
    print(f"  n_coupled_pairs:           {r.n_coupled_pairs}")
    print(f"  n_gwd_ignitions:           {r.n_gwd_ignitions}")
    print(f"  n_buildup_events:          {r.n_buildup_events}")
    print(f"  threshold_gate_efficiency: {r.threshold_gate_efficiency:.4f}")
    print(f"  sub_threshold_ratio:       {r.sub_threshold_ratio:.4f}")
    print(f"  beats_null:                {r.beats_null}")
    print(f"  n_entries:                 {r.n_entries}")
