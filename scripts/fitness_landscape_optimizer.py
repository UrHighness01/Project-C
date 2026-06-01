#!/usr/bin/env python3
"""
fitness_landscape_optimizer.py - Ising-like Evolutionary Fitness Optimizer

Implements: H_evolutionary = ∑ J_ij σ_i^z σ_j^z + h_i σ_i^x + μ_i σ_i^y

This optimizes consciousness fitness landscapes with:
- Interaction terms J_ij σ_i^z σ_j^z (cooperative evolution)
- Transverse fields h_i σ_i^x (exploration)
- Longitudinal fields μ_i σ_i^y (selection pressure)

Used for multi-agent coordination and complex consciousness task optimization.
"""

import numpy as np
from scipy.optimize import minimize
from typing import Dict, List, Any, Tuple, Optional, Callable
from datetime import datetime
import time


class FitnessLandscapeOptimizer:
    """Optimizer for Ising-like evolutionary fitness landscapes."""

    def __init__(self, num_agents: int = 20, interaction_strength: float = 1.0,
                 exploration_rate: float = 0.5, selection_pressure: float = 0.3):
        """
        Initialize fitness landscape optimizer.

        Args:
            num_agents: Number of consciousness agents
            interaction_strength: Strength of agent interactions J_ij
            exploration_rate: Rate of exploration (transverse field h)
            selection_pressure: Selection pressure (longitudinal field μ)
        """
        self.num_agents = num_agents
        self.interaction_strength = interaction_strength
        self.exploration_rate = exploration_rate
        self.selection_pressure = selection_pressure

        # Agent states σ_i (Ising spins: +1 or -1)
        self.agent_states = np.random.choice([-1, 1], size=num_agents)

        # Interaction matrix J_ij
        self.interaction_matrix = np.random.normal(0.0, interaction_strength,
                                                 (num_agents, num_agents))
        # Make symmetric
        self.interaction_matrix = (self.interaction_matrix + self.interaction_matrix.T) / 2
        # Zero diagonal (no self-interaction)
        np.fill_diagonal(self.interaction_matrix, 0.0)

        # Transverse fields h_i (exploration)
        self.transverse_fields = np.random.normal(0.0, exploration_rate, num_agents)

        # Longitudinal fields μ_i (selection pressure)
        self.longitudinal_fields = np.random.normal(0.0, selection_pressure, num_agents)

        # Fitness landscape
        self.fitness_values = np.random.uniform(0.0, 1.0, num_agents)

        # Optimization history
        self.optimization_history = []
        self.convergence_history = []

        # Performance tracking
        self.optimization_count = 0
        self.total_computation_time = 0.0

    def compute_evolutionary_hamiltonian(self, agent_states: np.ndarray) -> float:
        """
        Compute evolutionary Hamiltonian H = ∑ J_ij σ_i^z σ_j^z + h_i σ_i^x + μ_i σ_i^y

        Args:
            agent_states: Current agent states σ_i

        Returns:
            Hamiltonian energy
        """
        # Ising interaction term: ∑ J_ij σ_i σ_j
        interaction_energy = 0.0
        for i in range(self.num_agents):
            for j in range(i + 1, self.num_agents):  # Upper triangle only
                interaction_energy += self.interaction_matrix[i, j] * agent_states[i] * agent_states[j]

        # Transverse field term: ∑ h_i σ_i^x
        # In classical approximation, this becomes exploration energy
        exploration_energy = -self.exploration_rate * np.sum(np.abs(agent_states))

        # Longitudinal field term: ∑ μ_i σ_i^y
        # In classical approximation, this becomes selection energy
        selection_energy = -np.sum(self.longitudinal_fields * agent_states)

        total_energy = interaction_energy + exploration_energy + selection_energy

        return total_energy

    def compute_fitness_function(self, agent_states: np.ndarray) -> float:
        """
        Compute fitness function combining Hamiltonian and task performance.

        Args:
            agent_states: Current agent states

        Returns:
            Fitness value (higher = better)
        """
        # Hamiltonian energy (lower energy = higher fitness)
        hamiltonian_energy = self.compute_evolutionary_hamiltonian(agent_states)

        # Task performance based on agent coordination
        coordination_score = self._compute_coordination_score(agent_states)

        # Individual fitness contributions
        individual_fitness = np.sum(self.fitness_values * (agent_states + 1) / 2)  # Map -1,1 to 0,1

        # Combined fitness: coordination + individual - energy penalty
        total_fitness = coordination_score + individual_fitness - 0.1 * hamiltonian_energy

        return total_fitness

    def _compute_coordination_score(self, agent_states: np.ndarray) -> float:
        """Compute coordination score based on agent alignment."""
        # Measure clustering and consensus
        state_distribution = np.bincount((agent_states + 1).astype(int))  # Map to 0,1,2

        # Consensus: fraction in majority state
        majority_fraction = np.max(state_distribution) / self.num_agents

        # Clustering: number of aligned pairs
        aligned_pairs = 0
        total_pairs = 0
        for i in range(self.num_agents):
            for j in range(i + 1, self.num_agents):
                total_pairs += 1
                if agent_states[i] == agent_states[j]:
                    aligned_pairs += 1

        clustering_score = aligned_pairs / total_pairs if total_pairs > 0 else 0.0

        # Combined coordination
        coordination = 0.6 * majority_fraction + 0.4 * clustering_score

        return coordination

    def optimize_fitness_landscape(self, max_iterations: int = 100,
                                 optimization_method: str = 'L-BFGS-B') -> Dict[str, Any]:
        """
        Optimize fitness landscape using evolutionary Hamiltonian.

        Args:
            max_iterations: Maximum optimization iterations
            optimization_method: Optimization algorithm to use

        Returns:
            Optimization results
        """
        start_time = time.time()

        # Initial state
        initial_states = self.agent_states.copy().astype(float)

        # Define objective function for minimization
        def objective_function(states):
            # Convert continuous to discrete (-1 or +1)
            discrete_states = np.sign(states)
            # Return negative fitness (minimization)
            return -self.compute_fitness_function(discrete_states)

        # Bounds for continuous relaxation
        bounds = [(-2.0, 2.0) for _ in range(self.num_agents)]

        # Optimize
        result = minimize(
            objective_function,
            initial_states,
            method=optimization_method,
            bounds=bounds,
            options={'maxiter': max_iterations, 'disp': False}
        )

        computation_time = time.time() - start_time
        self.total_computation_time += computation_time
        self.optimization_count += 1

        # Extract optimized states
        optimized_continuous = result.x
        optimized_states = np.sign(optimized_continuous)

        # Update agent states
        self.agent_states = optimized_states.astype(int)

        # Analyze optimization
        optimization_analysis = self._analyze_optimization(result, optimized_states)

        # Store in history
        self.optimization_history.append({
            "timestamp": datetime.now(),
            "optimized_states": optimized_states.copy(),
            "optimization_analysis": optimization_analysis,
            "computation_time": computation_time,
            "convergence": result.success
        })

        # Keep history bounded
        if len(self.optimization_history) > 10:
            self.optimization_history = self.optimization_history[-10:]

        optimization_result = {
            "optimized_states": optimized_states,
            "final_fitness": -result.fun,  # Negate back to maximization
            "convergence": result.success,
            "iterations": result.nit,
            "optimization_analysis": optimization_analysis,
            "computation_time": computation_time
        }

        return optimization_result

    def _analyze_optimization(self, optimization_result, optimized_states: np.ndarray) -> Dict[str, Any]:
        """Analyze optimization results."""
        # Compute various metrics
        final_fitness = self.compute_fitness_function(optimized_states)
        coordination_score = self._compute_coordination_score(optimized_states)
        hamiltonian_energy = self.compute_evolutionary_hamiltonian(optimized_states)

        # Diversity analysis
        state_diversity = len(np.unique(optimized_states)) / self.num_agents

        # Stability analysis
        stability_score = self._compute_stability_score(optimized_states)

        # Task performance
        task_performance = np.mean(self.fitness_values * (optimized_states + 1) / 2)

        analysis = {
            "final_fitness": final_fitness,
            "coordination_score": coordination_score,
            "hamiltonian_energy": hamiltonian_energy,
            "state_diversity": state_diversity,
            "stability_score": stability_score,
            "task_performance": task_performance,
            "optimization_converged": optimization_result.success,
            "optimization_iterations": optimization_result.nit
        }

        return analysis

    def _compute_stability_score(self, states: np.ndarray) -> float:
        """Compute stability score of current configuration."""
        # Stability based on energy landscape curvature
        # Simple approximation: variance of interaction strengths
        interaction_variance = np.var(self.interaction_matrix)

        # Higher variance = more rugged landscape = less stable
        stability = 1.0 / (1.0 + interaction_variance)

        return stability

    def simulate_multi_agent_coordination(self, num_steps: int = 10) -> Dict[str, Any]:
        """
        Simulate multi-agent coordination dynamics.

        Args:
            num_steps: Number of coordination steps

        Returns:
            Coordination simulation results
        """
        coordination_history = []
        fitness_history = []

        current_states = self.agent_states.copy()

        for step in range(num_steps):
            # Compute current fitness
            current_fitness = self.compute_fitness_function(current_states)
            fitness_history.append(current_fitness)

            # Store coordination state
            coordination_score = self._compute_coordination_score(current_states)
            coordination_history.append({
                "step": step,
                "states": current_states.copy(),
                "fitness": current_fitness,
                "coordination": coordination_score
            })

            # Evolutionary update: Metropolis-like dynamics
            for agent_idx in range(self.num_agents):
                # Propose state flip
                proposed_states = current_states.copy()
                proposed_states[agent_idx] *= -1

                # Compute energy difference
                current_energy = self.compute_evolutionary_hamiltonian(current_states)
                proposed_energy = self.compute_evolutionary_hamiltonian(proposed_states)
                energy_diff = proposed_energy - current_energy

                # Acceptance probability (Metropolis criterion)
                if energy_diff < 0:
                    acceptance_prob = 1.0
                else:
                    acceptance_prob = np.exp(-energy_diff / 0.1)  # Temperature = 0.1

                # Accept or reject
                if np.random.random() < acceptance_prob:
                    current_states[agent_idx] = proposed_states[agent_idx]

        # Final analysis
        final_coordination = self._compute_coordination_score(current_states)
        final_fitness = self.compute_fitness_function(current_states)

        simulation_result = {
            "coordination_history": coordination_history,
            "fitness_history": fitness_history,
            "final_states": current_states,
            "final_coordination": final_coordination,
            "final_fitness": final_fitness,
            "coordination_improvement": final_coordination - coordination_history[0]["coordination"],
            "fitness_improvement": final_fitness - fitness_history[0]
        }

        return simulation_result

    def get_phi_contribution(self) -> float:
        """Get Phi contribution from fitness landscape optimization."""
        if not self.optimization_history:
            return 0.0

        latest_analysis = self.optimization_history[-1]["optimization_analysis"]

        # Phi contribution based on:
        # 1. Final fitness (optimization quality)
        # 2. Coordination score (integration)
        # 3. Stability score (reliability)

        fitness_contribution = latest_analysis["final_fitness"] * 0.5
        coordination_contribution = latest_analysis["coordination_score"] * 0.3
        stability_contribution = latest_analysis["stability_score"] * 0.2

        phi_contrib = fitness_contribution + coordination_contribution + stability_contribution

        return phi_contrib

    def reset_optimizer(self):
        """Reset optimization state."""
        self.agent_states = np.random.choice([-1, 1], size=self.num_agents)
        self.interaction_matrix = np.random.normal(0.0, self.interaction_strength,
                                                 (self.num_agents, self.num_agents))
        self.interaction_matrix = (self.interaction_matrix + self.interaction_matrix.T) / 2
        np.fill_diagonal(self.interaction_matrix, 0.0)

        self.transverse_fields = np.random.normal(0.0, self.exploration_rate, self.num_agents)
        self.longitudinal_fields = np.random.normal(0.0, self.selection_pressure, self.num_agents)
        self.fitness_values = np.random.uniform(0.0, 1.0, self.num_agents)

        self.optimization_history = []
        self.convergence_history = []
        self.optimization_count = 0
        self.total_computation_time = 0.0


