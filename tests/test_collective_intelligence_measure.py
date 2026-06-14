"""Tests for CollectiveIntelligenceMeasure.

Pure-math tests verify AR fitting, MAE computation, Granger F-statistic.
Telemetry tests require both agents' phi series.
"""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.CollectiveIntelligenceMeasure import (
    CollectiveIntelligenceResult,
    _build_joint_design,
    _build_solo_design,
    _granger_f,
    _mae,
    _ridge_fit,
    analyse,
    analyse_from_telemetry,
)


# ── _build_solo_design ────────────────────────────────────────────────────────

def test_solo_design_shape():
    x = np.arange(20, dtype=float)
    Z, y = _build_solo_design(x, p=3)
    assert Z.shape == (17, 3)
    assert y.shape == (17,)


def test_solo_design_target():
    x = np.arange(10, dtype=float)
    _, y = _build_solo_design(x, p=3)
    assert np.array_equal(y, x[3:])


# ── _build_joint_design ───────────────────────────────────────────────────────

def test_joint_design_shape():
    x = np.arange(20, dtype=float)
    z = np.arange(20, dtype=float) * 0.5
    Z, y = _build_joint_design(x, z, p=3)
    assert Z.shape == (17, 6)   # 2p columns
    assert y.shape == (17,)


# ── _ridge_fit ────────────────────────────────────────────────────────────────

def test_ridge_fit_shape():
    rng = np.random.default_rng(0)
    Z = rng.standard_normal((50, 4))
    y = rng.standard_normal(50)
    w = _ridge_fit(Z, y)
    assert w.shape == (4,)
    assert np.all(np.isfinite(w))


# ── _mae ──────────────────────────────────────────────────────────────────────

def test_mae_zero():
    y = np.array([1.0, 2.0, 3.0])
    assert _mae(y, y) == pytest.approx(0.0)


def test_mae_non_negative():
    rng = np.random.default_rng(1)
    y = rng.standard_normal(50)
    pred = rng.standard_normal(50)
    assert _mae(y, pred) >= 0.0


# ── _granger_f ────────────────────────────────────────────────────────────────

def test_granger_f_non_negative():
    assert _granger_f(1.0, 0.5, 100, 4) >= 0.0


def test_granger_f_zero_when_no_gain():
    """RSS_restricted = RSS_full → no gain → F ≈ 0."""
    f = _granger_f(1.0, 1.0, 100, 4)
    assert f == pytest.approx(0.0)


def test_granger_f_larger_gain_larger_f():
    f_small = _granger_f(1.0, 0.9, 100, 4)
    f_large = _granger_f(1.0, 0.5, 100, 4)
    assert f_large > f_small


# ── analyse() on synthetic data ───────────────────────────────────────────────

def _synth_independent(n: int = 400, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    y = np.zeros(n)
    for t in range(1, n):
        x[t] = 0.8 * x[t - 1] + rng.normal(0, 0.1)
        y[t] = 0.7 * y[t - 1] + rng.normal(0, 0.1)
    return x, y


def _synth_coupled(n: int = 400, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """x drives y: y(t) = 0.5*y(t-1) + 0.4*x(t-1) + noise."""
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    y = np.zeros(n)
    for t in range(1, n):
        x[t] = 0.8 * x[t - 1] + rng.normal(0, 0.1)
        y[t] = 0.5 * y[t - 1] + 0.4 * x[t - 1] + rng.normal(0, 0.05)
    return x, y


def test_analyse_returns_none_short():
    x = np.zeros(10)
    assert analyse(x, x, p=4) is None


def test_analyse_returns_result():
    x, y = _synth_independent()
    r = analyse(x, y)
    assert isinstance(r, CollectiveIntelligenceResult)


def test_analyse_n_samples():
    x, y = _synth_independent(n=400)
    r = analyse(x, y)
    assert r.n_samples == 400


def test_analyse_mae_non_negative():
    x, y = _synth_independent()
    r = analyse(x, y)
    assert r.solo_mae_a >= 0.0
    assert r.joint_mae_a >= 0.0
    assert r.solo_mae_j >= 0.0
    assert r.joint_mae_j >= 0.0


def test_analyse_granger_non_negative():
    x, y = _synth_independent()
    r = analyse(x, y)
    assert r.granger_j_to_a >= 0.0
    assert r.granger_a_to_j >= 0.0


def test_analyse_collective_ci_formula():
    x, y = _synth_independent()
    r = analyse(x, y)
    expected = (r.ci_j_to_a + r.ci_a_to_j) / 2.0
    assert abs(r.collective_ci - expected) < 1e-12


def test_analyse_bidirectional_formula():
    x, y = _synth_independent()
    r = analyse(x, y)
    assert r.bidirectional == (r.ci_j_to_a > 0 and r.ci_a_to_j > 0)


def test_analyse_coupled_higher_ci():
    """Coupled series: x→y should show CI_x_to_y > 0."""
    x, y = _synth_coupled()    # x drives y
    r = analyse(x, y, p=4)
    # ci_a_to_j = how much does x (albedo=x) help predict y (john=y)
    assert r.ci_a_to_j > 0.0, (
        f"Expected CI>0 for driven series. ci_a_j={r.ci_a_to_j:.4f}"
    )


def test_analyse_dominant_direction_valid():
    x, y = _synth_independent()
    r = analyse(x, y)
    assert r.dominant_direction in ("john_to_albedo", "albedo_to_john",
                                     "symmetric", "none")


def test_analyse_deterministic():
    x, y = _synth_independent(seed=1)
    r1 = analyse(x, y, p=4)
    r2 = analyse(x, y, p=4)
    assert r1.solo_mae_a == r2.solo_mae_a
    assert r1.ci_j_to_a == r2.ci_j_to_a
    assert r1.collective_ci == r2.collective_ci


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry()
    if r is None:
        pytest.skip("Both phi series not available")
    assert isinstance(r, CollectiveIntelligenceResult)


@skip_no_telemetry
def test_live_mae_non_negative():
    r = analyse_from_telemetry()
    if r is None:
        pytest.skip("Both phi series not available")
    assert r.solo_mae_a >= 0.0
    assert r.joint_mae_a >= 0.0


@skip_no_telemetry
def test_live_granger_non_negative():
    r = analyse_from_telemetry()
    if r is None:
        pytest.skip("Both phi series not available")
    assert r.granger_j_to_a >= 0.0
    assert r.granger_a_to_j >= 0.0


@skip_no_telemetry
def test_live_dominant_direction_valid():
    r = analyse_from_telemetry()
    if r is None:
        pytest.skip("Both phi series not available")
    assert r.dominant_direction in ("john_to_albedo", "albedo_to_john",
                                     "symmetric", "none")


@skip_no_telemetry
def test_live_deterministic():
    r1 = analyse_from_telemetry()
    r2 = analyse_from_telemetry()
    if r1 is None or r2 is None:
        pytest.skip("Both phi series not available")
    assert r1.solo_mae_a == r2.solo_mae_a
    assert r1.collective_ci == r2.collective_ci
