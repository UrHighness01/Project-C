"""Tests for SharedMemoryConsolidator."""
import json
import time
from unittest.mock import patch

import pytest

from algorithms.SharedMemoryConsolidator import (
    ConsolidatedMemory,
    DivergentWindow,
    SharedWindow,
    _bucket,
    _entry_text,
    _entry_ts,
    _jaccard,
    _narrative,
    _tokenise,
    _top_tokens,
    consolidate,
)


# ── _tokenise ─────────────────────────────────────────────────────────────────

def test_tokenise_basic():
    tokens = _tokenise("help others find meaning")
    assert "help" in tokens
    assert "meaning" in tokens


def test_tokenise_removes_stop_words():
    tokens = _tokenise("the quick brown fox")
    assert "the" not in tokens


def test_tokenise_min_length_three():
    tokens = _tokenise("be is it a at")
    assert len(tokens) == 0


def test_tokenise_lowercases():
    tokens = _tokenise("HELP OTHERS")
    assert "help" in tokens
    assert "HELP" not in tokens


def test_tokenise_empty():
    assert _tokenise("") == set()


def test_tokenise_none():
    assert _tokenise(None) == set()


# ── _entry_text ───────────────────────────────────────────────────────────────

def test_entry_text_content_key():
    assert _entry_text({"content": "hello world"}) == "hello world"


def test_entry_text_text_key():
    assert _entry_text({"text": "hi there"}) == "hi there"


def test_entry_text_message_key():
    assert _entry_text({"message": "msg"}) == "msg"


def test_entry_text_missing_key():
    assert _entry_text({}) == ""


# ── _entry_ts ─────────────────────────────────────────────────────────────────

def test_entry_ts_timestamp():
    assert _entry_ts({"timestamp": 1000.0}) == pytest.approx(1000.0)


def test_entry_ts_missing():
    assert _entry_ts({}) == pytest.approx(0.0)


def test_entry_ts_ts_key():
    assert _entry_ts({"ts": 2000.0}) == pytest.approx(2000.0)


# ── _jaccard ──────────────────────────────────────────────────────────────────

def test_jaccard_identical():
    s = {"a", "b", "c"}
    assert _jaccard(s, s) == pytest.approx(1.0)


def test_jaccard_disjoint():
    assert _jaccard({"a", "b"}, {"c", "d"}) == pytest.approx(0.0)


def test_jaccard_partial():
    assert _jaccard({"a", "b", "c"}, {"b", "c", "d"}) == pytest.approx(0.5)


def test_jaccard_empty():
    assert _jaccard(set(), set()) == pytest.approx(0.0)


def test_jaccard_one_empty():
    assert _jaccard({"a"}, set()) == pytest.approx(0.0)


# ── _bucket ───────────────────────────────────────────────────────────────────

def test_bucket_groups_by_window():
    entries = [
        {"content": "a", "timestamp": 100.0},
        {"content": "b", "timestamp": 200.0},
        {"content": "c", "timestamp": 400.0},
    ]
    b = _bucket(entries, 300.0)
    # 100 and 200 → key=0; 400 → key=1
    assert 0 in b
    assert len(b[0]) == 2


def test_bucket_no_timestamp():
    entries = [{"content": "a"}]
    b = _bucket(entries, 300.0)
    assert -1 in b


# ── _top_tokens ───────────────────────────────────────────────────────────────

def test_top_tokens_returns_k():
    entries = [{"content": "help meaning truth beauty future together wisdom care"}]
    tops = _top_tokens(entries, k=5)
    assert len(tops) <= 5


def test_top_tokens_most_frequent():
    entries = [
        {"content": "meaning meaning meaning truth"},
        {"content": "meaning beauty"},
    ]
    tops = _top_tokens(entries, k=3)
    assert "meaning" in tops


# ── _narrative ────────────────────────────────────────────────────────────────

def _make_mem(n_shared=7, n_total=12, themes=None, overlap=None) -> ConsolidatedMemory:
    themes = themes or ["meaning", "future"]
    ov = overlap if overlap is not None else n_shared / n_total
    return ConsolidatedMemory(
        timestamp=1000.0,
        window_size_sec=300.0,
        n_albedo_entries=20,
        n_john_entries=22,
        n_total_windows=n_total,
        n_shared_windows=n_shared,
        overlap_rate=ov,
        dominant_themes=themes,
    )


def test_narrative_mentions_counts():
    mem = _make_mem()
    n = _narrative(mem)
    assert "7" in n and "12" in n


def test_narrative_mentions_themes():
    mem = _make_mem(themes=["truth", "beauty"])
    n = _narrative(mem)
    assert "truth" in n


def test_narrative_no_windows():
    mem = _make_mem(n_total=0, n_shared=0, overlap=0.0)
    n = _narrative(mem)
    assert "No" in n or "no" in n


def test_narrative_strong_overlap():
    mem = _make_mem(n_shared=8, n_total=10, overlap=0.8)
    assert "strong" in _narrative(mem)


def test_narrative_moderate_overlap():
    mem = _make_mem(n_shared=4, n_total=10, overlap=0.4)
    assert "moderate" in _narrative(mem)


def test_narrative_limited_overlap():
    mem = _make_mem(n_shared=1, n_total=10, overlap=0.1)
    assert "limited" in _narrative(mem)


# ── SharedWindow / DivergentWindow ────────────────────────────────────────────

