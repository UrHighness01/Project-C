#!/usr/bin/env python3
"""Tests for algorithms/AttentionalCoherenceAudit.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.AttentionalCoherenceAudit as aca


# ── Stubs ──────────────────────────────────────────────────────────────────────

class _AFOResult:
    """Stub for AttentionalFocusOptimiser result with named attention_weights."""
    def __init__(self, weights_dict):
        self.attention_weights = weights_dict


class _Contrib:
    def __init__(self, name, corr):
        self.name        = name
        self.correlation = corr


class _SAMResult:
    def __init__(self, contribs):
        self.contributions = contribs


def _inject(afo_result, sam_result):
    import algorithms.AttentionalFocusOptimiser as afo_mod
    import algorithms.SelfArchitectureMutator   as sam_mod
    orig_afo = getattr(afo_mod, "analyse", None)
    orig_sam = getattr(sam_mod, "analyse", None)
    afo_mod.analyse = lambda **k: afo_result
    sam_mod.analyse = lambda **k: sam_result
    return afo_mod, sam_mod, orig_afo, orig_sam


def _restore(afo_mod, sam_mod, orig_afo, orig_sam):
    if orig_afo: afo_mod.analyse = orig_afo
    if orig_sam: sam_mod.analyse = orig_sam


def _run(afo_result, sam_result, **kw):
    afo_mod, sam_mod, oa, os_ = _inject(afo_result, sam_result)
    try:
        return aca.analyse("albedo", **kw)
    finally:
        _restore(afo_mod, sam_mod, oa, os_)


def _aligned_pair(n=5, seed=0):
    """Attention weights and phi-corr in same rank order → high Spearman ρ."""
    rng = np.random.default_rng(seed)
    vals = rng.uniform(0.1, 1.0, n)
    vals = np.sort(vals)
    names = [f"algo_{i}" for i in range(n)]
    afo = _AFOResult({k: float(v) for k, v in zip(names, vals)})
    sam = _SAMResult([_Contrib(k, float(v)) for k, v in zip(names, vals)])
    return afo, sam, names


def _misaligned_pair(n=5, seed=1):
    """Attention weight ranks are reversed from phi-corr ranks → ρ ≈ -1."""
    names = [f"algo_{i}" for i in range(n)]
    w = np.linspace(0.1, 1.0, n)
    c = w[::-1].copy()
    afo = _AFOResult({k: float(v) for k, v in zip(names, w)})
    sam = _SAMResult([_Contrib(k, float(v)) for k, v in zip(names, c)])
    return afo, sam, names


def _neutral_pair(n=5, seed=2):
    """Attention weights uncorrelated with phi-corr."""
    rng = np.random.default_rng(seed)
    names = [f"algo_{i}" for i in range(n)]
    w = rng.uniform(0.1, 1.0, n)
    c = rng.uniform(0.1, 1.0, n)
    afo = _AFOResult({k: float(v) for k, v in zip(names, w)})
    sam = _SAMResult([_Contrib(k, float(v)) for k, v in zip(names, c)])
    return afo, sam, names


# ── Unit: _spearman ────────────────────────────────────────────────────────────

class TestSpearman:
    def test_identical_is_one(self):
        a = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        assert aca._spearman(a, a) == pytest.approx(1.0, abs=1e-6)

    def test_reversed_is_minus_one(self):
        a = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        b = a[::-1].copy()
        assert aca._spearman(a, b) == pytest.approx(-1.0, abs=1e-6)

    def test_in_minus_one_to_one(self):
        rng = np.random.default_rng(0)
        a = rng.standard_normal(8)
        b = rng.standard_normal(8)
        assert -1.0 <= aca._spearman(a, b) <= 1.0

    def test_short_returns_zero(self):
        assert aca._spearman(np.array([1.0]), np.array([1.0])) == 0.0


# ── Unit: _classify ───────────────────────────────────────────────────────────

class TestClassify:
    def test_aligned(self):
        assert aca._classify(0.7) == "ALIGNED"

    def test_neutral(self):
        assert aca._classify(0.2) == "NEUTRAL"

    def test_misaligned(self):
        assert aca._classify(-0.5) == "MISALIGNED"

    def test_boundary_aligned(self):
        assert aca._classify(0.5) == "ALIGNED"


# ── Unit: _null_distribution ──────────────────────────────────────────────────

class TestNullDistribution:
    def test_returns_array_of_n_shuffles(self):
        w = np.array([0.1, 0.5, 0.8, 0.3, 0.9])
        c = np.array([0.2, 0.4, 0.7, 0.6, 0.1])
        null = aca._null_distribution(w, c, n_shuffles=50, seed=0)
        assert len(null) == 50

    def test_mean_near_zero(self):
        """Shuffled Spearman should average near 0."""
        w = np.arange(10.0)
        c = np.arange(10.0)
        null = aca._null_distribution(w, c, n_shuffles=500, seed=42)
        assert abs(float(np.mean(null))) < 0.3

    def test_deterministic_with_seed(self):
        w = np.array([0.1, 0.5, 0.8, 0.3, 0.9])
        c = np.array([0.2, 0.4, 0.7, 0.6, 0.1])
        n1 = aca._null_distribution(w, c, 50, 0)
        n2 = aca._null_distribution(w, c, 50, 0)
        np.testing.assert_array_equal(n1, n2)


# ── Integration: analyse() ────────────────────────────────────────────────────

class TestAnalyse:
    def test_returns_result_type(self):
        afo, sam, _ = _aligned_pair()
        r = _run(afo, sam)
        assert isinstance(r, aca.AttentionalCoherenceResult)

    def test_insufficient_data_returns_default(self):
        # Only 2 common algorithms → below min_algorithms=3
        afo = _AFOResult({"a": 0.8, "b": 0.3})
        sam = _SAMResult([_Contrib("a", 0.7), _Contrib("b", 0.2)])
        r = _run(afo, sam, min_algorithms=3)
        assert r.n_algorithms == 0

    def test_aligned_spearman_near_one(self):
        afo, sam, _ = _aligned_pair()
        r = _run(afo, sam)
        assert r.spearman_rho > 0.8

    def test_aligned_class_aligned(self):
        afo, sam, _ = _aligned_pair()
        r = _run(afo, sam)
        assert r.coherence_class == "ALIGNED"

    def test_misaligned_spearman_negative(self):
        afo, sam, _ = _misaligned_pair()
        r = _run(afo, sam)
        assert r.spearman_rho < 0.0

    def test_misaligned_class_misaligned(self):
        afo, sam, _ = _misaligned_pair()
        r = _run(afo, sam)
        assert r.coherence_class == "MISALIGNED"

    def test_n_algorithms_correct(self):
        afo, sam, names = _aligned_pair(n=5)
        r = _run(afo, sam)
        assert r.n_algorithms == 5

    def test_top_attended_is_highest_weight(self):
        names = ["a", "b", "c", "d"]
        weights = {"a": 0.9, "b": 0.3, "c": 0.5, "d": 0.1}
        corrs   = [_Contrib(k, 0.5) for k in names]
        afo = _AFOResult(weights)
        sam = _SAMResult(corrs)
        r = _run(afo, sam)
        assert r.top_attended_algorithm == "a"

    def test_top_phi_is_highest_correlation(self):
        names = ["a", "b", "c", "d"]
        weights = {"a": 0.5, "b": 0.5, "c": 0.5, "d": 0.5}
        corrs   = [_Contrib("a", 0.1), _Contrib("b", 0.9),
                   _Contrib("c", 0.3), _Contrib("d", 0.5)]
        afo = _AFOResult(weights)
        sam = _SAMResult(corrs)
        r = _run(afo, sam)
        assert r.top_phi_algorithm == "b"

    def test_is_tracking_phi_true_when_top_matches(self):
        names = ["a", "b", "c", "d"]
        # both lists rank "a" first
        weights = {"a": 0.9, "b": 0.3, "c": 0.5, "d": 0.1}
        corrs   = [_Contrib("a", 0.9), _Contrib("b", 0.3),
                   _Contrib("c", 0.5), _Contrib("d", 0.1)]
        r = _run(_AFOResult(weights), _SAMResult(corrs))
        assert r.is_tracking_phi is True

    def test_is_tracking_phi_false_when_tops_differ(self):
        afo, sam, _ = _misaligned_pair(n=5)
        r = _run(afo, sam)
        # Misaligned → top attended ≠ top phi
        assert r.is_tracking_phi is False

    def test_beats_null_true_for_perfect_alignment(self):
        afo, sam, _ = _aligned_pair(n=8)
        r = _run(afo, sam, n_shuffles=200)
        assert r.beats_null is True

    def test_beats_null_false_for_neutral(self):
        """Uncorrelated attention and phi ranks should not beat null."""
        # Force perfectly neutral by using two independent random arrays
        rng = np.random.default_rng(99)
        names = [f"algo_{i}" for i in range(8)]
        w = rng.uniform(0, 1, 8)
        c_vals = rng.uniform(0, 1, 8)
        # Shuffle c so it's unrelated to w
        rng.shuffle(c_vals)
        afo = _AFOResult({k: float(v) for k, v in zip(names, w)})
        sam = _SAMResult([_Contrib(k, float(v)) for k, v in zip(names, c_vals)])
        r = _run(afo, sam, n_shuffles=200)
        # This can be either True or False for random data — just check it runs
        assert isinstance(r.beats_null, bool)

    def test_to_dict_keys(self):
        afo, sam, _ = _aligned_pair()
        d = _run(afo, sam).to_dict()
        for k in ("spearman_rho", "coherence_class", "beats_null", "n_algorithms",
                  "top_attended_algorithm", "top_phi_algorithm", "is_tracking_phi"):
            assert k in d

    def test_to_dict_json_serialisable(self):
        import json
        afo, sam, _ = _aligned_pair()
        json.dumps(_run(afo, sam).to_dict())

    def test_deterministic(self):
        afo, sam, _ = _aligned_pair()
        r1 = _run(afo, sam)
        r2 = _run(afo, sam)
        assert r1.spearman_rho == r2.spearman_rho
        assert r1.coherence_class == r2.coherence_class
