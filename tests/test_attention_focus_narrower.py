#!/usr/bin/env python3
"""Tests for algorithms/AttentionFocusNarrower.py."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.AttentionFocusNarrower as afn


def _entries(texts):
    return [{"content": t} for t in texts]


DIVERSE = [
    "quantum entanglement produces non-local correlations between particles",
    "consciousness emerges from integrated information flows in neural networks",
    "the hippocampus consolidates episodic memories during slow-wave sleep",
    "fractals exhibit self-similarity across multiple scales of observation",
    "thermodynamic entropy increases monotonically in isolated systems",
    "dopamine modulates reward prediction error in the striatum",
    "recursion enables algorithms to solve problems through self-reference",
    "photosynthesis converts light energy into chemical bonds in chloroplasts",
    "language acquisition follows predictable developmental milestones in children",
    "synchronisation phenomena emerge from coupled oscillator dynamics",
]


class TestTokenise:
    def test_filters_stopwords(self):
        tokens = afn._tokenise("the cat sat on the mat")
        assert "the" not in tokens
        assert "on" not in tokens

    def test_filters_short_words(self):
        tokens = afn._tokenise("a big cat")
        assert "a" not in tokens

    def test_extracts_content_words(self):
        tokens = afn._tokenise("consciousness emerges from integrated information")
        assert "consciousness" in tokens
        assert "emerges" in tokens

    def test_empty_string_returns_empty(self):
        assert afn._tokenise("") == []


class TestToTokenStream:
    def test_content_key(self):
        entries = [{"content": "quantum consciousness field"}]
        tokens = afn._to_token_stream(entries)
        assert "quantum" in tokens

    def test_text_key(self):
        entries = [{"text": "neural synchrony emerges"}]
        tokens = afn._to_token_stream(entries)
        assert "neural" in tokens

    def test_ignores_non_string(self):
        entries = [{"content": 42}]
        tokens = afn._to_token_stream(entries)
        assert tokens == []

    def test_concatenates_multiple_entries(self):
        entries = [{"content": "alpha beta"}, {"content": "gamma delta"}]
        tokens = afn._to_token_stream(entries)
        assert len(tokens) == 4


class TestEntropy:
    def test_uniform_distribution_high_entropy(self):
        from collections import Counter
        c = Counter({"a": 10, "b": 10, "c": 10, "d": 10})
        h = afn._entropy(c)
        assert h > 1.9

    def test_single_token_zero_entropy(self):
        from collections import Counter
        c = Counter({"x": 100})
        assert afn._entropy(c) == pytest.approx(0.0, abs=1e-9)

    def test_empty_counter_zero(self):
        from collections import Counter
        assert afn._entropy(Counter()) == 0.0


class TestKlDiv:
    def test_identical_distributions_near_zero(self):
        from collections import Counter
        c = Counter({"a": 5, "b": 5})
        assert afn._kl_div(c, c) == pytest.approx(0.0, abs=1e-6)

    def test_divergent_distribution_positive(self):
        from collections import Counter
        local = Counter({"rare_tok": 10})
        bg = Counter({"common_tok": 100, "rare_tok": 1})
        assert afn._kl_div(local, bg) > 0

    def test_out_of_vocab_token_handled(self):
        from collections import Counter
        local = Counter({"novel_word": 5})
        bg = Counter({"other_word": 50})
        kl = afn._kl_div(local, bg)
        assert kl >= 0


class TestAnalyse:
    def test_empty_entries_returns_empty_result(self):
        result = afn.analyse([])
        assert result.top_k == []
        assert result.background_entropy == 0.0

    def test_returns_focus_narrower_result(self):
        entries = _entries(DIVERSE * 5)
        result = afn.analyse(entries, window_size=20, step=5, k=3)
        assert isinstance(result, afn.FocusNarrowerResult)

    def test_top_k_respects_limit(self):
        entries = _entries(DIVERSE * 5)
        result = afn.analyse(entries, window_size=20, step=5, k=3)
        assert len(result.top_k) <= 3

    def test_ranks_are_ascending(self):
        entries = _entries(DIVERSE * 5)
        result = afn.analyse(entries, window_size=20, step=5, k=5)
        ranks = [fp.rank for fp in result.top_k]
        assert ranks == sorted(ranks)

    def test_scores_are_descending(self):
        entries = _entries(DIVERSE * 5)
        result = afn.analyse(entries, window_size=20, step=5, k=5)
        scores = [fp.score for fp in result.top_k]
        assert scores == sorted(scores, reverse=True)

    def test_nms_no_overlapping_windows(self):
        entries = _entries(DIVERSE * 10)
        result = afn.analyse(entries, window_size=40, step=5, k=5)
        centres = [(fp.start_idx + fp.end_idx) / 2 for fp in result.top_k]
        for i in range(len(centres)):
            for j in range(i + 1, len(centres)):
                assert abs(centres[i] - centres[j]) >= 40

    def test_background_entropy_positive(self):
        entries = _entries(DIVERSE * 5)
        result = afn.analyse(entries, window_size=20, step=5, k=3)
        assert result.background_entropy > 0

    def test_mean_score_positive(self):
        entries = _entries(DIVERSE * 5)
        result = afn.analyse(entries, window_size=20, step=5, k=3)
        assert result.mean_score >= 0

    def test_focus_ratio_positive(self):
        entries = _entries(DIVERSE * 5)
        result = afn.analyse(entries, window_size=20, step=5, k=3)
        assert result.focus_ratio >= 0

    def test_focus_point_top_tokens_list(self):
        entries = _entries(DIVERSE * 5)
        result = afn.analyse(entries, window_size=20, step=5, k=3)
        for fp in result.top_k:
            assert isinstance(fp.top_tokens, list)

    def test_local_entropy_nonneg(self):
        entries = _entries(DIVERSE * 5)
        result = afn.analyse(entries, window_size=20, step=5, k=3)
        for fp in result.top_k:
            assert fp.local_entropy >= 0

    def test_surprisal_kl_nonneg(self):
        entries = _entries(DIVERSE * 5)
        result = afn.analyse(entries, window_size=20, step=5, k=3)
        for fp in result.top_k:
            assert fp.surprisal_kl >= 0

    def test_window_token_count(self):
        entries = _entries(DIVERSE * 10)
        result = afn.analyse(entries, window_size=30, step=10, k=3)
        for fp in result.top_k:
            assert len(fp.window_tokens) == 30

    def test_alpha_zero_uses_only_kl(self):
        entries = _entries(DIVERSE * 5)
        result = afn.analyse(entries, window_size=20, step=5, k=3, alpha=0.0)
        for fp in result.top_k:
            assert fp.score == pytest.approx(fp.surprisal_kl, rel=1e-5)

    def test_alpha_one_uses_only_entropy(self):
        entries = _entries(DIVERSE * 5)
        result = afn.analyse(entries, window_size=20, step=5, k=3, alpha=1.0)
        for fp in result.top_k:
            assert fp.score == pytest.approx(fp.local_entropy, rel=1e-5)

    def test_to_dict_serialisable(self):
        import json
        entries = _entries(DIVERSE * 5)
        result = afn.analyse(entries, window_size=20, step=5, k=3)
        json.dumps(result.to_dict())

    def test_to_dict_has_expected_keys(self):
        entries = _entries(DIVERSE * 5)
        result = afn.analyse(entries, window_size=20, step=5, k=3)
        d = result.to_dict()
        assert "background_entropy" in d
        assert "mean_score" in d
        assert "focus_ratio" in d
        assert "top_k" in d

    def test_stream_too_short_for_window(self):
        entries = _entries(["short text"])
        result = afn.analyse(entries, window_size=500, k=3)
        assert result.top_k == []

    def test_k_larger_than_windows_returns_all_valid(self):
        entries = _entries(DIVERSE * 3)
        result = afn.analyse(entries, window_size=40, step=40, k=20)
        assert len(result.top_k) <= 20
