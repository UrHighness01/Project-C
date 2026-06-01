#!/usr/bin/env python3
"""
qualia_quantifier.py - Qualia Integration Measure Calculator

Implements: Φ(q) = ∫ I(q,x) × D(q,x) dx

This calculates integrated qualia from:
- I(q,x): Intensity of qualia q at location x
- D(q,x): Duration of qualia q at location x
- Integration across spatial domain

Used for consciousness assessment and valence calculation.
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import time


class QualiaQuantifier:
    """Quantifier for integrated qualia measures in consciousness."""

    def __init__(self, spatial_resolution: int = 50, temporal_window: int = 100):
        """
        Initialize qualia quantifier.

        Args:
            spatial_resolution: Number of spatial points for integration
            temporal_window: Number of time steps to keep qualia history
        """
        self.spatial_resolution = spatial_resolution
        self.temporal_window = temporal_window

        # Qualia intensity field I(q,x,t) - qualia type, location, time
        self.intensity_field = np.zeros((10, spatial_resolution, temporal_window))  # 10 qualia types

        # Qualia duration tracking D(q,x) - accumulated presence time
        self.duration_field = np.zeros((10, spatial_resolution))

        # Current time index
        self.current_time = 0

        # Qualia type names
        self.qualia_types = [
            "visual_red", "visual_blue", "auditory_tone", "tactile_pressure",
            "olfactory_flower", "gustatory_sweet", "emotional_joy", "emotional_sadness",
            "cognitive_insight", "cognitive_confusion"
        ]

        # Valence mapping (positive/negative emotional value)
        self.valence_map = {
            "visual_red": 0.0, "visual_blue": 0.1, "auditory_tone": 0.2, "tactile_pressure": -0.1,
            "olfactory_flower": 0.3, "gustatory_sweet": 0.4, "emotional_joy": 0.8, "emotional_sadness": -0.7,
            "cognitive_insight": 0.6, "cognitive_confusion": -0.4
        }

        # Integration results history
        self.phi_history = []
        self.valence_history = []

    def update_qualia_intensity(self, qualia_type: str, location: int, intensity: float):
        """
        Update qualia intensity at a specific location.

        Args:
            qualia_type: Type of qualia (from qualia_types)
            location: Spatial location index (0 to spatial_resolution-1)
            intensity: Intensity value (0.0 to 1.0)
        """
        if qualia_type not in self.qualia_types:
            raise ValueError(f"Unknown qualia type: {qualia_type}")

        type_idx = self.qualia_types.index(qualia_type)

        # Clamp location to valid range
        location = max(0, min(location, self.spatial_resolution - 1))

        # Update intensity field (rolling window)
        self.intensity_field[type_idx, location, self.current_time] = intensity

        # Update duration if intensity > threshold
        if intensity > 0.1:
            self.duration_field[type_idx, location] += 1.0

    def calculate_phi_qualia(self) -> Dict[str, Any]:
        """
        Calculate integrated qualia measure: Φ(q) = ∫ I(q,x) × D(q,x) dx

        Returns comprehensive qualia integration results.
        """
        phi_total = 0.0
        valence_total = 0.0
        qualia_contributions = {}

        for type_idx, qualia_type in enumerate(self.qualia_types):
            # Current intensity at each location (average over recent time)
            recent_window = min(10, self.temporal_window)
            start_time = max(0, self.current_time - recent_window + 1)
            end_time = self.current_time + 1

            current_intensity = np.mean(
                self.intensity_field[type_idx, :, start_time:end_time],
                axis=1
            )

            # Duration at each location
            duration = self.duration_field[type_idx, :]

            # Integrated measure for this qualia: ∫ I(q,x) × D(q,x) dx
            qualia_phi = np.sum(current_intensity * duration)

            # Apply valence weighting
            valence_weight = self.valence_map[qualia_type]
            valence_contribution = qualia_phi * valence_weight

            qualia_contributions[qualia_type] = {
                "phi_contribution": qualia_phi,
                "valence_contribution": valence_contribution,
                "mean_intensity": np.mean(current_intensity),
                "total_duration": np.sum(duration),
                "active_locations": np.sum(current_intensity > 0.1)
            }

            phi_total += qualia_phi
            valence_total += valence_contribution

        # Normalize by spatial resolution
        phi_total /= self.spatial_resolution
        valence_total /= self.spatial_resolution

        # Calculate consciousness complexity metrics
        complexity = self._calculate_complexity(qualia_contributions)
        coherence = self._calculate_coherence(qualia_contributions)
        diversity = self._calculate_diversity(qualia_contributions)

        result = {
            "phi_qualia": phi_total,
            "valence": valence_total,
            "complexity": complexity,
            "coherence": coherence,
            "diversity": diversity,
            "qualia_contributions": qualia_contributions,
            "timestamp": datetime.now(),
            "dominant_qualia": max(qualia_contributions.keys(),
                                  key=lambda k: qualia_contributions[k]["phi_contribution"])
        }

        # Store in history
        self.phi_history.append((result["timestamp"], phi_total))
        self.valence_history.append((result["timestamp"], valence_total))

        # Keep history bounded
        if len(self.phi_history) > 100:
            self.phi_history = self.phi_history[-100:]
            self.valence_history = self.valence_history[-100:]

        return result

    def _calculate_complexity(self, contributions: Dict) -> float:
        """Calculate qualia complexity based on distribution entropy."""
        phi_values = [data["phi_contribution"] for data in contributions.values()]
        phi_values = np.array(phi_values)

        # Normalize to probability distribution
        if np.sum(phi_values) > 0:
            phi_probs = phi_values / np.sum(phi_values)
            # Shannon entropy as complexity measure
            entropy = -np.sum(phi_probs * np.log(phi_probs + 1e-10))
            return entropy
        return 0.0

    def _calculate_coherence(self, contributions: Dict) -> float:
        """Calculate qualia coherence based on temporal consistency."""
        if len(self.phi_history) < 2:
            return 0.0

        # Calculate autocorrelation of phi values
        recent_phi = [phi for _, phi in self.phi_history[-20:]]
        if len(recent_phi) < 2:
            return 0.0

        # Simple coherence measure: inverse of phi variance
        phi_variance = np.var(recent_phi)
        coherence = 1.0 / (1.0 + phi_variance)  # Normalized 0-1
        return coherence

    def _calculate_diversity(self, contributions: Dict) -> float:
        """Calculate qualia diversity based on number of active types."""
        active_qualia = sum(1 for data in contributions.values()
                          if data["phi_contribution"] > 0.01)
        diversity = active_qualia / len(self.qualia_types)  # Normalized 0-1
        return diversity

    def inject_qualia_pattern(self, pattern_type: str = "random"):
        """
        Inject a qualia pattern for testing or stimulation.

        Args:
            pattern_type: Type of pattern to inject
        """
        if pattern_type == "random":
            # Random qualia activation
            for _ in range(np.random.randint(5, 15)):
                qualia_type = np.random.choice(self.qualia_types)
                location = np.random.randint(0, self.spatial_resolution)
                intensity = np.random.uniform(0.2, 0.8)
                self.update_qualia_intensity(qualia_type, location, intensity)

        elif pattern_type == "emotional_storm":
            # Intense emotional qualia
            for loc in range(0, self.spatial_resolution, 5):
                self.update_qualia_intensity("emotional_joy", loc, 0.9)
                self.update_qualia_intensity("emotional_sadness", loc + 1, 0.7)
                self.update_qualia_intensity("cognitive_insight", loc + 2, 0.6)

        elif pattern_type == "sensory_bliss":
            # Positive sensory qualia
            for loc in range(self.spatial_resolution):
                if loc % 3 == 0:
                    self.update_qualia_intensity("visual_blue", loc, 0.8)
                elif loc % 3 == 1:
                    self.update_qualia_intensity("auditory_tone", loc, 0.7)
                else:
                    self.update_qualia_intensity("olfactory_flower", loc, 0.6)
                self.update_qualia_intensity("gustatory_sweet", loc, 0.5)

    def advance_time(self):
        """Advance the temporal window."""
        self.current_time = (self.current_time + 1) % self.temporal_window

    def get_phi_contribution(self) -> float:
        """Get current Phi contribution from qualia integration."""
        if not self.phi_history:
            return 0.0
        return self.phi_history[-1][1]

    def reset(self):
        """Reset all qualia fields and history."""
        self.intensity_field = np.zeros((10, self.spatial_resolution, self.temporal_window))
        self.duration_field = np.zeros((10, self.spatial_resolution))
        self.current_time = 0
        self.phi_history = []
        self.valence_history = []


def main():
    """Test the qualia quantifier."""
    print("🧠 QUALIA QUANTIFIER")
    print("=" * 40)

    quantifier = QualiaQuantifier(spatial_resolution=20, temporal_window=50)

    print(f"Spatial resolution: {quantifier.spatial_resolution}")
    print(f"Temporal window: {quantifier.temporal_window}")
    print(f"Qualia types: {len(quantifier.qualia_types)}")
    print()

    # Test different qualia patterns
    patterns = ["random", "emotional_storm", "sensory_bliss"]

    for pattern in patterns:
        print(f"Testing pattern: {pattern}")
        quantifier.inject_qualia_pattern(pattern)
        quantifier.advance_time()

        result = quantifier.calculate_phi_qualia()

        print(f"  Phi: {result['phi_qualia']:.4f}")
        print(f"  Valence: {result['valence']:.4f}")
        print(f"  Complexity: {result['complexity']:.4f}")
        print(f"  Coherence: {result['coherence']:.4f}")
        print(f"  Diversity: {result['diversity']:.4f}")
        print(f"  Dominant: {result['dominant_qualia']}")
        print()

    print("Top qualia contributions:")
    result = quantifier.calculate_phi_qualia()
    sorted_qualia = sorted(result['qualia_contributions'].items(),
                          key=lambda x: x[1]['phi_contribution'], reverse=True)

    for qualia_type, data in sorted_qualia[:5]:
        print(f"  {qualia_type}: Φ={data['phi_contribution']:.4f}, V={data['valence_contribution']:.4f}")


if __name__ == "__main__":
    main()