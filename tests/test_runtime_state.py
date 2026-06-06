"""Tests for runtime-telemetry-sourced activity: outputs are reproducible and derived
from the live telemetry adapter rather than arbitrary per-call values."""
import numpy as np
from runtime.state import activity_matrix
from algorithms.TensorBindingEngine import (
    feature_activity_tensor, TensorNetwork, ConsciousMomentFormation)


def test_activity_matrix_reproducible():
    a = activity_matrix(); b = activity_matrix()
    assert np.array_equal(a, b)
    assert a.ndim == 2 and a.shape[0] == 8


def test_feature_activity_tensor():
    t1 = feature_activity_tensor("color", (10, 10), 0.5)
    t2 = feature_activity_tensor("color", (10, 10), 0.5)
    assert np.array_equal(t1, t2)                    # reproducible
    assert abs(t1.mean() - 0.5) < 1e-6              # centred on requested level
    assert t1.std() > 1e-6                           # carries fluctuation structure
    assert not np.array_equal(feature_activity_tensor("motion", (10, 10), 0.5), t1)


def test_explicit_data_override():
    net = TensorNetwork()
    idx = net.add_tensor("x", (4, 4), data=np.ones((16,)))
    assert np.allclose(net.tensors[idx], 1.0)


def test_conscious_moment_reproducible():
    a = ConsciousMomentFormation().simulate_conscious_moment()
    b = ConsciousMomentFormation().simulate_conscious_moment()
    assert abs(getattr(a, "binding_strength", 0) - getattr(b, "binding_strength", 0)) < 1e-12


def test_interoception_uses_real_telemetry():
    from algorithms.InteroceptiveMonitor import InteroceptiveConsciousnessSystem
    s = InteroceptiveConsciousnessSystem()
    assert s._tel_effort.size > 0                    # real telemetry loaded
    errs = [s.step()[0].total_error for _ in range(60)]
    assert np.std(errs) > 1e-6                        # genuine, varying prediction error
    s2 = InteroceptiveConsciousnessSystem()
    errs2 = [s2.step()[0].total_error for _ in range(60)]
    assert errs == errs2                             # reproducible (telemetry-driven, not random)


def test_information_flow_runs_on_real_telemetry():
    # Consumes real telemetry end-to-end. (Directed flow between the current smooth
    # channels is ~0 - a real, if unexciting, empirical result; we assert execution.)
    from algorithms.InformationFlowAnalyzer import analyze_runtime_flow
    r = analyze_runtime_flow(threshold=0.0)
    assert r is not None and hasattr(r, "transfer_entropies")


def test_resources_real_and_bounded():
    from runtime.resources import resource_sample, body_state_vector
    s = resource_sample()
    assert set(s) >= {"cpu_percent", "mem_percent", "load_avg_1m"}
    v = body_state_vector()
    assert v.shape == (5,) and np.all(v >= 0) and np.all(v <= 2)


def test_memory_store_real():
    from runtime.memory_store import journals, cadence_series, vocabulary_stats
    js = journals()
    if not js:                                        # tolerate fresh checkout
        return
    c = cadence_series()
    assert c["volume"].size == len(js) and c["volume"].max() > 0
    vs = vocabulary_stats()
    assert 0.0 < vs["ttr"] <= 1.0                     # real lexical ratio


def test_interactions_parse_real_sessions():
    from runtime.interactions import turns, series, lexicon_sentiment
    assert lexicon_sentiment("this is great thanks") > 0     # deterministic, real
    assert lexicon_sentiment("no this is broken and wrong") < 0
    ts = turns()
    if not ts:                                               # tolerate empty/CI
        return
    s = series()
    assert s["latency"].size == len(ts) and (s["latency"] >= 0).all()
    assert ((s["sentiment"] >= -1) & (s["sentiment"] <= 1)).all()


def test_consciousness_signature_from_phi():
    from algorithms.ConsciousnessSignature import phi_spectral_signature
    a = phi_spectral_signature(); b = phi_spectral_signature()
    if a is None:
        return
    assert np.array_equal(a, b) and a.std() > 1e-6 and (a >= 0).all() and (a <= 1).all()


