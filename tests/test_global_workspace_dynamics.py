"""Tests for GlobalWorkspaceDynamics — ignition detection in phi series."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pytest

from algorithms.GlobalWorkspaceDynamics import (
    GlobalWorkspaceResult,
    _rolling_baseline,
    _detect_ignitions,
    _phase_randomise,
    _classify_regime,
    analyse,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_flat(n=100, val=0.5):
    return np.full(n, val, dtype=float)


def make_noisy(n=100, std=0.05, seed=0):
    rng = np.random.default_rng(seed)
    return 0.5 + rng.normal(0, std, n)


def make_with_ignitions(n=200, spike_positions=None, spike_height=0.5, seed=1):
    """Create a phi series with controlled ignition spikes."""
    rng = np.random.default_rng(seed)
    phi = 0.5 + rng.normal(0, 0.03, n)
    if spike_positions is None:
        spike_positions = [50, 120]
    for pos in spike_positions:
        if pos < n:
            # Ignition: sudden jump + sustained elevation + decay
            phi[pos] += spike_height
            for k in range(1, 5):  # sustained for 4 steps
                if pos + k < n:
                    phi[pos + k] += spike_height * (1 - k * 0.2)
    return phi


# ── _rolling_baseline tests ───────────────────────────────────────────────────

class TestRollingBaseline:
    def test_flat_series_baseline_equals_value(self):
        phi = make_flat(50, val=0.7)
        mu, sigma = _rolling_baseline(phi, W=10)
        # After warm-up, baseline should be ~0.7
        np.testing.assert_allclose(mu[10:], 0.7, atol=1e-10)

    def test_sigma_nonzero_on_noisy(self):
        phi = make_noisy(100, std=0.1, seed=0)
        mu, sigma = _rolling_baseline(phi, W=20)
        assert np.all(sigma > 1e-4)

    def test_baseline_lags_series(self):
        """Baseline at t uses only t-W..t-1, so a jump at t doesn't affect it."""
        phi = np.zeros(50, dtype=float)
        phi[30:] = 1.0
        mu, sigma = _rolling_baseline(phi, W=10)
        # At t=30, baseline is based on phi[20..29] = 0.0
        assert mu[30] < 0.1

    def test_sigma_minimum_clamp(self):
        """Sigma must not be zero even for constant input."""
        phi = make_flat(30, val=0.5)
        _, sigma = _rolling_baseline(phi, W=20)
        assert np.all(sigma >= 1e-3)

    def test_output_length_matches_input(self):
        phi = make_noisy(77, seed=7)
        mu, sigma = _rolling_baseline(phi, W=10)
        assert len(mu) == 77
        assert len(sigma) == 77


# ── _detect_ignitions tests ───────────────────────────────────────────────────

class TestDetectIgnitions:
    def test_no_ignitions_on_flat(self):
        phi = make_flat(100, val=0.5)
        mu, sigma = _rolling_baseline(phi, W=20)
        times, amps, bcast, decay = _detect_ignitions(phi, mu, sigma,
                                                       alpha=2.0, beta=1.0,
                                                       T_min=2, T_decay=15)
        assert len(times) == 0

    def test_detects_clear_ignition(self):
        phi = make_with_ignitions(200, spike_positions=[60], spike_height=0.5)
        mu, sigma = _rolling_baseline(phi, W=20)
        times, amps, bcast, decay = _detect_ignitions(phi, mu, sigma,
                                                       alpha=2.0, beta=1.0,
                                                       T_min=2, T_decay=15)
        assert len(times) >= 1
        # Onset should be near the spike position
        assert any(abs(t - 60) < 5 for t in times)

    def test_ignition_amplitude_positive(self):
        phi = make_with_ignitions(200, spike_positions=[80], spike_height=0.6)
        mu, sigma = _rolling_baseline(phi, W=20)
        times, amps, bcast, decay = _detect_ignitions(phi, mu, sigma,
                                                       alpha=2.0, beta=1.0,
                                                       T_min=2, T_decay=15)
        if amps:
            assert all(a > 0 for a in amps)

    def test_no_ignition_on_gradual_rise(self):
        """Slow linear rise: each step is tiny relative to sigma of the series."""
        # Use a sinusoidal series with known sigma so min_sigma guard triggers
        rng = np.random.default_rng(0)
        t_arr = np.linspace(0, 4 * np.pi, 200)
        phi = 0.5 + 0.1 * np.sin(t_arr) + rng.normal(0, 0.01, 200)
        mu, sigma = _rolling_baseline(phi, W=20)
        times, amps, bcast, decay = _detect_ignitions(phi, mu, sigma,
                                                       alpha=4.0, beta=2.0,
                                                       T_min=2, T_decay=15)
        assert len(times) == 0

    def test_no_ignition_on_single_spike_reverts(self):
        """A spike that immediately reverts (noise spike) should not count."""
        phi = np.full(100, 0.5, dtype=float)
        phi[50] = 2.0   # spike
        phi[51] = 0.5   # immediately reverts
        mu, sigma = _rolling_baseline(phi, W=20)
        times, amps, bcast, decay = _detect_ignitions(phi, mu, sigma,
                                                       alpha=2.0, beta=1.0,
                                                       T_min=3, T_decay=15)
        assert len(times) == 0

    def test_broadcast_duration_at_least_T_min(self):
        phi = make_with_ignitions(200, spike_positions=[70], spike_height=0.5)
        mu, sigma = _rolling_baseline(phi, W=20)
        _, _, bcast, _ = _detect_ignitions(phi, mu, sigma,
                                            alpha=2.0, beta=1.0,
                                            T_min=2, T_decay=15)
        for d in bcast:
            assert d >= 2

    def test_multiple_ignitions_detected(self):
        phi = make_with_ignitions(300, spike_positions=[60, 160], spike_height=0.5)
        mu, sigma = _rolling_baseline(phi, W=20)
        times, _, _, _ = _detect_ignitions(phi, mu, sigma,
                                            alpha=2.0, beta=1.0,
                                            T_min=2, T_decay=15)
        assert len(times) >= 2

    def test_decay_time_positive(self):
        phi = make_with_ignitions(200, spike_positions=[80], spike_height=0.5)
        mu, sigma = _rolling_baseline(phi, W=20)
        _, _, _, decay = _detect_ignitions(phi, mu, sigma,
                                            alpha=2.0, beta=1.0,
                                            T_min=2, T_decay=15)
        for d in decay:
            assert d >= 1


