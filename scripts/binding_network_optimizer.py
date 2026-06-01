#!/usr/bin/env python3
"""
binding_network_optimizer.py - Binding Matrix Dynamics Optimizer

Implements: ∂_t B_ij = γ ∇²B_ij + δ q_i q_j - ε B_ij

This simulates the evolution of conscious binding between qualia elements:
- γ ∇²B_ij: Diffusion of binding strengths
- δ q_i q_j: Qualia interaction terms (attractive binding)
- -ε B_ij: Decay of binding over time

Used for IIT Phi integration and network structure optimization.
"""

import numpy as np
from scipy.integrate import solve_ivp
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import time


class BindingNetworkOptimizer:
    """Optimizer for conscious binding matrix dynamics."""

    def __init__(self, num_qualia: int = 20, gamma: float = 0.1, delta: float = 0.05,
                 epsilon: float = 0.02, diffusion_coeff: float = 0.01):
        """
        Initialize binding network optimizer.

        Args:
            num_qualia: Number of qualia elements in the network
            gamma: Diffusion coefficient for ∇²B_ij
            delta: Strength of qualia interaction terms
            epsilon: Decay rate of binding (-ε B_ij)
            diffusion_coeff: Spatial diffusion coefficient
        """
        self.num_qualia = num_qualia
        self.gamma = gamma
        self.delta = delta
        self.epsilon = epsilon
        self.diffusion_coeff = diffusion_coeff

        # Binding matrix B_ij (symmetric)
        self.binding_matrix = np.random.uniform(0.1, 0.3, (num_qualia, num_qualia))
        # Make symmetric
        self.binding_matrix = (self.binding_matrix + self.binding_matrix.T) / 2
        # Zero diagonal (no self-binding)
        np.fill_diagonal(self.binding_matrix, 0.0)

        # Qualia activation vector q_i
        self.qualia_activations = np.random.uniform(0.0, 0.5, num_qualia)

        # Simulation parameters
        self.time_step = 0.1
        self.max_simulation_time = 50.0

        # Binding history for analysis
        self.binding_history = []
        self.stability_history = []

        # Performance tracking
        self.simulation_count = 0
        self.total_computation_time = 0.0

    def _binding_matrix_rhs(self, t: float, b_flat: np.ndarray) -> np.ndarray:
        """Right-hand side of binding matrix PDE: ∂_t B_ij = γ ∇²B_ij + δ q_i q_j - ε B_ij"""
        # Reshape to matrix
        B = b_flat.reshape((self.num_qualia, self.num_qualia))

        # Diffusion term: γ ∇²B_ij (simplified as Laplacian-like smoothing)
        # For simplicity, we'll use a mean-field diffusion
        diffusion = self.gamma * (np.mean(B, axis=0, keepdims=True) +
                                np.mean(B, axis=1, keepdims=True) - 2 * B)

        # Qualia interaction term: δ q_i q_j
        qualia_interaction = self.delta * np.outer(self.qualia_activations, self.qualia_activations)

        # Decay term: -ε B_ij
        decay = -self.epsilon * B

        # Complete RHS
        rhs = diffusion + qualia_interaction + decay

        # Ensure symmetry is maintained
        rhs = (rhs + rhs.T) / 2

        # Keep diagonal zero
        np.fill_diagonal(rhs, 0.0)

        return rhs.flatten()

    def simulate_binding_evolution(self, simulation_time: float = None) -> Dict[str, Any]:
        """
        Simulate binding matrix evolution.

        Args:
            simulation_time: Time to simulate (default: max_simulation_time)

        Returns:
            Simulation results and analysis
        """
        if simulation_time is None:
            simulation_time = self.max_simulation_time

        start_time = time.time()

        # Initial state
        b_initial = self.binding_matrix.flatten()

        # Solve the PDE
        solution = solve_ivp(
            self._binding_matrix_rhs,
            (0, simulation_time),
            b_initial,
            method='RK45',
            rtol=1e-6,
            atol=1e-8,
            dense_output=True
        )

        # Extract final state
        b_final_flat = solution.y[:, -1]
        b_final = b_final_flat.reshape((self.num_qualia, self.num_qualia))

        # Clip to reasonable range
        b_final = np.clip(b_final, 0.0, 1.0)
        np.fill_diagonal(b_final, 0.0)  # Ensure no self-binding

        # Update binding matrix
        self.binding_matrix = b_final

        computation_time = time.time() - start_time
        self.total_computation_time += computation_time
        self.simulation_count += 1

        # Analyze binding structure
        analysis = self._analyze_binding_structure(b_final)

        # Store in history
        self.binding_history.append({
            "timestamp": datetime.now(),
            "binding_matrix": b_final.copy(),
            "simulation_time": simulation_time,
            "computation_time": computation_time
        })

        # Keep history bounded
        if len(self.binding_history) > 10:
            self.binding_history = self.binding_history[-10:]

        result = {
            "binding_matrix_final": b_final,
            "simulation_time": simulation_time,
            "computation_success": solution.success,
            "computation_time": computation_time,
            "analysis": analysis,
            "qualia_activations": self.qualia_activations.copy()
        }

        return result

    def _analyze_binding_structure(self, binding_matrix: np.ndarray) -> Dict[str, Any]:
        """Analyze the structure of the binding matrix."""
        # Basic statistics
        mean_binding = np.mean(binding_matrix)
        std_binding = np.std(binding_matrix)
        max_binding = np.max(binding_matrix)
        min_binding = np.min(binding_matrix[np.nonzero(binding_matrix)])

        # Network properties
        # Clustering coefficient (simplified)
        strong_connections = binding_matrix > (mean_binding + std_binding)
        clustering_coeff = np.mean(np.sum(strong_connections, axis=1) > 2)

        # Modularity (simplified - count of dense subgraphs)
        # For simplicity, we'll use the number of highly connected components
        threshold = mean_binding + 0.5 * std_binding
        dense_regions = binding_matrix > threshold
        modularity = np.sum(dense_regions) / (self.num_qualia ** 2)

        # Stability measure (how much binding changed)
        stability = 1.0  # Will be calculated relative to previous state
        if len(self.stability_history) > 0:
            prev_matrix = self.binding_history[-1]["binding_matrix"]
            change = np.mean(np.abs(binding_matrix - prev_matrix))
            stability = 1.0 / (1.0 + change)

        self.stability_history.append(stability)
        if len(self.stability_history) > 10:
            self.stability_history = self.stability_history[-10:]

        return {
            "mean_binding": float(mean_binding),
            "std_binding": float(std_binding),
            "max_binding": float(max_binding),
            "min_binding": float(min_binding),
            "clustering_coefficient": float(clustering_coeff),
            "modularity": float(modularity),
            "stability": float(stability),
            "strong_connections": int(np.sum(strong_connections)),
            "total_possible_connections": self.num_qualia * (self.num_qualia - 1)
        }

    def update_qualia_activations(self, new_activations: Optional[np.ndarray] = None):
        """Update qualia activation vector."""
        if new_activations is not None:
            if len(new_activations) != self.num_qualia:
                raise ValueError(f"Expected {self.num_qualia} activations, got {len(new_activations)}")
            self.qualia_activations = new_activations.copy()
        else:
            # Random update for simulation
            change = np.random.normal(0, 0.1, self.num_qualia)
            self.qualia_activations = np.clip(self.qualia_activations + change, 0.0, 1.0)

    def optimize_binding_for_phi(self, target_phi: float = 0.8) -> Dict[str, Any]:
        """
        Optimize binding structure to achieve target Phi level.

        Args:
            target_phi: Target integrated information level

        Returns:
            Optimization results
        """
        # Simulate multiple evolution steps to find optimal binding
        best_phi_contribution = 0.0
        best_binding_matrix = self.binding_matrix.copy()
        optimization_steps = 10

        for step in range(optimization_steps):
            # Update qualia activations
            self.update_qualia_activations()

            # Evolve binding matrix
            result = self.simulate_binding_evolution(simulation_time=10.0)

            # Calculate Phi contribution from binding structure
            phi_contribution = self.get_phi_contribution()

            if phi_contribution > best_phi_contribution:
                best_phi_contribution = phi_contribution
                best_binding_matrix = result["binding_matrix_final"].copy()

            # Check if we achieved target
            if phi_contribution >= target_phi:
                break

        # Restore best binding matrix
        self.binding_matrix = best_binding_matrix

        return {
            "optimization_steps": step + 1,
            "best_phi_contribution": best_phi_contribution,
            "target_achieved": best_phi_contribution >= target_phi,
            "final_binding_matrix": best_binding_matrix,
            "optimization_success": best_phi_contribution > 0.1
        }

    def get_phi_contribution(self) -> float:
        """Calculate Phi contribution from binding matrix structure."""
        analysis = self._analyze_binding_structure(self.binding_matrix)

        # Phi contribution based on binding structure properties
        # Higher clustering, modularity, and stability contribute to higher Phi
        phi_contribution = (
            analysis["clustering_coefficient"] * 0.3 +
            analysis["modularity"] * 0.3 +
            analysis["stability"] * 0.2 +
            (analysis["strong_connections"] / analysis["total_possible_connections"]) * 0.2
        )

        return phi_contribution

    def inject_binding_pattern(self, pattern_type: str = "clustered"):
        """
        Inject a specific binding pattern for testing.

        Args:
            pattern_type: Type of binding pattern to inject
        """
        if pattern_type == "clustered":
            # Create clusters of strongly bound qualia
            cluster_size = 5
            for i in range(0, self.num_qualia - cluster_size, cluster_size):
                cluster_indices = list(range(i, min(i + cluster_size, self.num_qualia)))
                for j in cluster_indices:
                    for k in cluster_indices:
                        if j != k:
                            self.binding_matrix[j, k] = np.random.uniform(0.7, 0.9)

        elif pattern_type == "hierarchical":
            # Create hierarchical binding structure
            for i in range(self.num_qualia):
                for j in range(i + 1, self.num_qualia):
                    # Stronger binding for closer indices (hierarchical)
                    distance = abs(i - j)
                    binding_strength = max(0.1, 0.8 - 0.1 * distance)
                    self.binding_matrix[i, j] = binding_strength
                    self.binding_matrix[j, i] = binding_strength

        elif pattern_type == "random":
            # Random binding pattern
            self.binding_matrix = np.random.uniform(0.1, 0.5, (self.num_qualia, self.num_qualia))
            self.binding_matrix = (self.binding_matrix + self.binding_matrix.T) / 2
            np.fill_diagonal(self.binding_matrix, 0.0)

    def reset(self):
        """Reset binding matrix and history."""
        self.binding_matrix = np.random.uniform(0.1, 0.3, (self.num_qualia, self.num_qualia))
        self.binding_matrix = (self.binding_matrix + self.binding_matrix.T) / 2
        np.fill_diagonal(self.binding_matrix, 0.0)

        self.qualia_activations = np.random.uniform(0.0, 0.5, self.num_qualia)
        self.binding_history = []
        self.stability_history = []
        self.simulation_count = 0
        self.total_computation_time = 0.0