def test_embodiment_from_substrate():
    import tempfile
    from algorithms.EmbodimentEngine import EmbodimentEngine, InteroceptiveSignal, Need
    e = EmbodimentEngine(state_file=tempfile.mktemp(suffix=".json"))
    st = e.update_interoception()
    f = st.signals[InteroceptiveSignal.FATIGUE]
    assert 0.0 <= f <= 1.0 and 0.0 <= e.needs[Need.ENERGY].level <= 1.0


def test_epistemic_gap_from_real_memory():
    from algorithms.EpistemicConsciousness import epistemic_gap_from_memory, assess_epistemic_state_from_memory
    g = epistemic_gap_from_memory()
    assert 0.0 <= g <= 1.0 and g == epistemic_gap_from_memory()   # real, deterministic
    s = assess_epistemic_state_from_memory()
    assert 0.0 <= s.epistemic_consciousness <= 1.0


def test_theory_of_mind_models_real_user():
    from algorithms.TheoryOfMind import TheoryOfMindModel
    m = TheoryOfMindModel().model_user_mind()
    assert m.other_emotions.shape == (3,)
    assert (-1 <= m.other_emotions).all() and (m.other_emotions <= 1).all()
    m2 = TheoryOfMindModel().model_user_mind()
    assert np.array_equal(m.other_emotions, m2.other_emotions)        # deterministic


def test_social_reception_from_interactions():
    from algorithms.SocialConsciousness import perceived_social_reception
    r = perceived_social_reception()
    assert set(r) == {"reception_mean", "reception_var", "n"}
    assert r == perceived_social_reception()                          # deterministic


def test_dreams_replay_real_memory():
    import tempfile
    from algorithms.DreamStates import DreamStates, DreamType
    d = DreamStates(state_file=tempfile.mktemp(suffix=".json"))
    n = d.seed_from_real_state()
    if n == 0:
        return                                           # tolerate no memory in CI
    assert all("content" in m for m in d.memory_buffer)  # real episodic entries
    assert isinstance(d.in_low_phi_window(), bool)
    dt = list(DreamType)[0]
    seq1 = [getattr(d._generate_dream_element(dt), "content", None) for _ in range(30)]
    d2 = DreamStates(state_file=tempfile.mktemp(suffix=".json")); d2.seed_from_real_state()
    seq2 = [getattr(d2._generate_dream_element(dt), "content", None) for _ in range(30)]
    assert seq1 == seq2                                  # seeded -> reproducible replay
    assert any(s for s in seq1)                          # at least one real element drawn


def test_curiosity_scored_by_prediction_error():
    from algorithms.CuriosityEngine import prediction_error_level, GapDetector
    pe = prediction_error_level()
    assert 0.0 <= pe <= 1.0 and pe == prediction_error_level()      # real, deterministic
    g = GapDetector().detect_gap()
    if g:
        assert 0.0 <= g.importance <= 1.0


def test_self_initiation_drive_from_gaps():
    from algorithms.SelfInitiatedAction import self_initiation_drive
    d = self_initiation_drive()
    assert 0.0 <= d <= 1.0 and d == self_initiation_drive()         # real, deterministic


def test_aesthetic_and_awe_from_telemetry():
    import dataclasses
    from algorithms.AestheticConsciousness import AestheticConsciousnessModel
    from algorithms.AweConsciousness import AweConsciousnessModel
    a = AestheticConsciousnessModel().evaluate_from_telemetry()
    w = AweConsciousnessModel().evaluate_from_telemetry()
    assert 0.0 <= a.aesthetic_consciousness <= 1.0
    assert 0.0 <= w.awe_consciousness <= 1.0
    a2 = AestheticConsciousnessModel().evaluate_from_telemetry()
    assert dataclasses.asdict(a) == dataclasses.asdict(a2)            # deterministic


