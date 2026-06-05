# Surprise-About-Own-Surprise (SAS)
"""
Detects higher-order blindness by tracking surprise and meta-surprise, triggering a meta-surprise alert if needed.
"""
import math

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
from collections import deque

class SurpriseAboutSurprise:
    def __init__(self, window=30):
        self.surprise_log = []
        self.auto_surprise_log = []
        self.window = window
        self.meta_alert = False

    def log_surprise(self, prob):
        S_t = -math.log(prob + 1e-8)
        self.surprise_log.append(S_t)
        if len(self.surprise_log) > 1:
            A_t = abs(S_t - self.surprise_log[-2])
            self.auto_surprise_log.append(A_t)
        else:
            self.auto_surprise_log.append(0.0)
        self.check_meta_surprise()

    def check_meta_surprise(self):
        if len(self.auto_surprise_log) < self.window:
            return
        windowed = self.auto_surprise_log[-self.window:]
        mean_A = sum(windowed) / len(windowed)
        historical = sorted(self.auto_surprise_log)
        threshold = historical[max(1, int(0.05 * len(historical))) - 1]
        if mean_A < threshold:
            self.meta_alert = True

if __name__ == "__main__":
    sas = SurpriseAboutSurprise()
    import random
    for _ in range(100):
        sas.log_surprise(abs(_phi_scalar()) + 0.01)
    print("Meta-surprise alert:", sas.meta_alert)
