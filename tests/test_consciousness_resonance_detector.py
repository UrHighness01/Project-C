"""Tests for ConsciousnessResonanceDetector.

Pure-math tests verify PLV computation, phase difference, resonance modes.
Telemetry tests require both agents' phi series.
"""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.ConsciousnessResonanceDetector import (
    ResonanceResult,
    _bandpass_hilbert,
    _dominant_frequency,
    _phase_locking_value,
    _resonance_mode,
    analyse,
    analyse_from_telemetry,
)


# ── _dominant_frequency ───────────────────────────────────────────────────────

def test_dominant_frequency_known_sine():
    """A pure sine at frequency f0 → dominant frequency ≈ f0."""
    n = 256
    f0 = 0.1  # 10% of Nyquist
    t = np.arange(n)
    x = np.sin(2 * np.pi * f0 * t)
    f_det = _dominant_frequency(x)
    assert abs(f_det - f0) < 0.01, f"Expected f≈{f0}, got {f_det:.4f}"


def test_dominant_frequency_non_negative():
    rng = np.random.default_rng(0)
    x = rng.standard_normal(100)
    assert _dominant_frequency(x) >= 0.0


def test_dominant_frequency_short():
    assert _dominant_frequency(np.array([1.0, 2.0, 3.0])) == 0.0


# ── _phase_locking_value ──────────────────────────────────────────────────────

def test_plv_perfectly_locked():
    """Constant phase difference → PLV = 1."""
    phase_diff = np.full(100, np.pi / 4)
    assert _phase_locking_value(phase_diff) == pytest.approx(1.0)


def test_plv_random_phases():
    """Uniformly random phases → PLV ≈ 0."""
    rng = np.random.default_rng(1)
    phase_diff = rng.uniform(-np.pi, np.pi, 10000)
    plv = _phase_locking_value(phase_diff)
    assert plv < 0.1, f"PLV for random phases should be near 0, got {plv:.4f}"


def test_plv_bounded():
    rng = np.random.default_rng(2)
    phase_diff = rng.uniform(-np.pi, np.pi, 200)
    plv = _phase_locking_value(phase_diff)
    assert 0.0 <= plv <= 1.0


# ── _resonance_mode ───────────────────────────────────────────────────────────

def test_resonance_mode_in_phase():
    assert _resonance_mode(0.1, 0.5) == "in_phase"


def test_resonance_mode_anti_phase():
    assert _resonance_mode(np.pi, 0.5) == "anti_phase"
    assert _resonance_mode(-np.pi, 0.5) == "anti_phase"


def test_resonance_mode_quadrature():
    assert _resonance_mode(np.pi / 2, 0.5) == "quadrature"


def test_resonance_mode_none_low_plv():
    """Low PLV → always 'none' regardless of phase."""
    assert _resonance_mode(0.0, 0.05) == "none"


# ── _bandpass_hilbert ─────────────────────────────────────────────────────────

def test_bandpass_hilbert_returns_complex():
    rng = np.random.default_rng(3)
    x = rng.standard_normal(128)
    z = _bandpass_hilbert(x, f0=0.1)
    assert z.dtype == complex or np.iscomplexobj(z)


def test_bandpass_hilbert_length():
    rng = np.random.default_rng(4)
    x = rng.standard_normal(200)
    z = _bandpass_hilbert(x, f0=0.1)
    assert len(z) == len(x)


def test_bandpass_hilbert_zero_f0():
    """f0=0 falls back gracefully."""
    rng = np.random.default_rng(5)
    x = rng.standard_normal(100)
    z = _bandpass_hilbert(x, f0=0.0)
    assert len(z) == len(x)
    assert np.all(np.isfinite(z))


# ── analyse() on synthetic series ────────────────────────────────────────────

