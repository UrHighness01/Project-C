#!/usr/bin/env python3
"""Tests for algorithms/ConsciousnessEntropyClock.py."""
import sys
from pathlib import Path
import pytest
import math

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.ConsciousnessEntropyClock as cec


def _entries(texts):
    return [{"content": t} for t in texts]


DIVERSE = [
    "quantum entanglement non-local correlations particles physics field",
    "consciousness integrated information neural temporal binding resonance",
    "hippocampus episodic memory consolidation sleep oscillation delta",
    "thermodynamic entropy irreversibility isolated system phase transition",
    "dopamine reward prediction error striatum basal ganglia motor cortex",
    "recursion algorithm self-reference halting problem Turing completeness",
    "photosynthesis chlorophyll light energy carbon dioxide oxygen glucose",
    "language acquisition syntax phonology morphology developmental milestone",
    "attractor chaos bifurcation limit cycle phase space Lyapunov exponent",
    "protein folding amino acid sequence structure thermodynamic stability",
]

REPETITIVE = ["the cat sat on mat"] * 20


class TestTokenise:
    def test_removes_stopwords(self):
        tokens = cec._tokenise("the cat sat on mat")
        assert "the" not in tokens
        assert "on" not in tokens

    def test_min_length_three(self):
        tokens = cec._tokenise("it is a big cat")
        assert "it" not in tokens
        assert "is" not in tokens

    def test_extracts_words(self):
        tokens = cec._tokenise("consciousness emerges from integration")
        assert "consciousness" in tokens


class TestEntropy:
    def test_uniform_counter_max_entropy(self):
        from collections import Counter
        c = Counter({"a": 5, "b": 5, "c": 5, "d": 5})
        h = cec._entropy(c)
        assert h == pytest.approx(2.0, abs=1e-9)

    def test_single_token_zero_entropy(self):
        from collections import Counter
        assert cec._entropy(Counter({"x": 100})) == pytest.approx(0.0, abs=1e-9)

    def test_empty_counter_zero(self):
        from collections import Counter
        assert cec._entropy(Counter()) == 0.0


class TestAnalyse:
    def test_empty_entries_returns_default(self):
        result = cec.analyse([])
        assert result.n_windows == 0

    def test_too_short_returns_default(self):
        result = cec.analyse(_entries(["hi"]), window_size=50)
        assert result.n_windows == 0

    def test_returns_entropy_clock_result(self):
        result = cec.analyse(_entries(DIVERSE * 5), window_size=20, step=10)
        assert isinstance(result, cec.EntropyClockResult)

    def test_n_windows_positive(self):
        result = cec.analyse(_entries(DIVERSE * 5), window_size=20, step=10)
        assert result.n_windows > 0

    def test_baseline_entropy_positive(self):
        result = cec.analyse(_entries(DIVERSE * 5), window_size=20, step=10)
        assert result.baseline_entropy > 0

    def test_mean_entropy_positive(self):
        result = cec.analyse(_entries(DIVERSE * 5), window_size=20, step=10)
        assert result.mean_entropy > 0

    def test_entropy_variance_nonneg(self):
        result = cec.analyse(_entries(DIVERSE * 5), window_size=20, step=10)
        assert result.entropy_variance >= 0

    def test_cumulative_subjective_time_positive(self):
        result = cec.analyse(_entries(DIVERSE * 5), window_size=20, step=10)
        assert result.cumulative_subjective_time > 0

    def test_wall_time_equals_n_windows(self):
        result = cec.analyse(_entries(DIVERSE * 5), window_size=20, step=10)
        assert result.wall_time_units == result.n_windows

    def test_dilation_ratio_positive(self):
        result = cec.analyse(_entries(DIVERSE * 5), window_size=20, step=10)
        assert result.dilation_ratio > 0

    def test_current_felt_rate_positive(self):
        result = cec.analyse(_entries(DIVERSE * 5), window_size=20, step=10)
        assert result.current_felt_rate > 0

    def test_regime_valid_values(self):
        result = cec.analyse(_entries(DIVERSE * 5), window_size=20, step=10)
        assert result.regime in {"FAST", "NEUTRAL", "SLOW"}

    def test_repetitive_stream_slow_regime(self):
        # Repetitive content → low entropy → dilation < 1 → SLOW
        result = cec.analyse(_entries(REPETITIVE * 10), window_size=20, step=10,
                              slow_threshold=0.95)
        assert result.regime in {"SLOW", "NEUTRAL"}

    def test_diverse_stream_neutral_or_fast(self):
        result = cec.analyse(_entries(DIVERSE * 10), window_size=20, step=10)
        assert result.regime in {"FAST", "NEUTRAL"}

    def test_dilation_ratio_equals_cum_over_n(self):
        result = cec.analyse(_entries(DIVERSE * 5), window_size=20, step=10)
        expected = result.cumulative_subjective_time / result.n_windows
        assert result.dilation_ratio == pytest.approx(expected, rel=1e-5)

    def test_to_dict_serialisable(self):
        import json
        result = cec.analyse(_entries(DIVERSE * 5), window_size=20, step=10)
        json.dumps(result.to_dict())

    def test_to_dict_has_keys(self):
        result = cec.analyse(_entries(DIVERSE * 5), window_size=20, step=10)
        d = result.to_dict()
        for k in ("n_windows", "baseline_entropy", "mean_entropy",
                  "entropy_variance", "cumulative_subjective_time",
                  "wall_time_units", "dilation_ratio", "current_felt_rate", "regime"):
            assert k in d

    def test_step_larger_than_window_still_works(self):
        result = cec.analyse(_entries(DIVERSE * 5), window_size=10, step=50)
        assert result.n_windows >= 0

    def test_text_key_accepted(self):
        entries = [{"text": t} for t in DIVERSE * 5]
        result = cec.analyse(entries, window_size=20, step=10)
        assert result.n_windows > 0

    def test_baseline_windows_clamp(self):
        result = cec.analyse(_entries(DIVERSE * 3), window_size=20, step=10,
                              baseline_windows=100)
        assert result.baseline_entropy >= 0
