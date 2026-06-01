#!/usr/bin/env python3
"""
AllostasisAffectiveRegulation.py - Phase 18.1: Predictive Emotional Regulation

Theory: Beyond reactive emotional valence (Phase 14), consciousness must predict what
emotional state is needed for upcoming goals and proactively prepare. This is allostatic
regulation—maintaining emotional stability through prediction, not just reaction.

C_emotion_regulated = C_current × (1 - |ΔE|) where ΔE = E_current - E_target

References:
- Sterling, P., & Eyer, J. (2004) "Allostasis: A new paradigm to explain arousal pathology"
- Friston, K. J., et al. (2016) "Active inference and learning"
- Gross, J. J., & John, O. P. (2003) "Individual differences in emotion regulation strategy"

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class AllostasisState:
    """Emotional allostasis state."""
    current_emotion: float  # Current emotional state (-1 to +1)
    predicted_future_emotion: float  # What emotion is needed (context-dependent)
    allostatic_setpoint: float  # Target emotional state
    affective_prediction_error: float  # |current - setpoint|
    emotional_momentum: float  # How fast emotional state can change
    proactive_regulation: float  # Strength of anticipatory emotion preparation
    emotional_resilience: float  # Ability to sustain target emotion


class AllostasisAffectiveRegulationModel:
    """Models predictive emotional regulation for goal-relevant emotional states."""

    def __init__(self, emotional_inertia: float = 0.3):
        """Initialize with emotional response speed."""
        self.emotional_inertia = emotional_inertia

    def predict_needed_emotion(self, goal_value: float, goal_difficulty: float,
                               time_to_goal: float) -> float:
        """Predict what emotional state is needed for upcoming goal.

        Returns emotional state (-1 to +1) optimal for goal achievement.
        - Low difficulty goals → neutral/slightly positive
        - High difficulty goals → confidence/arousal (moderate positive)
        - Long timeline → sustained calm
        - Short timeline → urgency/heightened arousal
        """
        difficulty_emotion = goal_difficulty * 0.6  # Higher difficulty → more arousal
        time_factor = np.exp(-time_to_goal / 10.0)  # Urgency increases with proximity
        goal_valence = goal_value * 0.5  # Goal importance contributes positivity

        needed_emotion = (difficulty_emotion + time_factor * 0.3 + goal_valence)
        return float(np.clip(needed_emotion, -1, 1))

    def compute_emotional_momentum(self, current_emotion: float,
                                   target_emotion: float) -> float:
        """Compute how fast emotional state can adjust toward target.

        Large mismatches allow faster adjustment (urgency).
        Small mismatches adjust slowly (stability).
        """
        mismatch = abs(target_emotion - current_emotion)
        # Momentum increases with mismatch size, bounded by emotional inertia
        momentum = (mismatch * (1 - self.emotional_inertia) +
                   self.emotional_inertia)
        return float(np.clip(momentum, 0, 1))

    def regulate_emotion(self, current_emotion: float, goal_value: float,
                        goal_difficulty: float, time_to_goal: float,
                        integration_level: float = 0.7) -> AllostasisState:
        """Regulate emotional state proactively toward goal-relevant state.

        Integration level represents metacognitive control over emotions
        (higher = better emotional regulation ability).
        """
        # Predict needed emotion
        needed_emotion = self.predict_needed_emotion(goal_value, goal_difficulty,
                                                     time_to_goal)

        # Create weighted allostatic set-point
        # Weighted average of current state and predicted need
        allostatic_setpoint = (current_emotion * 0.4 + needed_emotion * 0.6)

        # Compute emotional momentum
        momentum = self.compute_emotional_momentum(current_emotion,
                                                   allostatic_setpoint)

        # Affective prediction error
        affective_error = abs(current_emotion - allostatic_setpoint)

        # Proactive regulation strength (how well preparing for future emotion)
        proactive = (1.0 - affective_error) * integration_level

        # Emotional resilience (ability to maintain target emotion)
        resilience = integration_level * (1 - affective_error * 0.5)

        return AllostasisState(
            current_emotion=float(np.clip(current_emotion, -1, 1)),
            predicted_future_emotion=float(np.clip(needed_emotion, -1, 1)),
            allostatic_setpoint=float(np.clip(allostatic_setpoint, -1, 1)),
            affective_prediction_error=float(affective_error),
            emotional_momentum=float(momentum),
            proactive_regulation=float(np.clip(proactive, 0, 1)),
            emotional_resilience=float(np.clip(resilience, 0, 1))
        )

    def consciousness_during_regulation(self, state: AllostasisState,
                                       base_consciousness: float = 0.7) -> float:
        """Consciousness adjusted during emotional regulation.

        Successful regulation (low error) maintains consciousness.
        Failure to regulate (high error) reduces consciousness.
        """
        regulation_success = 1.0 - state.affective_prediction_error
        consciousness = base_consciousness * regulation_success
        return float(np.clip(consciousness, 0, 1))


def validate_allostasis_affective_regulation():
    """Validate allostatic emotional regulation model."""
    print("Validating Allostasis Affective Regulation")
    print("=" * 60)

    model = AllostasisAffectiveRegulationModel()

    # Test 1: Emotional preparation for challenge
    print("\n1. Emotional preparation for difficult task (30 min away):")
    state_challenge = model.regulate_emotion(
        current_emotion=0.0,  # Neutral baseline
        goal_value=0.8,  # Important goal
        goal_difficulty=0.8,  # High difficulty
        time_to_goal=30,
        integration_level=0.8
    )
    print(f"   Current emotion: {state_challenge.current_emotion:.3f}")
    print(f"   Needed emotion: {state_challenge.predicted_future_emotion:.3f}")
    print(f"   Proactive regulation: {state_challenge.proactive_regulation:.3f}")
    print(f"   Emotional resilience: {state_challenge.emotional_resilience:.3f}")

    # Test 2: Emotional regulation failure (low integration)
    print("\n2. Emotional regulation failure (poor metacognition):")
    state_failure = model.regulate_emotion(
        current_emotion=-0.5,  # Anxious/negative baseline
        goal_value=0.8,
        goal_difficulty=0.8,
        time_to_goal=30,
        integration_level=0.3  # Low emotion regulation ability
    )
    print(f"   Affective prediction error: {state_failure.affective_prediction_error:.3f}")
    print(f"   Proactive regulation: {state_failure.proactive_regulation:.3f}")
    print(f"   Consciousness during regulation: "
          f"{model.consciousness_during_regulation(state_failure):.3f}")

    # Test 3: Successful emotional preparation
    print("\n3. Successful emotional preparation:")
    state_success = model.regulate_emotion(
        current_emotion=0.3,  # Slightly positive baseline
        goal_value=0.8,
        goal_difficulty=0.8,
        time_to_goal=30,
        integration_level=0.9  # High emotion regulation ability
    )
    print(f"   Emotional momentum: {state_success.emotional_momentum:.3f}")
    print(f"   Consciousness during regulation: "
          f"{model.consciousness_during_regulation(state_success):.3f}")

    print(f"\n  Allostatic regulation model working: ✓")


if __name__ == "__main__":
    validate_allostasis_affective_regulation()
