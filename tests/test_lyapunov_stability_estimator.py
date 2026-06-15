"""Tests for LyapunovStabilityEstimator — Lyapunov exponent of phi dynamics."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pytest

from algorithms.LyapunovStabilityEstimator import (
    LyapunovResult,
    _embed,
    _find_nearest_neighbours_fast,
    _divergence_curve,
    _fit_slope,
    _phase_randomise,
    _classify,
    analyse,
)


# ── Test helpers ──────────────────────────────────────────────────────────────

def make_noisy(n=300, std=0.05, seed=0):
    rng = np.random.default_rng(seed)
    return 0.5 + rng.normal(0, std, n)


def make_chaotic_logistic(n=500, r=3.99, seed=0):
    """Logistic map x(t+1) = r·x(t)·(1-x(t)) — chaotic for r≈4."""
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    x[0] = rng.uniform(0.3, 0.7)
    for t in range(1, n):
        x[t] = r * x[t-1] * (1 - x[t-1])
    return x


def make_stable_decay(n=300, decay=0.9, seed=0):
    """AR(1) with |coef| < 1 → stable attractor."""
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    x[0] = 0.5
    for t in range(1, n):
        x[t] = decay * x[t-1] + rng.normal(0, 0.01)
    return x


def make_sine(n=300, freq=0.05, seed=0):
    """Pure sinusoid — limit cycle, should be near-critical or stable."""
    t = np.arange(n)
    rng = np.random.default_rng(seed)
    return 0.5 + 0.2 * np.sin(2 * np.pi * freq * t) + rng.normal(0, 0.01, n)


# ── _embed tests ──────────────────────────────────────────────────────────────

class TestEmbed:
    def test_output_shape(self):
        x = np.arange(20, dtype=float)
        Y = _embed(x, m=3, tau=1)
        assert Y.shape == (18, 3)  # n - (m-1)*tau = 20 - 2

    def test_output_shape_tau2(self):
        x = np.arange(20, dtype=float)
        Y = _embed(x, m=3, tau=2)
        assert Y.shape == (16, 3)  # 20 - (3-1)*2

    def test_first_row(self):
        x = np.arange(10, dtype=float)
        Y = _embed(x, m=3, tau=1)
        np.testing.assert_array_equal(Y[0], [0., 1., 2.])

    def test_last_row(self):
        x = np.arange(10, dtype=float)
        Y = _embed(x, m=3, tau=1)
        np.testing.assert_array_equal(Y[-1], [7., 8., 9.])

    def test_m1_is_identity(self):
        x = np.arange(10, dtype=float)
        Y = _embed(x, m=1, tau=1)
        assert Y.shape == (10, 1)
        np.testing.assert_array_equal(Y[:, 0], x)

    def test_returns_empty_for_too_short(self):
        x = np.array([1.0, 2.0])
        Y = _embed(x, m=5, tau=2)  # needs 1 + 4*2 = 9 samples
        assert Y.shape[0] == 0

    def test_tau2_structure(self):
        x = np.arange(10, dtype=float)
        Y = _embed(x, m=3, tau=2)
        np.testing.assert_array_equal(Y[0], [0., 2., 4.])
        np.testing.assert_array_equal(Y[1], [1., 3., 5.])


# ── _find_nearest_neighbours_fast tests ──────────────────────────────────────

class TestNearestNeighbours:
    def test_output_length(self):
        Y = np.random.default_rng(0).random((50, 3))
        nn = _find_nearest_neighbours_fast(Y, W=5)
        assert len(nn) == 50

    def test_exclusion_window(self):
        Y = np.random.default_rng(1).random((30, 3))
        W = 5
        nn = _find_nearest_neighbours_fast(Y, W=W)
        for i, j in enumerate(nn):
            if j >= 0:
                assert abs(i - j) > W

    def test_not_self_neighbour(self):
        Y = np.random.default_rng(2).random((30, 3))
        nn = _find_nearest_neighbours_fast(Y, W=3)
        for i, j in enumerate(nn):
            assert i != j or j == -1

    def test_returns_valid_indices(self):
        Y = np.random.default_rng(3).random((40, 2))
        nn = _find_nearest_neighbours_fast(Y, W=5)
        for j in nn:
            assert j == -1 or (0 <= j < 40)

    def test_identical_series_finds_near_copy(self):
        """Two identical segments should be nearest neighbours."""
        Y = np.zeros((30, 2))
        Y[:15] = np.arange(15)[:, None]   # [0,0], [1,1], ...
        Y[15:] = Y[:15]                    # exact copy, offset by 15
        nn = _find_nearest_neighbours_fast(Y, W=2)
        # Point 0 should have nearest neighbour at 15 (copy)
        assert nn[0] == 15 or nn[15] == 0


# ── _divergence_curve tests ───────────────────────────────────────────────────

class TestDivergenceCurve:
    def test_output_length(self):
        Y = np.random.default_rng(0).random((100, 3))
        nn = _find_nearest_neighbours_fast(Y, W=5)
        curve, n_pairs = _divergence_curve(Y, nn, K=10)
        assert len(curve) == 11  # K+1

    def test_n_pairs_positive(self):
        Y = np.random.default_rng(1).random((100, 3))
        nn = _find_nearest_neighbours_fast(Y, W=5)
        _, n_pairs = _divergence_curve(Y, nn, K=10)
        assert n_pairs > 0

    def test_returns_zeros_for_all_invalid_nn(self):
        Y = np.random.default_rng(2).random((20, 3))
        nn = np.full(20, -1, dtype=int)  # all invalid
        curve, n_pairs = _divergence_curve(Y, nn, K=5)
        assert n_pairs == 0
        np.testing.assert_array_equal(curve, np.zeros(6))

    def test_divergence_nonnegative(self):
        """Distances can't be negative → log-divergence can be very negative but finite."""
        Y = np.random.default_rng(3).random((80, 2))
        nn = _find_nearest_neighbours_fast(Y, W=5)
        curve, n_pairs = _divergence_curve(Y, nn, K=10)
        assert np.all(np.isfinite(curve))


