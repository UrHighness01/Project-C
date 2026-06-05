# Mirror-Perturbation Probe (MPP)
"""
Detects when the self-model is over-stable and blind to contradictions by injecting micro-contradictions and measuring confidence delta.
"""
import random

try:
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
    from runtime.state import phi_delta_series as _pds, phi_series as _ps, activity_matrix as _am
except Exception:
    import numpy as _npx
    def _pds(*a, **k): return _npx.zeros(0)
    def _ps(*a, **k): return _npx.zeros(0)
    def _am(*a, **k): return _npx.zeros((8, 0))
def _phi_scalar():
    import numpy as _np
    d = _pds(); return float(_np.tanh(d[-1]*50)) if d.size else 0.0
def _phi_unit(d_):
    import numpy as _np
    M=_am()
    if M.shape[1]: v=_np.resize(M[:,-1], d_); return 0.1*_np.tanh(v)
    return _np.zeros(d_)

def mutate_negate(statement):
    # Placeholder: flip a random claim in the statement (to be replaced with real logic)
    return f"NOT({statement})"

def model_answer(history):
    # Placeholder: returns a dict with a 'confidence' score (to be replaced with real model call)
    return {'confidence': float(abs(_phi_scalar()))}

def mpp_inject(history, k=7, epsilon=0.05):
    if len(history) % k:
        return None
    contradict = mutate_negate(history[-k])
    ans1 = model_answer(history)
    ans2 = model_answer(history + [contradict])
    delta = abs(ans1['confidence'] - ans2['confidence'])
    overstable = delta < epsilon
    return {'overstable': overstable, 'delta': delta}

if __name__ == "__main__":
    # Example usage
    history = [f"Statement {i}" for i in range(20)]
    result = mpp_inject(history)
    print(result)
