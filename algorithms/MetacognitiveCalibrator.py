#!/usr/bin/env python3
"""
MetacognitiveCalibrator — measures how well the agent knows what it doesn't know.

Theory
------
Calibration (Lichtenstein & Fischhoff 1977) describes the alignment between
confidence and accuracy. A perfectly calibrated agent that reports confidence C
should be correct C fraction of the time. We operationalise this in the
consciousness system using:

  Confidence proxy : self-reported metacognitive_confidence from snapshots
  Accuracy proxy   : AR(4) phi prediction accuracy (1 - normalised RMSE)
                     drawn from the SurprisalMonitor residual series

  For each snapshot pair (confidence_t, accuracy_t), we compute:
    calibration_error_t = |confidence_t - accuracy_t|

  Aggregate measures
  ------------------
  Mean calibration error (MCE):
    MCE = mean_t |conf_t - acc_t|   ∈ [0, 1]
    Lower is better. MCE < 0.1 = well-calibrated.

  Overconfidence bias:
    OC = mean_t (conf_t - acc_t)    (signed)
    OC > 0 = agent overestimates its own accuracy
    OC < 0 = agent underestimates (conservative / humble)

  Expected Calibration Error (ECE) — binned version:
    Partition confidence values into B=10 equal bins.
    For each bin b: ECE_b = |mean_confidence_b - mean_accuracy_b| * n_b / N
    ECE = sum_b ECE_b
    ECE ∈ [0, 1], lower is better.

  Calibration class:
    EXCELLENT  : MCE < 0.05
    GOOD       : MCE < 0.10
    MODERATE   : MCE < 0.20
    POOR       : MCE >= 0.20

  Normalised RMSE → accuracy proxy
  ---------------------------------
  We convert SurprisalMonitor's surprisal series to an accuracy series:
    surprisal_norm = surprisal / (surprisal.max() + epsilon)
    accuracy = 1 - surprisal_norm   ∈ [0, 1]
  This ensures accuracy is high when phi prediction error is low.

Output
------
CalibrationResult:
  mce                : float   -- Mean Calibration Error
  overconfidence_bias: float   -- signed bias (+ = overconfident)
  ece                : float   -- Expected Calibration Error
  calibration_class  : str     -- EXCELLENT | GOOD | MODERATE | POOR
  is_overconfident   : bool    -- overconfidence_bias > 0.05
  is_humble          : bool    -- overconfidence_bias < -0.05
  n_pairs            : int
  mean_confidence    : float
  mean_accuracy      : float
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np


# ── Helpers ───────────────────────────────────────────────────────────────────

def _accuracy_from_surprisal(surprisal: np.ndarray) -> np.ndarray:
    """Convert squared-error surprisal series to [0,1] accuracy."""
    s_max = float(surprisal.max())
    if s_max == 0:
        return np.ones(len(surprisal))
    return 1.0 - surprisal / s_max


def _ece(confidences: np.ndarray, accuracies: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error via equal-width binning."""
    n = len(confidences)
    if n == 0:
        return 0.0
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (confidences >= lo) & (confidences < hi)
        if i == n_bins - 1:
            mask = (confidences >= lo) & (confidences <= hi)
        if mask.sum() == 0:
            continue
        mean_conf = float(confidences[mask].mean())
        mean_acc = float(accuracies[mask].mean())
        ece += abs(mean_conf - mean_acc) * mask.sum() / n
    return float(ece)


def _classify(mce: float) -> str:
    if mce < 0.05:
        return "EXCELLENT"
    if mce < 0.10:
        return "GOOD"
    if mce < 0.20:
        return "MODERATE"
    return "POOR"


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class CalibrationResult:
    mce: float = 0.0
    overconfidence_bias: float = 0.0
    ece: float = 0.0
    calibration_class: str = "MODERATE"
    is_overconfident: bool = False
    is_humble: bool = False
    n_pairs: int = 0
    mean_confidence: float = 0.0
    mean_accuracy: float = 0.0

    def to_dict(self) -> dict:
        return {
            "mce": round(self.mce, 4),
            "overconfidence_bias": round(self.overconfidence_bias, 4),
            "ece": round(self.ece, 4),
            "calibration_class": self.calibration_class,
            "is_overconfident": self.is_overconfident,
            "is_humble": self.is_humble,
            "n_pairs": self.n_pairs,
            "mean_confidence": round(self.mean_confidence, 4),
            "mean_accuracy": round(self.mean_accuracy, 4),
        }


# ── Core analysis ─────────────────────────────────────────────────────────────

def analyse(
    confidences: Optional[List[float]] = None,
    surprisal_series: Optional[np.ndarray] = None,
    *,
    overconfidence_threshold: float = 0.05,

    agent: str = "albedo",
) -> CalibrationResult:
    """
    Measure calibration between self-reported confidence and phi prediction accuracy.

    Args:
        confidences      : list of metacognitive_confidence values from snapshots,
                           each in [0, 1]. Chronological order.
        surprisal_series : squared phi prediction errors from SurprisalMonitor,
                           aligned in time with confidences.
        overconfidence_threshold : bias magnitude above which we flag over/underconfidence.
    """
    if confidences is None or surprisal_series is None:
        try:
            from algorithms.ConsciousnessHistoryStore import ConsciousnessHistoryStore
            from algorithms.SurprisalMonitor import analyse as sm_analyse
            from runtime.state import get_agent, phi_series
            agent = get_agent()
            store = ConsciousnessHistoryStore(agent)
            snaps = list(reversed(store.load()))  # chronological
            confidences = []
            for s in snaps:
                c = s.get("summary", s).get("metacognitive_confidence")
                if c is not None:
                    try:
                        confidences.append(float(c))
                    except (TypeError, ValueError):
                        pass
            phi = phi_series()
            if phi is not None and len(phi) > 5:
                import algorithms.SurprisalMonitor as sm
                weights = sm._fit_ar(np.asarray(phi, dtype=float), p=4)
                preds = sm._predict_ar(np.asarray(phi, dtype=float), weights)
                residuals = np.asarray(phi, dtype=float)[4:] - preds
                surprisal_series = residuals ** 2
            else:
                surprisal_series = np.array([])
        except Exception:
            return CalibrationResult()

    confs = np.asarray(confidences, dtype=float)
    surp = np.asarray(surprisal_series, dtype=float)

    if confs.size == 0 or surp.size == 0:
        return CalibrationResult()

    # Align lengths
    n = min(len(confs), len(surp))
    if n < 2:
        return CalibrationResult()

    confs = np.clip(confs[-n:], 0.0, 1.0)
    accs = _accuracy_from_surprisal(surp[-n:])

    errors = np.abs(confs - accs)
    mce = float(errors.mean())
    bias = float((confs - accs).mean())
    ece = _ece(confs, accs)

    return CalibrationResult(
        mce=mce,
        overconfidence_bias=bias,
        ece=ece,
        calibration_class=_classify(mce),
        is_overconfident=bias > overconfidence_threshold,
        is_humble=bias < -overconfidence_threshold,
        n_pairs=n,
        mean_confidence=float(confs.mean()),
        mean_accuracy=float(accs.mean()),
    )
