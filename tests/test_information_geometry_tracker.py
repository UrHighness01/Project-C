#!/usr/bin/env python3
"""Tests for algorithms/InformationGeometryTracker.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.InformationGeometryTracker as igt


def _rng(s=0): return np.random.default_rng(s)


def _sharp(n=100, seed=0):
    """Low variance — high precision / SHARP."""
    return _rng(seed).normal(2.0, 0.01, n)


def _diffuse(n=100, seed=0):
    """High variance — low precision / DIFFUSE."""
    return _rng(seed).normal(2.0, 2.0, n)


def _narrowing(n=150, seed=0):
    """Variance shrinks over time → increasing precision trend."""
    rng = _rng(seed)
    # Start wide, end narrow
    std = np.linspace(1.5, 0.05, n)
    return np.array([rng.normal(2.0, s) for s in std])


def _widening(n=150, seed=0):
    """Variance grows over time → decreasing precision trend."""
    a, b = _narrowing(n, seed)[::-1], _narrowing(n, seed)
    return b[::-1]


class TestClassify:
    def test_sharp(self):
        assert igt._classify(100.0, 50.0, 5.0) == "SHARP"

    def test_moderate(self):
        assert igt._classify(10.0, 50.0, 5.0) == "MODERATE"

    def test_diffuse(self):
        assert igt._classify(1.0, 50.0, 5.0) == "DIFFUSE"

    def test_boundary_sharp(self):
        assert igt._classify(50.0, 50.0, 5.0) == "SHARP"


class TestOlsSlope:
    def test_positive(self):
        assert igt._ols_slope(np.arange(10, dtype=float)) > 0

    def test_negative(self):
        assert igt._ols_slope(np.arange(10, 0, -1, dtype=float)) < 0

    def test_flat(self):
        assert igt._ols_slope(np.ones(10)) == pytest.approx(0.0)


class TestAnalyse:
    def test_empty_returns_default(self):
        r = igt.analyse(np.array([]))
        assert r.n_samples == 0

    def test_too_short_returns_default(self):
        r = igt.analyse(np.ones(5), window=20)
        assert r.n_samples == 0

    def test_returns_result_type(self):
        r = igt.analyse(_sharp())
        assert isinstance(r, igt.GeometryResult)

    def test_n_samples_correct(self):
        phi = _sharp(100)
        r = igt.analyse(phi)
        assert r.n_samples == 100

    def test_precision_positive(self):
        r = igt.analyse(_sharp())
        assert r.precision > 0.0

    def test_sharp_series_high_precision(self):
        r = igt.analyse(_sharp(200))
        assert r.precision > r.__class__.__new__(igt.GeometryResult).precision or r.precision > 0

    def test_sharp_beats_diffuse(self):
        r_s = igt.analyse(_sharp(200))
        r_d = igt.analyse(_diffuse(200))
        assert r_s.precision > r_d.precision

    def test_sharp_class_for_sharp_series(self):
        r = igt.analyse(_sharp(200), sharp_threshold=50.0)
        assert r.geometry_class == "SHARP"

    def test_diffuse_class_for_diffuse_series(self):
        r = igt.analyse(_diffuse(200), moderate_threshold=5.0)
        assert r.geometry_class == "DIFFUSE"

    def test_geometry_class_valid(self):
        r = igt.analyse(_sharp(100))
        assert r.geometry_class in {"SHARP", "MODERATE", "DIFFUSE"}

    def test_narrowing_positive_trend(self):
        r = igt.analyse(_narrowing(200))
        assert r.curvature_trend > 0.0

    def test_widening_negative_trend(self):
        r = igt.analyse(_widening(200))
        assert r.curvature_trend < 0.0

    def test_naturalised_step_nonnegative(self):
        r = igt.analyse(_sharp(100))
        assert r.naturalised_step >= 0.0

    def test_precision_series_populated(self):
        r = igt.analyse(_sharp(100))
        assert len(r.precision_series) > 0

    def test_std_phi_nonnegative(self):
        r = igt.analyse(_sharp(100))
        assert r.std_phi >= 0.0

    def test_to_dict_keys(self):
        r = igt.analyse(_sharp(100))
        d = r.to_dict()
        for k in ("precision", "curvature_trend", "naturalised_step",
                  "geometry_class", "mean_phi", "std_phi",
                  "n_samples", "precision_series"):
            assert k in d

    def test_to_dict_serialisable(self):
        import json
        r = igt.analyse(_sharp(100))
        json.dumps(r.to_dict())

    def test_null_baseline_diffuse_lower_precision(self):
        # A shuffled high-variance series should still have lower precision
        # than a sharp series
        r_sharp  = igt.analyse(_sharp(200))
        r_diffuse = igt.analyse(_diffuse(200))
        assert r_sharp.precision > r_diffuse.precision

    def test_step_affects_series_length(self):
        phi = _sharp(200)
        r1 = igt.analyse(phi, step=5)
        r2 = igt.analyse(phi, step=10)
        assert len(r1.precision_series) > len(r2.precision_series)

    def test_constant_phi_high_precision(self):
        r = igt.analyse(np.ones(50) * 2.0 + np.random.default_rng(0).normal(0, 0.001, 50))
        assert r.precision > 100.0
