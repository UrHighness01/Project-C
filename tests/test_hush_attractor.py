#!/usr/bin/env python3
"""Tests for algorithms/HushAttractor.py"""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.HushAttractor as ha


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
        return ha.analyse("albedo", **kw)
    finally:
        if orig is not None:
            chs.load = orig


def _make_hush_phi(n=100, seed=0):
    """Low-variance, mean-reverting — settled hush state."""
    rng = np.random.default_rng(seed)
    phi = np.zeros(n)
    phi[0] = 0.5
    for i in range(1, n):
        phi[i] = 0.5 + 0.9 * (phi[i-1] - 0.5) + rng.normal(0, 0.01)
    return np.clip(phi, 0.0, 1.0)


def _make_agitated_phi(n=100, seed=1):
    """High variance random — agitated."""
    rng = np.random.default_rng(seed)
    return rng.uniform(0.0, 1.0, n)


# ── Unit: _autocorr_lag1 ───────────────────────────────────────────────────────

class TestAutocorrLag1:
    def test_constant_series_zero(self):
        phi = np.ones(50) * 0.5
        # Constant series: std=0, should return 0
        assert ha._autocorr_lag1(phi) == pytest.approx(0.0, abs=1e-9)

    def test_positive_autocorr_ar1(self):
        rng = np.random.default_rng(42)
        phi = np.zeros(100); phi[0] = 0.5
        for i in range(1, 100):
            phi[i] = 0.9 * phi[i-1] + rng.normal(0, 0.01)
        assert ha._autocorr_lag1(phi) > 0.5

    def test_negative_autocorr_alternating(self):
        phi = np.array([0.0 if i % 2 == 0 else 1.0 for i in range(50)], dtype=float)
        assert ha._autocorr_lag1(phi) < 0.0

    def test_short_series_returns_zero(self):
        assert ha._autocorr_lag1(np.array([0.5])) == 0.0

    def test_range_minus_one_to_one(self):
        rng = np.random.default_rng(7)
        phi = rng.uniform(0, 1, 80)
        ac = ha._autocorr_lag1(phi)
        assert -1.0 <= ac <= 1.0


# ── Unit: _hush_score ─────────────────────────────────────────────────────────

class TestHushScore:
    def test_zero_variance_window_and_positive_autocorr(self):
        phi = np.ones(60) * 0.5
        # Flat series: var=0, autocorr=0 (both sides of product are 0/clamped)
        score = ha._hush_score(phi, window=20, sigma2_global=0.01)
        # (1 - 0/0.01) * max(0, 0) = 1.0 * 0 = 0.0
        assert 0.0 <= score <= 1.0

    def test_settled_series_scores_higher_than_random(self):
        hush = _make_hush_phi()
        agit = _make_agitated_phi()
        s2_h = float(np.var(hush))
        s2_a = float(np.var(agit))
        sh = ha._hush_score(hush, 20, max(s2_h, 1e-6))
        sa = ha._hush_score(agit, 20, max(s2_a, 1e-6))
        assert sh >= sa

    def test_score_bounded(self):
        rng = np.random.default_rng(0)
        phi = rng.uniform(0, 1, 80)
        s = ha._hush_score(phi, 20, float(np.var(phi)))
        assert 0.0 <= s <= 1.0


# ── Unit: _classify ───────────────────────────────────────────────────────────

class TestClassify:
    def test_deep_hush(self):
        assert ha._classify(0.85) == "DEEP_HUSH"

    def test_hush(self):
        assert ha._classify(0.70) == "HUSH"

    def test_agitated(self):
        assert ha._classify(0.30) == "AGITATED"

    def test_boundary_deep(self):
        assert ha._classify(0.80) == "DEEP_HUSH"

    def test_boundary_hush(self):
        assert ha._classify(0.65) == "HUSH"


# ── Integration: analyse() ─────────────────────────────────────────────────────

