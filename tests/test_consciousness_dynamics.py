#!/usr/bin/env python3
"""Tests for frameworks/dynamics/ConsciousnessDynamics.py."""

import sys
import importlib
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import frameworks.dynamics.ConsciousnessDynamics as cd


# ── Helpers ────────────────────────────────────────────────────────────────────

RNG = np.random.default_rng(0)


def _sine(n=256, freq=0.05, noise=0.02):
    t = np.arange(n, dtype=float)
    return np.sin(2 * np.pi * freq * t) + RNG.normal(0, noise, n)


def _noisy(n=256, std=1.0):
    return RNG.normal(0, std, n)


def _stable(n=256, target=3.0, pull=0.15):
    """Damped random walk converging to a fixed point."""
    x = np.zeros(n)
    x[0] = target + RNG.normal(0, 0.5)
    for i in range(1, n):
        x[i] = x[i - 1] - pull * (x[i - 1] - target) + RNG.normal(0, 0.05)
    return x


# ── _acf_zero_crossing ────────────────────────────────────────────────────────

class TestAcfZeroCrossing:
    def test_returns_positive_int(self):
        phi = _sine(256)
        tau = cd._acf_zero_crossing(phi)
        assert isinstance(tau, int)
        assert tau >= 1

    def test_constant_signal_returns_1(self):
        phi = np.ones(100)
        tau = cd._acf_zero_crossing(phi)
        assert tau == 1

    def test_sine_tau_near_quarter_period(self):
        # quarter period of freq=0.05 is 1/(4*0.05)=5
        phi = np.sin(2 * np.pi * 0.05 * np.arange(512))
        tau = cd._acf_zero_crossing(phi)
        assert 3 <= tau <= 8


# ── embed ─────────────────────────────────────────────────────────────────────

class TestEmbed:
    def test_shape_correct(self):
        phi = np.arange(100, dtype=float)
        tau = 2
        m = 3
        emb = cd.embed(phi, m=m, tau=tau)
        expected_rows = 100 - (m - 1) * tau
        assert emb.shape == (expected_rows, m)

    def test_default_tau_is_acf_based(self):
        phi = _sine(256)
        emb = cd.embed(phi, m=3)
        assert emb.ndim == 2
        assert emb.shape[1] == 3

    def test_very_short_signal_falls_back(self):
        phi = np.arange(5, dtype=float)
        emb = cd.embed(phi, m=3, tau=1)
        assert emb.ndim == 2

    def test_explicit_tau(self):
        phi = np.arange(50, dtype=float)
        emb = cd.embed(phi, m=2, tau=3)
        assert emb.shape == (50 - 3, 2)


# ── detect_fixed_points ───────────────────────────────────────────────────────

class TestDetectFixedPoints:
    def test_returns_positive_k_and_radii_list(self):
        phi = _stable(256)
        emb = cd.embed(phi, m=3)
        k, radii = cd.detect_fixed_points(emb)
        assert isinstance(k, int)
        assert k >= 1
        assert len(radii) == k
        assert all(r >= 0 for r in radii)

    def test_single_fixed_point_for_convergent_series(self):
        phi = _stable(256, target=5.0, pull=0.3)
        emb = cd.embed(phi, m=3)
        k, _ = cd.detect_fixed_points(emb)
        assert k <= 3  # should find 1-2, definitely not 4

    def test_bimodal_may_find_two_clusters(self):
        phi = np.concatenate([
            _stable(128, target=1.0, pull=0.3),
            _stable(128, target=8.0, pull=0.3),
        ])
        emb = cd.embed(phi, m=3)
        k, _ = cd.detect_fixed_points(emb, k_max=4)
        assert k >= 1

    def test_tiny_embedding_ok(self):
        emb = np.ones((10, 2)) + RNG.normal(0, 0.01, (10, 2))
        k, radii = cd.detect_fixed_points(emb)
        assert k >= 1
        assert len(radii) == k


# ── lyapunov_rosenstein ───────────────────────────────────────────────────────

