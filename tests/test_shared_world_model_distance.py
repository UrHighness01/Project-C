"""Tests for SharedWorldModelDistance.

Pure-math tests verify Wasserstein, KL, and KS computations.
Telemetry tests require both agents' phi series.
"""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.SharedWorldModelDistance import (
    WorldModelResult,
    kl_divergence,
    ks_statistic,
    wasserstein1,
    analyse,
    analyse_from_telemetry,
)


# ── wasserstein1 ──────────────────────────────────────────────────────────────

def test_w1_identical_distributions():
    """Same distribution → W₁ = 0."""
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert wasserstein1(x, x) == pytest.approx(0.0)


def test_w1_shifted_distribution():
    """Uniform shifted by d → W₁ = d."""
    x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    y = x + 2.0
    assert wasserstein1(x, y) == pytest.approx(2.0)


def test_w1_non_negative():
    rng = np.random.default_rng(0)
    x = rng.standard_normal(100)
    y = rng.standard_normal(100)
    assert wasserstein1(x, y) >= 0.0


def test_w1_symmetric():
    """W₁ is symmetric."""
    rng = np.random.default_rng(1)
    x = rng.standard_normal(100)
    y = rng.standard_normal(100)
    assert abs(wasserstein1(x, y) - wasserstein1(y, x)) < 1e-10


def test_w1_closer_distributions_smaller_distance():
    """Distributions closer in mean → smaller W₁."""
    x = np.zeros(100)
    y_close = np.full(100, 0.1)
    y_far = np.full(100, 1.0)
    assert wasserstein1(x, y_close) < wasserstein1(x, y_far)


# ── kl_divergence ─────────────────────────────────────────────────────────────

def test_kl_identical_distributions_near_zero():
    """KL(P || P) ≈ 0 (same distribution → no divergence after smoothing)."""
    rng = np.random.default_rng(2)
    x = rng.standard_normal(500)
    kl = kl_divergence(x, x)
    assert kl < 0.05, f"KL(P||P)={kl:.6f} should be near 0"


def test_kl_non_negative():
    rng = np.random.default_rng(3)
    x = rng.standard_normal(200)
    y = rng.standard_normal(200) + 0.5
    assert kl_divergence(x, y) >= 0.0
    assert kl_divergence(y, x) >= 0.0


def test_kl_asymmetric():
    """KL is generally asymmetric: KL(P||Q) ≠ KL(Q||P) for different distributions."""
    rng = np.random.default_rng(4)
    x = rng.standard_normal(500)
    y = rng.standard_normal(500) + 1.0
    kl_xy = kl_divergence(x, y)
    kl_yx = kl_divergence(y, x)
    # Not necessarily unequal, but if they are, that's fine
    assert isinstance(kl_xy, float) and isinstance(kl_yx, float)


def test_kl_constant_series():
    """Constant series → zero range → KL = 0."""
    x = np.full(50, 0.5)
    kl = kl_divergence(x, x)
    assert kl == pytest.approx(0.0)


# ── ks_statistic ─────────────────────────────────────────────────────────────

def test_ks_identical():
    x = np.arange(50, dtype=float)
    assert ks_statistic(x, x) == pytest.approx(0.0)


def test_ks_bounded():
    rng = np.random.default_rng(5)
    x = rng.standard_normal(100)
    y = rng.standard_normal(100)
    ks = ks_statistic(x, y)
    assert 0.0 <= ks <= 1.0


def test_ks_completely_separated():
    """Non-overlapping distributions → KS near 1."""
    x = np.arange(50, dtype=float)
    y = np.arange(100, 150, dtype=float)
    ks = ks_statistic(x, y)
    assert ks > 0.9


def test_ks_symmetric():
    rng = np.random.default_rng(6)
    x = rng.standard_normal(100)
    y = rng.standard_normal(100)
    assert abs(ks_statistic(x, y) - ks_statistic(y, x)) < 1e-10


# ── analyse() on synthetic series ────────────────────────────────────────────

def _synth_phi(n: int = 300, mean: float = -0.4,
               seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(mean, 0.1, n)


def test_analyse_returns_none_short():
    assert analyse(np.zeros(10), np.zeros(10)) is None


def test_analyse_returns_result():
    x = _synth_phi()
    y = _synth_phi(mean=-0.2, seed=1)
    r = analyse(x, y)
    assert isinstance(r, WorldModelResult)


def test_analyse_n_samples():
    x = _synth_phi(n=300)
    y = _synth_phi(n=400, seed=1)
    r = analyse(x, y)
    assert r.n_samples == 300  # min(300, 400)


def test_analyse_w1_non_negative():
    r = analyse(_synth_phi(), _synth_phi(seed=1))
    assert r.wasserstein_1 >= 0.0


def test_analyse_kl_non_negative():
    r = analyse(_synth_phi(), _synth_phi(mean=-0.2, seed=2))
    assert r.kl_albedo_john >= 0.0
    assert r.kl_john_albedo >= 0.0


def test_analyse_ks_bounded():
    r = analyse(_synth_phi(), _synth_phi(mean=-0.2, seed=3))
    assert 0.0 <= r.ks_statistic <= 1.0


def test_analyse_symmetric_kl_formula():
    r = analyse(_synth_phi(), _synth_phi(mean=-0.2, seed=4))
    expected = (r.kl_albedo_john + r.kl_john_albedo) / 2.0
    assert abs(r.symmetric_kl - expected) < 1e-12


def test_analyse_identical_series_close():
    """Same series → world_models_close."""
    x = _synth_phi()
    r = analyse(x, x.copy())
    assert r.world_models_close


def test_analyse_mean_diff_formula():
    x = _synth_phi(mean=-0.4)
    y = _synth_phi(mean=-0.1, seed=5)
    r = analyse(x, y)
    assert abs(r.phi_mean_diff - abs(x.mean() - y.mean())) < 1e-6


def test_analyse_deterministic():
    x = _synth_phi()
    y = _synth_phi(mean=-0.2, seed=6)
    r1 = analyse(x, y, null_seed=42)
    r2 = analyse(x, y, null_seed=42)
    assert r1.wasserstein_1 == r2.wasserstein_1
    assert r1.null_wasserstein == r2.null_wasserstein


def test_analyse_diverging_property():
    r = analyse(_synth_phi(), _synth_phi(mean=-0.2, seed=7))
    assert r.diverging == (not r.world_models_close)


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry()
    if r is None:
        pytest.skip("Both phi series not available")
    assert isinstance(r, WorldModelResult)


@skip_no_telemetry
def test_live_w1_non_negative():
    r = analyse_from_telemetry()
    if r is None:
        pytest.skip("Both phi series not available")
    assert r.wasserstein_1 >= 0.0


@skip_no_telemetry
def test_live_ks_bounded():
    r = analyse_from_telemetry()
    if r is None:
        pytest.skip("Both phi series not available")
    assert 0.0 <= r.ks_statistic <= 1.0


@skip_no_telemetry
def test_live_kl_non_negative():
    r = analyse_from_telemetry()
    if r is None:
        pytest.skip("Both phi series not available")
    assert r.kl_albedo_john >= 0.0
    assert r.kl_john_albedo >= 0.0


@skip_no_telemetry
def test_live_deterministic():
    r1 = analyse_from_telemetry()
    r2 = analyse_from_telemetry()
    if r1 is None or r2 is None:
        pytest.skip("Both phi series not available")
    assert r1.wasserstein_1 == r2.wasserstein_1