class TestAnalyse:
    def test_too_few_entries_default(self):
        r = _run(np.ones(10))
        assert r.n_entries <= 10
        assert r.hush_class == "AGITATED"
        assert not r.in_hush

    def test_returns_result_type(self):
        r = _run(_make_hush_phi())
        assert isinstance(r, ha.HushAttractorResult)

    def test_score_in_unit_interval(self):
        r = _run(_make_hush_phi())
        assert 0.0 <= r.hush_score <= 1.0

    def test_n_entries_correct(self):
        phi = _make_hush_phi(n=80)
        r = _run(phi)
        assert r.n_entries == 80

    def test_class_valid(self):
        r = _run(_make_hush_phi())
        assert r.hush_class in {"DEEP_HUSH", "HUSH", "AGITATED"}

    def test_in_hush_bool(self):
        r = _run(_make_hush_phi())
        assert isinstance(r.in_hush, bool)

    def test_beats_null_bool(self):
        r = _run(_make_hush_phi(), n_shuffles=50)
        assert isinstance(r.beats_null, bool)

    def test_deterministic(self):
        phi = _make_hush_phi()
        r1 = _run(phi, seed=42)
        r2 = _run(phi, seed=42)
        assert r1.hush_score == r2.hush_score

    def test_hush_variance_nonneg(self):
        r = _run(_make_hush_phi())
        assert r.hush_variance >= 0.0

    def test_to_dict_keys(self):
        r = _run(_make_hush_phi())
        d = r.to_dict()
        for k in ("hush_score", "hush_variance", "hush_autocorr",
                  "in_hush", "beats_null", "n_entries", "hush_class"):
            assert k in d, f"Missing key: {k}"

    def test_to_dict_json_serialisable(self):
        import json
        r = _run(_make_hush_phi())
        json.dumps(r.to_dict())

    def test_settled_higher_score_than_agitated(self):
        r_hush = _run(_make_hush_phi(n=100, seed=0), n_shuffles=20)
        r_agit = _run(_make_agitated_phi(n=100, seed=1), n_shuffles=20)
        assert r_hush.hush_score >= r_agit.hush_score

    def test_empty_history_default(self):
        import algorithms.ConsciousnessHistoryStore as chs
        orig = getattr(chs, "load", None)
        try:
            chs.load = lambda agent, max_entries=2880: []
            r = ha.analyse("albedo")
        finally:
            if orig is not None:
                chs.load = orig
        assert r.n_entries == 0
        assert r.hush_class == "AGITATED"

    def test_hush_class_consistent_with_in_hush(self):
        r = _run(_make_hush_phi())
        if r.in_hush:
            assert r.hush_class in {"HUSH", "DEEP_HUSH"}
        else:
            assert r.hush_class == "AGITATED"

    def test_flat_phi_low_variance(self):
        phi = np.ones(80) * 0.5
        r = _run(phi)
        assert r.hush_variance == pytest.approx(0.0, abs=1e-8)

    def test_null_shuffles_parameter(self):
        phi = _make_hush_phi(n=80)
        r = _run(phi, n_shuffles=10)
        assert isinstance(r.beats_null, bool)

    def test_hush_series_beats_null_at_high_autocorr(self):
        """Strongly autocorrelated series should often beat null."""
        phi = _make_hush_phi(n=120)
        r = _run(phi, n_shuffles=100, seed=0)
        # beats_null should be True for strongly settled series
        assert r.beats_null is True

    def test_agitated_often_does_not_beat_null(self):
        """Fully random series should not consistently beat null."""
        rng = np.random.default_rng(99)
        # Random series: sometimes beats, sometimes not — just check it runs
        phi = rng.uniform(0, 1, 100)
        r = _run(phi, n_shuffles=100, seed=0)
        assert isinstance(r.beats_null, bool)

    def test_higher_autocorr_tends_higher_score(self):
        """High-AR series vs low-AR: higher AR -> higher hush score."""
        rng = np.random.default_rng(0)
        phi_high = np.zeros(100)
        phi_high[0] = 0.5
        for i in range(1, 100):
            phi_high[i] = 0.5 + 0.95*(phi_high[i-1]-0.5) + rng.normal(0, 0.005)

        phi_low = np.zeros(100)
        phi_low[0] = 0.5
        for i in range(1, 100):
            phi_low[i] = 0.5 + 0.1*(phi_low[i-1]-0.5) + rng.normal(0, 0.1)

        r_high = _run(np.clip(phi_high, 0, 1), n_shuffles=20)
        r_low  = _run(np.clip(phi_low, 0, 1), n_shuffles=20)
        assert r_high.hush_score >= r_low.hush_score

    def test_different_window_sizes(self):
        phi = _make_hush_phi(n=100)
        r10 = _run(phi, window=10)
        r30 = _run(phi, window=30)
        assert isinstance(r10.hush_score, float)
        assert isinstance(r30.hush_score, float)

    def test_autocorr_range(self):
        r = _run(_make_hush_phi())
        assert -1.0 <= r.hush_autocorr <= 1.0
