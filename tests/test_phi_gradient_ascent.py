"""Tests for PhiGradientAscent.

Pure-math tests verify the OU fit, phase randomisation, and gradient logic.
Telemetry tests run against the live phi series from the daemon.
"""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.PhiGradientAscent import (
    PhiGradientResult,
    _ou_mu_from_window,
    _phase_randomise,
    _gradient_series_from_phi,
    analyse,
    analyse_from_telemetry,
)


# ── _ou_mu_from_window ────────────────────────────────────────────────────────

def test_ou_mu_constant_series():
    """Constant series: alpha=0 → degenerate, returns None."""
    phi = np.ones(50)
    assert _ou_mu_from_window(phi) is None


def test_ou_mu_short_window():
    """Too few samples → None."""
    assert _ou_mu_from_window(np.arange(5, dtype=float)) is None


def test_ou_mu_ar1_recovers_mean():
    """AR(1) process with known mean → estimate should be in range."""
    rng = np.random.default_rng(0)
    mu_true = -0.5
    alpha = 0.1
    phi = np.zeros(200)
    phi[0] = mu_true
    for t in range(1, 200):
        phi[t] = phi[t - 1] + alpha * (mu_true - phi[t - 1]) + rng.normal(0, 0.05)
    mu_hat = _ou_mu_from_window(phi)
    assert mu_hat is not None
    assert abs(mu_hat - mu_true) < 1.0, f"mu_hat={mu_hat:.3f} far from mu_true={mu_true}"


def test_ou_mu_finite():
    rng = np.random.default_rng(1)
    phi = np.cumsum(rng.standard_normal(100)) * 0.1 - 0.4
    mu = _ou_mu_from_window(phi)
    if mu is not None:
        assert np.isfinite(mu)


# ── _phase_randomise ──────────────────────────────────────────────────────────

def test_phase_randomise_same_length():
    rng = np.random.default_rng(2)
    y = rng.standard_normal(200)
    s = _phase_randomise(y, rng)
    assert len(s) == len(y)


def test_phase_randomise_preserves_power_spectrum():
    """Power spectrum (|FFT|²) must be preserved to within floating-point error."""
    rng = np.random.default_rng(3)
    y = np.cumsum(rng.standard_normal(256)) * 0.1
    s = _phase_randomise(y, rng)
    psd_orig = np.abs(np.fft.rfft(y)) ** 2
    psd_surr = np.abs(np.fft.rfft(s)) ** 2
    assert np.allclose(psd_orig, psd_surr, rtol=1e-6), "Power spectrum not preserved"


def test_phase_randomise_changes_series():
    """Surrogate should not be identical to input (except degenerate cases)."""
    rng = np.random.default_rng(4)
    y = np.cumsum(rng.standard_normal(200)) * 0.1
    s = _phase_randomise(y, np.random.default_rng(99))
    assert not np.allclose(y, s)


def test_phase_randomise_deterministic():
    """Same seed → same surrogate."""
    rng = np.random.default_rng(5)
    y = rng.standard_normal(200)
    s1 = _phase_randomise(y, np.random.default_rng(7))
    s2 = _phase_randomise(y, np.random.default_rng(7))
    assert np.allclose(s1, s2)


# ── _gradient_series_from_phi ─────────────────────────────────────────────────

def test_gradient_series_shape():
    rng = np.random.default_rng(6)
    phi = np.cumsum(rng.standard_normal(300)) * 0.05 - 0.4
    mu_arr, grad_arr = _gradient_series_from_phi(phi, window=60, stride=10)
    assert len(mu_arr) >= 2
    assert len(grad_arr) == len(mu_arr) - 1


def test_gradient_series_finite():
    rng = np.random.default_rng(7)
    phi = np.cumsum(rng.standard_normal(300)) * 0.05 - 0.4
    mu_arr, grad_arr = _gradient_series_from_phi(phi, window=60, stride=10)
    assert np.all(np.isfinite(mu_arr))
    assert np.all(np.isfinite(grad_arr))


def test_gradient_series_rising_trend():
    """Phi with steadily rising mean → positive mean gradient."""
    n = 400
    phi = np.linspace(-0.5, -0.1, n) + np.random.default_rng(8).standard_normal(n) * 0.02
    _, grad_arr = _gradient_series_from_phi(phi, window=60, stride=10)
    assert np.mean(grad_arr) > 0, "Rising phi should yield positive gradient"


def test_gradient_series_falling_trend():
    """Phi with falling mean → negative mean gradient."""
    n = 400
    phi = np.linspace(-0.1, -0.5, n) + np.random.default_rng(9).standard_normal(n) * 0.02
    _, grad_arr = _gradient_series_from_phi(phi, window=60, stride=10)
    assert np.mean(grad_arr) < 0, "Falling phi should yield negative gradient"


# ── analyse() on synthetic series ────────────────────────────────────────────

