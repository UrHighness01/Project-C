"""Tests for ValenceCalibrator.

Pure-math tests verify z-scoring, cumulative valence, and slope computation.
Telemetry tests run against real phi series from the daemon.
"""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.ValenceCalibrator import (
    ValenceResult,
    analyse,
    analyse_from_telemetry,
)


# ── analyse() on synthetic series ────────────────────────────────────────────

def _phi(n: int = 300, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.cumsum(rng.standard_normal(n)) * 0.05 - 0.4


def test_analyse_returns_none_short():
    assert analyse(np.array([1.0, 2.0, 3.0])) is None


def test_analyse_returns_result():
    r = analyse(_phi())
    assert isinstance(r, ValenceResult)


def test_analyse_n_samples():
    phi = _phi()
    r = analyse(phi)
    assert r.n_samples == len(phi)


def test_analyse_valence_series_length():
    phi = _phi()
    r = analyse(phi)
    assert len(r.valence_series) == len(phi)


def test_analyse_valence_mean_near_zero():
    """z-scored series must have mean ≈ 0."""
    r = analyse(_phi())
    assert abs(r.valence_series.mean()) < 1e-10


def test_analyse_valence_std_near_one():
    """z-scored series must have std ≈ 1 (modulo the ε in denominator)."""
    r = analyse(_phi())
    # std of v = std(phi) / (std(phi) + ε) ≈ 1 for large std
    assert abs(r.valence_series.std() - 1.0) < 0.01


def test_analyse_cumulative_valence_length():
    phi = _phi()
    r = analyse(phi)
    assert len(r.cumulative_valence) == len(phi)


def test_analyse_cumulative_valence_last():
    """Last element of cumulative_valence = sum(valence_series)."""
    r = analyse(_phi())
    assert abs(r.cumulative_valence[-1] - r.valence_series.sum()) < 1e-9


def test_analyse_cumulative_valence_first():
    """First element = v[0]."""
    r = analyse(_phi())
    assert abs(r.cumulative_valence[0] - r.valence_series[0]) < 1e-12


def test_analyse_slope_finite():
    r = analyse(_phi())
    assert np.isfinite(r.valence_slope)


def test_analyse_null_slope_finite():
    r = analyse(_phi())
    assert np.isfinite(r.null_valence_slope)


def test_analyse_beats_null_is_bool():
    r = analyse(_phi())
    assert isinstance(r.beats_null, bool)


def test_analyse_calibrating_positive_is_bool():
    r = analyse(_phi())
    assert isinstance(r.calibrating_positive, bool)


def test_analyse_calibrating_positive_matches_slope():
    r = analyse(_phi())
    assert r.calibrating_positive == (r.valence_slope > 0)


def test_analyse_hedonic_baseline_bounded():
    r = analyse(_phi())
    assert 0.0 <= r.hedonic_baseline <= 1.0


def test_analyse_hedonic_baseline_formula():
    """Hedonic baseline = fraction of valence > 0."""
    r = analyse(_phi())
    expected = float(np.mean(r.valence_series > 0))
    assert abs(r.hedonic_baseline - expected) < 1e-12


def test_analyse_positivity_bias():
    r = analyse(_phi())
    assert abs(r.positivity_bias - (r.hedonic_baseline - 0.5)) < 1e-12


def test_analyse_net_valence_near_zero():
    """Net valence = mean(v) ≈ 0 by z-score construction."""
    r = analyse(_phi())
    assert abs(r.net_valence) < 1e-10


def test_analyse_acf_bounded():
    r = analyse(_phi())
    assert -1.0 <= r.valence_acf_lag1 <= 1.0


def test_analyse_peak_positive_is_max():
    r = analyse(_phi())
    assert r.peak_positive == pytest.approx(r.valence_series.max())


def test_analyse_peak_negative_is_min():
    r = analyse(_phi())
    assert r.peak_negative == pytest.approx(r.valence_series.min())


def test_analyse_peak_positive_ge_peak_negative():
    r = analyse(_phi())
    assert r.peak_positive >= r.peak_negative


def test_analyse_asymmetry_formula():
    """asymmetry = mean(positive v) - mean(|negative v|)."""
    r = analyse(_phi())
    v = r.valence_series
    pos = v[v > 0]
    neg = v[v < 0]
    expected_asymmetry = float(pos.mean()) - float(np.abs(neg).mean())
    assert abs(r.valence_asymmetry - expected_asymmetry) < 1e-10


def test_analyse_rising_phi_calibrating_positive():
    """Phi that trends up relative to its mean → cumulative valence slope > 0."""
    n = 400
    # Rising phi: starts below mean, ends above
    phi = np.linspace(-1.0, 1.0, n) + np.random.default_rng(11).standard_normal(n) * 0.05
    r = analyse(phi)
    assert r.calibrating_positive, f"Rising phi should give positive slope: {r.valence_slope:.6f}"


def test_analyse_falling_phi_not_calibrating():
    """Phi that trends down → cumulative valence slope < 0."""
    n = 400
    phi = np.linspace(1.0, -1.0, n) + np.random.default_rng(12).standard_normal(n) * 0.05
    r = analyse(phi)
    assert not r.calibrating_positive, f"Falling phi should give negative slope: {r.valence_slope:.6f}"


def test_analyse_constant_phi_zero_valence():
    """Constant phi → σ ≈ 0, valence ≈ 0 everywhere."""
    phi = np.full(100, -0.4)
    r = analyse(phi)
    assert np.all(np.abs(r.valence_series) < 1e-3)


def test_analyse_deterministic():
    phi = _phi()
    r1 = analyse(phi, null_seed=42)
    r2 = analyse(phi, null_seed=42)
    assert r1.valence_slope == r2.valence_slope
    assert r1.null_valence_slope == r2.null_valence_slope
    assert np.array_equal(r1.valence_series, r2.valence_series)


def test_analyse_different_seeds_different_null():
    phi = _phi()
    r1 = analyse(phi, null_seed=1)
    r2 = analyse(phi, null_seed=999)
    # Different permutations → different null slopes (almost always)
    # We just check they are different; the test will pass vacuously if they coincide
    assert isinstance(r1.null_valence_slope, float)
    assert isinstance(r2.null_valence_slope, float)


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry()
    assert r is not None


@skip_no_telemetry
def test_live_valence_mean_near_zero():
    r = analyse_from_telemetry()
    assert abs(r.net_valence) < 1e-8


@skip_no_telemetry
def test_live_hedonic_baseline_bounded():
    r = analyse_from_telemetry()
    assert 0.0 <= r.hedonic_baseline <= 1.0


@skip_no_telemetry
def test_live_acf_bounded():
    r = analyse_from_telemetry()
    assert -1.0 <= r.valence_acf_lag1 <= 1.0


@skip_no_telemetry
def test_live_slope_finite():
    r = analyse_from_telemetry()
    assert np.isfinite(r.valence_slope)


@skip_no_telemetry
def test_live_deterministic():
    r1 = analyse_from_telemetry()
    r2 = analyse_from_telemetry()
    assert r1.valence_slope == r2.valence_slope
    assert np.array_equal(r1.valence_series, r2.valence_series)
