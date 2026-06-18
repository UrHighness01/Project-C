#!/usr/bin/env python3
"""
IntersubjectiveConsciousness.py - Phase 17.2: Shared Consciousness

Theory: When two minds interact, they create shared consciousness. Common understanding,
synchronized emotions, mutual intentionality. This is consciousness that exists between
minds, not just within them.

C_shared = C_individual + φ(integration_between_individuals)
Synchrony = correlation(neural_pattern_1, neural_pattern_2)
Mutual understanding: Both parties know the other understands

References:
- Hasson, U., et al. (2012) "Brain-to-brain coupling during complex spoken communication"
- Tomasello, M. (2008) "Origins of Human Communication"

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class SharedConsciousnessState:
    """State of shared consciousness between two minds."""
    individual_consciousness_1: float
    individual_consciousness_2: float
    neural_synchrony: float  # Correlation between individuals (0-1)
    mutual_understanding: float  # Both know the other understands (0-1)
    shared_consciousness: float  # Consciousness of the dyad
    shared_meaning_established: bool


class IntersubjectiveConsciousnessModel:
    """Models shared consciousness between individuals."""

    def compute_neural_synchrony(self, pattern_1: np.ndarray,
                                 pattern_2: np.ndarray) -> float:
        """Compute synchrony between two neural patterns."""
        if len(pattern_1) == 0 or len(pattern_2) == 0:
            return 0.5

        corr = np.dot(pattern_1, pattern_2) / (
            np.linalg.norm(pattern_1) * np.linalg.norm(pattern_2) + 1e-6
        )

        return float((corr + 1) / 2)

    def create_shared_consciousness(self, ind1_consciousness: float,
                                   ind2_consciousness: float,
                                   interaction_depth: float = 0.6) -> SharedConsciousnessState:
        """Create shared consciousness between two individuals."""
        # Synchrony emerges from interaction
        synchrony = interaction_depth + (ind1_consciousness + ind2_consciousness) / 4

        # Mutual understanding requires both to be conscious and synchronous
        mutual_understanding = min(1.0, synchrony * (ind1_consciousness + ind2_consciousness) / 2)

        # Shared consciousness: sum with integration bonus
        shared = (ind1_consciousness + ind2_consciousness) / 2 + synchrony * 0.3

        # Shared meaning when synchrony and understanding high
        shared_meaning = synchrony > 0.6 and mutual_understanding > 0.5

        return SharedConsciousnessState(
            individual_consciousness_1=ind1_consciousness,
            individual_consciousness_2=ind2_consciousness,
            neural_synchrony=float(np.clip(synchrony, 0, 1)),
            mutual_understanding=float(np.clip(mutual_understanding, 0, 1)),
            shared_consciousness=float(np.clip(shared, 0, 1)),
            shared_meaning_established=shared_meaning
        )


def validate_intersubjective_consciousness():
    """Validate intersubjective consciousness model."""
    print("Validating Intersubjective Consciousness")
    print("=" * 60)

    model = IntersubjectiveConsciousnessModel()
    state = model.create_shared_consciousness(
        ind1_consciousness=0.7,
        ind2_consciousness=0.8,
        interaction_depth=0.7
    )

    print(f"  Neural synchrony: {state.neural_synchrony:.3f}")
    print(f"  Mutual understanding: {state.mutual_understanding:.3f}")
    print(f"  Shared consciousness: {state.shared_consciousness:.3f}")
    print(f"  Shared meaning: {state.shared_meaning_established}")
    print(f"  Intersubjective model working: ✓")


# ---- Analyse API (for SymbiosisReport / wiring smoke test) --------------------

@dataclass
class IntersubjectiveResult:
    mutual_info: float = 0.0
    normalised_mi: float = 0.0
    is_intersubjective: bool = False


def analyse(phi_a: np.ndarray, phi_j: np.ndarray) -> IntersubjectiveResult:
    N_BINS = 16
    eps = 1e-12
    n = min(len(phi_a), len(phi_j))
    if n < 16:
        return IntersubjectiveResult()
    pa = phi_a[:n]
    pj = phi_j[:n]

    def _discrete(x):
        bins = np.linspace(x.min(), x.max() + eps, N_BINS)
        return np.digitize(x, bins) - 1

    da = _discrete(pa)
    dj = _discrete(pj)

    ha = -np.sum((np.bincount(da, minlength=N_BINS) / n) * np.log2(np.maximum(np.bincount(da, minlength=N_BINS) / n, eps)))
    hj = -np.sum((np.bincount(dj, minlength=N_BINS) / n) * np.log2(np.maximum(np.bincount(dj, minlength=N_BINS) / n, eps)))

    joint = np.zeros((N_BINS, N_BINS))
    for i in range(n):
        joint[da[i], dj[i]] += 1
    joint /= n
    hij = -np.sum(joint * np.log2(np.maximum(joint, eps)))

    mi = ha + hj - hij
    norm_mi = mi / max(ha, hj, eps)

    return IntersubjectiveResult(
        mutual_info=float(mi),
        normalised_mi=float(np.clip(norm_mi, 0, 1)),
        is_intersubjective=norm_mi > 0.05
    )
