"""Tests for InteroceptiveSignal.

Pure-math tests cover normalisation, regime classification, allostatic load.
Integration tests use synthetic snapshots (no OS reads needed).
Telemetry tests sample the live host — marked with skip_no_telemetry.
"""
import time

import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.InteroceptiveSignal import (
    InteroceptiveRegime,
    InteroceptiveResult,
    InteroceptiveSnapshot,
    _classify_regime,
    _normalise_snapshots,
    analyse,
    analyse_from_telemetry,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

_TOTAL_RAM = 16 * 1024 ** 3   # 16 GB synthetic total RAM


def _make_snap(cpu: float = 10.0, rss_mb: float = 500.0,
               disk_read: int = 0, disk_write: int = 0,
               net_sent: int = 0, net_recv: int = 0,
               t: float = 0.0) -> InteroceptiveSnapshot:
    return InteroceptiveSnapshot(
        timestamp=t,
        cpu_percent=cpu,
        rss_bytes=int(rss_mb * 1024 ** 2),
        total_ram_bytes=_TOTAL_RAM,
        disk_read_bytes=disk_read,
        disk_write_bytes=disk_write,
        net_sent_bytes=net_sent,
        net_recv_bytes=net_recv,
    )


def _make_series(n: int = 5, cpu: float = 20.0, rss_mb: float = 800.0,
                 interval: float = 1.0) -> list[InteroceptiveSnapshot]:
    return [_make_snap(cpu=cpu, rss_mb=rss_mb, t=i * interval)
            for i in range(n)]


# ── _normalise_snapshots ──────────────────────────────────────────────────────

def test_normalise_arousal_range():
    snaps = _make_series(n=3, cpu=50.0)
    _normalise_snapshots(snaps)
    for s in snaps:
        assert 0.0 <= s.arousal <= 1.0


def test_normalise_arousal_formula():
    snaps = [_make_snap(cpu=75.0)]
    _normalise_snapshots(snaps)
    assert snaps[0].arousal == pytest.approx(0.75)


def test_normalise_fatigue_formula():
    rss_mb = 4 * 1024.0   # 4 GB
    snaps = [_make_snap(rss_mb=rss_mb)]
    _normalise_snapshots(snaps)
    expected = (rss_mb * 1024 ** 2) / _TOTAL_RAM
    assert snaps[0].fatigue == pytest.approx(expected, abs=1e-6)


def test_normalise_stress_first_snap_zero():
    """First snapshot has no predecessor → stress = 0."""
    snaps = _make_series(n=3)
    _normalise_snapshots(snaps)
    assert snaps[0].stress == pytest.approx(0.0)


def test_normalise_stress_high_io():
    """High I/O delta → stress > 0 on subsequent snapshots."""
    snap0 = _make_snap(disk_read=0, disk_write=0, t=0.0)
    snap1 = _make_snap(disk_read=200 * 1024 ** 2, disk_write=0, t=1.0)
    snaps = [snap0, snap1]
    _normalise_snapshots(snaps)
    assert snaps[1].stress > 0.0


def test_normalise_engagement_first_snap_zero():
    snaps = _make_series(n=2)
    _normalise_snapshots(snaps)
    assert snaps[0].engagement == pytest.approx(0.0)


def test_normalise_all_bounded():
    snaps = _make_series(n=5, cpu=80.0, rss_mb=12 * 1024)
    _normalise_snapshots(snaps)
    for s in snaps:
        assert 0.0 <= s.arousal <= 1.0
        assert 0.0 <= s.fatigue <= 1.0
        assert 0.0 <= s.stress <= 1.0
        assert 0.0 <= s.engagement <= 1.0


def test_normalise_empty():
    _normalise_snapshots([])   # should not raise


# ── _classify_regime ──────────────────────────────────────────────────────────

def test_regime_resting():
    r = _classify_regime(arousal=0.1, fatigue=0.3, stress=0.1)
    assert r == InteroceptiveRegime.RESTING


def test_regime_active():
    r = _classify_regime(arousal=0.5, fatigue=0.3, stress=0.1)
    assert r == InteroceptiveRegime.ACTIVE


def test_regime_stressed_io():
    r = _classify_regime(arousal=0.6, fatigue=0.3, stress=0.8)
    assert r == InteroceptiveRegime.STRESSED


def test_regime_stressed_memory():
    r = _classify_regime(arousal=0.5, fatigue=0.9, stress=0.1)
    assert r == InteroceptiveRegime.STRESSED


def test_regime_fatigued():
    r = _classify_regime(arousal=0.1, fatigue=0.9, stress=0.1)
    assert r == InteroceptiveRegime.FATIGUED


def test_regime_fatigued_high_io_low_arousal():
    r = _classify_regime(arousal=0.1, fatigue=0.3, stress=0.7)
    assert r == InteroceptiveRegime.FATIGUED


# ── analyse() ─────────────────────────────────────────────────────────────────

def test_analyse_returns_none_single_snap():
    assert analyse([_make_snap()]) is None


def test_analyse_returns_result():
    r = analyse(_make_series(n=4))
    assert isinstance(r, InteroceptiveResult)


def test_analyse_n_samples():
    snaps = _make_series(n=6)
    r = analyse(snaps)
    assert r.n_samples == 6


def test_analyse_mean_arousal_formula():
    snaps = _make_series(n=4, cpu=40.0)
    r = analyse(snaps)
    assert r.mean_arousal == pytest.approx(0.4)


def test_analyse_mean_fatigue_bounded():
    r = analyse(_make_series(n=4))
    assert 0.0 <= r.mean_fatigue <= 1.0


def test_analyse_state_vector_shape():
    r = analyse(_make_series(n=4))
    assert r.state_vector.shape == (4,)


def test_analyse_state_vector_bounded():
    r = analyse(_make_series(n=4))
    assert np.all(r.state_vector >= 0.0)
    assert np.all(r.state_vector <= 1.0)


def test_analyse_series_length():
    snaps = _make_series(n=6)
    r = analyse(snaps)
    assert len(r.arousal_series) == 6
    assert len(r.fatigue_series) == 6
    assert len(r.stress_series) == 6
    assert len(r.engagement_series) == 6


def test_analyse_allostatic_load_non_negative():
    r = analyse(_make_series(n=4))
    assert r.allostatic_load >= 0.0


def test_analyse_constant_series_low_allostatic():
    """Constant resource usage → allostatic load near zero."""
    snaps = _make_series(n=10, cpu=20.0, rss_mb=500.0)
    r = analyse(snaps)
    assert r.allostatic_load < 0.05


def test_analyse_high_cpu_active_regime():
    snaps = _make_series(n=4, cpu=80.0, rss_mb=500.0)
    r = analyse(snaps)
    assert r.regime == InteroceptiveRegime.ACTIVE


def test_analyse_low_cpu_resting_regime():
    snaps = _make_series(n=4, cpu=5.0, rss_mb=500.0)
    r = analyse(snaps)
    assert r.regime == InteroceptiveRegime.RESTING


def test_analyse_high_ram_stressed_regime():
    snaps = _make_series(n=4, cpu=50.0, rss_mb=12 * 1024)  # ~75% of 16GB
    r = analyse(snaps)
    assert r.regime in (InteroceptiveRegime.STRESSED, InteroceptiveRegime.FATIGUED)


def test_analyse_is_elevated_property():
    r = analyse(_make_series(n=4))
    # is_elevated is defined as allostatic_load > 0.1 — just check bool type
    assert isinstance(r.is_elevated, bool)


def test_analyse_dominant_dimension():
    # Force arousal to be dominant
    snaps = _make_series(n=4, cpu=90.0, rss_mb=100.0)  # high CPU, low RAM
    r = analyse(snaps)
    assert r.dominant_dimension == "arousal"


def test_analyse_baseline_half_window():
    """Baseline computed from first half of samples."""
    # First half: low CPU, second half: high CPU
    snaps_low = _make_series(n=3, cpu=10.0, rss_mb=500.0)
    snaps_high = _make_series(n=3, cpu=80.0, rss_mb=500.0)
    for i, s in enumerate(snaps_low):
        s.timestamp = float(i)
    for i, s in enumerate(snaps_high):
        s.timestamp = float(len(snaps_low) + i)
    snaps = snaps_low + snaps_high
    r = analyse(snaps)
    # baseline_arousal should reflect the first-half low CPU
    assert r.baseline_arousal < 0.5


def test_analyse_regime_enum_value():
    r = analyse(_make_series(n=4))
    assert r.regime in list(InteroceptiveRegime)


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry(n=3, interval_sec=0.1)
    assert r is not None


@skip_no_telemetry
def test_live_state_vector_bounded():
    r = analyse_from_telemetry(n=3, interval_sec=0.1)
    assert np.all(r.state_vector >= 0.0)
    assert np.all(r.state_vector <= 1.0)


@skip_no_telemetry
def test_live_regime_valid():
    r = analyse_from_telemetry(n=3, interval_sec=0.1)
    assert r.regime in list(InteroceptiveRegime)


@skip_no_telemetry
def test_live_dominant_dimension_valid():
    r = analyse_from_telemetry(n=3, interval_sec=0.1)
    assert r.dominant_dimension in ("arousal", "fatigue", "stress", "engagement")
