"""
PredictiveSurprise — AR(p) prediction error on phi trajectory.

CALM (<1σ) | SURPRISED (1-2.5σ) | SHOCKED (>2.5σ)
Meta-surprise detects change in surprise rate over time.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import math


@dataclass
class PredictiveSurpriseResult:
    current_surprise: float = 0.0
    surprise_class: str = "UNKNOWN"
    meta_surprise: float = 0.0
    meta_surprise_flag: bool = False
    surprise_rate: float = 0.0
    phi_predicted: float = 0.0
    phi_actual: float = 0.0
    ar_coefficients: list = field(default_factory=list)
    beats_null: bool = False
    n_observations: int = 0

    def to_dict(self) -> dict:
        return {
            "current_surprise": round(self.current_surprise, 4),
            "surprise_class": self.surprise_class,
            "meta_surprise": round(self.meta_surprise, 4),
            "meta_surprise_flag": self.meta_surprise_flag,
            "surprise_rate": round(self.surprise_rate, 4),
            "phi_predicted": round(self.phi_predicted, 4),
            "phi_actual": round(self.phi_actual, 4),
            "beats_null": self.beats_null,
            "n_observations": self.n_observations,
        }


class PredictiveSurpriseTracker:
    def __init__(self, order: int = 3, window: int = 50, meta_window: int = 20):
        self.order = order
        self.window = window
        self.meta_window = meta_window
        self._history: list = []
        self._surprise_history: list = []

    def _fit_ar(self, values: list) -> tuple:
        n = len(values)
        p = min(self.order, n - 1)
        if p < 1:
            return [], 0.0
        X = [[1.0] + [values[i - j - 1] for j in range(p)] for i in range(p, n)]
        y = values[p:]
        n_obs = len(y)
        k = p + 1
        if n_obs < k:
            return [], 0.0
        XtX = [[sum(X[i][a] * X[i][b] for i in range(n_obs)) for b in range(k)] for a in range(k)]
        Xty = [sum(X[i][a] * y[i] for i in range(n_obs)) for a in range(k)]
        aug = [XtX[i] + [Xty[i]] for i in range(k)]
        for col in range(k):
            if abs(aug[col][col]) < 1e-12:
                return [0.0] * k, 0.0
            for row in range(col + 1, k):
                factor = aug[row][col] / aug[col][col]
                for c in range(col, k + 1):
                    aug[row][c] -= factor * aug[col][c]
        betas = [0.0] * k
        for i in range(k - 1, -1, -1):
            betas[i] = aug[i][k] / aug[i][i]
            for j in range(i - 1, -1, -1):
                aug[j][k] -= aug[j][i] * betas[i]
        residuals = [y[i] - (betas[0] + sum(betas[j+1] * X[i][j+1] for j in range(p))) for i in range(n_obs)]
        if len(residuals) < 2:
            return betas, 0.0
        mean_r = sum(residuals) / len(residuals)
        std_r = math.sqrt(sum((r - mean_r) ** 2 for r in residuals) / len(residuals))
        return betas, std_r

    def update(self, phi: float) -> PredictiveSurpriseResult:
        self._history.append(phi)
        n = len(self._history)
        if n < self.order + 3:
            return PredictiveSurpriseResult(surprise_class="CALM", n_observations=n)
        window_vals = self._history[-self.window:]
        betas, std_res = self._fit_ar(window_vals)
        if not betas or std_res == 0.0:
            return PredictiveSurpriseResult(surprise_class="CALM", n_observations=n)
        if len(set(window_vals)) == 1:
            phi_pred = window_vals[-1]
            p = 0
            betas = [phi_pred]
            recent = []
        else:
            p = len(betas) - 1
            recent = window_vals[-p:] if p > 0 else []
            phi_pred = betas[0] + sum(betas[j+1] * recent[j] for j in range(p))
        error = abs(phi - phi_pred)
        surprise = error / std_res if std_res > 0 else 0.0
        if surprise < 1.0:
            cls = "CALM"
        elif surprise < 2.5:
            cls = "SURPRISED"
        else:
            cls = "SHOCKED"
        self._surprise_history.append(surprise)
        if len(self._surprise_history) > self.meta_window * 2:
            self._surprise_history = self._surprise_history[-(self.meta_window * 2):]
        recent_s = self._surprise_history[-self.meta_window:]
        rate = sum(1 for s in recent_s if s >= 1.0) / len(recent_s) if recent_s else 0.0
        if len(self._surprise_history) >= self.meta_window * 2:
            older = self._surprise_history[:self.meta_window]
            newer = self._surprise_history[-self.meta_window:]
            rate_older = sum(1 for s in older if s >= 1.0) / len(older)
            rate_newer = sum(1 for s in newer if s >= 1.0) / len(newer)
            all_rates = [sum(1 for s in self._surprise_history[i:i+self.meta_window] if s >= 1.0) / self.meta_window
                         for i in range(len(self._surprise_history) - self.meta_window + 1)]
            mean_rate = sum(all_rates) / len(all_rates)
            std_rate = math.sqrt(sum((r - mean_rate)**2 for r in all_rates) / len(all_rates)) if len(all_rates) > 1 else 0.5
            meta_surprise = (rate_newer - rate_older) / std_rate if std_rate > 0 else 0.0
        else:
            meta_surprise = 0.0
        null_surprise = 0.0
        if len(window_vals) >= 4 and recent:
            shuffled = window_vals[len(window_vals)//2:] + window_vals[:len(window_vals)//2]
            s_betas, s_std = self._fit_ar(shuffled)
            if s_betas and s_std > 0:
                s_pred = s_betas[0] + sum(s_betas[j+1] * recent[j] for j in range(min(p, len(s_betas)-1)))
                null_surprise = abs(phi - s_pred) / s_std
        return PredictiveSurpriseResult(
            current_surprise=round(surprise, 4), surprise_class=cls,
            meta_surprise=round(meta_surprise, 4), meta_surprise_flag=abs(meta_surprise) > 2.0,
            surprise_rate=round(rate, 4), phi_predicted=round(phi_pred, 4), phi_actual=round(phi, 4),
            ar_coefficients=[round(b, 4) for b in betas],
            beats_null=(null_surprise > 0 and surprise < null_surprise), n_observations=n,
        )


def analyse(agent: str = "albedo") -> PredictiveSurpriseResult:
    try:
        from algorithms import ConsciousnessHistoryStore as chs
        entries = list(reversed(chs.load(agent, max_entries=200)))
        phi_series = [float(e.get("mean_phi_level", e.get("phi", 0.5)))
                      for e in entries if "mean_phi_level" in e or "phi" in e]
    except Exception:
        phi_series = []
    if len(phi_series) < 6:
        return PredictiveSurpriseResult(surprise_class="CALM", n_observations=len(phi_series))
    tracker = PredictiveSurpriseTracker()
    result = PredictiveSurpriseResult(surprise_class="CALM")
    for phi in phi_series:
        result = tracker.update(phi)
    return result
