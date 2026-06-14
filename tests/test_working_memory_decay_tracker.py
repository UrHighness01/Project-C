#!/usr/bin/env python3
"""Tests for algorithms/WorkingMemoryDecayTracker.py."""
import sys, math
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.WorkingMemoryDecayTracker as wmd

DIVERSE = [
    {"content": f"quantum consciousness neural binding integration field {i}"}
    for i in range(30)
]
CONCENTRATED = [{"content": "same word repeated again again again"} for _ in range(20)]


class TestTokenise:
    def test_stopwords_removed(self):
        assert "the" not in wmd._tokenise("the quick brown fox")

    def test_min_length(self):
        assert "it" not in wmd._tokenise("it is a fact")

    def test_content_words_kept(self):
        assert "quantum" in wmd._tokenise("quantum consciousness")


class TestClassify:
    def test_rapid(self):
        assert wmd._classify(0.3) == "RAPID"

    def test_normal(self):
        assert wmd._classify(0.1) == "NORMAL"

    def test_slow(self):
        assert wmd._classify(0.01) == "SLOW"

    def test_boundary_normal_low(self):
        assert wmd._classify(0.05) == "NORMAL"

    def test_boundary_rapid(self):
        assert wmd._classify(0.2) == "NORMAL"  # exactly 0.2 is NORMAL


class TestTotalStrength:
    def test_zero_lambda_returns_n(self):
        assert wmd._total_strength(0, 10) == pytest.approx(10.0, abs=1e-6)

    def test_large_lambda_approaches_one(self):
        # Very fast decay: almost no entries contribute
        s = wmd._total_strength(10.0, 100)
        assert s < 2.0

    def test_zero_n_returns_zero(self):
        assert wmd._total_strength(0.1, 0) == 0.0

    def test_positive_strength(self):
        assert wmd._total_strength(0.1, 20) > 0


class TestAnalyse:
    def test_empty_returns_default(self):
        result = wmd.analyse([])
        assert result.n_entries == 0

    def test_returns_decay_result(self):
        result = wmd.analyse(DIVERSE)
        assert isinstance(result, wmd.DecayResult)

    def test_n_entries_correct(self):
        result = wmd.analyse(DIVERSE)
        assert result.n_entries == 30

    def test_lambda_positive(self):
        result = wmd.analyse(DIVERSE)
        assert result.lambda_hat > 0

    def test_memory_span_positive(self):
        result = wmd.analyse(DIVERSE)
        assert result.memory_span > 0

    def test_span_inverse_of_lambda(self):
        result = wmd.analyse(DIVERSE)
        assert result.memory_span == pytest.approx(1.0 / result.lambda_hat, rel=1e-4)

    def test_total_strength_positive(self):
        result = wmd.analyse(DIVERSE)
        assert result.total_strength > 0

    def test_total_strength_lte_n(self):
        # Strength is sum of decaying weights, each <= 1, so total <= n
        result = wmd.analyse(DIVERSE)
        assert result.total_strength <= result.n_entries + 1e-6

    def test_decay_regime_valid(self):
        result = wmd.analyse(DIVERSE)
        assert result.decay_regime in {"RAPID", "NORMAL", "SLOW"}

    def test_n_unique_tokens_positive(self):
        result = wmd.analyse(DIVERSE)
        assert result.n_unique_tokens > 0

    def test_mean_token_age_nonneg(self):
        result = wmd.analyse(DIVERSE)
        assert result.mean_token_age >= 0

    def test_concentrated_entries_high_lambda(self):
        # All tokens in first entry → mean age near 0 → high lambda → RAPID
        entries = [{"content": "alpha beta gamma delta"}] + [{"content": ""}] * 19
        result = wmd.analyse(entries)
        # mean_age = 0 → clamp to 0.5 → lambda = 2.0 → RAPID
        assert result.decay_regime == "RAPID"

    def test_spread_entries_lower_lambda(self):
        # Unique token in each of 30 entries → mean age ~15 → lambda ~0.067 → NORMAL/SLOW
        entries = [{"content": f"unique_word_{i:04d}"} for i in range(30)]
        result = wmd.analyse(entries)
        assert result.decay_regime in {"NORMAL", "SLOW"}

    def test_text_key_accepted(self):
        entries = [{"text": "neural consciousness quantum"} for _ in range(10)]
        result = wmd.analyse(entries)
        assert result.n_unique_tokens > 0

    def test_non_string_content_ignored(self):
        entries = [{"content": 42}, {"content": "real text here"}]
        result = wmd.analyse(entries)
        assert result.n_entries == 2

    def test_single_entry_rapid_decay(self):
        result = wmd.analyse([{"content": "consciousness quantum neural"}])
        assert result.n_entries == 1
        assert result.decay_regime == "RAPID"

    def test_to_dict_serialisable(self):
        import json
        json.dumps(wmd.analyse(DIVERSE).to_dict())

    def test_to_dict_keys(self):
        d = wmd.analyse(DIVERSE).to_dict()
        for k in ("lambda_hat", "memory_span", "total_strength", "decay_regime",
                  "n_entries", "n_unique_tokens", "mean_token_age"):
            assert k in d

    def test_more_entries_more_strength(self):
        r10 = wmd.analyse(DIVERSE[:10])
        r30 = wmd.analyse(DIVERSE)
        assert r30.total_strength >= r10.total_strength

    def test_null_comparison_lambda_varies_with_input(self):
        # All tokens in first entry → mean age 0 (clamped to 0.5) → high lambda
        # Tokens evenly spread across 20 entries → mean age ~9.5 → low lambda
        front_loaded = [{"content": "alpha beta gamma delta epsilon zeta eta theta"}] + \
                       [{"content": ""} for _ in range(19)]
        back_spread = [{"content": f"unique_{i}"} for i in range(20)]
        r_front = wmd.analyse(front_loaded)
        r_back = wmd.analyse(back_spread)
        assert r_front.lambda_hat > r_back.lambda_hat