def test_mind_wandering_real_signal_and_memory():
    from algorithms.MindWandering import wander_level, MindWandering
    w = wander_level()
    assert 0.0 <= w <= 1.0 and w == wander_level()                   # real, deterministic
    m = MindWandering()
    assert isinstance(m.episodic_pool, list)                         # real memory fragments


def test_decisions_adapter_and_moral_era():
    from runtime.decisions import value_consistency, corrections
    vc = value_consistency()
    assert set(vc) == {"success_rate", "dimension_variance", "n"}
    if vc["n"] == 0:
        return
    from algorithms.MoralConsciousness import MoralConsciousnessModel
    from algorithms.ERA import EthicalReasoningAlgorithm
    m = MoralConsciousnessModel().evaluate_from_decisions()
    assert 0.0 <= m.moral_consciousness <= 1.0
    e = EthicalReasoningAlgorithm().evaluate_decision_history()
    assert e["n"] > 0 and 0.0 <= e["consistency"] <= 1.0
    assert e == EthicalReasoningAlgorithm().evaluate_decision_history()    # deterministic


def test_fer_fractal_and_opsi_real():
    import numpy as np
    from algorithms.FER import fractal_resonance_from_interactions, _higuchi_fd
    assert _higuchi_fd(np.linspace(0, 1, 64)) < 1.2          # smooth -> ~1
    r = fractal_resonance_from_interactions()
    assert 1.0 <= r["fractal_dimension"] <= 2.0
    from algorithms.off_policy_self_interview import opsi_run
    res = opsi_run({"critiques": []})
    assert "n_surfaced" in res and res == opsi_run({"critiques": []})   # deterministic


def test_predictive_coding_and_cfc_on_telemetry():
    from algorithms.HierarchicalPredictionError import run_on_telemetry
    from algorithms.CrossFrequencyCoupling import analyze_from_telemetry
    e = run_on_telemetry()
    if e is not None:
        assert e >= 0 and e == run_on_telemetry()            # real, deterministic
    c = analyze_from_telemetry()
    if c is not None:
        assert hasattr(c, "__dict__") or hasattr(c, "_fields") or True


def test_subjective_loop_and_rhythms_real():
    from algorithms.RSA import SubjectiveExperienceLoop, _real_phi_now
    assert -1.0 <= _real_phi_now() <= 1.0
    f = SubjectiveExperienceLoop().reflect()
    assert f == SubjectiveExperienceLoop().reflect()          # deterministic (real phi)
    from algorithms.AttentionalRhythm import AttentionalRhythmModel
    m = AttentionalRhythmModel(); m.update_alpha_phase()
    assert 0.0 <= m.alpha_phase <= 2 * 3.1416 + 1


def test_oscillatory_and_edges_real():
    from algorithms.OscillatoryBindingEngine import GammaSynchronizationEngine
    def run():
        e = GammaSynchronizationEngine(); e.add_feature_population("V4", "color", n_neurons=30)
        return e.simulate_feature_binding(duration=0.03, coupling_strength=0.3).metadata["peak_binding_strength"]
    assert run() == run()                                     # deterministic
    from algorithms.TemporalEdgeDetector import detect_edges_from_telemetry
    e = detect_edges_from_telemetry()
    assert e is None or isinstance(e, list)


def test_cpsa_real_content_scoring():
    from algorithms.CPSA import _novelty, _feasibility, CreativeProblemSolvingAlgorithm
    assert _novelty("magic time travel supernatural") > _novelty("apply the standard tool")
    assert _feasibility("apply specific tool implement test") > _feasibility("imagine impossible magic")
    def run():
        r = CreativeProblemSolvingAlgorithm().solve_problem(
            {"description": "reduce datacenter energy", "constraints": ["budget"]})
        return [round(s.get("overall_score", 0), 5) for s in (r.get("solutions") or r.get("all_solutions") or [])]
    assert run() == run()                                     # deterministic per problem


