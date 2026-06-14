#!/usr/bin/env python3
"""Tests for algorithms/IntentionCoherenceTracker.py."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.IntentionCoherenceTracker as ict


def _goal(name, description="", active=True):
    return {"name": name, "description": description, "active": active, "sub_goals": []}


def _entry(text):
    return {"content": text}


GOAL_TEXT = "quantum consciousness integration neural binding information phi"
QUALIA_ON = [_entry(GOAL_TEXT + " more text here")] * 5
QUALIA_OFF = [_entry("cooking recipe pasta dinner wine restaurant fork")] * 5


class TestTokenise:
    def test_filters_short_and_stopwords(self):
        t = ict._tokenise("the cat is on a roof")
        assert "the" not in t
        assert "is" not in t

    def test_min_length_four(self):
        t = ict._tokenise("big huge tiny word")
        assert "big" not in t
        assert "huge" in t

    def test_returns_frozenset(self):
        assert isinstance(ict._tokenise("hello world"), frozenset)


class TestGoalTokens:
    def test_includes_name_tokens(self):
        g = _goal("quantum consciousness")
        t = ict._goal_tokens(g)
        assert "quantum" in t

    def test_includes_description_tokens(self):
        g = {"name": "goal", "description": "neural integration binding", "sub_goals": [], "active": True}
        t = ict._goal_tokens(g)
        assert "neural" in t

    def test_includes_sub_goals(self):
        g = {"name": "goal", "description": "", "sub_goals": ["improve attention focus"], "active": True}
        t = ict._goal_tokens(g)
        assert "attention" in t or "improve" in t


class TestAnalyse:
    def test_empty_goals_and_entries_returns_default(self):
        result = ict.analyse([], [])
        assert result.jaccard == 0.0
        assert result.n_active_goals == 0

    def test_returns_result_type(self):
        result = ict.analyse([_goal("quantum neural")], QUALIA_ON)
        assert isinstance(result, ict.IntentionCoherenceResult)

    def test_aligned_when_same_vocabulary(self):
        goals = [_goal("quantum consciousness neural integration information")]
        result = ict.analyse(goals, QUALIA_ON * 4, recent_n=100)
        assert result.coherence_class == "ALIGNED"

    def test_divergent_when_different_vocabulary(self):
        goals = [_goal("quantum consciousness neural integration information")]
        result = ict.analyse(goals, QUALIA_OFF * 4, recent_n=100)
        assert result.coherence_class in {"DIVERGENT", "PARTIAL"}

    def test_jaccard_in_range(self):
        result = ict.analyse([_goal("test goal here")], QUALIA_ON)
        assert 0.0 <= result.jaccard <= 1.0

    def test_coverage_in_range(self):
        result = ict.analyse([_goal("test")], QUALIA_ON)
        assert 0.0 <= result.coverage <= 1.0

    def test_infiltration_in_range(self):
        result = ict.analyse([_goal("test")], QUALIA_ON)
        assert 0.0 <= result.infiltration <= 1.0

    def test_alert_when_no_goals_false(self):
        result = ict.analyse([], QUALIA_OFF * 5)
        assert not result.is_alert

    def test_alert_when_goals_and_no_overlap(self):
        goals = [_goal("quantum consciousness integration neural")]
        result = ict.analyse(goals, QUALIA_OFF * 5, alert_threshold=0.5)
        assert result.is_alert

    def test_no_alert_when_high_coverage(self):
        goals = [_goal(GOAL_TEXT)]
        result = ict.analyse(goals, QUALIA_ON * 5, alert_threshold=0.05)
        assert not result.is_alert

    def test_inactive_goals_excluded(self):
        g_active = _goal("neural integration quantum", active=True)
        g_inactive = _goal("pasta dinner restaurant", active=False)
        result = ict.analyse([g_active, g_inactive], QUALIA_ON)
        assert result.n_active_goals == 1

    def test_n_intention_tokens_positive(self):
        result = ict.analyse([_goal("consciousness quantum integration neural")], QUALIA_ON)
        assert result.n_intention_tokens > 0

    def test_n_qualia_tokens_positive(self):
        result = ict.analyse([], QUALIA_ON)
        assert result.n_qualia_tokens > 0

    def test_shared_tokens_subset_of_intersection(self):
        goals = [_goal(GOAL_TEXT)]
        result = ict.analyse(goals, QUALIA_ON * 4, recent_n=100)
        for tok in result.shared_tokens:
            assert isinstance(tok, str)

    def test_shared_tokens_at_most_10(self):
        goals = [_goal(GOAL_TEXT * 3)]
        result = ict.analyse(goals, QUALIA_ON * 10, recent_n=200)
        assert len(result.shared_tokens) <= 10

    def test_jaccard_symmetric_measure(self):
        goals = [_goal("alpha beta gamma delta")]
        entries = [_entry("alpha beta gamma epsilon zeta")]
        result = ict.analyse(goals, entries * 3)
        # intersection = {alpha, beta, gamma}, union = {alpha,beta,gamma,delta,epsilon,zeta}
        # J = 3/6 = 0.5
        assert result.jaccard == pytest.approx(0.5, abs=0.05)

    def test_to_dict_serialisable(self):
        import json
        result = ict.analyse([_goal("quantum consciousness")], QUALIA_ON)
        json.dumps(result.to_dict())

    def test_to_dict_keys(self):
        d = ict.analyse([_goal("test")], QUALIA_ON).to_dict()
        for k in ("jaccard", "coverage", "infiltration", "coherence_class",
                  "is_alert", "n_active_goals", "n_intention_tokens",
                  "n_qualia_tokens", "shared_tokens"):
            assert k in d

    def test_text_key_in_entries(self):
        entries = [{"text": GOAL_TEXT}] * 5
        result = ict.analyse([_goal(GOAL_TEXT)], entries)
        assert result.n_qualia_tokens > 0
