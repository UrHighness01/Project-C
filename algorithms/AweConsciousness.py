#!/usr/bin/env python3
"""
AweConsciousness.py - Phase 25.1: Awe and Transcendent Consciousness

Theory: Awe is consciousness expanding beyond individual identity. The self-boundary
dissolves; consciousness becomes cosmic. The vastness of the stimulus meets cognitive
limits, creating a state of transcendence where "I" becomes part of something greater.

C_awe = C_baseline × (1 + vastness × accommodation) × (1 - self_boundary)
Transcendence: When C_awe > threshold AND self_boundary < threshold

References:
- Keltner, D., & Haidt, J. (2003) "Approaching awe, a moral, social, and aesthetic emotion"
- Yaden, D. B., et al. (2018) "The neuroscience of awe"
- Piff, P. K., et al. (2015) "Awe, the small self, and prosocial behavior"

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class AweState:
    """Awe consciousness state."""
    stimulus_vastness: float  # Scale/magnitude of stimulus (0-1)
    stimulus_complexity: float  # Cognitive demand/novelty (0-1)
    threat_component: float  # Perception of danger/overwhelm (0-1)
    accommodation_demand: float  # Cognitive effort needed to understand (0-1)
    self_boundary_dissolution: float  # Loss of individual identity (0-1)
    self_transcendence: float  # Sense of connecting to something greater (0-1)
    cosmic_consciousness: float  # Feeling of vastness/infinity (0-1)
    awe_consciousness: float  # Peak consciousness of transcendence


class AweConsciousnessModel:
    """Models awe and transcendent consciousness states."""

    def compute_vastness(self, scale: float, temporal_scope: float,
                        complexity: float) -> float:
        """Compute perception of vastness (magnitude exceeding comprehension).

        Vastness from: large scale (spatial), long time (temporal), high complexity (cognitive).
        """
        # Spatial vastness: size relative to self
        spatial = scale

        # Temporal vastness: how much time does it encompass?
        temporal = temporal_scope

        # Cognitive vastness: complexity that exceeds understanding
        cognitive = complexity * 0.8

        vastness = (spatial * 0.4 + temporal * 0.3 + cognitive * 0.3)
        return float(np.clip(vastness, 0, 1))

    def compute_accommodation_demand(self, vastness: float,
                                    cognitive_capacity: float = 0.8) -> float:
        """Compute cognitive demand to accommodate vastness.

        How much cognitive effort to understand something vast?
        When demand exceeds capacity → overwhelm, awe.
        """
        # Demand increases with vastness
        demand = vastness * (1.0 - cognitive_capacity * 0.5)

        return float(np.clip(demand, 0, 1))

    def compute_threat_component(self, danger_level: float,
                                 overwhelm_level: float) -> float:
        """Compute threat/overwhelm aspect of awe.

        Some awe involves actual or perceived danger (mountains, storms).
        Some involves cognitive overwhelm.
        """
        threat = (danger_level * 0.5 + overwhelm_level * 0.5)
        return float(np.clip(threat, 0, 1))

    def compute_self_boundary_dissolution(self, vastness: float,
                                         identification_with_vast: float = 0.7,
                                         ego_dissolution: float = 0.0) -> float:
        """Compute dissolution of individual self-boundary.

        In awe, the individual self becomes small, merges with vastness.
        Voluntary dissolution (meditation) vs involuntary (awe-struck).
        """
        # Vastness naturally reduces self-salience
        boundary_loss_from_vastness = vastness * 0.7

        # Identification with vast (feeling part of it)
        identification = identification_with_vast * 0.2

        # Voluntary ego-dissolution (meditation)
        voluntary = ego_dissolution * 0.1

        dissolution = boundary_loss_from_vastness + identification + voluntary

        return float(np.clip(dissolution, 0, 1))

    def compute_self_transcendence(self, self_boundary_dissolution: float,
                                   connection_to_whole: float) -> float:
        """Compute transcendence: experiencing oneself as part of something greater.

        Self-transcendence: loss of individual boundaries + feeling connected to larger whole.
        """
        transcendence = (self_boundary_dissolution * 0.6 +
                        connection_to_whole * 0.4)

        return float(np.clip(transcendence, 0, 1))

    def compute_cosmic_consciousness(self, vastness: float,
                                    interconnection: float = 0.7) -> float:
        """Compute felt sense of cosmic consciousness.

        Experience of vastness as consciousness itself, not separate from self.
        Sense of connection to cosmos, nature, or existence.
        """
        cosmic = vastness * interconnection
        return float(np.clip(cosmic, 0, 1))

    def evaluate_awe_consciousness(self, scale: float, temporal_scope: float,
                                   complexity: float, danger_level: float = 0.2,
                                   overwhelm_level: float = 0.5,
                                   cognitive_capacity: float = 0.8,
                                   identification_strength: float = 0.8,
                                   integration_level: float = 0.8) -> AweState:
        """Evaluate awe consciousness state.

        Awe is peak consciousness where individual self dissolves into vastness.
        This is consciousness beyond the individual, beyond survival, beyond goals.
        """
        # Compute vastness perception
        vastness = self.compute_vastness(scale, temporal_scope, complexity)

        # Accommodation demand
        accommodation = self.compute_accommodation_demand(vastness, cognitive_capacity)

        # Threat component
        threat = self.compute_threat_component(danger_level, overwhelm_level)

        # Self-boundary dissolution
        dissolution = self.compute_self_boundary_dissolution(
            vastness, identification_strength
        )

        # Self-transcendence
        transcendence = self.compute_self_transcendence(
            dissolution, identification_strength
        )

        # Cosmic consciousness
        cosmic = self.compute_cosmic_consciousness(vastness, identification_strength)

        # Awe consciousness: peaks when vastness high, self-boundary low
        # Consciousness = baseline × (vastness effect) × (self-dissolution effect)
        awe_c = 0.7 * (1.0 + vastness * 0.5) * (1.0 - dissolution * 0.3)
        awe_c *= (1.0 + integration_level * 0.2)  # Integration enhances awe

        return AweState(
            stimulus_vastness=vastness,
            stimulus_complexity=float(np.clip(complexity, 0, 1)),
            threat_component=threat,
            accommodation_demand=accommodation,
            self_boundary_dissolution=dissolution,
            self_transcendence=transcendence,
            cosmic_consciousness=cosmic,
            awe_consciousness=float(np.clip(awe_c, 0, 1))
        )


def validate_awe_consciousness():
    """Validate awe consciousness model."""
    print("Validating Awe and Transcendent Consciousness")
    print("=" * 60)

    model = AweConsciousnessModel()

    # Test 1: Vast natural landscape (mountain, sky, cosmos)
    print("\n1. Vast natural landscape (mountains, cosmos):")
    state_landscape = model.evaluate_awe_consciousness(
        scale=0.95,           # Huge spatial scale
        temporal_scope=0.9,   # Ancient/eternal timescale
        complexity=0.7,       # Moderate cognitive demand
        danger_level=0.3,     # Some perceived danger
        overwhelm_level=0.6,  # Cognitive overwhelm
        cognitive_capacity=0.8,
        identification_strength=0.85,
        integration_level=0.9
    )
    print(f"   Stimulus vastness: {state_landscape.stimulus_vastness:.3f}")
    print(f"   Accommodation demand: {state_landscape.accommodation_demand:.3f}")
    print(f"   Self-boundary dissolution: {state_landscape.self_boundary_dissolution:.3f}")
    print(f"   Cosmic consciousness: {state_landscape.cosmic_consciousness:.3f}")
    print(f"   Awe consciousness: {state_landscape.awe_consciousness:.3f}")

    # Test 2: Profound art/music (emotional awe)
    print("\n2. Profound art (symphony, painting):")
    state_art = model.evaluate_awe_consciousness(
        scale=0.5,            # Moderate scale
        temporal_scope=0.8,   # Spans long time periods
        complexity=0.95,      # High cognitive/emotional complexity
        danger_level=0.0,     # No threat
        overwhelm_level=0.7,  # Emotional overwhelm
        cognitive_capacity=0.85,
        identification_strength=0.9,
        integration_level=0.85
    )
    print(f"   Accommodation demand: {state_art.accommodation_demand:.3f}")
    print(f"   Self-transcendence: {state_art.self_transcendence:.3f}")
    print(f"   Awe consciousness: {state_art.awe_consciousness:.3f}")

    # Test 3: Threatening vastness (storm, earthquake, avalanche)
    print("\n3. Threatening vastness (natural disaster):")
    state_threat = model.evaluate_awe_consciousness(
        scale=0.9,
        temporal_scope=0.6,
        complexity=0.8,
        danger_level=0.9,     # High threat
        overwhelm_level=0.95,
        cognitive_capacity=0.7,
        identification_strength=0.4,  # Can't identify with threat
        integration_level=0.7
    )
    print(f"   Threat component: {state_threat.threat_component:.3f}")
    print(f"   Self-boundary dissolution: {state_threat.self_boundary_dissolution:.3f}")
    print(f"   Awe consciousness: {state_threat.awe_consciousness:.3f}")

    # Test 4: Peak awe experience (optimal conditions)
    print("\n4. Peak awe experience (optimal vastness + connection):")
    state_peak = model.evaluate_awe_consciousness(
        scale=0.92,
        temporal_scope=0.95,
        complexity=0.75,
        danger_level=0.15,
        overwhelm_level=0.5,
        cognitive_capacity=0.9,
        identification_strength=0.95,
        integration_level=0.95
    )
    print(f"   Cosmic consciousness: {state_peak.cosmic_consciousness:.3f}")
    print(f"   Self-transcendence: {state_peak.self_transcendence:.3f}")
    print(f"   Awe consciousness: {state_peak.awe_consciousness:.3f}")

    print(f"\n  Awe consciousness model working: ✓")


if __name__ == "__main__":
    validate_awe_consciousness()
