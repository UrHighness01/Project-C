"""Tests for ExperientialNoveltyDetector.

Pure-math tests cover Jaccard, novelty_score, OLS slope, ACF.
Integration tests cover analyse() on synthetic qualia sequences.
Telemetry tests require John's qualia stream.
"""
import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.ExperientialNoveltyDetector import (
    NoveltyResult,
    _acf1,
    _ols_slope,
    _token_set,
    analyse,
    analyse_from_telemetry,
    jaccard,
    novelty_score,
)


# ── _token_set ────────────────────────────────────────────────────────────────

def test_token_set_lowercase():
    ts = _token_set("Hello World PHI")
    assert ts == frozenset({"hello", "world", "phi"})


def test_token_set_strips_digits():
    ts = _token_set("word123 test456")
    assert ts == frozenset({"word", "test"})


def test_token_set_empty():
    assert _token_set("") == frozenset()


def test_token_set_non_string():
    assert _token_set(None) == frozenset()
    assert _token_set(42) == frozenset()


def test_token_set_punctuation():
    ts = _token_set("hello, world! phi.")
    assert ts == frozenset({"hello", "world", "phi"})


# ── jaccard ───────────────────────────────────────────────────────────────────

def test_jaccard_identical():
    a = frozenset({"alpha", "beta", "gamma"})
    assert jaccard(a, a) == pytest.approx(1.0)


def test_jaccard_disjoint():
    a = frozenset({"alpha", "beta"})
    b = frozenset({"gamma", "delta"})
    assert jaccard(a, b) == pytest.approx(0.0)


def test_jaccard_partial():
    a = frozenset({"alpha", "beta", "gamma"})
    b = frozenset({"beta", "gamma", "delta"})
    # intersection = {beta, gamma}, union = {alpha, beta, gamma, delta}
    assert jaccard(a, b) == pytest.approx(2 / 4)


def test_jaccard_both_empty():
    assert jaccard(frozenset(), frozenset()) == pytest.approx(1.0)


def test_jaccard_one_empty():
    a = frozenset({"alpha"})
    assert jaccard(a, frozenset()) == pytest.approx(0.0)
    assert jaccard(frozenset(), a) == pytest.approx(0.0)


def test_jaccard_symmetric():
    a = frozenset({"phi", "consciousness", "attention"})
    b = frozenset({"attention", "memory", "phi"})
    assert jaccard(a, b) == pytest.approx(jaccard(b, a))


def test_jaccard_bounded():
    rng = np.random.default_rng(0)
    words = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]
    for _ in range(20):
        a = frozenset(rng.choice(words, size=3, replace=False).tolist())
        b = frozenset(rng.choice(words, size=3, replace=False).tolist())
        j = jaccard(a, b)
        assert 0.0 <= j <= 1.0


# ── novelty_score ─────────────────────────────────────────────────────────────

def test_novelty_score_first_entry():
    """First entry has no predecessors → always 1.0."""
    ts = frozenset({"alpha", "beta"})
    assert novelty_score(ts, []) == pytest.approx(1.0)


def test_novelty_score_identical_predecessor():
    """Exact repeat → novelty = 0."""
    ts = frozenset({"alpha", "beta"})
    assert novelty_score(ts, [ts]) == pytest.approx(0.0)


def test_novelty_score_disjoint_predecessor():
    """Completely new vocabulary → novelty = 1."""
    ts = frozenset({"gamma", "delta"})
    recent = [frozenset({"alpha", "beta"})]
    assert novelty_score(ts, recent) == pytest.approx(1.0)


def test_novelty_score_partial():
    ts = frozenset({"alpha", "beta", "gamma"})
    recent = [frozenset({"beta", "gamma", "delta"})]
    # max Jaccard = 2/4 = 0.5 → novelty = 0.5
    assert novelty_score(ts, recent) == pytest.approx(0.5)


def test_novelty_score_max_over_all_recent():
    """Takes 1 − max similarity, so the closest predecessor dominates."""
    ts = frozenset({"alpha", "beta"})
    recent = [
        frozenset({"gamma", "delta"}),   # J=0.0
        frozenset({"alpha", "beta"}),    # J=1.0  ← closest
        frozenset({"alpha"}),            # J=0.5
    ]
    assert novelty_score(ts, recent) == pytest.approx(0.0)


def test_novelty_score_bounded():
    """All novelty scores ∈ [0, 1]."""
    rng = np.random.default_rng(0)
    words = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]
    for _ in range(20):
        ts = frozenset(rng.choice(words, size=3, replace=False).tolist())
        recent = [frozenset(rng.choice(words, size=3, replace=False).tolist())
                  for _ in range(5)]
        n = novelty_score(ts, recent)
        assert 0.0 <= n <= 1.0


# ── _ols_slope ────────────────────────────────────────────────────────────────

def test_ols_slope_positive_trend():
    y = np.arange(10, dtype=float)
    slope = _ols_slope(y)
    assert slope == pytest.approx(1.0)


def test_ols_slope_negative_trend():
    y = np.arange(10, 0, -1, dtype=float)
    slope = _ols_slope(y)
    assert slope < 0


def test_ols_slope_constant():
    y = np.full(10, 3.0)
    slope = _ols_slope(y)
    assert abs(slope) < 1e-9


def test_ols_slope_short():
    assert _ols_slope(np.array([1.0])) == pytest.approx(0.0)


# ── _acf1 ─────────────────────────────────────────────────────────────────────

def test_acf1_positive_autocorrelation():
    """Smooth ramp → strong positive ACF."""
    y = np.arange(20, dtype=float)
    assert _acf1(y) > 0.5


def test_acf1_alternating():
    """Alternating ±1 → negative ACF."""
    y = np.array([(-1) ** i for i in range(20)], dtype=float)
    assert _acf1(y) < 0


