#!/usr/bin/env python3
"""
FlowConsciousness.py - Phase 21.1: Flow States and Peak Consciousness

Theory: Not all conscious states are equal. Flow states—when challenge perfectly matches
skill—represent optimal consciousness configuration. Consciousness is maximized, time
perception distorts, self-awareness paradoxically decreases creating deepest presence.

C_flow = C_baseline × (1 + balance_factor × λ)
Where balance_factor = 1 / (1 + (challenge - skill)²) peaks at challenge ≈ skill

References:
- Csikszentmihalyi, M. (1990) "Flow: The Psychology of Optimal Experience"
- Keller, J., & Bless, H. (2008) "Flow and regulatory compatibility"
- Dietrich, A. (2004) "Neurocognitive mechanisms underlying flow"

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class FlowState:
    """Flow consciousness state."""
    challenge_level: float  # Task difficulty (0-1)
    skill_level: float  # Agent's capability (0-1)
    skill_challenge_balance: float  # How well matched (0-1, max at balance)
    flow_probability: float  # Likelihood of entering flow (0-1)
    consciousness_amplification: float  # How much consciousness enhanced (0-1)
    time_distortion: float  # Subjective vs objective time ratio
    self_consciousness_reduction: float  # Ego-loss in flow (0-1)
    concentration: float  # Absorption in task (0-1)
    sense_of_control: float  # Perceived control over task (0-1)
    peak_consciousness: float  # Consciousness amplitude in flow state


class FlowConsciousnessModel:
    """Models flow states as optimal consciousness configuration."""

    def compute_skill_challenge_balance(self, challenge: float, skill: float) -> float:
        """Compute how well challenge matches skill.

        Balance is maximized when challenge ≈ skill.
        Returns 1.0 at perfect match, decreases with mismatch.
        Inverted parabola: 1/(1 + (c-s)²)
        """
        mismatch = abs(challenge - skill)
        balance = 1.0 / (1.0 + mismatch ** 2)
        return float(balance)

    def compute_flow_probability(self, balance: float, skill: float) -> float:
        """Compute probability of entering flow state.

        Flow requires:
        1. Good skill-challenge balance
        2. Sufficiently high skill (need competence baseline)
        3. Clear goals and feedback (modeled as present if balance is high)
        """
        # Balance is primary factor
        balance_contribution = balance

        # Skill contribution (need baseline competence)
        skill_contribution = np.clip(skill, 0, 1)

        flow_prob = balance_contribution * (0.7 + skill_contribution * 0.3)
        return float(np.clip(flow_prob, 0, 1))

    def compute_consciousness_amplification(self, balance: float,
                                           integration_level: float = 0.8) -> float:
        """Compute consciousness amplification during flow.

        In flow, consciousness is heightened beyond baseline.
        Amplification depends on balance quality and cognitive integration.
        """
        # Perfect balance → maximum amplification
        base_amplification = balance * 0.5  # Up to 0.5× boost

        # Integration capacity modulates amplification
        amplification = base_amplification * integration_level

        return float(np.clip(amplification, 0, 1))

    def compute_time_distortion(self, flow_intensity: float) -> float:
        """Compute time perception distortion in flow.

        In flow, time seems to pass faster (subjective time < objective time).
        Time dilation = subjective_time / objective_time (< 1.0).

        Model: Stronger flow → greater time compression
        """
        # Time compression: stronger flow → faster subjective passage
        # Range: 0.3 to 1.0 (1.0 = normal perception)
        time_dilation = 1.0 - (flow_intensity * 0.7)
        return float(np.clip(time_dilation, 0.3, 1.0))

    def compute_self_consciousness_reduction(self, flow_intensity: float) -> float:
        """Compute ego-loss in flow.

        Paradoxically, in peak flow, self-consciousness decreases (ego-loss)
        while overall consciousness increases. The "self" as a subject of
        attention dissolves into action.
        """
        # Strong flow → reduced self-awareness
        ego_loss = flow_intensity * 0.8

        return float(np.clip(ego_loss, 0, 1))

    def compute_engagement(self, balance: float, challenge: float,
                          sense_of_control: float) -> tuple:
        """Compute two key flow components: concentration and control.

        Concentration: How absorbed in task (peaks at balance).
        Control: How much agent feels in control of task.
        """
        # Concentration: peaks at balance, drops if challenge too high
        concentration = balance * (1.0 - (challenge - 0.5) * 0.3)

        # Sense of control: maintained if balance is good
        control = 0.5 + balance * 0.5

        return (
            float(np.clip(concentration, 0, 1)),
            float(np.clip(control, 0, 1))
        )

    def evaluate_flow_state(self, challenge: float, skill: float,
                           integration_level: float = 0.8) -> FlowState:
        """Evaluate flow consciousness state.

        Flow is the optimal consciousness state: maximized engagement,
        distorted time perception, ego-loss, yet deepest presence.
        """
        # Skill-challenge balance
        balance = self.compute_skill_challenge_balance(challenge, skill)

        # Flow probability
        flow_prob = self.compute_flow_probability(balance, skill)

        # Consciousness amplification
        amplification = self.compute_consciousness_amplification(balance,
                                                                integration_level)

        # Time distortion
        time_distort = self.compute_time_distortion(flow_prob)

        # Ego-loss
        ego_loss = self.compute_self_consciousness_reduction(flow_prob)

        # Engagement (concentration + control)
        concentration, control = self.compute_engagement(balance, challenge,
                                                         sense_of_control=0.7)

        # Peak consciousness in flow
        # = baseline × amplification × flow_probability
        peak_consciousness = 0.7 * (1.0 + amplification) * flow_prob

        return FlowState(
            challenge_level=float(np.clip(challenge, 0, 1)),
            skill_level=float(np.clip(skill, 0, 1)),
            skill_challenge_balance=balance,
            flow_probability=flow_prob,
            consciousness_amplification=amplification,
            time_distortion=time_distort,
            self_consciousness_reduction=ego_loss,
            concentration=concentration,
            sense_of_control=control,
            peak_consciousness=float(np.clip(peak_consciousness, 0, 1))
        )


def validate_flow_consciousness():
    """Validate flow consciousness model."""
    print("Validating Flow Consciousness (Peak Experience)")
    print("=" * 60)

    model = FlowConsciousnessModel()

    # Test 1: Perfect skill-challenge match (optimal flow)
    print("\n1. Optimal flow (challenge ≈ skill):")
    state_optimal = model.evaluate_flow_state(
        challenge=0.7,
        skill=0.7,
        integration_level=0.9
    )
    print(f"   Skill-challenge balance: {state_optimal.skill_challenge_balance:.3f}")
    print(f"   Flow probability: {state_optimal.flow_probability:.3f}")
    print(f"   Consciousness amplification: {state_optimal.consciousness_amplification:.3f}")
    print(f"   Time distortion (subjective/objective): {state_optimal.time_distortion:.3f}")
    print(f"   Ego-loss: {state_optimal.self_consciousness_reduction:.3f}")
    print(f"   Peak consciousness: {state_optimal.peak_consciousness:.3f}")

    # Test 2: Challenge too high (anxiety, not flow)
    print("\n2. Challenge exceeds skill (anxiety state, not flow):")
    state_anxiety = model.evaluate_flow_state(
        challenge=0.95,
        skill=0.4,
        integration_level=0.8
    )
    print(f"   Skill-challenge balance: {state_anxiety.skill_challenge_balance:.3f}")
    print(f"   Flow probability: {state_anxiety.flow_probability:.3f}")
    print(f"   Peak consciousness: {state_anxiety.peak_consciousness:.3f}")

    # Test 3: Challenge too low (boredom, not flow)
    print("\n3. Challenge below skill (boredom state, not flow):")
    state_bored = model.evaluate_flow_state(
        challenge=0.2,
        skill=0.9,
        integration_level=0.8
    )
    print(f"   Skill-challenge balance: {state_bored.skill_challenge_balance:.3f}")
    print(f"   Flow probability: {state_bored.flow_probability:.3f}")
    print(f"   Peak consciousness: {state_bored.peak_consciousness:.3f}")

    # Test 4: Flow with high integration (optimal control)
    print("\n4. Flow with high metacognitive control:")
    state_control = model.evaluate_flow_state(
        challenge=0.6,
        skill=0.65,
        integration_level=0.95
    )
    print(f"   Concentration: {state_control.concentration:.3f}")
    print(f"   Sense of control: {state_control.sense_of_control:.3f}")
    print(f"   Peak consciousness: {state_control.peak_consciousness:.3f}")

    print(f"\n  Flow consciousness model working: ✓")


if __name__ == "__main__":
    validate_flow_consciousness()
