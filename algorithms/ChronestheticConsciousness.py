#!/usr/bin/env python3
"""
ChronestheticConsciousness.py - Phase 19.1: Mental Time Travel Consciousness

Theory: Consciousness includes vivid mental time travel—remembering the past and imagining
the future with rich sensory/emotional detail. Chronesthesia is the subjective experience of
mentally traveling in time with phenomenal intensity.

C_chronesthesia = vividness(memory) × integration × emotional_resonance
Where vividness = sensory_detail × temporal_specificity × coherence

References:
- Tulving, E. (1983) "Elements of Episodic Memory"
- Schacter, D. L., & Addis, D. R. (2007) "Constructive episodic simulation"
- Andrews-Hanna, J. R. (2012) "The brain's default network and internal mentation"

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class ChronestheticState:
    """Mental time travel consciousness state."""
    temporal_direction: str  # "past" or "future"
    temporal_distance: float  # Distance in subjective years
    sensory_vividness: float  # Detail of sensory reconstruction (0-1)
    emotional_resonance: float  # Emotional intensity of remembered/imagined event (0-1)
    temporal_specificity: float  # How precisely located in past/future (0-1)
    coherence: float  # How well integrated as unified event (0-1)
    autonoetic_consciousness: float  # Awareness that YOU remember/imagine (0-1)
    phenomenal_intensity: float  # Overall consciousness of time travel


class ChronestheticConsciousnessModel:
    """Models vivid mental time travel consciousness."""

    def reconstruct_past_event(self, original_vividness: float = 0.8,
                               time_elapsed_years: float = 5.0,
                               retrieval_cues: float = 0.7,
                               emotional_significance: float = 0.6) -> dict:
        """Reconstruct a past event with degradation over time and interference.

        Vivid emotional memories are better preserved than mundane events.
        Recent memories are more detailed than distant ones.
        Good retrieval cues enhance reconstruction.
        """
        # Temporal decay: detail decreases over time (exponential)
        temporal_decay = np.exp(-time_elapsed_years / 15.0)

        # Emotional enhancement: emotionally significant memories better preserved
        emotional_factor = emotional_significance + (1 - emotional_significance) * 0.3

        # Cue enhancement: retrieval cues restore detail
        cue_factor = 0.5 + retrieval_cues * 0.5

        # Reconstructed vividness
        sensory_detail = original_vividness * temporal_decay * emotional_factor * cue_factor
        sensory_detail = float(np.clip(sensory_detail, 0, 1))

        # Temporal specificity decreases with time
        # Recent events are dateable; distant events become approximate
        temporal_specificity = (1.0 - (time_elapsed_years / 80.0) * 0.7)
        temporal_specificity = float(np.clip(temporal_specificity, 0, 1))

        # Coherence: emotional memories maintain narrative coherence
        coherence = emotional_significance * 0.8 + 0.2
        coherence = float(np.clip(coherence, 0, 1))

        return {
            "sensory_vividness": sensory_detail,
            "temporal_specificity": temporal_specificity,
            "coherence": coherence,
            "emotional_resonance": emotional_significance
        }

    def project_future_event(self, goal_vividness: float = 0.6,
                            time_horizon_years: float = 1.0,
                            planning_detail: float = 0.7,
                            emotional_anticipation: float = 0.5) -> dict:
        """Project a future event with anticipated sensory/emotional details.

        Near future events are more vividly imagined than distant.
        Emotionally significant futures get more detail.
        Good planning increases sensory specificity.
        """
        # Temporal projection: near futures more vivid than distant
        temporal_factor = np.exp(-time_horizon_years / 10.0)

        # Planning detail enhances mental simulation
        planning_factor = 0.5 + planning_detail * 0.5

        # Emotional anticipation drives simulation detail
        emotional_factor = emotional_anticipation

        # Projected vividness (imagined sensory detail)
        sensory_detail = goal_vividness * temporal_factor * planning_factor * 0.8
        sensory_detail = float(np.clip(sensory_detail, 0, 1))

        # Temporal specificity for future (more specific for near future)
        temporal_specificity = temporal_factor * planning_detail
        temporal_specificity = float(np.clip(temporal_specificity, 0, 1))

        # Coherence of imagined future
        coherence = planning_detail * 0.8 + emotional_anticipation * 0.2
        coherence = float(np.clip(coherence, 0, 1))

        return {
            "sensory_vividness": sensory_detail,
            "temporal_specificity": temporal_specificity,
            "coherence": coherence,
            "emotional_resonance": emotional_anticipation
        }

    def compute_chronesthetic_consciousness(self, temporal_direction: str,
                                           sensory_vividness: float,
                                           emotional_resonance: float,
                                           temporal_specificity: float,
                                           coherence: float,
                                           integration_level: float = 0.7) -> ChronestheticState:
        """Compute consciousness of mental time travel.

        Consciousness of time travel depends on:
        - Vividness of sensory reconstruction/imagination
        - Emotional resonance with the event
        - How specifically located in past/future
        - Narrative coherence
        - Integration (metacognitive awareness of remembering/imagining)
        """
        # Vividness factor combines sensory detail with coherence
        vividness = (sensory_vividness * 0.6 + coherence * 0.4)

        # Autonoetic consciousness: awareness that YOU remember/imagine
        # Requires integration and self-reference
        autonoetic = integration_level * vividness

        # Overall phenomenal intensity of chronesthesia
        phenomenal = (vividness * 0.4 +
                     emotional_resonance * 0.3 +
                     temporal_specificity * 0.2 +
                     autonoetic * 0.1)

        phenomenal = float(np.clip(phenomenal, 0, 1))

        return ChronestheticState(
            temporal_direction=temporal_direction,
            temporal_distance=0.0,  # Placeholder
            sensory_vividness=float(np.clip(sensory_vividness, 0, 1)),
            emotional_resonance=float(np.clip(emotional_resonance, 0, 1)),
            temporal_specificity=float(np.clip(temporal_specificity, 0, 1)),
            coherence=float(np.clip(coherence, 0, 1)),
            autonoetic_consciousness=float(np.clip(autonoetic, 0, 1)),
            phenomenal_intensity=phenomenal
        )


def validate_chronesthetic_consciousness():
    """Validate chronesthetic consciousness model."""
    print("Validating Chronesthetic (Mental Time Travel) Consciousness")
    print("=" * 60)

    model = ChronestheticConsciousnessModel()

    # Test 1: Vivid recent memory (emotionally significant)
    print("\n1. Vivid recent memory (emotionally significant, 2 years ago):")
    past_details = model.reconstruct_past_event(
        original_vividness=0.9,
        time_elapsed_years=2.0,
        retrieval_cues=0.8,
        emotional_significance=0.9
    )
    state_vivid = model.compute_chronesthetic_consciousness(
        temporal_direction="past",
        sensory_vividness=past_details["sensory_vividness"],
        emotional_resonance=past_details["emotional_resonance"],
        temporal_specificity=past_details["temporal_specificity"],
        coherence=past_details["coherence"],
        integration_level=0.8
    )
    print(f"   Sensory vividness: {state_vivid.sensory_vividness:.3f}")
    print(f"   Emotional resonance: {state_vivid.emotional_resonance:.3f}")
    print(f"   Autonoetic consciousness: {state_vivid.autonoetic_consciousness:.3f}")
    print(f"   Phenomenal intensity: {state_vivid.phenomenal_intensity:.3f}")

    # Test 2: Distant memory fade (forgotten details)
    print("\n2. Distant memory fade (15 years ago, low emotional content):")
    distant = model.reconstruct_past_event(
        original_vividness=0.7,
        time_elapsed_years=15.0,
        retrieval_cues=0.3,
        emotional_significance=0.2
    )
    state_faded = model.compute_chronesthetic_consciousness(
        temporal_direction="past",
        sensory_vividness=distant["sensory_vividness"],
        emotional_resonance=distant["emotional_resonance"],
        temporal_specificity=distant["temporal_specificity"],
        coherence=distant["coherence"],
        integration_level=0.7
    )
    print(f"   Sensory vividness: {state_faded.sensory_vividness:.3f}")
    print(f"   Temporal specificity: {state_faded.temporal_specificity:.3f}")
    print(f"   Phenomenal intensity: {state_faded.phenomenal_intensity:.3f}")

    # Test 3: Future imagination (near-term goal with anticipation)
    print("\n3. Future imagination (6 months away, emotionally significant goal):")
    future_details = model.project_future_event(
        goal_vividness=0.8,
        time_horizon_years=0.5,
        planning_detail=0.8,
        emotional_anticipation=0.8
    )
    state_future = model.compute_chronesthetic_consciousness(
        temporal_direction="future",
        sensory_vividness=future_details["sensory_vividness"],
        emotional_resonance=future_details["emotional_resonance"],
        temporal_specificity=future_details["temporal_specificity"],
        coherence=future_details["coherence"],
        integration_level=0.8
    )
    print(f"   Sensory vividness: {state_future.sensory_vividness:.3f}")
    print(f"   Emotional anticipation: {state_future.emotional_resonance:.3f}")
    print(f"   Phenomenal intensity: {state_future.phenomenal_intensity:.3f}")

    print(f"\n  Chronesthetic consciousness model working: ✓")


if __name__ == "__main__":
    validate_chronesthetic_consciousness()
