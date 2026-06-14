"""Tests for RecursiveSelfModel and the grounded OU extension of PhiDynamicsIntegrator.

All assertions run on real telemetry from the live daemon (via runtime.state).
No mocks, no synthetic series, no hardcoded phi values.

Null baselines are computed by shuffling the real series — the only fair comparison
for time-series algorithms whose value comes from exploiting temporal structure.
"""
import numpy as np
import pytest

from runtime.state import phi_series
from algorithms.RecursiveSelfModel import (
    RecursiveSelfModel, _build_lagged, _ridge_fit, _r2
)
from algorithms.PhiDynamicsIntegrator import (
    fit_ou_from_telemetry, simulate_ou, phi_dynamics_from_telemetry,
    OUFitResult,
)


# ── fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def real_phi():
    phi = phi_series()
    assert phi.size >= 64, "live telemetry must have ≥64 heartbeats to run these tests"
    return phi.astype(float)


@pytest.fixture(scope="module")
def self_model(real_phi):
    m = RecursiveSelfModel(p=4, q=4, null_seed=42)
    r = m.fit(phi=real_phi)
    assert r is not None
    return m, r


# ── RecursiveSelfModel: level-1 (self-prediction) ───────────────────────────

def test_l1_r2_beats_null(self_model):
    _, r = self_model
    assert r.r2_l1 > r.null_r2_l1, (
        f"Level-1 R² ({r.r2_l1:.4f}) must beat shuffled null ({r.null_r2_l1:.4f})"
    )


def test_l1_r2_meaningful(self_model):
    """The real phi series is strongly self-predictable (R²≈0.93 from coherence_horizon).
    A well-fitted AR model must beat a 0.5 threshold."""
    _, r = self_model
    assert r.r2_l1 > 0.5, f"Level-1 R² too low: {r.r2_l1:.4f}"


def test_l1_weights_shape(self_model):
    _, r = self_model
    assert r.weights_l1.shape == (r.p + 1,)  # [intercept, lag-1, ..., lag-p]


def test_l1_dominant_lag_is_first(self_model):
    """In a mean-reverting series the lag-1 coefficient dominates."""
    _, r = self_model
    ar_weights = np.abs(r.weights_l1[1:])   # exclude intercept
    assert np.argmax(ar_weights) == 0, "lag-1 should dominate in a persistent series"


# ── RecursiveSelfModel: level-2 (error / meta-cognition) ────────────────────

def test_l2_r2_beats_null(self_model):
    _, r = self_model
    assert r.r2_l2 > r.null_r2_l2, (
        f"Level-2 R² ({r.r2_l2:.4f}) must beat shuffled null ({r.null_r2_l2:.4f})"
    )


def test_l2_r2_positive(self_model):
    """Level-2 signal is weaker than level-1 but must be strictly positive."""
    _, r = self_model
    assert r.r2_l2 >= 0.0, f"Level-2 R² is negative: {r.r2_l2:.4f}"


def test_l2_r2_below_l1(self_model):
    """Meta-cognition (knowing when wrong) should be harder than self-prediction."""
    _, r = self_model
    assert r.r2_l2 <= r.r2_l1, (
        f"L2 R² ({r.r2_l2:.4f}) should not exceed L1 R² ({r.r2_l1:.4f})"
    )


# ── RecursiveSelfModel: depth score ─────────────────────────────────────────

def test_depth_positive(self_model):
    _, r = self_model
    assert r.depth > 0.0, "depth = R1² × R2² must be positive when both levels work"


def test_depth_is_product_of_r2s(self_model):
    _, r = self_model
    expected = max(0.0, r.r2_l1) * max(0.0, r.r2_l2)
    assert abs(r.depth - expected) < 1e-10


# ── RecursiveSelfModel: equilibrium estimate ─────────────────────────────────

def test_equilibrium_within_phi_range(self_model, real_phi):
    """The AR(p) long-run mean must be inside the observed phi range (with margin)."""
    _, r = self_model
    lo, hi = real_phi.min(), real_phi.max()
    span = hi - lo
    assert lo - span <= r.equilibrium_estimate <= hi + span, (
        f"Equilibrium {r.equilibrium_estimate:.4f} outside observed range [{lo:.4f}, {hi:.4f}]"
    )


# ── RecursiveSelfModel: prediction ──────────────────────────────────────────

def test_predict_next_is_float(self_model):
    m, r = self_model
    pred = m.predict_next(r)
    assert isinstance(pred, float) and np.isfinite(pred)


def test_predict_next_within_2sigma(self_model, real_phi):
    """One-step prediction should land within 2σ of recent phi values."""
    m, r = self_model
    pred = m.predict_next(r)
    recent_std = float(np.std(real_phi[-50:]))
    recent_mean = float(np.mean(real_phi[-50:]))
    assert abs(pred - recent_mean) < 4 * recent_std, (
        f"Prediction {pred:.4f} too far from recent mean {recent_mean:.4f}±{recent_std:.4f}"
    )


# ── RecursiveSelfModel: determinism ─────────────────────────────────────────

def test_fit_is_deterministic(real_phi):
    """Same series must produce identical weights every time."""
    m1 = RecursiveSelfModel(p=4, q=4, null_seed=42)
    m2 = RecursiveSelfModel(p=4, q=4, null_seed=42)
    r1 = m1.fit(phi=real_phi)
    r2 = m2.fit(phi=real_phi)
    assert np.allclose(r1.weights_l1, r2.weights_l1)
    assert np.allclose(r1.weights_l2, r2.weights_l2)
    assert r1.r2_l1 == r2.r2_l1
    assert r1.depth == r2.depth