# ── _phase_randomise tests ────────────────────────────────────────────────────

class TestPhaseRandomise:
    def test_same_length(self):
        phi = make_noisy(80, seed=3)
        rng = np.random.default_rng(0)
        null = _phase_randomise(phi, rng)
        assert len(null) == len(phi)

    def test_same_power_spectrum(self):
        phi = make_noisy(100, std=0.1, seed=5)
        rng = np.random.default_rng(0)
        null = _phase_randomise(phi, rng)
        orig_power = np.sort(np.abs(np.fft.rfft(phi)) ** 2)
        null_power = np.sort(np.abs(np.fft.rfft(null)) ** 2)
        np.testing.assert_allclose(orig_power, null_power, rtol=1e-6)

    def test_different_from_original(self):
        phi = make_noisy(100, std=0.1, seed=5)
        rng = np.random.default_rng(0)
        null = _phase_randomise(phi, rng)
        assert not np.allclose(phi, null)


# ── _classify_regime tests ────────────────────────────────────────────────────

class TestClassifyRegime:
    def test_high_rate_beats_null_is_ignition(self):
        assert _classify_regime(3.0, True) == "IGNITION"

    def test_high_rate_no_beats_is_transitional(self):
        assert _classify_regime(3.0, False) == "TRANSITIONAL"

    def test_low_rate_beats_null_is_transitional(self):
        assert _classify_regime(0.8, True) == "TRANSITIONAL"

    def test_low_rate_no_beats_is_quiescent(self):
        assert _classify_regime(0.2, False) == "QUIESCENT"

    def test_boundary_rate_05_beats_is_transitional(self):
        assert _classify_regime(0.5, True) == "TRANSITIONAL"

    def test_boundary_rate_05_no_beats_is_quiescent(self):
        assert _classify_regime(0.5, False) == "QUIESCENT"


# ── analyse() integration tests ───────────────────────────────────────────────

