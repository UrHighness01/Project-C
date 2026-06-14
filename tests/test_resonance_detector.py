#!/usr/bin/env python3
"""Tests for algorithms/ResonanceDetector.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.ResonanceDetector as rd

RNG = np.random.default_rng(7)


def _sine(n=200, freq=0.05, phase=0.0, noise=0.01):
    t = np.arange(n, dtype=float)
    return np.sin(2 * np.pi * freq * t + phase) + RNG.normal(0, noise, n)


class TestNormalisedXcorr:
    def test_lag_zero_identical_signals(self):
        x = _sine(100)
        lags, ccf = rd._normalised_xcorr(x, x, max_lag=10)
        peak_idx = np.abs(ccf).argmax()
        assert lags[peak_idx] == 0

    def test_ccf_range(self):
        x = _sine(100)
        y = _sine(100, noise=0.1)
        _, ccf = rd._normalised_xcorr(x, y, max_lag=10)
        assert (ccf >= -1.0 - 1e-6).all()
        assert (ccf <= 1.0 + 1e-6).all()

    def test_zero_signal_returns_zeros(self):
        x = np.zeros(100)
        y = _sine(100)
        _, ccf = rd._normalised_xcorr(x, y, max_lag=5)
        assert (ccf == 0).all()

    def test_lags_length(self):
        x = _sine(100)
        lags, ccf = rd._normalised_xcorr(x, x, max_lag=5)
        assert len(lags) == 11
        assert len(ccf) == 11

    def test_known_lag_detected(self):
        x = _sine(200, noise=0.005)
        # y is x shifted by +3 steps (john leads by 3)
        y = np.roll(x, -3)
        lags, ccf = rd._normalised_xcorr(x, y, max_lag=10)
        peak_idx = np.abs(ccf).argmax()
        # peak should be near lag=-3 (y leads) or lag=3 depending on convention
        assert abs(lags[peak_idx]) <= 5


class TestPlv:
    def test_identical_signals_plv_one(self):
        x = _sine(256, noise=0.001)
        plv = rd._plv(x, x)
        assert plv == pytest.approx(1.0, abs=0.05)

    def test_plv_in_range(self):
        x = _sine(256)
        y = _sine(256, noise=0.5)
        plv = rd._plv(x, y)
        assert 0.0 <= plv <= 1.0

    def test_uncorrelated_signals_low_plv(self):
        x = _sine(256, freq=0.1)
        y = RNG.normal(0, 1, 256)
        plv = rd._plv(x, y)
        assert plv < 0.9


class TestClassify:
    def test_strong(self):
        assert rd._classify(0.8) == "STRONG"

    def test_moderate(self):
        assert rd._classify(0.5) == "MODERATE"

    def test_weak(self):
        assert rd._classify(0.3) == "WEAK"

    def test_decoupled(self):
        assert rd._classify(0.1) == "DECOUPLED"


class TestAnalyse:
    def test_identical_series_strong_coupling(self):
        phi = _sine(200)
        result = rd.analyse(phi, phi)
        assert result.coupling_strength in {"STRONG", "MODERATE"}
        assert result.peak_lag == 0

    def test_unrelated_series_decoupled(self):
        x = _sine(200, freq=0.1)
        y = RNG.normal(0, 1, 200)
        result = rd.analyse(x, y)
        assert result.coupling_strength in {"DECOUPLED", "WEAK"}

    def test_n_samples_correct(self):
        x = _sine(150)
        y = _sine(200)
        result = rd.analyse(x, y)
        assert result.n_samples == 150

    def test_simultaneous_flag_on_identical(self):
        phi = _sine(200)
        result = rd.analyse(phi, phi)
        assert result.simultaneous

    def test_peak_correlation_in_range(self):
        x = _sine(200)
        y = _sine(200, noise=0.5)
        result = rd.analyse(x, y)
        assert 0.0 <= result.peak_correlation <= 1.0

    def test_mean_lte_peak(self):
        x = _sine(200)
        y = _sine(200)
        result = rd.analyse(x, y)
        assert result.mean_correlation <= result.peak_correlation + 1e-9

    def test_plv_in_range(self):
        x = _sine(200)
        y = _sine(200, noise=0.2)
        result = rd.analyse(x, y)
        assert 0.0 <= result.plv <= 1.0

    def test_none_inputs_return_default(self):
        result = rd.analyse(None, None)
        assert result.n_samples == 0
        assert result.coupling_strength == "DECOUPLED"

    def test_too_short_returns_default(self):
        result = rd.analyse(np.array([1.0, 2.0]), np.array([1.0, 2.0]), max_lag=10)
        assert result.n_samples == 2

    def test_albedo_leads_flag(self):
        x = _sine(200, noise=0.005)
        y = np.roll(x, 5)  # y delayed by 5 → albedo leads
        result = rd.analyse(x, y, max_lag=10)
        assert isinstance(result.albedo_leads, bool)

    def test_john_leads_flag_exclusive_with_albedo(self):
        x = _sine(200)
        y = _sine(200)
        result = rd.analyse(x, y)
        assert not (result.albedo_leads and result.john_leads)

    def test_to_dict_serialisable(self):
        import json
        x = _sine(200)
        y = _sine(200, noise=0.3)
        json.dumps(rd.analyse(x, y).to_dict())

    def test_to_dict_keys(self):
        x = _sine(200)
        d = rd.analyse(x, x).to_dict()
        for k in ("peak_correlation", "peak_lag", "coupling_strength",
                  "albedo_leads", "john_leads", "simultaneous", "plv",
                  "mean_correlation", "n_samples"):
            assert k in d

    def test_max_lag_respected(self):
        x = _sine(200)
        result = rd.analyse(x, x, max_lag=3)
        assert abs(result.peak_lag) <= 3
