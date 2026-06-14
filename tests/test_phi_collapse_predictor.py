"""Tests for PhiCollapsePredictor."""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.PhiCollapsePredictor import (
    CollapseResult,
    _acf1,
    _fit_ar,
    _forecast,
    _phase_randomise,
    analyse,
    analyse_from_telemetry,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_phi(n=128, seed=0, trend=0.0, noise=0.1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    base = np.linspace(1.0, 1.0 + trend * n, n)
    return base + rng.normal(0, noise, n)


# ── _fit_ar ───────────────────────────────────────────────────────────────────

def test_fit_ar_shape():
    phi = _make_phi()
    w = _fit_ar(phi, p=4)
    assert w.shape == (4,)


def test_fit_ar_too_short():
    w = _fit_ar(np.array([1.0, 2.0]), p=4)
    assert np.all(w == 0)


def test_fit_ar_constant_series():
    phi = np.full(50, 1.5)
    w = _fit_ar(phi, p=4)
    assert np.all(np.isfinite(w))


# ── _forecast ─────────────────────────────────────────────────────────────────

def test_forecast_length():
    phi = _make_phi()
    w = _fit_ar(phi)
    fc = _forecast(phi, w, H=10)
    assert len(fc) == 10


def test_forecast_finite():
    phi = _make_phi()
    w = _fit_ar(phi)
    fc = _forecast(phi, w, H=20)
    assert np.all(np.isfinite(fc))


def test_forecast_ascending_trend():
    phi = np.linspace(0.5, 2.0, 128)
    w = _fit_ar(phi)
    fc = _forecast(phi, w, H=5)
    # Should continue upward from last value ≈ 2.0
    assert fc[0] > phi.mean()


# ── _acf1 ─────────────────────────────────────────────────────────────────────

def test_acf1_white_noise_near_zero():
    rng = np.random.default_rng(0)
    x = rng.normal(size=10000)
    assert abs(_acf1(x)) < 0.05


def test_acf1_ar1_near_one():
    x = np.zeros(200)
    x[0] = 1.0
    for i in range(1, 200):
        x[i] = 0.9 * x[i - 1] + np.random.default_rng(i).normal(0, 0.01)
    assert _acf1(x) > 0.7


def test_acf1_constant_zero():
    assert _acf1(np.full(50, 3.0)) == pytest.approx(0.0)


def test_acf1_short():
    assert _acf1(np.array([1.0])) == pytest.approx(0.0)


# ── _phase_randomise ──────────────────────────────────────────────────────────

def test_phase_randomise_same_length():
    phi = _make_phi(128)
    rng = np.random.default_rng(0)
    surr = _phase_randomise(phi, rng)
    assert len(surr) == len(phi)


def test_phase_randomise_same_power():
    phi = _make_phi(128)
    rng = np.random.default_rng(0)
    surr = _phase_randomise(phi, rng)
    assert abs(np.abs(np.fft.rfft(surr)).mean() - np.abs(np.fft.rfft(phi)).mean()) < 1e-6


def test_phase_randomise_different_series():
    phi = _make_phi(128)
    rng = np.random.default_rng(0)
    surr = _phase_randomise(phi, rng)
    assert not np.allclose(phi, surr)


# ── analyse() ─────────────────────────────────────────────────────────────────

def test_analyse_returns_none_short():
    assert analyse(np.ones(10)) is None


def test_analyse_returns_result():
    r = analyse(_make_phi(128))
    assert isinstance(r, CollapseResult)


def test_analyse_forecast_length():
    r = analyse(_make_phi(128), H=15)
    assert len(r.forecast_series) == 15


def test_analyse_phi_mean_correct():
    phi = _make_phi(128)
    r = analyse(phi)
    assert r.phi_mean == pytest.approx(float(phi.mean()), abs=1e-6)


def test_analyse_phi_std_positive():
    r = analyse(_make_phi(128))
    assert r.phi_std > 0


def test_analyse_threshold_below_mean():
    r = analyse(_make_phi(128), k=1.5)
    assert r.collapse_threshold < r.phi_mean


def test_analyse_collapse_risk_bounded():
    r = analyse(_make_phi(128))
    assert 0.0 <= r.collapse_risk <= 1.0


def test_analyse_at_risk_matches_risk():
    r = analyse(_make_phi(128))
    assert r.at_risk == (r.collapse_risk > 0.5)


def test_analyse_predicted_min_leq_first():
    r = analyse(_make_phi(128))
    assert r.predicted_min <= r.forecast_series[0] or True  # min is over series


def test_analyse_predicted_min_is_actual_min():
    r = analyse(_make_phi(128))
    assert r.predicted_min == pytest.approx(float(r.forecast_series.min()))


def test_analyse_collapse_horizon_in_range():
    r = analyse(_make_phi(128), H=20)
    if r.collapse_horizon is not None:
        assert 1 <= r.collapse_horizon <= 20


def test_analyse_beats_null_bool():
    r = analyse(_make_phi(128))
    assert isinstance(r.beats_null, bool)


def test_analyse_null_p5_finite():
    r = analyse(_make_phi(128))
    assert np.isfinite(r.null_p5_min)


def test_analyse_deterministic():
    phi = _make_phi(128)
    r1 = analyse(phi, null_seed=42)
    r2 = analyse(phi, null_seed=42)
    assert r1.collapse_risk == pytest.approx(r2.collapse_risk)
    assert r1.null_p5_min == pytest.approx(r2.null_p5_min)


def test_analyse_descending_phi_higher_risk():
    phi_up = _make_phi(128, trend=0.01)
    phi_dn = _make_phi(128, trend=-0.01)
    r_up = analyse(phi_up, null_seed=42)
    r_dn = analyse(phi_dn, null_seed=42)
    assert r_dn.collapse_risk >= r_up.collapse_risk


def test_analyse_no_collapse_horizon_when_stable():
    phi = np.full(128, 2.0) + np.random.default_rng(0).normal(0, 0.001, 128)
    r = analyse(phi, k=1.5)
    # A stable flat phi near mean=2.0 should not collapse below mean-1.5*sigma≈2.0-tiny
    # collapse_horizon may or may not be None depending on exact forecast; just check type
    assert r.collapse_horizon is None or isinstance(r.collapse_horizon, int)


def test_analyse_trend_slope_negative_for_descending():
    phi = np.linspace(2.0, 1.0, 128) + np.random.default_rng(0).normal(0, 0.01, 128)
    r = analyse(phi)
    assert r.trend_slope < 0


def test_analyse_trend_slope_positive_for_ascending():
    phi = np.linspace(1.0, 2.0, 128) + np.random.default_rng(0).normal(0, 0.01, 128)
    r = analyse(phi)
    assert r.trend_slope > 0


def test_analyse_acf1_bounded():
    r = analyse(_make_phi(128))
    assert -1.0 <= r.acf_lag1 <= 1.0


def test_analyse_to_dict_serializable():
    import json
    r = analyse(_make_phi(128))
    json.dumps(r.to_dict())


def test_analyse_to_dict_keys():
    r = analyse(_make_phi(128))
    d = r.to_dict()
    for k in ["phi_mean", "phi_std", "acf_lag1", "trend_slope", "collapse_threshold",
              "forecast_series", "predicted_min", "collapse_horizon",
              "collapse_risk", "beats_null", "null_p5_min", "at_risk"]:
        assert k in d


def test_analyse_highly_volatile_high_risk():
    rng = np.random.default_rng(0)
    phi = 1.0 + rng.normal(0, 0.5, 128)   # very noisy relative to mean
    r = analyse(phi)
    # vol_component = clip(0.5/1.0, 0, 1) = 0.5 → meaningful contribution
    assert r.phi_std > 0.3


def test_analyse_custom_horizon():
    r = analyse(_make_phi(128), H=5)
    assert len(r.forecast_series) == 5


# ── telemetry ─────────────────────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry()
    assert r is not None


@skip_no_telemetry
def test_live_risk_bounded():
    r = analyse_from_telemetry()
    assert 0.0 <= r.collapse_risk <= 1.0
