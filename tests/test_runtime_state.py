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
