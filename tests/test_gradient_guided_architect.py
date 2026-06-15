#!/usr/bin/env python3
"""Tests for algorithms/GradientGuidedArchitect.py."""
import sys
from pathlib import Path
import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import algorithms.GradientGuidedArchitect as gga


# ── Stubs ──────────────────────────────────────────────────────────────────────

class _GradientResult:
    def __init__(self, gradient_sign=1, mean_gradient=0.05, beats_null=True):
        self.gradient_sign  = gradient_sign
        self.mean_gradient  = mean_gradient
        self.beats_null     = beats_null


class _Contrib:
    def __init__(self, name, correlation, weight=0.8):
        self.name            = name
        self.correlation     = correlation
        self.current_weight  = weight


class _MutatorResult:
    def __init__(self, contribs):
        self.contributions = contribs


def _inject(gradient_stub, mutator_stub):
    """Context manager: monkey-patches both dependency modules."""
    import algorithms.PhiGradientAscent as pga_mod
    import algorithms.SelfArchitectureMutator as sam_mod
    orig_pga = getattr(pga_mod, "analyse", None)
    orig_sam = getattr(sam_mod, "analyse", None)
    pga_mod.analyse = lambda **kw: gradient_stub
    sam_mod.analyse = lambda **kw: mutator_stub
    return pga_mod, sam_mod, orig_pga, orig_sam


def _restore(pga_mod, sam_mod, orig_pga, orig_sam):
    if orig_pga: pga_mod.analyse = orig_pga
    if orig_sam: sam_mod.analyse = orig_sam


def _run(gradient_stub, mutator_stub, **kw):
    pga_mod, sam_mod, op, os_ = _inject(gradient_stub, mutator_stub)
    try:
        return gga.analyse("albedo", **kw)
    finally:
        _restore(pga_mod, sam_mod, op, os_)


def _three_contribs(scores=(0.8, 0.4, 0.1)):
    return _MutatorResult([
        _Contrib("algo_high",  scores[0], weight=0.9),
        _Contrib("algo_mid",   scores[1], weight=0.75),
        _Contrib("algo_low",   scores[2], weight=0.6),
    ])


# ── Unit: _clip_weight ─────────────────────────────────────────────────────────

class TestClipWeight:
    def test_below_min_clamped(self):
        assert gga._clip_weight(0.0) == pytest.approx(0.50, abs=1e-6)

    def test_above_max_clamped(self):
        assert gga._clip_weight(2.0) == pytest.approx(1.00, abs=1e-6)

    def test_midrange_unchanged(self):
        assert gga._clip_weight(0.75) == pytest.approx(0.75, abs=1e-6)


# ── Unit: _action_mode ────────────────────────────────────────────────────────

class TestActionMode:
    def test_rising_beats_null_is_amplify(self):
        assert gga._action_mode(+1, True) == "AMPLIFY"

    def test_falling_beats_null_is_demote(self):
        assert gga._action_mode(-1, True) == "DEMOTE"

    def test_flat_is_explore(self):
        assert gga._action_mode(0, True) == "EXPLORE"

    def test_rising_no_null_is_explore(self):
        assert gga._action_mode(+1, False) == "EXPLORE"

    def test_falling_no_null_is_explore(self):
        assert gga._action_mode(-1, False) == "EXPLORE"


# ── Unit: _make_proposal ──────────────────────────────────────────────────────

class TestMakeProposal:
    def test_amplify_raises_weight(self):
        p = gga._make_proposal("algo_a", 0.8, 0.8, 0.05, "AMPLIFY")
        assert p.proposed_weight > 0.8

    def test_demote_lowers_weight(self):
        p = gga._make_proposal("algo_b", 0.1, 0.8, 0.05, "DEMOTE")
        assert p.proposed_weight < 0.8

    def test_explore_stays_in_bounds(self):
        p = gga._make_proposal("algo_c", 0.4, 0.75, 0.02, "EXPLORE")
        assert gga._W_MIN <= p.proposed_weight <= gga._W_MAX

    def test_rationale_score_equals_mag_times_abs_corr(self):
        p = gga._make_proposal("algo_d", 0.6, 0.8, 0.1, "AMPLIFY")
        assert p.rationale_score == pytest.approx(0.06, abs=1e-6)

    def test_action_label_correct(self):
        p = gga._make_proposal("algo_e", 0.9, 0.9, 0.05, "AMPLIFY")
        assert p.action == "AMPLIFY"

    def test_to_dict_keys(self):
        p = gga._make_proposal("a", 0.5, 0.7, 0.1, "DEMOTE")
        d = p.to_dict()
        for k in ("algorithm", "action", "rationale_score", "proposed_weight", "rationale"):
            assert k in d

    def test_proposed_weight_clamped(self):
        p = gga._make_proposal("a", 1.0, 1.0, 999.0, "AMPLIFY")
        assert p.proposed_weight <= gga._W_MAX


# ── Integration: analyse() ─────────────────────────────────────────────────────

