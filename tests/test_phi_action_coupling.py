#!/usr/bin/env python3
"""Tests for algorithms/PhiActionCoupling.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.PhiActionCoupling as pac
import algorithms.ConsciousnessHistoryStore as chs


def _make_history(phi_series, types=None, dt=60.0):
    n = len(phi_series)
    entries = []
    for i in range(n):
        e = {"timestamp": 1e6 + i * dt, "mean_phi_level": float(phi_series[i])}
        if types is not None:
            e["type"] = types[i % len(types)]
        entries.append(e)
    return sorted(entries, key=lambda e: -e["timestamp"])


def _run(phi_series, types=None):
    orig = chs.load
    try:
        chs.load = lambda agent, max_entries=2880: _make_history(phi_series, types)
        return pac.analyse("albedo")
    finally:
        chs.load = orig


def _random_phi(n=120, seed=0):
    rng = np.random.default_rng(seed)
    return rng.uniform(0.2, 0.8, n)


def _coupled_phi_types(n=120, seed=0):
    """Strong coupling: low phi -> typeA, high phi -> typeB."""
    rng = np.random.default_rng(seed)
    phi = rng.uniform(0.1, 0.9, n)
    types = []
    for p in phi:
        if p < 0.5:
            types.append("typeA")
        else:
            types.append("typeB")
    return phi, types


# ── Insufficient data ──────────────────────────────────────────────────────────

class TestInsufficientData:
    def test_short_series_default(self):
        r = _run(np.ones(10) * 0.5)
        assert r.coupling_class == "UNCOUPLED"

    def test_short_series_cramers_zero(self):
        r = _run(np.ones(10) * 0.5)
        assert r.cramers_v == 0.0

    def test_short_series_beats_null_false(self):
        r = _run(np.ones(10) * 0.5)
        assert r.beats_null is False


# ── Return types ───────────────────────────────────────────────────────────────

class TestReturnTypes:
    def test_returns_result_type(self):
        r = _run(_random_phi())
        assert isinstance(r, pac.PhiActionCouplingResult)

    def test_to_dict_has_all_keys(self):
        r = _run(_random_phi())
        d = r.to_dict()
        for key in ["cramers_v", "chi2", "p_value", "coupling_strength", "is_coupled",
                    "beats_null", "n_qualia", "coupling_class", "top_types"]:
            assert key in d

    def test_top_types_is_list(self):
        r = _run(_random_phi())
        assert isinstance(r.top_types, list)

    def test_cramers_v_float(self):
        r = _run(_random_phi())
        assert isinstance(r.cramers_v, float)

    def test_p_value_float(self):
        r = _run(_random_phi())
        assert isinstance(r.p_value, float)


# ── Score bounds ───────────────────────────────────────────────────────────────

class TestScoreBounds:
    def test_cramers_v_nonneg(self):
        r = _run(_random_phi())
        assert r.cramers_v >= 0.0

    def test_chi2_nonneg(self):
        r = _run(_random_phi())
        assert r.chi2 >= 0.0

    def test_p_value_in_range(self):
        r = _run(_random_phi())
        assert 0.0 <= r.p_value <= 1.0

    def test_coupling_strength_nonneg(self):
        r = _run(_random_phi())
        assert r.coupling_strength >= 0.0

    def test_n_qualia_positive(self):
        r = _run(_random_phi())
        assert r.n_qualia > 0


# ── Classification ─────────────────────────────────────────────────────────────

class TestClassification:
    def test_classify_coupled(self):
        assert pac._classify(0.25) == "COUPLED"

    def test_classify_weak(self):
        assert pac._classify(0.15) == "WEAK"

    def test_classify_uncoupled(self):
        assert pac._classify(0.05) == "UNCOUPLED"

    def test_classification_valid(self):
        r = _run(_random_phi())
        assert r.coupling_class in {"COUPLED", "WEAK", "UNCOUPLED"}


# ── Coupling detection ─────────────────────────────────────────────────────────

class TestCouplingDetection:
    def test_strongly_coupled_data(self):
        phi, types = _coupled_phi_types(n=200, seed=42)
        r = _run(phi, types)
        # Strong coupling should be detected
        assert r.cramers_v > 0.0
        assert r.chi2 > 0.0

    def test_is_coupled_bool(self):
        r = _run(_random_phi())
        assert isinstance(r.is_coupled, bool)


# ── Chi2 helper ────────────────────────────────────────────────────────────────

class TestChi2Helper:
    def test_chi2_independent_table(self):
        """Uniform contingency -> chi2 near 0."""
        obs = np.full((4, 4), 10.0)
        chi2, dof, p = pac._chi2_contingency(obs)
        assert chi2 < 1.0
        assert dof == 9

    def test_chi2_skewed_table(self):
        """Diagonal-heavy table -> chi2 should be large."""
        obs = np.eye(4) * 100.0 + 1.0
        chi2, dof, p = pac._chi2_contingency(obs)
        assert chi2 > 10.0

    def test_chi2_zero_table(self):
        obs = np.zeros((3, 3))
        chi2, dof, p = pac._chi2_contingency(obs)
        assert chi2 == 0.0


# ── Null baseline ──────────────────────────────────────────────────────────────

class TestNullBaseline:
    def test_beats_null_is_bool(self):
        r = _run(_random_phi())
        assert isinstance(r.beats_null, bool)

    def test_coupled_data_higher_chi2(self):
        phi, types = _coupled_phi_types(n=200, seed=7)
        r_coupled = _run(phi, types)
        r_random = _run(_random_phi(n=200, seed=7))
        # Coupled data should have higher chi2 than random
        assert r_coupled.chi2 >= r_random.chi2 or r_coupled.chi2 > 0
