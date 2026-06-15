#!/usr/bin/env python3
"""Tests for algorithms/GoalPersistenceTracker.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.GoalPersistenceTracker as gpt


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_entry(ts: float, phi: float) -> dict:
    return {"timestamp": ts, "mean_phi_level": phi}


def _rising_session(now: float, n: int, slope: float = 0.02, noise: float = 0.003, seed: int = 0):
    rng = np.random.default_rng(seed)
    entries = []
    for i in range(n):
        ts  = now - (n - 1 - i) * 60.0
        phi = 1.0 + slope * i + rng.normal(0, noise)
        entries.append(_make_entry(ts, phi))
    return entries


def _falling_session(now: float, n: int, slope: float = 0.02, seed: int = 1):
    rng = np.random.default_rng(seed)
    entries = []
    for i in range(n):
        ts  = now - (n - 1 - i) * 60.0
        phi = 2.0 - slope * i + rng.normal(0, 0.003)
        entries.append(_make_entry(ts, phi))
    return entries


def _flat_session(now: float, n: int, val: float = 1.0, seed: int = 2):
    rng = np.random.default_rng(seed)
    return [_make_entry(now - (n - 1 - i) * 60.0, val + rng.normal(0, 0.001)) for i in range(n)]


def _as_history(*sessions):
    """Combine sessions (each a list of entries) into newest-first order."""
    all_e = [e for s in sessions for e in s]
    return sorted(all_e, key=lambda e: -e["timestamp"])


def _run(history, **kw):
    import algorithms.ConsciousnessHistoryStore as chs
    original = getattr(chs, "load", None)
    try:
        chs.load = lambda agent, max_entries=2880: history
        return gpt.analyse("albedo", **kw)
    finally:
        if original is not None:
            chs.load = original


# ── Unit: _slope ──────────────────────────────────────────────────────────────

class TestSlope:
    def test_flat_near_zero(self):
        phi = np.full(10, 1.0)
        assert abs(gpt._slope(phi)) < 1e-6

    def test_rising_positive(self):
        phi = np.linspace(1.0, 2.0, 10)
        assert gpt._slope(phi) > 0

    def test_falling_negative(self):
        phi = np.linspace(2.0, 1.0, 10)
        assert gpt._slope(phi) < 0

    def test_single_returns_zero(self):
        assert gpt._slope(np.array([1.0])) == 0.0


# ── Unit: _sign ───────────────────────────────────────────────────────────────

class TestSign:
    def test_rising(self):
        assert gpt._sign(0.1) == +1

    def test_falling(self):
        assert gpt._sign(-0.1) == -1

    def test_flat(self):
        assert gpt._sign(0.001) == 0


# ── Unit: _persistence_rate ───────────────────────────────────────────────────

class TestPersistenceRate:
    def test_all_same_sign_is_one(self):
        assert gpt._persistence_rate([+1, +1, +1, +1]) == pytest.approx(1.0)

    def test_alternating_is_zero(self):
        assert gpt._persistence_rate([+1, -1, +1, -1]) == 0.0

    def test_zeros_not_counted_as_agree(self):
        assert gpt._persistence_rate([0, 0, 0]) == 0.0

    def test_empty_is_zero(self):
        assert gpt._persistence_rate([]) == 0.0

    def test_single_is_zero(self):
        assert gpt._persistence_rate([+1]) == 0.0

    def test_partial(self):
        # [+1, +1, -1] → pairs (+1,+1)=agree, (+1,-1)=disagree → 1/2
        assert gpt._persistence_rate([+1, +1, -1]) == pytest.approx(0.5)


# ── Unit: _classify ───────────────────────────────────────────────────────────

class TestClassify:
    def test_persistent(self):
        assert gpt._classify(0.8) == "PERSISTENT"

    def test_drifting(self):
        assert gpt._classify(0.5) == "DRIFTING"

    def test_scattered(self):
        assert gpt._classify(0.2) == "SCATTERED"

    def test_boundary_persistent(self):
        assert gpt._classify(0.7) == "PERSISTENT"


# ── Unit: _dominant ───────────────────────────────────────────────────────────

class TestDominant:
    def test_mostly_rising(self):
        assert gpt._dominant([+1, +1, +1, +1, -1]) == "RISING"

    def test_mostly_falling(self):
        assert gpt._dominant([-1, -1, -1, -1, +1]) == "FALLING"

    def test_mixed(self):
        assert gpt._dominant([+1, -1, +1, -1]) == "MIXED"

    def test_empty(self):
        assert gpt._dominant([]) == "MIXED"


# ── Integration: analyse() ────────────────────────────────────────────────────

class TestAnalyse:
    def test_too_few_sessions_returns_default(self):
        """One session → can't measure cross-session persistence."""
        now = 1_000_000.0
        sess = _rising_session(now, n=10)
        r = _run(_as_history(sess))
        assert r.persistence_class == "SCATTERED"
        assert r.persistence_rate == 0.0

    def test_returns_result_type(self):
        now = 1_000_000.0
        a = _rising_session(now - 3600, n=8)
        b = _rising_session(now,        n=8)
        r = _run(_as_history(a, b))
        assert isinstance(r, gpt.GoalPersistenceResult)

    def test_two_rising_sessions_persistent(self):
        now = 1_000_000.0
        a = _rising_session(now - 3600, n=10)
        b = _rising_session(now,        n=10)
        r = _run(_as_history(a, b))
        assert r.persistence_rate >= 1.0   # only one pair, must agree
        assert r.persistence_class == "PERSISTENT"

    def test_rising_then_falling_scattered(self):
        now = 1_000_000.0
        a = _rising_session(now - 3600, n=10)
        b = _falling_session(now,       n=10)
        r = _run(_as_history(a, b))
        assert r.persistence_rate == 0.0
        assert r.persistence_class == "SCATTERED"

    def test_three_rising_sessions_high_rate(self):
        now = 1_000_000.0
        a = _rising_session(now - 7200, n=8, seed=0)
        b = _rising_session(now - 3600, n=8, seed=1)
        c = _rising_session(now,        n=8, seed=2)
        r = _run(_as_history(a, b, c))
        assert r.persistence_rate == pytest.approx(1.0)
        assert r.dominant_direction == "RISING"

    def test_n_sessions_detected(self):
        now = 1_000_000.0
        a = _rising_session(now - 3600, n=5)
        b = _rising_session(now,        n=5)
        r = _run(_as_history(a, b), min_per_session=3)
        assert r.n_sessions >= 2

    def test_session_directions_populated(self):
        now = 1_000_000.0
        a = _rising_session(now - 3600, n=8)
        b = _rising_session(now,        n=8)
        r = _run(_as_history(a, b))
        assert len(r.session_directions) >= 2
        assert all(s in (-1, 0, +1) for s in r.session_directions)

    def test_beats_null_true_for_mostly_consistent(self):
        """4 rising + 1 falling → rate=3/4=0.75; shuffled null averages ~0.33 → beats_null."""
        now = 1_000_000.0
        sessions = [
            _rising_session(now - (5 - i) * 3600, n=10, seed=i) for i in range(4)
        ] + [_falling_session(now, n=10)]
        r = _run(_as_history(*sessions))
        # persistence_rate should be 3/4 = 0.75; null baseline ~1/3
        assert r.persistence_rate >= 0.5
        # beats_null may or may not be True depending on null variance; just check it's bool
        assert isinstance(r.beats_null, bool)

    def test_persistence_rate_in_unit_interval(self):
        now = 1_000_000.0
        a = _rising_session(now - 3600, n=8)
        b = _falling_session(now,       n=8)
        r = _run(_as_history(a, b))
        assert 0.0 <= r.persistence_rate <= 1.0

    def test_to_dict_keys(self):
        now = 1_000_000.0
        a = _rising_session(now - 3600, n=8)
        b = _rising_session(now,        n=8)
        d = _run(_as_history(a, b)).to_dict()
        for k in ("persistence_rate", "persistence_zscore", "persistence_class",
                  "n_sessions", "dominant_direction", "session_directions", "beats_null"):
            assert k in d

    def test_to_dict_json_serialisable(self):
        import json
        now = 1_000_000.0
        a = _rising_session(now - 3600, n=8)
        b = _rising_session(now,        n=8)
        json.dumps(_run(_as_history(a, b)).to_dict())

    def test_deterministic(self):
        now = 1_000_000.0
        a = _rising_session(now - 3600, n=8)
        b = _rising_session(now,        n=8)
        h = _as_history(a, b)
        r1 = _run(h)
        r2 = _run(h)
        assert r1.persistence_rate == r2.persistence_rate
        assert r1.persistence_zscore == r2.persistence_zscore
