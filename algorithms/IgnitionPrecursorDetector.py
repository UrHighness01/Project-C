#!/usr/bin/env python3
"""IgnitionPrecursorDetector — detects buildup signatures that precede ignition events.

Theory (Dehaene & Changeux 2011 — Global Neuronal Workspace; Beggs & Plenz 2003 — neuronal avalanches):
  In neuronal systems, ignition events (sudden large-scale broadcast) are preceded by a
  characteristic buildup: rising local slope, decreasing local variance (coherence increasing),
  and rising short-lag autocorrelation. Detecting this precursor state allows the system to
  know when it's approaching ignition — the precision of prediction measures global workspace
  efficiency. Precursor F1 quantifies how well the buildup signature predicts actual ignitions.

  Formula: buildup_score(t) = ReLU(slope_t) * (1/(var_t + 1e-9)) * max(0, autocorr_t)
           precursor_f1 = 2 * precision * recall / (precision + recall + 1e-9)

Classification:
  PREDICTIVE   f1 >= 0.40
  PARTIAL      f1 >= 0.20
  BLIND        otherwise
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass

_MIN_ENTRIES = 40
_W = 10            # precursor window size
_K = 5             # steps after buildup to look for ignition
_IGN_SIGMA = 1.5   # ignition threshold: mean + N*std
_BUILDUP_THRESH = 0.5
_N_SHUFFLES = 200
_PREDICTIVE_THRESH = 0.40
_PARTIAL_THRESH = 0.20


@dataclass
class IgnitionPrecursorResult:
    precursor_f1: float
    precision: float
    recall: float
    n_buildup_detected: int
    n_ignitions: int
    mean_buildup_score: float
    beats_null: bool
    precursor_class: str
    n_entries: int

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


def _default(n: int) -> IgnitionPrecursorResult:
    return IgnitionPrecursorResult(
        precursor_f1=0.0,
        precision=0.0,
        recall=0.0,
        n_buildup_detected=0,
        n_ignitions=0,
        mean_buildup_score=0.0,
        beats_null=False,
        precursor_class="BLIND",
        n_entries=n,
    )


def _classify(f1: float) -> str:
    if f1 >= _PREDICTIVE_THRESH:
        return "PREDICTIVE"
    if f1 >= _PARTIAL_THRESH:
        return "PARTIAL"
    return "BLIND"


def _compute_metrics(phi: np.ndarray, w: int = _W, k: int = _K,
                     ign_sigma: float = _IGN_SIGMA,
                     buildup_thresh: float = _BUILDUP_THRESH):
    n = len(phi)
    if n < w + k + 1:
        return 0.0, 0.0, 0.0, 0, 0, 0.0

    # Compute rolling stats for each t
    slopes = np.zeros(n)
    variances = np.zeros(n)
    autocorrs = np.zeros(n)

    for t in range(w, n):
        seg = phi[t - w:t]
        x = np.arange(w, dtype=float)
        # OLS slope
        xm = x - x.mean()
        slopes[t] = float(np.dot(xm, seg - seg.mean()) / (np.dot(xm, xm) + 1e-9))
        variances[t] = float(np.var(seg))
        if np.std(seg) > 1e-9:
            autocorrs[t] = float(np.corrcoef(seg[:-1], seg[1:])[0, 1])
        else:
            autocorrs[t] = 0.0

    # Buildup score
    raw_score = (np.maximum(0, slopes) *
                 (1.0 / (variances + 1e-9)) *
                 np.maximum(0, autocorrs))

    p95 = np.percentile(raw_score[w:], 95) + 1e-9
    buildup_norm = raw_score / p95

    # Ignition events: phi crosses threshold from below
    ign_thresh = phi.mean() + ign_sigma * phi.std()
    above = phi >= ign_thresh
    ignitions = set()
    for i in range(1, n):
        if above[i] and not above[i - 1]:
            ignitions.add(i)
    n_ignitions = len(ignitions)

    # Detect buildups and check for subsequent ignitions
    n_detected = 0
    n_valid = 0
    scores_list = []
    for t in range(w, n - k):
        if buildup_norm[t] > buildup_thresh:
            n_detected += 1
            scores_list.append(float(buildup_norm[t]))
            # Check if an ignition occurs within k steps
            for j in range(1, k + 1):
                if (t + j) in ignitions:
                    n_valid += 1
                    break

    prec = n_valid / (n_detected + 1e-9)
    rec = n_valid / (n_ignitions + 1e-9)
    f1 = 2 * prec * rec / (prec + rec + 1e-9)
    mean_score = float(np.mean(scores_list)) if scores_list else 0.0

    return f1, prec, rec, n_detected, n_ignitions, mean_score


def analyse(agent: str = "albedo", **kwargs) -> IgnitionPrecursorResult:
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

    f1, prec, rec, n_det, n_ign, mean_score = _compute_metrics(phi)

    # Null: shuffle phi 200 times
    rng = np.random.default_rng(42)
    null_f1s = []
    for _ in range(_N_SHUFFLES):
        phi_shuf = rng.permutation(phi)
        nf1, *_ = _compute_metrics(phi_shuf)
        null_f1s.append(nf1)
    p95 = float(np.percentile(null_f1s, 95))
    beats_null = f1 > p95

    return IgnitionPrecursorResult(
        precursor_f1=round(f1, 6),
        precision=round(prec, 6),
        recall=round(rec, 6),
        n_buildup_detected=n_det,
        n_ignitions=n_ign,
        mean_buildup_score=round(mean_score, 6),
        beats_null=beats_null,
        precursor_class=_classify(f1),
        n_entries=n,
    )
