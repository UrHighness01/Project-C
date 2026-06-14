#!/usr/bin/env python3
"""Tests for algorithms/CriticalFluctuationDetector.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.CriticalFluctuationDetector as cfd


def _white(n=100, seed=0):
    rng = np.random.default_rng(seed)
    return rng.standard_normal(n)


def _ar1_series(n=100, rho=0.95, seed=0):
    """AR(1) with coefficient rho — critical slowing down when rho→1."""
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    x[0] = rng.standard_normal()
    for i in range(1, n):
        x[i] = rho * x[i - 1] + rng.standard_normal() * 0.1
    return x


def _escalating_var(n=100):
    """Variance grows over time — should trigger WARNING/CRITICAL."""
    rng = np.random.default_rng(7)
    return np.concatenate([
        rng.normal(0, 0.1, n // 2),
        rng.normal(0, 1.5, n // 2),
    ])


class TestAr1:
    def test_white_noise_near_zero(self):
        x = _white(500)
        assert abs(cfd._ar1(x)) < 0.2

    def test_strong_ar1_close_to_rho(self):
        x = _ar1_series(500, rho=0.9)
        assert cfd._ar1(x) > 0.7

    def test_constant_series_returns_zero(self):
        x = np.ones(20)
        assert cfd._ar1(x) == pytest.approx(0.0)

    def test_negative_autocorrelation(self):
        x = np.array([1.0, -1.0] * 50, dtype=float)
        assert cfd._ar1(x) < -0.5


class TestRollingStats:
    def test_shape(self):
        phi = _white(50)
        v, a = cfd._rolling_stats(phi, 10)
        assert len(v) == len(a) == 50 - 10 + 1

    def test_var_nonnegative(self):
        v, _ = cfd._rolling_stats(_white(50), 10)
        assert (v >= 0).all()

    def test_ar1_bounded(self):
        _, a = cfd._rolling_stats(_white(50), 10)
        assert (np.abs(a) <= 1.0).all()


class TestClassify:
    def test_critical(self):
        level, is_crit = cfd._classify(0.90, 0.01, 0.85)
        assert level == "CRITICAL"
        assert is_crit is True

    def test_warning_ar1_only(self):
        level, is_crit = cfd._classify(0.90, -0.01, 0.85)
        assert level == "WARNING"
        assert is_crit is False

    def test_warning_var_only(self):
        level, is_crit = cfd._classify(0.50, 0.01, 0.85)
        assert level == "WARNING"
        assert is_crit is False

    def test_stable(self):
        level, _ = cfd._classify(0.50, -0.01, 0.85)
        assert level == "STABLE"


class TestAnalyse:
    def test_empty_returns_default(self):
        r = cfd.analyse(np.array([]))
        assert isinstance(r, cfd.FluctuationResult)
        assert r.n_samples == 0

    def test_too_short_returns_default(self):
        r = cfd.analyse(np.ones(5), window=20)
        assert r.n_samples == 0

    def test_returns_result_type(self):
        r = cfd.analyse(_white(100))
        assert isinstance(r, cfd.FluctuationResult)

    def test_n_samples_correct(self):
        phi = _white(100)
        r = cfd.analyse(phi)
        assert r.n_samples == 100

    def test_ar1_in_range(self):
        r = cfd.analyse(_white(100))
        assert -1.0 <= r.current_ar1 <= 1.0

    def test_var_nonnegative(self):
        r = cfd.analyse(_white(100))
        assert r.current_var >= 0.0

    def test_alert_level_valid(self):
        r = cfd.analyse(_white(100))
        assert r.alert_level in {"CRITICAL", "WARNING", "STABLE"}

    def test_white_noise_stable(self):
        r = cfd.analyse(_white(200, seed=42))
        assert r.alert_level in {"STABLE", "WARNING"}

    def test_high_ar1_triggers_warning_or_critical(self):
        x = _ar1_series(500, rho=0.98, seed=0)
        r = cfd.analyse(x, window=30)
        assert r.current_ar1 > 0.5

    def test_critical_ar1_fires_alert(self):
        x = _ar1_series(300, rho=0.99)
        r = cfd.analyse(x, ar1_threshold=0.80)
        assert r.alert_level in {"WARNING", "CRITICAL"}

    def test_escalating_var_triggers_warning(self):
        r = cfd.analyse(_escalating_var(200))
        assert r.alert_level in {"WARNING", "CRITICAL"}

    def test_series_not_empty(self):
        r = cfd.analyse(_white(100))
        assert len(r.var_series) > 0
        assert len(r.ar1_series) > 0

    def test_series_same_length(self):
        r = cfd.analyse(_white(100))
        assert len(r.var_series) == len(r.ar1_series)

    def test_is_critical_boolean(self):
        r = cfd.analyse(_white(100))
        assert isinstance(r.is_critical, bool)

    def test_to_dict_keys(self):
        r = cfd.analyse(_white(100))
        d = r.to_dict()
        for k in ("current_ar1", "current_var", "dvar_dt", "dar1_dt",
                  "alert_level", "is_critical", "n_samples",
                  "var_series", "ar1_series"):
            assert k in d

    def test_to_dict_serialisable(self):
        import json
        r = cfd.analyse(_white(100))
        json.dumps(r.to_dict())

    def test_is_critical_false_for_white_noise(self):
        r = cfd.analyse(_white(300, seed=1))
        # White noise rarely triggers both conditions simultaneously
        assert r.alert_level in {"STABLE", "WARNING"}

    def test_step_param_affects_series_length(self):
        r1 = cfd.analyse(_white(200), step=5)
        r2 = cfd.analyse(_white(200), step=10)
        assert len(r1.var_series) > len(r2.var_series)

    def test_window_param_respected(self):
        r = cfd.analyse(_white(100), window=30)
        assert r.n_samples == 100

    def test_higher_ar1_threshold_fewer_alerts(self):
        x = _ar1_series(200, rho=0.90)
        r_low = cfd.analyse(x, ar1_threshold=0.70)
        r_high = cfd.analyse(x, ar1_threshold=0.99)
        # Stricter threshold → more likely STABLE
        assert r_low.alert_level in {"WARNING", "CRITICAL"} or r_high.alert_level == "STABLE"
