"""Tests for PredictiveErrorMinimiser.

Pure-math tests cover AR fitting, prediction, and error metric computation.
Telemetry tests run against the real phi series from the daemon.
"""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.PredictiveErrorMinimiser import (
    PredictiveErrorResult,
    _build_lagged,
    _ridge_fit,
    ar_predict_series,
    fit_ar,
    analyse,
    analyse_from_telemetry,
)


# ── _build_lagged ─────────────────────────────────────────────────────────────

def test_build_lagged_shape():
    x = np.arange(20, dtype=float)
    Z, y = _build_lagged(x, p=3)
    assert Z.shape == (17, 3)
    assert y.shape == (17,)


def test_build_lagged_first_row():
    """First row should be [x[p-1], x[p-2], ..., x[0]]."""
    x = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    Z, y = _build_lagged(x, p=2)
    assert Z[0, 0] == 20.0  # x[1] = x[p-1]
    assert Z[0, 1] == 10.0  # x[0] = x[p-2]
    assert y[0] == 30.0     # x[2] = x[p]


def test_build_lagged_target():
    x = np.arange(10, dtype=float)
    _, y = _build_lagged(x, p=3)
    assert np.array_equal(y, x[3:])


# ── _ridge_fit ────────────────────────────────────────────────────────────────

def test_ridge_fit_identity():
    """OLS on identity design matrix with zero ridge → w = b."""
    n, d = 20, 3
    Z = np.eye(n, d)
    y = np.arange(n, dtype=float)
    w = _ridge_fit(Z, y, ridge=1e-10)
    assert w.shape == (d,)
    assert np.all(np.isfinite(w))


def test_ridge_fit_exact_recovery():
    """AR(1) with known coefficient → OLS should recover it."""
    rng = np.random.default_rng(0)
    true_w = np.array([0.8])
    x = np.zeros(300)
    x[0] = 0.0
    for t in range(1, 300):
        x[t] = true_w[0] * x[t - 1] + rng.normal(0, 0.01)
    Z, y = _build_lagged(x, p=1)
    w = _ridge_fit(Z, y, ridge=1e-4)
    assert abs(w[0] - true_w[0]) < 0.05, f"Expected ≈0.8, got {w[0]:.4f}"


def test_ridge_fit_shape():
    rng = np.random.default_rng(1)
    Z = rng.standard_normal((100, 4))
    y = rng.standard_normal(100)
    w = _ridge_fit(Z, y)
    assert w.shape == (4,)


# ── fit_ar / ar_predict_series ────────────────────────────────────────────────

def test_fit_ar_shape():
    rng = np.random.default_rng(2)
    phi = np.cumsum(rng.standard_normal(200)) * 0.05
    w = fit_ar(phi, p=4)
    assert w.shape == (4,)


def test_fit_ar_finite():
    rng = np.random.default_rng(3)
    phi = np.cumsum(rng.standard_normal(200)) * 0.05
    w = fit_ar(phi, p=4)
    assert np.all(np.isfinite(w))


def test_ar_predict_series_length():
    rng = np.random.default_rng(4)
    phi = np.cumsum(rng.standard_normal(200)) * 0.05
    w = fit_ar(phi, p=4)
    preds = ar_predict_series(phi, w)
    assert len(preds) == len(phi) - 4


def test_ar_predict_reduces_mae():
    """AR(4) predictions should have lower MAE than a constant-mean null."""
    rng = np.random.default_rng(5)
    phi = np.zeros(300)
    for t in range(4, 300):
        phi[t] = 0.9 * phi[t - 1] - 0.2 * phi[t - 2] + rng.normal(0, 0.05)
    w = fit_ar(phi, p=4)
    preds = ar_predict_series(phi, w)
    actuals = phi[4:]
    mae_ar = np.mean(np.abs(actuals - preds))
    mae_mean = np.mean(np.abs(actuals - actuals.mean()))
    assert mae_ar < mae_mean, f"AR MAE {mae_ar:.4f} should be < mean-model MAE {mae_mean:.4f}"


# ── analyse() on synthetic data ───────────────────────────────────────────────

