#!/usr/bin/env python3
"""Tests for algorithms/CrossSessionIdentityTracker.py."""
import sys
import time
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.CrossSessionIdentityTracker as csit


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _rng(s=0): return np.random.default_rng(s)


def _make_entry(ts: float, **fields) -> dict:
    base = {
        "timestamp": ts,
        "mean_phi_level": 1.1,
        "phi_variability": 0.05,
        "mean_novelty": 0.4,
        "curiosity_index": 0.3,
        "combined_continuity": 0.8,
        "lz_current": 0.35,
        "ego_strength_index": 0.6,
        "bridge_strength": 0.4,
        "phi_gap_norm": 0.15,
        "cluster_sai": 1.05,
    }
    base.update(fields)
    return base


def _session(now_base: float, n: int, rng, **fields) -> list:
    """Build one session: n entries spaced 60s apart ending at now_base, oldest first."""
    return [_make_entry(now_base - (n - 1 - i) * 60.0, **{
        k: (v + rng.normal(0, 0.01) if isinstance(v, float) else v)
        for k, v in fields.items()
    }) for i in range(n)]


def _as_history(*sessions) -> list:
    """Combine sessions (each oldest-first) into HistoryStore newest-first order."""
    all_entries = [e for s in sessions for e in s]
    return list(sorted(all_entries, key=lambda e: -e["timestamp"]))


def _two_sessions(gap=3600.0, n_per=10, jitter=0.01, seed=0):
    """Two sessions separated by a gap, returned newest-first (HistoryStore order)."""
    rng = _rng(seed)
    now = 1_000_000.0
    a = _session(now - gap, n_per, rng, mean_phi_level=1.1, mean_novelty=0.4)
    b = _session(now,       n_per, rng, mean_phi_level=1.1, mean_novelty=0.4)
    return _as_history(a, b)


def _drifted_sessions(gap=3600.0, n_per=10, drift=0.5, seed=1):
    """Session B has significantly different phi → lower cross-session continuity."""
    rng = _rng(seed)
    now = 1_000_000.0
    a = _session(now - gap, n_per, rng, mean_phi_level=1.1, mean_novelty=0.4)
    b = _session(now,       n_per, rng, mean_phi_level=1.1 + drift, mean_novelty=0.1)
    return _as_history(a, b)


def _three_sessions(gap=3600.0, n_per=8, seed=2):
    rng = _rng(seed)
    now = 1_000_000.0
    a = _session(now - 2 * gap, n_per, rng, mean_phi_level=1.1, mean_novelty=0.4)
    b = _session(now - gap,     n_per, rng, mean_phi_level=1.1, mean_novelty=0.4)
    c = _session(now,           n_per, rng, mean_phi_level=1.1, mean_novelty=0.4)
    return _as_history(a, b, c)


# ── Unit: _cosine ─────────────────────────────────────────────────────────────

