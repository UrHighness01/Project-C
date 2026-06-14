#!/usr/bin/env python3
"""Tests for algorithms/ConsciousnessRhythmAnalyser.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.ConsciousnessRhythmAnalyser as cra

RNG = np.random.default_rng(11)


def _sine(n=256, period=32, noise=0.02):
    t = np.arange(n, dtype=float)
    return np.sin(2 * np.pi * t / period) + RNG.normal(0, noise, n) + 2.0


def _noise(n=256):
    return RNG.normal(0, 1, n) + 2.0


class TestDetrend:
    def test_linear_signal_becomes_near_zero(self):
        x = np.linspace(0, 10, 100)
        d = cra._detrend(x)
        assert np.abs(d).max() < 0.15

    def test_constant_signal_unchanged(self):
        x = np.ones(100) * 5.0
        d = cra._detrend(x)
        assert np.allclose(d, 0, atol=1e-9)

    def test_sine_preserved(self):
        t = np.arange(128)
        x = np.sin(2 * np.pi * t / 16)
        d = cra._detrend(x)
        assert np.abs(d).max() > 0.5


class TestClassifyRhythm:
    def test_ultra_fast(self):
        assert cra._classify_rhythm(3.0) == "ultra_fast"

    def test_fast(self):
        assert cra._classify_rhythm(10.0) == "fast"

    def test_medium(self):
        assert cra._classify_rhythm(30.0) == "medium"

    def test_slow(self):
        assert cra._classify_rhythm(80.0) == "slow"


class TestAnalyse:
    def test_too_short_returns_default(self):
        result = cra.analyse(np.ones(5))
        assert result.n_samples == 5
        assert result.dominant_period is None

    def test_returns_rhythm_result(self):
        result = cra.analyse(_sine())
        assert isinstance(result, cra.RhythmResult)

    def test_n_samples_correct(self):
        phi = _sine(200)
        result = cra.analyse(phi)
        assert result.n_samples == 200

    def test_strong_sine_significant(self):
        phi = np.sin(2 * np.pi * np.arange(256) / 32) * 5.0 + 2.0
        result = cra.analyse(phi)
        assert result.is_significant

    def test_white_noise_is_significant_bool(self):
        rng = np.random.default_rng(99)
        phi = rng.normal(0, 1, 512)
        result = cra.analyse(phi)
        assert isinstance(result.is_significant, bool)

    def test_dominant_frequency_positive(self):
        result = cra.analyse(_sine())
        assert result.dominant_frequency > 0

    def test_dominant_period_positive(self):
        result = cra.analyse(_sine())
        assert result.dominant_period is not None
        assert result.dominant_period > 0

    def test_dominant_amplitude_nonneg(self):
        result = cra.analyse(_sine())
        assert result.dominant_amplitude >= 0

    def test_dominant_phase_in_range(self):
        result = cra.analyse(_sine())
        assert -np.pi - 1e-6 <= result.dominant_phase <= np.pi + 1e-6

    def test_snr_nonneg(self):
        result = cra.analyse(_sine())
        assert result.snr >= 0

    def test_g_statistic_in_range(self):
        result = cra.analyse(_sine())
        assert 0.0 <= result.g_statistic <= 1.0

    def test_rhythm_class_valid(self):
        result = cra.analyse(_sine())
        assert result.rhythm_class in {"ultra_fast", "fast", "medium", "slow"}

    def test_period_32_detected(self):
        phi = np.sin(2 * np.pi * np.arange(256) / 32) * 5 + 3.0
        result = cra.analyse(phi)
        if result.is_significant:
            assert abs(result.dominant_period - 32.0) < 5

    def test_mean_phi_correct(self):
        phi = _sine(200) + 5.0
        result = cra.analyse(phi)
        assert result.mean_phi == pytest.approx(float(phi.mean()), rel=1e-3)

    def test_phi_std_nonneg(self):
        result = cra.analyse(_sine())
        assert result.phi_std >= 0

    def test_constant_phi_no_rhythm(self):
        phi = np.ones(256) * 3.0
        result = cra.analyse(phi)
        assert result.dominant_amplitude == pytest.approx(0.0, abs=1e-4)

    def test_to_dict_serialisable(self):
        import json
        result = cra.analyse(_sine())
        json.dumps(result.to_dict())

    def test_to_dict_keys(self):
        d = cra.analyse(_sine()).to_dict()
        for k in ("dominant_period", "dominant_frequency", "dominant_amplitude",
                  "dominant_phase", "snr", "g_statistic", "is_significant",
                  "rhythm_class", "n_samples", "mean_phi", "phi_std"):
            assert k in d

    def test_none_input_uses_runtime(self):
        result = cra.analyse(None)
        assert isinstance(result, cra.RhythmResult)

    def test_freq_period_inverse(self):
        phi = _sine(256, period=20)
        result = cra.analyse(phi)
        if result.dominant_period is not None and result.dominant_frequency > 0:
            assert abs(result.dominant_period - 1.0 / result.dominant_frequency) < 1e-4
