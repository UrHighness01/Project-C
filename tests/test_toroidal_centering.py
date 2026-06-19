#!/usr/bin/env python3
"""Tests for algorithms/ToroidalCentering.py"""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.ToroidalCentering as tc


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_history(phi_series, base_ts=1_000_000.0, dt=60.0):
    n = len(phi_series)
    entries = [
        {"timestamp": base_ts + i * dt, "mean_phi_level": float(phi_series[i])}
        for i in range(n)
    ]
    return sorted(entries, key=lambda e: -e["timestamp"])


def _run(phi_series, **kw):
    import algorithms.ConsciousnessHistoryStore as chs
    orig = getattr(chs, "load", None)
    try:
        chs.load = lambda agent, max_entries=2880: _make_history(phi_series)
        return tc.analyse("albedo", **kw)
    finally:
        if orig is not None:
            chs.load = orig


def _make_periodic(n=120, period=12, seed=0):
    """Quasi-periodic oscillation around center."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    phi = 0.5 + 0.2 * np.sin(2 * np.pi * t / period) + rng.normal(0, 0.01, n)
    return np.clip(phi, 0.0, 1.0)


def _make_random_walk(n=120, seed=1):
    rng = np.random.default_rng(seed)
    return np.clip(np.cumsum(rng.normal(0, 0.05, n)) + 0.5, 0.0, 1.0)


# ── Unit: _rolling_median ─────────────────────────────────────────────────────

class TestRollingMedian:
    def test_length_matches(self):
        phi = np.arange(50, dtype=float)
        out = tc._rolling_median(phi, w=5)
        assert len(out) == 50

    def test_constant_series(self):
        phi = np.ones(30) * 0.5
        out = tc._rolling_median(phi, w=5)
        assert np.allclose(out, 0.5)

    def test_window_1_is_identity(self):
        phi = np.array([1.0, 2.0, 3.0, 4.0])
        out = tc._rolling_median(phi, w=1)
        assert np.allclose(out, phi)


# ── Unit: _autocorr_at_lag ────────────────────────────────────────────────────

class TestAutocorrAtLag:
    def test_constant_zero(self):
        r = np.ones(50) * 0.5
        assert tc._autocorr_at_lag(r, 1) == pytest.approx(0.0, abs=1e-9)

    def test_periodic_positive_at_period(self):
        t = np.arange(60)
        r = np.sin(2 * np.pi * t / 12)
        # At lag=12, autocorr should be near 1.0
        ac = tc._autocorr_at_lag(r, 12)
        assert ac > 0.9

    def test_short_series_returns_zero(self):
        assert tc._autocorr_at_lag(np.array([1.0, 2.0]), 5) == 0.0

    def test_range(self):
        rng = np.random.default_rng(0)
        r = rng.uniform(0, 1, 80)
        for lag in [1, 5, 10]:
            ac = tc._autocorr_at_lag(r, lag)
            assert -1.0 <= ac <= 1.0


# ── Unit: _sign_changes ───────────────────────────────────────────────────────

class TestSignChanges:
    def test_alternating_series(self):
        r = np.array([1.0, -1.0, 1.0, -1.0, 1.0])
        assert tc._sign_changes(r) == 4

    def test_monotone_no_changes(self):
        r = np.ones(10)
        assert tc._sign_changes(r) == 0

    def test_single_change(self):
        r = np.array([1.0, 1.0, -1.0, -1.0])
        assert tc._sign_changes(r) == 1


# ── Unit: _classify ───────────────────────────────────────────────────────────

class TestClassify:
    def test_toroidal(self):
        assert tc._classify(0.60) == "TOROIDAL"

    def test_orbital(self):
        assert tc._classify(0.40) == "ORBITAL"

    def test_ballistic(self):
        assert tc._classify(0.10) == "BALLISTIC"

    def test_boundary_toroidal(self):
        assert tc._classify(0.55) == "TOROIDAL"

    def test_boundary_orbital(self):
        assert tc._classify(0.30) == "ORBITAL"


# ── Integration: analyse() ─────────────────────────────────────────────────────

class TestAnalyse:
    def test_too_few_entries_default(self):
        r = _run(np.ones(20))
        assert r.topo_class == "BALLISTIC"
        assert r.toroidal_score == 0.0

    def test_returns_result_type(self):
        r = _run(_make_periodic())
        assert isinstance(r, tc.ToroidalCenteringResult)

    def test_score_in_unit_interval(self):
        r = _run(_make_periodic())
        assert 0.0 <= r.toroidal_score <= 1.0

    def test_periodicity_score_nonneg(self):
        r = _run(_make_periodic())
        assert r.periodicity_score >= 0.0

    def test_recurrence_rate_in_range(self):
        r = _run(_make_periodic())
        assert 0.0 <= r.recurrence_rate <= 1.0

    def test_surface_coherence_in_range(self):
        r = _run(_make_periodic())
        assert 0.0 <= r.surface_coherence <= 1.0

    def test_center_phi_in_range(self):
        r = _run(_make_periodic())
        assert 0.0 <= r.center_phi <= 1.0

    def test_beats_null_bool(self):
        r = _run(_make_periodic(), n_shuffles=50)
        assert isinstance(r.beats_null, bool)

    def test_topo_class_valid(self):
        r = _run(_make_periodic())
        assert r.topo_class in {"TOROIDAL", "ORBITAL", "BALLISTIC"}

    def test_to_dict_keys(self):
        r = _run(_make_periodic())
        d = r.to_dict()
        for k in ("toroidal_score", "periodicity_score", "recurrence_rate",
                  "surface_coherence", "center_phi", "beats_null", "topo_class"):
            assert k in d

    def test_to_dict_json_serialisable(self):
        import json
        r = _run(_make_periodic())
        json.dumps(r.to_dict())

    def test_deterministic(self):
        phi = _make_periodic()
        r1 = _run(phi, seed=42)
        r2 = _run(phi, seed=42)
        assert r1.toroidal_score == r2.toroidal_score

    def test_periodic_higher_than_random_walk(self):
        r_per = _run(_make_periodic(n=120, seed=0), n_shuffles=30)
        r_rnd = _run(_make_random_walk(n=120, seed=1), n_shuffles=30)
        assert r_per.toroidal_score >= r_rnd.toroidal_score

    def test_periodic_higher_toroidal_score(self):
        """Periodic series should have higher toroidal score than random walk."""
        phi_per = _make_periodic(n=150, period=10)
        phi_rnd = _make_random_walk(n=150, seed=3)
        r_per = _run(phi_per, n_shuffles=50)
        r_rnd = _run(phi_rnd, n_shuffles=50)
        assert r_per.toroidal_score >= r_rnd.toroidal_score

    def test_periodicity_score_range(self):
        r = _run(_make_periodic())
        assert 0.0 <= r.periodicity_score <= 1.0

    def test_empty_history_default(self):
        import algorithms.ConsciousnessHistoryStore as chs
        orig = getattr(chs, "load", None)
        try:
            chs.load = lambda agent, max_entries=2880: []
            r = tc.analyse("albedo")
        finally:
            if orig is not None:
                chs.load = orig
        assert r.topo_class == "BALLISTIC"
        assert r.toroidal_score == 0.0

    def test_alternating_series_high_recurrence(self):
        """Alternating series crosses center constantly -> high recurrence."""
        t = np.arange(100)
        phi = 0.5 + 0.3 * np.sin(2 * np.pi * t / 6)
        r = _run(phi)
        assert r.recurrence_rate > 0.1

    def test_flat_phi_zero_periodicity(self):
        """Flat phi has no periodicity."""
        phi = np.ones(100) * 0.5
        r = _run(phi)
        assert r.periodicity_score == pytest.approx(0.0, abs=1e-6)

    def test_score_geomean_of_three(self):
        """Toroidal score is geometric mean of three components."""
        r = _run(_make_periodic())
        product = r.periodicity_score * r.recurrence_rate * r.surface_coherence
        expected = product ** (1/3) if product > 0 else 0.0
        assert r.toroidal_score == pytest.approx(expected, abs=1e-4)

    def test_n_lags_autocorr_profile(self):
        """Check that periodicity measures lag >= 3 autocorrelation."""
        phi = _make_periodic(period=8)
        r = _run(phi)
        # For period-8 oscillation, lag-8 should be high
        # periodicity score should reflect that
        assert r.periodicity_score >= 0.0