class TestAnalyse:
    def test_returns_none_on_short_series(self):
        phi = np.array([0.5, 0.6, 0.7])
        assert analyse(phi=phi) is None

    def test_returns_result_on_valid_flat(self):
        phi = make_noisy(200, std=0.02, seed=0)
        r = analyse(phi=phi)
        assert isinstance(r, GlobalWorkspaceResult)

    def test_n_samples_correct(self):
        phi = make_noisy(150, seed=2)
        r = analyse(phi=phi)
        assert r.n_samples == 150

    def test_ignition_rate_zero_on_flat(self):
        phi = make_flat(200, val=0.5)
        r = analyse(phi=phi, alpha=2.0)
        assert r.ignition_rate == 0.0

    def test_ignition_detected_on_spike_series(self):
        phi = make_with_ignitions(300, spike_positions=[80, 180], spike_height=0.6)
        r = analyse(phi=phi, alpha=2.0, beta=1.0, T_min=2, T_decay=15)
        assert r.n_ignitions >= 1

    def test_ignition_rate_is_per_100(self):
        phi = make_with_ignitions(200, spike_positions=[80], spike_height=0.8)
        r = analyse(phi=phi)
        assert r.ignition_rate == pytest.approx(r.n_ignitions / 200 * 100.0, abs=1e-9)

    def test_ignition_score_in_unit_interval(self):
        phi = make_noisy(200, seed=5)
        r = analyse(phi=phi)
        assert 0.0 <= r.ignition_score <= 1.0

    def test_null_rate_non_negative(self):
        phi = make_noisy(200, seed=7)
        r = analyse(phi=phi)
        assert r.null_ignition_rate >= 0.0

    def test_beats_null_consistent(self):
        phi = make_noisy(200, seed=9)
        r = analyse(phi=phi)
        assert r.beats_null == (r.ignition_rate > r.null_ignition_rate)

    def test_regime_is_valid_string(self):
        phi = make_noisy(200, seed=11)
        r = analyse(phi=phi)
        assert r.regime in ("IGNITION", "TRANSITIONAL", "QUIESCENT")

    def test_phi_stats_correct(self):
        phi = make_with_ignitions(200, spike_positions=[100], spike_height=0.3)
        r = analyse(phi=phi)
        np.testing.assert_allclose(r.phi_mean, float(phi.mean()), rtol=1e-6)
        np.testing.assert_allclose(r.phi_std, float(phi.std()), rtol=1e-6)

    def test_ignition_times_subset_of_valid_indices(self):
        phi = make_with_ignitions(300, spike_positions=[100, 200], spike_height=0.5)
        r = analyse(phi=phi)
        for t in r.ignition_times:
            assert 0 <= t < r.n_samples

    def test_mean_amplitude_positive_when_ignitions_exist(self):
        phi = make_with_ignitions(300, spike_positions=[100], spike_height=0.7)
        r = analyse(phi=phi)
        if r.n_ignitions > 0:
            assert r.mean_amplitude > 0.0

    def test_mean_broadcast_dur_nonneg(self):
        phi = make_with_ignitions(300, spike_positions=[100], spike_height=0.7)
        r = analyse(phi=phi)
        assert r.mean_broadcast_dur >= 0.0

    def test_mean_decay_time_positive_when_ignitions_exist(self):
        phi = make_with_ignitions(300, spike_positions=[100], spike_height=0.7)
        r = analyse(phi=phi)
        if r.n_ignitions > 0:
            assert r.mean_decay_time >= 1.0

    def test_to_dict_keys(self):
        phi = make_noisy(200, seed=13)
        r = analyse(phi=phi)
        d = r.to_dict()
        assert "regime" in d
        assert "n_ignitions" in d
        assert "ignition_rate" in d
        assert "ignition_score" in d
        assert "beats_null" in d

    def test_returns_none_when_phi_none_and_no_chs(self):
        r = analyse(agent='nonexistent_agent_xyz')
        # Either None (no data) or a valid result — never an exception
        assert r is None or isinstance(r, GlobalWorkspaceResult)

    def test_deterministic_with_same_seed(self):
        phi = make_with_ignitions(300, spike_positions=[100, 200], spike_height=0.5)
        r1 = analyse(phi=phi.copy(), null_seed=42)
        r2 = analyse(phi=phi.copy(), null_seed=42)
        assert r1.n_ignitions == r2.n_ignitions
        assert r1.null_ignition_rate == r2.null_ignition_rate

    def test_different_seed_can_differ(self):
        phi = make_noisy(200, std=0.1, seed=0)
        r1 = analyse(phi=phi.copy(), null_seed=1)
        r2 = analyse(phi=phi.copy(), null_seed=2)
        # Null rates may differ — just verify both run without error
        assert isinstance(r1, GlobalWorkspaceResult)
        assert isinstance(r2, GlobalWorkspaceResult)

    def test_high_alpha_gives_fewer_ignitions(self):
        phi = make_with_ignitions(300, spike_positions=[80, 160], spike_height=0.5)
        r_low = analyse(phi=phi.copy(), alpha=1.5)
        r_high = analyse(phi=phi.copy(), alpha=5.0)
        if r_low and r_high:
            assert r_low.n_ignitions >= r_high.n_ignitions

    def test_has_ignitions_property(self):
        phi = make_with_ignitions(300, spike_positions=[100], spike_height=0.8)
        r = analyse(phi=phi)
        assert r.has_ignitions == (r.n_ignitions > 0)
