#!/usr/bin/env python3
"""Tests for algorithms/RecursiveSelfModel.py."""
import sys
import json
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.RecursiveSelfModel as rsm


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_history(phi_series, base_ts=1_000_000.0, dt=60.0):
    """Return newest-first list of entries."""
    n = len(phi_series)
    entries = [
        {"timestamp": base_ts + i * dt, "mean_phi_level": float(phi_series[i])}
        for i in range(n)
    ]
    return sorted(entries, key=lambda e: -e["timestamp"])


def _run(phi_series, **kw):
    import algorithms.ConsciousnessHistoryStore as chs
    original = getattr(chs, "load", None)
    try:
        chs.load = lambda agent, max_entries=2880: _make_history(phi_series)
        return rsm.analyse("albedo", **kw)
    finally:
        if original is not None:
            chs.load = original


def _ar1(n=120, alpha=0.85, noise=0.1, seed=0):
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    x[0] = 0.5
    for i in range(1, n):
        x[i] = alpha * x[i - 1] + rng.normal(0, noise)
    return x


# ── Unit: _depth_class ────────────────────────────────────────────────────────

class TestDepthClass:
    def test_deep(self):
        assert rsm._depth_class(0.30) == "DEEP"

    def test_shallow(self):
        assert rsm._depth_class(0.10) == "SHALLOW"

    def test_surface(self):
        assert rsm._depth_class(0.01) == "SURFACE"

    def test_boundary_deep(self):
        assert rsm._depth_class(0.25) == "DEEP"

    def test_boundary_shallow(self):
        assert rsm._depth_class(0.05) == "SHALLOW"


# ── Unit: _build_lagged ───────────────────────────────────────────────────────

class TestBuildLagged:
    def test_output_shape(self):
        x = np.arange(20, dtype=float)
        Z, y = rsm._build_lagged(x, p=3)
        assert Z.shape == (17, 4)  # T-p rows, p+1 cols (intercept + p lags)
        assert len(y) == 17

    def test_intercept_col_is_ones(self):
        x = np.arange(20, dtype=float)
        Z, _ = rsm._build_lagged(x, p=2)
        np.testing.assert_array_equal(Z[:, 0], np.ones(18))

    def test_first_lag_is_correct(self):
        x = np.arange(10, dtype=float)
        Z, y = rsm._build_lagged(x, p=1)
        np.testing.assert_array_equal(Z[:, 1], x[:-1])
        np.testing.assert_array_equal(y, x[1:])


# ── Unit: _ridge_fit ──────────────────────────────────────────────────────────

class TestRidgeFit:
    def test_returns_array(self):
        Z = np.column_stack([np.ones(20), np.arange(20, dtype=float)])
        y = 2.0 + 3.0 * np.arange(20, dtype=float)
        w = rsm._ridge_fit(Z, y, ridge=1e-6)
        assert isinstance(w, np.ndarray)
        assert len(w) == 2

    def test_approximates_linear_fit(self):
        x = np.arange(50, dtype=float)
        Z = np.column_stack([np.ones(50), x])
        y = 1.0 + 2.0 * x
        w = rsm._ridge_fit(Z, y, ridge=1e-6)
        assert w[0] == pytest.approx(1.0, abs=0.1)
        assert w[1] == pytest.approx(2.0, abs=0.1)


# ── Unit: _r2 ─────────────────────────────────────────────────────────────────

class TestR2:
    def test_perfect_prediction(self):
        y = np.array([1.0, 2.0, 3.0, 4.0])
        assert rsm._r2(y, y) == pytest.approx(1.0, abs=1e-6)

    def test_flat_target_returns_zero(self):
        y = np.ones(10)
        pred = np.ones(10) * 2.0
        assert rsm._r2(y, pred) == 0.0

    def test_clamped_below_neg_one(self):
        y = np.array([1.0, 2.0, 3.0, 4.0])
        # Wildly wrong predictions
        pred = np.array([100.0, 200.0, 300.0, 400.0])
        r2 = rsm._r2(y, pred)
        assert r2 >= -1.0


# ── Unit: SelfModelResult.to_dict ─────────────────────────────────────────────