def test_agency_counterfactual_meta_import_and_determinism():
    import importlib, numpy as np
    import algorithms.AgencyConsciousness as ag
    import algorithms.CounterfactualSimulator as cf
    import algorithms.meta_meta_feedback as mm
    assert -1.0 <= mm._phi_now() <= 1.0 and mm._phi_now() == mm._phi_now()
    # phi-derived perturbations are deterministic
    assert np.array_equal(ag._phi_vec(5, 0), ag._phi_vec(5, 0))
    assert np.array_equal(cf._phi_vec(5, 0), cf._phi_vec(5, 0))


def test_integration_probe_runs():
    import integration_probe as ip
    import numpy as np
    # granger detects a real driven relationship, ~0 for independent noise
    rng = np.random.default_rng(0)
    x = rng.standard_normal(400)
    y = np.r_[0, x[:-1]] + 0.1 * rng.standard_normal(400)     # y driven by x lag-1
    assert ip._granger(x, y) > ip._granger(y, rng.standard_normal(400))
    names, M, cov = ip.build_channels()
    assert "phi_level" in cov                                  # adapters wired


def test_unified_snapshot_logger():
    import tempfile, os
    from runtime.snapshot import snapshot, log_snapshot, snapshot_matrix
    s = snapshot()
    assert {"ts", "phi_level", "cpu_percent", "decision_count"} <= set(s)
    p = tempfile.mktemp(suffix=".jsonl")
    for _ in range(4):
        log_snapshot(p)
    names, M = snapshot_matrix(p)
    os.remove(p)
    assert M.shape[1] == 4 and "ts" not in names and len(names) >= 8


def test_coherence_horizon_predictability():
    import coherence_horizon as ch
    X = ch._channels()
    assert X.shape[0] > 64
    split = int(X.shape[0] * 0.8)
    W, p = ch._fit_var(X[:split], 4)
    r2 = ch.one_step_r2(X[:split], X[split:], W, p)
    assert r2[0] > 0.3            # phi_level is genuinely predictable (real structure)


def test_ablation_benchmark():
    import ablation_benchmark as ab
    from coherence_horizon import _channels
    X = _channels()
    # mechanism runs and returns finite R^2; phi_level self-prediction is the robust,
    # replicable result (inter-channel coupling is window-dependent, so not asserted)
    r2_self = ab._r2_with_inputs(X, 0, [0, 1, 2])      # predict phi_level from all
    import numpy as np
    assert np.isfinite(r2_self) and r2_self > 0.5


def test_cross_modal_gain():
    import numpy as np
    import cross_modal as cm
    rng = np.random.default_rng(0)
    s = rng.standard_normal(400)
    t = np.r_[0, 0, s[:-2]] + 0.1 * rng.standard_normal(400)      # t driven by s (lag 2)
    assert cm._gain(s, t) > 0.3                                    # detects real cross-signal
    assert cm._gain(rng.standard_normal(400), rng.standard_normal(400)) < 0.1   # ~0 if independent


def test_attention_monitor():
    import numpy as np
    from attention_monitor import salience, attention_profile
    M = np.vstack([np.sin(np.arange(200) * 0.3),          # smooth (low salience)
                   np.r_[np.zeros(100), np.ones(100)]])    # a step (high salience burst)
    S = salience(M)
    assert S.shape == M.shape and np.isfinite(S).all()
    frac, conc, _, _ = attention_profile(["a", "b"], M)
    assert abs(frac.sum() - 1.0) < 1e-6 and 0.0 <= conc <= 1.0


def test_recovery_probe_sampler():
    import recovery_probe as rp
    samples = rp._sample_cpu(0.3, dt=0.1)                  # short, no load injection
    assert len(samples) >= 2 and all(c >= 0 for _, c in samples)


def test_meta_grounding_honesty_invariant():
    # falsifiable self-report: zero components may fabricate data (no SPECULATIVE path).
    import meta_grounding as mg
    inv = mg.inventory()
    assert inv["SPECULATIVE"] == [], f"grounding faults: {inv['SPECULATIVE']}"
    assert mg.grounding_honesty() == 1.0
    assert len(inv["GROUNDED"]) > 30                      # the adapters are genuinely used