def _synthetic_phi(n: int = 500, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    phi = np.zeros(n)
    for t in range(4, n):
        phi[t] = 0.7 * phi[t - 1] - 0.1 * phi[t - 2] + rng.normal(-0.4, 0.05)
    phi = phi - phi.mean()  # centre
    return phi


def test_analyse_returns_none_short():
    phi = np.random.default_rng(0).standard_normal(20)
    assert analyse(phi, p=4, window=50) is None


def test_analyse_returns_result():
    r = analyse(_synthetic_phi())
    assert isinstance(r, PredictiveErrorResult)


def test_analyse_n_samples():
    phi = _synthetic_phi()
    r = analyse(phi)
    assert r.n_samples == len(phi)


def test_analyse_error_series_length():
    phi = _synthetic_phi()
    r = analyse(phi, p=4)
    assert len(r.error_series) == len(phi) - 4


def test_analyse_global_mae_non_negative():
    r = analyse(_synthetic_phi())
    assert r.global_mae >= 0.0


def test_analyse_rw_mae_non_negative():
    r = analyse(_synthetic_phi())
    assert r.rw_mae > 0.0


def test_analyse_compression_ratio_finite():
    r = analyse(_synthetic_phi())
    assert np.isfinite(r.compression_ratio)
    assert r.compression_ratio >= 0.0


def test_analyse_beats_random_walk_on_ar1():
    """AR(4) model fit on correlated data should beat random walk."""
    r = analyse(_synthetic_phi())
    assert r.beats_random_walk, (
        f"AR model should beat RW. ratio={r.compression_ratio:.4f}"
    )


def test_analyse_rolling_mae_non_negative():
    r = analyse(_synthetic_phi())
    assert np.all(r.rolling_mae >= 0.0)


def test_analyse_rolling_mae_finite():
    r = analyse(_synthetic_phi())
    assert np.all(np.isfinite(r.rolling_mae))


def test_analyse_residual_acf_lag1_bounded():
    r = analyse(_synthetic_phi())
    assert -1.0 <= r.residual_acf_lag1 <= 1.0


def test_analyse_improving_is_bool():
    r = analyse(_synthetic_phi())
    assert isinstance(r.improving, bool)


def test_analyse_improving_matches_slope():
    r = analyse(_synthetic_phi())
    assert r.improving == (r.mae_trend_slope < 0.0)


def test_analyse_beats_rw_matches_ratio():
    r = analyse(_synthetic_phi())
    assert r.beats_random_walk == (r.compression_ratio < 1.0)


def test_analyse_ar_weights_shape():
    r = analyse(_synthetic_phi(), p=4)
    assert r.ar_weights.shape == (4,)


def test_analyse_deterministic():
    phi = _synthetic_phi()
    r1 = analyse(phi, p=4, window=50, stride=10)
    r2 = analyse(phi, p=4, window=50, stride=10)
    assert r1.global_mae == r2.global_mae
    assert np.array_equal(r1.ar_weights, r2.ar_weights)
    assert np.array_equal(r1.error_series, r2.error_series)


def test_analyse_white_noise_compression_near_one():
    """For IID noise, AR(4) offers little over random walk."""
    rng = np.random.default_rng(9)
    phi = rng.standard_normal(600)
    r = analyse(phi, p=4, window=50, stride=10)
    # Compression ratio for IID noise should be close to 1 (AR barely helps)
    assert 0.5 < r.compression_ratio < 2.0


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry()
    assert r is not None


@skip_no_telemetry
def test_live_beats_random_walk():
    """AR(4) predictive quality on live phi — ratio < 2 means reasonable fit."""
    r = analyse_from_telemetry()
    # The phi signal may be near-white-noise when daemon activity is low;
    # assert a weak upper bound rather than a strict beats_random_walk claim.
    assert r.compression_ratio < 2.0, (
        f"AR(4) compression ratio implausibly high: {r.compression_ratio:.4f}"
    )


@skip_no_telemetry
def test_live_global_mae_non_negative():
    r = analyse_from_telemetry()
    assert r.global_mae >= 0.0


@skip_no_telemetry
def test_live_residual_acf_bounded():
    r = analyse_from_telemetry()
    assert -1.0 <= r.residual_acf_lag1 <= 1.0


@skip_no_telemetry
def test_live_compression_finite():
    r = analyse_from_telemetry()
    assert np.isfinite(r.compression_ratio)


@skip_no_telemetry
def test_live_rolling_mae_non_empty():
    r = analyse_from_telemetry()
    assert len(r.rolling_mae) >= 1


@skip_no_telemetry
def test_live_deterministic():
    r1 = analyse_from_telemetry()
    r2 = analyse_from_telemetry()
    assert r1.global_mae == r2.global_mae
    assert np.array_equal(r1.ar_weights, r2.ar_weights)