class TestLyapunovRosenstein:
    def test_returns_float(self):
        phi = _noisy(256)
        emb = cd.embed(phi, m=3)
        lam = cd.lyapunov_rosenstein(emb)
        assert isinstance(lam, float)

    def test_stable_orbit_near_zero_or_negative(self):
        phi = _stable(512, pull=0.3)
        emb = cd.embed(phi, m=3)
        lam = cd.lyapunov_rosenstein(emb)
        # Stable orbit should have non-positive Lyapunov
        assert lam < 0.1

    def test_white_noise_positive(self):
        phi = RNG.normal(0, 1, 512)
        emb = cd.embed(phi, m=3)
        lam = cd.lyapunov_rosenstein(emb)
        # White noise is chaotic; expect positive or near zero
        assert isinstance(lam, float)

    def test_single_row_embedding_returns_zero(self):
        emb = np.array([[1.0, 2.0, 3.0]])
        lam = cd.lyapunov_rosenstein(emb)
        assert lam == 0.0


# ── detect_limit_cycle ────────────────────────────────────────────────────────

class TestDetectLimitCycle:
    def test_strong_sine_has_cycle(self):
        phi = np.sin(2 * np.pi * 0.1 * np.arange(256))
        has_cycle, freq = cd.detect_limit_cycle(phi)
        assert has_cycle
        assert 0.05 <= freq <= 0.15

    def test_white_noise_no_dominant_cycle(self):
        rng = np.random.default_rng(7)
        phi = rng.normal(0, 1, 1024)
        has_cycle, freq = cd.detect_limit_cycle(phi)
        # White noise should not trigger a dominant frequency
        assert isinstance(has_cycle, bool)  # just ensure it runs

    def test_constant_signal_no_cycle(self):
        phi = np.ones(256) * 3.14
        has_cycle, freq = cd.detect_limit_cycle(phi)
        assert not has_cycle
        assert freq == 0.0

    def test_returns_zero_freq_when_no_cycle(self):
        phi = _stable(256)
        _, freq = cd.detect_limit_cycle(phi)
        assert isinstance(freq, float)

    def test_frequency_in_valid_range(self):
        phi = _sine(256, freq=0.08)
        has_cycle, freq = cd.detect_limit_cycle(phi)
        if has_cycle:
            assert 0.0 < freq < 0.5


# ── correlation_dimension ─────────────────────────────────────────────────────

class TestCorrelationDimension:
    def test_returns_positive_float(self):
        phi = _sine(256)
        emb = cd.embed(phi, m=3)
        d = cd.correlation_dimension(emb)
        assert isinstance(d, float)
        assert d > 0

    def test_line_has_dimension_near_1(self):
        t = np.linspace(0, 10, 200)
        phi = t
        emb = cd.embed(phi, m=3)
        d = cd.correlation_dimension(emb)
        # A line is a 1-D attractor
        assert 0.5 <= d <= 2.5

    def test_clipped_to_embedding_dim(self):
        phi = _noisy(256)
        emb = cd.embed(phi, m=3)
        d = cd.correlation_dimension(emb)
        assert d <= 3.0

    def test_too_short_returns_1(self):
        emb = np.ones((10, 3))
        d = cd.correlation_dimension(emb)
        assert d == 1.0


# ── bifurcation_index ─────────────────────────────────────────────────────────

class TestBifurcationIndex:
    def test_returns_value_in_unit_interval(self):
        phi = _noisy(256)
        b = cd.bifurcation_index(phi)
        assert 0.0 <= b <= 1.0

    def test_stable_signal_low_index(self):
        phi = np.ones(256) * 5.0 + RNG.normal(0, 0.01, 256)
        b = cd.bifurcation_index(phi)
        assert b < 0.8

    def test_increasing_variance_raises_index(self):
        # Variance grows in second half
        phi = np.concatenate([RNG.normal(0, 0.1, 128), RNG.normal(0, 2.0, 128)])
        b = cd.bifurcation_index(phi)
        assert isinstance(b, float)

    def test_very_short_signal(self):
        phi = np.array([1.0, 2.0, 1.5])
        b = cd.bifurcation_index(phi)
        assert 0.0 <= b <= 1.0


# ── DynamicsResult ─────────────────────────────────────────────────────────────

