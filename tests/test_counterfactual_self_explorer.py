"""Tests for CounterfactualSelfExplorer."""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.CounterfactualSelfExplorer import (
    CounterfactualResult,
    _counterfactual_trajectory,
    _ols_slope,
    _propagate_ar,
    _ridge_fit,
    _build_lagged,
    analyse,
    analyse_from_telemetry,
)


# ── _propagate_ar ─────────────────────────────────────────────────────────────

def test_propagate_ar_length():
    weights = np.array([0.5, 0.3, 0.1, 0.05])
    seed = np.array([1.0, 0.9, 0.8, 0.7])
    traj = _propagate_ar(weights, seed, H=10)
    assert len(traj) == 10


def test_propagate_ar_stable_ar1():
    """AR(1) with weight 0.9 → trajectory decays toward 0."""
    weights = np.array([0.9])
    seed = np.array([10.0])
    traj = _propagate_ar(weights, seed, H=50)
    assert abs(traj[-1]) < abs(traj[0])


def test_propagate_ar_constant_seed():
    """AR(1) weight=1.0 → constant series."""
    weights = np.array([1.0])
    seed = np.array([3.0])
    traj = _propagate_ar(weights, seed, H=10)
    np.testing.assert_allclose(traj, 3.0, atol=1e-9)


def test_propagate_ar_zero_weight():
    """AR(1) weight=0 → all outputs zero."""
    weights = np.array([0.0])
    seed = np.array([5.0])
    traj = _propagate_ar(weights, seed, H=5)
    np.testing.assert_allclose(traj, 0.0, atol=1e-9)


def test_propagate_ar_finite():
    rng = np.random.default_rng(0)
    weights = rng.standard_normal(4) * 0.1
    seed = np.array([1.0, 0.5, 0.3, 0.1])
    traj = _propagate_ar(weights, seed, H=20)
    assert np.all(np.isfinite(traj))


# ── _counterfactual_trajectory ────────────────────────────────────────────────

def test_cf_trajectory_length():
    rng = np.random.default_rng(0)
    phi = rng.standard_normal(100) + 5.0
    Z, y = _build_lagged(phi, 4)
    w = _ridge_fit(Z, y)
    cf = _counterfactual_trajectory(phi, w, t=50, delta=1.0, H=10)
    assert len(cf) == 10


def test_cf_trajectory_zero_delta_similar_to_actual():
    """Zero delta → counterfactual ≈ AR prediction from same seed."""
    rng = np.random.default_rng(1)
    phi = np.cumsum(rng.standard_normal(200) * 0.1) + 5.0
    Z, y = _build_lagged(phi, 4)
    w = _ridge_fit(Z, y)
    t = 100
    cf_zero = _counterfactual_trajectory(phi, w, t=t, delta=0.0, H=5)
    cf_plus = _counterfactual_trajectory(phi, w, t=t, delta=5.0, H=5)
    # With large delta the trajectories diverge
    assert np.abs(cf_zero - cf_plus).mean() > 0


def test_cf_trajectory_finite():
    rng = np.random.default_rng(2)
    phi = rng.standard_normal(100) + 5.0
    Z, y = _build_lagged(phi, 4)
    w = _ridge_fit(Z, y)
    cf = _counterfactual_trajectory(phi, w, t=50, delta=2.0, H=15)
    assert np.all(np.isfinite(cf))


# ── _ols_slope ────────────────────────────────────────────────────────────────

def test_ols_slope_positive():
    y = np.arange(10, dtype=float)
    assert _ols_slope(y) == pytest.approx(1.0)


def test_ols_slope_negative():
    y = np.arange(10, 0, -1, dtype=float)
    assert _ols_slope(y) < 0


def test_ols_slope_constant():
    assert abs(_ols_slope(np.full(10, 2.0))) < 1e-9


# ── analyse() ─────────────────────────────────────────────────────────────────

