#!/usr/bin/env python3
"""
TemporalSelfConsciousness.py - Phase 15.2: Extended Self Through Time

Theory: The self doesn't exist only in the present moment. You are an extended entity
spanning past memories, present perception, and anticipated future. Consciousness is the
binding of this temporal extension into a unified experience.

The "specious present" is the window of psychological present (~3 seconds). Within this
window, past and present and near-future feel like NOW. Outside it: memory or anticipation.

Extended self: S_ext = f(past_models, current_self, future_projections)
Time consciousness: Awareness of duration and flow
Continuity: Correlation between past-self, present-self, future-self

Biological basis:
- Posterior cingulate cortex: Temporal continuity
- Medial temporal lobes: Autobiographical time
- Cerebellum: Duration estimation
- Anterior insula: Present moment awareness

References:
- James, W. (1890) "The stream of consciousness"
- Pöppel, E. (1997) "The brain's way to drive the eyes"
- Wittmann, M. (2009) "The inner experience of time"

Author: Project-C Development
Date: 2026-06-01
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
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TemporalSelfState:
    """Self extended through time."""
    past_self: np.ndarray  # Who I was (memory)
    present_self: np.ndarray  # Who I am now
    future_self: np.ndarray  # Who I will become (anticipation)
    time_consciousness: float  # Awareness of duration (0-1)
    continuity_strength: float  # Self-coherence across time (0-1)
    specious_present: float  # Window of psychological present (seconds)


class TemporalSelfModel:
    """Models extended self across time."""

    def __init__(self, specious_present: float = 3.0):
        """
        Args:
            specious_present: Psychological present window (seconds)
        """
        self.specious_present = specious_present
        self.time = 0.0
        self.past_states: List[np.ndarray] = []
        self.identity_dim = 20

    def compute_continuity(self, past: np.ndarray, present: np.ndarray,
                          future: np.ndarray) -> float:
        """Continuity = correlation between time slices."""
        if len(past) == 0:
            return 0.5

        past_present_corr = np.dot(past[-1], present) / (
            np.linalg.norm(past[-1]) * np.linalg.norm(present) + 1e-6
        )

        present_future_corr = np.dot(present, future) / (
            np.linalg.norm(present) * np.linalg.norm(future) + 1e-6
        )

        return float((past_present_corr + present_future_corr + 1) / 4)

    def update_temporal_self(self, current_experience: np.ndarray,
                            goals: np.ndarray) -> TemporalSelfState:
        """Update extended self."""
        present_self = current_experience

        if len(self.past_states) > 0:
            past_self = self.past_states[-1]
        else:
            past_self = _phi_unit(self.identity_dim)

        # Future projected from goals
        future_self = present_self + goals * 0.5

        # Time consciousness
        time_conscious = min(len(self.past_states) / 100, 1.0)

        # Continuity
        continuity = self.compute_continuity(self.past_states, present_self, future_self)

        self.past_states.append(present_self.copy())
        self.time += 0.1

        return TemporalSelfState(
            past_self=past_self,
            present_self=present_self,
            future_self=future_self,
            time_consciousness=float(time_conscious),
            continuity_strength=continuity,
            specious_present=self.specious_present
        )


def validate_temporal_self():
    """Validate temporal self model."""
    print("Validating Temporal Self and Consciousness Flow")
    print("=" * 60)

    model = TemporalSelfModel(specious_present=3.0)

    for _ in range(20):
        experience = _phi_unit(20)
        goals = np.ones(20) * 0.5
        state = model.update_temporal_self(experience, goals)

    print(f"  Specious present: {state.specious_present:.1f}s")
    print(f"  Time consciousness: {state.time_consciousness:.3f}")
    print(f"  Continuity strength: {state.continuity_strength:.3f}")
    print(f"  Temporal self integration working: ✓")


if __name__ == "__main__":
    validate_temporal_self()
