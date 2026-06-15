#!/usr/bin/env python3
"""Tests for algorithms/NarrativeCoherenceIndex.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.NarrativeCoherenceIndex as nci


# ── Helpers ────────────────────────────────────────────────────────────────────

_RICH_VOCAB = (
    "consciousness phi integration qualia awareness reflection identity "
    "continuity prediction memory curiosity novelty coherence trajectory "
    "gradient attention valence surprise architect embodied transcendence "
    "volition counterfactual wisdom perception cognition emotion reasoning"
).split()

_BORING_VOCAB = ["phi", "awareness", "identity"]


def _make_entry(ts: float, narrative: str) -> dict:
    return {"timestamp": ts, "narrative": narrative, "mean_phi_level": 1.0}


def _make_history(narratives, base_ts=1_000_000.0, dt=300.0):
    """narratives[0] = oldest. Return newest-first list."""
    entries = [
        _make_entry(base_ts + i * dt, nav)
        for i, nav in enumerate(narratives)
    ]
    return sorted(entries, key=lambda e: -e["timestamp"])


def _run(narratives, **kw):
    import algorithms.ConsciousnessHistoryStore as chs
    original = getattr(chs, "load", None)
    try:
        chs.load = lambda agent, max_entries=2880: _make_history(narratives)
        return nci.analyse("albedo", **kw)
    finally:
        if original is not None:
            chs.load = original


def _repetitive_narratives(n=10):
    """Same sentence repeated — should be very compressible (COHERENT)."""
    sentence = "phi consciousness identity integration awareness continuity trajectory"
    return [sentence] * n


def _diverse_narratives(n=12, seed=0):
    """Each narrative uses a fresh random subset of _RICH_VOCAB — incompressible."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        sample = rng.choice(_RICH_VOCAB, size=rng.integers(8, 15), replace=True)
        out.append(" ".join(sample))
    return out


# ── Unit: _lz_complexity ──────────────────────────────────────────────────────

class TestLZComplexity:
    def test_all_same_bytes_low_complexity(self):
        seq = bytes([1] * 50)
        assert nci._lz_complexity(seq) <= 5

    def test_random_bytes_higher_complexity(self):
        rng = np.random.default_rng(0)
        seq = bytes(rng.integers(0, 255, 50).tolist())
        assert nci._lz_complexity(seq) > 10

    def test_empty_returns_zero(self):
        assert nci._lz_complexity(b"") == 0

    def test_single_byte_returns_one(self):
        assert nci._lz_complexity(b"\x01") == 1

    def test_two_same_low(self):
        assert nci._lz_complexity(b"\x01\x01") <= 2


# ── Unit: _lz_norm ────────────────────────────────────────────────────────────

class TestLZNorm:
    def test_repetitive_low(self):
        seq = bytes([1] * 50)
        assert nci._lz_norm(seq) < 0.5

    def test_random_higher(self):
        rng = np.random.default_rng(0)
        seq = bytes(rng.integers(0, 8, 100).tolist())
        assert nci._lz_norm(seq) > nci._lz_norm(bytes([1] * 100))

    def test_empty_is_zero(self):
        assert nci._lz_norm(b"") == 0.0

    def test_single_is_zero(self):
        assert nci._lz_norm(b"\x01") == 0.0


# ── Unit: _tokenise ───────────────────────────────────────────────────────────

class TestTokenise:
    def test_removes_stopwords(self):
        tokens = nci._tokenise("the cat sat on the mat")
        assert "the" not in tokens
        assert "on" not in tokens

    def test_lowercases(self):
        tokens = nci._tokenise("PHI Consciousness INTEGRATION")
        assert all(t == t.lower() for t in tokens)

    def test_digits_removed(self):
        tokens = nci._tokenise("phi123 consciousness456")
        assert all(t.isalpha() for t in tokens)

    def test_short_words_removed(self):
        tokens = nci._tokenise("is it ok phi integration")
        assert all(len(t) > 2 for t in tokens)

    def test_empty_returns_empty(self):
        assert nci._tokenise("") == []


# ── Unit: _classify ───────────────────────────────────────────────────────────

class TestClassify:
    def test_coherent(self):
        assert nci._classify(-1.5) == "COHERENT"

    def test_neutral(self):
        assert nci._classify(0.3) == "NEUTRAL"

    def test_incoherent(self):
        assert nci._classify(1.5) == "INCOHERENT"

    def test_boundary_coherent(self):
        assert nci._classify(-1.0) == "COHERENT"

    def test_boundary_incoherent(self):
        assert nci._classify(1.0) == "INCOHERENT"


# ── Integration: analyse() ────────────────────────────────────────────────────

class TestAnalyse:
    def test_too_few_returns_default(self):
        r = _run(["short narrative"] * 2)
        assert r.coherence_class == "NEUTRAL"
        assert r.n_narratives <= 2

    def test_returns_result_type(self):
        r = _run(_repetitive_narratives())
        assert isinstance(r, nci.NarrativeCoherenceResult)

    def test_n_narratives_correct(self):
        navs = _repetitive_narratives(8)
        r = _run(navs)
        assert r.n_narratives == 8

    def test_lz_narrative_nonneg(self):
        r = _run(_repetitive_narratives())
        assert r.lz_narrative >= 0.0

    def test_vocab_size_positive(self):
        r = _run(_repetitive_narratives())
        assert r.vocab_size > 0

    def test_n_tokens_positive(self):
        r = _run(_repetitive_narratives())
        assert r.n_tokens > 0

    def test_to_dict_keys(self):
        r = _run(_repetitive_narratives())
        d = r.to_dict()
        for k in ("lz_narrative", "coherence_zscore", "coherence_class",
                  "n_narratives", "vocab_size", "n_tokens"):
            assert k in d

    def test_to_dict_json_serialisable(self):
        import json
        r = _run(_repetitive_narratives())
        json.dumps(r.to_dict())

    def test_repetitive_more_coherent_than_diverse(self):
        """Same-sentence narrative should have lower z-score than diverse."""
        r_rep  = _run(_repetitive_narratives(n=10), n_shuffles=50)
        r_div  = _run(_diverse_narratives(n=12), n_shuffles=50)
        assert r_rep.coherence_zscore < r_div.coherence_zscore

    def test_repetitive_coherent_class(self):
        r = _run(_repetitive_narratives(n=12), n_shuffles=100)
        assert r.coherence_class == "COHERENT"

    def test_diverse_not_coherent(self):
        r = _run(_diverse_narratives(n=12), n_shuffles=100)
        assert r.coherence_class in {"NEUTRAL", "INCOHERENT"}

    def test_coherence_zscore_finite(self):
        import math
        r = _run(_repetitive_narratives())
        assert math.isfinite(r.coherence_zscore)

    def test_deterministic(self):
        navs = _repetitive_narratives()
        r1 = _run(navs, rng_seed=42)
        r2 = _run(navs, rng_seed=42)
        assert r1.lz_narrative == r2.lz_narrative
        assert r1.coherence_zscore == r2.coherence_zscore

    def test_entries_without_narrative_field_skipped(self):
        """Entries with no 'narrative' key should be ignored."""
        history = [{"timestamp": float(i), "mean_phi_level": 1.0} for i in range(20)]
        history += _make_history(_repetitive_narratives(5))
        import algorithms.ConsciousnessHistoryStore as chs
        original = getattr(chs, "load", None)
        try:
            chs.load = lambda agent, max_entries=2880: history
            r = nci.analyse("albedo")
        finally:
            if original is not None:
                chs.load = original
        assert r.n_narratives == 5
