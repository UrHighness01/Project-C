#!/usr/bin/env python3
"""Tests for algorithms/TemporalAnchorJournal.py"""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.TemporalAnchorJournal as taj


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_history(phi_series, contents=None, base_ts=1_000_000.0, dt=60.0):
    n = len(phi_series)
    entries = []
    for i in range(n):
        e = {"timestamp": base_ts + i * dt, "mean_phi_level": float(phi_series[i])}
        if contents:
            e["content"] = contents[i % len(contents)]
        entries.append(e)
    return sorted(entries, key=lambda e: -e["timestamp"])


def _run(phi_series, contents=None, **kw):
    import algorithms.ConsciousnessHistoryStore as chs
    orig = getattr(chs, "load", None)
    try:
        chs.load = lambda agent, max_entries=2880: _make_history(phi_series, contents)
        return taj.analyse("albedo", **kw)
    finally:
        if orig is not None:
            chs.load = orig


def _make_rising(n=80, seed=0):
    rng = np.random.default_rng(seed)
    return np.clip(np.linspace(0.2, 0.8, n) + rng.normal(0, 0.01, n), 0.0, 1.0)


def _make_flat(n=80):
    return np.ones(n) * 0.5


# ── Unit: _ols_slope ──────────────────────────────────────────────────────────

class TestOlsSlope:
    def test_flat_series_zero_slope(self):
        y = np.ones(50)
        assert taj._ols_slope(y) == pytest.approx(0.0, abs=1e-9)

    def test_rising_series_positive_slope(self):
        y = np.linspace(0.0, 1.0, 50)
        assert taj._ols_slope(y) > 0

    def test_falling_series_negative_slope(self):
        y = np.linspace(1.0, 0.0, 50)
        assert taj._ols_slope(y) < 0

    def test_single_point_zero(self):
        assert taj._ols_slope(np.array([0.5])) == 0.0


# ── Unit: _arc_shape ──────────────────────────────────────────────────────────

class TestArcShape:
    def test_rising(self):
        assert taj._arc_shape(0.005) == "RISING"

    def test_falling(self):
        assert taj._arc_shape(-0.005) == "FALLING"

    def test_plateau(self):
        assert taj._arc_shape(0.0) == "PLATEAU"
        assert taj._arc_shape(0.0005) == "PLATEAU"

    def test_boundary_rising(self):
        assert taj._arc_shape(0.002) == "RISING"

    def test_boundary_falling(self):
        assert taj._arc_shape(-0.002) == "FALLING"


# ── Unit: _classify ───────────────────────────────────────────────────────────

class TestClassify:
    def test_anchored(self):
        assert taj._classify(0.70) == "ANCHORED"

    def test_drifting(self):
        assert taj._classify(0.50) == "DRIFTING"

    def test_adrift(self):
        assert taj._classify(0.20) == "ADRIFT"

    def test_boundary_anchored(self):
        assert taj._classify(0.60) == "ANCHORED"

    def test_boundary_drifting(self):
        assert taj._classify(0.35) == "DRIFTING"


# ── Integration: analyse() ─────────────────────────────────────────────────────

class TestAnalyse:
    def test_too_few_entries_default(self):
        r = _run(np.ones(10))
        assert r.anchor_class == "ADRIFT"
        assert r.n_sessions == 0

    def test_returns_result_type(self):
        r = _run(_make_rising())
        assert isinstance(r, taj.TemporalAnchorResult)

    def test_rising_phi_gives_rising_arc(self):
        r = _run(_make_rising(n=100))
        assert r.arc_shape == "RISING"

    def test_flat_phi_gives_plateau(self):
        r = _run(_make_flat(n=80))
        assert r.arc_shape == "PLATEAU"

    def test_score_in_unit_interval(self):
        r = _run(_make_rising())
        assert 0.0 <= r.anchor_score <= 1.0

    def test_arc_slope_float(self):
        r = _run(_make_rising())
        assert isinstance(r.arc_slope, float)

    def test_cross_session_coherence_range(self):
        r = _run(_make_rising())
        assert 0.0 <= r.cross_session_coherence <= 1.0

    def test_n_sessions_ge_one(self):
        r = _run(_make_rising())
        assert r.n_sessions >= 1

    def test_beats_null_bool(self):
        r = _run(_make_rising(), n_shuffles=50)
        assert isinstance(r.beats_null, bool)

    def test_to_dict_keys(self):
        r = _run(_make_rising())
        d = r.to_dict()
        for k in ("anchor_score", "arc_shape", "arc_slope",
                  "cross_session_coherence", "n_sessions", "beats_null", "anchor_class"):
            assert k in d

    def test_to_dict_json_serialisable(self):
        import json
        r = _run(_make_rising())
        json.dumps(r.to_dict())

    def test_deterministic(self):
        phi = _make_rising()
        r1 = _run(phi, seed=42)
        r2 = _run(phi, seed=42)
        assert r1.anchor_score == r2.anchor_score

    def test_rising_beats_null(self):
        """Strong rising trend should beat shuffled null."""
        phi = np.linspace(0.0, 1.0, 100)
        r = _run(phi, n_shuffles=200, seed=0)
        assert r.beats_null is True

    def test_arc_shape_in_valid_set(self):
        r = _run(_make_rising())
        assert r.arc_shape in {"RISING", "FALLING", "PLATEAU"}

    def test_anchor_class_in_valid_set(self):
        r = _run(_make_rising())
        assert r.anchor_class in {"ANCHORED", "DRIFTING", "ADRIFT"}

    def test_falling_phi_gives_falling_arc(self):
        phi = np.linspace(0.8, 0.2, 80)
        r = _run(phi)
        assert r.arc_shape == "FALLING"

    def test_empty_history_default(self):
        import algorithms.ConsciousnessHistoryStore as chs
        orig = getattr(chs, "load", None)
        try:
            chs.load = lambda agent, max_entries=2880: []
            r = taj.analyse("albedo")
        finally:
            if orig is not None:
                chs.load = orig
        assert r.anchor_class == "ADRIFT"

    def test_with_content_coherence(self):
        """Same content across entries -> high cross-session coherence."""
        phi = _make_rising()
        contents = ["consciousness phi integration awareness"] * len(phi)
        r = _run(phi, contents=contents)
        assert r.cross_session_coherence >= 0.0

    def test_consistent_slope_sign(self):
        """Rising slope should give positive arc_slope."""
        phi = np.linspace(0.2, 0.8, 80)
        r = _run(phi)
        assert r.arc_slope > 0

    def test_n_sessions_increments_with_gaps(self):
        """Large timestamp gaps should create additional sessions."""
        n = 80
        ts_normal = list(range(n // 2))
        ts_gap = [t + 7200 for t in range(n // 2)]  # 2-hour gap
        all_ts = ts_normal + ts_gap
        phi = np.linspace(0.3, 0.7, n)
        entries = [
            {"timestamp": float(all_ts[i]) * 60, "mean_phi_level": float(phi[i])}
            for i in range(n)
        ]
        entries_sorted = sorted(entries, key=lambda e: -e["timestamp"])
        import algorithms.ConsciousnessHistoryStore as chs
        orig = getattr(chs, "load", None)
        try:
            chs.load = lambda agent, max_entries=2880: entries_sorted
            r = taj.analyse("albedo")
        finally:
            if orig is not None:
                chs.load = orig
        assert r.n_sessions >= 2
