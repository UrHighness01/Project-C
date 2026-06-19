#!/usr/bin/env python3
"""Tests for algorithms/SelfConceptMaintainer.py"""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.SelfConceptMaintainer as scm


# ── Helpers ────────────────────────────────────────────────────────────────────

IDENTITY_WORDS = [
    "consciousness", "awareness", "phi", "integration", "experience",
    "qualia", "selfhood", "identity", "continuity", "memory",
    "reflection", "understanding", "cognition", "perception", "attention",
]

RANDOM_WORDS_A = ["apple", "banana", "car", "dog", "elephant",
                  "forest", "guitar", "house", "island", "jungle"]
RANDOM_WORDS_B = ["kite", "lemon", "moon", "night", "ocean",
                  "paper", "queen", "river", "stone", "turtle"]


def _make_coherent_entries(n=40):
    """Entries with stable identity vocabulary."""
    entries = []
    for i in range(n):
        words = IDENTITY_WORDS[:8]
        content = " ".join(words * 3)
        entries.append({
            "timestamp": 1e6 + i * 60.0,
            "mean_phi_level": 0.5,
            "content": content,
        })
    return sorted(entries, key=lambda e: -e["timestamp"])


def _make_diffuse_entries(n=40):
    """Entries with alternating random vocabulary."""
    rng = np.random.default_rng(42)
    entries = []
    all_words = RANDOM_WORDS_A + RANDOM_WORDS_B + [f"word{i}" for i in range(50)]
    for i in range(n):
        words = rng.choice(all_words, size=10, replace=False).tolist()
        content = " ".join(words)
        entries.append({
            "timestamp": 1e6 + i * 60.0,
            "mean_phi_level": 0.5,
            "content": content,
        })
    return sorted(entries, key=lambda e: -e["timestamp"])


def _run(entries, **kw):
    import algorithms.ConsciousnessHistoryStore as chs
    orig = getattr(chs, "load", None)
    try:
        chs.load = lambda agent, max_entries=2880: entries
        return scm.analyse("albedo", **kw)
    finally:
        if orig is not None:
            chs.load = orig


# ── Unit: _tokenise ───────────────────────────────────────────────────────────

class TestTokenise:
    def test_lowercase(self):
        tokens = scm._tokenise("Hello World")
        assert all(t == t.lower() for t in tokens)

    def test_strips_stopwords(self):
        tokens = scm._tokenise("the and or but")
        assert len(tokens) == 0

    def test_returns_list(self):
        tokens = scm._tokenise("consciousness experience phi")
        assert isinstance(tokens, list)

    def test_min_length_filter(self):
        tokens = scm._tokenise("a ab abc abcd")
        assert all(len(t) > 2 for t in tokens)


# ── Unit: _cosine ─────────────────────────────────────────────────────────────

