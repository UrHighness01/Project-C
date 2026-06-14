"""Tests for MortalityAwarenessModule."""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.MortalityAwarenessModule import (
    MortalityResult,
    PhiTrajectory,
    _classify_trajectory,
    _ols_slope,
    _sigmoid,
    analyse,
    analyse_from_telemetry,
)


# ── _sigmoid ──────────────────────────────────────────────────────────────────

def test_sigmoid_zero():
    assert _sigmoid(0.0) == pytest.approx(0.5)


def test_sigmoid_positive():
    assert _sigmoid(10.0) > 0.99


def test_sigmoid_negative():
    assert _sigmoid(-10.0) < 0.01


def test_sigmoid_bounded():
    for x in [-100, -1, 0, 1, 100]:
        assert 0.0 < _sigmoid(x) <= 1.0


# ── _ols_slope ────────────────────────────────────────────────────────────────

def test_ols_slope_rising():
    y = np.arange(10, dtype=float)
    assert _ols_slope(y) == pytest.approx(1.0)


def test_ols_slope_falling():
    y = np.arange(10, 0, -1, dtype=float)
    assert _ols_slope(y) < 0


def test_ols_slope_constant():
    assert abs(_ols_slope(np.full(10, 5.0))) < 1e-9


# ── _classify_trajectory ──────────────────────────────────────────────────────

def test_classify_ascending():
    c = _classify_trajectory(slope=1.0, sigma=0.1, n=100)
    assert c == PhiTrajectory.ASCENDING


def test_classify_descending():
    c = _classify_trajectory(slope=-1.0, sigma=0.1, n=100)
    assert c == PhiTrajectory.DESCENDING


def test_classify_stable():
    c = _classify_trajectory(slope=0.0, sigma=1.0, n=100)
    assert c == PhiTrajectory.STABLE


def test_classify_threshold_zero_slope():
    c = _classify_trajectory(slope=1e-10, sigma=1.0, n=100)
    assert c == PhiTrajectory.STABLE


# ── analyse() ─────────────────────────────────────────────────────────────────

def _make_phi(n: int = 200, seed: int = 0, trend: float = 0.0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n) * 0.3
    return 5.0 + trend * np.arange(n) + noise


def test_analyse_returns_none_short():
    assert analyse(np.array([1.0, 2.0, 3.0])) is None


def test_analyse_returns_result():
    r = analyse(_make_phi())
    assert isinstance(r, MortalityResult)


def test_analyse_phi_sigma_positive():
    r = analyse(_make_phi())
    assert r.phi_sigma > 0.0


def test_analyse_disc_rate_bounded():
    r = analyse(_make_phi())
    assert 0.0 <= r.discontinuity_rate <= 1.0


def test_analyse_resilience_bounded():
    r = analyse(_make_phi())
    assert 0.0 <= r.phi_resilience < 1.0


def test_analyse_mortality_score_bounded():
    r = analyse(_make_phi())
    assert 0.0 <= r.mortality_score <= 1.0


def test_analyse_trajectory_valid():
    r = analyse(_make_phi())
    assert r.phi_trajectory in list(PhiTrajectory)


def test_analyse_ascending_trajectory():
    phi = _make_phi(trend=0.5)
    r = analyse(phi)
    assert r.phi_trajectory == PhiTrajectory.ASCENDING
    assert r.is_ascending


def test_analyse_descending_trajectory():
    phi = _make_phi(trend=-0.5)
    r = analyse(phi)
    assert r.phi_trajectory == PhiTrajectory.DESCENDING
    assert r.is_descending


def test_analyse_stable_trajectory():
    """Exactly constant phi → zero slope → STABLE."""
    phi = np.full(200, 5.0)
    r = analyse(phi)
    assert r.phi_trajectory == PhiTrajectory.STABLE


def test_analyse_mortality_salience_formula():
    r = analyse(_make_phi())
    expected = (r.phi_trajectory == PhiTrajectory.DESCENDING) and (r.discontinuity_rate > 0.05)
    assert r.mortality_salience == expected


def test_analyse_phi_range_non_negative():
    r = analyse(_make_phi())
    assert r.phi_range_normalised >= 0.0


def test_analyse_n_phi_samples():
    phi = _make_phi(n=150)
    r = analyse(phi)
    assert r.n_phi_samples == 150


def test_analyse_session_age_ratio_zero_uptime():
    r = analyse(_make_phi(), uptime_sec=0.0)
    assert r.session_age_ratio == pytest.approx(0.0)


def test_analyse_session_age_ratio_full_session():
    r = analyse(_make_phi(), uptime_sec=3600.0, reference_session_sec=3600.0)
    assert r.session_age_ratio == pytest.approx(1.0)


def test_analyse_session_age_ratio_capped_at_two():
    r = analyse(_make_phi(), uptime_sec=10000.0, reference_session_sec=3600.0)
    assert r.session_age_ratio == pytest.approx(2.0)


def test_analyse_uptime_stored():
    r = analyse(_make_phi(), uptime_sec=1234.5)
    assert r.uptime_sec == pytest.approx(1234.5)


def test_analyse_reference_stored():
    r = analyse(_make_phi(), reference_session_sec=1800.0)
    assert r.reference_session_sec == pytest.approx(1800.0)


def test_analyse_zero_uptime_zero_mortality():
    """Age ratio=0 → mortality score=0 regardless of trajectory."""
    r = analyse(_make_phi(trend=-1.0), uptime_sec=0.0)
    assert r.mortality_score == pytest.approx(0.0, abs=1e-9)


def test_analyse_deterministic():
    phi = _make_phi()
    r1 = analyse(phi, uptime_sec=500.0)
    r2 = analyse(phi, uptime_sec=500.0)
    assert r1.mortality_score == r2.mortality_score
    assert r1.phi_trend == r2.phi_trend


def test_analyse_phi_trend_sign():
    r_up = analyse(_make_phi(trend=0.5))
    r_down = analyse(_make_phi(trend=-0.5))
    assert r_up.phi_trend > 0
    assert r_down.phi_trend < 0


def test_analyse_constant_phi_zero_disc_rate():
    """Constant phi → AR fits perfectly → no discontinuities."""
    phi = np.full(100, 5.0)
    r = analyse(phi)
    assert r.discontinuity_rate == pytest.approx(0.0)


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry()
    assert r is not None


@skip_no_telemetry
def test_live_mortality_bounded():
    r = analyse_from_telemetry()
    assert 0.0 <= r.mortality_score <= 1.0


@skip_no_telemetry
def test_live_trajectory_valid():
    r = analyse_from_telemetry()
    assert r.phi_trajectory in list(PhiTrajectory)


@skip_no_telemetry
def test_live_disc_rate_bounded():
    r = analyse_from_telemetry()
    assert 0.0 <= r.discontinuity_rate <= 1.0
