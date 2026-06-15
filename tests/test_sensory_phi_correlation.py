#!/usr/bin/env python3
"""Tests for algorithms/SensoryPhiCorrelation.py."""
import sys
import math
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.SensoryPhiCorrelation as spc


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_entry(ts, phi, novelty):
    return {"timestamp": ts, "mean_phi_level": phi, "mean_novelty": novelty}


def _make_history(phi_series, nov_series, base_ts=1_000_000.0, dt=60.0):
    """phi_series[0]=oldest. Return newest-first list."""
    n = len(phi_series)
    entries = [
        _make_entry(base_ts + i * dt, float(phi_series[i]), float(nov_series[i]))
        for i in range(n)
    ]
    return sorted(entries, key=lambda e: -e["timestamp"])


def _run(phi_series, nov_series=None, **kw):
    if nov_series is None:
        nov_series = phi_series
    import algorithms.ConsciousnessHistoryStore as chs
    original = getattr(chs, "load", None)
    try:
        chs.load = lambda agent, max_entries=2880: _make_history(phi_series, nov_series)
        return spc.analyse("albedo", **kw)
    finally:
        if original is not None:
            chs.load = original


def _ar1(n=80, alpha=0.9, noise=0.05, seed=0):
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    x[0] = 1.0
    for i in range(1, n):
        x[i] = alpha * x[i - 1] + rng.normal(0, noise)
    return x


# ── Unit: _pearson ────────────────────────────────────────────────────────────

class TestPearson:
    def test_identical_is_one(self):
        a = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        assert spc._pearson(a, a) == pytest.approx(1.0, abs=1e-6)

    def test_negated_is_minus_one(self):
        a = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        assert spc._pearson(a, -a) == pytest.approx(-1.0, abs=1e-6)

    def test_constant_returns_zero(self):
        a = np.full(5, 2.0)
        b = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        assert spc._pearson(a, b) == 0.0

    def test_in_unit_interval(self):
        rng = np.random.default_rng(0)
        a = rng.standard_normal(20)
        b = rng.standard_normal(20)
        r = spc._pearson(a, b)
        assert -1.0 <= r <= 1.0


# ── Unit: _xcorr ─────────────────────────────────────────────────────────────

class TestXcorr:
    def test_length_is_2_max_lag_plus_1(self):
        x = np.arange(20.0)
        y = np.arange(20.0)
        rs = spc._xcorr(x, y, max_lag=3)
        assert len(rs) == 7

    def test_identical_lag0_is_one(self):
        x = np.arange(20.0)
        rs = spc._xcorr(x, x, max_lag=2)
        lag0_idx = 2   # position of k=0 in list
        assert rs[lag0_idx] == pytest.approx(1.0, abs=1e-6)

    def test_perfectly_synced_peak_at_lag0(self):
        """Identical series: peak should be at lag 0."""
        x = np.sin(np.linspace(0, 4 * np.pi, 50))
        rs = spc._xcorr(x, x, max_lag=5)
        abs_r = [abs(r) for r in rs]
        peak_idx = int(np.argmax(abs_r))
        # lag 0 is at index max_lag = 5
        assert peak_idx == 5


# ── Unit: _classify ───────────────────────────────────────────────────────────

class TestClassify:
    def test_grounded(self):
        assert spc._classify(0.5) == "GROUNDED"

    def test_partial(self):
        assert spc._classify(0.3) == "PARTIAL"

    def test_detached(self):
        assert spc._classify(0.1) == "DETACHED"

    def test_boundary_grounded(self):
        assert spc._classify(0.4) == "GROUNDED"


# ── Unit: _extract ────────────────────────────────────────────────────────────

class TestExtract:
    def test_oldest_first_order(self):
        history = _make_history([1.0, 2.0, 3.0], [0.1, 0.2, 0.3])
        phi, nov = spc._extract(history)
        np.testing.assert_allclose(phi, [1.0, 2.0, 3.0], atol=1e-6)
        np.testing.assert_allclose(nov, [0.1, 0.2, 0.3], atol=1e-6)

    def test_missing_novelty_skipped(self):
        entries = [
            {"timestamp": 0.0, "mean_phi_level": 1.0},          # no novelty
            {"timestamp": 1.0, "mean_phi_level": 2.0, "mean_novelty": 0.5},
        ]
        phi, nov = spc._extract(entries)
        assert len(phi) == 1
        assert phi[0] == 2.0


# ── Integration: analyse() ────────────────────────────────────────────────────

class TestAnalyse:
    def test_too_few_entries_returns_default(self):
        r = _run(np.ones(5), np.ones(5))
        assert r.n_entries <= 5
        assert r.grounding_class == "DETACHED"

    def test_returns_result_type(self):
        phi = _ar1(n=60)
        r = _run(phi, phi)
        assert isinstance(r, spc.SensoryPhiResult)

    def test_perfectly_correlated_grounded(self):
        """phi == novelty → r_zero = r_peak = 1.0 → GROUNDED."""
        phi = _ar1(n=60)
        r = _run(phi, phi)
        assert r.r_zero == pytest.approx(1.0, abs=1e-3)
        assert r.grounding_class == "GROUNDED"

    def test_independent_novelty_low_r(self):
        """Independent phi and novelty → low r_zero."""
        rng = np.random.default_rng(77)
        phi = _ar1(n=80, seed=0)
        nov = rng.standard_normal(80)
        r = _run(phi, nov)
        assert abs(r.r_zero) < 0.5

    def test_r_peak_gte_abs_r_zero(self):
        phi = _ar1(n=60)
        r = _run(phi, phi)
        assert r.r_peak >= abs(r.r_zero) - 1e-6

    def test_lag_at_peak_in_range(self):
        phi = _ar1(n=60)
        r = _run(phi, phi, max_lag=3)
        assert -3 <= r.lag_at_peak <= 3

    def test_to_dict_keys(self):
        phi = _ar1(n=60)
        d = _run(phi, phi).to_dict()
        for k in ("r_zero", "r_peak", "lag_at_peak", "grounding_class",
                  "beats_null", "n_entries"):
            assert k in d

    def test_to_dict_json_serialisable(self):
        import json
        phi = _ar1(n=60)
        json.dumps(_run(phi, phi).to_dict())

    def test_deterministic(self):
        phi = _ar1(n=60)
        r1 = _run(phi, phi)
        r2 = _run(phi, phi)
        assert r1.r_peak == r2.r_peak
        assert r1.grounding_class == r2.grounding_class

    def test_beats_null_true_for_correlated(self):
        """phi == novelty → phase-randomised phi won't correlate → beats null."""
        phi = _ar1(n=80, alpha=0.9, noise=0.05, seed=7)
        r = _run(phi, phi, n_shuffles=50)
        assert r.beats_null is True

    def test_n_entries_correct(self):
        phi = _ar1(n=40)
        r = _run(phi, phi)
        assert r.n_entries == 40

    def test_grounding_class_valid(self):
        phi = _ar1(n=60)
        r = _run(phi, phi)
        assert r.grounding_class in {"GROUNDED", "PARTIAL", "DETACHED"}