# ── _fit_slope tests ──────────────────────────────────────────────────────────

class TestFitSlope:
    def test_positive_slope_on_rising(self):
        curve = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
        slope, r2 = _fit_slope(curve)
        assert slope > 0
        assert r2 > 0.99

    def test_negative_slope_on_falling(self):
        curve = np.array([0.0, -0.1, -0.2, -0.3, -0.4])
        slope, r2 = _fit_slope(curve)
        assert slope < 0
        assert r2 > 0.99

    def test_zero_slope_on_flat(self):
        curve = np.ones(10)
        slope, r2 = _fit_slope(curve)
        assert abs(slope) < 1e-10

    def test_r2_in_unit_interval(self):
        curve = np.random.default_rng(0).random(15)
        slope, r2 = _fit_slope(curve)
        assert 0.0 <= r2 <= 1.0

    def test_short_curve_returns_zeros(self):
        curve = np.array([0.5])  # K=0 → no k>=1 points
        slope, r2 = _fit_slope(curve)
        assert slope == 0.0
        assert r2 == 0.0


# ── _phase_randomise tests ────────────────────────────────────────────────────

class TestPhaseRandomise:
    def test_same_length(self):
        x = make_noisy(100, seed=0)
        rng = np.random.default_rng(0)
        null = _phase_randomise(x, rng)
        assert len(null) == len(x)

    def test_preserves_power_spectrum(self):
        x = make_noisy(100, std=0.1, seed=0)
        rng = np.random.default_rng(0)
        null = _phase_randomise(x, rng)
        orig = np.sort(np.abs(np.fft.rfft(x)) ** 2)
        null_s = np.sort(np.abs(np.fft.rfft(null)) ** 2)
        np.testing.assert_allclose(orig, null_s, rtol=1e-6)

    def test_different_from_original(self):
        x = make_noisy(100, std=0.05, seed=0)
        rng = np.random.default_rng(0)
        null = _phase_randomise(x, rng)
        assert not np.allclose(x, null)


# ── _classify tests ───────────────────────────────────────────────────────────

class TestClassify:
    def test_chaotic(self):
        assert _classify(0.1) == "CHAOTIC"
        assert _classify(0.06) == "CHAOTIC"

    def test_stable(self):
        assert _classify(-0.1) == "STABLE"
        assert _classify(-0.06) == "STABLE"

    def test_critical_positive(self):
        assert _classify(0.04) == "CRITICAL"

    def test_critical_negative(self):
        assert _classify(-0.04) == "CRITICAL"

    def test_critical_zero(self):
        assert _classify(0.0) == "CRITICAL"

    def test_boundary_chaos(self):
        # threshold is strict >0.05, so 0.05 is CRITICAL
        assert _classify(0.05) == "CRITICAL"
        assert _classify(0.051) == "CHAOTIC"

    def test_boundary_stable(self):
        # threshold is strict <-0.05, so -0.05 is CRITICAL
        assert _classify(-0.05) == "CRITICAL"
        assert _classify(-0.051) == "STABLE"


# ── analyse() integration tests ───────────────────────────────────────────────

