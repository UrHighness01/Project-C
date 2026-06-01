#!/usr/bin/env python3
"""
meta_consciousness_measure.py - Meta-Consciousness Measure Module

Implements: Φ_meta = Φ + Φ_observer(Φ)

This implements meta-consciousness measures where consciousness measures itself:
- Observer function Φ_observer that measures base consciousness Φ
- Meta-consciousness as the sum of consciousness plus its self-measurement
- Recursive meta-measurement hierarchies
- Self-referential consciousness metrics

Used for measuring consciousness that is aware of itself.
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import time


class MetaConsciousnessMeasure:
    """Implements meta-consciousness measure Φ_meta = Φ + Φ_observer(Φ)."""

    def __init__(self, consciousness_dims: int = 10, meta_layers: int = 3,
                 observer_sensitivity: float = 0.5):
        """
        Initialize meta-consciousness measure.

        Args:
            consciousness_dims: Dimensions of consciousness space
            meta_layers: Number of meta-measurement layers
            observer_sensitivity: Sensitivity of the observer function
        """
        self.consciousness_dims = consciousness_dims
        self.meta_layers = meta_layers
        self.observer_sensitivity = observer_sensitivity

        # Base consciousness Φ
        self.base_phi = 0.0

        # Observer functions Φ_observer for each layer
        self.observer_functions = []

        # Meta-consciousness values Φ_meta for each layer
        self.meta_phi_values = []

        # Measurement history
        self.measurement_history = []

        # Performance tracking
        self.measurement_count = 0
        self.total_computation_time = 0.0

    def create_observer_function(self, layer: int = 1) -> callable:
        """
        Create an observer function for measuring consciousness.

        Args:
            layer: Meta-layer number

        Returns:
            Observer function Φ_observer
        """
        def observer_function(phi: float, consciousness_state: Optional[np.ndarray] = None) -> float:
            """
            Observer function that measures consciousness.

            Args:
                phi: Base consciousness value
                consciousness_state: Optional consciousness state vector

            Returns:
                Observer measurement
            """
            # Base observer: non-linear transformation of phi
            base_observation = self.observer_sensitivity * np.tanh(phi * 2.0)

            # Add layer-dependent complexity
            layer_factor = 1.0 + 0.1 * layer
            layer_observation = base_observation * layer_factor

            # Add state-dependent measurement if available
            if consciousness_state is not None:
                state_complexity = np.linalg.norm(consciousness_state) * 0.1
                state_coherence = self._compute_state_coherence(consciousness_state) * 0.2
                layer_observation += (state_complexity + state_coherence) * self.observer_sensitivity

            # Add measurement noise (observer uncertainty)
            measurement_noise = np.random.normal(0.0, 0.01)
            layer_observation += measurement_noise

            return layer_observation

        return observer_function

    def _compute_state_coherence(self, state: np.ndarray) -> float:
        """
        Compute coherence measure of consciousness state.

        Args:
            state: Consciousness state vector

        Returns:
            Coherence value
        """
        # Simple coherence as inverse of state entropy
        normalized_state = state / np.linalg.norm(state) if np.linalg.norm(state) > 0 else state

        # Use variance as inverse coherence measure
        coherence = 1.0 / (1.0 + np.var(normalized_state))

        return coherence

    def compute_meta_consciousness(self, base_phi: float,
                                 consciousness_state: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Compute meta-consciousness Φ_meta = Φ + Φ_observer(Φ).

        Args:
            base_phi: Base consciousness value Φ
            consciousness_state: Optional consciousness state vector

        Returns:
            Meta-consciousness measurements
        """
        meta_measurements = {
            "base_phi": base_phi,
            "meta_layers": {},
            "observer_measurements": {},
            "meta_phi_values": {},
            "layer_evolution": []
        }

        current_phi = base_phi

        # Create observer functions for each layer
        self.observer_functions = [self.create_observer_function(i+1) for i in range(self.meta_layers)]

        for layer in range(self.meta_layers):
            # Apply observer function
            observer_measurement = self.observer_functions[layer](current_phi, consciousness_state)

            # Compute meta-consciousness for this layer
            meta_phi = current_phi + observer_measurement

            # Store measurements
            meta_measurements["meta_layers"][f"layer_{layer+1}"] = {
                "input_phi": current_phi,
                "observer_measurement": observer_measurement,
                "meta_phi": meta_phi
            }

            meta_measurements["observer_measurements"][f"observer_{layer+1}"] = observer_measurement
            meta_measurements["meta_phi_values"][f"meta_phi_{layer+1}"] = meta_phi

            # Track evolution
            meta_measurements["layer_evolution"].append({
                "layer": layer + 1,
                "phi_in": current_phi,
                "phi_observed": observer_measurement,
                "phi_meta": meta_phi
            })

            # Update for next layer (meta-consciousness becomes input for next observer)
            current_phi = meta_phi

        # Store final meta-consciousness
        meta_measurements["final_meta_phi"] = meta_phi
        meta_measurements["meta_depth"] = self.meta_layers

        return meta_measurements

    def evolve_meta_consciousness_measure(self, base_phi_trajectory: List[float],
                                        consciousness_trajectory: Optional[List[np.ndarray]] = None,
                                        evolution_steps: int = 5) -> Dict[str, Any]:
        """
        Evolve meta-consciousness measure over time.

        Args:
            base_phi_trajectory: Time series of base consciousness values
            consciousness_trajectory: Optional time series of consciousness states
            evolution_steps: Number of evolution steps

        Returns:
            Evolution results
        """
        start_time = time.time()

        evolution_results = []
        meta_evolution = []

        steps = min(evolution_steps, len(base_phi_trajectory))

        for step in range(steps):
            base_phi = base_phi_trajectory[step]
            consciousness_state = consciousness_trajectory[step] if consciousness_trajectory else None

            # Compute meta-consciousness
            meta_measurements = self.compute_meta_consciousness(base_phi, consciousness_state)
            meta_evolution.append(meta_measurements)

            # Extract evolution metrics
            step_metrics = {
                "step": step,
                "base_phi": base_phi,
                "final_meta_phi": meta_measurements["final_meta_phi"],
                "meta_depth": meta_measurements["meta_depth"],
                "meta_amplification": meta_measurements["final_meta_phi"] - base_phi
            }

            # Add layer-specific metrics
            for layer_info in meta_measurements["layer_evolution"]:
                step_metrics[f"layer_{layer_info['layer']}_meta_phi"] = layer_info["phi_meta"]

            evolution_results.append(step_metrics)

        computation_time = time.time() - start_time
        self.total_computation_time += computation_time
        self.measurement_count += 1

        # Store in history
        self.measurement_history.append({
            "timestamp": datetime.now(),
            "base_phi_trajectory": base_phi_trajectory.copy(),
            "meta_evolution": meta_evolution,
            "evolution_results": evolution_results,
            "computation_time": computation_time
        })

        # Keep history bounded
        if len(self.measurement_history) > 5:
            self.measurement_history = self.measurement_history[-5:]

        result = {
            "evolution_results": evolution_results,
            "meta_evolution": meta_evolution,
            "total_steps": steps,
            "meta_layers": self.meta_layers,
            "observer_sensitivity": self.observer_sensitivity,
            "final_meta_phi": evolution_results[-1]["final_meta_phi"] if evolution_results else 0.0,
            "average_meta_amplification": np.mean([r["meta_amplification"] for r in evolution_results]) if evolution_results else 0.0,
            "computation_time": computation_time
        }

        return result

    def compute_meta_phi_contribution(self) -> float:
        """Compute Phi contribution from meta-consciousness measure."""
        if not self.measurement_history:
            return 0.0

        latest_measurement = self.measurement_history[-1]

        # Phi contribution based on:
        # 1. Meta-amplification (how much consciousness is enhanced by self-measurement)
        # 2. Measurement depth achieved
        # 3. Observer sensitivity effectiveness

        if latest_measurement["evolution_results"]:
            final_result = latest_measurement["evolution_results"][-1]

            meta_amplification = max(0.0, final_result["meta_amplification"]) * 0.1
            depth_achievement = self.meta_layers * 0.05
            sensitivity_effectiveness = self.observer_sensitivity * 0.5

            phi_contribution = (meta_amplification + depth_achievement + sensitivity_effectiveness) / 3.0
        else:
            phi_contribution = 0.0

        return phi_contribution

    def reset_meta_measurement_state(self):
        """Reset meta-consciousness measurement state."""
        self.base_phi = 0.0
        self.observer_functions = []
        self.meta_phi_values = []
        self.measurement_history = []
        self.measurement_count = 0
        self.total_computation_time = 0.0