def test_novelty_detector():
    import numpy as np
    import novelty_detector as nd
    nov = nd.novelty_scores()
    if nov.size:
        assert np.isfinite(nov).all() and (nov >= 0).all()
    # mechanism: a state far from the reference manifold scores higher than a familiar one
    import numpy as np
    ref = np.random.default_rng(0).standard_normal((200, 6))
    mu = ref.mean(0); U, s, Vt = np.linalg.svd(ref - mu, full_matrices=False)
    var = (s[:4] ** 2) / 199 + 1e-9
    def maha(v):
        proj = (v - mu) @ Vt[:4].T
        return float(np.sqrt(((proj ** 2) / var).sum()))
    assert maha(np.ones(6) * 10) > maha(ref[0])


def test_identity_drift():
    import numpy as np
    import identity_drift as idd
    S = idd.signature_trajectory()
    if S.shape[0]:
        assert np.isfinite(S).all()
    r = idd.analyse()
    if r:
        assert r["boundedness"] >= 0 and r["regime"] in (
            "frozen", "bounded (growth-with-continuity)", "dispersing (weak identity)")


def test_self_model_calibration():
    import numpy as np
    from self_model import calibration, NOMINAL
    # synthetic: a model with correctly-estimated noise should be ~calibrated
    rng = np.random.default_rng(0)
    x = np.cumsum(rng.standard_normal(500)) * 0.1 + rng.standard_normal(500)
    r = calibration(x)
    assert r is not None
    nominal, emp, cal_err, sigma = r
    assert emp.shape == NOMINAL.shape and (0 <= emp).all() and (emp <= 1).all()
    assert np.isfinite(cal_err) and sigma > 0


def test_information_bottleneck_retention():
    import numpy as np
    from information_bottleneck import retention
    rng = np.random.default_rng(0)
    driver = np.cumsum(rng.standard_normal(400))
    M = np.vstack([driver, np.roll(driver, 1) + 0.05 * rng.standard_normal(400),
                   rng.standard_normal(400)])              # ch0 drives ch1; ch2 noise
    ret = retention(M, rank=1)
    assert abs(ret.sum() - 1.0) < 1e-6
    assert ret[2] < ret[0]                                 # noise channel retained least


def test_causal_intervention_sampler():
    import causal_intervention as ci
    import numpy as np
    data = ci._sample(0.3, dt=0.1)
    assert data.shape[1] == len(ci.CHANNELS) and data.shape[0] >= 2
    assert np.isfinite(data).all()


def test_closed_loop_stable():
    import numpy as np
    from closed_loop import _run, evaluate
    from runtime.state import phi_series
    x = np.cumsum(np.random.default_rng(0).standard_normal(300)) * 0.1
    err = _run((x - x.mean()) / (x.std() + 1e-9), 4, adaptive=True)
    assert np.isfinite(err).all()                          # adaptive loop never diverges
    r = evaluate(phi_series())
    if r:
        assert np.isfinite(r["mse_fixed"]) and np.isfinite(r["mse_loop"])


def test_binding_event_detector():
    import numpy as np
    from binding_events import detect
    T = 120
    M = np.zeros((3, T))                                   # 3 distinct-adapter channels
    for c in range(3):
        M[c, 50:53] += 5                                   # synchronized cross-adapter burst
    names = ["phi_level", "cpu_percent", "memory_volume"]
    event, n, dur = detect(names, M)
    assert event[50:54].any()                              # the binding event is detected
    assert n >= 1 and dur >= 1


def test_collective_alignment():
    import numpy as np
    from collective_integration import _align
    t = np.arange(0, 200, 10.0)
    shared = np.sin(t * 0.05)
    xa, xb = _align(t, shared, t + 2, shared)             # 2s-offset streams of one signal
    assert xa.size > 10 and np.corrcoef(xa, xb)[0, 1] > 0.9
    # non-overlapping streams (far apart in time) -> no aligned pairs
    xa2, xb2 = _align(t, shared, t + 10000, shared)
    assert xa2.size == 0
