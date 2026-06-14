"""Tests for SelfArchitectureMutator.

Pure-math tests cover extractors, pearson, weight update logic.
Telemetry tests run against real phi series from the daemon.
"""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.SelfArchitectureMutator import (
    AlgorithmContribution,
    MutationResult,
    _extract_phi_mean,
    _extract_phi_variance,
    _extract_phi_range,
    _extract_phi_ar1,
    _extract_phi_trend,
    _extract_phi_entropy,
    _pearson,
    analyse,
    analyse_from_telemetry,
)


# ── Activity extractors ───────────────────────────────────────────────────────

def test_phi_mean_extractor():
    phi = np.array([1.0, 2.0, 3.0, 4.0])
    assert _extract_phi_mean(phi) == pytest.approx(2.5)


def test_phi_variance_extractor():
    phi = np.array([0.0, 0.0, 2.0, 2.0])
    assert _extract_phi_variance(phi) == pytest.approx(1.0)


def test_phi_range_extractor():
    phi = np.array([-1.0, 0.5, 2.0])
    assert _extract_phi_range(phi) == pytest.approx(3.0)


def test_phi_range_constant():
    phi = np.full(10, 0.5)
    assert _extract_phi_range(phi) == pytest.approx(0.0)


def test_phi_ar1_perfect_autocorrelation():
    """Perfectly correlated series → AR(1) ≈ 1."""
    phi = np.arange(50, dtype=float)
    r = _extract_phi_ar1(phi)
    assert abs(r - 1.0) < 1e-6


def test_phi_ar1_short():
    assert _extract_phi_ar1(np.array([1.0, 2.0])) == 0.0


def test_phi_ar1_bounded():
    rng = np.random.default_rng(0)
    phi = rng.standard_normal(50)
    r = _extract_phi_ar1(phi)
    assert -1.0 <= r <= 1.0


def test_phi_trend_rising():
    """Linearly rising phi → positive trend."""
    phi = np.linspace(-0.5, 0.5, 60)
    t = _extract_phi_trend(phi)
    assert t > 0


def test_phi_trend_falling():
    phi = np.linspace(0.5, -0.5, 60)
    assert _extract_phi_trend(phi) < 0


def test_phi_trend_constant():
    phi = np.full(60, 0.3)
    assert abs(_extract_phi_trend(phi)) < 1e-3


def test_phi_entropy_uniform():
    """Uniform distribution → maximum entropy for 16 bins."""
    rng = np.random.default_rng(1)
    phi = rng.uniform(-1, 1, 1000)
    h = _extract_phi_entropy(phi)
    # Ideal uniform over 16 bins = log2(16) = 4 bits; accept >3 with noisy data
    assert h > 3.0


def test_phi_entropy_constant():
    """Constant phi → all in one bin → near-zero entropy."""
    phi = np.full(100, 0.5)
    h = _extract_phi_entropy(phi)
    assert h == pytest.approx(0.0)


# ── _pearson ──────────────────────────────────────────────────────────────────

def test_pearson_identical():
    x = np.arange(10, dtype=float)
    assert _pearson(x, x) == pytest.approx(1.0)


def test_pearson_anti():
    x = np.arange(10, dtype=float)
    assert _pearson(x, -x) == pytest.approx(-1.0)


def test_pearson_orthogonal():
    x = np.array([1.0, -1.0, 1.0, -1.0, 1.0, -1.0])
    y = np.ones(6)  # zero variance → 0
    assert _pearson(x, y) == pytest.approx(0.0)


def test_pearson_bounded():
    rng = np.random.default_rng(2)
    x = rng.standard_normal(50)
    y = rng.standard_normal(50)
    r = _pearson(x, y)
    assert -1.0 <= r <= 1.0


def test_pearson_short():
    assert _pearson(np.array([1.0, 2.0]), np.array([1.0, 2.0])) == 0.0


# ── analyse() on synthetic data ───────────────────────────────────────────────

