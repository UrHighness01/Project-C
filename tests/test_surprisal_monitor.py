#!/usr/bin/env python3
"""Tests for algorithms/SurprisalMonitor.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.SurprisalMonitor as sm


RNG = np.random.default_rng(42)


def _stable(n=200):
    return np.ones(n) * 2.5 + RNG.normal(0, 0.01, n)


def _ar1(n=200, a=0.8):
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = a * x[i - 1] + RNG.normal(0, 0.1)
    return x + 2.0


def _spike(n=200, at=None):
    x = _ar1(n)
    pos = n - 1 if at is None else at
    x[pos] = x.mean() + 20 * x.std()
    return x


class TestFitAr:
    def test_returns_weight_vector_of_length_p(self):
        phi = _ar1(100)
        w = sm._fit_ar(phi, p=4)
        assert len(w) == 4

    def test_too_short_returns_zeros(self):
        phi = np.array([1.0, 2.0, 3.0])
        w = sm._fit_ar(phi, p=4)
        assert (w == 0).all()

    def test_ar1_recovers_coefficient(self):
        rng = np.random.default_rng(0)
        x = np.zeros(500)
        for i in range(1, 500):
            x[i] = 0.9 * x[i - 1] + rng.normal(0, 0.01)
        w = sm._fit_ar(x, p=1, lam=1e-6)
        assert abs(w[0] - 0.9) < 0.05


class TestPredictAr:
    def test_output_length(self):
        phi = _ar1(100)
        w = sm._fit_ar(phi, p=4)
        preds = sm._predict_ar(phi, w)
        assert len(preds) == len(phi) - 4

    def test_too_short_returns_mean_fill(self):
        phi = np.array([1.0, 2.0])
        w = np.array([0.5, 0.5, 0.0, 0.0])
        preds = sm._predict_ar(phi, w)
        assert len(preds) == len(phi)


class TestEmpricalDist:
    def test_sums_to_one(self):
        vals = RNG.normal(0, 1, 100)
        d = sm._empirical_dist(vals, bins=16, range_=(-4, 4))
        assert d.sum() == pytest.approx(1.0, abs=1e-3)

    def test_no_zero_bins(self):
        vals = np.array([1.0])
        d = sm._empirical_dist(vals, bins=8, range_=(0, 2))
        assert (d > 0).all()


class TestKl:
    def test_identical_distributions_zero(self):
        p = np.array([0.25, 0.25, 0.25, 0.25])
        assert sm._kl(p, p) == pytest.approx(0.0, abs=1e-9)

    def test_divergent_positive(self):
        p = np.array([0.9, 0.1])
        q = np.array([0.5, 0.5])
        assert sm._kl(p, q) > 0


class TestAnalyse:
    def test_empty_returns_default(self):
        result = sm.analyse(np.array([]))
        assert result.current_surprisal == 0.0

    def test_too_short_returns_default(self):
        result = sm.analyse(np.ones(3))
        assert result.n_observations == 0

    def test_returns_surprisal_result(self):
        phi = _ar1(100)
        result = sm.analyse(phi)
        assert isinstance(result, sm.SurprisalResult)

    def test_n_observations_correct(self):
        phi = _ar1(150)
        result = sm.analyse(phi)
        assert result.n_observations == 150

    def test_stable_series_routine_level(self):
        phi = _stable(300)
        result = sm.analyse(phi)
        assert result.surprisal_level in {"ROUTINE", "ELEVATED"}

    def test_spike_raises_level(self):
        phi = _spike(200)
        result = sm.analyse(phi)
        assert result.surprisal_level in {"ELEVATED", "HIGH", "ANOMALOUS"}

    def test_is_novel_false_for_stable(self):
        phi = _stable(300)
        result = sm.analyse(phi)
        assert not result.is_novel

    def test_current_surprisal_nonneg(self):
        phi = _ar1(100)
        result = sm.analyse(phi)
        assert result.current_surprisal >= 0

    def test_peak_gte_current(self):
        phi = _ar1(100)
        result = sm.analyse(phi)
        assert result.peak_surprisal >= result.current_surprisal - 1e-9

    def test_peak_gte_mean(self):
        phi = _ar1(100)
        result = sm.analyse(phi)
        assert result.peak_surprisal >= result.mean_surprisal - 1e-9

    def test_kl_divergence_nonneg(self):
        phi = _ar1(100)
        result = sm.analyse(phi)
        assert result.kl_divergence >= 0

    def test_ar_weights_length(self):
        phi = _ar1(100)
        result = sm.analyse(phi, p=4)
        assert len(result.ar_weights) == 4

    def test_surprisal_trend_float(self):
        phi = _ar1(100)
        result = sm.analyse(phi)
        assert isinstance(result.surprisal_trend, float)

    def test_valid_level_values(self):
        phi = _ar1(100)
        result = sm.analyse(phi)
        assert result.surprisal_level in {"ROUTINE", "ELEVATED", "HIGH", "ANOMALOUS"}

    def test_constant_phi_low_surprisal(self):
        phi = np.ones(200) * 3.0
        result = sm.analyse(phi)
        assert result.mean_surprisal < 0.01

    def test_to_dict_serialisable(self):
        import json
        phi = _ar1(100)
        json.dumps(sm.analyse(phi).to_dict())

    def test_to_dict_keys(self):
        phi = _ar1(100)
        d = sm.analyse(phi).to_dict()
        for k in ("current_surprisal", "mean_surprisal", "surprisal_level",
                  "kl_divergence", "is_novel", "peak_surprisal",
                  "surprisal_trend", "ar_weights", "n_observations"):
            assert k in d

    def test_window_larger_than_phi(self):
        phi = _ar1(30)
        result = sm.analyse(phi, window=1000)
        assert isinstance(result, sm.SurprisalResult)

    def test_p_2_works(self):
        phi = _ar1(100)
        result = sm.analyse(phi, p=2)
        assert len(result.ar_weights) == 2
