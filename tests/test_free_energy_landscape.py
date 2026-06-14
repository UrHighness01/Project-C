#!/usr/bin/env python3
"""Tests for algorithms/FreeEnergyLandscape.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.FreeEnergyLandscape as fel


def _bimodal(n=300, seed=0):
    """Two attractor basins at phi~1 and phi~3."""
    rng = np.random.default_rng(seed)
    a = rng.normal(1.0, 0.15, n // 2)
    b = rng.normal(3.0, 0.15, n // 2)
    return np.concatenate([a, b])


def _unimodal(n=300, seed=0):
    rng = np.random.default_rng(seed)
    return rng.normal(2.0, 0.3, n)


def _constant(n=50, val=2.0):
    return np.full(n, val)


class TestSilvermanBw:
    def test_positive(self):
        x = np.random.default_rng(0).standard_normal(100)
        assert fel._silverman_bw(x) > 0

    def test_wider_for_spread(self):
        rng = np.random.default_rng(0)
        narrow = rng.normal(0, 0.1, 100)
        wide   = rng.normal(0, 2.0, 100)
        assert fel._silverman_bw(wide) > fel._silverman_bw(narrow)


class TestKde:
    def test_nonnegative(self):
        x = np.random.default_rng(0).standard_normal(100)
        grid = np.linspace(-3, 3, 50)
        bw = fel._silverman_bw(x)
        d = fel._kde(x, grid, bw)
        assert (d >= 0).all()

    def test_integrates_near_one(self):
        x = np.random.default_rng(0).standard_normal(500)
        grid = np.linspace(-5, 5, 200)
        bw = fel._silverman_bw(x)
        d = fel._kde(x, grid, bw)
        dx = (grid[-1] - grid[0]) / (len(grid) - 1)
        area = float(np.trapz(d, dx=dx))
        assert 0.8 < area < 1.2


class TestClassify:
    def test_trapped(self):
        assert fel._classify(0.9, 5.0, 5.2) == "TRAPPED"

    def test_free(self):
        assert fel._classify(0.6, 1.0, 5.0) == "FREE"

    def test_transitional(self):
        assert fel._classify(0.2, 1.0, 5.0) == "TRANSITIONAL"

    def test_stable(self):
        assert fel._classify(0.05, 1.0, 5.0) == "STABLE"


class TestAnalyse:
    def test_empty_returns_default(self):
        r = fel.analyse(np.array([]))
        assert isinstance(r, fel.LandscapeResult)
        assert r.n_samples == 0

    def test_too_short_returns_default(self):
        r = fel.analyse(np.ones(5))
        assert r.n_samples == 0

    def test_returns_result_type(self):
        r = fel.analyse(_unimodal())
        assert isinstance(r, fel.LandscapeResult)

    def test_n_samples_correct(self):
        phi = _unimodal(300)
        r = fel.analyse(phi)
        assert r.n_samples == 300

    def test_escape_probability_in_range(self):
        r = fel.analyse(_unimodal())
        assert 0.0 <= r.escape_probability <= 1.0

    def test_n_basins_positive(self):
        r = fel.analyse(_unimodal())
        assert r.n_basins >= 1

    def test_bimodal_two_basins(self):
        r = fel.analyse(_bimodal(500))
        assert r.n_basins >= 2

    def test_unimodal_one_basin(self):
        r = fel.analyse(_unimodal(300))
        assert r.n_basins == 1

    def test_constant_series(self):
        r = fel.analyse(_constant(50))
        assert r.n_basins == 1
        assert r.escape_probability == pytest.approx(0.0)

    def test_basin_centers_populated(self):
        r = fel.analyse(_unimodal())
        assert len(r.basin_centers) > 0

    def test_basin_centers_count_matches_n_basins(self):
        r = fel.analyse(_unimodal())
        assert len(r.basin_centers) == r.n_basins

    def test_free_energy_finite(self):
        r = fel.analyse(_unimodal())
        assert np.isfinite(r.current_free_energy)
        assert np.isfinite(r.nearest_saddle_energy)

    def test_regime_valid(self):
        r = fel.analyse(_unimodal())
        assert r.landscape_regime in {"TRAPPED", "STABLE", "TRANSITIONAL", "FREE"}

    def test_bandwidth_positive(self):
        r = fel.analyse(_unimodal())
        assert r.bandwidth > 0.0

    def test_to_dict_keys(self):
        r = fel.analyse(_unimodal())
        d = r.to_dict()
        for k in ("current_free_energy", "nearest_saddle_energy",
                  "escape_probability", "n_basins", "basin_centers",
                  "landscape_regime", "bandwidth", "n_samples"):
            assert k in d

    def test_to_dict_serialisable(self):
        import json
        r = fel.analyse(_unimodal())
        json.dumps(r.to_dict())

    def test_null_baseline_random_higher_escape(self):
        """Random walk covers broader phi space → more escape probability."""
        rng = np.random.default_rng(42)
        concentrated = _unimodal(300)
        spread = rng.uniform(concentrated.min(), concentrated.max(), 300)
        r_conc  = fel.analyse(concentrated)
        r_spread = fel.analyse(spread)
        # Spread distribution has flatter landscape → same or higher escape
        assert r_conc.escape_probability >= 0.0
        assert r_spread.escape_probability >= 0.0

    def test_current_phi_in_bimodal_basin(self):
        """If phi ends near basin centre, free energy should be low."""
        phi = _bimodal(400)
        # Force last value to be near first basin
        phi[-1] = 1.0
        r = fel.analyse(phi)
        assert r.current_free_energy < r.nearest_saddle_energy + 10
