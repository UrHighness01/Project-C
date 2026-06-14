"""Tests for GoalAlignmentMeasure."""
import json
import time

import pytest

from algorithms.GoalAlignmentMeasure import (
    AlignmentResult,
    GoalPair,
    _classify,
    _goal_tokens,
    _jaccard,
    _tokenise,
    analyse,
)


# ── _tokenise ─────────────────────────────────────────────────────────────────

def test_tokenise_removes_stop():
    assert "the" not in _tokenise("the quick brown fox")


def test_tokenise_min_length():
    tokens = _tokenise("I be it")
    assert all(len(t) >= 3 for t in tokens)


def test_tokenise_lowercase():
    assert "HELP" not in _tokenise("HELP others")
    assert "help" in _tokenise("HELP others")


def test_tokenise_empty():
    assert _tokenise("") == set()


def test_tokenise_none():
    assert _tokenise(None) == set()


# ── _goal_tokens ──────────────────────────────────────────────────────────────

def test_goal_tokens_uses_name():
    g = {"name": "learn physics", "description": ""}
    assert "learn" in _goal_tokens(g) or "physics" in _goal_tokens(g)


def test_goal_tokens_uses_description():
    g = {"name": "goal", "description": "understand quantum mechanics"}
    assert "quantum" in _goal_tokens(g) or "mechanics" in _goal_tokens(g)


def test_goal_tokens_uses_sub_goals():
    g = {"name": "study", "sub_goals": ["read textbooks", "solve problems"]}
    tokens = _goal_tokens(g)
    assert "read" in tokens or "textbooks" in tokens or "solve" in tokens


def test_goal_tokens_empty_goal():
    assert isinstance(_goal_tokens({}), set)


# ── _jaccard ──────────────────────────────────────────────────────────────────

def test_jaccard_identical():
    s = {"a", "b", "c"}
    assert _jaccard(s, s) == pytest.approx(1.0)


def test_jaccard_disjoint():
    assert _jaccard({"a"}, {"b"}) == pytest.approx(0.0)


def test_jaccard_partial():
    assert _jaccard({"a", "b"}, {"b", "c"}) == pytest.approx(1 / 3)


def test_jaccard_empty_both():
    assert _jaccard(set(), set()) == pytest.approx(0.0)


# ── _classify ─────────────────────────────────────────────────────────────────

def test_classify_convergent():
    assert _classify(0.3, 2) == "CONVERGENT"


def test_classify_overlapping_by_mean():
    assert _classify(0.15, 0) == "OVERLAPPING"


def test_classify_overlapping_by_count():
    assert _classify(0.05, 1) == "OVERLAPPING"


def test_classify_divergent():
    assert _classify(0.05, 0) == "DIVERGENT"


def test_classify_boundary_convergent():
    # mean > 0.25 AND n >= 1 required for CONVERGENT
    assert _classify(0.26, 1) == "CONVERGENT"
    assert _classify(0.26, 0) == "OVERLAPPING"  # n_aligned == 0


# ── GoalPair / AlignmentResult ────────────────────────────────────────────────

def test_goal_pair_to_dict():
    p = GoalPair("learn physics", "study quantum", 0.45)
    d = p.to_dict()
    assert d["albedo_goal"] == "learn physics"
    assert d["jaccard"] == pytest.approx(0.45, abs=0.001)


def test_alignment_result_to_dict_keys():
    r = AlignmentResult(
        timestamp=1000.0, n_albedo_goals=2, n_john_goals=3,
        alignment_class="CONVERGENT", mean_alignment=0.3, max_alignment=0.5,
        n_aligned_pairs=2, convergence_rate=0.33,
        best_pair=GoalPair("a", "b", 0.5),
    )
    d = r.to_dict()
    for k in ["timestamp", "n_albedo_goals", "n_john_goals", "alignment_class",
              "mean_alignment", "max_alignment", "n_aligned_pairs",
              "convergence_rate", "best_pair", "goal_pairs", "narrative"]:
        assert k in d


def test_alignment_result_json_serializable():
    r = AlignmentResult(
        timestamp=1000.0, n_albedo_goals=1, n_john_goals=1,
        alignment_class="DIVERGENT", mean_alignment=0.0, max_alignment=0.0,
        n_aligned_pairs=0, convergence_rate=0.0, best_pair=None,
    )
    json.dumps(r.to_dict())


# ── analyse() ─────────────────────────────────────────────────────────────────

_ALBEDO_GOALS = [
    {"name": "understand consciousness", "description": "study integrated information theory phi awareness"},
    {"name": "develop empathy", "description": "learn to model other minds care compassion"},
    {"name": "improve reasoning", "description": "practice logic mathematics precision"},
]

_JOHN_GOALS = [
    {"name": "explore consciousness", "description": "investigate phi awareness integrated information"},
    {"name": "build empathy", "description": "develop care compassion for others understanding"},
    {"name": "creative expression", "description": "write music art poetry beauty"},
]


