"""Tests for SymbiosisPhiMeasure.

Pure-math tests verify correlation, cross-correlation, and mutual information
on synthetic series. Telemetry tests require both agents to be running.
"""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.SymbiosisPhiMeasure import (
    SymbiosisResult,
    _cross_correlation,
    _mutual_info_bins,
    _normalise,
    _pearson,
    analyse,
    analyse_from_telemetry,
)


# ── _pearson ──────────────────────────────────────────────────────────────────

def test_pearson_identical():
    x = np.arange(50, dtype=float)
    assert _pearson(x, x) == pytest.approx(1.0)


def test_pearson_anti():
    x = np.arange(50, dtype=float)
    assert _pearson(x, -x) == pytest.approx(-1.0)


def test_pearson_zero_std():
    x = np.ones(20)
    y = np.arange(20, dtype=float)
    assert _pearson(x, y) == pytest.approx(0.0)


def test_pearson_bounded():
    rng = np.random.default_rng(0)
    x, y = rng.standard_normal(100), rng.standard_normal(100)
    assert -1.0 <= _pearson(x, y) <= 1.0


# ── _normalise ────────────────────────────────────────────────────────────────

def test_normalise_mean_zero():
    x = np.arange(50, dtype=float)
    assert abs(_normalise(x).mean()) < 1e-10


def test_normalise_std_one():
    x = np.arange(50, dtype=float)
    assert abs(_normalise(x).std() - 1.0) < 0.01


def test_normalise_constant():
    """Constant series → all zeros after normalisation."""
    x = np.full(20, 3.5)
    assert np.all(np.abs(_normalise(x)) < 1e-6)


# ── _cross_correlation ────────────────────────────────────────────────────────

def test_cross_correlation_self_peaks_at_zero():
    """Cross-correlation of a series with itself → peak at lag 0."""
    rng = np.random.default_rng(1)
    x = np.cumsum(rng.standard_normal(200)) * 0.05
    _, lag, _ = _cross_correlation(x, x, tau_max=10)
    assert lag == 0


def test_cross_correlation_known_lag():
    """Series y = x delayed by 3 → peak lag = +3."""
    rng = np.random.default_rng(2)
    x = np.cumsum(rng.standard_normal(300)) * 0.05
    delay = 3
    y = np.roll(x, delay)
    y[:delay] = x[:delay]        # no wrap
    _, lag, _ = _cross_correlation(x, y, tau_max=10)
    assert lag == delay, f"Expected lag={delay}, got {lag}"


def test_cross_correlation_peak_cc_positive():
    rng = np.random.default_rng(3)
    x = np.cumsum(rng.standard_normal(200)) * 0.05
    _, _, peak = _cross_correlation(x, x, tau_max=10)
    assert peak > 0.0


def test_cross_correlation_cc_bounded():
    rng = np.random.default_rng(4)
    x, y = rng.standard_normal(200), rng.standard_normal(200)
    cc, _, _ = _cross_correlation(x, y, tau_max=10)
    assert np.all(np.abs(cc) <= 1.1)   # normalised, may slightly exceed 1 due to edge effects


# ── _mutual_info_bins ─────────────────────────────────────────────────────────

def test_mi_identical_series():
    """I(X; X) should be positive (and equal to H(X))."""
    rng = np.random.default_rng(5)
    x = rng.standard_normal(200)
    mi = _mutual_info_bins(x, x, bins=16)
    assert mi > 0.0


def test_mi_independent_series_near_zero():
    """I(X; Y) for independent X, Y should be near 0."""
    rng = np.random.default_rng(6)
    x = rng.standard_normal(500)
    y = rng.standard_normal(500)
    mi = _mutual_info_bins(x, y, bins=16)
    # For 500 samples and 16 bins, chance MI is small
    assert mi < 0.5, f"MI for independent series too high: {mi:.4f}"


def test_mi_non_negative():
    rng = np.random.default_rng(7)
    x, y = rng.standard_normal(200), rng.standard_normal(200)
    assert _mutual_info_bins(x, y) >= 0.0


def test_mi_correlated_gt_independent():
    """Correlated series should have higher MI than independent."""
    rng = np.random.default_rng(8)
    x = rng.standard_normal(400)
    y_corr = x + rng.standard_normal(400) * 0.1
    y_indep = rng.standard_normal(400)
    mi_corr = _mutual_info_bins(x, y_corr)
    mi_indep = _mutual_info_bins(x, y_indep)
    assert mi_corr > mi_indep, f"Correlated MI {mi_corr:.4f} should exceed independent {mi_indep:.4f}"


# ── analyse() on synthetic series ────────────────────────────────────────────

