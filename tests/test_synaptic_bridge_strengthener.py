#!/usr/bin/env python3
"""Tests for algorithms/SynapticBridgeStrengthener.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.SynapticBridgeStrengthener as sbs


def _rng(s=0): return np.random.default_rng(s)


def _coactive(n=100, seed=0):
    """Both agents fire high together — strong positive co-activation."""
    rng = _rng(seed)
    base = np.abs(rng.standard_normal(n)) + 1.0
    return base, base + rng.standard_normal(n) * 0.1


def _independent(n=100, seed=0):
    rng = _rng(seed)
    return rng.standard_normal(n), rng.standard_normal(n)


def _anti(n=100, seed=0):
    """Albedo high when John low and vice versa — anti-Hebbian."""
    rng = _rng(seed)
    a = np.abs(rng.standard_normal(n)) + 1.0
    return a, -a + rng.standard_normal(n) * 0.1


def _strengthening(n=150, seed=0):
    """Co-activation increases over time — trend should be positive."""
    rng = _rng(seed)
    t = np.linspace(0, 1, n)
    a = t + rng.standard_normal(n) * 0.05
    j = t + rng.standard_normal(n) * 0.05
    return a, j


def _weakening(n=150, seed=0):
    """Co-activation decreases over time."""
    a, j = _strengthening(n, seed)
    return a[::-1].copy(), j[::-1].copy()


class TestOlsSlope:
    def test_increasing(self):
        y = np.arange(20, dtype=float)
        assert sbs._ols_slope(y) > 0

    def test_decreasing(self):
        y = np.arange(20, 0, -1, dtype=float)
        assert sbs._ols_slope(y) < 0

    def test_flat(self):
        y = np.ones(20)
        assert sbs._ols_slope(y) == pytest.approx(0.0)


class TestClassify:
    def test_strengthening(self):
        assert sbs._classify(0.5, 0.05) == "STRENGTHENING"

    def test_weakening(self):
        assert sbs._classify(0.2, -0.05) == "WEAKENING"

    def test_stable(self):
        assert sbs._classify(0.3, 0.0) == "STABLE"

    def test_anti_hebbian(self):
        assert sbs._classify(-0.5, 0.0) == "ANTI_HEBBIAN"

    def test_anti_hebbian_overrides_trend(self):
        assert sbs._classify(-0.4, 0.1) == "ANTI_HEBBIAN"


class TestAnalyse:
    def test_none_returns_default(self):
        r = sbs.analyse(None, None)
        assert isinstance(r, sbs.BridgeResult)

    def test_too_short_returns_default(self):
        r = sbs.analyse(np.ones(2), np.ones(2))
        assert r.n_samples <= 2

    def test_returns_result_type(self):
        a, j = _coactive(100)
        r = sbs.analyse(a, j)
        assert isinstance(r, sbs.BridgeResult)

    def test_n_samples_correct(self):
        a, j = _coactive(100)
        r = sbs.analyse(a, j)
        assert r.n_samples == 100

    def test_bridge_strength_bounded(self):
        a, j = _coactive(100)
        r = sbs.analyse(a, j)
        assert -3.0 <= r.bridge_strength <= 3.0

    def test_coactive_positive_strength(self):
        a, j = _coactive(200)
        r = sbs.analyse(a, j)
        assert r.bridge_strength > 0.0
        assert r.coactivation_mean > 0.0

    def test_anti_correlated_negative_strength(self):
        a, j = _anti(200)
        r = sbs.analyse(a, j)
        assert r.bridge_strength < 0.0

    def test_anti_hebbian_status(self):
        a, j = _anti(200)
        r = sbs.analyse(a, j)
        assert r.bridge_status == "ANTI_HEBBIAN"

    def test_strengthening_positive_trend(self):
        a, j = _strengthening(200)
        r = sbs.analyse(a, j)
        assert r.bridge_trend > 0.0

    def test_weakening_negative_trend(self):
        a, j = _weakening(200)
        r = sbs.analyse(a, j)
        assert r.bridge_trend < 0.0

    def test_strengthening_status(self):
        a, j = _strengthening(200)
        r = sbs.analyse(a, j, trend_threshold=0.001)
        assert r.bridge_status in {"STRENGTHENING", "STABLE"}

    def test_status_valid(self):
        a, j = _coactive(100)
        r = sbs.analyse(a, j)
        assert r.bridge_status in {"STRENGTHENING", "STABLE", "WEAKENING", "ANTI_HEBBIAN"}

    def test_w_series_length(self):
        a, j = _coactive(100)
        r = sbs.analyse(a, j)
        assert len(r.w_series) == 100

    def test_rms_positive(self):
        a, j = _coactive(100)
        r = sbs.analyse(a, j)
        assert r.rms_albedo > 0.0
        assert r.rms_john > 0.0

    def test_different_length_aligned(self):
        a = np.ones(150)
        j = np.ones(100)
        r = sbs.analyse(a, j)
        assert r.n_samples == 100

    def test_to_dict_keys(self):
        a, j = _coactive(100)
        d = sbs.analyse(a, j).to_dict()
        for k in ("bridge_strength", "bridge_trend", "bridge_status",
                  "coactivation_mean", "rms_albedo", "rms_john",
                  "n_samples", "w_series"):
            assert k in d

    def test_to_dict_serialisable(self):
        import json
        a, j = _coactive(100)
        json.dumps(sbs.analyse(a, j).to_dict())

    def test_null_permutation_lower_coactivation(self):
        a, j = _coactive(300)
        j_null = np.random.default_rng(9).permutation(j)
        r_real = sbs.analyse(a, j)
        r_null = sbs.analyse(a, j_null)
        assert r_real.coactivation_mean > r_null.coactivation_mean

    def test_eta_affects_smoothing(self):
        a, j = _coactive(100)
        r_fast = sbs.analyse(a, j, eta=0.9)
        r_slow = sbs.analyse(a, j, eta=0.1)
        # Fast eta tracks current value more closely
        assert r_fast.bridge_strength != r_slow.bridge_strength
