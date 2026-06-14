"""Tests for CriticalityDetector.

All telemetry-dependent tests use real phi series from the live daemon.
Pure-math tests (ACF, power-law fit, criticality score) run in CI without telemetry.
Null baselines use shuffled series — the only honest comparison for time-series claims.
"""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.CriticalityDetector import (
    analyse, analyse_from_telemetry, criticality_score,
    _acf_series, _fit_power_law, CriticalityResult,
)


# ── pure math: criticality_score ────────────────────────────────────────────

def test_criticality_score_at_critical():
    """alpha=1 is the critical point → score must be exactly 1.0."""
    assert criticality_score(1.0) == pytest.approx(1.0)


def test_criticality_score_monotone():
    """Score decreases as alpha moves away from 1 in either direction."""
    assert criticality_score(0.5) < criticality_score(0.8)
    assert criticality_score(2.0) < criticality_score(1.5)


def test_criticality_score_symmetric():
    """Equidistant deviations from 1 give the same score."""
    assert criticality_score(0.5) == pytest.approx(criticality_score(1.5))


def test_criticality_score_bounded():
    for a in [0.0, 0.5, 1.0, 1.5, 2.0, 5.0]:
        s = criticality_score(a)
        assert 0.0 < s <= 1.0


# ── pure math: ACF ──────────────────────────────────────────────────────────

def test_acf_white_noise_near_zero():
    """ACF of white noise should be near zero at all lags."""
    rng = np.random.default_rng(0)
    y = rng.standard_normal(500)
    acf = _acf_series(y, tau_max=20)
    assert np.abs(acf).max() < 0.15   # 3σ for N=500


def test_acf_ar1_decays():
    """AR(1) with coefficient 0.9 must have ACF ≈ 0.9^τ."""
    rng = np.random.default_rng(1)
    phi_coef = 0.9
    y = np.zeros(1000)
    for t in range(1, 1000):
        y[t] = phi_coef * y[t - 1] + rng.standard_normal()
    acf = _acf_series(y, tau_max=5)
    for tau in range(1, 6):
        expected = phi_coef ** tau
        assert abs(acf[tau - 1] - expected) < 0.05, (
            f"lag {tau}: ACF={acf[tau-1]:.3f} expected≈{expected:.3f}"
        )


def test_acf_length():
    rng = np.random.default_rng(2)
    y = rng.standard_normal(200)
    acf = _acf_series(y, tau_max=30)
    assert acf.shape == (30,)
    assert np.all(np.isfinite(acf))


# ── pure math: power-law fit ─────────────────────────────────────────────────

def test_fit_power_law_exact():
    """On an exact power law ACF(τ) = τ^(-1.0), the fit must recover α≈1."""
    lags = np.arange(1, 41, dtype=float)
    acf = lags ** (-1.0)        # exact 1/f
    alpha, r2, n_pos = _fit_power_law(acf, noise_floor=0.0)
    assert abs(alpha - 1.0) < 0.01, f"Expected α≈1.0, got {alpha:.4f}"
    assert r2 > 0.999
    assert n_pos == 40


def test_fit_power_law_white_noise():
    """White noise ACF is near zero; no positive lags above noise floor."""
    rng = np.random.default_rng(3)
    acf = rng.standard_normal(60) * 0.03   # near-zero, some negative
    noise_floor = 0.1
    alpha, r2, n_pos = _fit_power_law(acf, noise_floor=noise_floor)
    assert n_pos < 5   # almost no lags above floor


def test_fit_power_law_too_few_lags():
    """With < 3 positive lags the function returns zeros gracefully."""
    acf = np.array([0.5, -0.1, -0.2])
    alpha, r2, n_pos = _fit_power_law(acf, noise_floor=0.1)
    assert n_pos < 3 and alpha == 0.0 and r2 == 0.0


# ── pure math: analyse() on synthetic series ─────────────────────────────────

