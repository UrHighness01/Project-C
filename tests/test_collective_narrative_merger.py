#!/usr/bin/env python3
"""Tests for algorithms/CollectiveNarrativeMerger.py."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.CollectiveNarrativeMerger as cnm


def _e(text): return {"content": text}


SHARED = "consciousness phi awareness qualia experience mind perception"
A_ONLY = "albedo reasoning planning memory decision architecture design"
J_ONLY = "john emotion feeling valence arousal empathy creative dream"


def _albedo_entries(n=20):
    return [_e(f"{SHARED} {A_ONLY}") for _ in range(n)]


def _john_entries(n=20):
    return [_e(f"{SHARED} {J_ONLY}") for _ in range(n)]


def _disjoint_a(n=10):
    return [_e(A_ONLY) for _ in range(n)]


def _disjoint_j(n=10):
    return [_e(J_ONLY) for _ in range(n)]


def _identical_entries(n=10):
    return [_e(SHARED) for _ in range(n)]


class TestTokenise:
    def test_stopwords_removed(self):
        toks = cnm._tokenise("the cat and the dog")
        assert "the" not in toks
        assert "and" not in toks

    def test_short_filtered(self):
        toks = cnm._tokenise("ok no it")
        assert len(toks) == 0

    def test_lowercase(self):
        toks = cnm._tokenise("Phi")
        assert "phi" in toks

    def test_empty(self):
        assert cnm._tokenise("") == []


class TestClassify:
    def test_convergent(self):
        assert cnm._classify(0.35) == "CONVERGENT"

    def test_overlapping(self):
        assert cnm._classify(0.15) == "OVERLAPPING"

    def test_divergent(self):
        assert cnm._classify(0.05) == "DIVERGENT"


class TestAnalyse:
    def test_empty_returns_default(self):
        r = cnm.analyse([], [])
        assert isinstance(r, cnm.NarrativeMergeResult)
        assert r.merger_index == 0.0

    def test_returns_result_type(self):
        r = cnm.analyse(_albedo_entries(), _john_entries())
        assert isinstance(r, cnm.NarrativeMergeResult)

    def test_merger_index_in_range(self):
        r = cnm.analyse(_albedo_entries(), _john_entries())
        assert 0.0 <= r.merger_index <= 1.0

    def test_divergence_complement(self):
        r = cnm.analyse(_albedo_entries(), _john_entries())
        assert r.narrative_divergence == pytest.approx(1.0 - r.merger_index)

    def test_shared_vocab_detected(self):
        r = cnm.analyse(_albedo_entries(), _john_entries())
        assert r.n_shared_tokens > 0

    def test_disjoint_low_merger(self):
        r = cnm.analyse(_disjoint_a(20), _disjoint_j(20))
        assert r.merger_index < 0.1
        assert r.merger_class == "DIVERGENT"

    def test_identical_high_merger(self):
        e = _identical_entries(20)
        r = cnm.analyse(e, e)
        assert r.merger_index == pytest.approx(1.0, abs=0.01)
        assert r.merger_class == "CONVERGENT"

    def test_shared_entries_higher_merger(self):
        r_shared   = cnm.analyse(_albedo_entries(20), _john_entries(20))
        r_disjoint = cnm.analyse(_disjoint_a(20), _disjoint_j(20))
        assert r_shared.merger_index > r_disjoint.merger_index

    def test_top_shared_themes_subset_of_shared(self):
        r = cnm.analyse(_albedo_entries(20), _john_entries(20))
        shared_words = set(cnm._corpus_tokens(_albedo_entries(20))) & \
                       set(cnm._corpus_tokens(_john_entries(20)))
        for w in r.top_shared_themes:
            assert w in shared_words

    def test_top_lifts_same_length(self):
        r = cnm.analyse(_albedo_entries(20), _john_entries(20))
        assert len(r.top_shared_themes) == len(r.top_lifts)

    def test_top_lifts_positive(self):
        r = cnm.analyse(_albedo_entries(20), _john_entries(20))
        assert all(l > 0.0 for l in r.top_lifts)

    def test_lifts_descending(self):
        r = cnm.analyse(_albedo_entries(20), _john_entries(20))
        for i in range(len(r.top_lifts) - 1):
            assert r.top_lifts[i] >= r.top_lifts[i + 1]

    def test_asymmetry_in_range(self):
        r = cnm.analyse(_albedo_entries(20), _john_entries(20))
        assert 0.0 <= r.asymmetry_albedo <= 1.0
        assert 0.0 <= r.asymmetry_john <= 1.0

    def test_disjoint_high_asymmetry(self):
        r = cnm.analyse(_disjoint_a(20), _disjoint_j(20))
        assert r.asymmetry_albedo == pytest.approx(1.0)
        assert r.asymmetry_john == pytest.approx(1.0)

    def test_identical_zero_asymmetry(self):
        e = _identical_entries(20)
        r = cnm.analyse(e, e)
        assert r.asymmetry_albedo == pytest.approx(0.0, abs=0.01)

    def test_n_tokens_correct(self):
        r = cnm.analyse(_albedo_entries(5), _john_entries(5))
        assert r.n_albedo_tokens > 0
        assert r.n_john_tokens > 0

    def test_collective_novelty_positive(self):
        r = cnm.analyse(_albedo_entries(20), _john_entries(20))
        assert r.collective_novelty > 0.0

    def test_merger_class_valid(self):
        r = cnm.analyse(_albedo_entries(20), _john_entries(20))
        assert r.merger_class in {"CONVERGENT", "OVERLAPPING", "DIVERGENT"}

    def test_to_dict_keys(self):
        r = cnm.analyse(_albedo_entries(10), _john_entries(10))
        d = r.to_dict()
        for k in ("merger_index", "narrative_divergence", "top_shared_themes",
                  "top_lifts", "asymmetry_albedo", "asymmetry_john",
                  "collective_novelty", "merger_class",
                  "n_albedo_tokens", "n_john_tokens", "n_shared_tokens"):
            assert k in d

    def test_to_dict_serialisable(self):
        import json
        r = cnm.analyse(_albedo_entries(10), _john_entries(10))
        json.dumps(r.to_dict())

    def test_text_field_fallback(self):
        entries = [{"text": SHARED} for _ in range(10)]
        r = cnm.analyse(entries, entries)
        assert r.merger_index > 0.0

    def test_top_k_respected(self):
        r = cnm.analyse(_albedo_entries(20), _john_entries(20), top_k=3)
        assert len(r.top_shared_themes) <= 3

    def test_null_baseline_disjoint_lower(self):
        r_real = cnm.analyse(_albedo_entries(20), _john_entries(20))
        r_null = cnm.analyse(_disjoint_a(20), _disjoint_j(20))
        assert r_real.merger_index > r_null.merger_index