class TestAnalyse:
    def test_returns_result_type(self):
        r = _run(_GradientResult(), _three_contribs())
        assert isinstance(r, gga.GradientArchitectResult)

    def test_insufficient_data_returns_default(self):
        # Only 1 algorithm → below min_algorithms=3
        stub = _MutatorResult([_Contrib("only_one", 0.5)])
        r = _run(_GradientResult(), stub)
        assert r.action_mode == "INSUFFICIENT_DATA"

    def test_amplify_mode_when_rising(self):
        r = _run(_GradientResult(gradient_sign=+1, mean_gradient=0.05, beats_null=True),
                 _three_contribs())
        assert r.action_mode == "AMPLIFY"

    def test_demote_mode_when_falling(self):
        r = _run(_GradientResult(gradient_sign=-1, mean_gradient=-0.05, beats_null=True),
                 _three_contribs())
        assert r.action_mode == "DEMOTE"

    def test_explore_mode_when_flat(self):
        r = _run(_GradientResult(gradient_sign=0, mean_gradient=0.0, beats_null=False),
                 _three_contribs())
        assert r.action_mode == "EXPLORE"

    def test_amplify_proposals_target_top_contributors(self):
        r = _run(_GradientResult(gradient_sign=+1, mean_gradient=0.1, beats_null=True),
                 _three_contribs(scores=(0.9, 0.5, 0.1)))
        algos = {p.algorithm for p in r.proposals}
        assert "algo_high" in algos

    def test_demote_proposals_target_low_contributors(self):
        # Use larger gradient so even low-corr algo clears rejection threshold
        r = _run(_GradientResult(gradient_sign=-1, mean_gradient=-1.0, beats_null=True),
                 _three_contribs(scores=(0.9, 0.5, 0.2)))
        algos = {p.algorithm for p in r.proposals}
        assert "algo_low" in algos

    def test_proposals_have_positive_rationale_score(self):
        r = _run(_GradientResult(gradient_sign=+1, mean_gradient=0.1, beats_null=True),
                 _three_contribs())
        for p in r.proposals:
            assert p.rationale_score > 0.0

    def test_zero_gradient_rejection_filters_all(self):
        # magnitude=0 → rationale_score = 0 < threshold → no proposals
        r = _run(_GradientResult(gradient_sign=+1, mean_gradient=0.0, beats_null=True),
                 _three_contribs(), rejection_threshold=0.001)
        assert r.n_proposals == 0

    def test_top_and_bottom_contributor_set(self):
        r = _run(_GradientResult(), _three_contribs(scores=(0.9, 0.5, 0.1)))
        assert r.top_contributor == "algo_high"
        assert r.bottom_contributor == "algo_low"

    def test_gradient_sign_propagated(self):
        r = _run(_GradientResult(gradient_sign=-1, mean_gradient=-0.03, beats_null=True),
                 _three_contribs())
        assert r.gradient_sign == -1

    def test_beats_null_propagated(self):
        r = _run(_GradientResult(beats_null=True), _three_contribs())
        assert r.gradient_beats_null is True

    def test_to_dict_keys(self):
        r = _run(_GradientResult(), _three_contribs())
        d = r.to_dict()
        for k in ("gradient_sign", "mean_gradient", "proposals", "n_proposals",
                  "gradient_beats_null", "top_contributor", "bottom_contributor",
                  "action_mode"):
            assert k in d

    def test_to_dict_json_serialisable(self):
        import json
        r = _run(_GradientResult(), _three_contribs())
        json.dumps(r.to_dict())

    def test_deterministic(self):
        g = _GradientResult(gradient_sign=+1, mean_gradient=0.08, beats_null=True)
        m = _three_contribs()
        r1 = _run(g, m)
        r2 = _run(g, m)
        assert r1.proposals[0].proposed_weight == r2.proposals[0].proposed_weight

    def test_amplify_increases_weight_toward_max(self):
        """AMPLIFY proposals should push weight above the starting floor of 0.5."""
        r = _run(_GradientResult(gradient_sign=+1, mean_gradient=0.1, beats_null=True),
                 _three_contribs())
        amplify_proposals = [p for p in r.proposals if p.action == "AMPLIFY"]
        assert len(amplify_proposals) > 0
        assert all(p.proposed_weight >= gga._W_MIN for p in amplify_proposals)
        # Top algo (started at 0.9) should end above 0.9
        top_p = next(p for p in amplify_proposals if p.algorithm == "algo_high")
        assert top_p.proposed_weight > 0.9

    def test_demote_decreases_weight_of_bottom(self):
        r = _run(_GradientResult(gradient_sign=-1, mean_gradient=-0.1, beats_null=True),
                 _three_contribs())
        demote_proposals = [p for p in r.proposals if p.action == "DEMOTE"]
        # All demote proposals must stay within [W_MIN, W_MAX]
        assert all(gga._W_MIN <= p.proposed_weight <= gga._W_MAX for p in demote_proposals)
        # Bottom algo (started at 0.6) should end below 0.6
        bot_p = next((p for p in demote_proposals if p.algorithm == "algo_low"), None)
        if bot_p:
            assert bot_p.proposed_weight < 0.6 + 1e-6