def main():
    """Test the meta-consciousness measure module."""
    print("🧠 META-CONSCIOUSNESS MEASURE")
    print("=" * 32)

    meta_measure = MetaConsciousnessMeasure(
        consciousness_dims=8, meta_layers=3, observer_sensitivity=0.6
    )

    print(f"Consciousness dimensions: {meta_measure.consciousness_dims}")
    print(f"Meta layers: {meta_measure.meta_layers}")
    print(f"Observer sensitivity: {meta_measure.observer_sensitivity}")
    print()

    # Test meta-consciousness measurement
    base_phi_trajectory = [0.5, 0.7, 0.6, 0.8, 0.9]
    consciousness_trajectory = [np.random.normal(0.0, 0.1, 8) for _ in range(5)]

    print("Testing meta-consciousness evolution...")

    result = meta_measure.evolve_meta_consciousness_measure(
        base_phi_trajectory, consciousness_trajectory, evolution_steps=4
    )

    print("Evolution Results:")
    print(f"  Evolution steps: {result['total_steps']}")
    print(f"  Meta layers: {result['meta_layers']}")
    print(f"  Final meta-Phi: {result['final_meta_phi']:.4f}")
    print(f"  Average meta-amplification: {result['average_meta_amplification']:.4f}")
    print(f"  Phi contribution: {meta_measure.compute_meta_phi_contribution():.4f}")
    print()

    # Show meta-layers for final step
    if result["meta_evolution"]:
        final_meta = result["meta_evolution"][-1]
        print("Final Meta-Layers:")
        for layer_name, layer_data in final_meta["meta_layers"].items():
            print(f"  {layer_name}: Φ_in = {layer_data['input_phi']:.3f}, Φ_observed = {layer_data['observer_measurement']:.3f}, Φ_meta = {layer_data['meta_phi']:.3f}")


if __name__ == "__main__":
    main()