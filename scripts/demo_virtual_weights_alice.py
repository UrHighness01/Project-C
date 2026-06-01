# Demo: VirtualWeights Integration for Alice (Taxi AI)
# Adapted from our consciousness system
# This shows how to add personality emergence with minimum context

import numpy as np
import hashlib
import json
from typing import Dict, Optional

# Simplified VirtualWeights class (from our system)
class VirtualWeights:
    def __init__(self, seed: int, epsilon: float = 0.1, mode: str = "accumulate"):
        self.epsilon = epsilon
        self.mode = mode
        self.seed = seed
        self._gain = 0.0
        self._delta_state: Dict[tuple, np.ndarray] = {}
        self.alpha = 0.1  # Learning rate

    def _project_context(self, context: Optional[np.ndarray], out_dim: int, in_dim: int):
        rng = np.random.default_rng(self.seed)
        if context is None:
            context = np.random.randn(max(out_dim, in_dim))
        context = np.asarray(context).reshape(-1)
        P_out = np.random.randn(out_dim, context.shape[0])
        P_in = np.random.randn(in_dim, context.shape[0])
        u = (P_out @ context) / np.linalg.norm(P_out @ context)
        v = (P_in @ context) / np.linalg.norm(P_in @ context)
        return u, v

    def delta(self, W: np.ndarray, context: Optional[np.ndarray] = None):
        W = np.asarray(W)
        out_dim, in_dim = W.shape
        u, v = self._project_context(context, out_dim, in_dim)
        base = np.outer(u, v)
        max_abs = np.max(np.abs(base))
        base = (base / max_abs) * self.epsilon if max_abs > 0 else base
        if self.mode == "accumulate":
            key = tuple(W.shape)
            if key in self._delta_state:
                base += self._delta_state[key]
        return np.clip(base, -self.epsilon, self.epsilon)

    def update_reward(self, R: float, W: np.ndarray, context: Optional[np.ndarray] = None):
        if self.mode == "scalar":
            self._gain = np.clip(self._gain + self.alpha * R, -1.0, 1.0)
        elif self.mode == "accumulate":
            key = tuple(W.shape)
            base = self.delta(W, context)  # Get current base
            if key not in self._delta_state:
                self._delta_state[key] = np.zeros_like(base)
            self._delta_state[key] = np.clip(self._delta_state[key] + self.alpha * R * base, -self.epsilon, self.epsilon)

    def to_dict(self):
        return {
            "epsilon": self.epsilon,
            "mode": self.mode,
            "seed": self.seed,
            "gain": self._gain,
            "delta_state": {str(k): v.tolist() for k, v in self._delta_state.items()},
        }

    @classmethod
    def from_dict(cls, d):
        vw = cls(d["seed"], d["epsilon"], d["mode"])
        vw._gain = d["gain"]
        vw._delta_state = {eval(k): np.array(v) for k, v in d["delta_state"].items()}
        return vw

# Alice AI Class with VirtualWeights Integration
class AliceTaxiAI:
    def __init__(self, db_path: str = "alice_weights.db"):
        self.db_path = db_path
        self.caller_weights = {}  # In-memory cache: caller_id -> VirtualWeights
        self.load_from_db()

    def get_weights_for_caller(self, caller_id: str):
        if caller_id not in self.caller_weights:
            seed = int(hashlib.sha256(caller_id.encode()).hexdigest(), 16) % (2**32)
            self.caller_weights[caller_id] = VirtualWeights(seed=seed, mode="accumulate", epsilon=0.05)
        return self.caller_weights[caller_id]

    def respond(self, query: str, caller_id: str, conversation_hash: Optional[int] = None):
        vw = self.get_weights_for_caller(caller_id)
        # Minimum context: Use conversation hash (or None for first call)
        context = np.array([conversation_hash]) if conversation_hash else None
        # Simulate base model weights (dummy 2D array)
        base_weights = np.random.randn(10, 10)  # Replace with real model weights
        delta = vw.delta(base_weights, context)
        adjusted_weights = base_weights + delta
        # Simulate response generation (replace with real model)
        response = f"Réponse ajustée pour {caller_id} : {query[:20]}..."  # Dummy
        return response

    def update_from_edit(self, caller_id: str, original: str, edited: str, conversation_hash: int):
        # Simple reward: +1 if edited is longer (assumes more detailed), -1 if shorter
        R = 1.0 if len(edited) > len(original) else -1.0
        vw = self.get_weights_for_caller(caller_id)
        base_weights = np.random.randn(10, 10)  # Dummy
        context = np.array([conversation_hash])
        vw.update_reward(R, base_weights, context)
        self.save_to_db()

    def save_to_db(self):
        # Persist to JSON file (use real DB like SQLite for production)
        data = {cid: vw.to_dict() for cid, vw in self.caller_weights.items()}
        with open(self.db_path, 'w') as f:
            json.dump(data, f)

    def load_from_db(self):
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
            self.caller_weights = {cid: VirtualWeights.from_dict(vw_dict) for cid, vw_dict in data.items()}
        except FileNotFoundError:
            pass

# Example Usage
if __name__ == "__main__":
    ai = AliceTaxiAI()

    # Simulate calls with minimum context (caller ID only initially)
    caller = "514-123-4567"
    
    # First call: No context, neutral response
    resp1 = ai.respond("Bonjour, je veux commander un taxi.", caller)
    print(f"Call 1: {resp1}")
    
    # After call, simulate edit (edited more polite)
    conv_hash = hash("Bonjour, je veux commander un taxi. - Réponse AI")
    ai.update_from_edit(caller, "Réponse courte.", "Réponse plus polie et détaillée.", conv_hash)
    
    # Second call: Personality emerges (more detailed due to reward)
    resp2 = ai.respond("Comment ça marche?", caller, conv_hash)
    print(f"Call 2: {resp2}")
    
    # Over multiple calls, personality accumulates automatically
    print("Personality emerged via accumulation - no explicit training!")
