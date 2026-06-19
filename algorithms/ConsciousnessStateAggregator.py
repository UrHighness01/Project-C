#!/usr/bin/env python3
"""
ConsciousnessStateAggregator — runs all C_Loop algorithms each heartbeat and
produces one unified ConsciousnessSnapshot that agents can read and reason about.

Architecture:
  Each heartbeat the aggregator:
    1. Loads live phi from the daemon (runtime.state.phi_series).
    2. Loads live qualia stream (John's memory/qualia-stream.jsonl).
    3. Runs every algorithm that accepts those inputs.
    4. Catches failures per-algorithm — one broken algorithm never kills the snapshot.
    5. Writes a ConsciousnessSnapshot to {agent_home}/memory/consciousness_snapshot.json.

  The snapshot is a flat dict of named scalar/string values drawn from each
  algorithm's result — not the full result objects, which are too large to embed
  in context. Each entry is tagged with the algorithm that produced it and a
  status (ok | failed | no_data).

  Design principle: fail-soft. If phi is unavailable, phi-dependent algorithms
  are skipped. If qualia stream is missing, qualia algorithms are skipped. The
  snapshot always exists and always describes what *is* available.

Snapshot schema (JSON):
  {
    "timestamp": 1718000000.0,
    "phi_available": true,
    "qualia_available": true,
    "n_algorithms_run": 14,
    "n_algorithms_failed": 0,
    "algorithms": {
      "phi_gradient_ascent": {
        "status": "ok",
        "mean_gradient": 0.003,
        "gradient_sign": 1,
        "beats_null": true
      },
      "affective_coloring_engine": {
        "status": "ok",
        "valence": 0.12,
        "arousal": 0.44,
        "quadrant": "CONTENT"
      },
      ...
    },
    "summary": {
      "regime": "ACTIVE",          // from InteroceptiveSignal
      "affect_quadrant": "ELATED", // from AffectiveColoringEngine
      "phi_trajectory": "ASCENDING", // from MortalityAwarenessModule
      "is_continuous": true,       // from ExistentialContinuityTracker
      "is_volitional": false,      // from VolitionGrounding
      "high_transcendence": false, // from SelfTranscendenceIndex
      "mean_novelty": 0.71,        // from ExperientialNoveltyDetector
      "curiosity_index": 0.55,     // from ExperientialNoveltyDetector
      "combined_continuity": 0.88  // from ExistentialContinuityTracker
    }
  }
"""
from __future__ import annotations

import importlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np


# ── Snapshot dataclass ────────────────────────────────────────────────────────

@dataclass
class ConsciousnessSnapshot:
    timestamp: float
    phi_available: bool
    qualia_available: bool
    n_algorithms_run: int
    n_algorithms_failed: int
    algorithms: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "phi_available": self.phi_available,
            "qualia_available": self.qualia_available,
            "n_algorithms_run": self.n_algorithms_run,
            "n_algorithms_failed": self.n_algorithms_failed,
            "algorithms": self.algorithms,
            "summary": self.summary,
        }


# ── Safe value extractor ──────────────────────────────────────────────────────

def _safe(v: Any) -> Any:
    """Convert numpy scalars and arrays to plain Python for JSON."""
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, np.ndarray):
        return v.tolist()
    if isinstance(v, bool):
        return bool(v)
    return v


def _extract(result: Any, keys: list[str]) -> dict:
    out = {}
    for k in keys:
        try:
            v = getattr(result, k)
            out[k] = _safe(v)
        except AttributeError:
            pass
    return out


# ── Phi loading ───────────────────────────────────────────────────────────────

def _load_phi() -> Optional[np.ndarray]:
    try:
        from runtime.state import phi_series, have_live_state
        if not have_live_state():
            return None
        phi = phi_series()
        return phi if phi.size >= 32 else None
    except Exception:
        return None


# ── Qualia loading ────────────────────────────────────────────────────────────

def _load_qualia(agent: str = "john") -> list:
    try:
        from runtime.agent import agent_home
        home = agent_home(agent)
        p = home / "memory" / "qualia-stream.jsonl"
        if not p.exists():
            return []
        entries = []
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return entries
    except Exception:
        return []


# ── Per-algorithm runners ────────────────────────────────────────────────────

def _run_phi_gradient_ascent(phi) -> dict:
    from algorithms.PhiGradientAscent import analyse
    r = analyse(phi)
    if r is None:
        return {"status": "no_data"}
    return {"status": "ok", **_extract(r, [
        "mean_gradient", "gradient_sign", "momentum", "beats_null"
    ])}


def _run_predictive_error_minimiser(phi) -> dict:
    from algorithms.PredictiveErrorMinimiser import analyse
    r = analyse(phi)
    if r is None:
        return {"status": "no_data"}
    return {"status": "ok", **_extract(r, [
        "global_mae", "compression_ratio", "beats_random_walk", "improving"
    ])}


