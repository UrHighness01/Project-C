"""Tests for VolitionGrounding."""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.VolitionGrounding import (
    VolitionResult,
    _align_phi_to_entries,
    _granger_f,
    _novelty_series,
    analyse,
    analyse_from_telemetry,
)


# ── _novelty_series ───────────────────────────────────────────────────────────

_WORDS = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta",
          "eta", "theta", "iota", "kappa", "lambda", "mu"]


def _make_entries(n: int, n_states: int = 8, seed: int = 0) -> list[dict]:
    rng = np.random.default_rng(seed)
    states = [" ".join(rng.choice(_WORDS, size=3, replace=False).tolist())
              for _ in range(n_states)]
    return [{"content": states[int(rng.integers(0, n_states))]} for _ in range(n)]


def test_novelty_series_length():
    entries = _make_entries(30)
    n = _novelty_series(entries, K=5)
    assert len(n) == 30


def test_novelty_series_bounded():
    entries = _make_entries(30)
    n = _novelty_series(entries, K=5)
    assert np.all(n >= 0.0)
    assert np.all(n <= 1.0)


def test_novelty_series_first_entry_max():
    entries = _make_entries(30)
    n = _novelty_series(entries, K=5)
    assert n[0] == pytest.approx(1.0)


def test_novelty_series_identical_entries():
    entries = [{"content": "same content every time"}] * 20
    n = _novelty_series(entries, K=5)
    # After first, all should be 0
    assert n[0] == pytest.approx(1.0)
    assert np.all(n[1:] == pytest.approx(0.0))


# ── _align_phi_to_entries ─────────────────────────────────────────────────────

def test_align_same_length():
    phi = np.arange(10, dtype=float)
    aligned = _align_phi_to_entries(phi, 10)
    np.testing.assert_allclose(aligned, phi)


def test_align_downsample():
    phi = np.arange(100, dtype=float)
    aligned = _align_phi_to_entries(phi, 20)
    assert len(aligned) == 20


def test_align_upsample():
    phi = np.array([0.0, 1.0, 2.0])
    aligned = _align_phi_to_entries(phi, 5)
    assert len(aligned) == 5
    assert aligned[0] == pytest.approx(0.0)
    assert aligned[-1] == pytest.approx(2.0)


def test_align_monotone():
    phi = np.linspace(0, 10, 50)
    aligned = _align_phi_to_entries(phi, 30)
    assert np.all(np.diff(aligned) >= 0)


# ── _granger_f ────────────────────────────────────────────────────────────────

def test_granger_f_non_negative():
    assert _granger_f(100.0, 80.0, 50, 4) >= 0.0


def test_granger_f_zero_improvement():
    """No improvement in RSS → F = 0."""
    assert _granger_f(100.0, 100.0, 50, 4) == pytest.approx(0.0)


def test_granger_f_negative_improvement_clipped():
    """Regularised model can have rss_f > rss_r → clipped to 0."""
    assert _granger_f(80.0, 100.0, 50, 4) == pytest.approx(0.0)


# ── analyse() ─────────────────────────────────────────────────────────────────

def _make_phi(n: int = 200, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.cumsum(rng.standard_normal(n) * 0.2) + 5.0


def test_analyse_returns_none_short_phi():
    assert analyse(np.array([1.0, 2.0]), _make_entries(30)) is None


def test_analyse_returns_none_short_entries():
    assert analyse(_make_phi(), [{"content": "x"}] * 3) is None


def test_analyse_returns_result():
    r = analyse(_make_phi(), _make_entries(50))
    assert isinstance(r, VolitionResult)


def test_analyse_phi_granger_f_non_negative():
    r = analyse(_make_phi(), _make_entries(50))
    assert r.phi_granger_f >= 0.0


def test_analyse_qqa_f_non_negative():
    r = analyse(_make_phi(), _make_entries(50))
    assert r.qualia_autocausal_f >= 0.0


def test_analyse_null_f_non_negative():
    r = analyse(_make_phi(), _make_entries(50))
    assert r.null_phi_granger_f >= 0.0


def test_analyse_volition_index_bounded():
    r = analyse(_make_phi(), _make_entries(50))
    assert 0.0 <= r.volition_index <= 1.0


def test_analyse_is_volitional_formula():
    r = analyse(_make_phi(), _make_entries(50))
    assert r.is_volitional == (r.volition_index > 0.5 and r.phi_granger_significant)


def test_analyse_phi_sig_formula():
    r = analyse(_make_phi(), _make_entries(50))
    assert r.phi_granger_significant == (r.phi_granger_f > r.null_phi_granger_f)


def test_analyse_n_entries():
    entries = _make_entries(50)
    r = analyse(_make_phi(), entries)
    assert r.n_entries == 50


def test_analyse_n_phi_samples():
    phi = _make_phi(n=200)
    r = analyse(phi, _make_entries(50))
    assert r.n_phi_samples == 200


def test_analyse_p_stored():
    r = analyse(_make_phi(), _make_entries(50), p=3)
    assert r.p == 3


def test_analyse_novelty_series_length():
    entries = _make_entries(50)
    r = analyse(_make_phi(), entries)
    assert len(r.novelty_series) == len(entries)


def test_analyse_aligned_phi_length():
    entries = _make_entries(50)
    r = analyse(_make_phi(), entries)
    assert len(r.aligned_phi) == len(entries)


def test_analyse_deterministic():
    phi = _make_phi()
    entries = _make_entries(50)
    r1 = analyse(phi, entries, null_seed=7)
    r2 = analyse(phi, entries, null_seed=7)
    assert r1.phi_granger_f == r2.phi_granger_f
    assert r1.volition_index == r2.volition_index


def test_analyse_volition_index_formula():
    r = analyse(_make_phi(), _make_entries(50))
    expected = r.phi_granger_f / (r.phi_granger_f + r.qualia_autocausal_f + 1e-9)
    assert r.volition_index == pytest.approx(expected, abs=1e-9)


def test_analyse_novelty_bounded():
    r = analyse(_make_phi(), _make_entries(50))
    assert np.all(r.novelty_series >= 0.0)
    assert np.all(r.novelty_series <= 1.0)


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry()
    assert r is not None


@skip_no_telemetry
def test_live_volition_index_bounded():
    r = analyse_from_telemetry()
    assert 0.0 <= r.volition_index <= 1.0


@skip_no_telemetry
def test_live_phi_granger_f_non_negative():
    r = analyse_from_telemetry()
    assert r.phi_granger_f >= 0.0