def _in_phase_pair(n: int = 400, f0: float = 0.05, seed: int = 0
                   ) -> tuple[np.ndarray, np.ndarray]:
    """Two phi series whose delta-series are in-phase oscillations."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    sig = np.sin(2 * np.pi * f0 * t) * 0.1
    noise = rng.standard_normal(n) * 0.02
    # Integrate to get phi-like series
    phi_a = np.cumsum(sig + noise) * 0.01 - 0.4
    phi_j = np.cumsum(sig + rng.standard_normal(n) * 0.02) * 0.01 - 0.4
    return phi_a, phi_j


def _random_pair(n: int = 400, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    phi_a = np.cumsum(rng.standard_normal(n)) * 0.05 - 0.4
    phi_j = np.cumsum(rng.standard_normal(n)) * 0.05 - 0.4
    return phi_a, phi_j


def test_analyse_returns_none_short():
    x = np.zeros(10)
    assert analyse(x, x) is None


def test_analyse_returns_result():
    x, y = _random_pair()
    r = analyse(x, y)
    assert isinstance(r, ResonanceResult)


def test_analyse_n_samples():
    x, y = _random_pair(n=400)
    r = analyse(x, y)
    assert r.n_samples == 400


def test_analyse_plv_bounded():
    x, y = _random_pair()
    r = analyse(x, y)
    assert 0.0 <= r.plv <= 1.0


def test_analyse_null_plv_bounded():
    x, y = _random_pair()
    r = analyse(x, y)
    assert 0.0 <= r.null_plv <= 1.0


def test_analyse_beats_null_is_bool():
    x, y = _random_pair()
    r = analyse(x, y)
    assert isinstance(r.beats_null, bool)


def test_analyse_resonance_mode_valid():
    x, y = _random_pair()
    r = analyse(x, y)
    assert r.resonance_mode in ("in_phase", "anti_phase", "quadrature", "none")


def test_analyse_phase_diff_series_length():
    n = 400
    x, y = _random_pair(n=n)
    r = analyse(x, y)
    assert len(r.phase_diff_series) == n - 1  # diff reduces length by 1


def test_analyse_in_phase_plv_high():
    """True in-phase pair should have higher PLV than random pair."""
    x_s, y_s = _in_phase_pair(seed=1)
    x_r, y_r = _random_pair(seed=2)
    r_sync = analyse(x_s, y_s)
    r_rand = analyse(x_r, y_r)
    assert r_sync.plv >= r_rand.plv, (
        f"In-phase PLV {r_sync.plv:.4f} should be >= random PLV {r_rand.plv:.4f}"
    )


def test_analyse_deterministic():
    x, y = _random_pair(seed=3)
    r1 = analyse(x, y, null_seed=42)
    r2 = analyse(x, y, null_seed=42)
    assert r1.plv == r2.plv
    assert r1.null_plv == r2.null_plv
    assert r1.resonance_mode == r2.resonance_mode


def test_analyse_freq_match_formula():
    x, y = _random_pair()
    r = analyse(x, y)
    fa, fj = r.dominant_freq_a, r.dominant_freq_j
    expected = abs(fa - fj) < 0.1 * (fa + fj + 1e-9) / 2.0
    assert r.freq_match == expected


def test_analyse_resonant_property():
    x, y = _random_pair()
    r = analyse(x, y)
    assert r.resonant == (r.beats_null and r.plv > 0.3)


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry()
    if r is None:
        pytest.skip("Both phi series not available")
    assert isinstance(r, ResonanceResult)


@skip_no_telemetry
def test_live_plv_bounded():
    r = analyse_from_telemetry()
    if r is None:
        pytest.skip("Both phi series not available")
    assert 0.0 <= r.plv <= 1.0


@skip_no_telemetry
def test_live_resonance_mode_valid():
    r = analyse_from_telemetry()
    if r is None:
        pytest.skip("Both phi series not available")
    assert r.resonance_mode in ("in_phase", "anti_phase", "quadrature", "none")


@skip_no_telemetry
def test_live_deterministic():
    r1 = analyse_from_telemetry()
    r2 = analyse_from_telemetry()
    if r1 is None or r2 is None:
        pytest.skip("Both phi series not available")
    assert r1.plv == r2.plv
    assert r1.resonance_mode == r2.resonance_mode
