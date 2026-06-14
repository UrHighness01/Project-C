"""Tests for ConsciousnessHistoryStore."""
import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from algorithms.ConsciousnessHistoryStore import (
    MAX_ENTRIES,
    HistoryDelta,
    _entry_from_snapshot,
    _ols_slope,
    append,
    compare_now_vs_minutes_ago,
    delta,
    load,
    trend,
)


# ── _ols_slope ────────────────────────────────────────────────────────────────

def test_ols_slope_positive():
    assert _ols_slope(np.arange(10, dtype=float)) == pytest.approx(1.0)


def test_ols_slope_constant():
    assert _ols_slope(np.full(10, 5.0)) == pytest.approx(0.0, abs=1e-9)


def test_ols_slope_negative():
    assert _ols_slope(np.arange(10, 0, -1, dtype=float)) == pytest.approx(-1.0)


def test_ols_slope_single_point():
    assert _ols_slope(np.array([3.0])) == pytest.approx(0.0)


def test_ols_slope_empty():
    assert _ols_slope(np.array([])) == pytest.approx(0.0)


# ── _entry_from_snapshot ─────────────────────────────────────────────────────

def _make_snap_dict(mean_novelty=0.5, regime="ACTIVE", ts=None) -> dict:
    return {
        "timestamp": ts or time.time(),
        "n_algorithms_run": 15,
        "phi_available": True,
        "qualia_available": True,
        "algorithms": {},
        "summary": {
            "regime": regime,
            "mean_novelty": mean_novelty,
            "combined_continuity": 0.8,
            "is_continuous": True,
        },
    }


def test_entry_from_snapshot_has_timestamp():
    e = _entry_from_snapshot(_make_snap_dict())
    assert "timestamp" in e


def test_entry_from_snapshot_has_mean_novelty():
    e = _entry_from_snapshot(_make_snap_dict(mean_novelty=0.7))
    assert e["mean_novelty"] == pytest.approx(0.7)


def test_entry_from_snapshot_has_regime():
    e = _entry_from_snapshot(_make_snap_dict(regime="STRESSED"))
    assert e["regime"] == "STRESSED"


def test_entry_from_snapshot_n_algorithms_run():
    e = _entry_from_snapshot(_make_snap_dict())
    assert e["n_algorithms_run"] == 15


# ── append() and load() ───────────────────────────────────────────────────────

@pytest.fixture
def tmp_store(tmp_path):
    """Fixture: patch _store_path to use a temp dir."""
    p = tmp_path / "memory" / "consciousness_history.jsonl"
    with patch("algorithms.ConsciousnessHistoryStore._store_path", return_value=p):
        yield p


def test_append_creates_file(tmp_store):
    snap = _make_snap_dict()
    append(snap)
    assert tmp_store.exists()


def test_append_load_roundtrip(tmp_store):
    snap = _make_snap_dict(mean_novelty=0.6)
    append(snap)
    entries = load()
    assert len(entries) == 1
    assert entries[0]["mean_novelty"] == pytest.approx(0.6)


def test_load_empty_when_no_file(tmp_store):
    entries = load()
    assert entries == []


def test_append_multiple_entries(tmp_store):
    for i in range(5):
        append(_make_snap_dict(mean_novelty=i * 0.1, ts=1000.0 + i))
    entries = load()
    assert len(entries) == 5


def test_load_newest_first(tmp_store):
    for i in range(3):
        append(_make_snap_dict(ts=1000.0 + i))
    entries = load()
    assert entries[0]["timestamp"] >= entries[-1]["timestamp"]


def test_append_cap_enforced(tmp_store):
    for i in range(MAX_ENTRIES + 10):
        append(_make_snap_dict(ts=float(i)))
    entries = load()
    assert len(entries) <= MAX_ENTRIES


def test_append_cap_keeps_newest(tmp_store):
    for i in range(MAX_ENTRIES + 5):
        append(_make_snap_dict(ts=float(i)))
    entries = load()
    # Newest entry timestamp should be MAX_ENTRIES+4
    assert entries[0]["timestamp"] == pytest.approx(MAX_ENTRIES + 4)


def test_append_custom_cap(tmp_store):
    for i in range(20):
        append(_make_snap_dict(ts=float(i)), max_entries=10)
    entries = load()
    assert len(entries) <= 10


def test_append_accepts_dict_with_to_dict(tmp_store):
    class FakeSnap:
        def to_dict(self):
            return _make_snap_dict()
    append(FakeSnap())
    assert len(load()) == 1


def test_load_max_entries_param(tmp_store):
    for i in range(20):
        append(_make_snap_dict(ts=float(i)))
    entries = load(max_entries=5)
    assert len(entries) == 5


# ── delta() ──────────────────────────────────────────────────────────────────

def test_delta_numeric_difference():
    now = {"mean_novelty": 0.7, "combined_continuity": 0.9}
    then = {"mean_novelty": 0.5, "combined_continuity": 0.8}
    d = delta(now, then)
    assert d["mean_novelty"] == pytest.approx(0.2)
    assert d["combined_continuity"] == pytest.approx(0.1)


