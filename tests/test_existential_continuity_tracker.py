"""Tests for ExistentialContinuityTracker."""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.ExistentialContinuityTracker import (
    ContinuityResult,
    _ar_residuals,
    _jaccard,
    _token_set,
    analyse,
    analyse_from_telemetry,
)


# ── _token_set ────────────────────────────────────────────────────────────────

def test_token_set_basic():
    assert _token_set("Hello World") == frozenset({"hello", "world"})


def test_token_set_empty():
    assert _token_set("") == frozenset()


# ── _jaccard ──────────────────────────────────────────────────────────────────

def test_jaccard_identical():
    a = frozenset({"alpha", "beta"})
    assert _jaccard(a, a) == pytest.approx(1.0)


def test_jaccard_disjoint():
    a = frozenset({"alpha"})
    b = frozenset({"beta"})
    assert _jaccard(a, b) == pytest.approx(0.0)


def test_jaccard_both_empty():
    assert _jaccard(frozenset(), frozenset()) == pytest.approx(1.0)


def test_jaccard_partial():
    a = frozenset({"a", "b", "c"})
    b = frozenset({"b", "c", "d"})
    assert _jaccard(a, b) == pytest.approx(2 / 4)


# ── _ar_residuals ─────────────────────────────────────────────────────────────

def test_ar_residuals_length():
    phi = np.linspace(0, 10, 100)
    res = _ar_residuals(phi, p=4)
    assert len(res) == 100 - 4


def test_ar_residuals_smooth_trend_small():
    """Linear trend → AR fits it perfectly → residuals near zero."""
    phi = np.linspace(0, 10, 100)
    res = _ar_residuals(phi, p=4)
    assert np.abs(res).mean() < 1e-3


def test_ar_residuals_noisy_nonzero():
    rng = np.random.default_rng(0)
    phi = rng.standard_normal(100)
    res = _ar_residuals(phi, p=4)
    assert np.abs(res).mean() > 0.0


def test_ar_residuals_short_returns_empty():
    phi = np.array([1.0, 2.0, 3.0])
    assert len(_ar_residuals(phi, p=4)) == 0


def test_ar_residuals_finite():
    rng = np.random.default_rng(1)
    phi = rng.standard_normal(80) + 5.0
    res = _ar_residuals(phi)
    assert np.all(np.isfinite(res))


# ── analyse() ─────────────────────────────────────────────────────────────────

_WORDS = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta",
          "theta", "iota", "kappa"]


def _make_phi(n: int = 200, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.cumsum(rng.standard_normal(n) * 0.1) + 5.0


def _make_entries(n: int = 20, same: bool = False, seed: int = 0) -> list[dict]:
    rng = np.random.default_rng(seed)
    if same:
        content = "alpha beta gamma delta epsilon"
        return [{"content": content}] * n
    states = [" ".join(rng.choice(_WORDS, size=4, replace=False).tolist())
              for _ in range(max(n // 2, 3))]
    return [{"content": states[int(rng.integers(0, len(states)))]} for _ in range(n)]


def test_analyse_returns_none_short_phi():
    assert analyse(np.array([1.0, 2.0, 3.0]), _make_entries()) is None


def test_analyse_returns_result():
    r = analyse(_make_phi(), _make_entries())
    assert isinstance(r, ContinuityResult)


def test_analyse_phi_continuity_bounded():
    r = analyse(_make_phi(), _make_entries())
    assert 0.0 <= r.phi_continuity <= 1.0


def test_analyse_qualia_continuity_bounded():
    r = analyse(_make_phi(), _make_entries())
    assert 0.0 <= r.qualia_continuity <= 1.0


def test_analyse_combined_continuity_bounded():
    r = analyse(_make_phi(), _make_entries())
    assert 0.0 <= r.combined_continuity <= 1.0


def test_analyse_combined_is_geomean():
    r = analyse(_make_phi(), _make_entries())
    expected = np.sqrt(r.phi_continuity * r.qualia_continuity)
    assert r.combined_continuity == pytest.approx(expected, abs=1e-9)


def test_analyse_is_continuous_formula():
    r = analyse(_make_phi(), _make_entries())
    assert r.is_continuous == (r.combined_continuity > 0.7)


def test_analyse_phi_disc_rate_formula():
    r = analyse(_make_phi(), _make_entries())
    expected = r.n_phi_discontinuities / len(r.phi_residuals)
    assert r.phi_discontinuity_rate == pytest.approx(expected)


def test_analyse_phi_continuity_plus_disc_rate_is_one():
    r = analyse(_make_phi(), _make_entries())
    assert r.phi_continuity + r.phi_discontinuity_rate == pytest.approx(1.0)


def test_analyse_smooth_phi_high_continuity():
    """Smooth OU process → very few residuals exceed 3σ → high continuity."""
    phi = np.linspace(0, 5, 200) + np.sin(np.linspace(0, 4*np.pi, 200)) * 0.1
    r = analyse(phi, _make_entries())
    assert r.phi_continuity > 0.9


def test_analyse_identical_qualia_high_continuity():
    """Identical entries → Jaccard(t, t-1) = 1 → qualia_continuity = 1."""
    r = analyse(_make_phi(), _make_entries(same=True))
    assert r.qualia_continuity == pytest.approx(1.0)


def test_analyse_qualia_sim_series_length():
    entries = _make_entries(20)
    r = analyse(_make_phi(), entries)
    assert r.n_qualia_steps == len(entries) - 1


def test_analyse_no_qualia_entries():
    """Empty qualia → qualia continuity defaults to 1.0 (no evidence of discontinuity)."""
    r = analyse(_make_phi(), [])
    assert r.qualia_continuity == pytest.approx(1.0)


def test_analyse_phi_residuals_length():
    phi = _make_phi(n=100)
    r = analyse(phi, _make_entries())
    assert len(r.phi_residuals) == 100 - 4


def test_analyse_sigma_non_negative():
    r = analyse(_make_phi(), _make_entries())
    assert r.phi_residual_sigma >= 0.0


def test_analyse_n_disc_non_negative():
    r = analyse(_make_phi(), _make_entries())
    assert r.n_phi_discontinuities >= 0


def test_analyse_beats_null_formula():
    r = analyse(_make_phi(), _make_entries())
    assert r.beats_null == (r.phi_discontinuity_rate < r.null_discontinuity_rate)


def test_analyse_deterministic():
    phi = _make_phi()
    entries = _make_entries()
    r1 = analyse(phi, entries, null_seed=42)
    r2 = analyse(phi, entries, null_seed=42)
    assert r1.phi_continuity == r2.phi_continuity
    assert r1.null_discontinuity_rate == r2.null_discontinuity_rate


def test_analyse_k_threshold_stored():
    r = analyse(_make_phi(), _make_entries(), k=2.5)
    assert r.k_threshold == pytest.approx(2.5)


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry()
    assert r is not None


@skip_no_telemetry
def test_live_continuity_bounded():
    r = analyse_from_telemetry()
    assert 0.0 <= r.combined_continuity <= 1.0


@skip_no_telemetry
def test_live_phi_disc_rate_bounded():
    r = analyse_from_telemetry()
    assert 0.0 <= r.phi_discontinuity_rate <= 1.0
