#!/usr/bin/env python3
"""Tests for algorithms/HomeostaticRegulation.py."""
import sys
import math
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.HomeostaticRegulation as hr


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_history(phi_series, base_ts=1_000_000.0, dt=60.0):
    """Return newest-first list of history entries."""
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
        return hr.analyse("albedo", **kw)
    finally:
        if original is not None:
            chs.load = original


def _make_resilient(n=120, seed=0):
    """Mean-reverting AR(1) with mean 0.5 — strongly homeostatic."""
    rng = np.random.default_rng(seed)
    phi = np.zeros(n)
    phi[0] = 0.5
    for i in range(1, n):
        phi[i] = 0.5 + 0.6 * (phi[i - 1] - 0.5) + rng.normal(0, 0.05)
    return phi


def _make_random_walk(n=120, seed=1):
    """Pure random walk — no homeostasis."""
    rng = np.random.default_rng(seed)
    return np.cumsum(rng.normal(0, 0.1, n)) + 0.5


# ── Unit: _rolling ─────────────────────────────────────────────────────────────

class TestRolling:
    def test_length_matches_phi(self):
        phi = np.arange(30, dtype=float)
        mu, sig = hr._rolling(phi, w=5)
        assert len(mu) == 30
        assert len(sig) == 30

    def test_mean_last_window(self):
        phi = np.ones(20)
        phi[-5:] = 2.0
        mu, sig = hr._rolling(phi, w=5)
        # Last element's rolling mean should be 2.0
        assert mu[-1] == pytest.approx(2.0, abs=1e-6)

    def test_sig_always_positive(self):
        phi = np.ones(30)  # flat → std=0 → clamped to 1e-8
        _, sig = hr._rolling(phi, w=5)
        assert (sig > 0).all()


# ── Unit: _scan ───────────────────────────────────────────────────────────────

class TestScan:
    def test_no_perturbations_on_flat(self):
        phi = np.ones(60)
        np_, nr, rt = hr._scan(phi, w=10, p_thresh=1.5, r_thresh=0.75, max_return=10)
        assert np_ == 0
        assert nr == 0
        assert rt == []

    def test_detects_spike_and_recovery(self):
        """Insert one sharp spike; series immediately returns."""
        phi = np.zeros(80) + 0.5
        phi[40] = 5.0          # big perturbation
        phi[41:] = 0.5         # immediately returns
        np_, nr, rt = hr._scan(phi, w=10, p_thresh=1.5, r_thresh=0.75, max_return=10)
        assert np_ >= 1
        assert nr >= 1
        assert rt[0] >= 1

    def test_spike_no_recovery_counted_as_failure(self):
        """Series never returns → n_recovered should be 0."""
        phi = np.zeros(80) + 0.5
        phi[30:] = 5.0         # stays high forever — no recovery
        np_, nr, rt = hr._scan(phi, w=10, p_thresh=1.5, r_thresh=0.75, max_return=5)
        assert np_ >= 1
        assert nr == 0


# ── Unit: _h_score ────────────────────────────────────────────────────────────

class TestHScore:
    def test_zero_if_no_perturbations(self):
        assert hr._h_score(0, 0, [], 10) == 0.0

    def test_zero_if_no_recovery(self):
        assert hr._h_score(5, 0, [], 10) == 0.0

    def test_positive_if_recovered(self):
        s = hr._h_score(4, 4, [2, 2, 2, 2], 10)
        assert s > 0.0

    def test_faster_recovery_higher_score(self):
        fast = hr._h_score(4, 4, [1, 1, 1, 1], 10)
        slow = hr._h_score(4, 4, [9, 9, 9, 9], 10)
        assert fast > slow

    def test_higher_rate_higher_score(self):
        full  = hr._h_score(4, 4, [3, 3, 3, 3], 10)
        half  = hr._h_score(4, 2, [3, 3], 10)
        assert full > half


# ── Unit: _classify ───────────────────────────────────────────────────────────

class TestClassify:
    def test_resilient(self):
        assert hr._classify(0.7) == "RESILIENT"

    def test_adapting(self):
        assert hr._classify(0.4) == "ADAPTING"

    def test_dysregulated(self):
        assert hr._classify(0.1) == "DYSREGULATED"

    def test_boundary_resilient(self):
        assert hr._classify(0.6) == "RESILIENT"

    def test_boundary_adapting(self):
        assert hr._classify(0.3) == "ADAPTING"