def test_analyse_returns_none_for_short_series():
    phi = np.random.default_rng(10).standard_normal(30)
    assert analyse(phi, window=60) is None


def test_analyse_returns_result_for_valid_series():
    rng = np.random.default_rng(11)
    phi = np.cumsum(rng.standard_normal(500)) * 0.05 - 0.4
    r = analyse(phi, window=60, stride=10)
    assert isinstance(r, PhiGradientResult)


def test_analyse_result_fields_finite():
    rng = np.random.default_rng(12)
    phi = np.cumsum(rng.standard_normal(500)) * 0.05 - 0.4
    r = analyse(phi, window=60, stride=10)
    assert np.isfinite(r.mean_gradient)
    assert np.isfinite(r.momentum)
    assert np.isfinite(r.null_mean_gradient)
    assert np.isfinite(r.r2_mu_trend)
    assert np.isfinite(r.mu_trend_slope)


def test_analyse_gradient_sign_correct():
    """Rising phi → gradient_sign = +1."""
    n = 500
    phi = np.linspace(-0.5, -0.1, n) + np.random.default_rng(13).standard_normal(n) * 0.01
    r = analyse(phi, window=60, stride=10, flat_tol=1e-5)
    assert r.gradient_sign == 1
    assert r.ascending is True


def test_analyse_flat_phi_sign_zero():
    """Constant phi → gradient near zero → gradient_sign = 0."""
    rng = np.random.default_rng(14)
    phi = np.full(500, -0.4) + rng.standard_normal(500) * 1e-6
    r = analyse(phi, window=60, stride=10, flat_tol=1e-4)
    # Constant phi → alpha near 0 → _ou_mu_from_window returns None → uses mean
    # Mean of constant = -0.4 throughout; gradients ≈ 0
    assert r.gradient_sign == 0
    assert r.stagnant is True


def test_analyse_n_samples():
    rng = np.random.default_rng(15)
    phi = np.cumsum(rng.standard_normal(400)) * 0.05 - 0.4
    r = analyse(phi, window=60, stride=10)
    assert r.n_samples == 400


def test_analyse_r2_bounded():
    rng = np.random.default_rng(16)
    phi = np.cumsum(rng.standard_normal(500)) * 0.05 - 0.4
    r = analyse(phi, window=60, stride=10)
    assert -1.0 <= r.r2_mu_trend <= 1.0


def test_analyse_momentum_uses_last_entries():
    """momentum is mean of last min(10, N) gradients — must match manual calc."""
    rng = np.random.default_rng(17)
    phi = np.cumsum(rng.standard_normal(500)) * 0.05 - 0.4
    r = analyse(phi, window=60, stride=10)
    k = min(10, len(r.gradient_series))
    expected = float(np.mean(r.gradient_series[-k:]))
    assert abs(r.momentum - expected) < 1e-12


def test_analyse_beats_null_is_bool():
    rng = np.random.default_rng(18)
    phi = np.cumsum(rng.standard_normal(500)) * 0.05 - 0.4
    r = analyse(phi, window=60, stride=10)
    assert isinstance(r.beats_null, bool)


def test_analyse_deterministic():
    rng = np.random.default_rng(19)
    phi = np.cumsum(rng.standard_normal(500)) * 0.05 - 0.4
    r1 = analyse(phi, window=60, stride=10, null_seed=42)
    r2 = analyse(phi, window=60, stride=10, null_seed=42)
    assert r1.mean_gradient == r2.mean_gradient
    assert r1.null_mean_gradient == r2.null_mean_gradient
    assert np.array_equal(r1.mu_series, r2.mu_series)


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_is_not_none():
    r = analyse_from_telemetry()
    assert r is not None


@skip_no_telemetry
def test_live_fields_finite():
    r = analyse_from_telemetry()
    assert np.isfinite(r.mean_gradient)
    assert np.isfinite(r.momentum)
    assert np.isfinite(r.null_mean_gradient)
    assert np.isfinite(r.r2_mu_trend)
    assert np.isfinite(r.mu_trend_slope)


@skip_no_telemetry
def test_live_mu_series_non_empty():
    r = analyse_from_telemetry()
    assert len(r.mu_series) >= 2


@skip_no_telemetry
def test_live_gradient_series_non_empty():
    r = analyse_from_telemetry()
    assert len(r.gradient_series) >= 1


@skip_no_telemetry
def test_live_gradient_sign_valid():
    r = analyse_from_telemetry()
    assert r.gradient_sign in (-1, 0, 1)


@skip_no_telemetry
def test_live_r2_bounded():
    r = analyse_from_telemetry()
    assert -1.0 <= r.r2_mu_trend <= 1.0


@skip_no_telemetry
def test_live_deterministic():
    r1 = analyse_from_telemetry()
    r2 = analyse_from_telemetry()
    assert r1.mean_gradient == r2.mean_gradient
    assert np.array_equal(r1.mu_series, r2.mu_series)