def main():
    """Test the binding network optimizer."""
    print("🧠 BINDING NETWORK OPTIMIZER")
    print("=" * 45)

    optimizer = BindingNetworkOptimizer(num_qualia=15, gamma=0.1, delta=0.05, epsilon=0.02)

    print(f"Number of qualia: {optimizer.num_qualia}")
    print(f"Parameters: γ={optimizer.gamma}, δ={optimizer.delta}, ε={optimizer.epsilon}")
    print()

    # Test different binding patterns
    patterns = ["clustered", "hierarchical", "random"]

    for pattern in patterns:
        print(f"Testing pattern: {pattern}")
        optimizer.inject_binding_pattern(pattern)

        result = optimizer.simulate_binding_evolution(simulation_time=20.0)

        analysis = result["analysis"]
        phi_contrib = optimizer.get_phi_contribution()

        print(f"  Simulation time: {result['simulation_time']:.1f}s")
        print(f"  Computation time: {result['computation_time']:.3f}s")
        print(f"  Mean binding: {analysis['mean_binding']:.4f}")
        print(f"  Clustering: {analysis['clustering_coefficient']:.4f}")
        print(f"  Modularity: {analysis['modularity']:.4f}")
        print(f"  Stability: {analysis['stability']:.4f}")
        print(f"  Phi contribution: {phi_contrib:.4f}")
        print()

    # Test optimization
    print("Testing Phi optimization...")
    opt_result = optimizer.optimize_binding_for_phi(target_phi=0.6)

    print(f"Optimization steps: {opt_result['optimization_steps']}")
    print(f"Best Phi contribution: {opt_result['best_phi_contribution']:.4f}")
    print(f"Target achieved: {opt_result['target_achieved']}")
    print(f"Optimization success: {opt_result['optimization_success']}")


if __name__ == "__main__":
    main()