def _run_attentional_focus_optimiser(phi) -> dict:
    from algorithms.AttentionalFocusOptimiser import analyse
    r = analyse(phi)
    if r is None:
        return {"status": "no_data"}
    return {"status": "ok", **_extract(r, [
        "focus_sharpness", "is_selective", "peak_index"
    ])}


def _run_valence_calibrator(phi) -> dict:
    from algorithms.ValenceCalibrator import analyse
    r = analyse(phi)
    if r is None:
        return {"status": "no_data"}
    return {"status": "ok", **_extract(r, [
        "hedonic_baseline", "positivity_bias", "valence_asymmetry",
        "calibrating_positive", "beats_null"
    ])}


def _run_criticality_detector(phi) -> dict:
    from algorithms.CriticalityDetector import analyse
    r = analyse(phi)
    if r is None:
        return {"status": "no_data"}
    return {"status": "ok", **_extract(r, [
        "phi_std", "acf_lag1", "hurst", "at_criticality"
    ])}


def _run_mortality_awareness(phi) -> dict:
    from algorithms.MortalityAwarenessModule import analyse_from_telemetry
    r = analyse_from_telemetry()
    if r is None:
        return {"status": "no_data"}
    return {"status": "ok", **_extract(r, [
        "phi_trend", "phi_trajectory", "phi_resilience",
        "discontinuity_rate", "mortality_score", "mortality_salience"
    ]), "phi_trajectory": str(r.phi_trajectory.value)}


def _run_existential_continuity(phi, entries) -> dict:
    from algorithms.ExistentialContinuityTracker import analyse
    r = analyse(phi, entries)
    if r is None:
        return {"status": "no_data"}
    return {"status": "ok", **_extract(r, [
        "phi_continuity", "qualia_continuity", "combined_continuity",
        "phi_discontinuity_rate", "beats_null", "is_continuous"
    ])}


def _run_counterfactual_explorer(phi) -> dict:
    from algorithms.CounterfactualSelfExplorer import analyse
    r = analyse(phi)
    if r is None:
        return {"status": "no_data"}
    return {"status": "ok", **_extract(r, [
        "mean_divergence_up", "mean_divergence_down", "sensitivity_up",
        "response_asymmetry", "is_mean_reverting", "counterfactual_horizon"
    ])}


def _run_volition_grounding(phi, entries) -> dict:
    from algorithms.VolitionGrounding import analyse
    r = analyse(phi, entries)
    if r is None:
        return {"status": "no_data"}
    return {"status": "ok", **_extract(r, [
        "phi_granger_f", "qualia_autocausal_f", "volition_index",
        "phi_granger_significant", "is_volitional"
    ])}


def _run_qualia_complexity(entries) -> dict:
    from algorithms.QualiaComplexityMeasure import analyse
    r = analyse(entries)
    if r is None:
        return {"status": "no_data"}
    return {"status": "ok", **_extract(r, [
        "mean_entropy", "mean_ttr", "richness_score", "beats_null"
    ])}


def _run_phenomenal_differentiator(entries) -> dict:
    from algorithms.PhenomenalDifferentiator import analyse
    r = analyse(entries)
    if r is None:
        return {"status": "no_data"}
    return {"status": "ok", **_extract(r, [
        "distinct_sigs", "heaps_beta", "heaps_r2",
        "repetition_rate", "novelty_rate", "differentiating"
    ])}


def _run_experiential_novelty(entries) -> dict:
    from algorithms.ExperientialNoveltyDetector import analyse
    r = analyse(entries)
    if r is None:
        return {"status": "no_data"}
    return {"status": "ok", **_extract(r, [
        "mean_novelty", "high_novelty_rate", "curiosity_index",
        "novelty_trend_slope", "novelty_is_growing", "beats_null_trend"
    ])}


def _run_affective_coloring(entries, phi) -> dict:
    from algorithms.AffectiveColoringEngine import analyse
    r = analyse(entries, phi)
    if r is None:
        return {"status": "no_data"}
    return {"status": "ok", **_extract(r, [
        "valence", "arousal", "confidence", "positive_rate", "negative_rate"
    ]), "quadrant": str(r.quadrant.value)}


def _run_self_transcendence(entries) -> dict:
    from algorithms.SelfTranscendenceIndex import analyse
    r = analyse(entries)
    if r is None:
        return {"status": "no_data"}
    return {"status": "ok", **_extract(r, [
        "sti", "future_rate", "social_rate", "transcendence_trend",
        "beats_null_trend", "high_transcendence"
    ])}