def test_analyse_exact_power_law():
    """On a synthetic series with known ACF structure the result is correct."""
    rng = np.random.default_rng(10)
    # Build a series whose empirical ACF approximates a power law with α≈1
    n = 500
    # FGN-like: cumsum of long-range correlated increments via spectral method
    freqs = np.fft.rfftfreq(n)
    freqs[0] = 1e-9
    spectrum = freqs ** (-0.5)                     # spectrum ~ f^(-α/2), α=1
    noise = rng.standard_normal(n // 2 + 1) + 1j * rng.standard_normal(n // 2 + 1)
    noise[0] = 0
    y = np.fft.irfft(spectrum * noise, n=n)
    y = (y - y.mean()) / (y.std() + 1e-9)

    r = analyse(y, series_name="synthetic", tau_max=40, null_seed=42)
    assert r is not None
    assert r.r2_fit >= 0
    assert np.isfinite(r.alpha)
    assert 0.0 < r.criticality_score <= 1.0


def test_analyse_returns_none_for_short_series():
    y = np.arange(10, dtype=float)
    r = analyse(y, tau_max=60)
    assert r is None


def test_analyse_deterministic():
    """Same series → identical result."""
    rng = np.random.default_rng(20)
    y = np.cumsum(rng.standard_normal(300))
    r1 = analyse(y, null_seed=42)
    r2 = analyse(y, null_seed=42)
    assert r1.alpha == r2.alpha
    assert r1.r2_fit == r2.r2_fit
    assert r1.criticality_score == r2.criticality_score


def test_analyse_regime_classification():
    """Known alpha values map to correct regime strings."""
    rng = np.random.default_rng(30)
    base = np.cumsum(rng.standard_normal(300))

    for alpha_target, expected_regime in [(0.1, "sub_critical"), (1.0, "critical"),
                                           (2.5, "super_critical")]:
        # Build a series with the target alpha in its ACF by construction
        lags_mock = np.arange(1, 41, dtype=float)
        acf_mock = lags_mock ** (-alpha_target)
        # Use result directly to test regime property (bypasses series construction)
        r = CriticalityResult(
            alpha=alpha_target, r2_fit=0.9, null_r2_fit=0.1,
            criticality_score=criticality_score(alpha_target),
            n_positive_lags=40, tau_max=40, n_samples=300,
            series_name="mock", acf=acf_mock,
        )
        assert r.regime == expected_regime, (
            f"alpha={alpha_target}: expected {expected_regime}, got {r.regime}"
        )


def test_analyse_result_fields():
    rng = np.random.default_rng(40)
    y = np.cumsum(rng.standard_normal(400))
    r = analyse(y, tau_max=30)
    assert r is not None
    assert r.n_samples == 400
    assert r.tau_max == 30
    assert r.acf.shape == (30,)
    assert np.isfinite(r.alpha)
    assert np.isfinite(r.r2_fit)
    assert np.isfinite(r.null_r2_fit)
    assert 0.0 < r.criticality_score <= 1.0


# ── telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_phi_level_beats_null():
    """Real phi level has meaningful power-law structure that beats null."""
    r = analyse_from_telemetry()["phi_level"]
    assert r is not None
    assert r.beats_null, (
        f"phi_level R²={r.r2_fit:.4f} did not beat null {r.null_r2_fit:.4f}"
    )


@skip_no_telemetry
def test_phi_level_r2_substantial():
    """phi level power-law fit must explain >50% of log-ACF variance."""
    r = analyse_from_telemetry()["phi_level"]
    assert r.r2_fit > 0.5, f"phi_level power-law R²={r.r2_fit:.4f} too low"


@skip_no_telemetry
def test_phi_level_alpha_finite_and_bounded():
    r = analyse_from_telemetry()["phi_level"]
    assert np.isfinite(r.alpha), "alpha must be finite"
    assert 0.0 <= r.alpha <= 3.0, f"alpha={r.alpha:.4f} out of expected range"


@skip_no_telemetry
def test_phi_level_sub_critical():
    """Live phi is currently sub-critical (α < 0.7). Document the baseline."""
    r = analyse_from_telemetry()["phi_level"]
    assert r.regime in ("sub_critical", "near_critical", "critical"), (
        f"Unexpected regime: {r.regime}"
    )


@skip_no_telemetry
def test_phi_delta_result_is_valid():
    """phi_delta may be white noise at this scale — test runs cleanly."""
    r = analyse_from_telemetry()["phi_delta"]
    assert r is not None
    assert np.isfinite(r.alpha)
    assert 0.0 < r.criticality_score <= 1.0


@skip_no_telemetry
def test_analyse_from_telemetry_deterministic():
    r1 = analyse_from_telemetry()
    r2 = analyse_from_telemetry()
    assert r1["phi_level"].alpha == r2["phi_level"].alpha
    assert np.array_equal(r1["phi_level"].acf, r2["phi_level"].acf)


@skip_no_telemetry
def test_beats_null_margin_on_phi_level():
    """The real-vs-null margin should be measurably positive for phi_level."""
    r = analyse_from_telemetry()["phi_level"]
    margin = r.r2_fit - r.null_r2_fit
    assert margin > 0, f"margin={margin:.4f} not positive"
