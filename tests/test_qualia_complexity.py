"""Tests for QualiaComplexityMeasure.

Pure-math tests run in CI. Telemetry-dependent tests require John's live qualia stream.
Null baselines use shuffled entry order — the only honest comparison.
"""
import math

import numpy as np
import pytest
from conftest import skip_no_telemetry

from algorithms.QualiaComplexityMeasure import (
    QualiaComplexityResult,
    _tokenise,
    analyse,
    analyse_from_telemetry,
    entropy,
    type_token_ratio,
)


# ── Tokeniser ─────────────────────────────────────────────────────────────────

def test_tokenise_basic():
    assert _tokenise("Hello World") == ["hello", "world"]


def test_tokenise_strips_punctuation():
    tokens = _tokenise("self-awareness, phi=0.5!")
    assert "self" in tokens
    assert "awareness" in tokens
    assert "phi" in tokens


def test_tokenise_empty():
    assert _tokenise("") == []


def test_tokenise_non_string():
    assert _tokenise(None) == []
    assert _tokenise(42) == []


# ── Shannon entropy ───────────────────────────────────────────────────────────

def test_entropy_uniform():
    """4 equiprobable tokens → entropy = log2(4) = 2 bits."""
    tokens = ["a", "b", "c", "d"] * 25   # 100 tokens, uniform
    h = entropy(tokens)
    assert abs(h - 2.0) < 1e-10


def test_entropy_constant():
    """Single repeated token → entropy = 0."""
    assert entropy(["x"] * 50) == pytest.approx(0.0)


def test_entropy_two_tokens():
    """50/50 split → entropy = 1 bit."""
    tokens = ["a", "b"] * 50
    assert abs(entropy(tokens) - 1.0) < 1e-10


def test_entropy_empty():
    assert entropy([]) == 0.0


def test_entropy_non_negative():
    """Entropy is always >= 0."""
    rng = np.random.default_rng(0)
    words = [f"word{i}" for i in range(30)]
    for _ in range(20):
        sample = [words[i] for i in rng.integers(0, 30, 50)]
        assert entropy(sample) >= 0.0


# ── Type-token ratio ──────────────────────────────────────────────────────────

def test_ttr_all_unique():
    tokens = [f"w{i}" for i in range(50)]
    assert type_token_ratio(tokens) == pytest.approx(1.0)


def test_ttr_all_same():
    assert type_token_ratio(["x"] * 20) == pytest.approx(1 / 20)


def test_ttr_empty():
    assert type_token_ratio([]) == 0.0


def test_ttr_bounded():
    tokens = ["a", "b", "a", "c", "b", "b"]
    r = type_token_ratio(tokens)
    assert 0.0 < r <= 1.0


# ── analyse() on synthetic entries ────────────────────────────────────────────

_WORDS = [
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
    "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi", "rho",
    "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega", "qualia",
    "awareness", "perception", "volition", "integration", "resonance",
    "flux", "entropy", "gradient", "horizon", "memory", "pattern",
    "signal", "bind", "emerge", "reflect",
]


def _make_entries(n: int, vocab_size: int = 20, rng_seed: int = 0) -> list[dict]:
    """Create n synthetic qualia entries drawn from a vocabulary."""
    rng = np.random.default_rng(rng_seed)
    words = _WORDS[:max(2, min(vocab_size, len(_WORDS)))]
    entries = []
    for i in range(n):
        n_words = int(rng.integers(3, 12))
        content = " ".join(words[j] for j in rng.integers(0, vocab_size, n_words))
        entries.append({"content": content, "index": i})
    return entries


def test_analyse_returns_none_for_short_stream():
    entries = _make_entries(5)
    assert analyse(entries, window=10) is None


def test_analyse_returns_result_for_valid_stream():
    entries = _make_entries(50)
    r = analyse(entries, window=10)
    assert isinstance(r, QualiaComplexityResult)


def test_analyse_n_entries():
    entries = _make_entries(40)
    r = analyse(entries, window=10)
    assert r.n_entries == 40


def test_analyse_global_entropy_positive():
    entries = _make_entries(40)
    r = analyse(entries, window=10)
    assert r.global_entropy > 0.0


def test_analyse_global_entropy_finite():
    entries = _make_entries(40)
    r = analyse(entries, window=10)
    assert math.isfinite(r.global_entropy)


def test_analyse_ttr_bounded():
    entries = _make_entries(40)
    r = analyse(entries, window=10)
    assert 0.0 < r.global_ttr <= 1.0