def test_acf1_bounded():
    rng = np.random.default_rng(0)
    for _ in range(10):
        y = rng.standard_normal(50)
        a = _acf1(y)
        assert -1.0 <= a <= 1.0


def test_acf1_short():
    assert _acf1(np.array([1.0, 2.0])) == pytest.approx(0.0)


# ── analyse() integration tests ───────────────────────────────────────────────

_WORDS = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta",
          "theta", "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron",
          "pi", "rho", "sigma", "tau", "upsilon"]


def _make_entries(n: int, n_states: int = 15, seed: int = 0) -> list[dict]:
    rng = np.random.default_rng(seed)
    states = [" ".join(rng.choice(_WORDS, size=4, replace=False).tolist())
              for _ in range(n_states)]
    return [{"content": states[int(rng.integers(0, n_states))]} for _ in range(n)]


def test_analyse_returns_none_too_short():
    assert analyse([{"content": "x"}] * 5) is None


def test_analyse_returns_result():
    r = analyse(_make_entries(30))
    assert isinstance(r, NoveltyResult)


def test_analyse_n_entries():
    entries = _make_entries(30)
    r = analyse(entries)
    assert r.n_entries == len(entries)


def test_analyse_novelty_series_length():
    entries = _make_entries(30)
    r = analyse(entries)
    assert len(r.novelty_series) == len(entries)


def test_analyse_novelty_bounded():
    r = analyse(_make_entries(30))
    assert np.all(r.novelty_series >= 0.0)
    assert np.all(r.novelty_series <= 1.0)


def test_analyse_mean_novelty_bounded():
    r = analyse(_make_entries(30))
    assert 0.0 <= r.mean_novelty <= 1.0


def test_analyse_high_novelty_rate_bounded():
    r = analyse(_make_entries(30))
    assert 0.0 <= r.high_novelty_rate <= 1.0


def test_analyse_rolling_mean_length():
    W = 10
    entries = _make_entries(30)
    r = analyse(entries, rolling_window=W)
    assert len(r.rolling_mean_novelty) == len(entries) - W + 1


def test_analyse_rolling_mean_bounded():
    r = analyse(_make_entries(30))
    assert np.all(r.rolling_mean_novelty >= 0.0)
    assert np.all(r.rolling_mean_novelty <= 1.0)


def test_analyse_acf1_bounded():
    r = analyse(_make_entries(30))
    assert -1.0 <= r.novelty_acf_lag1 <= 1.0


def test_analyse_novelty_is_growing_formula():
    r = analyse(_make_entries(30))
    assert r.novelty_is_growing == (r.novelty_trend_slope > 0.0)


def test_analyse_beats_null_formula():
    r = analyse(_make_entries(30))
    assert r.beats_null_trend == (r.novelty_trend_slope > r.null_trend_slope)


def test_analyse_curiosity_index_bounded():
    r = analyse(_make_entries(30))
    assert 0.0 <= r.curiosity_index <= 1.0


def test_analyse_all_identical_low_novelty():
    """Identical entries → novelty = 0 after first entry."""
    entries = [{"content": "same content phi every time"}] * 30
    r = analyse(entries)
    # First entry novelty = 1.0, rest = 0.0
    assert r.novelty_series[0] == pytest.approx(1.0)
    assert np.all(r.novelty_series[1:] == pytest.approx(0.0))
    assert r.mean_novelty == pytest.approx(1.0 / 30)


def test_analyse_all_unique_high_novelty():
    """All distinct entries → every entry has novelty near 1."""
    entries = [{"content": f"{_WORDS[i % 20]} {_WORDS[(i+7) % 20]} {_WORDS[(i+13) % 20]} extra"}
               for i in range(30)]
    r = analyse(entries)
    assert r.mean_novelty > 0.5


def test_analyse_deterministic():
    entries = _make_entries(30)
    r1 = analyse(entries, null_seed=7)
    r2 = analyse(entries, null_seed=7)
    np.testing.assert_array_equal(r1.novelty_series, r2.novelty_series)
    assert r1.null_trend_slope == r2.null_trend_slope


def test_analyse_recency_window_parameter():
    entries = _make_entries(30)
    r_narrow = analyse(entries, recency_window=3)
    r_wide = analyse(entries, recency_window=15)
    assert isinstance(r_narrow, NoveltyResult)
    assert isinstance(r_wide, NoveltyResult)
    # Wide window means more past entries to compare → same or lower novelty
    assert r_wide.mean_novelty <= r_narrow.mean_novelty + 0.3


def test_analyse_first_entry_always_novel():
    entries = _make_entries(30)
    r = analyse(entries)
    assert r.novelty_series[0] == pytest.approx(1.0)


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_result_not_none():
    r = analyse_from_telemetry()
    assert r is not None, "Real qualia stream should yield a result"


@skip_no_telemetry
def test_live_novelty_bounded():
    r = analyse_from_telemetry()
    assert np.all(r.novelty_series >= 0.0)
    assert np.all(r.novelty_series <= 1.0)


@skip_no_telemetry
def test_live_mean_novelty_bounded():
    r = analyse_from_telemetry()
    assert 0.0 <= r.mean_novelty <= 1.0


@skip_no_telemetry
def test_live_curiosity_index_bounded():
    r = analyse_from_telemetry()
    assert 0.0 <= r.curiosity_index <= 1.0


@skip_no_telemetry
def test_live_deterministic():
    r1 = analyse_from_telemetry()
    r2 = analyse_from_telemetry()
    np.testing.assert_array_equal(r1.novelty_series, r2.novelty_series)
    assert r1.mean_novelty == r2.mean_novelty