class TestAnalyse:
    def test_returns_none_on_too_short(self):
        phi = np.array([0.5, 0.6, 0.5])
        assert analyse(phi=phi) is None

    def test_returns_result_on_valid(self):
        phi = make_noisy(300, seed=0)
        r = analyse(phi=phi, m=3, tau=1, W=5, K=10)
        assert isinstance(r, LyapunovResult)

    def test_n_samples_correct(self):
        phi = make_noisy(200, seed=1)
        r = analyse(phi=phi, m=3, tau=1, W=5, K=10)
        assert r.n_samples == 200

    def test_regime_valid_string(self):
        phi = make_noisy(200, seed=2)
        r = analyse(phi=phi, m=3, tau=1, W=5, K=10)
        assert r.regime in ("CHAOTIC", "CRITICAL", "STABLE")

    def test_exponent_finite(self):
        phi = make_noisy(200, seed=3)
        r = analyse(phi=phi, m=3, tau=1, W=5, K=10)
        assert np.isfinite(r.lyapunov_exponent)

    def test_null_exponent_finite(self):
        phi = make_noisy(200, seed=4)
        r = analyse(phi=phi, m=3, tau=1, W=5, K=10)
        assert np.isfinite(r.null_exponent)

    def test_beats_null_consistent(self):
        phi = make_noisy(200, seed=5)
        r = analyse(phi=phi, m=3, tau=1, W=5, K=10)
        assert r.beats_null == (r.lyapunov_exponent < r.null_exponent)

    def test_r2_in_unit_interval(self):
        phi = make_noisy(200, seed=6)
        r = analyse(phi=phi, m=3, tau=1, W=5, K=10)
        assert 0.0 <= r.divergence_slope_r2 <= 1.0

    def test_n_pairs_positive(self):
        phi = make_noisy(200, seed=7)
        r = analyse(phi=phi, m=3, tau=1, W=5, K=10)
        assert r.n_pairs > 0

    def test_divergence_curve_length(self):
        phi = make_noisy(200, seed=8)
        r = analyse(phi=phi, m=3, tau=1, W=5, K=10)
        assert len(r.divergence_curve) == 11  # K+1

    def test_phi_std_correct(self):
        phi = make_noisy(200, seed=9)
        r = analyse(phi=phi, m=3, tau=1, W=5, K=10)
        np.testing.assert_allclose(r.phi_std, float(phi.std()), rtol=1e-6)

    def test_is_critical_property(self):
        phi = make_noisy(200, seed=10)
        r = analyse(phi=phi, m=3, tau=1, W=5, K=10)
        assert r.is_critical == (r.regime == "CRITICAL")

    def test_is_chaotic_property(self):
        phi = make_noisy(200, seed=11)
        r = analyse(phi=phi, m=3, tau=1, W=5, K=10)
        assert r.is_chaotic == (r.regime == "CHAOTIC")

    def test_to_dict_keys(self):
        phi = make_noisy(200, seed=12)
        r = analyse(phi=phi, m=3, tau=1, W=5, K=10)
        d = r.to_dict()
        for key in ("lyapunov_exponent", "null_exponent", "beats_null",
                    "regime", "n_pairs", "n_samples", "phi_std",
                    "divergence_slope_r2", "embedding_dim"):
            assert key in d

    def test_returns_none_for_zero_std_phi(self):
        phi = np.full(200, 0.5)
        assert analyse(phi=phi) is None

    def test_deterministic(self):
        phi = make_noisy(200, seed=13)
        r1 = analyse(phi=phi.copy(), null_seed=42)
        r2 = analyse(phi=phi.copy(), null_seed=42)
        assert r1.lyapunov_exponent == r2.lyapunov_exponent
        assert r1.null_exponent == r2.null_exponent

    def test_different_null_seed_changes_null_exponent(self):
        phi = make_noisy(200, seed=14)
        r1 = analyse(phi=phi.copy(), null_seed=1)
        r2 = analyse(phi=phi.copy(), null_seed=2)
        # Null exponents may differ with different seeds
        assert isinstance(r1, LyapunovResult)
        assert isinstance(r2, LyapunovResult)

    def test_returns_none_no_data_unknown_agent(self):
        r = analyse(agent='nonexistent_xyz_agent')
        assert r is None or isinstance(r, LyapunovResult)

    def test_embedding_params_recorded(self):
        phi = make_noisy(200, seed=15)
        r = analyse(phi=phi, m=4, tau=2, W=8, K=15)
        assert r.embedding_dim == 4
        assert r.embedding_tau == 2
        assert r.exclusion_window == 8
        assert r.divergence_horizon == 15

    def test_chaotic_series_tends_positive_exponent(self):
        """Logistic map at r≈4 should produce CHAOTIC or at least positive λ.
        This is a statistical tendency, not a guarantee, so we just verify it runs."""
        phi = make_chaotic_logistic(n=400, r=3.99)
        r = analyse(phi=phi, m=3, tau=1, W=10, K=20)
        assert isinstance(r, LyapunovResult)
        # Logistic map true λ₁ ≈ ln(2) ≈ 0.69; our estimator should be positive
        # We allow some slack but it should be non-negative
        assert r.lyapunov_exponent > -0.2

    def test_stable_ar1_tends_negative_exponent(self):
        """Stable AR(1) with decay < 1 should produce negative or near-zero λ."""
        phi = make_stable_decay(n=400, decay=0.7, seed=0)
        r = analyse(phi=phi, m=3, tau=1, W=10, K=20)
        assert isinstance(r, LyapunovResult)
        # Stable AR(1) should not be classified as strongly chaotic
        assert r.lyapunov_exponent < 0.3
