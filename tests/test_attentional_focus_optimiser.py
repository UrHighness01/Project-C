"""Tests for AttentionalFocusOptimiser.

Pure-math tests cover local surprise, softmax, KL divergence, entropy.
Telemetry tests run against real phi from the daemon.
"""
import math

import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.AttentionalFocusOptimiser import (
    AttentionResult,
    _entropy,
    _kl_from_uniform,
    _local_surprise,
    _phase_randomise,
    _softmax,
    analyse,
    analyse_from_telemetry,
)


# ── _local_surprise ───────────────────────────────────────────────────────────

def test_local_surprise_constant_phi():
    """Constant phi → local variance = 0 everywhere."""
    phi = np.full(60, 0.5)
    s = _local_surprise(phi, half_window=5)
    assert np.all(s == pytest.approx(0.0))


def test_local_surprise_length():
    n, k = 100, 10
    s = _local_surprise(np.arange(n, dtype=float), half_window=k)
    assert len(s) == n - 2 * k


def test_local_surprise_non_negative():
    rng = np.random.default_rng(0)
    phi = rng.standard_normal(200)
    s = _local_surprise(phi, half_window=10)
    assert np.all(s >= 0.0)


def test_local_surprise_spike():
    """A spike at the centre should have high local variance."""
    phi = np.zeros(60)
    phi[30] = 10.0
    s = _local_surprise(phi, half_window=5)
    # Centre positions near 30 should have high variance
    assert s.max() > 1.0


def test_local_surprise_short_series():
    phi = np.array([1.0, 2.0, 3.0])
    s = _local_surprise(phi, half_window=5)
    assert len(s) == 0


# ── _softmax ──────────────────────────────────────────────────────────────────

def test_softmax_sums_to_one():
    rng = np.random.default_rng(1)
    x = rng.standard_normal(20)
    w = _softmax(x, temperature=1.0)
    assert abs(w.sum() - 1.0) < 1e-10


def test_softmax_all_equal_gives_uniform():
    x = np.ones(10)
    w = _softmax(x, temperature=1.0)
    assert np.allclose(w, 1.0 / 10)


def test_softmax_high_temperature_approaches_uniform():
    rng = np.random.default_rng(2)
    x = rng.standard_normal(20)
    w = _softmax(x, temperature=1e6)
    assert np.allclose(w, 1.0 / 20, atol=1e-4)


def test_softmax_winner_take_all():
    x = np.array([0.0, 0.0, 5.0, 0.0])
    w = _softmax(x, temperature=1e-15)
    assert w[2] == pytest.approx(1.0)
    assert w.sum() == pytest.approx(1.0)


def test_softmax_non_negative():
    rng = np.random.default_rng(3)
    x = rng.standard_normal(30)
    w = _softmax(x, temperature=0.5)
    assert np.all(w >= 0.0)


# ── _kl_from_uniform ─────────────────────────────────────────────────────────

def test_kl_uniform_is_zero():
    n = 20
    w = np.full(n, 1.0 / n)
    assert _kl_from_uniform(w) == pytest.approx(0.0, abs=1e-10)


def test_kl_concentrated_is_positive():
    """Peaked distribution → KL > 0."""
    n = 20
    w = np.zeros(n)
    w[0] = 1.0
    kl = _kl_from_uniform(w)
    assert kl > 0.0


def test_kl_maximum_at_point_mass():
    """Single point mass → KL = log(N) nats."""
    n = 20
    w = np.zeros(n)
    w[0] = 1.0
    kl = _kl_from_uniform(w)
    assert abs(kl - math.log(n)) < 1e-10


def test_kl_non_negative():
    rng = np.random.default_rng(4)
    x = rng.exponential(size=30)
    w = x / x.sum()
    assert _kl_from_uniform(w) >= 0.0


# ── _entropy ─────────────────────────────────────────────────────────────────

def test_entropy_uniform():
    n = 16
    w = np.full(n, 1.0 / n)
    assert abs(_entropy(w) - math.log(n)) < 1e-10


def test_entropy_point_mass():
    w = np.zeros(10)
    w[0] = 1.0
    assert _entropy(w) == pytest.approx(0.0)


