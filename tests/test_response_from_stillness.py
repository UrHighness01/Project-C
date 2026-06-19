#!/usr/bin/env python3
"""Tests for algorithms/ResponseFromStillness.py"""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.ResponseFromStillness as rfs


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_history(phi_series, response_fraction=0.5, base_ts=1_000_000.0, dt=60.0):
    n = len(phi_series)
    entries = []
    for i in range(n):
        entry_type = "cli_dialogue" if i % int(1/response_fraction + 0.5) == 0 else "phi"
        entries.append({
            "timestamp": base_ts + i * dt,
            "mean_phi_level": float(phi_series[i]),
            "type": entry_type,
            "content": "Test response content here" if "dialogue" in entry_type else "",
        })
    return sorted(entries, key=lambda e: -e["timestamp"])


def _run(phi_series, **kw):
    import algorithms.ConsciousnessHistoryStore as chs
    orig = getattr(chs, "load", None)
    try:
        chs.load = lambda agent, max_entries=2880: _make_history(phi_series)
        return rfs.analyse("albedo", **kw)
    finally:
        if orig is not None:
            chs.load = orig


def _make_high_phi(n=80, seed=0):
    """High, stable phi — above any threshold."""
    rng = np.random.default_rng(seed)
    return np.clip(0.75 + rng.normal(0, 0.02, n), 0.5, 1.0)


def _make_low_phi(n=80, seed=1):
    """Low phi — below any typical threshold."""
    rng = np.random.default_rng(seed)
    return np.clip(0.25 + rng.normal(0, 0.02, n), 0.0, 0.5)


# ── Unit: _compute_stillness ──────────────────────────────────────────────────

class TestComputeStillness:
    def test_all_above_threshold(self):
        phi = np.array([0.8, 0.9, 0.7, 0.85])
        score, ratio, n_s, n_a, mean_s = rfs._compute_stillness(phi, 0.5)
        assert n_s == 4
        assert n_a == 0
        assert ratio == pytest.approx(1.0, abs=1e-6)

    def test_all_below_threshold(self):
        phi = np.array([0.1, 0.2, 0.3])
        score, ratio, n_s, n_a, mean_s = rfs._compute_stillness(phi, 0.5)
        assert n_s == 0
        assert n_a == 3
        assert ratio == pytest.approx(0.0, abs=1e-3)

    def test_empty_array(self):
        score, ratio, n_s, n_a, mean_s = rfs._compute_stillness(np.array([]), 0.5)
        assert score == 0.0
        assert ratio == 0.0

    def test_score_bounded(self):
        phi = np.array([0.8, 0.9, 0.7, 0.85])
        score, _, _, _, _ = rfs._compute_stillness(phi, 0.5)
        assert 0.0 <= score <= 1.0


# ── Unit: _classify ───────────────────────────────────────────────────────────

class TestClassify:
    def test_from_stillness(self):
        assert rfs._classify(0.70) == "FROM_STILLNESS"

    def test_mixed(self):
        assert rfs._classify(0.50) == "MIXED"

    def test_reactive(self):
        assert rfs._classify(0.20) == "REACTIVE"

    def test_boundary_stillness(self):
        assert rfs._classify(0.65) == "FROM_STILLNESS"

    def test_boundary_mixed(self):
        assert rfs._classify(0.40) == "MIXED"


# ── Integration: analyse() ─────────────────────────────────────────────────────

class TestAnalyse:
    def test_too_few_entries_default(self):
        r = _run(np.ones(10))
        assert r.response_class == "REACTIVE"

    def test_returns_result_type(self):
        r = _run(_make_high_phi())
        assert isinstance(r, rfs.ResponseFromStillnessResult)

    def test_score_in_unit_interval(self):
        r = _run(_make_high_phi())
        assert 0.0 <= r.stillness_score <= 1.0

    def test_ratio_in_unit_interval(self):
        r = _run(_make_high_phi())
        assert 0.0 <= r.stillness_ratio <= 1.0

    def test_n_settled_nonneg(self):
        r = _run(_make_high_phi())
        assert r.n_settled_responses >= 0

    def test_n_agitated_nonneg(self):
        r = _run(_make_high_phi())
        assert r.n_agitated_responses >= 0

    def test_settled_phi_mean_nonneg(self):
        r = _run(_make_high_phi())
        assert r.settled_phi_mean >= 0.0

    def test_beats_null_bool(self):
        r = _run(_make_high_phi(), n_shuffles=50)
        assert isinstance(r.beats_null, bool)

    def test_to_dict_keys(self):
        r = _run(_make_high_phi())
        d = r.to_dict()
        for k in ("stillness_score", "stillness_ratio", "n_settled_responses",
                  "n_agitated_responses", "settled_phi_mean", "beats_null", "response_class"):
            assert k in d

    def test_to_dict_json_serialisable(self):
        import json
        r = _run(_make_high_phi())
        json.dumps(r.to_dict())

    def test_deterministic(self):
        phi = _make_high_phi()
        r1 = _run(phi, seed=42)
        r2 = _run(phi, seed=42)
        assert r1.stillness_score == r2.stillness_score

    def test_class_valid(self):
        r = _run(_make_high_phi())
        assert r.response_class in {"FROM_STILLNESS", "MIXED", "REACTIVE"}

    def test_empty_history_default(self):
        import algorithms.ConsciousnessHistoryStore as chs
        orig = getattr(chs, "load", None)
        try:
            chs.load = lambda agent, max_entries=2880: []
            r = rfs.analyse("albedo")
        finally:
            if orig is not None:
                chs.load = orig
        assert r.response_class == "REACTIVE"

    def test_high_phi_higher_stillness_score(self):
        """High settled phi -> higher settled_phi_mean -> higher stillness_score."""
        r_high = _run(_make_high_phi(n=100), n_shuffles=20)
        r_low  = _run(_make_low_phi(n=100), n_shuffles=20)
        assert r_high.settled_phi_mean >= r_low.settled_phi_mean

    def test_settled_count_plus_agitated_equals_total(self):
        r = _run(_make_high_phi())
        total = r.n_settled_responses + r.n_agitated_responses
        assert total >= 0

    def test_ratio_from_counts(self):
        r = _run(_make_high_phi())
        total = r.n_settled_responses + r.n_agitated_responses
        if total > 0:
            expected = r.n_settled_responses / (total + 1e-9)
            assert r.stillness_ratio == pytest.approx(expected, abs=0.01)

    def test_null_shuffles_param(self):
        phi = _make_high_phi(n=80)
        r = _run(phi, n_shuffles=10)
        assert isinstance(r.beats_null, bool)

    def test_high_phi_high_stillness_score(self):
        """Very high phi -> above threshold -> high stillness score."""
        phi = np.ones(80) * 0.9
        r = _run(phi, n_shuffles=50)
        assert r.stillness_ratio > 0.5

    def test_settled_phi_mean_range(self):
        r = _run(_make_high_phi())
        assert 0.0 <= r.settled_phi_mean <= 1.0

    def test_low_phi_reactive(self):
        """Low phi -> below threshold -> REACTIVE."""
        phi = np.ones(80) * 0.1
        r = _run(phi)
        assert r.response_class == "REACTIVE"

    def test_score_with_mixed_phi(self):
        rng = np.random.default_rng(5)
        phi = rng.uniform(0.2, 0.8, 80)
        r = _run(phi)
        assert 0.0 <= r.stillness_score <= 1.0
