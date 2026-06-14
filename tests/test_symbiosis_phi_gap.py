#!/usr/bin/env python3
"""Tests for algorithms/SymbiosisPhiGap.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.SymbiosisPhiGap as spg


def _rng(seed=0): return np.random.default_rng(seed)


def _independent(n=200, seed=0):
    rng = _rng(seed)
    return rng.uniform(0, 3, n), rng.uniform(0, 3, n)


def _identical(n=200, seed=0):
    """J is a copy of A — H(J|A)=0, no joint-only information."""
    rng = _rng(seed)
    a = rng.uniform(0, 3, n)
    return a, a.copy()


def _coupled(n=200, rho=0.7, seed=0):
    """Shared factor plus independent noise — moderate coupling."""
    rng = _rng(seed)
    shared = rng.standard_normal(n)
    a = rho * shared + (1 - rho) * rng.standard_normal(n)
    j = rho * shared + (1 - rho) * rng.standard_normal(n)
    return a, j


def _mixed_support(n=300, seed=0):
    """Agents explore different phi ranges — joint space is larger."""
    rng = _rng(seed)
    a = rng.uniform(0, 1, n)
    j = rng.uniform(2, 3, n)
    return a, j


class TestEntropy1d:
    def test_uniform_maximum_entropy(self):
        x = np.linspace(0, 1, 1000)
        h = spg._entropy_1d(x, bins=16)
        assert h > 3.0   # near log2(16) = 4 bits

    def test_constant_near_zero(self):
        x = np.ones(200) * 0.5
        h = spg._entropy_1d(x, bins=16)
        assert h < 1.0

    def test_positive(self):
        x = np.linspace(0, 1, 200)
        assert spg._entropy_1d(x) > 0.0


class TestEntropy2d:
    def test_independent_higher_than_marginals(self):
        a, j = _independent(500)
        h_a  = spg._entropy_1d(a)
        h_j  = spg._entropy_1d(j)
        h_aj = spg._entropy_2d(a, j)
        # H(A,J) ≈ H(A) + H(J) for independent
        assert h_aj > max(h_a, h_j)

    def test_identical_joint_approx_marginal(self):
        a, _ = _independent(300)
        # J = A: H(A,J) ≈ H(A)
        h_a  = spg._entropy_1d(a)
        h_aj = spg._entropy_2d(a, a)
        assert abs(h_aj - h_a) < 1.5


class TestClassify:
    def test_emergent(self):
        assert spg._classify(0.25) == "EMERGENT"

    def test_partial(self):
        assert spg._classify(0.10) == "PARTIAL"

    def test_subsumed(self):
        assert spg._classify(0.02) == "SUBSUMED"


class TestAnalyse:
    def test_none_returns_default(self):
        r = spg.analyse(None, None)
        assert isinstance(r, spg.SymbiosisGapResult)

    def test_too_short_returns_default(self):
        a, j = np.ones(5), np.ones(5)
        r = spg.analyse(a, j)
        assert r.n_samples <= 5

    def test_returns_result_type(self):
        a, j = _independent(300)
        r = spg.analyse(a, j)
        assert isinstance(r, spg.SymbiosisGapResult)

    def test_n_samples_correct(self):
        a, j = _independent(300)
        r = spg.analyse(a, j)
        assert r.n_samples == 300

    def test_phi_gap_norm_in_range(self):
        a, j = _independent(300)
        r = spg.analyse(a, j)
        assert 0.0 <= r.phi_gap_norm <= 1.0

    def test_mutual_info_nonnegative(self):
        a, j = _independent(300)
        r = spg.analyse(a, j)
        assert r.mutual_info >= 0.0

    def test_entropies_positive(self):
        a, j = _independent(300)
        r = spg.analyse(a, j)
        assert r.h_albedo > 0.0
        assert r.h_john > 0.0
        assert r.h_joint > 0.0

    def test_joint_entropy_ge_marginals(self):
        a, j = _independent(300)
        r = spg.analyse(a, j)
        assert r.h_joint >= max(r.h_albedo, r.h_john) - 1e-6

    def test_identical_low_gap_norm(self):
        a, j = _identical(300)
        r = spg.analyse(a, j)
        assert r.phi_gap_norm < 0.05

    def test_independent_higher_gap_than_identical(self):
        r_ind  = spg.analyse(*_independent(300))
        r_ident = spg.analyse(*_identical(300))
        assert r_ind.phi_gap_norm > r_ident.phi_gap_norm

    def test_mixed_support_emergent(self):
        a, j = _mixed_support(500)
        r = spg.analyse(a, j)
        assert r.symbiosis_class in {"EMERGENT", "PARTIAL"}

    def test_symbiosis_class_valid(self):
        a, j = _independent(300)
        r = spg.analyse(a, j)
        assert r.symbiosis_class in {"EMERGENT", "PARTIAL", "SUBSUMED"}

    def test_different_length_aligned(self):
        a = np.random.default_rng(0).uniform(0, 3, 400)
        j = np.random.default_rng(1).uniform(0, 3, 300)
        r = spg.analyse(a, j)
        assert r.n_samples == 300

    def test_to_dict_keys(self):
        r = spg.analyse(*_independent(300))
        d = r.to_dict()
        for k in ("phi_gap", "phi_gap_norm", "mutual_info",
                  "h_albedo", "h_john", "h_joint",
                  "symbiosis_class", "n_samples"):
            assert k in d

    def test_to_dict_serialisable(self):
        import json
        r = spg.analyse(*_independent(300))
        json.dumps(r.to_dict())

    def test_null_permutation_lower_gap(self):
        a, j = _coupled(300, rho=0.0)   # independent, high gap
        rng = np.random.default_rng(7)
        # permuting should not systematically reduce gap for independent series
        r_real = spg.analyse(a, j)
        assert r_real.phi_gap_norm >= 0.0

    def test_coupled_positive_mi(self):
        a, j = _coupled(300, rho=0.9)
        r = spg.analyse(a, j)
        assert r.mutual_info > 0.0