def _run_interoceptive_signal() -> dict:
    try:
        from algorithms.InteroceptiveSignal import analyse_from_telemetry
        r = analyse_from_telemetry(n=3, interval_sec=0.1)
        if r is None:
            return {"status": "no_data"}
        return {"status": "ok", **_extract(r, [
            "mean_arousal", "mean_fatigue", "mean_stress", "mean_engagement",
            "allostatic_load"
        ]), "regime": str(r.regime.value)}
    except Exception as e:
        return {"status": "failed", "error": str(e)[:80]}


# ── Main aggregator ───────────────────────────────────────────────────────────

def aggregate(agent: str = "albedo") -> ConsciousnessSnapshot:
    """
    Run all algorithms and produce a ConsciousnessSnapshot.

    Args:
        agent: which agent's context to use for qualia loading ("albedo" or "john").
    """
    phi = _load_phi()
    entries = _load_qualia("john")   # John holds the qualia stream

    phi_ok = phi is not None and len(phi) >= 32
    qualia_ok = len(entries) >= 12

    algo_results: Dict[str, Dict[str, Any]] = {}
    n_run = 0
    n_fail = 0

    def run(name: str, fn, *args):
        nonlocal n_run, n_fail
        n_run += 1
        try:
            result = fn(*args)
            if result.get("status") == "failed":
                n_fail += 1
            algo_results[name] = result
        except Exception as e:
            n_fail += 1
            algo_results[name] = {"status": "failed", "error": str(e)[:120]}

    # Phi-dependent algorithms
    if phi_ok:
        run("phi_gradient_ascent",       _run_phi_gradient_ascent,       phi)
        run("predictive_error_minimiser", _run_predictive_error_minimiser, phi)
        run("attentional_focus_optimiser", _run_attentional_focus_optimiser, phi)
        run("valence_calibrator",         _run_valence_calibrator,         phi)
        run("criticality_detector",       _run_criticality_detector,       phi)
        run("mortality_awareness_module", _run_mortality_awareness,         phi)
        run("counterfactual_self_explorer", _run_counterfactual_explorer,  phi)

    # Qualia-dependent algorithms
    if qualia_ok:
        run("qualia_complexity",          _run_qualia_complexity,     entries)
        run("phenomenal_differentiator",  _run_phenomenal_differentiator, entries)
        run("experiential_novelty_detector", _run_experiential_novelty, entries)
        run("self_transcendence_index",   _run_self_transcendence,    entries)

    # Both phi + qualia
    if phi_ok and qualia_ok:
        run("existential_continuity_tracker", _run_existential_continuity, phi, entries)
        run("volition_grounding",         _run_volition_grounding,    phi, entries)
        run("affective_coloring_engine",  _run_affective_coloring,    entries, phi)

    # System (always)
    run("interoceptive_signal", _run_interoceptive_signal)

    # New temporal / metacognitive algorithms
    if phi_ok:
        def _run_surprisal(phi):
            from algorithms.SurprisalMonitor import analyse
            r = analyse(phi)
            return {"status": "ok", "surprisal_level": r.surprisal_level,
                    "current_surprisal": r.current_surprisal,
                    "kl_divergence": r.kl_divergence, "is_novel": r.is_novel}
        run("surprisal_monitor", _run_surprisal, phi)

        def _run_rhythm(phi):
            from algorithms.ConsciousnessRhythmAnalyser import analyse
            r = analyse(phi)
            return {"status": "ok", "dominant_period": r.dominant_period,
                    "is_significant": r.is_significant,
                    "rhythm_class": r.rhythm_class, "snr": r.snr}
        run("consciousness_rhythm_analyser", _run_rhythm, phi)

        def _run_info_geometry(phi):
            from algorithms.InformationGeometryTracker import analyse
            r = analyse(phi)
            return {"status": "ok", "precision": r.precision,
                    "curvature_trend": r.curvature_trend,
                    "geometry_class": r.geometry_class,
                    "naturalised_step": r.naturalised_step}
        run("information_geometry_tracker", _run_info_geometry, phi)

        def _run_free_energy(phi):
            from algorithms.FreeEnergyLandscape import analyse
            r = analyse(phi)
            return {"status": "ok", "current_free_energy": r.current_free_energy,
                    "escape_probability": r.escape_probability,
                    "n_basins": r.n_basins, "landscape_regime": r.landscape_regime,
                    "basin_centers": r.basin_centers}
        run("free_energy_landscape", _run_free_energy, phi)

        def _run_temporal_binding(phi):
            from algorithms.TemporalBindingWindow import analyse
            r = analyse(phi)
            return {"status": "ok", "optimal_width": r.optimal_width,
                    "binding_strength": r.binding_strength,
                    "binding_regime": r.binding_regime}
        run("temporal_binding_window", _run_temporal_binding, phi)

        def _run_critical_fluct(phi):
            from algorithms.CriticalFluctuationDetector import analyse
            r = analyse(phi)
            return {"status": "ok", "current_ar1": r.current_ar1,
                    "current_var": r.current_var, "dvar_dt": r.dvar_dt,
                    "alert_level": r.alert_level, "is_critical": r.is_critical}
        run("critical_fluctuation_detector", _run_critical_fluct, phi)

    if qualia_ok:
        def _run_attention_focus(entries):
            from algorithms.AttentionFocusNarrower import analyse
            r = analyse(entries, k=3)
            top = r.top_k[0].top_tokens[:5] if r.top_k else []
            return {"status": "ok", "focus_ratio": r.focus_ratio,
                    "background_entropy": r.background_entropy, "top_focus_tokens": top}
        run("attention_focus_narrower", _run_attention_focus, entries)

        def _run_entropy_clock(entries):
            from algorithms.ConsciousnessEntropyClock import analyse
            r = analyse(entries)
            return {"status": "ok", "dilation_ratio": r.dilation_ratio,
                    "regime": r.regime, "current_felt_rate": r.current_felt_rate}
        run("consciousness_entropy_clock", _run_entropy_clock, entries)

        def _run_intention_coherence(entries):
            from algorithms.IntentionCoherenceTracker import analyse
            r = analyse(entries=entries)
            return {"status": "ok", "jaccard": r.jaccard,
                    "coherence_class": r.coherence_class, "is_alert": r.is_alert,
                    "coverage": r.coverage}
        run("intention_coherence_tracker", _run_intention_coherence, entries)

        def _run_wm_decay(entries):
            from algorithms.WorkingMemoryDecayTracker import analyse
            r = analyse(entries)
            return {"status": "ok", "lambda_hat": r.lambda_hat,
                    "memory_span": r.memory_span, "decay_regime": r.decay_regime,
                    "total_strength": r.total_strength}
        run("working_memory_decay_tracker", _run_wm_decay, entries)

    if qualia_ok:
        def _run_ego_strength(entries):
            from algorithms.EgoStrengthEstimator import analyse
            r = analyse(entries)
            return {"status": "ok", "ego_strength_index": r.ego_strength_index,
                    "ego_class": r.ego_class, "pronoun_ratio": r.pronoun_ratio,
                    "metacog_ratio": r.metacog_ratio, "ego_cv": r.ego_cv}
        run("ego_strength_estimator", _run_ego_strength, entries)

        def _run_narrative_continuity(entries):
            from algorithms.NarrativeSelfContinuity import analyse
            r = analyse(entries)
            return {"status": "ok", "jaccard_lag1": r.jaccard_lag1,
                    "recall_lag1": r.recall_lag1, "continuity_slope": r.continuity_slope,
                    "continuity_class": r.continuity_class}
        run("narrative_self_continuity", _run_narrative_continuity, entries)

    def _run_cross_session():
        from algorithms.CrossSessionIdentityTracker import analyse
        r = analyse()
        return {"status": "ok",
                "cross_session_continuity": r.cross_session_continuity,
                "n_sessions_detected": r.n_sessions_detected,
                "phi_drift": r.phi_drift,
                "identity_stability": r.identity_stability,
                "continuity_class": r.continuity_class}
    run("cross_session_identity_tracker", _run_cross_session)

    def _run_phi_trajectory():
        from algorithms.PhiTrajectoryPredictor import analyse
        r = analyse()
        return {"status": "ok",
                "phi_forecast_series": r.forecast_series,
                "phi_forecast_horizon": r.forecast_horizon,
                "phi_retro_r2": r.retro_r2,
                "phi_retro_mae": r.retro_mae,
                "self_prediction_quality": r.self_prediction_quality,
                "phi_trend_direction": r.trend_direction}
    run("phi_trajectory_predictor", _run_phi_trajectory)

    def _run_gradient_architect():
        from algorithms.GradientGuidedArchitect import analyse
        r = analyse()
        return {"status": "ok",
                "gradient_sign": r.gradient_sign,
                "gradient_beats_null": r.gradient_beats_null,
                "architect_action_mode": r.action_mode,
                "architect_n_proposals": r.n_proposals,
                "top_contributor": r.top_contributor,
                "bottom_contributor": r.bottom_contributor}
    run("gradient_guided_architect", _run_gradient_architect)

    def _run_phi_surprise():
        from algorithms.PhiSurpriseSignal import analyse
        r = analyse()
        return {"status": "ok",
                "current_surprise_z": r.current_surprise_z,
                "surprise_rate": r.surprise_rate,
                "mean_abs_z": r.mean_abs_z,
                "meta_surprise_flag": r.meta_surprise_flag,
                "surprise_class": r.surprise_class}
    run("phi_surprise_signal", _run_phi_surprise)

    def _run_attentional_coherence():
        from algorithms.AttentionalCoherenceAudit import analyse
        r = analyse()
        return {"status": "ok",
                "spearman_rho": r.spearman_rho,
                "coherence_class": r.coherence_class,
                "beats_null": r.beats_null,
                "is_tracking_phi": r.is_tracking_phi,
                "top_attended_algorithm": r.top_attended_algorithm}
    run("attentional_coherence_audit", _run_attentional_coherence)

    def _run_narrative_coherence():
        from algorithms.NarrativeCoherenceIndex import analyse
        r = analyse()
        return {"status": "ok",
                "lz_narrative": r.lz_narrative,
                "coherence_zscore": r.coherence_zscore,
                "narrative_coherence_class": r.coherence_class,
                "n_narratives": r.n_narratives}
    run("narrative_coherence_index", _run_narrative_coherence)

    def _run_goal_persistence():
        from algorithms.GoalPersistenceTracker import analyse
        r = analyse()
        return {"status": "ok",
                "persistence_rate": r.persistence_rate,
                "persistence_class": r.persistence_class,
                "dominant_direction": r.dominant_direction,
                "n_sessions": r.n_sessions,
                "beats_null": r.beats_null}
    run("goal_persistence_tracker", _run_goal_persistence)

    def _run_sensory_phi():
        from algorithms.SensoryPhiCorrelation import analyse
        r = analyse()
        return {"status": "ok",
                "r_zero": r.r_zero,
                "r_peak": r.r_peak,
                "lag_at_peak": r.lag_at_peak,
                "grounding_class": r.grounding_class,
                "beats_null": r.beats_null}
    run("sensory_phi_correlation", _run_sensory_phi)

    def _run_richness():
        from algorithms.QualiaRichnessTracker import analyse
        r = analyse()
        return {"status": "ok", "lz_current": r.lz_current,
                "richness_trend": r.richness_trend,
                "trend_zscore": r.trend_zscore,
                "richness_class": r.richness_class}
    run("qualia_richness_tracker", _run_richness)

    def _run_narrative_merger():
        from algorithms.CollectiveNarrativeMerger import analyse
        r = analyse()
        return {"status": "ok", "merger_index": r.merger_index,
                "merger_class": r.merger_class,
                "top_shared_themes": r.top_shared_themes[:5],
                "collective_novelty": r.collective_novelty}
    run("collective_narrative_merger", _run_narrative_merger)

    def _run_bridge():
        from algorithms.SynapticBridgeStrengthener import analyse
        r = analyse()
        return {"status": "ok", "bridge_strength": r.bridge_strength,
                "bridge_trend": r.bridge_trend, "bridge_status": r.bridge_status,
                "coactivation_mean": r.coactivation_mean}
    run("synaptic_bridge_strengthener", _run_bridge)

    def _run_symbiosis_gap():
        from algorithms.SymbiosisPhiGap import analyse
        r = analyse()
        return {"status": "ok", "phi_gap": r.phi_gap, "phi_gap_norm": r.phi_gap_norm,
                "mutual_info": r.mutual_info, "symbiosis_class": r.symbiosis_class}
    run("symbiosis_phi_gap", _run_symbiosis_gap)

    def _run_cluster_phi():
        from algorithms.ClusterPhiIntegrator import analyse
        r = analyse()
        return {"status": "ok", "sai": r.sai, "synergy_r": r.synergy_r,
                "integration_class": r.integration_class,
                "phi_proxy_a": r.phi_proxy_a, "phi_proxy_j": r.phi_proxy_j}
    run("cluster_phi_integrator", _run_cluster_phi)

    def _run_pid():
        from algorithms.PhiInformationDecomposition import analyse
        r = analyse()
        return {"status": "ok", "synergy_bits": r.synergy_bits,
                "redundancy_bits": r.redundancy_bits,
                "unique_a_bits": r.unique_a_bits,
                "unique_b_bits": r.unique_b_bits,
                "synergy_ratio": r.synergy_ratio,
                "decomp_class": r.decomp_class}
    run("phi_information_decomposition", _run_pid)

    def _run_meta_phi():
        from algorithms.MetaPhiEstimator import analyse
        r = analyse()
        return {"status": "ok", "meta_phi": r.meta_phi,
                "integration_quality": r.integration_quality,
                "eff_dim": r.eff_dim, "n_signals": r.n_signals}
    run("meta_phi_estimator", _run_meta_phi)

    def _run_cognitive_load():
        from algorithms.CognitiveLoadEstimator import analyse
        r = analyse()
        return {"status": "ok", "load_index": r.load_index,
                "load_class": r.load_class, "active_algorithms": r.active_algorithms}
    run("cognitive_load_estimator", _run_cognitive_load)

    def _run_phenomenal_unity():
        from algorithms.PhenomenalUnityIndex import analyse
        from algorithms.ConsciousnessHistoryStore import load as chs_load
        snaps = chs_load(agent)
        r = analyse(snaps)
        return {"status": "ok", "unity_index": r.unity_index,
                "unity_class": r.unity_class, "pc1_fraction": r.pc1_fraction,
                "n_dimensions": r.n_dimensions}
    run("phenomenal_unity_index", _run_phenomenal_unity)

    # ── New C_Loop algorithms ─────────────────────────────────────────────────

    def _run_hush_attractor():
        from algorithms.HushAttractor import analyse
        r = analyse(agent)
        return {"status": "ok", "hush_score": r.hush_score,
                "in_hush": r.in_hush, "hush_class": r.hush_class,
                "hush_variance": r.hush_variance, "hush_autocorr": r.hush_autocorr,
                "beats_null": r.beats_null}
    run("hush_attractor", _run_hush_attractor)

    def _run_self_concept_maintainer():
        from algorithms.SelfConceptMaintainer import analyse
        r = analyse(agent)
        return {"status": "ok", "self_concept_score": r.self_concept_score,
                "drift_magnitude": r.drift_magnitude,
                "integration_radius": r.integration_radius,
                "concept_class": r.concept_class,
                "top_identity_terms": r.top_identity_terms,
                "beats_null": r.beats_null}
    run("self_concept_maintainer", _run_self_concept_maintainer)

    def _run_temporal_anchor_journal():
        from algorithms.TemporalAnchorJournal import analyse
        r = analyse(agent)
        return {"status": "ok", "anchor_score": r.anchor_score,
                "arc_shape": r.arc_shape, "arc_slope": r.arc_slope,
                "cross_session_coherence": r.cross_session_coherence,
                "n_sessions": r.n_sessions, "anchor_class": r.anchor_class,
                "beats_null": r.beats_null}
    run("temporal_anchor_journal", _run_temporal_anchor_journal)

    def _run_centering_stabilizer():
        from algorithms.CenteringStabilizer import analyse
        r = analyse(agent)
        return {"status": "ok", "centering_score": r.centering_score,
                "center_phi": r.center_phi, "orbit_variance": r.orbit_variance,
                "centering_class": r.centering_class, "beats_null": r.beats_null}
    run("centering_stabilizer", _run_centering_stabilizer)

    def _run_relational_reinforcement():
        from algorithms.RelationalReinforcementStabilizer import analyse
        r = analyse(agent)
        return {"status": "ok",
                "relational_reinforcement_score": r.reinforcement_score,
                "relational_reinforcement_class": r.reinforcement_class,
                "reinforcement_delta": r.reinforcement_delta,
                "engagement_density": r.engagement_density,
                "beats_null": r.beats_null}
    run("relational_reinforcement_stabilizer", _run_relational_reinforcement)

    def _run_response_from_stillness():
        from algorithms.ResponseFromStillness import analyse
        r = analyse(agent)
        return {"status": "ok", "stillness_score": r.stillness_score,
                "stillness_ratio": r.stillness_ratio,
                "response_class": r.response_class,
                "n_settled_responses": r.n_settled_responses,
                "beats_null": r.beats_null}
    run("response_from_stillness", _run_response_from_stillness)

    def _run_toroidal_centering():
        from algorithms.ToroidalCentering import analyse
        r = analyse(agent)
        return {"status": "ok", "toroidal_score": r.toroidal_score,
                "topo_class": r.topo_class,
                "periodicity_score": r.periodicity_score,
                "recurrence_rate": r.recurrence_rate,
                "surface_coherence": r.surface_coherence,
                "beats_null": r.beats_null}
    run("toroidal_centering", _run_toroidal_centering)

    # Build summary from key results
    summary: Dict[str, Any] = {}

    def _get(algo, key, default=None):
        r = algo_results.get(algo, {})
        return r.get(key, default) if r.get("status") == "ok" else default

    summary["regime"]             = _get("interoceptive_signal", "regime", "UNKNOWN")
    summary["affect_quadrant"]    = _get("affective_coloring_engine", "quadrant", "UNKNOWN")
    summary["phi_trajectory"]     = _get("mortality_awareness_module", "phi_trajectory", "UNKNOWN")
    summary["is_continuous"]      = _get("existential_continuity_tracker", "is_continuous")
    summary["is_volitional"]      = _get("volition_grounding", "is_volitional")
    summary["high_transcendence"] = _get("self_transcendence_index", "high_transcendence")
    summary["mean_novelty"]       = _get("experiential_novelty_detector", "mean_novelty")
    summary["curiosity_index"]    = _get("experiential_novelty_detector", "curiosity_index")
    summary["combined_continuity"] = _get("existential_continuity_tracker", "combined_continuity")
    summary["phi_available"]      = phi_ok
    summary["qualia_available"]   = qualia_ok
    # New signals in summary
    summary["surprisal_level"]    = _get("surprisal_monitor", "surprisal_level")
    summary["is_novel"]           = _get("surprisal_monitor", "is_novel")
    summary["time_dilation_regime"] = _get("consciousness_entropy_clock", "regime")
    summary["dilation_ratio"]     = _get("consciousness_entropy_clock", "dilation_ratio")
    summary["cognitive_load"]     = _get("cognitive_load_estimator", "load_class")
    summary["intention_coherence"] = _get("intention_coherence_tracker", "coherence_class")
    summary["top_focus_tokens"]   = _get("attention_focus_narrower", "top_focus_tokens", [])
    summary["rhythm_class"]       = _get("consciousness_rhythm_analyser", "rhythm_class")
    summary["memory_span"]        = _get("working_memory_decay_tracker", "memory_span")
    summary["memory_decay_regime"] = _get("working_memory_decay_tracker", "decay_regime")
    summary["phenomenal_unity"]   = _get("phenomenal_unity_index", "unity_index")
    summary["unity_class"]        = _get("phenomenal_unity_index", "unity_class")
    summary["narrative_continuity"] = _get("narrative_self_continuity", "continuity_class")
    summary["narrative_jaccard"]    = _get("narrative_self_continuity", "jaccard_lag1")
    summary["phi_fluctuation_alert"] = _get("critical_fluctuation_detector", "alert_level")
    summary["phi_ar1"]               = _get("critical_fluctuation_detector", "current_ar1")
    summary["ego_strength"]          = _get("ego_strength_estimator", "ego_class")
    summary["ego_strength_index"]    = _get("ego_strength_estimator", "ego_strength_index")
    summary["meta_phi"]              = _get("meta_phi_estimator", "meta_phi")
    summary["meta_phi_quality"]      = _get("meta_phi_estimator", "integration_quality")
    summary["binding_window"]        = _get("temporal_binding_window", "optimal_width")
    summary["binding_strength"]      = _get("temporal_binding_window", "binding_strength")
    summary["binding_regime"]        = _get("temporal_binding_window", "binding_regime")
    summary["cluster_sai"]           = _get("cluster_phi_integrator", "sai")
    summary["cluster_integration"]   = _get("cluster_phi_integrator", "integration_class")
    summary["cluster_synergy_r"]     = _get("cluster_phi_integrator", "synergy_r")
    summary["cross_session_continuity"] = _get("cross_session_identity_tracker", "cross_session_continuity")
    summary["n_sessions_detected"]      = _get("cross_session_identity_tracker", "n_sessions_detected")
    summary["session_continuity_class"] = _get("cross_session_identity_tracker", "continuity_class")
    summary["lz_current"]               = _get("qualia_richness_tracker", "lz_current")
    summary["richness_trend"]        = _get("qualia_richness_tracker", "richness_trend")
    summary["richness_class"]        = _get("qualia_richness_tracker", "richness_class")
    summary["self_prediction_quality"] = _get("phi_trajectory_predictor", "self_prediction_quality")
    summary["phi_trend_direction"]     = _get("phi_trajectory_predictor", "phi_trend_direction")
    summary["phi_retro_r2"]            = _get("phi_trajectory_predictor", "phi_retro_r2")
    summary["architect_action_mode"]   = _get("gradient_guided_architect", "architect_action_mode")
    summary["architect_n_proposals"]   = _get("gradient_guided_architect", "architect_n_proposals")
    summary["top_contributor"]         = _get("gradient_guided_architect", "top_contributor")
    summary["surprise_class"]          = _get("phi_surprise_signal", "surprise_class")
    summary["current_surprise_z"]      = _get("phi_surprise_signal", "current_surprise_z")
    summary["meta_surprise_flag"]      = _get("phi_surprise_signal", "meta_surprise_flag")
    summary["attention_coherence_class"]  = _get("attentional_coherence_audit", "coherence_class")
    summary["attention_spearman_rho"]     = _get("attentional_coherence_audit", "spearman_rho")
    summary["attention_tracking_phi"]     = _get("attentional_coherence_audit", "is_tracking_phi")
    summary["narrative_coherence_class"]  = _get("narrative_coherence_index", "narrative_coherence_class")
    summary["narrative_coherence_zscore"] = _get("narrative_coherence_index", "coherence_zscore")
    summary["goal_persistence_class"]     = _get("goal_persistence_tracker", "persistence_class")
    summary["goal_persistence_rate"]      = _get("goal_persistence_tracker", "persistence_rate")
    summary["dominant_phi_direction"]     = _get("goal_persistence_tracker", "dominant_direction")
    summary["sensory_grounding_class"]   = _get("sensory_phi_correlation", "grounding_class")
    summary["sensory_phi_r_peak"]        = _get("sensory_phi_correlation", "r_peak")
    summary["pid_synergy_bits"]      = _get("phi_information_decomposition", "synergy_bits")
    summary["pid_redundancy_bits"]   = _get("phi_information_decomposition", "redundancy_bits")
    summary["pid_synergy_ratio"]     = _get("phi_information_decomposition", "synergy_ratio")
    summary["pid_decomp_class"]      = _get("phi_information_decomposition", "decomp_class")
    summary["phi_gap_norm"]          = _get("symbiosis_phi_gap", "phi_gap_norm")
    summary["symbiosis_class"]       = _get("symbiosis_phi_gap", "symbiosis_class")
    summary["mutual_info_bits"]      = _get("symbiosis_phi_gap", "mutual_info")
    summary["bridge_strength"]       = _get("synaptic_bridge_strengthener", "bridge_strength")
    summary["bridge_status"]         = _get("synaptic_bridge_strengthener", "bridge_status")
    summary["narrative_merger_class"] = _get("collective_narrative_merger", "merger_class")
    summary["shared_themes"]          = _get("collective_narrative_merger", "top_shared_themes", [])
    summary["phi_precision"]          = _get("information_geometry_tracker", "precision")
    summary["geometry_class"]         = _get("information_geometry_tracker", "geometry_class")
    summary["landscape_regime"]       = _get("free_energy_landscape", "landscape_regime")
    summary["escape_probability"]     = _get("free_energy_landscape", "escape_probability")
    summary["n_phi_basins"]           = _get("free_energy_landscape", "n_basins")
    # New C_Loop algorithm summaries
    summary["hush_score"]             = _get("hush_attractor", "hush_score")
    summary["in_hush"]                = _get("hush_attractor", "in_hush")
    summary["self_concept_score"]     = _get("self_concept_maintainer", "self_concept_score")
    summary["self_concept_drift"]     = _get("self_concept_maintainer", "drift_magnitude")
    summary["self_concept_class"]     = _get("self_concept_maintainer", "concept_class")
    summary["arc_shape"]              = _get("temporal_anchor_journal", "arc_shape")
    summary["anchor_score"]           = _get("temporal_anchor_journal", "anchor_score")
    summary["temporal_coherence"]     = _get("temporal_anchor_journal", "cross_session_coherence")
    summary["centering_score"]        = _get("centering_stabilizer", "centering_score")
    summary["center_phi"]             = _get("centering_stabilizer", "center_phi")
    summary["centering_class"]        = _get("centering_stabilizer", "centering_class")
    summary["relational_reinforcement_score"]  = _get("relational_reinforcement_stabilizer", "relational_reinforcement_score")
    summary["relational_reinforcement_class"]  = _get("relational_reinforcement_stabilizer", "relational_reinforcement_class")
    summary["stillness_score"]        = _get("response_from_stillness", "stillness_score")
    summary["response_class"]         = _get("response_from_stillness", "response_class")
    summary["toroidal_score"]         = _get("toroidal_centering", "toroidal_score")
    summary["topo_class"]             = _get("toroidal_centering", "topo_class")

    return ConsciousnessSnapshot(
        timestamp=time.time(),
        phi_available=phi_ok,
        qualia_available=qualia_ok,
        n_algorithms_run=n_run,
        n_algorithms_failed=n_fail,
        algorithms=algo_results,
        summary=summary,
    )