class TestToDict:
    def _make_result(self):
        phi = _ar1(n=60)
        model = rsm.RecursiveSelfModel(p=4, q=4, null_seed=42)
        return model.fit(phi)

    def test_keys_present(self):
        r = self._make_result()
        d = r.to_dict()
        for k in ("n_samples", "p", "q", "r2_l1", "r2_l2", "depth",
                  "depth_class", "null_r2_l1", "null_r2_l2",
                  "beats_null_l1", "beats_null_l2", "equilibrium_estimate"):
            assert k in d

    def test_json_serialisable(self):
        r = self._make_result()
        json.dumps(r.to_dict())

    def test_depth_class_valid(self):
        r = self._make_result()
        assert r.to_dict()["depth_class"] in {"DEEP", "SHALLOW", "SURFACE"}

    def test_beats_null_are_bools(self):
        r = self._make_result()
        d = r.to_dict()
        assert isinstance(d["beats_null_l1"], bool)
        assert isinstance(d["beats_null_l2"], bool)


# ── Unit: RecursiveSelfModel.fit ──────────────────────────────────────────────

class TestFit:
    def test_returns_result_on_sufficient_data(self):
        phi = _ar1(n=60)
        model = rsm.RecursiveSelfModel(p=4, q=4)
        r = model.fit(phi)
        assert isinstance(r, rsm.SelfModelResult)

    def test_returns_none_on_too_short_series(self):
        phi = _ar1(n=5)
        model = rsm.RecursiveSelfModel(p=4, q=4)
        r = model.fit(phi)
        assert r is None

    def test_n_samples_correct(self):
        phi = _ar1(n=80)
        model = rsm.RecursiveSelfModel(p=4, q=4)
        r = model.fit(phi)
        assert r.n_samples == 80

    def test_r2_in_valid_range(self):
        phi = _ar1(n=80)
        model = rsm.RecursiveSelfModel(p=4, q=4)
        r = model.fit(phi)
        assert -1.0 <= r.r2_l1 <= 1.0
        assert -1.0 <= r.r2_l2 <= 1.0

    def test_depth_nonnegative(self):
        phi = _ar1(n=80)
        model = rsm.RecursiveSelfModel(p=4, q=4)
        r = model.fit(phi)
        assert r.depth >= 0.0

    def test_depth_nonnegative_on_random_walk(self):
        """depth = max(0,r2_l1)*max(0,r2_l2) — always ≥ 0."""
        rng = np.random.default_rng(99)
        phi = rng.standard_normal(80)
        model = rsm.RecursiveSelfModel(p=4, q=4, null_seed=99)
        r = model.fit(phi)
        assert r.depth >= 0.0

    def test_ar1_series_beats_l1_null(self):
        """Strong AR(1) should produce L1 R² > null."""
        phi = _ar1(n=120, alpha=0.9, noise=0.05, seed=7)
        model = rsm.RecursiveSelfModel(p=4, q=4, null_seed=42)
        r = model.fit(phi)
        assert r.r2_l1 > r.null_r2_l1

    def test_deterministic(self):
        phi = _ar1(n=80)
        model = rsm.RecursiveSelfModel(p=4, q=4, null_seed=42)
        r1 = model.fit(phi)
        r2 = model.fit(phi)
        assert r1.depth == r2.depth
        assert r1.r2_l1 == r2.r2_l1

    def test_predict_next_returns_float(self):
        phi = _ar1(n=60)
        model = rsm.RecursiveSelfModel(p=4, q=4)
        r = model.fit(phi)
        nxt = model.predict_next(r)
        assert isinstance(nxt, float)


# ── Integration: analyse() ────────────────────────────────────────────────────

class TestAnalyse:
    def test_too_few_entries_returns_none(self):
        r = _run(np.ones(5))
        assert r is None

    def test_returns_result_type(self):
        phi = _ar1(n=80)
        r = _run(phi)
        assert isinstance(r, rsm.SelfModelResult)

    def test_n_samples_matches(self):
        phi = _ar1(n=80)
        r = _run(phi)
        assert r.n_samples == 80

    def test_empty_history_returns_none(self):
        import algorithms.ConsciousnessHistoryStore as chs
        original = getattr(chs, "load", None)
        try:
            chs.load = lambda agent, max_entries=2880: []
            r = rsm.analyse("albedo")
        finally:
            if original is not None:
                chs.load = original
        assert r is None

    def test_deterministic_via_analyse(self):
        phi = _ar1(n=80)
        r1 = _run(phi, null_seed=42)
        r2 = _run(phi, null_seed=42)
        assert r1.depth == r2.depth
