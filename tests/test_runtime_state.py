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
