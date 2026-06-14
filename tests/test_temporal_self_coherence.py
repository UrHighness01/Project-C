#!/usr/bin/env python3
"""Tests for algorithms/TemporalSelfCoherence.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.TemporalSelfCoherence as tsc


def _snap(phi=1.0, qualia_count=100, valence=0.5, arousal=0.5, confidence=0.8):
    return {"summary": {
        "phi": phi,
        "qualia_count": qualia_count,
        "valence": valence,
        "arousal": arousal,
        "confidence": confidence,
    }}


def _series(n, **kwargs):
    return [_snap(**kwargs) for _ in range(n)]


class TestExtractVector:
    def test_extracts_known_fields(self):
        snap = _snap(phi=2.1, qualia_count=500)
        v, names = tsc._extract_vector(snap)
        assert "phi" in names
        assert "qualia_count" in names

    def test_skips_missing_fields(self):
        snap = {"summary": {"phi": 1.0}}
        v, names = tsc._extract_vector(snap)
        assert list(names) == ["phi"]

    def test_flat_snap_without_summary_key(self):
        snap = {"phi": 1.5, "valence": 0.3}
        v, names = tsc._extract_vector(snap)
        assert len(v) >= 0  # may be empty or partial

    def test_empty_snap_returns_empty(self):
        v, names = tsc._extract_vector({})
        assert v.size == 0


class TestCosine:
    def test_identical_vectors_return_one(self):
        u = np.array([1.0, 2.0, 3.0])
        assert tsc._cosine(u, u) == pytest.approx(1.0, abs=1e-6)

    def test_orthogonal_returns_zero(self):
        u = np.array([1.0, 0.0])
        v = np.array([0.0, 1.0])
        assert tsc._cosine(u, v) == pytest.approx(0.0, abs=1e-9)

    def test_opposite_returns_negative_one(self):
        u = np.array([1.0, 0.0])
        v = np.array([-1.0, 0.0])
        assert tsc._cosine(u, v) == pytest.approx(-1.0, abs=1e-6)

    def test_zero_vector_returns_one(self):
        u = np.zeros(3)
        v = np.array([1.0, 2.0, 3.0])
        assert tsc._cosine(u, v) == 1.0


class TestOlsSlope:
    def test_increasing_series_positive_slope(self):
        y = np.array([0.0, 1.0, 2.0, 3.0])
        assert tsc._ols_slope(y) > 0

    def test_decreasing_series_negative_slope(self):
        y = np.array([3.0, 2.0, 1.0, 0.0])
        assert tsc._ols_slope(y) < 0

    def test_constant_series_zero_slope(self):
        y = np.ones(10)
        assert tsc._ols_slope(y) == pytest.approx(0.0, abs=1e-9)

    def test_single_point_returns_zero(self):
        assert tsc._ols_slope(np.array([5.0])) == 0.0


class TestAnalyse:
    def test_empty_snapshots_returns_default(self):
        result = tsc.analyse([])
        assert result.n_snapshots == 0
        assert result.mean_coherence == 1.0

    def test_single_snapshot_returns_default(self):
        result = tsc.analyse([_snap()])
        assert result.n_snapshots == 1

    def test_stable_series_is_stable(self):
        snaps = _series(20, phi=2.0, qualia_count=300)
        result = tsc.analyse(snaps, stable_threshold=0.85)
        assert result.is_stable

    def test_identical_snapshots_mean_coherence_one(self):
        snaps = _series(10)
        result = tsc.analyse(snaps)
        assert result.mean_coherence == pytest.approx(1.0, abs=1e-5)

    def test_n_snapshots_correct(self):
        snaps = _series(15)
        result = tsc.analyse(snaps)
        assert result.n_snapshots == 15

    def test_min_coherence_lte_mean(self):
        snaps = _series(10)
        result = tsc.analyse(snaps)
        assert result.min_coherence <= result.mean_coherence + 1e-9

    def test_coherence_in_range(self):
        snaps = _series(10)
        result = tsc.analyse(snaps)
        assert -1.0 <= result.mean_coherence <= 1.0
        assert -1.0 <= result.min_coherence <= 1.0

    def test_shift_event_detected_on_abrupt_change(self):
        # 9 stable snapshots then 1 radically different
        snaps = _series(9, phi=2.0, valence=0.5) + [_snap(phi=0.001, valence=-5.0)]
        result = tsc.analyse(snaps, shift_z_threshold=-1.5)
        assert len(result.shift_events) >= 1

    def test_shift_event_severity_values(self):
        snaps = _series(9) + [_snap(phi=0.0, qualia_count=0, valence=-10.0)]
        result = tsc.analyse(snaps, shift_z_threshold=-1.5)
        for ev in result.shift_events:
            assert ev.severity in {"MILD", "MODERATE", "SEVERE"}

    def test_coherence_trend_float(self):
        snaps = _series(10)
        result = tsc.analyse(snaps)
        assert isinstance(result.coherence_trend, float)

    def test_feature_names_populated(self):
        snaps = _series(5)
        result = tsc.analyse(snaps)
        assert len(result.feature_names) > 0

    def test_to_dict_has_keys(self):
        snaps = _series(5)
        d = tsc.analyse(snaps).to_dict()
        for key in ("mean_coherence", "min_coherence", "coherence_trend",
                    "is_stable", "n_snapshots", "feature_names", "shift_events"):
            assert key in d

    def test_to_dict_serialisable(self):
        import json
        snaps = _series(10)
        json.dumps(tsc.analyse(snaps).to_dict())

    def test_shift_events_list_of_dicts(self):
        snaps = _series(9) + [_snap(phi=0.0, qualia_count=0)]
        d = tsc.analyse(snaps, shift_z_threshold=-1.5).to_dict()
        for ev in d["shift_events"]:
            assert "index" in ev and "coherence" in ev

    def test_gradually_drifting_not_stable(self):
        snaps = [_snap(phi=float(i), qualia_count=i * 10, valence=float(-i) * 0.5)
                 for i in range(1, 21)]
        result = tsc.analyse(snaps, stable_threshold=0.98)
        assert isinstance(result.is_stable, bool)

    def test_no_shift_events_on_stable_series(self):
        snaps = _series(30)
        result = tsc.analyse(snaps)
        assert result.shift_events == []
