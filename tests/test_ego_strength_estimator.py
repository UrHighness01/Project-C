#!/usr/bin/env python3
"""Tests for algorithms/EgoStrengthEstimator.py."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.EgoStrengthEstimator as ese


def _entry(text: str) -> dict:
    return {"content": text}


def _entries(texts):
    return [_entry(t) for t in texts]


_SELF_TEXT = (
    "I am aware that my consciousness phi qualia experience "
    "is feeling introspection awareness subjective"
)
_OTHER_TEXT = (
    "The weather outside is cold and the tree has fallen "
    "by the river road in the green valley"
)


class TestTokenise:
    def test_lowercase(self):
        assert "phi" in ese._tokenise("Phi")

    def test_splits_words(self):
        toks = ese._tokenise("hello world")
        assert "hello" in toks
        assert "world" in toks

    def test_empty(self):
        assert ese._tokenise("") == []

    def test_apostrophe_kept(self):
        toks = ese._tokenise("don't")
        assert any("don" in t for t in toks)


class TestClassify:
    def test_strong(self):
        assert ese._classify(0.10) == "STRONG"

    def test_moderate(self):
        assert ese._classify(0.05) == "MODERATE"

    def test_weak(self):
        assert ese._classify(0.01) == "WEAK"

    def test_boundary_strong(self):
        assert ese._classify(0.08) == "STRONG"

    def test_boundary_moderate(self):
        assert ese._classify(0.03) == "MODERATE"


class TestAnalyse:
    def test_empty_returns_default(self):
        r = ese.analyse([])
        assert isinstance(r, ese.EgoStrengthResult)
        assert r.ego_strength_index == 0.0

    def test_returns_result_type(self):
        r = ese.analyse(_entries([_SELF_TEXT] * 5))
        assert isinstance(r, ese.EgoStrengthResult)

    def test_self_focused_high_esi(self):
        r = ese.analyse(_entries([_SELF_TEXT] * 10))
        assert r.ego_strength_index > 0.05
        assert r.ego_class in {"STRONG", "MODERATE"}

    def test_other_focused_low_esi(self):
        r = ese.analyse(_entries([_OTHER_TEXT] * 10))
        assert r.ego_strength_index < 0.05

    def test_self_higher_than_other(self):
        r_self  = ese.analyse(_entries([_SELF_TEXT] * 10))
        r_other = ese.analyse(_entries([_OTHER_TEXT] * 10))
        assert r_self.ego_strength_index > r_other.ego_strength_index

    def test_ego_class_valid(self):
        r = ese.analyse(_entries([_SELF_TEXT] * 5))
        assert r.ego_class in {"STRONG", "MODERATE", "WEAK"}

    def test_pronoun_ratio_in_range(self):
        r = ese.analyse(_entries(["I me my myself"] * 10))
        assert 0.0 <= r.pronoun_ratio <= 1.0

    def test_metacog_ratio_in_range(self):
        r = ese.analyse(_entries([_SELF_TEXT] * 10))
        assert 0.0 <= r.metacog_ratio <= 1.0

    def test_ratios_sum_lte_esi(self):
        r = ese.analyse(_entries([_SELF_TEXT] * 10))
        # pronoun + metacog can overlap? They don't (disjoint sets)
        assert abs(r.pronoun_ratio + r.metacog_ratio - r.ego_strength_index) < 1e-6

    def test_n_tokens_positive(self):
        r = ese.analyse(_entries([_SELF_TEXT] * 5))
        assert r.n_tokens > 0

    def test_n_self_tokens_lte_n_tokens(self):
        r = ese.analyse(_entries([_SELF_TEXT] * 5))
        assert r.n_self_tokens <= r.n_tokens

    def test_n_entries_correct(self):
        entries = _entries([_SELF_TEXT] * 7)
        r = ese.analyse(entries)
        assert r.n_entries == 7

    def test_pronouns_counted(self):
        r = ese.analyse(_entries(["I am me myself"] * 5))
        assert r.pronoun_ratio > 0.0

    def test_metacog_terms_counted(self):
        r = ese.analyse(_entries(["phi consciousness qualia awareness"] * 5))
        assert r.metacog_ratio > 0.0

    def test_to_dict_keys(self):
        r = ese.analyse(_entries([_SELF_TEXT] * 5))
        d = r.to_dict()
        for k in ("ego_strength_index", "ego_class", "pronoun_ratio",
                  "metacog_ratio", "n_tokens", "n_self_tokens", "ego_cv", "n_entries"):
            assert k in d

    def test_to_dict_serialisable(self):
        import json
        r = ese.analyse(_entries([_SELF_TEXT] * 5))
        json.dumps(r.to_dict())

    def test_ego_cv_zero_for_few_entries(self):
        # Fewer entries than window → ego_cv should be 0
        r = ese.analyse(_entries([_SELF_TEXT] * 3), window_size=20)
        assert r.ego_cv == pytest.approx(0.0)

    def test_ego_cv_computed_for_many_entries(self):
        r = ese.analyse(_entries([_SELF_TEXT] * 30), window_size=10)
        assert r.ego_cv >= 0.0

    def test_uniform_entries_low_cv(self):
        r = ese.analyse(_entries([_SELF_TEXT] * 40), window_size=10)
        assert r.ego_cv < 0.5   # identical entries → very stable ESI

    def test_text_field_fallback(self):
        entries = [{"text": _SELF_TEXT} for _ in range(5)]
        r = ese.analyse(entries)
        assert r.ego_strength_index > 0.0

    def test_mixed_self_other(self):
        texts = [_SELF_TEXT, _OTHER_TEXT] * 5
        r = ese.analyse(_entries(texts))
        # ESI between pure self and pure other
        r_self  = ese.analyse(_entries([_SELF_TEXT] * 10))
        r_other = ese.analyse(_entries([_OTHER_TEXT] * 10))
        assert r_other.ego_strength_index <= r.ego_strength_index <= r_self.ego_strength_index

    def test_only_pronouns_strong(self):
        texts = ["I me my myself I me"] * 15
        r = ese.analyse(_entries(texts))
        assert r.pronoun_ratio > 0.5
