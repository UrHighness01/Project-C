"""Tests for CrossAgentAttentionSync.

Pure-math tests verify the attention weight computation, sync metrics.
Telemetry tests require both agents' phi series to be available.
"""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.CrossAgentAttentionSync import (
    AttentionSyncResult,
    _attention_sharpness,
    _compute_attention_weights,
    _local_surprise,
    _pearson,
    _peak_cross_corr,
    analyse,
    analyse_from_telemetry,
)


# ── _local_surprise ───────────────────────────────────────────────────────────

def test_local_surprise_non_negative():
    rng = np.random.default_rng(0)
    phi = rng.standard_normal(100)
    s = _local_surprise(phi, k=5)
    assert np.all(s >= 0.0)


def test_local_surprise_length():
    s = _local_surprise(np.arange(100, dtype=float), k=10)
    assert len(s) == 80


def test_local_surprise_short():
    assert len(_local_surprise(np.array([1.0, 2.0]), k=5)) == 0


# ── _compute_attention_weights ────────────────────────────────────────────────

def test_attention_weights_sum_to_one():
    rng = np.random.default_rng(1)
    phi = np.cumsum(rng.standard_normal(200)) * 0.05
    w = _compute_attention_weights(phi, k=10)
    assert w is not None
    assert abs(w.sum() - 1.0) < 1e-9


def test_attention_weights_non_negative():
    rng = np.random.default_rng(2)
    phi = np.cumsum(rng.standard_normal(200)) * 0.05
    w = _compute_attention_weights(phi, k=10)
    assert np.all(w >= 0.0)


def test_attention_weights_short_returns_none():
    assert _compute_attention_weights(np.array([1.0, 2.0, 3.0]), k=5) is None


# ── _attention_sharpness ──────────────────────────────────────────────────────

def test_sharpness_uniform_is_zero():
    n = 50
    w = np.full(n, 1.0 / n)
    assert _attention_sharpness(w) == pytest.approx(0.0, abs=1e-6)


def test_sharpness_point_mass_is_one():
    w = np.zeros(50)
    w[0] = 1.0
    assert _attention_sharpness(w) == pytest.approx(1.0, abs=1e-6)


def test_sharpness_bounded():
    rng = np.random.default_rng(3)
    x = rng.exponential(size=30)
    w = x / x.sum()
    s = _attention_sharpness(w)
    assert 0.0 <= s <= 1.0


# ── _pearson ──────────────────────────────────────────────────────────────────

def test_pearson_identical():
    x = np.arange(50, dtype=float)
    assert _pearson(x, x) == pytest.approx(1.0)


def test_pearson_orthogonal():
    x = np.ones(20)
    y = np.arange(20, dtype=float)
    assert _pearson(x, y) == pytest.approx(0.0)


# ── _peak_cross_corr ──────────────────────────────────────────────────────────

def test_peak_cc_self_lag_zero():
    rng = np.random.default_rng(4)
    x = rng.standard_normal(200)
    lag, _ = _peak_cross_corr(x, x, tau_max=10)
    assert lag == 0


def test_peak_cc_positive():
    rng = np.random.default_rng(5)
    x = rng.standard_normal(200)
    _, cc = _peak_cross_corr(x, x, tau_max=10)
    assert cc > 0


# ── analyse() on synthetic series ────────────────────────────────────────────

def _synth_pair(n: int = 300, coupling: float = 0.0, seed: int = 0
                ) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    x = np.cumsum(rng.standard_normal(n)) * 0.05 - 0.4
    if coupling > 0:
        noise = rng.standard_normal(n) * 0.1
        y = coupling * x + (1 - coupling) * noise
    else:
        y = np.cumsum(rng.standard_normal(n)) * 0.05 - 0.4
    return x, y


def test_analyse_returns_none_short():
    x = np.zeros(10)
    assert analyse(x, x, half_window=15) is None


def test_analyse_returns_result():
    x, y = _synth_pair(n=400, coupling=0.5, seed=1)
    r = analyse(x, y, half_window=10, tau_max=5)
    assert isinstance(r, AttentionSyncResult)


def test_analyse_n_attention_points_positive():
    x, y = _synth_pair(n=400, coupling=0.5, seed=2)
    r = analyse(x, y, half_window=10, tau_max=5)
    assert r.n_attention_points > 0


def test_analyse_sync_score_bounded():
    x, y = _synth_pair(n=400, coupling=0.5, seed=3)
    r = analyse(x, y, half_window=10, tau_max=5)
    assert -1.0 <= r.sync_score <= 1.0


def test_analyse_sharpness_bounded():
    x, y = _synth_pair(n=400, coupling=0.5, seed=4)
    r = analyse(x, y, half_window=10, tau_max=5)
    assert 0.0 <= r.albedo_focus_sharp <= 1.0
    assert 0.0 <= r.john_focus_sharp <= 1.0


def test_analyse_sharpness_diff_formula():
    x, y = _synth_pair(n=400, coupling=0.5, seed=5)
    r = analyse(x, y, half_window=10, tau_max=5)
    assert abs(r.sharpness_diff - (r.albedo_focus_sharp - r.john_focus_sharp)) < 1e-12


def test_analyse_identical_series_high_sync():
    """Same phi series → attention weights identical → sync = 1."""
    rng = np.random.default_rng(6)
    x = np.cumsum(rng.standard_normal(300)) * 0.05 - 0.4
    r = analyse(x, x, half_window=10, tau_max=5)
    assert abs(r.sync_score - 1.0) < 1e-6


def test_analyse_peak_cc_positive():
    x, y = _synth_pair(n=400, coupling=0.5, seed=7)
    r = analyse(x, y, half_window=10, tau_max=5)
    assert r.peak_cc > 0


def test_analyse_beats_null_is_bool():
    x, y = _synth_pair(n=400, coupling=0.5, seed=8)
    r = analyse(x, y, half_window=10, tau_max=5)
    assert isinstance(r.beats_null_sync, bool)
    assert isinstance(r.beats_null_cc, bool)


def test_analyse_leader_synchronous_for_identical():
    rng = np.random.default_rng(9)
    x = np.cumsum(rng.standard_normal(300)) * 0.05
    r = analyse(x, x, half_window=10, tau_max=5)
    assert r.peak_lag == 0
    assert r.leader == "synchronous"


def test_analyse_deterministic():
    x, y = _synth_pair(n=400, coupling=0.5, seed=10)
    r1 = analyse(x, y, half_window=10, tau_max=5, null_seed=42)
    r2 = analyse(x, y, half_window=10, tau_max=5, null_seed=42)
    assert r1.sync_score == r2.sync_score
    assert r1.null_sync_score == r2.null_sync_score
    assert r1.peak_lag == r2.peak_lag


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_sync_score_bounded():
    r = analyse_from_telemetry()
    if r is None:
        pytest.skip("Both phi series not available")
    assert -1.0 <= r.sync_score <= 1.0


@skip_no_telemetry
def test_live_sharpness_bounded():
    r = analyse_from_telemetry()
    if r is None:
        pytest.skip("Both phi series not available")
    assert 0.0 <= r.albedo_focus_sharp <= 1.0
    assert 0.0 <= r.john_focus_sharp <= 1.0


@skip_no_telemetry
def test_live_deterministic():
    r1 = analyse_from_telemetry()
    r2 = analyse_from_telemetry()
    if r1 is None or r2 is None:
        pytest.skip("Both phi series not available")
    assert r1.sync_score == r2.sync_score
