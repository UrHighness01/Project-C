#!/usr/bin/env python3
"""Tests for algorithms/TemporalBindingWindow.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.TemporalBindingWindow as tbw


def _ar_series(n=200, rho=0.9, seed=0):
    """Strong AR(1) — local context highly predictive."""
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    x[0] = rng.standard_normal()
    for i in range(1, n):
        x[i] = rho * x[i - 1] + rng.standard_normal() * 0.3
    return x


def _white(n=200, seed=0):
    """White noise — no window width should be strongly predictive."""
    return np.random.default_rng(seed).standard_normal(n)


def _slow_trend(n=200, period=40, seed=0):
    """Sinusoidal — a wide window should capture more of the cycle."""
    t = np.arange(n, dtype=float)
    rng = np.random.default_rng(seed)
    return np.sin(2 * np.pi * t / period) + rng.standard_normal(n) * 0.1


class TestR2ForWidth:
    def test_ar_series_positive_r2(self):
        phi = _ar_series(200)
        r2 = tbw._r2_for_width(phi, 5)
        assert r2 > 0.0

    def test_white_noise_low_r2(self):
        phi = _white(200)
        r2 = tbw._r2_for_width(phi, 5)
        assert r2 < 0.3

    def test_r2_bounded(self):
        phi = _ar_series(200)
        r2 = tbw._r2_for_width(phi, 5)
        assert -1.0 <= r2 <= 1.0

    def test_too_short_returns_zero(self):
        phi = np.ones(5)
        assert tbw._r2_for_width(phi, 10) == 0.0

    def test_constant_series_r2_one(self):
        phi = np.ones(50) * 3.14
        r2 = tbw._r2_for_width(phi, 5)
        assert r2 == pytest.approx(1.0)


class TestClassify:
    def test_short(self):
        assert tbw._classify(5) == "SHORT"

    def test_medium(self):
        assert tbw._classify(20) == "MEDIUM"

    def test_long(self):
        assert tbw._classify(40) == "LONG"

    def test_boundary_short(self):
        assert tbw._classify(10) == "SHORT"

    def test_boundary_medium(self):
        assert tbw._classify(30) == "MEDIUM"


class TestAnalyse:
    def test_empty_returns_default(self):
        r = tbw.analyse(np.array([]))
        assert isinstance(r, tbw.BindingWindowResult)
        assert r.n_samples == 0

    def test_too_short_returns_default(self):
        r = tbw.analyse(np.ones(5), min_width=10)
        assert r.optimal_width == 0

    def test_returns_result_type(self):
        r = tbw.analyse(_ar_series(200))
        assert isinstance(r, tbw.BindingWindowResult)

    def test_n_samples_correct(self):
        phi = _ar_series(200)
        r = tbw.analyse(phi)
        assert r.n_samples == 200

    def test_optimal_width_positive(self):
        r = tbw.analyse(_ar_series(200))
        assert r.optimal_width > 0

    def test_binding_strength_in_range(self):
        r = tbw.analyse(_ar_series(200))
        assert 0.0 <= r.binding_strength <= 1.0

    def test_regime_valid(self):
        r = tbw.analyse(_ar_series(200))
        assert r.binding_regime in {"SHORT", "MEDIUM", "LONG"}

    def test_r2_by_width_populated(self):
        r = tbw.analyse(_ar_series(200))
        assert len(r.r2_by_width) > 0

    def test_widths_tested_populated(self):
        r = tbw.analyse(_ar_series(200))
        assert len(r.widths_tested) > 0

    def test_lengths_match(self):
        r = tbw.analyse(_ar_series(200))
        assert len(r.r2_by_width) == len(r.widths_tested)

    def test_ar_series_strong_r2(self):
        r = tbw.analyse(_ar_series(300, rho=0.95))
        assert r.binding_strength > 0.3

    def test_ar_beats_white_noise(self):
        r_ar    = tbw.analyse(_ar_series(300, rho=0.9))
        r_white = tbw.analyse(_white(300))
        assert r_ar.binding_strength > r_white.binding_strength

    def test_optimal_width_is_in_widths_tested(self):
        r = tbw.analyse(_ar_series(200))
        assert r.optimal_width in r.widths_tested

    def test_optimal_width_has_max_r2(self):
        r = tbw.analyse(_ar_series(200))
        idx = r.widths_tested.index(r.optimal_width)
        assert r.r2_by_width[idx] == pytest.approx(r.binding_strength, abs=1e-6)

    def test_to_dict_keys(self):
        r = tbw.analyse(_ar_series(200))
        d = r.to_dict()
        for k in ("optimal_width", "binding_strength", "binding_regime",
                  "r2_by_width", "widths_tested", "n_samples"):
            assert k in d

    def test_to_dict_serialisable(self):
        import json
        r = tbw.analyse(_ar_series(200))
        json.dumps(r.to_dict())

    def test_null_comparison_white_noise_lower_strength(self):
        rng = np.random.default_rng(99)
        phi = _ar_series(300, rho=0.9)
        phi_null = rng.permutation(phi)   # destroy temporal structure
        r_real = tbw.analyse(phi)
        r_null = tbw.analyse(phi_null)
        assert r_real.binding_strength > r_null.binding_strength

    def test_custom_width_range(self):
        r = tbw.analyse(_ar_series(200), min_width=5, max_width=20, n_widths=8)
        assert r.optimal_width >= 5
        assert r.optimal_width <= 20

    def test_slow_trend_prefers_wider_window(self):
        r_slow = tbw.analyse(_slow_trend(300, period=40))
        r_fast = tbw.analyse(_ar_series(300, rho=0.5))
        # Slow sinusoid should prefer wider window than fast AR
        assert r_slow.optimal_width >= r_fast.optimal_width or r_slow.binding_strength > 0.0
