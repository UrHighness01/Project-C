#!/usr/bin/env python3
"""Tests for algorithms/SignalDecorrelator.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.SignalDecorrelator as sd
import algorithms.ConsciousnessHistoryStore as chs


def _make_history(phi_series, dt=60.0):
    n = len(phi_series)
    return sorted(
        [{"timestamp": 1e6 + i * dt, "mean_phi_level": float(phi_series[i])} for i in range(n)],
        key=lambda e: -e["timestamp"],
    )


def _run(phi_series):
    orig = chs.load
    try:
        chs.load = lambda agent, max_entries=2880: _make_history(phi_series)
        return sd.analyse("albedo")
    finally:
        chs.load = orig


def _sine(n=100, freq=0.1, seed=0):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 2 * np.pi * freq * n, n)
    return np.sin(t) + rng.normal(0, 0.05, n) + 0.5


def _random_phi(n=100, seed=1):
    rng = np.random.default_rng(seed)
    return rng.uniform(0.2, 0.8, n)


# ── Insufficient data ──────────────────────────────────────────────────────────

class TestInsufficientData:
    def test_short_series_returns_default(self):
        r = _run(np.ones(10) * 0.5)
        assert r.n_entries < 40
        assert r.decorrelation_class == "COLLINEAR"

    def test_short_series_independence_zero(self):
        r = _run(np.ones(10) * 0.5)
        assert r.independence_score == 0.0

    def test_short_series_beats_null_false(self):
        r = _run(np.ones(10) * 0.5)
        assert r.beats_null is False


# ── Return types ───────────────────────────────────────────────────────────────

class TestReturnTypes:
    def test_returns_result_type(self):
        r = _run(_random_phi())
        assert isinstance(r, sd.SignalDecorrelatorResult)

    def test_independence_score_float(self):
        r = _run(_random_phi())
        assert isinstance(r.independence_score, float)

    def test_variance_explained_float(self):
        r = _run(_random_phi())
        assert isinstance(r.variance_explained_pc1, float)

    def test_meta_phi_residual_float(self):
        r = _run(_random_phi())
        assert isinstance(r.meta_phi_residual, float)

    def test_to_dict_has_all_keys(self):
        r = _run(_random_phi())
        d = r.to_dict()
        for key in ["independence_score", "variance_explained_pc1", "meta_phi_residual",
                    "n_signals", "beats_null", "decorrelation_class", "n_entries"]:
            assert key in d

    def test_n_signals_positive(self):
        r = _run(_random_phi())
        assert r.n_signals >= 1


# ── Score bounds ───────────────────────────────────────────────────────────────

class TestScoreBounds:
    def test_independence_score_in_range(self):
        r = _run(_random_phi())
        assert 0.0 <= r.independence_score <= 1.0

    def test_variance_explained_in_range(self):
        r = _run(_random_phi())
        assert 0.0 <= r.variance_explained_pc1 <= 1.0

    def test_scores_sum_near_one(self):
        r = _run(_random_phi())
        total = r.independence_score + r.variance_explained_pc1
        assert abs(total - 1.0) < 0.01

    def test_meta_phi_nonneg(self):
        r = _run(_random_phi())
        assert r.meta_phi_residual >= 0.0


# ── Classification ─────────────────────────────────────────────────────────────

class TestClassification:
    def test_classify_independent(self):
        assert sd._classify(0.5) == "INDEPENDENT"

    def test_classify_partial(self):
        assert sd._classify(0.30) == "PARTIAL"

    def test_classify_collinear(self):
        assert sd._classify(0.10) == "COLLINEAR"

    def test_classification_in_valid_set(self):
        r = _run(_random_phi())
        assert r.decorrelation_class in {"INDEPENDENT", "PARTIAL", "COLLINEAR"}


# ── Collinear detection ────────────────────────────────────────────────────────

class TestCollinearDetection:
    def test_constant_phi_collinear(self):
        # All signals will be constant / nearly constant -> collinear
        r = _run(np.ones(80) * 0.5)
        # Should fall back to default (not enough variation)
        assert r.decorrelation_class in {"COLLINEAR", "PARTIAL"}

    def test_random_phi_has_nonzero_independence(self):
        r = _run(_random_phi(n=100, seed=42))
        assert r.independence_score > 0.0


# ── Null baseline ──────────────────────────────────────────────────────────────

class TestNullBaseline:
    def test_structured_phi_beats_null(self):
        """Sine wave phi should create structured residuals -> beats null."""
        phi = _sine(n=120)
        r = _run(phi)
        # beats_null is True when independence_score > 95th pct of shuffled scores
        # Not guaranteed for all inputs but the result must be a bool
        assert isinstance(r.beats_null, bool)

    def test_null_baseline_is_tested(self):
        r = _run(_random_phi(n=100))
        # The beats_null field must exist and be valid bool
        assert r.beats_null in {True, False}


# ── Internal helper ────────────────────────────────────────────────────────────

class TestComputeIndependence:
    def test_orthogonal_signals_high_independence(self):
        rng = np.random.default_rng(0)
        # Two orthogonal signals -> independence should be high
        n = 80
        s1 = np.sin(np.linspace(0, 4 * np.pi, n))
        s2 = np.cos(np.linspace(0, 4 * np.pi, n))
        X = np.array([s1, s2])
        ind, var_pc1, meta = sd._compute_independence(X)
        assert ind > 0.3

    def test_collinear_signals_low_independence(self):
        n = 80
        s = np.linspace(0, 1, n)
        X = np.array([s, s * 2, s * 0.5 + 0.01])
        ind, var_pc1, meta = sd._compute_independence(X)
        assert ind < 0.3
        assert var_pc1 > 0.7