def test_delta_excludes_timestamp():
    now = {"timestamp": 2000.0, "mean_novelty": 0.7}
    then = {"timestamp": 1000.0, "mean_novelty": 0.5}
    d = delta(now, then)
    assert "timestamp" not in d


def test_delta_excludes_string_keys():
    now = {"regime": "ACTIVE", "mean_novelty": 0.7}
    then = {"regime": "STRESSED", "mean_novelty": 0.5}
    d = delta(now, then)
    assert "regime" not in d


def test_delta_missing_key_excluded():
    now = {"mean_novelty": 0.7}
    then = {"combined_continuity": 0.8}
    d = delta(now, then)
    assert d == {}


def test_delta_negative_change():
    now = {"mean_novelty": 0.3}
    then = {"mean_novelty": 0.7}
    d = delta(now, then)
    assert d["mean_novelty"] == pytest.approx(-0.4)


# ── trend() ──────────────────────────────────────────────────────────────────

def test_trend_positive():
    entries = [{"mean_novelty": float(i) * 0.1} for i in range(10)]
    s = trend("mean_novelty", entries)
    assert s is not None
    assert s > 0


def test_trend_constant_zero():
    entries = [{"mean_novelty": 0.5}] * 10
    s = trend("mean_novelty", entries)
    assert s == pytest.approx(0.0, abs=1e-9)


def test_trend_missing_key_none():
    entries = [{"other": 1.0}] * 5
    s = trend("mean_novelty", entries)
    assert s is None


def test_trend_single_entry_none():
    entries = [{"mean_novelty": 0.5}]
    s = trend("mean_novelty", entries)
    assert s is None


def test_trend_window_limits():
    entries = [{"mean_novelty": float(i)} for i in range(100)]
    # Only last 10 entries used; slope over i=90..99 → 1.0
    s = trend("mean_novelty", entries, window=10)
    assert s == pytest.approx(1.0)


# ── compare_now_vs_minutes_ago() ──────────────────────────────────────────────

def test_compare_returns_none_insufficient(tmp_store):
    append(_make_snap_dict())  # only 1 entry
    result = compare_now_vs_minutes_ago()
    assert result is None


def test_compare_returns_delta(tmp_store):
    t_base = time.time() - 700  # ~12 min ago
    for i in range(15):
        append(_make_snap_dict(mean_novelty=0.3 + i * 0.01, ts=t_base + i * 60))
    result = compare_now_vs_minutes_ago(minutes=10)
    assert isinstance(result, HistoryDelta)


def test_compare_seconds_apart_non_negative(tmp_store):
    t_base = time.time() - 700
    for i in range(15):
        append(_make_snap_dict(ts=t_base + i * 60))
    result = compare_now_vs_minutes_ago(minutes=10)
    assert result.seconds_apart >= 0


def test_compare_mood_shift_improving(tmp_store):
    t_base = time.time() - 700
    for i in range(15):
        # novelty grows from 0.3 → 0.7
        append(_make_snap_dict(mean_novelty=0.3 + i * 0.03, ts=t_base + i * 60))
    result = compare_now_vs_minutes_ago(minutes=10)
    # Now ~0.72, then ~0.3 → delta > 0.05 → IMPROVING
    assert result.mood_shift in ("IMPROVING", "STABLE", "DEGRADING")


def test_compare_mood_shift_stable(tmp_store):
    t_base = time.time() - 700
    for i in range(15):
        append(_make_snap_dict(mean_novelty=0.5, ts=t_base + i * 60))
    result = compare_now_vs_minutes_ago(minutes=10)
    assert result.mood_shift == "STABLE"


def test_compare_to_dict_serializable(tmp_store):
    t_base = time.time() - 700
    for i in range(15):
        append(_make_snap_dict(ts=t_base + i * 60))
    result = compare_now_vs_minutes_ago(minutes=10)
    json.dumps(result.to_dict())


def test_compare_changes_dict_numeric(tmp_store):
    t_base = time.time() - 700
    for i in range(15):
        append(_make_snap_dict(mean_novelty=0.3 + i * 0.01, ts=t_base + i * 60))
    result = compare_now_vs_minutes_ago(minutes=10)
    for k, v in result.changes.items():
        assert isinstance(v, float), f"{k} should be float"


def test_history_delta_to_dict_keys():
    d = HistoryDelta(
        timestamp_now=2000.0,
        timestamp_then=1000.0,
        seconds_apart=1000.0,
        changes={"mean_novelty": 0.1},
        trends={"mean_novelty": 0.001},
        mood_shift="STABLE",
        novelty_delta=0.1,
        continuity_delta=None,
    )
    di = d.to_dict()
    for k in ["timestamp_now", "timestamp_then", "seconds_apart",
              "changes", "trends", "mood_shift", "novelty_delta", "continuity_delta"]:
        assert k in di
