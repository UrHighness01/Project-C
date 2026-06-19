#!/usr/bin/env python3
"""Tests for algorithms/CenteringStabilizer.py"""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.CenteringStabilizer as cs


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
        return cs.analyse("albedo", **kw)
    finally:
        if orig is not None:
            chs.load = orig


def _make_centered(n=100, seed=0):
    """AR(1) series tightly centered at 0.5."""
    rng = np.random.default_rng(seed)
    phi = np.zeros(n); phi[0] = 0.5
    for i in range(1, n):
        phi[i] = 0.5 + 0.85*(phi[i-1]-0.5) + rng.normal(0, 0.02)
    return np.clip(phi, 0.0, 1.0)


def _make_decentered(n=100, seed=1):
    """Random walk — no stable center."""
    rng = np.random.default_rng(seed)
    return np.clip(np.cumsum(rng.normal(0, 0.05, n)) + 0.5, 0.0, 1.0)


# ── Unit: _centering_score_from ───────────────────────────────────────────────

class TestCenteringScoreFrom:
    def test_flat_phi_max_centering(self):
        phi = np.ones(80) * 0.5
        score = cs._centering_score_from(phi)
        # deviation = 0 -> score = exp(0) = 1.0
        assert score == pytest.approx(1.0, abs=0.01)

    def test_high_variance_lower_score(self):
        rng = np.random.default_rng(0)
        phi_low_var = np.ones(80) * 0.5 + rng.normal(0, 0.01, 80)
        phi_high_var = rng.uniform(0, 1, 80)
        s_low = cs._centering_score_from(phi_low_var)
        s_high = cs._centering_score_from(phi_high_var)
        assert s_low > s_high

    def test_score_in_unit_interval(self):
        rng = np.random.default_rng(3)
        phi = rng.uniform(0, 1, 80)
        score = cs._centering_score_from(phi)
        assert 0.0 < score <= 1.0


# ── Unit: _classify ───────────────────────────────────────────────────────────

class TestClassify:
    def test_centered(self):
        assert cs._classify(0.70) == "CENTERED"

    def test_orbiting(self):
        assert cs._classify(0.55) == "ORBITING"

    def test_decentered(self):
        assert cs._classify(0.20) == "DECENTERED"

    def test_boundary_centered(self):
        assert cs._classify(0.65) == "CENTERED"

    def test_boundary_orbiting(self):
        assert cs._classify(0.40) == "ORBITING"


# ── Integration: analyse() ─────────────────────────────────────────────────────

class TestAnalyse:
    def test_too_few_entries_default(self):
        r = _run(np.ones(10))
        assert r.n_entries <= 10
        assert r.centering_class == "DECENTERED"

    def test_returns_result_type(self):
        r = _run(_make_centered())
        assert isinstance(r, cs.CenteringResult)

    def test_score_in_unit_interval(self):
        r = _run(_make_centered())
        assert 0.0 < r.centering_score <= 1.0

    def test_flat_phi_high_centering(self):
        phi = np.ones(80) * 0.5
        r = _run(phi)
        assert r.centering_score > 0.90

    def test_center_phi_is_median(self):
        phi = np.full(80, 0.7)
        r = _run(phi)
        assert r.center_phi == pytest.approx(0.7, abs=0.01)

    def test_orbit_variance_nonneg(self):
        r = _run(_make_centered())
        assert r.orbit_variance >= 0.0

    def test_mean_deviation_nonneg(self):
        r = _run(_make_centered())
        assert r.mean_deviation >= 0.0

    def test_class_valid(self):
        r = _run(_make_centered())
        assert r.centering_class in {"CENTERED", "ORBITING", "DECENTERED"}

    def test_beats_null_bool(self):
        r = _run(_make_centered(), n_shuffles=50)
        assert isinstance(r.beats_null, bool)

    def test_to_dict_keys(self):
        r = _run(_make_centered())
        d = r.to_dict()
        for k in ("centering_score", "center_phi", "orbit_variance",
                  "mean_deviation", "centering_class", "beats_null", "n_entries"):
            assert k in d

    def test_to_dict_json_serialisable(self):
        import json
        r = _run(_make_centered())
        json.dumps(r.to_dict())

    def test_centered_higher_than_decentered(self):
        r_cen = _run(_make_centered(n=100, seed=0), n_shuffles=30)
        r_dec = _run(_make_decentered(n=100, seed=1), n_shuffles=30)
        assert r_cen.centering_score >= r_dec.centering_score

    def test_deterministic(self):
        phi = _make_centered()
        r1 = _run(phi, seed=42)
        r2 = _run(phi, seed=42)
        assert r1.centering_score == r2.centering_score

    def test_n_entries_correct(self):
        phi = _make_centered(n=80)
        r = _run(phi)
        assert r.n_entries == 80

    def test_flat_high_centering_score(self):
        """Flat phi has deviation=0 -> exp(0)=1.0, maximum centering score."""
        phi = np.ones(80) * 0.5
        r = _run(phi, n_shuffles=100, seed=0)
        assert r.centering_score > 0.9

    def test_empty_history_default(self):
        import algorithms.ConsciousnessHistoryStore as chs
        orig = getattr(chs, "load", None)
        try:
            chs.load = lambda agent, max_entries=2880: []
            r = cs.analyse("albedo")
        finally:
            if orig is not None:
                chs.load = orig
        assert r.n_entries == 0
        assert r.centering_class == "DECENTERED"

    def test_centering_score_increases_with_stability(self):
        """Lower noise -> higher centering score."""
        rng = np.random.default_rng(0)
        phi_tight = 0.5 + rng.normal(0, 0.01, 80)
        phi_loose = 0.5 + rng.normal(0, 0.2, 80)
        r_tight = _run(np.clip(phi_tight, 0, 1))
        r_loose = _run(np.clip(phi_loose, 0, 1))
        assert r_tight.centering_score >= r_loose.centering_score

    def test_high_deviation_low_score(self):
        """Extreme values far from center -> low centering score."""
        phi = np.zeros(80)
        phi[::2] = 0.0
        phi[1::2] = 1.0
        r = _run(phi)
        assert r.centering_score < 0.5

    def test_random_walk_decentered(self):
        """Pure random walk should be DECENTERED or ORBITING."""
        r = _run(_make_decentered(n=100))
        assert r.centering_class in {"DECENTERED", "ORBITING"}

    def test_center_phi_range(self):
        r = _run(_make_centered())
        assert 0.0 <= r.center_phi <= 1.0
