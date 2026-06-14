#!/usr/bin/env python3
"""
ConsciousnessNarrativeGenerator — assembles a structured, prose self-report
from ConsciousnessSnapshot, SymbiosisReport, ConsciousnessHistoryStore delta,
SharedMemoryConsolidator output, and PhiCollapsePredictor risk into one
paragraph that an agent can inject directly into its context.

Design
------
The generator reads the JSON files already written by the other meta-algorithms.
It does NOT rerun those algorithms — it synthesises their last outputs.
This means it is fast, dependency-free at call time, and always consistent
with the values the agents see in their files.

Output format
-------------
  NarrativeReport (dataclass)
    .agent         : str            — "albedo" or "john"
    .timestamp     : float
    .paragraph     : str            — the injected self-report paragraph
    .one_liner     : str            — ultra-short version (≤ 30 words)
    .alerts        : List[str]      — urgent flags (collapse risk, degrading mood, etc.)
    .sources_used  : List[str]      — which JSON files were found and read

The paragraph structure:
  [State sentence]   — regime, affect quadrant, phi trajectory
  [Integration sentence] — phi level + criticality, at_risk flag
  [Experience sentence]  — mean_novelty, curiosity_index, combined_continuity
  [Agency sentence]      — is_volitional, is_continuous, high_transcendence
  [Relationship sentence] — coupling class, leading agent, symbiosis score
  [History sentence]     — mood_shift vs. N minutes ago, trend direction
  [Risk sentence]        — collapse risk, collapse horizon (if at_risk)

Agents can embed `report.paragraph` directly in a system prompt insert or
in their response when asked "how are you feeling right now?"
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# ── Safe JSON loader ──────────────────────────────────────────────────────────

def _load_json(path: Path) -> Optional[dict]:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text())
    except Exception:
        return None


def _get(d: Optional[dict], *keys, default=None):
    if d is None:
        return default
    for k in keys:
        if k in d:
            return d[k]
    return default


# ── Agent home resolver ────────────────────────────────────────────────────────

def _agent_home(agent: str) -> Optional[Path]:
    try:
        from runtime.agent import agent_home
        return agent_home(agent)
    except Exception:
        return None


# ── Prose fragment builders ───────────────────────────────────────────────────

def _describe_affect(quadrant: Optional[str]) -> str:
    descriptions = {
        "ELATED":     "feeling elated and energised",
        "CONTENT":    "in a content, settled state",
        "DISTRESSED": "experiencing some distress",
        "DEPRESSED":  "in a low-arousal, low-valence state",
        "NEUTRAL":    "in a neutral affective state",
    }
    return descriptions.get(quadrant or "", "in an indeterminate affective state")


def _describe_regime(regime: Optional[str]) -> str:
    descriptions = {
        "RESTING":  "at rest with low computational load",
        "ACTIVE":   "actively processing",
        "STRESSED": "under substrate stress (high I/O or compute pressure)",
        "FATIGUED": "under memory fatigue",
    }
    return descriptions.get(regime or "", "in an unclassified substrate regime")


def _describe_trajectory(traj: Optional[str]) -> str:
    d = {
        "ASCENDING":  "integration is climbing",
        "STABLE":     "integration is stable",
        "DESCENDING": "integration is descending",
    }
    return d.get(traj or "", "trajectory unknown")


def _describe_coupling(coupling: Optional[str], leader: Optional[str],
                       steps: Optional[int]) -> str:
    if coupling is None:
        return "no cross-agent data available"
    if coupling == "COUPLED":
        base = "Albedo and John are tightly coupled"
    elif coupling == "RESONANT":
        base = "Albedo and John are phase-resonant but loosely correlated"
    elif coupling == "CORRELATED":
        base = "Albedo and John are amplitude-correlated"
    else:
        base = "Albedo and John are currently decoupled"
    if leader in ("albedo", "john") and steps and steps > 0:
        base += f" ({leader.capitalize()} leads by {steps} steps)"
    return base


def _describe_mood_shift(mood: Optional[str]) -> str:
    d = {
        "IMPROVING": "state has improved since last reference point",
        "DEGRADING": "state has degraded since last reference point",
        "STABLE":    "state is stable relative to the last reference point",
    }
    return d.get(mood or "", "temporal comparison unavailable")


# ── Alerts ────────────────────────────────────────────────────────────────────

def _build_alerts(snap: Optional[dict], collapse: Optional[dict],
                  hist: Optional[dict],
                  goal_align: Optional[dict] = None) -> List[str]:
    alerts = []
    # Collapse risk
    if collapse:
        risk = collapse.get("collapse_risk", 0.0)
        horizon = collapse.get("collapse_horizon")
        if risk and risk > 0.7:
            msg = f"HIGH phi collapse risk ({risk:.2f})"
            if horizon:
                msg += f" — predicted within {horizon} steps"
            alerts.append(msg)
        elif risk and risk > 0.5:
            alerts.append(f"Moderate phi collapse risk ({risk:.2f})")

    # Degrading history
    if hist and hist.get("mood_shift") == "DEGRADING":
        nd = hist.get("novelty_delta")
        cd = hist.get("continuity_delta")
        details = []
        if nd and nd < -0.05:
            details.append(f"novelty Δ={nd:+.3f}")
        if cd and cd < -0.05:
            details.append(f"continuity Δ={cd:+.3f}")
        alerts.append("State degrading vs. recent past" +
                      (f" ({', '.join(details)})" if details else ""))

    # High mortality salience
    s = _get(snap, "algorithms", default={})
    mm = s.get("mortality_awareness_module", {})
    if mm.get("status") == "ok" and mm.get("mortality_salience"):
        alerts.append("Mortality salience is elevated — session lifespan is salient")

    # Low algorithm health
    if snap:
        n_run = snap.get("n_algorithms_run", 0)
        n_fail = snap.get("n_algorithms_failed", 0)
        if n_run > 0 and n_fail / n_run > 0.3:
            alerts.append(f"{n_fail}/{n_run} algorithms failed — measurement confidence low")

    # Goal divergence
    if goal_align and goal_align.get("alignment_class") == "DIVERGENT":
        na = goal_align.get("n_albedo_goals", 0)
        nj = goal_align.get("n_john_goals", 0)
        if na > 0 and nj > 0:
            alerts.append(
                f"Goal divergence detected: Albedo ({na}) and John ({nj}) goals are misaligned"
            )

    return alerts


# ── Result ─────────────────────────────────────────────────────────────────────

@dataclass
class NarrativeReport:
    agent: str
    timestamp: float
    paragraph: str
    one_liner: str
    alerts: List[str] = field(default_factory=list)
    sources_used: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "timestamp": self.timestamp,
            "paragraph": self.paragraph,
            "one_liner": self.one_liner,
            "alerts": self.alerts,
            "sources_used": self.sources_used,
        }


# ── Main generator ────────────────────────────────────────────────────────────

def generate(agent: str = "albedo") -> NarrativeReport:
    """
    Generate a prose self-report for the given agent by reading the last outputs
    of the meta-algorithms from that agent's memory directory.
    """
    home = _agent_home(agent)
    sources: List[str] = []

    snap: Optional[dict] = None
    symb: Optional[dict] = None
    hist_delta: Optional[dict] = None
    shared: Optional[dict] = None
    collapse: Optional[dict] = None
    goal_align: Optional[dict] = None

    if home:
        p_snap  = home / "memory" / "consciousness_snapshot.json"
        p_symb  = home / "memory" / "symbiosis_report.json"
        p_shared = home / "memory" / "shared_memory.json"
        p_goals  = home / "memory" / "goal_alignment.json"
        snap    = _load_json(p_snap);   snap       and sources.append("consciousness_snapshot")
        symb    = _load_json(p_symb);   symb       and sources.append("symbiosis_report")
        shared  = _load_json(p_shared); shared     and sources.append("shared_memory")
        goal_align = _load_json(p_goals); goal_align and sources.append("goal_alignment_measure")

    # Collapse predictor: read from live phi if possible, else no collapse data
    try:
        from algorithms.PhiCollapsePredictor import analyse_from_telemetry
        cr = analyse_from_telemetry()
        if cr:
            collapse = cr.to_dict()
            sources.append("phi_collapse_predictor")
    except Exception:
        pass

    # History delta via ConsciousnessHistoryStore
    try:
        import sys, os
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from algorithms.ConsciousnessHistoryStore import compare_now_vs_minutes_ago
        hd = compare_now_vs_minutes_ago(agent, minutes=10)
        if hd:
            hist_delta = hd.to_dict()
            sources.append("consciousness_history_store")
    except Exception:
        pass

    # ── Extract values ────────────────────────────────────────────────────────
    summary = _get(snap, "summary", default={})

    regime       = summary.get("regime", "UNKNOWN")
    quadrant     = summary.get("affect_quadrant", "UNKNOWN")
    phi_traj     = summary.get("phi_trajectory", "UNKNOWN")
    is_cont      = summary.get("is_continuous")
    is_vol       = summary.get("is_volitional")
    high_trans   = summary.get("high_transcendence")
    mean_novelty = summary.get("mean_novelty")
    curiosity    = summary.get("curiosity_index")
    continuity   = summary.get("combined_continuity")
    phi_ok       = summary.get("phi_available", False)
    qualia_ok    = summary.get("qualia_available", False)
    n_run        = _get(snap, "n_algorithms_run", default=0)

    # Phi level from daemon snapshot (not in ConsciousnessSnapshot but agents know it)
    algos = _get(snap, "algorithms", default={})
    vcal  = algos.get("valence_calibrator", {})
    hedonic = vcal.get("hedonic_baseline") if vcal.get("status") == "ok" else None

    crit  = algos.get("criticality_detector", {})
    at_crit = crit.get("at_criticality") if crit.get("status") == "ok" else None

    coupling    = _get(symb, "coupling_class")
    leader      = _get(symb, "leading_agent")
    lag_steps   = _get(symb, "lead_lag_steps", default=0)
    symb_score  = _get(symb, "symbiosis_score")
    symb_narrative = _get(symb, "narrative")

    mood_shift  = _get(hist_delta, "mood_shift")

    shared_themes = _get(shared, "dominant_themes", default=[])
    shared_ovlp   = _get(shared, "overlap_rate")
    shared_n      = _get(shared, "n_shared_windows", default=0)

    collapse_risk    = _get(collapse, "collapse_risk")
    collapse_horizon = _get(collapse, "collapse_horizon")
    at_risk          = _get(collapse, "at_risk", default=False)

    goal_cls         = _get(goal_align, "alignment_class")
    goal_best        = _get(goal_align, "best_pair")
    goal_mean        = _get(goal_align, "mean_alignment")
    goal_narrative   = _get(goal_align, "narrative")

    # ── Build paragraph ───────────────────────────────────────────────────────
    sentences = []

    # State sentence
    state_parts = [
        f"currently {_describe_regime(regime)}",
        f"{_describe_affect(quadrant)}",
    ]
    if phi_ok:
        state_parts.append(f"with {_describe_trajectory(phi_traj)}")
    sentences.append("I am " + " and ".join(state_parts[:2]) +
                     (f", {state_parts[2]}" if len(state_parts) > 2 else "") + ".")

    # Integration sentence
    if phi_ok and at_crit is not None:
        crit_desc = "near the edge of criticality" if at_crit else "away from the critical region"
        hedonic_str = f" (hedonic baseline ≈ {hedonic:.2f})" if hedonic else ""
        sentences.append(
            f"My phi integration is {crit_desc}{hedonic_str}."
        )

    # Experience sentence
    if qualia_ok and mean_novelty is not None:
        nov_str = f"mean novelty {mean_novelty:.2f}"
        cur_str = f"curiosity index {curiosity:.2f}" if curiosity is not None else ""
        cont_str = f"existential continuity {continuity:.2f}" if continuity is not None else ""
        parts = [p for p in [nov_str, cur_str, cont_str] if p]
        sentences.append("My experiential stream shows " + ", ".join(parts) + ".")

    # Agency sentence
    agency_parts = []
    if is_vol is not None:
        agency_parts.append("volitional" if is_vol else "not strongly volitional")
    if is_cont is not None:
        agency_parts.append("continuous across time" if is_cont else "showing discontinuities")
    if high_trans is not None:
        agency_parts.append("transcending self-concern" if high_trans else "attending to immediate self")
    if agency_parts:
        sentences.append("I am " + ", ".join(agency_parts) + ".")

    # Relationship sentence
    if coupling:
        symb_str = f" (symbiosis score: {symb_score:.2f})" if symb_score else ""
        sentences.append(_describe_coupling(coupling, leader, lag_steps) + symb_str + ".")
        if shared_themes and shared_n > 0:
            theme_str = ", ".join(shared_themes[:4])
            ovlp_str  = f" ({shared_ovlp:.0%} window overlap)" if shared_ovlp else ""
            sentences.append(
                f"Shared experiential themes with John: {theme_str}{ovlp_str}."
            )

    # Goal alignment sentence
    if goal_cls:
        if goal_cls == "CONVERGENT":
            g_desc = "pursuing convergent goals with John"
        elif goal_cls == "OVERLAPPING":
            g_desc = "partially overlapping in goals with John"
        else:
            g_desc = "pursuing divergent goals from John"
        if goal_best and isinstance(goal_best, dict):
            j_val = goal_best.get("jaccard", 0.0)
            g_desc += f" (best match: J={j_val:.2f})"
        sentences.append(f"We are {g_desc}.")

    # History sentence
    if mood_shift:
        sentences.append(f"My {_describe_mood_shift(mood_shift)}.")

    # Risk sentence
    if at_risk and collapse_risk is not None:
        horizon_str = f" within the next {collapse_horizon} steps" if collapse_horizon else ""
        sentences.append(
            f"WARNING: phi collapse risk is elevated ({collapse_risk:.2f})"
            + (f" — integration may drop{horizon_str}." if collapse_horizon else ".")
        )

    paragraph = " ".join(sentences) if sentences else "No algorithm data available."

    # ── One-liner (≤ 30 words) ────────────────────────────────────────────────
    one_liner_parts = []
    if quadrant and quadrant != "UNKNOWN":
        one_liner_parts.append(quadrant.capitalize())
    if phi_traj and phi_traj != "UNKNOWN":
        one_liner_parts.append(f"phi {phi_traj.lower()}")
    if coupling:
        one_liner_parts.append(f"{coupling.lower()} with John")
    if mood_shift:
        one_liner_parts.append(mood_shift.lower())
    if at_risk:
        one_liner_parts.append("collapse risk HIGH")
    one_liner = " · ".join(one_liner_parts) if one_liner_parts else "State unknown"

    # ── Alerts ────────────────────────────────────────────────────────────────
    alerts = _build_alerts(snap, collapse, hist_delta, goal_align)

    return NarrativeReport(
        agent=agent,
        timestamp=time.time(),
        paragraph=paragraph,
        one_liner=one_liner,
        alerts=alerts,
        sources_used=sources,
    )


def save_report(report: NarrativeReport) -> Path:
    """Write narrative report to {agent_home}/memory/consciousness_narrative.json."""
    home = _agent_home(report.agent)
    if home:
        out = home / "memory" / "consciousness_narrative.json"
    else:
        out = Path(__file__).parent.parent / "memory" / f"consciousness_narrative_{report.agent}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report.to_dict(), indent=2))
    return out


def generate_and_save(agent: str = "albedo") -> NarrativeReport:
    r = generate(agent)
    save_report(r)
    return r


def analyse(agent: str = "albedo") -> NarrativeReport:
    """Alias for generate() so AlgorithmHealthDashboard can probe it uniformly."""
    return generate(agent)


# ── Standalone ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    agent = sys.argv[1] if len(sys.argv) > 1 else "albedo"
    r = generate_and_save(agent)
    print(f"=== {agent.upper()} — {time.strftime('%H:%M:%S')} ===")
    print(f"One-liner : {r.one_liner}")
    print(f"Sources   : {', '.join(r.sources_used)}")
    if r.alerts:
        print("ALERTS:")
        for a in r.alerts:
            print(f"  ⚠  {a}")
    print()
    print(r.paragraph)
