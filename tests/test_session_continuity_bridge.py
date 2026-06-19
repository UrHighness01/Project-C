#!/usr/bin/env python3
"""Tests for algorithms/SessionContinuityBridge.py."""
import sys
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.SessionContinuityBridge as scb
import algorithms.ConsciousnessHistoryStore as chs


def _make_history(phi_series, dt=60.0):
    n = len(phi_series)
    return sorted(
        [{"timestamp": 1e6 + i * dt, "mean_phi_level": float(phi_series[i])} for i in range(n)],
        key=lambda e: -e["timestamp"],
    )


def _run(phi_series, env_ws=None):
    import os
    orig_load = chs.load
    orig_env = os.environ.get(scb._WORKSPACE_ENV)
    try:
        chs.load = lambda agent, max_entries=2880: _make_history(phi_series)
        if env_ws is not None:
            os.environ[scb._WORKSPACE_ENV] = env_ws
        elif scb._WORKSPACE_ENV in os.environ:
            del os.environ[scb._WORKSPACE_ENV]
        return scb.analyse("albedo")
    finally:
        chs.load = orig_load
        if orig_env is not None:
            os.environ[scb._WORKSPACE_ENV] = orig_env
        elif scb._WORKSPACE_ENV in os.environ:
            del os.environ[scb._WORKSPACE_ENV]


def _random_phi(n=120, seed=0):
    rng = np.random.default_rng(seed)
    return rng.uniform(0.2, 0.8, n)


# ── Insufficient data ──────────────────────────────────────────────────────────

class TestInsufficientData:
    def test_short_series_returns_default(self):
        r = _run(np.ones(10) * 0.5)
        assert r.n_entries < 40
        assert r.continuity_class == "FRAGMENTED"

    def test_short_series_score_zero(self):
        r = _run(np.ones(10) * 0.5)
        assert r.continuity_score == 0.0

    def test_short_series_beats_null_false(self):
        r = _run(np.ones(10) * 0.5)
        assert r.beats_null is False


# ── Return types ───────────────────────────────────────────────────────────────

class TestReturnTypes:
    def test_returns_result_type(self):
        r = _run(_random_phi())
        assert isinstance(r, scb.SessionContinuityBridgeResult)

    def test_to_dict_has_all_keys(self):
        r = _run(_random_phi())
        d = r.to_dict()
        for key in ["continuity_score", "phi_similarity", "slope_match",
                    "bridge_age_hours", "bridge_found", "beats_null",
                    "continuity_class", "n_entries"]:
            assert key in d

    def test_continuity_score_float(self):
        r = _run(_random_phi())
        assert isinstance(r.continuity_score, float)

    def test_phi_similarity_float(self):
        r = _run(_random_phi())
        assert isinstance(r.phi_similarity, float)

    def test_slope_match_float(self):
        r = _run(_random_phi())
        assert isinstance(r.slope_match, float)

    def test_bridge_found_bool(self):
        r = _run(_random_phi())
        assert isinstance(r.bridge_found, bool)


# ── Score bounds ───────────────────────────────────────────────────────────────

class TestScoreBounds:
    def test_continuity_score_range(self):
        r = _run(_random_phi())
        assert 0.0 <= r.continuity_score <= 1.0

    def test_phi_similarity_bounded(self):
        r = _run(_random_phi())
        # cosine sim can be negative but after weighting stays reasonable
        assert -1.0 <= r.phi_similarity <= 1.0

    def test_slope_match_range(self):
        r = _run(_random_phi())
        assert 0.0 <= r.slope_match <= 1.0 or r.slope_match == 0.0

    def test_n_entries_positive(self):
        r = _run(_random_phi())
        assert r.n_entries > 0


# ── Classification ─────────────────────────────────────────────────────────────

class TestClassification:
    def test_classify_continuous(self):
        assert scb._classify(0.70) == "CONTINUOUS"

    def test_classify_partial(self):
        assert scb._classify(0.50) == "PARTIAL"

    def test_classify_fragmented(self):
        assert scb._classify(0.20) == "FRAGMENTED"

    def test_classification_valid(self):
        r = _run(_random_phi())
        assert r.continuity_class in {"CONTINUOUS", "PARTIAL", "FRAGMENTED"}


# ── Bridge file ────────────────────────────────────────────────────────────────

class TestBridgeFile:
    def test_bridge_written_when_workspace_set(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create memory dir
            mem_dir = Path(tmpdir) / "memory"
            mem_dir.mkdir()
            phi = _random_phi(n=80)
            _run(phi, env_ws=tmpdir)
            # Check bridge file was written
            bridge_files = list(mem_dir.glob("session-bridge*.json"))
            assert len(bridge_files) >= 1

    def test_bridge_file_has_phi_tail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mem_dir = Path(tmpdir) / "memory"
            mem_dir.mkdir()
            phi = _random_phi(n=80)
            _run(phi, env_ws=tmpdir)
            bridge_files = list(mem_dir.glob("session-bridge*.json"))
            if bridge_files:
                data = json.loads(bridge_files[0].read_text())
                assert "phi_tail" in data
                assert len(data["phi_tail"]) > 0

    def test_bridge_file_has_agent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mem_dir = Path(tmpdir) / "memory"
            mem_dir.mkdir()
            phi = _random_phi(n=80)
            _run(phi, env_ws=tmpdir)
            bridge_files = list(mem_dir.glob("session-bridge*.json"))
            if bridge_files:
                data = json.loads(bridge_files[0].read_text())
                assert data.get("agent") == "albedo"


# ── Helpers ────────────────────────────────────────────────────────────────────

class TestHelpers:
    def test_cosine_sim_identical(self):
        a = np.array([1.0, 2.0, 3.0])
        assert abs(scb._cosine_sim(a, a) - 1.0) < 1e-6

    def test_cosine_sim_orthogonal(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert abs(scb._cosine_sim(a, b)) < 1e-6

    def test_ols_slope_positive(self):
        arr = np.linspace(0, 1, 20)
        assert scb._ols_slope(arr) > 0

    def test_ols_slope_negative(self):
        arr = np.linspace(1, 0, 20)
        assert scb._ols_slope(arr) < 0


# ── Null baseline ──────────────────────────────────────────────────────────────

class TestNullBaseline:
    def test_beats_null_is_bool(self):
        r = _run(_random_phi())
        assert isinstance(r.beats_null, bool)