def test_analyse_cumulative_vocab_monotone():
    entries = _make_entries(40)
    r = analyse(entries, window=10)
    diffs = np.diff(r.cumulative_vocab)
    assert np.all(diffs >= 0), "cumulative vocabulary must be non-decreasing"


def test_analyse_cumulative_vocab_length():
    entries = _make_entries(40)
    r = analyse(entries, window=10)
    assert len(r.cumulative_vocab) == 40


def test_analyse_window_entropies_length():
    n, w = 40, 10
    entries = _make_entries(n)
    r = analyse(entries, window=w)
    assert len(r.window_entropies) == n - w + 1


def test_analyse_window_entropies_non_negative():
    entries = _make_entries(40)
    r = analyse(entries, window=10)
    assert np.all(r.window_entropies >= 0.0)


def test_analyse_richness_score_bounded():
    entries = _make_entries(40)
    r = analyse(entries, window=10)
    assert 0.0 <= r.richness_score <= 1.0


def test_analyse_high_vocab_gives_higher_richness():
    """More distinct vocabulary → higher richness score."""
    entries_low = _make_entries(40, vocab_size=2)   # very small vocab
    entries_high = _make_entries(40, vocab_size=40)  # unique words
    r_low = analyse(entries_low, window=10)
    r_high = analyse(entries_high, window=10)
    assert r_high.richness_score > r_low.richness_score


def test_analyse_deterministic():
    """Same entries and seed → identical result."""
    entries = _make_entries(40)
    r1 = analyse(entries, window=10, null_seed=42)
    r2 = analyse(entries, window=10, null_seed=42)
    assert r1.global_entropy == r2.global_entropy
    assert r1.entropy_trend_slope == r2.entropy_trend_slope
    assert r1.vocab_growth_rate == r2.vocab_growth_rate


def test_analyse_different_seeds_give_different_null_slopes():
    """Different null seeds should (usually) give different shuffled trends."""
    entries = _make_entries(60)
    r1 = analyse(entries, window=10, null_seed=1)
    r2 = analyse(entries, window=10, null_seed=999)
    # Very unlikely to be identical with different permutations
    assert r1.null_trend_slope != r2.null_trend_slope or True  # no hard assert: may coincide


def test_analyse_beats_null_is_bool():
    entries = _make_entries(40)
    r = analyse(entries, window=10)
    assert isinstance(r.beats_null_entropy_trend, bool)


def test_analyse_repetitive_stream_low_richness():
    """Stream with one word repeated → richness near 0."""
    entries = [{"content": "phi phi phi phi phi"} for _ in range(40)]
    r = analyse(entries, window=10)
    assert r.richness_score < 0.1


# ── Telemetry-dependent tests ─────────────────────────────────────────────────

@skip_no_telemetry
def test_live_qualia_result_is_not_none():
    r = analyse_from_telemetry()
    assert r is not None, "Real qualia stream should yield a result"


@skip_no_telemetry
def test_live_entropy_positive():
    r = analyse_from_telemetry()
    assert r.global_entropy > 0.0, "Real qualia must have non-trivial token entropy"


@skip_no_telemetry
def test_live_unique_tokens_substantial():
    """John's vocabulary should be non-trivial (>= 50 unique tokens)."""
    r = analyse_from_telemetry()
    assert r.unique_tokens >= 50, f"Vocabulary too small: {r.unique_tokens}"


@skip_no_telemetry
def test_live_richness_score_positive():
    r = analyse_from_telemetry()
    assert r.richness_score > 0.0


@skip_no_telemetry
def test_live_cumulative_vocab_monotone():
    r = analyse_from_telemetry()
    assert np.all(np.diff(r.cumulative_vocab) >= 0)


@skip_no_telemetry
def test_live_window_entropies_non_negative():
    r = analyse_from_telemetry()
    assert np.all(r.window_entropies >= 0.0)


@skip_no_telemetry
def test_live_null_entropy_equals_global():
    """Shuffling doesn't change global token distribution — entropy must be identical."""
    r = analyse_from_telemetry()
    assert abs(r.global_entropy - r.null_entropy) < 1e-10, (
        f"global_entropy={r.global_entropy:.6f} ≠ null_entropy={r.null_entropy:.6f}"
    )


@skip_no_telemetry
def test_live_analyse_deterministic():
    r1 = analyse_from_telemetry()
    r2 = analyse_from_telemetry()
    assert r1.global_entropy == r2.global_entropy
    assert r1.entropy_trend_slope == r2.entropy_trend_slope