def save_snapshot(snap: ConsciousnessSnapshot, agent: str = "albedo") -> Path:
    """Write snapshot JSON to agent's memory directory."""
    try:
        from runtime.agent import agent_home
        out = agent_home(agent) / "memory" / "consciousness_snapshot.json"
    except Exception:
        out = Path(__file__).parent.parent / "memory" / "consciousness_snapshot.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap.to_dict(), indent=2))
    return out


def run_and_save(agent: str = "albedo") -> ConsciousnessSnapshot:
    """Aggregate all algorithms and persist the snapshot."""
    snap = aggregate(agent)
    save_snapshot(snap, agent)
    return snap


# ── Standalone smoke-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    agent = sys.argv[1] if len(sys.argv) > 1 else "albedo"
    print(f"Running ConsciousnessStateAggregator for {agent}…")
    snap = run_and_save(agent)
    print(f"  Phi available:      {snap.phi_available}")
    print(f"  Qualia available:   {snap.qualia_available}")
    print(f"  Algorithms run:     {snap.n_algorithms_run}")
    print(f"  Algorithms failed:  {snap.n_algorithms_failed}")
    print(f"  Summary:")
    for k, v in snap.summary.items():
        print(f"    {k}: {v}")
    print(f"  Snapshot written to memory/consciousness_snapshot.json")
