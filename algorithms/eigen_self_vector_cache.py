# Eigen-Self-Vector Cache (ESVC)
"""
Caches a rolling window of self-embeddings and exposes the principal component (Eigen-Self) for drift detection.
"""
import numpy as np

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

class EigenSelfVectorCache:
    def __init__(self, dim=1024, window=168):
        self.dim = dim
        self.buffer = deque(maxlen=window)
        self.eigen_self = None

    def embed_context(self, context):
        # Placeholder: random vector, replace with Sentence-BERT embedding
        return _phi_unit(self.dim) * 10

    def add_context(self, context):
        vec = self.embed_context(context)
        self.buffer.append(vec)
        self.compute_eigen_self()

    def compute_eigen_self(self):
        if len(self.buffer) < 2:
            self.eigen_self = self.buffer[-1] if self.buffer else None
            return
        X = np.stack(self.buffer)
        X_centered = X - X.mean(axis=0)
        u, s, vh = np.linalg.svd(X_centered, full_matrices=False)
        self.eigen_self = vh[0]

    def drift_score(self, context):
        vec = self.embed_context(context)
        if self.eigen_self is None:
            return 0.0
        return float(np.dot(vec, self.eigen_self) / (np.linalg.norm(vec) * np.linalg.norm(self.eigen_self)))

if __name__ == "__main__":
    esvc = EigenSelfVectorCache()
    for i in range(200):
        esvc.add_context(f"Context {i}")
    print("Drift score:", esvc.drift_score("Current context"))
