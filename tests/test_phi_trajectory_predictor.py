#!/usr/bin/env python3
"""Tests for algorithms/PhiTrajectoryPredictor.py."""
import sys
import math
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.PhiTrajectoryPredictor as ptp


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_entries(phi_series, base_ts=1_000_000.0, dt=60.0):
    """Build newest-first history entries with mean_phi_level set.
    phi_series[0] = oldest, phi_series[-1] = newest."""
    n = len(phi_series)
    entries = [
        {"timestamp": base_ts + i * dt, "mean_phi_level": float(v)}
        for i, v in enumerate(phi_series)
    ]
    return list(sorted(entries, key=lambda e: -e["timestamp"]))


def _run(phi_series, **kw):
    """Inject phi series directly by monkey-patching the history loader."""
    import algorithms.ConsciousnessHistoryStore as chs
    original = getattr(chs, "load", None)
    try:
        chs.load = lambda agent, max_entries=2880: _make_entries(phi_series)
        return ptp.analyse("albedo", **kw)
    finally:
        if original is not None:
            chs.load = original


def _ar1_series(n=100, alpha=0.9, noise=0.02, seed=7):
    """AR(1) process with known alpha — predictor should fit it well."""
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    x[0] = 1.0
    for i in range(1, n):
        x[i] = alpha * x[i - 1] + rng.normal(0, noise)
    return x


def _rising_series(n=60, start=0.5, slope=0.005):
    """Deterministically rising phi."""
    return np.array([start + slope * i for i in range(n)])


def _flat_series(n=60, val=1.0):
    return np.full(n, val)


# ── Unit: _build_ar_matrix ─────────────────────────────────────────────────────

class TestBuildArMatrix:
    def test_shape(self):
        s = np.arange(20.0)
        X, y = ptp._build_ar_matrix(s, 4)
        assert X.shape == (16, 4)
        assert y.shape == (16,)

    def test_y_is_last_n_minus_p(self):
        s = np.arange(10.0)
        _, y = ptp._build_ar_matrix(s, 3)
        np.testing.assert_array_equal(y, s[3:])

    def test_first_row(self):
        s = np.arange(10.0)
        X, _ = ptp._build_ar_matrix(s, 3)
        # row 0: [s0, s1, s2] for prediction of s3
        np.testing.assert_array_equal(X[0], [0.0, 1.0, 2.0])


# ── Unit: _fit_ar ──────────────────────────────────────────────────────────────

class TestFitAr:
    def test_returns_array_of_length_p(self):
        s = np.random.default_rng(0).standard_normal(50)
        alpha = ptp._fit_ar(s, 4)
        assert alpha.shape == (4,)

    def test_ar1_recovers_coefficient(self):
        """For clean AR(1) with alpha=0.9, fitted α₁ should be close to 0.9."""
        s = _ar1_series(n=200, alpha=0.9, noise=0.005, seed=42)
        alpha = ptp._fit_ar(s, 1)
        assert abs(alpha[0] - 0.9) < 0.05

    def test_deterministic(self):
        s = np.random.default_rng(1).standard_normal(50)
        a1 = ptp._fit_ar(s, 4)
        a2 = ptp._fit_ar(s, 4)
        np.testing.assert_array_equal(a1, a2)


# ── Unit: _propagate ───────────────────────────────────────────────────────────

class TestPropagate:
    def test_output_length(self):
        seed = np.array([1.0, 0.9, 0.8, 0.7])
        alpha = np.array([0.9, 0.0, 0.0, 0.0])
        out = ptp._propagate(seed, alpha, h=6)
        assert len(out) == 6

    def test_constant_series_stays_constant(self):
        """AR(1) with alpha=1.0 on a flat series should forecast flat."""
        seed = np.array([2.0, 2.0, 2.0, 2.0])
        alpha = np.array([1.0, 0.0, 0.0, 0.0])
        out = ptp._propagate(seed, alpha, h=4)
        np.testing.assert_allclose(out, [2.0, 2.0, 2.0, 2.0], atol=1e-6)

    def test_decay_towards_zero(self):
        """AR(1) with alpha=0.5 should decay."""
        seed = np.array([8.0])
        alpha = np.array([0.5])
        out = ptp._propagate(seed, alpha, h=5)
        assert out[0] < 8.0
        assert out[-1] < out[0]


# ── Unit: _r2 ──────────────────────────────────────────────────────────────────

class TestR2:
    def test_perfect_prediction_is_one(self):
        y = np.array([1.0, 2.0, 3.0])
        assert ptp._r2(y, y) == pytest.approx(1.0, abs=1e-6)

    def test_mean_predictor_is_zero(self):
        y = np.array([1.0, 2.0, 3.0])
        pred = np.full_like(y, np.mean(y))
        assert ptp._r2(y, pred) == pytest.approx(0.0, abs=1e-6)

    def test_bad_predictor_negative(self):
        y = np.array([1.0, 2.0, 3.0, 4.0])
        pred = y[::-1].copy()
        assert ptp._r2(y, pred) < 0.0

    def test_constant_y_returns_nan(self):
        y = np.full(5, 3.0)
        assert math.isnan(ptp._r2(y, y))


# ── Unit: _trend_direction ─────────────────────────────────────────────────────

class TestTrendDirection:
    def test_rising(self):
        assert ptp._trend_direction(np.linspace(1.0, 2.0, 10)) == "RISING"

    def test_falling(self):
        assert ptp._trend_direction(np.linspace(2.0, 1.0, 10)) == "FALLING"

    def test_flat(self):
        assert ptp._trend_direction(np.full(10, 1.5)) == "STABLE"