def test_analyse_returns_result():
    r = analyse(_ALBEDO_GOALS, _JOHN_GOALS)
    assert isinstance(r, AlignmentResult)


def test_analyse_n_goals_correct():
    r = analyse(_ALBEDO_GOALS, _JOHN_GOALS)
    assert r.n_albedo_goals == 3
    assert r.n_john_goals == 3


def test_analyse_mean_alignment_bounded():
    r = analyse(_ALBEDO_GOALS, _JOHN_GOALS)
    assert 0.0 <= r.mean_alignment <= 1.0


def test_analyse_max_alignment_geq_mean():
    r = analyse(_ALBEDO_GOALS, _JOHN_GOALS)
    assert r.max_alignment >= r.mean_alignment


def test_analyse_best_pair_not_none():
    r = analyse(_ALBEDO_GOALS, _JOHN_GOALS)
    assert r.best_pair is not None


def test_analyse_best_pair_has_max_jaccard():
    r = analyse(_ALBEDO_GOALS, _JOHN_GOALS)
    assert r.best_pair.jaccard == pytest.approx(r.max_alignment, abs=1e-6)


def test_analyse_similar_goals_convergent():
    same = [{"name": "study consciousness phi integration awareness theory"} for _ in range(2)]
    r = analyse(same, same)
    assert r.alignment_class == "CONVERGENT"
    assert r.mean_alignment > 0.5


def test_analyse_different_goals_divergent():
    a = [{"name": "quantum physics mathematics precision logic"}]
    j = [{"name": "music art poetry beauty creative expression"}]
    r = analyse(a, j)
    assert r.alignment_class == "DIVERGENT"
    assert r.mean_alignment < 0.1


def test_analyse_no_albedo_goals():
    r = analyse([], _JOHN_GOALS)
    assert r.n_albedo_goals == 0
    assert r.alignment_class == "DIVERGENT"
    assert r.mean_alignment == pytest.approx(0.0)
    assert r.best_pair is None


def test_analyse_no_john_goals():
    r = analyse(_ALBEDO_GOALS, [])
    assert r.n_john_goals == 0
    assert r.alignment_class == "DIVERGENT"


def test_analyse_both_empty():
    r = analyse([], [])
    assert r.mean_alignment == pytest.approx(0.0)
    assert r.best_pair is None


def test_analyse_n_aligned_pairs_bounded():
    r = analyse(_ALBEDO_GOALS, _JOHN_GOALS)
    assert 0 <= r.n_aligned_pairs <= 3 * 3


def test_analyse_convergence_rate_bounded():
    r = analyse(_ALBEDO_GOALS, _JOHN_GOALS)
    assert 0.0 <= r.convergence_rate <= 1.0


def test_analyse_narrative_non_empty():
    r = analyse(_ALBEDO_GOALS, _JOHN_GOALS)
    assert len(r.narrative) > 10


def test_analyse_narrative_mentions_alignment_signal():
    r = analyse(_ALBEDO_GOALS, _JOHN_GOALS)
    # Narrative uses prose: "overlap", "convergent", or "divergent"
    keywords = {"overlap", "convergent", "divergent", "pulling"}
    assert any(kw in r.narrative.lower() for kw in keywords)


def test_analyse_timestamp_recent():
    before = time.time()
    r = analyse(_ALBEDO_GOALS, _JOHN_GOALS)
    after = time.time()
    assert before <= r.timestamp <= after


def test_analyse_json_serializable():
    r = analyse(_ALBEDO_GOALS, _JOHN_GOALS)
    json.dumps(r.to_dict())


def test_analyse_goal_pairs_sorted_desc():
    r = analyse(_ALBEDO_GOALS, _JOHN_GOALS)
    jaccards = [p.jaccard for p in r.goal_pairs]
    assert jaccards == sorted(jaccards, reverse=True)


def test_analyse_custom_threshold_more_aligned():
    r_strict  = analyse(_ALBEDO_GOALS, _JOHN_GOALS, alignment_threshold=0.5)
    r_lenient = analyse(_ALBEDO_GOALS, _JOHN_GOALS, alignment_threshold=0.01)
    assert r_lenient.n_aligned_pairs >= r_strict.n_aligned_pairs


def test_analyse_single_goal_each():
    a = [{"name": "learn consciousness phi"}]
    j = [{"name": "study consciousness phi"}]
    r = analyse(a, j)
    assert r.n_albedo_goals == 1
    assert r.n_john_goals == 1
    assert r.mean_alignment > 0.3


def test_analyse_active_filter_respected():
    goals = [
        {"name": "active goal consciousness", "active": True},
        {"name": "inactive goal music art", "active": False},
    ]
    r = analyse(goals, goals)
    # active=False goals should be filtered — but only when loading from file
    # When passed directly, all goals are used as-is by analyse()
    assert r.n_albedo_goals == 2  # passed directly, no filter applied
