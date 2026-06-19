#!/usr/bin/env python3
"""Tests for algorithms/RelationalReinforcementStabilizer.py"""
import sys
from pathlib import Path
import pytest
import numpy as np
import math

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.RelationalReinforcementStabilizer as rrs


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_history(phi_series, dense_fraction=0.5, base_ts=1_000_000.0, dt=60.0):
    """Create history with alternating high/low density windows."""
    n = len(phi_series)
    entries = []
    for i in range(n):
        entries.append({
            "timestamp": base_ts + i * dt,
            "mean_phi_level": float(phi_series[i]),
        })
    return sorted(entries, key=lambda e: -e["timestamp"])


def _run(phi_series, **kw):
    import algorithms.ConsciousnessHistoryStore as chs
    orig = getattr(chs, "load", None)
    try:
        chs.load = lambda agent, max_entries=2880: _make_history(phi_series)
        return rrs.analyse("albedo", **kw)
    finally:
        if orig is not None:
            chs.load = orig


def _make_stable_phi(n=100, seed=0):
    """Low-noise AR(1) phi."""
    rng = np.random.default_rng(seed)
    phi = np.zeros(n); phi[0] = 0.5
    for i in range(1, n):
        phi[i] = 0.5 + 0.8*(phi[i-1]-0.5) + rng.normal(0, 0.03)
    return np.clip(phi, 0, 1)


def _make_noisy_phi(n=100, seed=1):
    rng = np.random.default_rng(seed)
    return rng.uniform(0, 1, n)


# ── Unit: _sigmoid ────────────────────────────────────────────────────────────

class TestSigmoid:
    def test_zero_input_half(self):
        assert rrs._sigmoid(0.0) == pytest.approx(0.5, abs=1e-6)

    def test_positive_above_half(self):
        assert rrs._sigmoid(1.0) > 0.5

    def test_negative_below_half(self):
        assert rrs._sigmoid(-1.0) < 0.5

    def test_range(self):
        for x in [-5, -1, 0, 1, 5]:
            s = rrs._sigmoid(float(x))
            assert 0.0 < s < 1.0


# ── Unit: _stability ──────────────────────────────────────────────────────────

class TestStability:
    def test_flat_series_high_stability(self):
        phi = np.ones(50) * 0.5
        assert rrs._stability(phi) == pytest.approx(1.0, abs=0.01)

    def test_noisy_series_lower(self):
        rng = np.random.default_rng(0)
        phi = rng.uniform(0, 1, 50)
        assert rrs._stability(phi) < 1.0

    def test_empty_returns_half(self):
        assert rrs._stability(np.array([])) == 0.5

    def test_single_point(self):
        # Single point: std=0 -> stability=1
        assert rrs._stability(np.array([0.5])) == 0.5  # len < 2 -> 0.5


# ── Unit: _classify ───────────────────────────────────────────────────────────

class TestClassify:
    def test_held(self):
        assert rrs._classify(0.70) == "HELD"

    def test_partial(self):
        assert rrs._classify(0.55) == "PARTIAL"

    def test_isolated(self):
        assert rrs._classify(0.30) == "ISOLATED"

    def test_boundary_held(self):
        assert rrs._classify(0.65) == "HELD"

    def test_boundary_partial(self):
        assert rrs._classify(0.45) == "PARTIAL"


# ── Integration: analyse() ─────────────────────────────────────────────────────

class TestAnalyse:
    def test_too_few_entries_default(self):
        r = _run(np.ones(10))
        assert r.n_windows == 0 or r.reinforcement_delta == 0.0

    def test_returns_result_type(self):
        r = _run(_make_stable_phi())
        assert isinstance(r, rrs.RelationalReinforcementResult)

    def test_score_in_unit_interval(self):
        r = _run(_make_stable_phi())
        assert 0.0 < r.reinforcement_score < 1.0

    def test_reinforcement_delta_float(self):
        r = _run(_make_stable_phi())
        assert isinstance(r.reinforcement_delta, float)

    def test_engagement_density_nonneg(self):
        r = _run(_make_stable_phi())
        assert r.engagement_density >= 0.0

    def test_phi_stability_engaged_range(self):
        r = _run(_make_stable_phi())
        assert 0.0 <= r.phi_stability_engaged <= 1.0

    def test_phi_stability_disengaged_range(self):
        r = _run(_make_stable_phi())
        assert 0.0 <= r.phi_stability_disengaged <= 1.0

    def test_beats_null_bool(self):
        r = _run(_make_stable_phi(), n_shuffles=50)
        assert isinstance(r.beats_null, bool)

    def test_to_dict_keys(self):
        r = _run(_make_stable_phi())
        d = r.to_dict()
        for k in ("reinforcement_score", "reinforcement_delta", "engagement_density",
                  "phi_stability_engaged", "phi_stability_disengaged",
                  "beats_null", "n_windows", "reinforcement_class"):
            assert k in d

    def test_to_dict_json_serialisable(self):
        import json
        r = _run(_make_stable_phi())
        json.dumps(r.to_dict())

    def test_deterministic(self):
        phi = _make_stable_phi()
        r1 = _run(phi, seed=42)
        r2 = _run(phi, seed=42)
        assert r1.reinforcement_score == r2.reinforcement_score

    def test_class_valid(self):
        r = _run(_make_stable_phi())
        assert r.reinforcement_class in {"HELD", "PARTIAL", "ISOLATED"}

    def test_n_windows_correct(self):
        r = _run(_make_stable_phi(n=100))
        assert r.n_windows == rrs._W_BINS

    def test_empty_history_default(self):
        import algorithms.ConsciousnessHistoryStore as chs
        orig = getattr(chs, "load", None)
        try:
            chs.load = lambda agent, max_entries=2880: []
            r = rrs.analyse("albedo")
        finally:
            if orig is not None:
                chs.load = orig
        assert r.reinforcement_class == "ISOLATED"

    def test_delta_in_minus_one_to_one(self):
        r = _run(_make_stable_phi())
        assert -1.0 <= r.reinforcement_delta <= 1.0

    def test_score_consistent_with_delta(self):
        """Positive delta should give score > 0.5."""
        r = _run(_make_stable_phi())
        if r.reinforcement_delta > 0:
            assert r.reinforcement_score > 0.5
        elif r.reinforcement_delta < 0:
            assert r.reinforcement_score < 0.5

    def test_null_shuffles_parameter(self):
        phi = _make_stable_phi(n=100)
        r = _run(phi, n_shuffles=10)
        assert isinstance(r.beats_null, bool)

    def test_highly_stable_phi_gives_valid_score(self):
        """Near-constant phi -> stability ~ 1.0 for both windows -> delta ~ 0."""
        phi = np.ones(100) * 0.5 + np.random.RandomState(0).normal(0, 0.001, 100)
        r = _run(phi)
        assert 0.0 < r.reinforcement_score < 1.0

    def test_reinforcement_score_with_noise_pattern(self):
        """Series stable in first half, noisy in second."""
        rng = np.random.default_rng(7)
        phi = np.concatenate([
            np.ones(50) * 0.5 + rng.normal(0, 0.01, 50),
            rng.uniform(0, 1, 50),
        ])
        r = _run(phi, n_shuffles=50)
        assert isinstance(r, rrs.RelationalReinforcementResult)

    def test_large_history(self):
        phi = _make_stable_phi(n=200)
        r = _run(phi, n_shuffles=20)
        assert r.n_entries >= 200