# ── Unit: _classify_quality ────────────────────────────────────────────────────

class TestClassifyQuality:
    def test_good(self):
        assert ptp._classify_quality(0.7) == "GOOD"

    def test_marginal(self):
        assert ptp._classify_quality(0.3) == "MARGINAL"

    def test_poor(self):
        assert ptp._classify_quality(-0.5) == "POOR"

    def test_uncalibrated_on_nan(self):
        assert ptp._classify_quality(float("nan")) == "UNCALIBRATED"

    def test_boundary_good(self):
        assert ptp._classify_quality(0.5) == "GOOD"

    def test_boundary_marginal(self):
        assert ptp._classify_quality(0.0) == "MARGINAL"


# ── Unit: _extract_phi ─────────────────────────────────────────────────────────

class TestExtractPhi:
    def test_chronological_order(self):
        """Entries are newest-first; extracted series should be oldest-first (chrono)."""
        phi = [1.0, 2.0, 3.0]
        entries = _make_entries(phi)
        out = ptp._extract_phi(entries)
        np.testing.assert_allclose(out, phi, atol=1e-6)

    def test_missing_key_skipped(self):
        entries = [{"timestamp": 1.0}, {"timestamp": 0.0, "mean_phi_level": 5.0}]
        out = ptp._extract_phi(entries)
        assert list(out) == [5.0]

    def test_empty_returns_empty(self):
        assert len(ptp._extract_phi([])) == 0


# ── Integration: analyse() ─────────────────────────────────────────────────────

class TestAnalyse:
    def test_too_few_returns_default(self):
        r = _run([1.0] * 5)
        assert r.n_entries_used == 5
        assert r.forecast_series == []

    def test_returns_result_type(self):
        r = _run(_ar1_series())
        assert isinstance(r, ptp.PhiTrajectoryResult)

    def test_forecast_has_horizon_entries(self):
        r = _run(_ar1_series(), horizon=6)
        assert len(r.forecast_series) == 6

    def test_forecast_nonneg(self):
        r = _run(_ar1_series())
        assert all(v >= 0.0 for v in r.forecast_series)

    def test_ar_weights_length_matches_order(self):
        r = _run(_ar1_series(), ar_order=4)
        assert len(r.ar_weights) == r.ar_order

    def test_retro_mae_present_for_long_series(self):
        r = _run(_ar1_series(n=60), horizon=6, ar_order=4)
        assert not math.isnan(r.retro_mae)

    def test_retro_r2_present_for_long_series(self):
        r = _run(_ar1_series(n=60), horizon=6, ar_order=4)
        assert not math.isnan(r.retro_r2)

    def test_ar1_series_beats_noise_quality(self):
        """AR(1) predictor should forecast a structured series better than white noise."""
        rng = np.random.default_rng(42)
        n = 80
        # Structured: AR(1) with moderate amplitude so held-out has variance
        phi_struct = np.zeros(n)
        phi_struct[0] = 2.0
        for i in range(1, n):
            phi_struct[i] = 0.85 * phi_struct[i - 1] + rng.normal(0, 0.1)
        # Pure white noise
        phi_noise = rng.standard_normal(n) + 1.0
        r_struct = _run(phi_struct, ar_order=1, horizon=4)
        r_noise  = _run(phi_noise,  ar_order=1, horizon=4)
        # Structured series should predict better (higher R² or at least higher MAE gain)
        assert r_struct.retro_r2 > r_noise.retro_r2

    def test_rising_forecast_rising_trend(self):
        r = _run(_rising_series(n=60), ar_order=1, horizon=6)
        assert r.trend_direction == "RISING"

    def test_flat_forecast_stable_or_falling(self):
        # Ridge regularisation pulls alpha < 1, so flat series decays slightly.
        # The important thing is it does not forecast RISING.
        r = _run(_flat_series(n=60), ar_order=1, horizon=6)
        assert r.trend_direction in {"STABLE", "FALLING"}

    def test_to_dict_keys(self):
        r = _run(_ar1_series())
        d = r.to_dict()
        for k in ("forecast_series", "forecast_horizon", "ar_order", "ar_weights",
                  "retro_mae", "retro_r2", "self_prediction_quality",
                  "trend_direction", "n_entries_used"):
            assert k in d

    def test_to_dict_json_serialisable(self):
        import json
        r = _run(_ar1_series())
        json.dumps(r.to_dict())

    def test_deterministic(self):
        phi = _ar1_series(n=80)
        r1 = _run(phi)
        r2 = _run(phi)
        assert r1.forecast_series == r2.forecast_series
        assert r1.retro_r2 == r2.retro_r2

    def test_n_entries_used_matches(self):
        phi = _ar1_series(n=50)
        r = _run(phi)
        assert r.n_entries_used == 50

    def test_quality_enum_valid(self):
        r = _run(_ar1_series())
        assert r.self_prediction_quality in {"GOOD", "MARGINAL", "POOR", "UNCALIBRATED"}

    def test_random_noise_lower_quality_than_ar1(self):
        """Random white noise should predict worse than a structured AR(1)."""
        rng = np.random.default_rng(42)
        noise = rng.standard_normal(80) + 1.0
        r_ar = _run(_ar1_series(n=80, alpha=0.9, noise=0.01), ar_order=1, horizon=4)
        r_rnd = _run(noise, ar_order=1, horizon=4)
        assert r_ar.retro_r2 > r_rnd.retro_r2