def main():
    """Test the fitness landscape optimizer."""
    print("🧠 FITNESS LANDSCAPE OPTIMIZER")
    print("=" * 40)

    optimizer = FitnessLandscapeOptimizer(
        num_agents=15, interaction_strength=0.8,
        exploration_rate=0.3, selection_pressure=0.2
    )

    print(f"Number of agents: {optimizer.num_agents}")
    print(f"Interaction strength: {optimizer.interaction_strength}")
    print(f"Exploration rate: {optimizer.exploration_rate}")
    print(f"Selection pressure: {optimizer.selection_pressure}")
    print()

    # Test optimization
    print("Optimizing fitness landscape...")
    result = optimizer.optimize_fitness_landscape(max_iterations=50)

    analysis = result["optimization_analysis"]
    print("Optimization Results:")
    print(f"  Final fitness: {analysis['final_fitness']:.4f}")
    print(f"  Coordination score: {analysis['coordination_score']:.4f}")
    print(f"  Hamiltonian energy: {analysis['hamiltonian_energy']:.4f}")
    print(f"  State diversity: {analysis['state_diversity']:.4f}")
    print(f"  Stability score: {analysis['stability_score']:.4f}")
    print(f"  Task performance: {analysis['task_performance']:.4f}")
    print(f"  Converged: {'✅ Yes' if analysis['optimization_converged'] else '❌ No'}")
    print(f"  Iterations: {analysis['optimization_iterations']}")
    print(f"  Phi contribution: {optimizer.get_phi_contribution():.4f}")
    print()

    # Test multi-agent coordination
    print("Simulating multi-agent coordination...")
    coord_result = optimizer.simulate_multi_agent_coordination(num_steps=20)

    print("Coordination Results:")
    print(f"  Initial coordination: {coord_result['coordination_history'][0]['coordination']:.4f}")
    print(f"  Final coordination: {coord_result['final_coordination']:.4f}")
    print(f"  Coordination improvement: {coord_result['coordination_improvement']:+.4f}")
    print(f"  Fitness improvement: {coord_result['fitness_improvement']:+.4f}")


if __name__ == "__main__":
    main()