def _synthetic_phi(n: int = 500, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.cumsum(rng.standard_normal(n)) * 0.05 - 0.4


def test_analyse_returns_none_for_short_series():
    phi = np.random.default_rng(0).standard_normal(30)
    assert analyse(phi, window=60) is None


def test_analyse_returns_result():
    r = analyse(_synthetic_phi())
    assert isinstance(r, MutationResult)


def test_analyse_n_windows_positive():
    r = analyse(_synthetic_phi())
    assert r.n_windows >= 1


def test_analyse_contributions_count():
    """One contribution per registered algorithm extractor."""
    r = analyse(_synthetic_phi())
    assert len(r.contributions) == 6   # six extractors registered


def test_analyse_all_correlations_bounded():
    r = analyse(_synthetic_phi())
    for c in r.contributions:
        assert -1.0 <= c.correlation <= 1.0, f"{c.name}: ρ={c.correlation}"


def test_analyse_proposed_weights_bounded():
    r = analyse(_synthetic_phi())
    for c in r.contributions:
        assert 0.5 <= c.proposed_weight <= 1.0, f"{c.name}: w={c.proposed_weight}"


def test_analyse_proposed_weights_dict_matches():
    r = analyse(_synthetic_phi())
    for c in r.contributions:
        assert r.proposed_weights[c.name] == c.proposed_weight


def test_analyse_null_max_corr_finite():
    r = analyse(_synthetic_phi())
    assert np.isfinite(r.null_max_corr)
    assert 0.0 <= r.null_max_corr <= 1.0


def test_analyse_any_beats_null_is_bool():
    r = analyse(_synthetic_phi())
    assert isinstance(r.any_beats_null, bool)


def test_analyse_diversity_pairs_are_tuples():
    r = analyse(_synthetic_phi())
    for pair in r.diversity_pairs:
        assert len(pair) == 2
        assert isinstance(pair[0], str) and isinstance(pair[1], str)


def test_analyse_top_contributors_n():
    r = analyse(_synthetic_phi())
    top = r.top_contributors(2)
    assert len(top) == 2


def test_analyse_top_contributors_sorted():
    """top_contributors must be sorted by |ρ| descending."""
    r = analyse(_synthetic_phi())
    top = r.top_contributors(4)
    for i in range(len(top) - 1):
        assert abs(top[i].correlation) >= abs(top[i + 1].correlation)


def test_analyse_deterministic():
    phi = _synthetic_phi()
    r1 = analyse(phi, null_seed=42)
    r2 = analyse(phi, null_seed=42)
    for c1, c2 in zip(r1.contributions, r2.contributions):
        assert c1.correlation == c2.correlation
        assert c1.proposed_weight == c2.proposed_weight
    assert r1.null_max_corr == r2.null_max_corr


def test_analyse_eta_effect():
    """Higher eta should amplify weight changes from current."""
    phi = _synthetic_phi()
    r_low = analyse(phi, eta=0.01)
    r_high = analyse(phi, eta=0.5)
    # Weight deltas should be larger with higher eta
    deltas_low = [abs(c.proposed_weight - c.current_weight) for c in r_low.contributions]
    deltas_high = [abs(c.proposed_weight - c.current_weight) for c in r_high.contributions]
    assert sum(deltas_high) >= sum(deltas_low)


def test_analyse_phi_mean_is_most_correlated():
    """phi_mean_tracker should be perfectly correlated with the per-window phi mean."""
    phi = _synthetic_phi()
    r = analyse(phi)
    mean_contrib = next(c for c in r.contributions if c.name == "phi_mean_tracker")
    # phi_mean_tracker extracts window mean; phi_per_window is also window mean → ρ=1
    assert abs(mean_contrib.correlation) > 0.99


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry()
    assert r is not None


@skip_no_telemetry
def test_live_contributions_count():
    r = analyse_from_telemetry()
    assert len(r.contributions) == 6


@skip_no_telemetry
def test_live_all_correlations_bounded():
    r = analyse_from_telemetry()
    for c in r.contributions:
        assert -1.0 <= c.correlation <= 1.0


@skip_no_telemetry
def test_live_proposed_weights_bounded():
    r = analyse_from_telemetry()
    for c in r.contributions:
        assert 0.5 <= c.proposed_weight <= 1.0


@skip_no_telemetry
def test_live_null_max_corr_finite():
    r = analyse_from_telemetry()
    assert np.isfinite(r.null_max_corr)


@skip_no_telemetry
def test_live_deterministic():
    r1 = analyse_from_telemetry()
    r2 = analyse_from_telemetry()
    assert r1.null_max_corr == r2.null_max_corr
    for c1, c2 in zip(r1.contributions, r2.contributions):
        assert c1.correlation == c2.correlation