def test_entropy_non_negative():
    rng = np.random.default_rng(5)
    x = rng.exponential(size=20)
    w = x / x.sum()
    assert _entropy(w) >= 0.0


# ── analyse() on synthetic series ────────────────────────────────────────────

def _synthetic_phi(n: int = 500, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.cumsum(rng.standard_normal(n)) * 0.05 - 0.4


def test_analyse_returns_none_for_short_series():
    phi = np.random.default_rng(0).standard_normal(20)
    assert analyse(phi, half_window=15) is None


def test_analyse_returns_result():
    r = analyse(_synthetic_phi())
    assert isinstance(r, AttentionResult)


def test_analyse_attention_sums_to_one():
    r = analyse(_synthetic_phi())
    assert abs(r.attention_weights.sum() - 1.0) < 1e-10


def test_analyse_attention_non_negative():
    r = analyse(_synthetic_phi())
    assert np.all(r.attention_weights >= 0.0)


def test_analyse_focus_non_negative():
    r = analyse(_synthetic_phi())
    assert r.focus_score >= 0.0


def test_analyse_focus_finite():
    r = analyse(_synthetic_phi())
    assert math.isfinite(r.focus_score)


def test_analyse_sharpness_bounded():
    r = analyse(_synthetic_phi())
    assert 0.0 <= r.focus_sharpness <= 1.0


def test_analyse_peak_index_valid():
    r = analyse(_synthetic_phi())
    assert 0 <= r.peak_index < len(r.attention_weights)


def test_analyse_peak_is_argmax():
    r = analyse(_synthetic_phi())
    assert r.peak_index == int(np.argmax(r.attention_weights))


def test_analyse_null_focus_non_negative():
    r = analyse(_synthetic_phi())
    assert r.null_focus_score >= 0.0


def test_analyse_beats_null_is_bool():
    r = analyse(_synthetic_phi())
    assert isinstance(r.beats_null, bool)


def test_analyse_deterministic():
    phi = _synthetic_phi()
    r1 = analyse(phi, null_seed=42)
    r2 = analyse(phi, null_seed=42)
    assert r1.focus_score == r2.focus_score
    assert r1.null_focus_score == r2.null_focus_score
    assert np.array_equal(r1.attention_weights, r2.attention_weights)


def test_analyse_spiked_phi_high_sharpness():
    """Phi with a single large spike should produce sharp attention."""
    rng = np.random.default_rng(6)
    phi = rng.standard_normal(300) * 0.01 - 0.4
    phi[150] = 10.0     # large spike
    r = analyse(phi, half_window=10)
    assert r.focus_sharpness > 0.5, f"Expected high sharpness, got {r.focus_sharpness:.4f}"


def test_analyse_constant_phi_zero_focus():
    """Constant phi → zero surprise → uniform attention → zero KL."""
    phi = np.full(200, -0.4)
    r = analyse(phi, half_window=10)
    assert r is not None
    assert r.focus_score == pytest.approx(0.0, abs=1e-6)
    assert r.focus_sharpness == pytest.approx(0.0, abs=1e-6)


def test_analyse_is_selective_flag():
    r = analyse(_synthetic_phi())
    assert r.is_selective == (r.focus_sharpness > 0.01)


def test_analyse_focus_gain_formula():
    r = analyse(_synthetic_phi())
    assert abs(r.focus_gain_over_null - (r.focus_score - r.null_focus_score)) < 1e-12


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry()
    assert r is not None


@skip_no_telemetry
def test_live_attention_sums_to_one():
    r = analyse_from_telemetry()
    assert abs(r.attention_weights.sum() - 1.0) < 1e-10


@skip_no_telemetry
def test_live_focus_non_negative():
    r = analyse_from_telemetry()
    assert r.focus_score >= 0.0


@skip_no_telemetry
def test_live_sharpness_bounded():
    r = analyse_from_telemetry()
    assert 0.0 <= r.focus_sharpness <= 1.0


@skip_no_telemetry
def test_live_temperature_positive():
    r = analyse_from_telemetry()
    assert r.temperature > 0.0


@skip_no_telemetry
def test_live_deterministic():
    r1 = analyse_from_telemetry()
    r2 = analyse_from_telemetry()
    assert r1.focus_score == r2.focus_score
    assert r1.null_focus_score == r2.null_focus_score
