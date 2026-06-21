"""
TemporalIntegrator — time-aware phi metrics: slope, recency-weighted mean,
predictive deviation, acceleration, trajectory, regime.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import List


def linear_slope(values: List[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    den = sum((i - x_mean) ** 2 for i in range(n))
    return num / den if den != 0 else 0.0


def recency_weighted_mean(values: List[float], decay: float = 0.9) -> float:
    n = len(values)
    if n == 0:
        return 0.0
    weights = [decay ** (n - 1 - i) for i in range(n)]
    total = sum(weights)
    return sum(w * v for w, v in zip(weights, values)) / total


def predictive_deviation(values: List[float]) -> float:
    if len(values) < 3:
        return 0.0
    predicted = values[-2] + (values[-2] - values[-3])
    return values[-1] - predicted


def acceleration(values: List[float]) -> float:
    if len(values) < 4:
        return 0.0
    half = len(values) // 2
    return linear_slope(values[half:]) - linear_slope(values[:half])


@dataclass
class TemporalIntegratorResult:
    n_samples: int = 0
    current: float = 0.0
    mean: float = 0.0
    slope: float = 0.0
    recency_mean: float = 0.0
    predictive_deviation: float = 0.0
    acceleration: float = 0.0
    min_phi: float = 0.0
    max_phi: float = 0.0
    range_phi: float = 0.0
    trajectory: str = "flat"
    regime: str = "steady"

    def to_dict(self) -> dict:
        return {
            "n_samples": self.n_samples,
            "current": round(self.current, 6),
            "mean": round(self.mean, 6),
            "slope": round(self.slope, 6),
            "recency_mean": round(self.recency_mean, 6),
            "predictive_deviation": round(self.predictive_deviation, 6),
            "acceleration": round(self.acceleration, 6),
            "min": round(self.min_phi, 6),
            "max": round(self.max_phi, 6),
            "range": round(self.range_phi, 6),
            "trajectory": self.trajectory,
            "regime": self.regime,
        }


def analyse(agent: str = "albedo", window: int = 50) -> TemporalIntegratorResult:
    try:
        from algorithms import ConsciousnessHistoryStore as chs
        entries = list(reversed(chs.load(agent, max_entries=window * 2)))
        vals = [float(e.get("mean_phi_level", e.get("phi", 0.5)))
                for e in entries if "mean_phi_level" in e or "phi" in e]
        vals = vals[-window:]
    except Exception:
        vals = []
    if len(vals) < 2:
        return TemporalIntegratorResult(n_samples=len(vals))
    sl = linear_slope(vals)
    acc = acceleration(vals)
    return TemporalIntegratorResult(
        n_samples=len(vals),
        current=round(vals[-1], 6),
        mean=round(sum(vals) / len(vals), 6),
        slope=round(sl, 6),
        recency_mean=round(recency_weighted_mean(vals), 6),
        predictive_deviation=round(predictive_deviation(vals), 6),
        acceleration=round(acc, 6),
        min_phi=round(min(vals), 6),
        max_phi=round(max(vals), 6),
        range_phi=round(max(vals) - min(vals), 6),
        trajectory="ascending" if sl > 0.001 else ("descending" if sl < -0.001 else "flat"),
        regime="accelerating" if acc > 0.0001 else ("decelerating" if acc < -0.0001 else "steady"),
    )