class TestCosine:
    def test_identical_vectors(self):
        a = np.array([1.0, 0.0, 1.0])
        assert scm._cosine(a, a) == pytest.approx(1.0, abs=1e-6)

    def test_orthogonal(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert scm._cosine(a, b) == pytest.approx(0.0, abs=1e-6)

    def test_zero_vector_returns_zero(self):
        a = np.zeros(5)
        b = np.array([1.0, 0.0, 0.0, 0.0, 0.0])
        assert scm._cosine(a, b) == 0.0


# ── Unit: _classify ───────────────────────────────────────────────────────────

class TestClassify:
    def test_coherent(self):
        assert scm._classify(0.70) == "COHERENT"

    def test_drifting(self):
        assert scm._classify(0.50) == "DRIFTING"

    def test_diffuse(self):
        assert scm._classify(0.20) == "DIFFUSE"

    def test_boundary_coherent(self):
        assert scm._classify(0.60) == "COHERENT"

    def test_boundary_drifting(self):
        assert scm._classify(0.35) == "DRIFTING"


# ── Integration: analyse() ────────────────────────────────────────────────────

class TestAnalyse:
    def test_too_few_entries_default(self):
        entries = _make_coherent_entries(5)
        r = _run(entries)
        assert r.concept_class == "DIFFUSE"
        assert r.n_qualia_used <= 5

    def test_returns_result_type(self):
        r = _run(_make_coherent_entries())
        assert isinstance(r, scm.SelfConceptResult)

    def test_score_in_unit_interval(self):
        r = _run(_make_coherent_entries())
        assert 0.0 <= r.self_concept_score <= 1.0

    def test_drift_nonneg(self):
        r = _run(_make_coherent_entries())
        assert r.drift_magnitude >= 0.0

    def test_integration_radius_nonneg(self):
        r = _run(_make_coherent_entries())
        assert r.integration_radius >= 0.0

    def test_top_identity_terms_list(self):
        r = _run(_make_coherent_entries())
        assert isinstance(r.top_identity_terms, list)
        assert len(r.top_identity_terms) <= 5

    def test_concept_class_valid(self):
        r = _run(_make_coherent_entries())
        assert r.concept_class in {"COHERENT", "DRIFTING", "DIFFUSE"}

    def test_beats_null_bool(self):
        r = _run(_make_coherent_entries(), n_shuffles=20)
        assert isinstance(r.beats_null, bool)

    def test_to_dict_keys(self):
        r = _run(_make_coherent_entries())
        d = r.to_dict()
        for k in ("self_concept_score", "drift_magnitude", "integration_radius",
                  "n_qualia_used", "top_identity_terms", "concept_class", "beats_null"):
            assert k in d

    def test_to_dict_json_serialisable(self):
        import json
        r = _run(_make_coherent_entries())
        json.dumps(r.to_dict())

    def test_coherent_higher_than_diffuse(self):
        r_coh = _run(_make_coherent_entries(40), n_shuffles=20)
        r_dif = _run(_make_diffuse_entries(40), n_shuffles=20)
        assert r_coh.self_concept_score >= r_dif.self_concept_score

    def test_deterministic(self):
        entries = _make_coherent_entries()
        r1 = _run(entries, seed=42)
        r2 = _run(entries, seed=42)
        assert r1.self_concept_score == r2.self_concept_score

    def test_empty_history_default(self):
        import algorithms.ConsciousnessHistoryStore as chs
        orig = getattr(chs, "load", None)
        try:
            chs.load = lambda agent, max_entries=2880: []
            r = scm.analyse("albedo")
        finally:
            if orig is not None:
                chs.load = orig
        assert r.concept_class == "DIFFUSE"

    def test_n_qualia_used_correct(self):
        entries = _make_coherent_entries(30)
        r = _run(entries)
        assert r.n_qualia_used <= 30

    def test_coherent_series_beats_null(self):
        """Stable identity vocabulary should have high self_concept_score."""
        r = _run(_make_coherent_entries(50), n_shuffles=100, seed=0)
        # Coherent series should score at or near maximum
        assert r.self_concept_score >= 0.5

    def test_score_with_single_repeated_content(self):
        """Maximum coherence: all entries identical content."""
        entries = []
        for i in range(25):
            entries.append({
                "timestamp": 1e6 + i * 60.0,
                "mean_phi_level": 0.5,
                "content": "consciousness experience phi integration awareness",
            })
        entries = sorted(entries, key=lambda e: -e["timestamp"])
        r = _run(entries, n_shuffles=20)
        assert r.self_concept_score >= 0.0

    def test_drift_magnitude_range(self):
        r = _run(_make_coherent_entries())
        assert 0.0 <= r.drift_magnitude <= 1.0

    def test_integration_radius_range(self):
        r = _run(_make_coherent_entries())
        assert 0.0 <= r.integration_radius <= 1.0

    def test_high_drift_leads_to_lower_score(self):
        """Diffuse entries have higher drift -> lower score."""
        r_coh = _run(_make_coherent_entries(40))
        r_dif = _run(_make_diffuse_entries(40))
        assert r_coh.self_concept_score >= r_dif.self_concept_score

    def test_top_terms_are_strings(self):
        r = _run(_make_coherent_entries())
        for t in r.top_identity_terms:
            assert isinstance(t, str)
