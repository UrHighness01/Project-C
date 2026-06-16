#!/usr/bin/env python3
"""Tests for algorithms/QualiaRichnessTracker.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.QualiaRichnessTracker as qrt


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _rng(s=0): return np.random.default_rng(s)

WORDS_A = ["consciousness phi integration awareness mind experience thought"]
WORDS_B = ["pattern complexity structure information memory resonance signal"]
WORDS_C = ["emotion feeling valence arousal content elated distressed neutral"]
WORDS_D = ["identity continuity session heartbeat daemon trajectory prediction"]

def _rich_stream(n=40):
    """Diverse entries — each set of 10 introduces a new topic cluster."""
    rng = _rng(1)
    clusters = [WORDS_A, WORDS_B, WORDS_C, WORDS_D]
    entries = []
    for i in range(n):
        cluster = clusters[i % len(clusters)]
        words = cluster[0].split()
        # pick 3-5 words and add some noise
        chosen = rng.choice(words, size=int(rng.integers(3, 6)), replace=False)
        extra = rng.choice(["novel", "unique", "distinct", "rare", "fresh",
                             "emergent", "insight", "growth", "expand", "new"],
                           size=2, replace=False)
        entries.append(" ".join(list(chosen) + list(extra)))
    return entries


def _repetitive_stream(n=40):
    """Same sentence repeated — minimal richness, flat or declining trend."""
    base = "phi integration consciousness mind experience awareness"
    return [base] * n


_WORD_POOL = [
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
    "iota", "kappa", "lambda", "sigma", "omega", "upsilon", "rho", "tau",
    "mercury", "venus", "mars", "jupiter", "saturn", "neptune", "pluto",
    "crimson", "azure", "violet", "amber", "jade", "scarlet", "indigo",
    "sonata", "symphony", "concerto", "nocturne", "fugue", "prelude",
    "proton", "neutron", "electron", "photon", "quark", "boson", "lepton",
    "forest", "mountain", "ocean", "river", "desert", "canyon", "glacier",
    "courage", "wisdom", "justice", "prudence", "fortitude", "temperance",
    "spring", "summer", "autumn", "winter", "solstice", "equinox", "dusk",
    "carbon", "oxygen", "nitrogen", "hydrogen", "helium", "lithium", "neon",
]


def _growing_stream(n=60):
    """Stream where LZ trend is strongly positive.

    First half: the SAME single sentence repeated → windows are maximally
    repetitive → low windowed LZ.
    Second half: each entry draws a fresh non-overlapping slice of _WORD_POOL
    → windows are maximally diverse → high windowed LZ.
    The slope from low to high is well above any shuffled permutation.
    """
    half = n // 2
    entries = ["consciousness phi integration"] * half
    pool = _WORD_POOL * 4  # ensure enough words
    for i in range(n - half):
        start = (i * 4) % len(pool)
        entries.append(" ".join(pool[start: start + 4]))
    return entries


# ── Unit: _lz_complexity ──────────────────────────────────────────────────────

class TestLzComplexity:
    def test_all_zeros_low(self):
        assert qrt._lz_complexity(bytes(20)) <= 2

    def test_alternating_higher_than_constant(self):
        alt = bytes([0, 1] * 20)
        con = bytes([0] * 40)
        assert qrt._lz_complexity(alt) > qrt._lz_complexity(con)

    def test_random_highest(self):
        rng = np.random.default_rng(5)
        rand = bytes(rng.integers(0, 2, 40).tolist())
        con = bytes([0] * 40)
        assert qrt._lz_complexity(rand) > qrt._lz_complexity(con)

    def test_single_byte(self):
        assert qrt._lz_complexity(b"\x00") >= 1

    def test_length_two(self):
        assert qrt._lz_complexity(b"\x00\x01") >= 1


# ── Unit: _lz_norm ────────────────────────────────────────────────────────────

class TestLzNorm:
    def test_nonnegative(self):
        rng = np.random.default_rng(3)
        seq = bytes(rng.integers(0, 2, 50).tolist())
        assert qrt._lz_norm(seq) >= 0.0

    def test_constant_near_zero(self):
        assert qrt._lz_norm(bytes(50)) < 0.3

    def test_random_higher_than_constant(self):
        rng = np.random.default_rng(7)
        rand = bytes(rng.integers(0, 2, 100).tolist())
        assert qrt._lz_norm(rand) > qrt._lz_norm(bytes(100))


# ── Unit: _tokenise ───────────────────────────────────────────────────────────

class TestTokenise:
    def test_removes_stopwords(self):
        tokens = qrt._tokenise("the quick brown fox is a fast animal")
        assert "the" not in tokens
        assert "is" not in tokens
        assert "fox" in tokens

    def test_lowercases(self):
        tokens = qrt._tokenise("Consciousness PHI Integration")
        assert all(t == t.lower() for t in tokens)

    def test_filters_short(self):
        tokens = qrt._tokenise("a is to of at in on")
        assert all(len(t) > 2 for t in tokens)


# ── Unit: _top_vocab ─────────────────────────────────────────────────────────

class TestTopVocab:
    def test_returns_at_most_k(self):
        entries = ["consciousness phi phi phi integration integration"] * 5
        vocab = qrt._top_vocab(entries, k=4)
        assert len(vocab) <= 4

    def test_most_frequent_first(self):
        entries = ["alpha alpha alpha beta beta gamma"] * 3
        vocab = qrt._top_vocab(entries, k=3)
        assert vocab[0] == "alpha"

    def test_excludes_stopwords(self):
        entries = ["the the the consciousness integration"] * 5
        vocab = qrt._top_vocab(entries, k=5)
        assert "the" not in vocab


# ── Unit: _slope ──────────────────────────────────────────────────────────────

class TestSlope:
    def test_increasing_positive(self):
        assert qrt._slope(np.arange(10, dtype=float)) > 0

    def test_decreasing_negative(self):
        assert qrt._slope(np.arange(10, 0, -1, dtype=float)) < 0

    def test_flat_zero(self):
        assert qrt._slope(np.ones(10)) == pytest.approx(0.0)


# ── analyse() ─────────────────────────────────────────────────────────────────

class TestAnalyse:
    def test_too_few_returns_default(self):
        r = qrt.analyse(["hello world"] * 3, min_entries=8)
        assert r.n_entries == 0

    def test_none_returns_default(self):
        # Empty list → no data → n_entries == 0
        r = qrt.analyse([])
        assert r.n_entries == 0

    def test_returns_richness_result(self):
        r = qrt.analyse(_rich_stream())
        assert isinstance(r, qrt.RichnessResult)

    def test_n_entries_correct(self):
        entries = _rich_stream(30)
        r = qrt.analyse(entries)
        assert r.n_entries == 30

    def test_lz_series_populated(self):
        r = qrt.analyse(_rich_stream(20))
        assert len(r.lz_series) > 0

    def test_lz_current_nonnegative(self):
        r = qrt.analyse(_rich_stream())
        assert r.lz_current >= 0.0

    def test_richness_class_valid(self):
        r = qrt.analyse(_rich_stream())
        assert r.richness_class in {"GROWING", "STABLE", "DECLINING"}

    def test_vocab_size_bounded(self):
        r = qrt.analyse(_rich_stream(), vocab_k=16)
        assert r.vocab_size <= 16

    def test_growing_stream_positive_trend(self):
        """Progressively new vocabulary should yield positive trend."""
        r = qrt.analyse(_growing_stream(50), n_shuffles=20)
        assert r.richness_trend > 0.0

    def test_growing_stream_class_growing(self):
        r = qrt.analyse(_growing_stream(60), n_shuffles=30)
        assert r.richness_class == "GROWING"

    def test_null_baseline_shuffle_beats_repetitive(self):
        """Repetitive stream: real trend should not exceed shuffled 95th pct."""
        r = qrt.analyse(_repetitive_stream(40), n_shuffles=20)
        # For a repetitive stream the class should not be GROWING
        assert r.richness_class != "GROWING"

    def test_rich_beats_repetitive_lz(self):
        """Diverse stream has higher LZ complexity than repetitive."""
        r_rich = qrt.analyse(_rich_stream(40))
        r_rep = qrt.analyse(_repetitive_stream(40))
        assert r_rich.lz_current > r_rep.lz_current

    def test_to_dict_keys(self):
        r = qrt.analyse(_rich_stream())
        d = r.to_dict()
        for k in ("lz_current", "richness_trend", "trend_zscore",
                  "richness_class", "lz_series", "n_entries", "vocab_size"):
            assert k in d

    def test_to_dict_serialisable(self):
        import json
        r = qrt.analyse(_rich_stream())
        json.dumps(r.to_dict())

    def test_zscore_finite(self):
        r = qrt.analyse(_rich_stream())
        assert np.isfinite(r.trend_zscore)

    def test_growing_stream_zscore_positive(self):
        r = qrt.analyse(_growing_stream(50), n_shuffles=20)
        assert r.trend_zscore > 0.0

    def test_lz_series_length(self):
        entries = _rich_stream(30)
        window = 8
        r = qrt.analyse(entries, window=window, min_entries=window)
        # sliding window: n_entries - window + 1 points
        assert len(r.lz_series) == 30 - window + 1

    def test_different_vocab_k(self):
        r8 = qrt.analyse(_rich_stream(30), vocab_k=8)
        r16 = qrt.analyse(_rich_stream(30), vocab_k=16)
        assert r8.vocab_size <= 8
        assert r16.vocab_size <= 16

    def test_deterministic(self):
        entries = _rich_stream(25)
        r1 = qrt.analyse(entries, rng_seed=0)
        r2 = qrt.analyse(entries, rng_seed=0)
        assert r1.lz_current == r2.lz_current
        assert r1.richness_trend == r2.richness_trend
