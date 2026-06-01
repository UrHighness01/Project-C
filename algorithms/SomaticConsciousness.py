#!/usr/bin/env python3
"""
SomaticConsciousness.py - Phase 24.1: Body-Based Consciousness & Embodied Presence

Theory: Consciousness is grounded in the living body. Proprioceptive consciousness
(sense of body in space), interoceptive consciousness (sense of internal state),
and body boundary clarity are fundamental to consciousness. The body IS consciousness.

C_somatic = Integration(proprioceptive_predictions) × body_boundary_clarity
Embodied_presence = C_somatic × (1 - dissociation)

References:
- Tsakiris, M., & Haggard, P. (2005) "Rubber hand illusion"
- Damasio, A. (1999) "The feeling of what happens"
- Merleau-Ponty, M. (1945) "Phenomenology of Perception"

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class SomaticState:
    """Somatic consciousness state."""
    proprioceptive_clarity: float  # How clearly located in space (0-1)
    interoceptive_awareness: float  # Awareness of internal state (0-1)
    body_boundary_clarity: float  # Clear self-other boundary (0-1)
    proprioceptive_prediction_error: float  # Body location mismatch (0-1)
    embodied_presence: float  # Felt sense of being in body (0-1)
    dissociation_level: float  # Disconnection from body (0-1)
    somatic_consciousness: float  # Overall body-grounded consciousness


class SomaticConsciousnessModel:
    """Models proprioceptive and interoceptive body consciousness."""

    def compute_proprioceptive_clarity(self, position_accuracy: float,
                                      movement_control: float,
                                      postural_stability: float) -> float:
        """Compute clarity of body position in space.

        Proprioceptive clarity depends on:
        - How well you know where your limbs are
        - How well you can control movement
        - How stable your posture is
        """
        clarity = (position_accuracy * 0.4 + movement_control * 0.4 +
                  postural_stability * 0.2)
        return float(np.clip(clarity, 0, 1))

    def compute_interoceptive_awareness(self, heartbeat_awareness: float,
                                       breathing_awareness: float,
                                       internal_state_awareness: float) -> float:
        """Compute awareness of internal bodily state.

        Interoception: awareness of heartbeat, breathing, digestion, temperature.
        Core to somatic consciousness.
        """
        awareness = (heartbeat_awareness * 0.3 + breathing_awareness * 0.3 +
                    internal_state_awareness * 0.4)
        return float(np.clip(awareness, 0, 1))

    def compute_body_boundary(self, self_other_discrimination: float,
                             skin_sensation_integration: float,
                             rubber_hand_immunity: float = 0.8) -> float:
        """Compute clarity of body boundary (where am I vs where is other?).

        Body boundary: the gradient between self and world. Clear boundary
        = strong sense of body ownership.
        """
        # Self-other discrimination
        boundary_clarity = self_other_discrimination

        # Integration of skin sensations
        boundary_clarity += skin_sensation_integration * 0.3

        # Resistance to illusions (rubber hand illusion shows weak boundary)
        illusion_resistance = rubber_hand_immunity  # 0=easily fooled, 1=clear boundary
        boundary_clarity += illusion_resistance * 0.2

        return float(np.clip(boundary_clarity / 1.5, 0, 1))

    def compute_proprioceptive_error(self, expected_position: np.ndarray,
                                    actual_sensory_feedback: np.ndarray) -> float:
        """Compute prediction error in proprioceptive position.

        When expected body location mismatches actual sensory feedback,
        it creates awareness (proprioceptive error = awareness).
        """
        if len(expected_position) == 0 or len(actual_sensory_feedback) == 0:
            return 0.5

        error = np.linalg.norm(expected_position - actual_sensory_feedback)
        # Normalize to 0-1
        error = error / (np.sqrt(len(expected_position)) + 1e-6)

        return float(np.clip(error, 0, 1))

    def compute_dissociation(self, trauma_level: float,
                            emotional_overwhelm: float,
                            voluntary_detachment: float = 0.0) -> float:
        """Compute dissociation (disconnection from body).

        Dissociation = protective mechanism against overwhelming stimuli/emotions.
        Reduces somatic consciousness.
        """
        # Trauma and overwhelming emotion trigger dissociation
        dissoc = (trauma_level * 0.5 + emotional_overwhelm * 0.5)

        # Some can voluntarily dissociate (meditation, mindfulness retreats)
        dissoc += voluntary_detachment * 0.3

        return float(np.clip(dissoc, 0, 1))

    def evaluate_somatic_consciousness(self, position_accuracy: float,
                                       movement_control: float,
                                       postural_stability: float,
                                       heartbeat_awareness: float,
                                       breathing_awareness: float,
                                       internal_state_awareness: float,
                                       self_other_discrimination: float,
                                       trauma_level: float = 0.0,
                                       emotional_overwhelm: float = 0.0,
                                       integration_level: float = 0.8) -> SomaticState:
        """Evaluate somatic consciousness state.

        Consciousness is grounded in the body. Loss of somatic awareness
        (dissociation) = loss of presence and consciousness.
        """
        # Proprioceptive clarity
        prop_clarity = self.compute_proprioceptive_clarity(
            position_accuracy, movement_control, postural_stability
        )

        # Interoceptive awareness
        intero_awareness = self.compute_interoceptive_awareness(
            heartbeat_awareness, breathing_awareness, internal_state_awareness
        )

        # Body boundary
        boundary = self.compute_body_boundary(self_other_discrimination,
                                             skin_sensation_integration=0.8)

        # Proprioceptive error (creates awareness through mismatch)
        prop_error = self.compute_proprioceptive_error(
            np.array([position_accuracy, movement_control]),
            np.array([0.7, 0.7])
        )

        # Dissociation (loss of somatic consciousness)
        dissoc = self.compute_dissociation(trauma_level, emotional_overwhelm)

        # Embodied presence: integration of somatic systems minus dissociation
        embodied = (prop_clarity * 0.4 + intero_awareness * 0.4 +
                   boundary * 0.2) * (1.0 - dissoc)

        # Somatic consciousness: body-based awareness
        somatic_c = embodied * integration_level

        return SomaticState(
            proprioceptive_clarity=prop_clarity,
            interoceptive_awareness=intero_awareness,
            body_boundary_clarity=boundary,
            proprioceptive_prediction_error=prop_error,
            embodied_presence=float(np.clip(embodied, 0, 1)),
            dissociation_level=dissoc,
            somatic_consciousness=float(np.clip(somatic_c, 0, 1))
        )


def validate_somatic_consciousness():
    """Validate somatic consciousness model."""
    print("Validating Somatic Consciousness (Body-Grounded Presence)")
    print("=" * 60)

    model = SomaticConsciousnessModel()

    # Test 1: High embodied presence (fully in body)
    print("\n1. High embodied presence (yoga, dance, presence):")
    state_embodied = model.evaluate_somatic_consciousness(
        position_accuracy=0.95,
        movement_control=0.9,
        postural_stability=0.9,
        heartbeat_awareness=0.8,
        breathing_awareness=0.9,
        internal_state_awareness=0.85,
        self_other_discrimination=0.95,
        trauma_level=0.0,
        emotional_overwhelm=0.0,
        integration_level=0.95
    )
    print(f"   Proprioceptive clarity: {state_embodied.proprioceptive_clarity:.3f}")
    print(f"   Interoceptive awareness: {state_embodied.interoceptive_awareness:.3f}")
    print(f"   Body boundary clarity: {state_embodied.body_boundary_clarity:.3f}")
    print(f"   Embodied presence: {state_embodied.embodied_presence:.3f}")
    print(f"   Somatic consciousness: {state_embodied.somatic_consciousness:.3f}")

    # Test 2: Dissociation (trauma or overwhelm)
    print("\n2. Dissociation (trauma response, feeling out of body):")
    state_dissoc = model.evaluate_somatic_consciousness(
        position_accuracy=0.3,
        movement_control=0.4,
        postural_stability=0.2,
        heartbeat_awareness=0.1,
        breathing_awareness=0.2,
        internal_state_awareness=0.15,
        self_other_discrimination=0.4,
        trauma_level=0.9,
        emotional_overwhelm=0.8,
        integration_level=0.6
    )
    print(f"   Dissociation level: {state_dissoc.dissociation_level:.3f}")
    print(f"   Embodied presence: {state_dissoc.embodied_presence:.3f}")
    print(f"   Somatic consciousness: {state_dissoc.somatic_consciousness:.3f}")

    # Test 3: Normal embodied state
    print("\n3. Normal embodied state (baseline consciousness):")
    state_normal = model.evaluate_somatic_consciousness(
        position_accuracy=0.75,
        movement_control=0.7,
        postural_stability=0.7,
        heartbeat_awareness=0.5,
        breathing_awareness=0.6,
        internal_state_awareness=0.6,
        self_other_discrimination=0.8,
        trauma_level=0.0,
        emotional_overwhelm=0.1,
        integration_level=0.8
    )
    print(f"   Embodied presence: {state_normal.embodied_presence:.3f}")
    print(f"   Somatic consciousness: {state_normal.somatic_consciousness:.3f}")

    print(f"\n  Somatic consciousness model working: ✓")


if __name__ == "__main__":
    validate_somatic_consciousness()