# ── Integration: analyse() ────────────────────────────────────────────────────

class TestAnalyse:
    def test_too_few_entries_returns_default(self):
        r = _run(np.ones(10))
        assert r.n_entries <= 10
        assert r.regulation_class == "DYSREGULATED"
        assert r.n_perturbations == 0

    def test_returns_result_type(self):
        phi = _make_resilient()
        r = _run(phi)
        assert isinstance(r, hr.HomeostaticResult)

    def test_flat_phi_has_no_perturbations(self):
        phi = np.ones(80) * 0.5
        r = _run(phi)
        assert r.n_perturbations == 0
        assert r.homeostatic_score == 0.0

    def test_resilient_series_has_recoveries(self):
        """Mean-reverting AR1 should detect perturbations that recover."""
        # Build a series with guaranteed perturbations that recover
        phi = np.full(80, 0.5)
        for i in [25, 50]:
            phi[i] = 3.0      # spike
            # Returns immediately after spike (next ~5 steps)
        r = _run(phi, window=10, perturb_threshold=1.5, recover_threshold=0.75,
                 max_return_steps=10)
        # Should detect at least one perturbation and at least one recovery
        assert r.n_perturbations >= 1
        assert r.n_recovered >= 1
        assert r.resilience_rate > 0

    def test_phi_set_point_is_median(self):
        phi = np.full(80, 0.7)
        r = _run(phi)
        assert r.phi_set_point == pytest.approx(0.7, abs=0.01)

    def test_regulation_class_valid_set(self):
        phi = _make_resilient()
        r = _run(phi)
        assert r.regulation_class in {"RESILIENT", "ADAPTING", "DYSREGULATED"}

    def test_to_dict_keys(self):
        phi = _make_resilient()
        d = _run(phi).to_dict()
        for k in ("homeostatic_score", "resilience_rate", "mean_return_time",
                  "n_perturbations", "n_recovered", "null_score_p95",
                  "beats_null", "regulation_class", "phi_set_point",
                  "n_entries"):
            assert k in d

    def test_to_dict_json_serialisable(self):
        import json
        phi = _make_resilient()
        json.dumps(_run(phi).to_dict())

    def test_deterministic(self):
        phi = _make_resilient()
        r1 = _run(phi, null_seed=42)
        r2 = _run(phi, null_seed=42)
        assert r1.homeostatic_score == r2.homeostatic_score
        assert r1.regulation_class == r2.regulation_class

    def test_n_entries_correct(self):
        phi = _make_resilient(n=80)
        r = _run(phi)
        assert r.n_entries == 80

    def test_score_in_unit_interval(self):
        phi = _make_resilient()
        r = _run(phi)
        assert 0.0 <= r.homeostatic_score <= 1.0

    def test_resilience_rate_in_unit_interval(self):
        phi = _make_resilient()
        r = _run(phi)
        assert 0.0 <= r.resilience_rate <= 1.0

    def test_recovered_le_perturbations(self):
        phi = _make_resilient()
        r = _run(phi)
        assert r.n_recovered <= r.n_perturbations

    def test_random_walk_low_score_vs_resilient(self):
        """Mean-reverting series should score >= random walk."""
        phi_rev  = _make_resilient(n=100, seed=0)
        phi_rand = _make_random_walk(n=100, seed=1)
        r_rev  = _run(phi_rev,  n_shuffles=20)
        r_rand = _run(phi_rand, n_shuffles=20)
        # Not strictly guaranteed, but mean-reverting should be >= random walk
        assert r_rev.homeostatic_score >= r_rand.homeostatic_score

    def test_beats_null_is_bool(self):
        phi = _make_resilient()
        r = _run(phi, n_shuffles=20)
        assert isinstance(r.beats_null, bool)

    def test_empty_history_returns_default(self):
        import algorithms.ConsciousnessHistoryStore as chs
        original = getattr(chs, "load", None)
        try:
            chs.load = lambda agent, max_entries=2880: []
            r = hr.analyse("albedo")
        finally:
            if original is not None:
                chs.load = original
        assert r.n_entries == 0
        assert r.regulation_class == "DYSREGULATED"
