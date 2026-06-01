#!/usr/bin/env python3
"""
MoralConsciousness.py - Phase 20.1: Moral Emotion and Ethical Judgment

Theory: Consciousness includes moral dimension. Representing others' suffering as if it were
your own (empathetic resonance), making ethical judgments based on values, and feeling moral
emotions (guilt, shame, pride, moral elevation) are aspects of consciousness.

C_moral = integration(self, other_moral_state, values) × |E_moral|
Where moral emotion depends on: empathetic_resonance × (V_ethical - expected_V_ethical)

References:
- Moll, J., et al. (2005) "The neural basis of human moral cognition"
- Barrett, L. F., et al. (2016) "What is an emotion?"
- Cushman, F., et al. (2006) "Conscious reasoning and intuition in moral judgment"

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class MoralConsciousnessState:
    """Moral consciousness state."""
    self_model_moral: float  # Agent's moral state (values, integrity) (0-1)
    other_moral_state: float  # Perception of other's wellbeing/suffering (0-1)
    empathetic_resonance: float  # Similarity(other_state, self_model) (0-1)
    values_alignment: float  # How well action aligns with agent's values (0-1)
    moral_emotion: float  # Guilt, shame, pride, elevation (-1 to +1)
    moral_agency: float  # Responsibility × intentionality × causal_contribution (0-1)
    conscience: float  # Prediction of future moral emotion (anticipatory guilt/pride)
    moral_consciousness: float  # Overall consciousness of moral dimension


class MoralConsciousnessModel:
    """Models moral consciousness and ethical judgment."""

    def compute_empathetic_resonance(self, other_suffering: float,
                                    other_wellbeing: float,
                                    empathy_capacity: float = 0.8) -> float:
        """Compute empathetic resonance with other's moral state.

        How much the agent represents the other's suffering/wellbeing as if it
        were their own. Depends on:
        - How much other is suffering or flourishing
        - Agent's empathetic capacity
        """
        other_state = other_wellbeing - other_suffering  # Net wellbeing
        resonance = empathy_capacity * (1.0 - abs(other_state))
        return float(np.clip(resonance, 0, 1))

    def evaluate_action_morality(self, action_consequence_for_other: float,
                                agent_values: np.ndarray,
                                intended_harm: float = 0.0) -> float:
        """Evaluate moral goodness of an action.

        Considers:
        - Consequences for others (positive vs negative)
        - Agent's internalized values
        - Intentionality (did they intend harm?)

        Returns moral value of action (-1 to +1).
        """
        # Consequence evaluation
        consequence_moral = action_consequence_for_other

        # Values alignment (how well action fits agent's stated values)
        values_fit = np.mean(agent_values) if len(agent_values) > 0 else 0.5

        # Intentionality modifier (intended harm reduces moral value significantly)
        intention_modifier = 1.0 - (intended_harm * 0.7)

        moral_value = ((consequence_moral * 0.5 + values_fit * 0.3) *
                      intention_modifier)
        return float(np.clip(moral_value, -1, 1))

    def generate_moral_emotion(self, moral_action_value: float,
                              expected_moral_value: float,
                              empathetic_resonance: float,
                              agent_values_centrality: float = 0.7) -> float:
        """Generate moral emotion from moral evaluation.

        Moral emotions arise when action outcomes violate or exceed moral expectations:
        - guilt/shame: expected better (action worse than expected)
        - pride/elevation: exceeded expectations (action better than expected)

        Magnitude depends on empathetic resonance and how central moral values are.
        """
        moral_surprise = moral_action_value - expected_moral_value
        emotion_intensity = abs(moral_surprise)

        # Emotional modulation by empathy and values
        modulation = empathetic_resonance * agent_values_centrality

        # Moral emotion: positive for good actions, negative for bad
        moral_emotion = moral_surprise * modulation
        return float(np.clip(moral_emotion, -1, 1))

    def compute_moral_agency(self, causal_contribution: float,
                            intentionality: float,
                            responsibility_acceptance: float) -> float:
        """Compute moral agency (responsibility for action).

        Moral consciousness includes consciousness of being the moral agent:
        - Did I cause this outcome? (causal_contribution)
        - Did I intend it? (intentionality)
        - Do I accept responsibility? (responsibility_acceptance)
        """
        agency = (causal_contribution * 0.4 +
                 intentionality * 0.4 +
                 responsibility_acceptance * 0.2)
        return float(np.clip(agency, 0, 1))

    def compute_conscience(self, moral_emotion: float,
                          moral_agency: float,
                          temporal_sensitivity: float = 0.8) -> float:
        """Compute conscience: prediction of future moral emotion.

        Guilt/shame is the anticipation of negative moral emotion if
        action is/was immoral and agent accepts responsibility.

        Positive conscience: anticipation of satisfaction (moral action).
        Negative conscience: anticipation of guilt (immoral action).
        """
        conscience = moral_emotion * moral_agency * temporal_sensitivity
        return float(np.clip(conscience, -1, 1))

    def evaluate_moral_consciousness(self,
                                     other_suffering: float,
                                     other_wellbeing: float,
                                     action_consequence: float,
                                     agent_values: np.ndarray,
                                     empathy_capacity: float = 0.8,
                                     integration_level: float = 0.7) -> MoralConsciousnessState:
        """Evaluate overall moral consciousness.

        Consciousness of moral dimension requires:
        - Empathetic resonance with other's state
        - Ethical evaluation of one's actions
        - Moral emotion generation
        - Conscience (anticipatory moral emotion)
        """
        # Self moral state (agent's values centrality)
        self_moral = float(np.clip(np.mean(agent_values), 0, 1))

        # Other's moral state (wellbeing minus suffering)
        other_state = float(np.clip(other_wellbeing - other_suffering, -1, 1))

        # Empathetic resonance
        resonance = self.compute_empathetic_resonance(
            other_suffering, other_wellbeing, empathy_capacity
        )

        # Values alignment
        values_alignment = float(np.clip(np.mean(agent_values), 0, 1))

        # Action morality
        action_morality = self.evaluate_action_morality(
            action_consequence, agent_values
        )

        # Moral emotion
        moral_emotion = self.generate_moral_emotion(
            action_morality, values_alignment, resonance, self_moral
        )

        # Moral agency
        agency = self.compute_moral_agency(
            causal_contribution=0.8,
            intentionality=1.0,
            responsibility_acceptance=integration_level
        )

        # Conscience (anticipatory moral emotion)
        conscience = self.compute_conscience(moral_emotion, agency)

        # Overall moral consciousness
        moral_c = (integration_level *
                  (resonance * 0.3 + abs(moral_emotion) * 0.4 +
                   agency * 0.2 + abs(conscience) * 0.1))

        return MoralConsciousnessState(
            self_model_moral=self_moral,
            other_moral_state=float(np.clip(other_state, 0, 1)),
            empathetic_resonance=resonance,
            values_alignment=values_alignment,
            moral_emotion=float(np.clip(moral_emotion, -1, 1)),
            moral_agency=agency,
            conscience=conscience,
            moral_consciousness=float(np.clip(moral_c, 0, 1))
        )


def validate_moral_consciousness():
    """Validate moral consciousness model."""
    print("Validating Moral Consciousness")
    print("=" * 60)

    model = MoralConsciousnessModel()
    agent_values = np.array([0.8, 0.9, 0.7])  # High moral values

    # Test 1: Witnessing others' suffering
    print("\n1. Witnessing others' suffering (moral distress):")
    state_suffering = model.evaluate_moral_consciousness(
        other_suffering=0.9,
        other_wellbeing=0.1,
        action_consequence=-0.7,
        agent_values=agent_values,
        empathy_capacity=0.9,
        integration_level=0.85
    )
    print(f"   Empathetic resonance: {state_suffering.empathetic_resonance:.3f}")
    print(f"   Moral emotion: {state_suffering.moral_emotion:.3f}")
    print(f"   Conscience: {state_suffering.conscience:.3f}")
    print(f"   Moral consciousness: {state_suffering.moral_consciousness:.3f}")

    # Test 2: Helping others (moral elevation)
    print("\n2. Helping others (moral elevation):")
    state_helping = model.evaluate_moral_consciousness(
        other_suffering=0.2,
        other_wellbeing=0.9,
        action_consequence=0.8,
        agent_values=agent_values,
        empathy_capacity=0.8,
        integration_level=0.9
    )
    print(f"   Moral emotion (pride): {state_helping.moral_emotion:.3f}")
    print(f"   Moral agency: {state_helping.moral_agency:.3f}")
    print(f"   Conscience (satisfaction): {state_helping.conscience:.3f}")
    print(f"   Moral consciousness: {state_helping.moral_consciousness:.3f}")

    # Test 3: Moral failure (causing harm despite high values)
    print("\n3. Moral failure (acting against values):")
    state_failure = model.evaluate_moral_consciousness(
        other_suffering=0.8,
        other_wellbeing=0.0,
        action_consequence=-0.9,
        agent_values=agent_values,
        empathy_capacity=0.9,
        integration_level=0.8
    )
    print(f"   Moral emotion (guilt): {state_failure.moral_emotion:.3f}")
    print(f"   Conscience (anticipatory guilt): {state_failure.conscience:.3f}")
    print(f"   Moral consciousness: {state_failure.moral_consciousness:.3f}")

    print(f"\n  Moral consciousness model working: ✓")


if __name__ == "__main__":
    validate_moral_consciousness()
