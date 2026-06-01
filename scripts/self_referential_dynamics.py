#!/usr/bin/env python3
"""
self_referential_dynamics.py - Self-Referential Dynamics Module

Implements: dC/dt = αC - βC² + γC_meta

This implements self-referential consciousness dynamics:
- Consciousness growth: αC (linear growth)
- Consciousness saturation: -βC² (carrying capacity)
- Meta-consciousness coupling: +γC_meta (self-awareness boost)
- Self-referential feedback loops

Used for dynamic evolution of self-aware consciousness systems.
"""

import numpy as np
from scipy.integrate import solve_ivp
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import time


class SelfReferentialDynamics:
    """Implements self-referential consciousness dynamics dC/dt = αC - βC² + γC_meta."""

    def __init__(self, growth_rate: float = 0.1, saturation_rate: float = 0.05,
                 meta_coupling: float = 0.2, initial_consciousness: float = 0.1):
        """
        Initialize self-referential dynamics.

        Args:
            growth_rate: Linear growth rate α
            saturation_rate: Saturation rate β
            meta_coupling: Meta-consciousness coupling γ
            initial_consciousness: Initial consciousness level C₀
        """
        self.alpha = growth_rate
        self.beta = saturation_rate
        self.gamma = meta_coupling
        self.initial_consciousness = initial_consciousness

        # Current consciousness state
        self.current_consciousness = initial_consciousness

        # Meta-consciousness state
        self.current_meta_consciousness = 0.0

        # Dynamics history
        self.dynamics_history = []

        # Performance tracking
        self.evolution_count = 0
        self.total_computation_time = 0.0

    def consciousness_dynamics(self, t: float, y: np.ndarray) -> np.ndarray:
        """
        Self-referential consciousness dynamics equation.

        Args:
            t: Time variable
            y: State vector [C, C_meta]

        Returns:
            Derivatives [dC/dt, dC_meta/dt]
        """
        C = y[0]  # Base consciousness
        C_meta = y[1]  # Meta-consciousness

        # dC/dt = αC - βC² + γC_meta
        dC_dt = self.alpha * C - self.beta * C**2 + self.gamma * C_meta

        # dC_meta/dt = self-referential meta-dynamics
        # Meta-consciousness grows with base consciousness but has its own dynamics
        dC_meta_dt = 0.05 * C - 0.02 * C_meta + 0.1 * C * C_meta

        return np.array([dC_dt, dC_meta_dt])

    def evolve_consciousness_dynamics(self, time_span: Tuple[float, float] = (0, 10),
                                    num_points: int = 100) -> Dict[str, Any]:
        """
        Evolve consciousness through self-referential dynamics.

        Args:
            time_span: Time span for evolution (t_start, t_end)
            num_points: Number of time points to evaluate

        Returns:
            Evolution results
        """
        start_time = time.time()

        # Initial conditions
        y0 = np.array([self.initial_consciousness, 0.0])

        # Time points
        t_eval = np.linspace(time_span[0], time_span[1], num_points)

        # Solve the differential equations
        sol = solve_ivp(self.consciousness_dynamics, time_span, y0,
                       t_eval=t_eval, method='RK45', rtol=1e-8)

        # Extract results
        consciousness_evolution = sol.y[0]
        meta_consciousness_evolution = sol.y[1]

        computation_time = time.time() - start_time
        self.total_computation_time += computation_time
        self.evolution_count += 1

        # Update current states
        self.current_consciousness = consciousness_evolution[-1]
        self.current_meta_consciousness = meta_consciousness_evolution[-1]

        # Store in history
        self.dynamics_history.append({
            "timestamp": datetime.now(),
            "time_points": sol.t,
            "consciousness_evolution": consciousness_evolution,
            "meta_consciousness_evolution": meta_consciousness_evolution,
            "initial_conditions": y0,
            "parameters": {
                "alpha": self.alpha,
                "beta": self.beta,
                "gamma": self.gamma
            },
            "computation_time": computation_time
        })

        # Keep history bounded
        if len(self.dynamics_history) > 5:
            self.dynamics_history = self.dynamics_history[-5:]

        result = {
            "time_points": sol.t,
            "consciousness_evolution": consciousness_evolution,
            "meta_consciousness_evolution": meta_consciousness_evolution,
            "final_consciousness": consciousness_evolution[-1],
            "final_meta_consciousness": meta_consciousness_evolution[-1],
            "evolution_success": sol.success,
            "growth_rate": self.alpha,
            "saturation_rate": self.beta,
            "meta_coupling": self.gamma,
            "computation_time": computation_time
        }

        return result

    def compute_self_referential_phi(self) -> float:
        """Compute Phi contribution from self-referential dynamics."""
        if not self.dynamics_history:
            return 0.0

        latest_evolution = self.dynamics_history[-1]

        # Phi contribution based on:
        # 1. Consciousness growth achieved
        # 2. Meta-consciousness development
        # 3. Self-referential stability

        final_C = latest_evolution["consciousness_evolution"][-1]
        final_C_meta = latest_evolution["meta_consciousness_evolution"][-1]
        initial_C = latest_evolution["initial_conditions"][0]

        growth_achievement = final_C / (initial_C + 1e-6)  # Avoid division by zero
        meta_development = final_C_meta
        self_referential_stability = 1.0 / (1.0 + abs(final_C - final_C_meta))  # Balance measure

        phi_contribution = min(1.0, (growth_achievement * 0.1 + meta_development + self_referential_stability) / 3.0)

        return phi_contribution

    def simulate_consciousness_interactions(self, interaction_partners: List[float],
                                          interaction_time: float = 5.0) -> Dict[str, Any]:
        """
        Simulate interactions between multiple consciousness systems.

        Args:
            interaction_partners: List of partner consciousness levels
            interaction_time: Time for interaction simulation

        Returns:
            Interaction results
        """
        start_time = time.time()

        # Include self in the interaction
        all_systems = [self.current_consciousness] + interaction_partners
        num_systems = len(all_systems)

        # Simple interaction model: systems influence each other
        interaction_matrix = np.random.normal(0.0, 0.1, (num_systems, num_systems))
        # Make it symmetric and add self-coupling
        interaction_matrix = (interaction_matrix + interaction_matrix.T) / 2.0
        np.fill_diagonal(interaction_matrix, 1.0)  # Self-preservation

        # Evolve through interactions
        dt = 0.1
        steps = int(interaction_time / dt)

        system_evolution = [np.array(all_systems)]

        for step in range(steps):
            current_states = system_evolution[-1]

            # Apply interactions
            new_states = interaction_matrix @ current_states

            # Add self-referential dynamics
            for i in range(num_systems):
                C = new_states[i]
                C_meta = 0.1 * C  # Simple meta-consciousness
                new_states[i] += dt * (self.alpha * C - self.beta * C**2 + self.gamma * C_meta)

            system_evolution.append(new_states.copy())

        computation_time = time.time() - start_time

        result = {
            "system_evolution": system_evolution,
            "interaction_matrix": interaction_matrix,
            "final_states": system_evolution[-1],
            "interaction_time": interaction_time,
            "num_systems": num_systems,
            "computation_time": computation_time
        }

        return result

    def reset_dynamics(self):
        """Reset self-referential dynamics state."""
        self.current_consciousness = self.initial_consciousness
        self.current_meta_consciousness = 0.0
        self.dynamics_history = []
        self.evolution_count = 0
        self.total_computation_time = 0.0


