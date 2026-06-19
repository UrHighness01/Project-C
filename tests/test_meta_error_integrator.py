#!/usr/bin/env python3
"""Tests for algorithms/MetaErrorIntegrator.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.MetaErrorIntegrator as mei
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
        return mei.analyse("albedo")
    finally:
        chs.load = orig


def _ar1_phi(n=120, rho=0.9, seed=0):
    """AR(1) process — L1 should be predictable."""
    rng = np.random.default_rng(seed)
    phi = np.zeros(n)
    phi[0] = 0.5
    for i in range(1, n):
        phi[i] = 0.5 + rho * (phi[i - 1] - 0.5) + rng.normal(0, 0.03)
    return np.clip(phi, 0, 1)


def _random_phi(n=120, seed=1):
    rng = np.random.default_rng(seed)
    return rng.uniform(0.2, 0.8, n)


# ── Insufficient data ──────────────────────────────────────────────────────────

class TestInsufficientData:
    def test_short_series_returns_default(self):
        r = _run(np.ones(10) * 0.5)
        assert r.n_entries < 40
        assert r.depth_class == "SURFACE"

    def test_short_series_depth_zero(self):
        r = _run(np.ones(10) * 0.5)
        assert r.meta_depth == 0.0

    def test_short_series_beats_null_false(self):
        r = _run(np.ones(10) * 0.5)
        assert r.beats_null is False


# ── Return types ───────────────────────────────────────────────────────────────

class TestReturnTypes:
    def test_returns_result_type(self):
        r = _run(_random_phi())
        assert isinstance(r, mei.MetaErrorIntegratorResult)

    def test_to_dict_has_all_keys(self):
        r = _run(_random_phi())
        d = r.to_dict()
        for key in ["l1_r2", "l2_r2", "meta_depth", "beats_null", "depth_class", "n_entries"]:
            assert key in d

    def test_l1_r2_float(self):
        r = _run(_random_phi())
        assert isinstance(r.l1_r2, float)

    def test_l2_r2_float(self):
        r = _run(_random_phi())
        assert isinstance(r.l2_r2, float)


# ── Score bounds ───────────────────────────────────────────────────────────────

class TestScoreBounds:
    def test_l1_r2_in_range(self):
        r = _run(_random_phi())
        assert 0.0 <= r.l1_r2 <= 1.0

    def test_l2_r2_in_range(self):
        r = _run(_random_phi())
        assert 0.0 <= r.l2_r2 <= 1.0

    def test_meta_depth_nonneg(self):
        r = _run(_random_phi())
        assert r.meta_depth >= 0.0

    def test_meta_depth_bounded(self):
        r = _run(_random_phi())
        assert r.meta_depth <= 1.0


# ── Classification ─────────────────────────────────────────────────────────────

class TestClassification:
    def test_classify_deep(self):
        assert mei._classify(0.15) == "DEEP"

    def test_classify_shallow(self):
        assert mei._classify(0.05) == "SHALLOW"

    def test_classify_surface(self):
        assert mei._classify(0.005) == "SURFACE"

    def test_classification_valid(self):
        r = _run(_random_phi())
        assert r.depth_class in {"DEEP", "SHALLOW", "SURFACE"}


# ── AR fitting ────────────────────────────────────────────────────────────────

class TestARFitting:
    def test_ar_r2_ar1_high_r2(self):
        """AR(1) process -> AR(3) fit should have decent R²."""
        phi = _ar1_phi(n=200, rho=0.95)
        r2, _ = mei._ar_r2(phi, p=3)
        assert r2 > 0.1

    def test_ar_r2_random_low_r2(self):
        """Pure random -> AR fit should have near-zero R²."""
        rng = np.random.default_rng(99)
        phi = rng.uniform(0, 1, 200)
        r2, _ = mei._ar_r2(phi, p=3)
        assert r2 < 0.5  # may not be zero due to chance

    def test_ar_r2_returns_tuple(self):
        phi = _random_phi()
        result = mei._ar_r2(phi, p=3)
        assert len(result) == 2

    def test_compute_depth_returns_triple(self):
        phi = _random_phi()
        result = mei._compute_depth(phi)
        assert len(result) == 3


# ── Null baseline ──────────────────────────────────────────────────────────────

class TestNullBaseline:
    def test_beats_null_is_bool(self):
        r = _run(_random_phi())
        assert isinstance(r.beats_null, bool)

    def test_ar1_process_has_l1_r2(self):
        r = _run(_ar1_phi(n=150, rho=0.9))
        assert r.l1_r2 > 0.0