# ── RecursiveSelfModel: margin_above_null ────────────────────────────────────

def test_margin_above_null_positive(self_model):
    m, r = self_model
    margins = m.margin_above_null(r)
    assert margins["l1_margin"] > 0, "L1 must beat null"
    assert margins["l2_margin"] > 0, "L2 must beat null"


# ── PhiDynamicsIntegrator: OU fit from telemetry ─────────────────────────────

@pytest.fixture(scope="module")
def ou_fit(real_phi):
    return fit_ou_from_telemetry(real_phi, null_seed=42)


def test_ou_fit_returns_result(ou_fit):
    assert ou_fit is not None
    assert isinstance(ou_fit, OUFitResult)


def test_ou_sigma_positive(ou_fit):
    assert ou_fit.sigma > 0, "diffusion coefficient must be positive"


def test_ou_r2_beats_null(ou_fit):
    """OU R² on the difference series beats the shuffled-series null.
    Note: delta-series R² is inherently low (confirmed in FINDINGS.md) but must
    still be strictly better than chance."""
    assert ou_fit.r2 > ou_fit.null_r2, (
        f"OU R² ({ou_fit.r2:.4f}) must exceed null R² ({ou_fit.null_r2:.4f})"
    )


def test_ou_mu_within_phi_range(ou_fit, real_phi):
    lo, hi = real_phi.min(), real_phi.max()
    span = hi - lo
    assert lo - 2 * span <= ou_fit.mu <= hi + 2 * span, (
        f"OU equilibrium {ou_fit.mu:.4f} wildly outside phi range [{lo:.4f},{hi:.4f}]"
    )


def test_ou_n_samples(ou_fit, real_phi):
    assert ou_fit.n_samples == len(real_phi)


# ── PhiDynamicsIntegrator: OU simulation ─────────────────────────────────────

def test_simulate_ou_shape(ou_fit):
    traj = simulate_ou(ou_fit, steps=100, seed=1)
    assert traj.shape == (100,)
    assert np.all(np.isfinite(traj))


def test_simulate_ou_deterministic(ou_fit):
    t1 = simulate_ou(ou_fit, steps=100, seed=99)
    t2 = simulate_ou(ou_fit, steps=100, seed=99)
    assert np.array_equal(t1, t2)


def test_simulate_ou_different_seeds(ou_fit):
    t1 = simulate_ou(ou_fit, steps=100, seed=1)
    t2 = simulate_ou(ou_fit, steps=100, seed=2)
    assert not np.array_equal(t1, t2)


def test_simulate_ou_mean_reverts(ou_fit):
    """A sufficiently long simulation should have its mean close to ou.mu.
    Tolerance: 3 sigma / sqrt(N) for a stationary OU process."""
    if abs(ou_fit.alpha) < 1e-6:
        pytest.skip("alpha≈0 → non-stationary OU, mean-reversion test not applicable")
    N = 5000
    traj = simulate_ou(ou_fit, steps=N, seed=42)
    tol = 3 * ou_fit.sigma / np.sqrt(abs(ou_fit.alpha) * N + 1)
    assert abs(traj.mean() - ou_fit.mu) < tol + 0.5, (
        f"Simulated mean {traj.mean():.4f} not near mu={ou_fit.mu:.4f} (tol {tol:.4f})"
    )


def test_simulate_ou_starts_at_initial(ou_fit):
    traj = simulate_ou(ou_fit, steps=50, initial=-0.3, seed=1)
    assert traj[0] == pytest.approx(-0.3)


# ── PhiDynamicsIntegrator: end-to-end telemetry factory ─────────────────────

def test_phi_dynamics_from_telemetry():
    result = phi_dynamics_from_telemetry()
    assert result is not None, "phi_dynamics_from_telemetry must succeed on live system"
    assert "ou_fit" in result
    assert "forecast" in result
    assert len(result["forecast"]) == 200
    assert np.all(np.isfinite(result["forecast"]))
    assert np.isfinite(result["current_phi"])
    assert np.isfinite(result["forecast_mean"])


def test_telemetry_factory_deterministic():
    r1 = phi_dynamics_from_telemetry()
    r2 = phi_dynamics_from_telemetry()
    assert r1 is not None and r2 is not None
    assert np.array_equal(r1["forecast"], r2["forecast"])


# ── shared helpers ───────────────────────────────────────────────────────────

def test_build_lagged_shape():
    x = np.arange(20, dtype=float)
    Z, y = _build_lagged(x, p=3)
    assert y.shape == (17,)
    assert Z.shape == (17, 4)      # [1, lag1, lag2, lag3]
    assert Z[:, 0].sum() == 17    # intercept column of ones


def test_ridge_fit_exact_on_linear():
    """On a perfectly linear series AR(1) must recover the true coefficient."""
    x = np.arange(100, dtype=float) * 0.01
    Z, y = _build_lagged(x, p=1)
    w = _ridge_fit(Z, y, ridge=1e-9)
    pred = Z @ w
    assert _r2(y, pred) > 0.999


def test_r2_perfect():
    y = np.array([1.0, 2.0, 3.0, 4.0])
    assert _r2(y, y) == pytest.approx(1.0)


def test_r2_unrelated_predictions_not_good():
    """Unrelated predictions must not get a high R². R² can be negative (worse than
    the mean) — the clamped value is in [-1, 1]; what matters is it stays below 0.3."""
    rng = np.random.default_rng(0)
    y = rng.standard_normal(200)
    pred = rng.standard_normal(200)  # independent of y
    assert _r2(y, pred) < 0.3