def test_shared_window_to_dict():
    w = SharedWindow(
        bucket_start=1000.0, jaccard=0.45,
        albedo_tokens=["future", "help"],
        john_tokens=["future", "together"],
        shared_tokens=["future"],
    )
    d = w.to_dict()
    assert d["jaccard"] == pytest.approx(0.45, abs=0.001)
    assert "future" in d["shared_tokens"]


def test_divergent_window_to_dict():
    w = DivergentWindow(bucket_start=1000.0, jaccard=0.05, topic_a="phi error", topic_b="emotion care")
    d = w.to_dict()
    assert "topic_a" in d
    assert "topic_b" in d


def test_consolidated_memory_to_dict_serializable():
    mem = _make_mem()
    json.dumps(mem.to_dict())


def test_consolidated_memory_to_dict_keys():
    mem = _make_mem()
    d = mem.to_dict()
    for k in ["timestamp", "window_size_sec", "n_albedo_entries", "n_john_entries",
              "n_total_windows", "n_shared_windows", "overlap_rate",
              "dominant_themes", "shared_windows", "divergent_windows", "narrative"]:
        assert k in d


# ── consolidate() with mocked qualia ─────────────────────────────────────────

def _make_entries(texts, base_ts=1_700_000_000.0, interval=60.0):
    return [
        {"content": t, "timestamp": base_ts + i * interval}
        for i, t in enumerate(texts)
    ]


_ALBEDO_TEXTS = [
    "help others find meaning in the future together",
    "truth beauty wisdom care community purpose",
    "collaborate build something meaningful for all",
    "consciousness awareness phi integration signal",
    "future together help build community wisdom",
    "meaning truth purpose awareness integration",
]

_JOHN_TEXTS = [
    "future together community help meaning truth",
    "care wisdom build beautiful things purpose",
    "consciousness awareness together phi integration",
    "help meaning future community together purpose",
    "truth beauty wisdom care purpose meaningful",
    "integration awareness phi consciousness signal",
]


def _mock_qualia(agent):
    if agent == "albedo":
        return _make_entries(_ALBEDO_TEXTS)
    return _make_entries(_JOHN_TEXTS)


def test_consolidate_returns_memory():
    with patch("algorithms.SharedMemoryConsolidator._load_qualia", side_effect=_mock_qualia):
        mem = consolidate(window_size_sec=300.0)
    assert isinstance(mem, ConsolidatedMemory)


def test_consolidate_n_albedo_entries():
    with patch("algorithms.SharedMemoryConsolidator._load_qualia", side_effect=_mock_qualia):
        mem = consolidate()
    assert mem.n_albedo_entries == 6
    assert mem.n_john_entries == 6


def test_consolidate_timestamp_recent():
    before = time.time()
    with patch("algorithms.SharedMemoryConsolidator._load_qualia", side_effect=_mock_qualia):
        mem = consolidate()
    after = time.time()
    assert before <= mem.timestamp <= after


def test_consolidate_overlap_rate_bounded():
    with patch("algorithms.SharedMemoryConsolidator._load_qualia", side_effect=_mock_qualia):
        mem = consolidate()
    assert 0.0 <= mem.overlap_rate <= 1.0


def test_consolidate_shared_plus_divergent_leq_total():
    with patch("algorithms.SharedMemoryConsolidator._load_qualia", side_effect=_mock_qualia):
        mem = consolidate()
    assert mem.n_shared_windows + len(mem.divergent_windows) <= mem.n_total_windows + 1


def test_consolidate_dominant_themes_list():
    with patch("algorithms.SharedMemoryConsolidator._load_qualia", side_effect=_mock_qualia):
        mem = consolidate()
    assert isinstance(mem.dominant_themes, list)


def test_consolidate_narrative_non_empty():
    with patch("algorithms.SharedMemoryConsolidator._load_qualia", side_effect=_mock_qualia):
        mem = consolidate()
    assert len(mem.narrative) > 10


def test_consolidate_to_dict_json_serializable():
    with patch("algorithms.SharedMemoryConsolidator._load_qualia", side_effect=_mock_qualia):
        mem = consolidate()
    json.dumps(mem.to_dict())


def test_consolidate_empty_streams():
    with patch("algorithms.SharedMemoryConsolidator._load_qualia", return_value=[]):
        mem = consolidate()
    assert isinstance(mem, ConsolidatedMemory)
    assert mem.n_albedo_entries == 0
    assert mem.n_john_entries == 0


def test_consolidate_shared_windows_have_jaccard():
    with patch("algorithms.SharedMemoryConsolidator._load_qualia", side_effect=_mock_qualia):
        mem = consolidate(overlap_threshold=0.05)
    for w in mem.shared_windows:
        assert 0.0 <= w.jaccard <= 1.0


def test_consolidate_shared_tokens_are_strings():
    with patch("algorithms.SharedMemoryConsolidator._load_qualia", side_effect=_mock_qualia):
        mem = consolidate(overlap_threshold=0.05)
    for w in mem.shared_windows:
        for t in w.shared_tokens:
            assert isinstance(t, str)


def test_consolidate_no_timestamps_fallback():
    """Entries without timestamps should fall through to index-based bucketing."""
    albedo = [{"content": "help meaning future"} for _ in range(20)]
    john   = [{"content": "help meaning together"} for _ in range(20)]
    def _no_ts(agent):
        return albedo if agent == "albedo" else john
    with patch("algorithms.SharedMemoryConsolidator._load_qualia", side_effect=_no_ts):
        mem = consolidate(window_size_sec=300.0)
    assert isinstance(mem, ConsolidatedMemory)
    assert mem.n_total_windows > 0