def _synth_pair(n: int = 400, lag: int = 0, coupling: float = 0.5,
                seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Generate a pair of coupled phi series."""
    rng = np.random.default_rng(seed)
    x = np.cumsum(rng.standard_normal(n)) * 0.05 - 0.4
    noise = rng.standard_normal(n) * 0.1
    if lag == 0:
        y = coupling * x + (1 - coupling) * noise
    else:
        y = coupling * np.roll(x, lag) + (1 - coupling) * noise
        y[:abs(lag)] = noise[:abs(lag)]
    return x, y


def test_analyse_returns_none_short():
    x = np.zeros(10)
    assert analyse(x, x, tau_max=20) is None


def test_analyse_returns_result():
    x, y = _synth_pair()
    r = analyse(x, y)
    assert isinstance(r, SymbiosisResult)


def test_analyse_n_samples():
    x, y = _synth_pair(400, seed=1)
    r = analyse(x, y, tau_max=10)
    assert r.n_samples == 400


def test_analyse_pearson_identical_series():
    """Passing same series twice → ρ=1."""
    rng = np.random.default_rng(9)
    x = np.cumsum(rng.standard_normal(300)) * 0.05
    r = analyse(x, x, tau_max=10)
    assert abs(r.pearson_corr - 1.0) < 1e-6


def test_analyse_pearson_independent_series():
    """IID independent series → |ρ| should be small (raw normals, not cumsums)."""
    rng = np.random.default_rng(10)
    x = rng.standard_normal(400) - 0.4
    y = rng.standard_normal(400) - 0.4
    r = analyse(x, y, tau_max=10)
    assert abs(r.pearson_corr) < 0.15, f"|ρ|={abs(r.pearson_corr):.4f} too high for IID"


def test_analyse_corr_beats_null_for_coupled():
    """Strongly coupled series → corr_beats_null."""
    x, y = _synth_pair(coupling=0.95, seed=11)
    r = analyse(x, y, tau_max=10)
    assert r.corr_beats_null


def test_analyse_symbiosis_score_bounded():
    x, y = _synth_pair(seed=12)
    r = analyse(x, y, tau_max=10)
    assert 0.0 <= r.symbiosis_score <= 1.0


def test_analyse_leader_synchronous():
    """Zero-lag coupling → peak_lag = 0 → leader = synchronous."""
    x, y = _synth_pair(lag=0, coupling=0.99, seed=13)
    r = analyse(x, y, tau_max=10)
    assert r.peak_lag == 0
    assert r.leader == "synchronous"


def test_analyse_leader_john_leads():
    """Positive lag → john leads."""
    x, y = _synth_pair(lag=5, coupling=0.99, seed=14)
    r = analyse(x, y, tau_max=15)
    assert r.peak_lag > 0
    assert r.leader == "john_leads"


def test_analyse_coupled_property():
    """Identical series → all three metrics beat null → coupled."""
    rng = np.random.default_rng(15)
    x = np.cumsum(rng.standard_normal(300)) * 0.05
    r = analyse(x, x, tau_max=10)
    assert r.coupled


def test_analyse_mutual_info_non_negative():
    x, y = _synth_pair(seed=16)
    r = analyse(x, y, tau_max=10)
    assert r.mutual_info >= 0.0


def test_analyse_deterministic():
    x, y = _synth_pair(seed=17)
    r1 = analyse(x, y, null_seed=42)
    r2 = analyse(x, y, null_seed=42)
    assert r1.pearson_corr == r2.pearson_corr
    assert r1.symbiosis_score == r2.symbiosis_score
    assert r1.mutual_info == r2.mutual_info


def test_analyse_phi_means_stored():
    x = np.full(300, -0.4)
    y = np.full(300, -0.2)
    # Constant series → all zeros — may return None if std=0 causes degenerate CC
    # Use non-constant
    rng = np.random.default_rng(18)
    x = rng.standard_normal(300) - 0.4
    y = rng.standard_normal(300) - 0.2
    r = analyse(x, y, tau_max=10)
    assert abs(r.phi_albedo_mean - x[-300:].mean()) < 1e-6
    assert abs(r.phi_john_mean - y[-300:].mean()) < 1e-6


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry()
    # May be None if John phi unavailable; we skip gracefully
    if r is None:
        pytest.skip("Could not load both agent phi series")
    assert isinstance(r, SymbiosisResult)


@skip_no_telemetry
def test_live_pearson_bounded():
    r = analyse_from_telemetry()
    if r is None:
        pytest.skip("Both phi series not available")
    assert -1.0 <= r.pearson_corr <= 1.0


@skip_no_telemetry
def test_live_symbiosis_score_bounded():
    r = analyse_from_telemetry()
    if r is None:
        pytest.skip("Both phi series not available")
    assert 0.0 <= r.symbiosis_score <= 1.0


@skip_no_telemetry
def test_live_mutual_info_non_negative():
    r = analyse_from_telemetry()
    if r is None:
        pytest.skip("Both phi series not available")
    assert r.mutual_info >= 0.0


@skip_no_telemetry
def test_live_deterministic():
    r1 = analyse_from_telemetry()
    r2 = analyse_from_telemetry()
    if r1 is None or r2 is None:
        pytest.skip("Both phi series not available")
    assert r1.pearson_corr == r2.pearson_corr
    assert r1.symbiosis_score == r2.symbiosis_score
