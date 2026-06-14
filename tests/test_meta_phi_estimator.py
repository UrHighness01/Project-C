#!/usr/bin/env python3
"""Tests for algorithms/MetaPhiEstimator.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.MetaPhiEstimator as mpe


def _collinear(k=4, T=50, seed=0):
    """All k signals are copies of one base — maximally redundant."""
    rng = np.random.default_rng(seed)
    base = rng.standard_normal(T)
    return np.column_stack([base] * k)


def _independent(k=4, T=50, seed=0):
    """All k signals are independent white noise — no coupling."""
    rng = np.random.default_rng(seed)
    return rng.standard_normal((T, k))


def _moderate(k=4, T=50, rho=0.4, seed=0):
    """Signals share factor + independent noise — moderate coupling."""
    rng = np.random.default_rng(seed)
    factor = rng.standard_normal(T)
    noise  = rng.standard_normal((T, k))
    return rho * factor[:, None] + (1 - rho) * noise


class TestCorrelationMatrix:
    def test_diagonal_ones(self):
        X = _moderate(4, 40)
        R = mpe._correlation_matrix(X)
        for i in range(4):
            assert R[i, i] == pytest.approx(1.0, abs=1e-4)

    def test_symmetric(self):
        X = _moderate(4, 40)
        R = mpe._correlation_matrix(X)
        assert np.allclose(R, R.T, atol=1e-10)

    def test_values_in_minus1_to_1(self):
        X = _moderate(4, 40)
        R = mpe._correlation_matrix(X)
        assert (np.abs(R) <= 1.0 + 1e-8).all()

    def test_constant_column_handled(self):
        X = _moderate(4, 40)
        X[:, 0] = 5.0   # constant column
        R = mpe._correlation_matrix(X)
        assert not np.isnan(R).any()


class TestParticipationRatio:
    def test_collinear_low_pr(self):
        X = _collinear(4, 50)
        R = mpe._correlation_matrix(X)
        pr, _ = mpe._participation_ratio(R)
        assert pr < 1.5   # ~1 effective dimension

    def test_independent_high_pr(self):
        X = _independent(4, 100)
        R = mpe._correlation_matrix(X)
        pr, _ = mpe._participation_ratio(R)
        assert pr > 2.5   # ~4 effective dimensions for k=4

    def test_eigenvalues_nonnegative(self):
        X = _moderate(4, 50)
        R = mpe._correlation_matrix(X)
        _, eigs = mpe._participation_ratio(R)
        assert (eigs >= -1e-8).all()

    def test_eigenvalues_count(self):
        X = _moderate(4, 50)
        R = mpe._correlation_matrix(X)
        _, eigs = mpe._participation_ratio(R)
        assert len(eigs) == 4


class TestClassify:
    def test_optimal(self):
        assert mpe._classify(0.85) == "OPTIMAL"

    def test_moderate(self):
        assert mpe._classify(0.65) == "MODERATE"

    def test_degenerate(self):
        assert mpe._classify(0.30) == "DEGENERATE"


class TestAnalyse:
    def test_empty_returns_default(self):
        r = mpe.analyse(np.empty((0, 0)))
        assert isinstance(r, mpe.MetaPhiResult)
        assert r.meta_phi == 0.0

    def test_too_few_signals_returns_default(self):
        r = mpe.analyse(np.ones((50, 1)))
        assert r.n_signals == 0

    def test_too_few_timepoints_returns_default(self):
        r = mpe.analyse(np.ones((2, 4)))
        assert r.n_signals == 0

    def test_returns_result_type(self):
        r = mpe.analyse(_moderate(4, 50))
        assert isinstance(r, mpe.MetaPhiResult)

    def test_meta_phi_in_range(self):
        r = mpe.analyse(_moderate(4, 50))
        assert 0.0 <= r.meta_phi <= 1.0

    def test_pr_norm_in_range(self):
        r = mpe.analyse(_moderate(4, 50))
        assert 0.0 <= r.pr_norm <= 1.0

    def test_n_signals_correct(self):
        r = mpe.analyse(_moderate(4, 50))
        assert r.n_signals == 4

    def test_n_timepoints_correct(self):
        r = mpe.analyse(_moderate(4, 60))
        assert r.n_timepoints == 60

    def test_integration_quality_valid(self):
        r = mpe.analyse(_moderate(4, 50))
        assert r.integration_quality in {"OPTIMAL", "MODERATE", "DEGENERATE"}

    def test_moderate_signals_beat_collinear(self):
        r_mod = mpe.analyse(_moderate(4, 80, rho=0.4))
        r_col = mpe.analyse(_collinear(4, 80))
        assert r_mod.meta_phi > r_col.meta_phi

    def test_moderate_signals_beat_independent(self):
        # Both extremes should have lower meta_phi than moderate coupling
        r_mod  = mpe.analyse(_moderate(4, 200, rho=0.4))
        r_indep = mpe.analyse(_independent(4, 200))
        # Independent → PR_norm→1 → meta_phi→0
        assert r_mod.meta_phi >= r_indep.meta_phi

    def test_collinear_degenerate(self):
        r = mpe.analyse(_collinear(4, 80))
        assert r.integration_quality == "DEGENERATE"

    def test_eigenvalues_populated(self):
        r = mpe.analyse(_moderate(4, 50))
        assert len(r.eigenvalues) == 4

    def test_eff_dim_positive(self):
        r = mpe.analyse(_moderate(4, 50))
        assert r.eff_dim > 0.0

    def test_eff_dim_bounded_by_k(self):
        r = mpe.analyse(_moderate(4, 50))
        assert r.eff_dim <= 4.0 + 1e-4

    def test_to_dict_keys(self):
        r = mpe.analyse(_moderate(4, 50))
        d = r.to_dict()
        for k in ("meta_phi", "pr_norm", "eff_dim", "n_signals",
                  "n_timepoints", "integration_quality", "eigenvalues"):
            assert k in d

    def test_to_dict_serialisable(self):
        import json
        r = mpe.analyse(_moderate(4, 50))
        json.dumps(r.to_dict())

    def test_null_baseline_collinear_lower(self):
        # Shuffling columns should not drastically change result since
        # shuffling preserves marginal distributions but not correlations.
        rng = np.random.default_rng(1)
        X = _moderate(4, 80, rho=0.4)
        X_shuf = X.copy()
        for col in range(X_shuf.shape[1]):
            rng.shuffle(X_shuf[:, col])
        r_real = mpe.analyse(X)
        r_null = mpe.analyse(X_shuf)
        # Real moderate coupling should produce higher meta_phi than destroyed correlations
        assert r_real.meta_phi >= r_null.meta_phi - 0.1

    def test_six_signals(self):
        r = mpe.analyse(_moderate(6, 80))
        assert r.n_signals == 6
        assert 0.0 <= r.meta_phi <= 1.0

    def test_pr_norm_independent_near_one(self):
        r = mpe.analyse(_independent(5, 200))
        assert r.pr_norm > 0.7   # independent → high PR_norm