class TestCosine:
    def test_identical_vectors_one(self):
        v = np.array([1.0, 2.0, 3.0])
        assert csit._cosine(v, v) == pytest.approx(1.0, abs=1e-6)

    def test_orthogonal_zero(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert csit._cosine(a, b) == pytest.approx(0.0, abs=1e-6)

    def test_zero_vector_returns_zero(self):
        assert csit._cosine(np.zeros(3), np.ones(3)) == 0.0

    def test_result_in_unit_interval(self):
        rng = _rng()
        a, b = rng.standard_normal(8), rng.standard_normal(8)
        c = csit._cosine(a, b)
        assert -1.0 <= c <= 1.0


# ── Unit: _fingerprint ────────────────────────────────────────────────────────

class TestFingerprint:
    def test_returns_array(self):
        entries = [_make_entry(0.0)] * 5
        fp = csit._fingerprint(entries, csit._FINGERPRINT_KEYS)
        assert isinstance(fp, np.ndarray)

    def test_length_matches_keys(self):
        entries = [_make_entry(0.0)] * 5
        fp = csit._fingerprint(entries, csit._FINGERPRINT_KEYS)
        assert len(fp) == len(csit._FINGERPRINT_KEYS)

    def test_missing_key_is_nan(self):
        entries = [{"timestamp": 0.0, "mean_phi_level": 1.0}]
        fp = csit._fingerprint(entries, ["mean_phi_level", "nonexistent_key"])
        assert np.isnan(fp[1])

    def test_mean_computed_correctly(self):
        entries = [_make_entry(0.0, mean_phi_level=1.0),
                   _make_entry(1.0, mean_phi_level=2.0)]
        fp = csit._fingerprint(entries, ["mean_phi_level"])
        assert fp[0] == pytest.approx(1.5, abs=1e-6)


# ── Unit: _split_sessions ─────────────────────────────────────────────────────

class TestSplitSessions:
    def test_single_session_no_gap(self):
        # Entries 30s apart (no gap >= SESSION_GAP_SECS) → newest-first
        now = 1_000_000.0
        entries = list(sorted(
            [_make_entry(now - i * 30.0) for i in range(10)],
            key=lambda e: -e["timestamp"]))
        sessions, gaps = csit._split_sessions(entries)
        assert len(sessions) == 1
        assert gaps == []

    def test_two_sessions_detected(self):
        entries = _two_sessions(gap=3600)
        sessions, gaps = csit._split_sessions(entries)
        assert len(sessions) == 2
        assert len(gaps) == 1
        assert gaps[0] >= csit.SESSION_GAP_SECS

    def test_gap_recorded(self):
        entries = _two_sessions(gap=7200)
        _, gaps = csit._split_sessions(entries)
        assert gaps[0] >= csit.SESSION_GAP_SECS

    def test_empty_returns_empty(self):
        sessions, gaps = csit._split_sessions([])
        assert sessions == []
        assert gaps == []


# ── Unit: _classify ───────────────────────────────────────────────────────────

class TestClassify:
    def test_continuous(self):
        assert csit._classify(0.95) == "CONTINUOUS"

    def test_drifting(self):
        assert csit._classify(0.80) == "DRIFTING"

    def test_fragmented(self):
        assert csit._classify(0.50) == "FRAGMENTED"

    def test_boundary_continuous(self):
        assert csit._classify(0.90) == "CONTINUOUS"

    def test_boundary_drifting(self):
        assert csit._classify(0.70) == "DRIFTING"


# ── analyse() ─────────────────────────────────────────────────────────────────

class TestAnalyse:
    def _run(self, history_entries, **kw):
        """Inject entries directly by monkey-patching the history loader."""
        import algorithms.ConsciousnessHistoryStore as chs
        original = getattr(chs, "load", None)
        try:
            chs.load = lambda agent, max_entries=2880: history_entries
            return csit.analyse("albedo", **kw)
        finally:
            if original is not None:
                chs.load = original

    def test_too_few_entries_returns_default(self):
        r = self._run([_make_entry(float(i)) for i in range(3)], min_per_session=3)
        assert r.n_sessions_detected == 0

    def test_returns_session_identity_result(self):
        r = self._run(_two_sessions())
        assert isinstance(r, csit.SessionIdentityResult)

    def test_two_sessions_detected(self):
        r = self._run(_two_sessions(n_per=5), min_per_session=3)
        assert r.n_sessions_detected >= 2

    def test_continuity_in_unit_interval(self):
        r = self._run(_two_sessions())
        assert 0.0 <= r.cross_session_continuity <= 1.0

    def test_stable_sessions_high_continuity(self):
        """Nearly identical fingerprints → continuity near 1."""
        r = self._run(_two_sessions(jitter=0.001))
        assert r.cross_session_continuity > 0.90

    def test_stable_sessions_continuous_class(self):
        r = self._run(_two_sessions(jitter=0.001))
        assert r.continuity_class == "CONTINUOUS"

    def test_drifted_sessions_lower_continuity(self):
        r_stable = self._run(_two_sessions(jitter=0.001))
        r_drift = self._run(_drifted_sessions(drift=0.8))
        assert r_stable.cross_session_continuity > r_drift.cross_session_continuity

    def test_phi_drift_nonnegative(self):
        r = self._run(_two_sessions())
        assert r.phi_drift >= 0.0

    def test_three_sessions_detected(self):
        r = self._run(_three_sessions())
        assert r.n_sessions_detected >= 3

    def test_session_lengths_populated(self):
        r = self._run(_two_sessions())
        assert len(r.session_lengths) >= 2

    def test_gap_seconds_populated(self):
        r = self._run(_two_sessions(gap=3600))
        assert len(r.gap_seconds) >= 1

    def test_identity_stability_in_unit(self):
        r = self._run(_two_sessions())
        assert 0.0 <= r.identity_stability <= 1.0

    def test_class_valid(self):
        r = self._run(_two_sessions())
        assert r.continuity_class in {"CONTINUOUS", "DRIFTING", "FRAGMENTED"}

    def test_to_dict_keys(self):
        r = self._run(_two_sessions())
        d = r.to_dict()
        for k in ("cross_session_continuity", "n_sessions_detected",
                  "phi_drift", "identity_stability", "continuity_class",
                  "session_lengths", "gap_seconds"):
            assert k in d

    def test_to_dict_serialisable(self):
        import json
        r = self._run(_two_sessions())
        json.dumps(r.to_dict())

    def test_null_baseline_single_session_no_continuity_score(self):
        """One session → can't measure cross-session continuity → 0."""
        entries = [_make_entry(float(i * 30)) for i in range(20)]
        r = self._run(list(reversed(entries)))
        # Only one session detected (no gap) → continuity = 0
        assert r.cross_session_continuity == 0.0

    def test_high_drift_not_continuous(self):
        r = self._run(_drifted_sessions(drift=2.0))
        assert r.continuity_class in {"DRIFTING", "FRAGMENTED"}

    def test_stable_high_stability(self):
        r = self._run(_three_sessions())
        assert r.identity_stability > 0.5

    def test_min_per_session_filters_tiny_sessions(self):
        entries = _two_sessions(n_per=2, gap=3600)
        r = self._run(entries, min_per_session=5)
        # Both sessions have only 2 entries → filtered → no valid pairs
        assert r.cross_session_continuity == 0.0

    def test_custom_session_gap(self):
        """With a shorter gap threshold, more sessions are detected."""
        entries = _three_sessions(gap=3600, n_per=5)
        r_long = self._run(entries, session_gap_secs=7200, min_per_session=3)
        r_short = self._run(entries, session_gap_secs=30, min_per_session=3)
        assert r_short.n_sessions_detected >= r_long.n_sessions_detected