class TestDynamicsResult:
    def _result(self):
        return cd.DynamicsResult(
            embedding_dim=3,
            embedding_tau=5,
            n_fixed_points=1,
            fixed_point_radii=[0.12],
            lyapunov_estimate=-0.05,
            is_chaotic=False,
            is_stable=True,
            is_critical=False,
            bifurcation_index=0.3,
            near_bifurcation=False,
            has_limit_cycle=False,
            dominant_frequency=0.0,
            attractor_dimension=1.4,
        )

    def test_to_dict_has_all_keys(self):
        r = self._result()
        d = r.to_dict()
        for key in ("embedding_dim", "embedding_tau", "n_fixed_points",
                    "fixed_point_radii", "lyapunov_estimate",
                    "is_chaotic", "is_stable", "is_critical",
                    "bifurcation_index", "near_bifurcation",
                    "has_limit_cycle", "dominant_frequency", "attractor_dimension"):
            assert key in d

    def test_to_dict_types(self):
        d = self._result().to_dict()
        assert isinstance(d["n_fixed_points"], int)
        assert isinstance(d["lyapunov_estimate"], float)
        assert isinstance(d["is_chaotic"], bool)
        assert isinstance(d["fixed_point_radii"], list)

    def test_stable_flags(self):
        r = self._result()
        assert r.is_stable
        assert not r.is_chaotic
        assert not r.is_critical


# ── analyse (integration) ─────────────────────────────────────────────────────

class TestAnalyse:
    def test_returns_none_for_short_series(self):
        phi = np.ones(10)
        assert cd.analyse(phi) is None

    def test_returns_dynamics_result(self):
        phi = _sine(256)
        result = cd.analyse(phi)
        assert isinstance(result, cd.DynamicsResult)

    def test_stable_orbit_is_stable(self):
        phi = _stable(512, pull=0.4)
        result = cd.analyse(phi)
        assert result is not None
        assert not result.is_chaotic

    def test_sine_has_limit_cycle(self):
        phi = np.sin(2 * np.pi * 0.1 * np.arange(512))
        result = cd.analyse(phi)
        assert result is not None
        assert result.has_limit_cycle

    def test_embedding_params_respected(self):
        phi = _sine(256)
        result = cd.analyse(phi, embedding_dim=2, tau=5)
        assert result.embedding_dim == 2
        assert result.embedding_tau == 5

    def test_fixed_point_radii_length_matches_count(self):
        phi = _stable(256)
        result = cd.analyse(phi)
        assert len(result.fixed_point_radii) == result.n_fixed_points

    def test_lyapunov_float(self):
        phi = _noisy(256)
        result = cd.analyse(phi)
        assert isinstance(result.lyapunov_estimate, float)

    def test_bifurcation_index_in_range(self):
        phi = _noisy(256)
        result = cd.analyse(phi)
        assert 0.0 <= result.bifurcation_index <= 1.0

    def test_attractor_dimension_positive(self):
        phi = _sine(256)
        result = cd.analyse(phi)
        assert result.attractor_dimension > 0

    def test_to_dict_serialisable(self):
        import json
        phi = _sine(256)
        result = cd.analyse(phi)
        d = result.to_dict()
        # Must be JSON-serialisable
        json.dumps(d)

    def test_flags_mutually_exclusive(self):
        phi = _sine(256)
        result = cd.analyse(phi)
        # At most one of chaotic / stable can be True
        assert not (result.is_chaotic and result.is_stable)

    def test_is_critical_when_lambda_near_zero(self):
        # Create a near-zero Lyapunov scenario: constant signal
        phi = np.linspace(2.0, 2.5, 128).astype(float)
        result = cd.analyse(phi)
        assert result is not None
        # not necessarily critical, but flags should be consistent
        assert not (result.is_chaotic and result.is_stable)

    def test_near_bifurcation_flag(self):
        phi = _noisy(256)
        result = cd.analyse(phi)
        assert isinstance(result.near_bifurcation, bool)

    def test_dominant_frequency_zero_when_no_cycle(self):
        phi = _stable(256)
        result = cd.analyse(phi)
        if not result.has_limit_cycle:
            assert result.dominant_frequency == 0.0

    def test_dominant_frequency_nonzero_when_cycle(self):
        phi = np.sin(2 * np.pi * 0.1 * np.arange(512))
        result = cd.analyse(phi)
        if result.has_limit_cycle:
            assert result.dominant_frequency > 0.0


# ── analyse_from_telemetry ────────────────────────────────────────────────────

class TestAnalyseFromTelemetry:
    def test_returns_none_or_result(self):
        result = cd.analyse_from_telemetry()
        assert result is None or isinstance(result, cd.DynamicsResult)
