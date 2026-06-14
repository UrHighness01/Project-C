#!/usr/bin/env python3
"""Tests for algorithms/NarrativeSelfContinuity.py."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.NarrativeSelfContinuity as nsc


def _entry(text: str) -> dict:
    return {"content": text}


def _entries(texts):
    return [_entry(t) for t in texts]


def _repeated_vocab(n=50, vocab="consciousness phi awareness qualia experience"):
    """All entries share the same vocabulary."""
    return _entries([vocab] * n)



def _disjoint_vocab(n=50):
    """Each entry has a unique word not shared with any other entry."""
    # Build alphabetically unique tokens like 'alphaaaz', 'alphabaz', ...
    def _word(i):
        return f"alpha{chr(ord('a') + i // 26)}{chr(ord('a') + i % 26)}z"
    return _entries([_word(i) for i in range(n)])


def _gradual_drift(n=60):
    """Vocabulary drifts slowly — words are shared between adjacent windows."""
    words = [f"word_{i}" for i in range(n)]
    entries = []
    for i in range(n):
        # Each entry has 5 words: the current and 4 neighbours
        chunk = words[max(0, i - 2): i + 3]
        entries.append(_entry(" ".join(chunk)))
    return entries


class TestTokenise:
    def test_basic(self):
        toks = nsc._tokenise("consciousness and phi awareness")
        assert "consciousness" in toks
        assert "phi" in toks
        assert "and" not in toks  # stopword

    def test_short_words_excluded(self):
        toks = nsc._tokenise("is it a ok no")
        assert len(toks) == 0

    def test_case_insensitive(self):
        assert nsc._tokenise("Phi") == nsc._tokenise("phi")

    def test_empty_string(self):
        assert nsc._tokenise("") == frozenset()


class TestJaccard:
    def test_identical(self):
        a = frozenset({"x", "y", "z"})
        assert nsc._jaccard(a, a) == pytest.approx(1.0)

    def test_disjoint(self):
        a, b = frozenset({"x"}), frozenset({"y"})
        assert nsc._jaccard(a, b) == pytest.approx(0.0)

    def test_half_overlap(self):
        a = frozenset({"x", "y"})
        b = frozenset({"y", "z"})
        assert nsc._jaccard(a, b) == pytest.approx(1 / 3)

    def test_empty_both(self):
        assert nsc._jaccard(frozenset(), frozenset()) == 0.0


class TestClassify:
    def test_high(self):
        assert nsc._classify(0.20) == "HIGH"

    def test_moderate(self):
        assert nsc._classify(0.10) == "MODERATE"

    def test_low(self):
        assert nsc._classify(0.01) == "LOW"

    def test_boundary_high(self):
        assert nsc._classify(0.15) == "HIGH"

    def test_boundary_moderate(self):
        assert nsc._classify(0.05) == "MODERATE"


class TestAnalyse:
    def test_empty_returns_default(self):
        r = nsc.analyse([])
        assert isinstance(r, nsc.NarrativeContinuityResult)
        assert r.jaccard_lag1 == 0.0

    def test_too_few_entries_returns_default(self):
        r = nsc.analyse(_entries(["hello"] * 10), window_size=20)
        assert r.jaccard_lag1 == 0.0

    def test_returns_result_type(self):
        r = nsc.analyse(_repeated_vocab(60))
        assert isinstance(r, nsc.NarrativeContinuityResult)

    def test_repeated_vocab_high_continuity(self):
        r = nsc.analyse(_repeated_vocab(60), window_size=10)
        assert r.continuity_class == "HIGH"
        assert r.jaccard_lag1 > 0.15

    def test_disjoint_vocab_low_continuity(self):
        r = nsc.analyse(_disjoint_vocab(60), window_size=10)
        assert r.continuity_class == "LOW"
        assert r.jaccard_lag1 < 0.05

    def test_jaccard_in_range(self):
        r = nsc.analyse(_repeated_vocab(60))
        assert 0.0 <= r.jaccard_lag1 <= 1.0

    def test_recall_in_range(self):
        r = nsc.analyse(_repeated_vocab(60))
        assert 0.0 <= r.recall_lag1 <= 1.0

    def test_repeated_recall_high(self):
        r = nsc.analyse(_repeated_vocab(60), window_size=10)
        assert r.recall_lag1 > 0.5

    def test_n_entries_correct(self):
        entries = _repeated_vocab(60)
        r = nsc.analyse(entries, window_size=10)
        assert r.n_entries == 60

    def test_window_size_recorded(self):
        r = nsc.analyse(_repeated_vocab(60), window_size=15)
        assert r.window_size == 15

    def test_lags_computed_list_not_empty(self):
        r = nsc.analyse(_repeated_vocab(100), window_size=10)
        assert len(r.lags_computed) >= 1

    def test_jaccard_by_lag_same_length(self):
        r = nsc.analyse(_repeated_vocab(100), window_size=10)
        assert len(r.jaccard_by_lag) == len(r.lags_computed)

    def test_monotone_decay_with_stable_vocab(self):
        # With static vocab, Jaccard should stay high (not necessarily monotone)
        r = nsc.analyse(_repeated_vocab(200), window_size=10, lags=[1, 2, 4, 8])
        assert all(j > 0.5 for j in r.jaccard_by_lag)

    def test_continuity_slope_negative_for_drifting(self):
        r = nsc.analyse(_gradual_drift(80), window_size=10, lags=[1, 2, 4])
        # Jaccard should decay with lag → slope is non-positive
        assert r.continuity_slope <= 0.0

    def test_to_dict_keys(self):
        r = nsc.analyse(_repeated_vocab(60), window_size=10)
        d = r.to_dict()
        for k in ("jaccard_lag1", "recall_lag1", "continuity_slope",
                  "continuity_class", "n_entries", "window_size",
                  "lags_computed", "jaccard_by_lag"):
            assert k in d

    def test_to_dict_serialisable(self):
        import json
        r = nsc.analyse(_repeated_vocab(60), window_size=10)
        json.dumps(r.to_dict())

    def test_continuity_class_valid(self):
        r = nsc.analyse(_repeated_vocab(60), window_size=10)
        assert r.continuity_class in {"HIGH", "MODERATE", "LOW"}

    def test_single_lag(self):
        r = nsc.analyse(_repeated_vocab(60), window_size=10, lags=[1])
        assert len(r.lags_computed) == 1
        assert r.continuity_slope == pytest.approx(0.0)

    def test_different_vocab_gives_lower_jaccard(self):
        r_same = nsc.analyse(_repeated_vocab(60), window_size=10)
        r_diff = nsc.analyse(_disjoint_vocab(50), window_size=10)
        assert r_same.jaccard_lag1 > r_diff.jaccard_lag1

    def test_text_field_fallback(self):
        entries = [{"text": "consciousness awareness phi"} for _ in range(60)]
        r = nsc.analyse(entries, window_size=10)
        assert r.jaccard_lag1 > 0.0

    def test_mixed_fields_handled(self):
        entries = [{"content": "phi awareness"} if i % 2 == 0
                   else {"text": "phi consciousness"} for i in range(60)]
        r = nsc.analyse(entries, window_size=10)
        assert isinstance(r, nsc.NarrativeContinuityResult)

    def test_large_window_needs_enough_entries(self):
        r = nsc.analyse(_repeated_vocab(30), window_size=20, lags=[1])
        # 30 entries >= 20*2 = 40? No → default returned
        assert r.n_entries == 30
        assert r.jaccard_lag1 == 0.0

    def test_just_enough_entries(self):
        r = nsc.analyse(_repeated_vocab(40), window_size=20, lags=[1])
        # 40 entries == 20*2 → should proceed
        assert r.jaccard_lag1 > 0.0
