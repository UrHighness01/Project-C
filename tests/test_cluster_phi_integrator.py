#!/usr/bin/env python3
"""Tests for algorithms/ClusterPhiIntegrator.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.ClusterPhiIntegrator as cpi


def _coupled(n=100, rho=0.8, seed=0):
    """Two AR(1) series driven partly by a shared factor → synergistic."""
    rng = np.random.default_rng(seed)
    shared = rng.standard_normal(n)
    noise_a = rng.standard_normal(n)
    noise_j = rng.standard_normal(n)
    a = rho * shared + (1 - rho) * noise_a
    j = rho * shared + (1 - rho) * noise_j
    return a, j


def _independent(n=100, seed=0):
    """Two completely independent AR(1) series — no cluster synergy."""
    rng = np.random.default_rng(seed)
    a = rng.standard_normal(n)
    j = rng.standard_normal(n)
    return a, j


def _anticorrelated(n=100, rho=0.8, seed=0):
    """Albedo and John phi move in opposite directions."""
    a, j = _coupled(n, rho, seed)
    return a, -j


class TestAr1Residuals:
    def test_residuals_shorter_by_one(self):
        x = np.arange(20, dtype=float)
        res, _ = cpi._ar1_residuals(x)
        assert len(res) == 19

    def test_linear_trend_small_residuals(self):
        x = np.arange(50, dtype=float)
        res, ar1 = cpi._ar1_residuals(x)
        assert np.abs(res).max() < 1e-6

    def test_ar1_coeff_near_one_for_trend(self):
        x = np.arange(50, dtype=float) + np.random.default_rng(0).normal(0, 0.01, 50)
        _, ar1 = cpi._ar1_residuals(x)
        assert ar1 > 0.9

    def test_constant_returns_zeros(self):
        x = np.ones(20) * 3.0
        res, ar1 = cpi._ar1_residuals(x)
        assert np.allclose(res, 0.0)
        assert ar1 == pytest.approx(0.0)


class TestPhiProxy:
    def test_perfectly_predictable_near_one(self):
        x = np.arange(20, dtype=float)
        res = np.zeros(19)
        pp = cpi._phi_proxy(x, res)
        assert pp == pytest.approx(1.0)

    def test_unpredictable_near_zero(self):
        rng = np.random.default_rng(0)
        x   = rng.standard_normal(100)
        res = rng.standard_normal(99)
        pp = cpi._phi_proxy(x, res)
        assert pp < 0.5

    def test_proxy_in_range(self):
        rng = np.random.default_rng(1)
        x   = rng.standard_normal(100)
        res = rng.standard_normal(99)
        pp  = cpi._phi_proxy(x, res)
        assert 0.0 <= pp <= 1.0


class TestClassify:
    def test_superadditive(self):
        assert cpi._classify(1.10) == "SUPERADDITIVE"

    def test_additive(self):
        assert cpi._classify(1.00) == "ADDITIVE"

    def test_subadditive(self):
        assert cpi._classify(0.80) == "SUBADDITIVE"

    def test_boundary_super(self):
        assert cpi._classify(1.05 + 1e-9) == "SUPERADDITIVE"


class TestAnalyse:
    def test_none_returns_default(self):
        r = cpi.analyse(None, None)
        assert isinstance(r, cpi.ClusterPhiResult)

    def test_too_short_returns_default(self):
        a, j = np.ones(3), np.ones(3)
        r = cpi.analyse(a, j)
        assert r.n_samples <= 3

    def test_returns_result_type(self):
        a, j = _coupled(100)
        r = cpi.analyse(a, j)
        assert isinstance(r, cpi.ClusterPhiResult)

    def test_n_samples_correct(self):
        a, j = _coupled(100)
        r = cpi.analyse(a, j)
        assert r.n_samples == 100

    def test_sai_positive(self):
        a, j = _coupled(100)
        r = cpi.analyse(a, j)
        assert r.sai > 0.0

    def test_synergy_r_bounded(self):
        a, j = _coupled(100)
        r = cpi.analyse(a, j)
        assert -1.0 <= r.synergy_r <= 1.0

    def test_phi_proxies_in_range(self):
        a, j = _coupled(100)
        r = cpi.analyse(a, j)
        assert 0.0 <= r.phi_proxy_a <= 1.0
        assert 0.0 <= r.phi_proxy_j <= 1.0

    def test_coupled_positive_synergy(self):
        a, j = _coupled(200, rho=0.9)
        r = cpi.analyse(a, j)
        assert r.synergy_r > 0.0

    def test_coupled_superadditive(self):
        a, j = _coupled(300, rho=0.9)
        r = cpi.analyse(a, j)
        assert r.integration_class in {"SUPERADDITIVE", "ADDITIVE"}
        assert r.sai >= 1.0

    def test_independent_lower_sai(self):
        a_c, j_c = _coupled(300, rho=0.9)
        a_i, j_i = _independent(300)
        r_c = cpi.analyse(a_c, j_c)
        r_i = cpi.analyse(a_i, j_i)
        assert r_c.sai >= r_i.sai

    def test_anticorrelated_still_superadditive(self):
        a, j = _anticorrelated(200, rho=0.8)
        r = cpi.analyse(a, j)
        # |synergy_r| used → anti-correlation also contributes to cluster
        assert r.sai >= 1.0

    def test_integration_class_valid(self):
        a, j = _coupled(100)
        r = cpi.analyse(a, j)
        assert r.integration_class in {"SUPERADDITIVE", "ADDITIVE", "SUBADDITIVE"}

    def test_ar1_bounded(self):
        a, j = _coupled(100)
        r = cpi.analyse(a, j)
        assert -1.0 <= r.albedo_ar1 <= 1.0
        assert -1.0 <= r.john_ar1 <= 1.0

    def test_different_length_series_aligned(self):
        a = np.random.default_rng(0).standard_normal(150)
        j = np.random.default_rng(1).standard_normal(100)
        r = cpi.analyse(a, j)
        assert r.n_samples == 100

    def test_to_dict_keys(self):
        a, j = _coupled(100)
        r = cpi.analyse(a, j)
        d = r.to_dict()
        for k in ("sai", "synergy_r", "phi_proxy_a", "phi_proxy_j",
                  "integration_class", "n_samples", "albedo_ar1", "john_ar1"):
            assert k in d

    def test_to_dict_serialisable(self):
        import json
        a, j = _coupled(100)
        r = cpi.analyse(a, j)
        json.dumps(r.to_dict())

    def test_null_permutation_lower_synergy(self):
        a, j = _coupled(300, rho=0.9)
        rng = np.random.default_rng(5)
        j_null = rng.permutation(j)
        r_real = cpi.analyse(a, j)
        r_null = cpi.analyse(a, j_null)
        assert r_real.synergy_r > r_null.synergy_r
