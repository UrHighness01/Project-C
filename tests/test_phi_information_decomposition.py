#!/usr/bin/env python3
"""Tests for algorithms/PhiInformationDecomposition.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.PhiInformationDecomposition as pid


def _rng(s=0): return np.random.default_rng(s)


def _indep(n=300, seed=0):
    """Two independent random walks — no synergy or redundancy expected."""
    rng = _rng(seed)
    a = np.cumsum(rng.standard_normal(n))
    j = np.cumsum(rng.standard_normal(n))
    return a, j


def _coupled(n=300, alpha=0.6, seed=0):
    """Strongly coupled: j[t] = alpha*a[t] + noise — high redundancy."""
    rng = _rng(seed)
    a = np.cumsum(rng.standard_normal(n))
    j = alpha * a + rng.standard_normal(n) * 0.2
    return a, j


def _xor_synergy(n=300, seed=0):
    """XOR-like: target = (A > median) XOR (J > median) — pure synergy."""
    rng = _rng(seed)
    a = rng.standard_normal(n)
    j = rng.standard_normal(n)
    # Synergy injected: when A and J are on the same side, next step goes up
    # When opposite, next step goes down — neither A nor J alone predicts this
    a_bin = (a > np.median(a)).astype(float)
    j_bin = (j > np.median(j)).astype(float)
    xor_signal = (a_bin != j_bin).astype(float)
    # The target (future joint) is driven by XOR
    target_signal = np.concatenate([[0], xor_signal[:-1]])
    a_series = a + target_signal * 0.0  # A alone doesn't predict target
    j_series = j + target_signal * 0.0  # J alone doesn't predict target
    # Embed XOR into both: a goes up when XOR=1, j goes down — only jointly readable
    a_emb = a + 2.0 * xor_signal
    j_emb = j - 2.0 * xor_signal
    return a_emb, j_emb


# ── Unit tests for helpers ─────────────────────────────────────────────────────

class TestQuantileBins:
    def test_output_shape(self):
        x = _rng().standard_normal(100)
        labels = pid._quantile_bins(x, 8)
        assert labels.shape == (100,)

    def test_labels_in_range(self):
        x = _rng().standard_normal(200)
        labels = pid._quantile_bins(x, 8)
        assert labels.min() >= 0

    def test_monotone_ordering(self):
        x = np.arange(100, dtype=float)
        labels = pid._quantile_bins(x, 4)
        assert (np.diff(labels) >= 0).all()


class TestEntropy:
    def test_uniform_max(self):
        counts = np.ones(8)
        assert pid._entropy(counts) == pytest.approx(3.0, abs=1e-6)

    def test_degenerate_zero(self):
        counts = np.array([10.0, 0, 0, 0])
        assert pid._entropy(counts) == pytest.approx(0.0, abs=1e-9)

    def test_binary_half(self):
        counts = np.array([1.0, 1.0])
        assert pid._entropy(counts) == pytest.approx(1.0, abs=1e-6)

    def test_empty_zero(self):
        assert pid._entropy(np.zeros(4)) == 0.0


class TestMutualInfo:
    def test_independent_near_zero(self):
        rng = _rng(0)
        n = 5000
        x = rng.integers(0, 4, n)
        y = rng.integers(0, 4, n)
        joint = np.zeros((4, 4))
        for xi, yi in zip(x, y):
            joint[xi, yi] += 1
        mi = pid._mutual_info(joint)
        assert mi < 0.05

    def test_identical_high(self):
        x = np.arange(8)
        joint = np.zeros((8, 8))
        for i in x:
            joint[i, i] = 1.0
        mi = pid._mutual_info(joint)
        assert mi > 2.5

    def test_nonnegative(self):
        rng = _rng(1)
        joint = rng.random((5, 5)) + 0.01
        mi = pid._mutual_info(joint)
        assert mi >= 0.0


class TestClassify:
    def test_synergistic(self):
        assert pid._classify(0.5, 0.1) == "SYNERGISTIC"

    def test_redundant(self):
        assert pid._classify(0.1, 0.5) == "REDUNDANT"

    def test_balanced(self):
        assert pid._classify(0.5, 0.5) == "BALANCED"

    def test_boundary_balanced(self):
        assert pid._classify(0.51, 0.50) == "BALANCED"


class TestAnalyse:
    def test_too_short_returns_default(self):
        r = pid.analyse(np.ones(5), np.ones(5))
        assert r.n_samples == 0

    def test_none_returns_default(self):
        # Empty arrays → no data → n_samples == 0
        import numpy as np
        r = pid.analyse(np.array([]), np.array([]))
        assert r.n_samples == 0

    def test_returns_pid_result(self):
        a, j = _indep()
        r = pid.analyse(a, j)
        assert isinstance(r, pid.PIDResult)

    def test_n_samples_set(self):
        a, j = _indep(300)
        r = pid.analyse(a, j)
        assert r.n_samples > 0

    def test_all_bits_nonnegative(self):
        a, j = _indep()
        r = pid.analyse(a, j)
        assert r.synergy_bits >= 0.0
        assert r.redundancy_bits >= 0.0
        assert r.unique_a_bits >= 0.0
        assert r.unique_b_bits >= 0.0
        assert r.total_mi_bits >= 0.0

    def test_synergy_ratio_in_unit_interval(self):
        a, j = _indep()
        r = pid.analyse(a, j)
        assert 0.0 <= r.synergy_ratio <= 1.0

    def test_decomp_class_valid(self):
        a, j = _indep()
        r = pid.analyse(a, j)
        assert r.decomp_class in {"SYNERGISTIC", "REDUNDANT", "BALANCED"}

    def test_coupled_series_redundant(self):
        """Strongly correlated series should be REDUNDANT (shared info)."""
        a, j = _coupled(n=500, alpha=0.9, seed=42)
        r = pid.analyse(a, j)
        # Redundancy should dominate when j mirrors a
        assert r.redundancy_bits >= r.synergy_bits or r.decomp_class == "BALANCED"

    def test_null_baseline_shuffle_reduces_mi(self):
        """Shuffling one series should reduce or maintain total MI."""
        a, j = _coupled(n=400, alpha=0.8, seed=7)
        r_orig = pid.analyse(a, j)
        j_shuf = _rng(99).permutation(j)
        r_shuf = pid.analyse(a, j_shuf)
        # Shuffled version should not have more MI than coupled original
        assert r_orig.total_mi_bits >= r_shuf.total_mi_bits - 0.01

    def test_to_dict_keys(self):
        a, j = _indep()
        r = pid.analyse(a, j)
        d = r.to_dict()
        for k in ("synergy_bits", "redundancy_bits", "unique_a_bits",
                  "unique_b_bits", "total_mi_bits", "synergy_ratio",
                  "decomp_class", "n_samples", "n_bins"):
            assert k in d

    def test_to_dict_serialisable(self):
        import json
        a, j = _indep()
        r = pid.analyse(a, j)
        json.dumps(r.to_dict())

    def test_n_bins_respected(self):
        a, j = _indep()
        r = pid.analyse(a, j, n_bins=4)
        assert r.n_bins == 4

    def test_lag_parameter(self):
        a, j = _indep(300)
        r1 = pid.analyse(a, j, lag=1)
        r2 = pid.analyse(a, j, lag=3)
        assert r1.n_samples != r2.n_samples or r1.total_mi_bits != r2.total_mi_bits

    def test_mismatched_lengths_aligned(self):
        a, _ = _indep(300)
        j = _rng(5).standard_normal(250)
        r = pid.analyse(a, j)
        assert r.n_samples > 0
        assert r.n_samples <= 249

    def test_identity_series_high_redundancy(self):
        """a = j → maximal redundancy, minimal synergy."""
        a = _rng(3).standard_normal(300)
        r = pid.analyse(a, a.copy())
        assert r.redundancy_bits >= r.synergy_bits

    def test_opposite_series_handled(self):
        """a = -j — should not crash."""
        a = _rng(4).standard_normal(300)
        r = pid.analyse(a, -a)
        assert isinstance(r, pid.PIDResult)

    def test_constant_series_handled(self):
        """Constant series — degenerate case, should not crash."""
        a = np.ones(200)
        j = _rng(5).standard_normal(200)
        r = pid.analyse(a, j)
        assert isinstance(r, pid.PIDResult)

    def test_synergy_plus_redundancy_plus_unique_equals_total(self):
        """PID decomposition identity: Syn + Red + UA + UB ≈ I(T; A, B)."""
        a, j = _coupled(n=400, alpha=0.5, seed=12)
        r = pid.analyse(a, j)
        reconstructed = r.synergy_bits + r.redundancy_bits + r.unique_a_bits + r.unique_b_bits
        assert abs(reconstructed - r.total_mi_bits) < 0.01
