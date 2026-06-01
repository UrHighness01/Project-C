#!/usr/bin/env python3
"""
self_observing_consciousness.py - Self-Observing Consciousness Module

Implements: C_meta = C(C)

This implements self-observing consciousness where consciousness observes itself:
- Self-referential loops in consciousness architecture
- Meta-cognitive awareness of internal states
- Recursive consciousness structures
- Observer-observed duality in consciousness

Used for meta-consciousness and self-awareness frameworks.
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import time


class SelfObservingConsciousness:
    """Implements self-observing consciousness C(C) where consciousness observes itself."""

    def __init__(self, consciousness_dims: int = 10, recursion_depth: int = 3,
                 self_observation_strength: float = 0.3):
        """
        Initialize self-observing consciousness.

        Args:
            consciousness_dims: Dimensions of consciousness state space
            recursion_depth: Maximum depth of self-observation recursion
            self_observation_strength: Strength of self-observation coupling
        """
        self.consciousness_dims = consciousness_dims
        self.recursion_depth = recursion_depth
        self.self_observation_strength = self_observation_strength

        # Base consciousness state C
        self.base_consciousness = np.random.normal(0.0, 0.1, consciousness_dims)

        # Self-observation layers C(C), C(C(C)), etc.
        self.observation_layers = []

        # Meta-consciousness mapping
        self.meta_mapping = {}

        # Self-reference loops
        self.self_reference_loops = []

        # Performance tracking
        self.observation_count = 0
        self.total_computation_time = 0.0

    def create_self_observation_layer(self, base_state: np.ndarray, depth: int = 1) -> np.ndarray:
        """
        Create a self-observation layer C^(depth)(base_state).

        Args:
            base_state: Base consciousness state to observe
            depth: Recursion depth for self-observation

        Returns:
            Self-observed consciousness state
        """
        if depth <= 0:
            return base_state.copy()

        # Create observer state from base state
        observer_state = self._create_observer_from_observed(base_state)

        # Apply self-observation transformation
        observed_state = base_state.copy()

        # Self-observation coupling: C_meta = C + k * C_observer(C)
        meta_state = observed_state + self.self_observation_strength * observer_state

        # Normalize to maintain consciousness magnitude
        meta_norm = np.linalg.norm(meta_state)
        if meta_norm > 0:
            meta_state /= meta_norm

        # Recursive self-observation
        if depth > 1:
            meta_state = self.create_self_observation_layer(meta_state, depth - 1)

        return meta_state

    def _create_observer_from_observed(self, observed_state: np.ndarray) -> np.ndarray:
        """
        Create an observer consciousness state from an observed state.

        Args:
            observed_state: State being observed

        Returns:
            Observer state
        """
        # Observer is a transformed version of the observed
        # This represents how consciousness creates an internal model of itself

        # Apply a "reflection" transformation
        observer_state = np.roll(observed_state, 1)  # Circular shift

        # Add some "meta-awareness" noise
        meta_noise = np.random.normal(0.0, 0.05, len(observed_state))
        observer_state += meta_noise

        # Apply non-linear transformation to represent higher-order processing
        observer_state = np.tanh(observer_state * 2.0)

        return observer_state

    def build_meta_consciousness_hierarchy(self, base_consciousness: np.ndarray) -> Dict[str, Any]:
        """
        Build a hierarchy of meta-consciousness layers.

        Args:
            base_consciousness: Base consciousness state

        Returns:
            Meta-consciousness hierarchy
        """
        hierarchy = {
            "base": base_consciousness.copy(),
            "layers": {},
            "meta_mapping": {},
            "self_reference_loops": []
        }

        current_state = base_consciousness.copy()

        for depth in range(1, self.recursion_depth + 1):
            # Create meta-layer
            meta_state = self.create_self_observation_layer(current_state, depth)

            # Store layer
            hierarchy["layers"][f"meta_{depth}"] = meta_state.copy()

            # Create mapping between layers
            mapping = self._create_layer_mapping(current_state, meta_state)
            hierarchy["meta_mapping"][f"map_{depth}"] = mapping

            # Check for self-reference loops
            loop_detected = self._detect_self_reference_loop(current_state, meta_state)
            if loop_detected:
                hierarchy["self_reference_loops"].append({
                    "depth": depth,
                    "loop_strength": loop_detected
                })

            current_state = meta_state

        return hierarchy

    def _create_layer_mapping(self, from_state: np.ndarray, to_state: np.ndarray) -> np.ndarray:
        """
        Create mapping matrix between consciousness layers.

        Args:
            from_state: Source consciousness state
            to_state: Target consciousness state

        Returns:
            Mapping matrix
        """
        # Create a mapping that transforms from_state to to_state
        # This represents how meta-consciousness transforms base consciousness

        # Simple linear mapping for now
        mapping = np.outer(to_state, from_state.conj())

        # Normalize
        mapping /= np.trace(mapping) if np.trace(mapping) != 0 else 1.0

        return mapping

    def _detect_self_reference_loop(self, state_a: np.ndarray, state_b: np.ndarray) -> float:
        """
        Detect self-reference loops between consciousness states.

        Args:
            state_a: First consciousness state
            state_b: Second consciousness state

        Returns:
            Loop strength (0 = no loop, 1 = strong loop)
        """
        # Self-reference loop detection via correlation
        correlation = np.abs(np.corrcoef(state_a, state_b)[0, 1])

        # Also check for fixed points (states that map to themselves)
        difference = np.linalg.norm(state_a - state_b)
        fixed_point_measure = 1.0 / (1.0 + difference)

        # Combine measures
        loop_strength = (correlation + fixed_point_measure) / 2.0

        return loop_strength

    def evolve_self_observing_consciousness(self, base_consciousness: np.ndarray,
                                          evolution_steps: int = 5) -> Dict[str, Any]:
        """
        Evolve self-observing consciousness over time.

        Args:
            base_consciousness: Initial base consciousness
            evolution_steps: Number of evolution steps

        Returns:
            Evolution results
        """
        start_time = time.time()

        evolution_trajectory = []
        hierarchy_evolution = []

        current_base = base_consciousness.copy()

        for step in range(evolution_steps):
            # Build meta-hierarchy
            hierarchy = self.build_meta_consciousness_hierarchy(current_base)
            hierarchy_evolution.append(hierarchy)

            # Extract key metrics
            step_metrics = {
                "step": step,
                "base_norm": np.linalg.norm(hierarchy["base"]),
                "meta_layers": len(hierarchy["layers"]),
                "self_reference_loops": len(hierarchy["self_reference_loops"]),
                "hierarchy_depth": self.recursion_depth
            }

            # Add layer norms
            for layer_name, layer_state in hierarchy["layers"].items():
                step_metrics[f"{layer_name}_norm"] = np.linalg.norm(layer_state)

            evolution_trajectory.append(step_metrics)

            # Evolve base consciousness based on meta-feedback
            if hierarchy["layers"]:
                # Use highest meta-layer to influence base consciousness
                highest_meta = list(hierarchy["layers"].values())[-1]
                feedback = self.self_observation_strength * (highest_meta - current_base)
                current_base += 0.1 * feedback  # Small feedback step

                # Normalize
                current_base /= np.linalg.norm(current_base) if np.linalg.norm(current_base) > 0 else 1.0

        computation_time = time.time() - start_time
        self.total_computation_time += computation_time
        self.observation_count += 1

        # Store in history
        self.observation_layers.append({
            "timestamp": datetime.now(),
            "base_consciousness": base_consciousness.copy(),
            "hierarchy_evolution": hierarchy_evolution,
            "final_hierarchy": hierarchy,
            "computation_time": computation_time
        })

        # Keep history bounded
        if len(self.observation_layers) > 5:
            self.observation_layers = self.observation_layers[-5:]

        result = {
            "evolution_trajectory": evolution_trajectory,
            "final_hierarchy": hierarchy,
            "hierarchy_evolution": hierarchy_evolution,
            "total_evolution_steps": evolution_steps,
            "recursion_depth": self.recursion_depth,
            "self_observation_strength": self.self_observation_strength,
            "computation_time": computation_time
        }

        return result

    def compute_self_observation_phi_contribution(self) -> float:
        """Compute Phi contribution from self-observing consciousness."""
        if not self.observation_layers:
            return 0.0

        latest_observation = self.observation_layers[-1]

        # Phi contribution based on:
        # 1. Meta-hierarchy complexity
        # 2. Self-reference loop strength
        # 3. Recursion depth achieved

        final_hierarchy = latest_observation["final_hierarchy"]

        hierarchy_complexity = len(final_hierarchy["layers"]) * 0.1
        recursion_achievement = self.recursion_depth * 0.05

        loop_strength = 0.0
        if final_hierarchy["self_reference_loops"]:
            loop_strength = np.mean([loop["loop_strength"] for loop in final_hierarchy["self_reference_loops"]])

        phi_contribution = (hierarchy_complexity + recursion_achievement + loop_strength) / 3.0

        return phi_contribution

    def reset_self_observation_state(self):
        """Reset self-observing consciousness state."""
        self.base_consciousness = np.random.normal(0.0, 0.1, self.consciousness_dims)
        self.observation_layers = []
        self.meta_mapping = {}
        self.self_reference_loops = []
        self.observation_count = 0
        self.total_computation_time = 0.0


def main():
    """Test the self-observing consciousness module."""
    print("🧠 SELF-OBSERVING CONSCIOUSNESS")
    print("=" * 35)

    self_obs = SelfObservingConsciousness(
        consciousness_dims=8, recursion_depth=3, self_observation_strength=0.4
    )

    print(f"Consciousness dimensions: {self_obs.consciousness_dims}")
    print(f"Recursion depth: {self_obs.recursion_depth}")
    print(f"Self-observation strength: {self_obs.self_observation_strength}")
    print()

    # Test self-observing consciousness
    base_consciousness = np.random.normal(0.0, 0.1, 8)

    print("Testing self-observing consciousness evolution...")

    result = self_obs.evolve_self_observing_consciousness(base_consciousness, evolution_steps=4)

    print("Evolution Results:")
    print(f"  Evolution steps: {result['total_evolution_steps']}")
    print(f"  Recursion depth: {result['recursion_depth']}")
    print(f"  Meta-layers created: {len(result['final_hierarchy']['layers'])}")
    print(f"  Self-reference loops: {len(result['final_hierarchy']['self_reference_loops'])}")
    print(f"  Phi contribution: {self_obs.compute_self_observation_phi_contribution():.4f}")
    print()

    # Show hierarchy
    print("Final Meta-Hierarchy:")
    print(f"  Base consciousness norm: {np.linalg.norm(result['final_hierarchy']['base']):.4f}")
    for layer_name, layer_state in result['final_hierarchy']['layers'].items():
        print(f"  {layer_name}: norm = {np.linalg.norm(layer_state):.4f}")


if __name__ == "__main__":
    main()