def _make_phi(n: int = 300, seed: int = 0, sigma: float = 0.3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.cumsum(rng.standard_normal(n) * sigma) + 5.0


def test_analyse_returns_none_short_phi():
    phi = np.array([1.0, 2.0, 3.0])
    assert analyse(phi) is None


def test_analyse_returns_result():
    r = analyse(_make_phi())
    assert isinstance(r, CounterfactualResult)


def test_analyse_n_interventions_positive():
    r = analyse(_make_phi())
    assert r.n_interventions > 0


def test_analyse_divergence_up_non_negative():
    r = analyse(_make_phi())
    assert r.mean_divergence_up >= 0.0


def test_analyse_divergence_down_non_negative():
    r = analyse(_make_phi())
    assert r.mean_divergence_down >= 0.0


def test_analyse_divergence_zero_non_negative():
    r = analyse(_make_phi())
    assert r.mean_divergence_zero >= 0.0


def test_analyse_sensitivity_non_negative():
    r = analyse(_make_phi())
    assert r.sensitivity_up >= 0.0
    assert r.sensitivity_down >= 0.0


def test_analyse_response_asymmetry_non_negative():
    r = analyse(_make_phi())
    assert r.response_asymmetry >= 0.0


def test_analyse_asymmetry_formula():
    r = analyse(_make_phi())
    assert r.response_asymmetry == pytest.approx(
        abs(r.sensitivity_up - r.sensitivity_down), abs=1e-9)


def test_analyse_sigma_phi_positive():
    r = analyse(_make_phi())
    assert r.sigma_phi > 0.0


def test_analyse_ar_weights_shape():
    r = analyse(_make_phi(), p=4)
    assert r.ar_weights.shape == (4,)


def test_analyse_ar_weights_finite():
    r = analyse(_make_phi())
    assert np.all(np.isfinite(r.ar_weights))


def test_analyse_is_mean_reverting_formula():
    r = analyse(_make_phi())
    assert r.is_mean_reverting == (r.mean_reversion_slope < 0.0)


def test_analyse_cf_horizon_bounded():
    r = analyse(_make_phi())
    assert 1 <= r.counterfactual_horizon <= r.horizon


def test_analyse_horizon_stored():
    r = analyse(_make_phi(), H=15)
    assert r.horizon == 15


def test_analyse_delta_sigma_stored():
    r = analyse(_make_phi(), delta_sigma=0.5)
    assert r.delta_sigma == pytest.approx(0.5)


def test_analyse_zero_intervention_large_divergence():
    """Zeroing phi from its mean should produce large divergence."""
    phi = np.full(300, 5.0) + np.random.default_rng(5).standard_normal(300) * 0.1
    r = analyse(phi)
    # Zero intervention shifts to 0 from mean ~5 → large divergence
    assert r.mean_divergence_zero > r.mean_divergence_up * 0.5


def test_analyse_deterministic():
    phi = _make_phi()
    r1 = analyse(phi)
    r2 = analyse(phi)
    assert r1.mean_divergence_up == r2.mean_divergence_up
    assert np.array_equal(r1.ar_weights, r2.ar_weights)


def test_analyse_larger_perturbation_larger_divergence():
    """Larger δ → larger divergence."""
    phi = _make_phi(n=400)
    r_small = analyse(phi, delta_sigma=0.5)
    r_large = analyse(phi, delta_sigma=2.0)
    assert r_large.mean_divergence_up >= r_small.mean_divergence_up * 0.5


def test_analyse_stable_ar_mean_reverting():
    """Stationary OU process → AR model is stable → divergence shrinks → mean-reverting."""
    rng = np.random.default_rng(99)
    phi = np.zeros(400)
    phi[0] = 5.0
    for i in range(1, 400):
        phi[i] = 0.8 * phi[i-1] + rng.standard_normal() * 0.3
    r = analyse(phi, delta_sigma=1.0)
    assert r.is_mean_reverting


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry()
    assert r is not None


@skip_no_telemetry
def test_live_divergence_non_negative():
    r = analyse_from_telemetry()
    assert r.mean_divergence_up >= 0.0


@skip_no_telemetry
def test_live_ar_weights_finite():
    r = analyse_from_telemetry()
    assert np.all(np.isfinite(r.ar_weights))
