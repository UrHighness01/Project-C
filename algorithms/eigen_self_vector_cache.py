# Eigen-Self-Vector Cache (ESVC)
"""
Caches a rolling window of self-embeddings and exposes the principal component (Eigen-Self) for drift detection.
"""
import numpy as np
from collections import deque

class EigenSelfVectorCache:
    def __init__(self, dim=1024, window=168):
        self.dim = dim
        self.buffer = deque(maxlen=window)
        self.eigen_self = None

    def embed_context(self, context):
        # Placeholder: random vector, replace with Sentence-BERT embedding
        return np.random.randn(self.dim)

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