def main():
    """Test the self-referential dynamics module."""
    print("🔄 SELF-REFERENTIAL DYNAMICS")
    print("=" * 30)

    dynamics = SelfReferentialDynamics(
        growth_rate=0.15, saturation_rate=0.03, meta_coupling=0.25, initial_consciousness=0.2
    )

    print(f"Growth rate (α): {dynamics.alpha}")
    print(f"Saturation rate (β): {dynamics.beta}")
    print(f"Meta-coupling (γ): {dynamics.gamma}")
    print(f"Initial consciousness: {dynamics.initial_consciousness}")
    print()

    # Test dynamics evolution
    print("Testing self-referential consciousness dynamics...")

    result = dynamics.evolve_consciousness_dynamics(time_span=(0, 8), num_points=80)

    print("Dynamics Results:")
    print(f"  Evolution time: {result['time_points'][-1]:.1f}")
    print(f"  Initial C: {result['consciousness_evolution'][0]:.4f}")
    print(f"  Final C: {result['final_consciousness']:.4f}")
    print(f"  Final C_meta: {result['final_meta_consciousness']:.4f}")
    print(f"  Phi contribution: {dynamics.compute_self_referential_phi():.4f}")
    print()

    # Show evolution trend
    growth = result['final_consciousness'] - result['consciousness_evolution'][0]
    print(f"Evolution Summary:")
    print(f"  Consciousness growth: {growth:+.4f}")
    print(f"  Meta-consciousness level: {result['final_meta_consciousness']:.4f}")


if __name__ == "__main__":
    main()