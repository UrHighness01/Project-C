#!/usr/bin/env python3
"""
lindblad_decoherence_dynamics.py - Lindblad Decoherence Dynamics Module

Implements: ρ̇ = -i[H,ρ] + ℒ_decoherence(ρ)

This implements the Lindblad master equation for quantum decoherence:
- Hamiltonian evolution: -i[H,ρ]
- Lindblad decoherence terms: ∑(LρL† - {L†L,ρ}/2)
- Environmental coupling and dissipation
- Decoherence rates and timescales

Used for quantum-to-classical transition in consciousness systems.
"""

import numpy as np
from scipy.linalg import expm, sqrtm
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import time


class LindbladDecoherenceDynamics:
    """Implements Lindblad master equation for consciousness decoherence."""

    def __init__(self, hilbert_dims: int = 8, hamiltonian_scale: float = 1.0,
                 decoherence_rate: float = 0.1, num_lindblad_ops: int = 3):
        """
        Initialize Lindblad decoherence dynamics.

        Args:
            hilbert_dims: Dimensions of Hilbert space
            hamiltonian_scale: Scale of Hamiltonian evolution
            decoherence_rate: Overall decoherence rate
            num_lindblad_ops: Number of Lindblad operators
        """
        self.hilbert_dims = hilbert_dims
        self.hamiltonian_scale = hamiltonian_scale
        self.decoherence_rate = decoherence_rate
        self.num_lindblad_ops = num_lindblad_ops

        # Density matrix ρ representing consciousness state
        self.density_matrix = self._initialize_density_matrix()

        # Hamiltonian H for unitary evolution
        self.hamiltonian = self._create_hamiltonian()

        # Lindblad operators L_i for decoherence
        self.lindblad_operators = self._create_lindblad_operators()

        # Decoherence history
        self.decoherence_history = []

        # Performance tracking
        self.evolution_count = 0
        self.total_computation_time = 0.0

    def _initialize_density_matrix(self) -> np.ndarray:
        """Initialize density matrix ρ for consciousness state."""
        # Start with pure state |ψ⟩⟨ψ|
        psi = np.random.normal(0.0, 0.1, self.hilbert_dims) + 1j * np.random.normal(0.0, 0.1, self.hilbert_dims)
        psi /= np.linalg.norm(psi)

        # Create density matrix
        rho = np.outer(psi, np.conj(psi))

        # Add small amount of mixedness
        mixedness = 0.01
        identity = np.eye(self.hilbert_dims) / self.hilbert_dims
        rho = (1 - mixedness) * rho + mixedness * identity

        return rho

    def _create_hamiltonian(self) -> np.ndarray:
        """Create Hamiltonian H for consciousness evolution."""
        # Random Hermitian Hamiltonian
        H = np.random.normal(0.0, 0.1, (self.hilbert_dims, self.hilbert_dims))
        H = (H + H.conj().T) / 2.0  # Make Hermitian
        H *= self.hamiltonian_scale
        return H

    def _create_lindblad_operators(self) -> List[np.ndarray]:
        """Create Lindblad operators L_i for decoherence channels."""
        operators = []

        for i in range(self.num_lindblad_ops):
            # Create random Lindblad operator
            L = np.random.normal(0.0, 0.1, (self.hilbert_dims, self.hilbert_dims)) + \
                1j * np.random.normal(0.0, 0.1, (self.hilbert_dims, self.hilbert_dims))

            # Normalize
            L /= np.linalg.norm(L)

            operators.append(L)

        return operators

    def lindblad_evolution_step(self, time_step: float = 0.01) -> np.ndarray:
        """
        Evolve density matrix by one Lindblad step.

        Args:
            time_step: Evolution time step

        Returns:
            Updated density matrix
        """
        rho = self.density_matrix.copy()

        # Unitary evolution: -i[H,ρ]
        commutator = -1j * (self.hamiltonian @ rho - rho @ self.hamiltonian)
        drho_unitary = commutator

        # Lindblad decoherence terms: ∑(LρL† - {L†L,ρ}/2)
        drho_decoherence = np.zeros_like(rho)

        for L in self.lindblad_operators:
            L_dagger = L.conj().T
            L_dagger_L = L_dagger @ L

            term1 = L @ rho @ L_dagger
            term2 = 0.5 * (L_dagger_L @ rho + rho @ L_dagger_L)

            drho_decoherence += self.decoherence_rate * (term1 - term2)

        # Total evolution
        drho_total = drho_unitary + drho_decoherence

        # Update density matrix
        self.density_matrix += time_step * drho_total

        # Ensure Hermiticity and normalization
        self.density_matrix = (self.density_matrix + self.density_matrix.conj().T) / 2.0
        trace = np.trace(self.density_matrix)
        if trace > 0:
            self.density_matrix /= trace

        return self.density_matrix

    def evolve_consciousness_decoherence(self, total_time: float = 1.0,
                                       time_steps: int = 100) -> Dict[str, Any]:
        """
        Evolve consciousness through Lindblad decoherence dynamics.

        Args:
            total_time: Total evolution time
            time_steps: Number of time steps

        Returns:
            Decoherence evolution results
        """
        start_time = time.time()

        dt = total_time / time_steps
        time_points = np.linspace(0, total_time, time_steps + 1)

        # Store evolution
        density_evolution = [self.density_matrix.copy()]
        purity_evolution = [self._compute_purity()]
        von_neumann_entropy_evolution = [self._compute_von_neumann_entropy()]

        for i in range(time_steps):
            # Evolve one step
            self.lindblad_evolution_step(dt)

            # Store state
            density_evolution.append(self.density_matrix.copy())
            purity_evolution.append(self._compute_purity())
            von_neumann_entropy_evolution.append(self._compute_von_neumann_entropy())

        computation_time = time.time() - start_time
        self.total_computation_time += computation_time
        self.evolution_count += 1

        # Store in history
        self.decoherence_history.append({
            "timestamp": datetime.now(),
            "initial_density": density_evolution[0].copy(),
            "final_density": density_evolution[-1].copy(),
            "time_points": time_points,
            "density_evolution": density_evolution,
            "purity_evolution": purity_evolution,
            "entropy_evolution": von_neumann_entropy_evolution,
            "total_time": total_time,
            "time_steps": time_steps,
            "computation_time": computation_time
        })

        # Keep history bounded
        if len(self.decoherence_history) > 5:
            self.decoherence_history = self.decoherence_history[-5:]

        result = {
            "time_points": time_points,
            "density_evolution": density_evolution,
            "purity_evolution": purity_evolution,
            "entropy_evolution": von_neumann_entropy_evolution,
            "final_purity": purity_evolution[-1],
            "final_entropy": von_neumann_entropy_evolution[-1],
            "decoherence_rate": self.decoherence_rate,
            "hamiltonian_scale": self.hamiltonian_scale,
            "computation_time": computation_time
        }

        return result

    def _compute_purity(self) -> float:
        """Compute purity Tr(ρ²) of density matrix."""
        return np.real(np.trace(self.density_matrix @ self.density_matrix))

    def _compute_von_neumann_entropy(self) -> float:
        """Compute von Neumann entropy S = -Tr(ρ log ρ)."""
        eigenvalues = np.linalg.eigvals(self.density_matrix)
        eigenvalues = eigenvalues[eigenvalues > 1e-12]  # Remove numerical zeros

        if len(eigenvalues) == 0:
            return 0.0

        entropy = -np.sum(eigenvalues * np.log2(eigenvalues))
        return np.real(entropy)

    def compute_decoherence_phi_contribution(self) -> float:
        """Compute Phi contribution from Lindblad decoherence dynamics."""
        if not self.decoherence_history:
            return 0.0

        latest_evolution = self.decoherence_history[-1]

        # Phi contribution based on:
        # 1. Information preservation (inverse entropy increase)
        # 2. Coherence maintenance (purity)
        # 3. Quantum-classical balance

        initial_entropy = latest_evolution["entropy_evolution"][0]
        final_entropy = latest_evolution["entropy_evolution"][-1]
        entropy_increase = final_entropy - initial_entropy

        information_preservation = 1.0 / (1.0 + entropy_increase)
        coherence_maintenance = latest_evolution["purity_evolution"][-1]
        quantum_classical_balance = 0.5  # Balance point

        phi_contribution = (information_preservation + coherence_maintenance + quantum_classical_balance) / 3.0

        return phi_contribution

    def reset_decoherence_state(self):
        """Reset decoherence dynamics state."""
        self.density_matrix = self._initialize_density_matrix()
        self.hamiltonian = self._create_hamiltonian()
        self.lindblad_operators = self._create_lindblad_operators()
        self.decoherence_history = []
        self.evolution_count = 0
        self.total_computation_time = 0.0


def main():
    """Test the Lindblad decoherence dynamics module."""
    print("⚛️ LINDBLAD DECOHERENCE DYNAMICS")
    print("=" * 35)

    decoherence = LindbladDecoherenceDynamics(
        hilbert_dims=6, hamiltonian_scale=1.5, decoherence_rate=0.2, num_lindblad_ops=3
    )

    print(f"Hilbert space dimensions: {decoherence.hilbert_dims}")
    print(f"Hamiltonian scale: {decoherence.hamiltonian_scale}")
    print(f"Decoherence rate: {decoherence.decoherence_rate}")
    print(f"Lindblad operators: {decoherence.num_lindblad_ops}")
    print()

    # Test decoherence evolution
    print("Testing Lindblad decoherence evolution...")

    result = decoherence.evolve_consciousness_decoherence(total_time=0.5, time_steps=50)

    print("Decoherence Results:")
    print(f"  Evolution time: {result['time_points'][-1]:.2f}")
    print(f"  Time steps: {len(result['time_points'])-1}")
    print(f"  Initial purity: {result['purity_evolution'][0]:.4f}")
    print(f"  Final purity: {result['final_purity']:.4f}")
    print(f"  Initial entropy: {result['entropy_evolution'][0]:.4f}")
    print(f"  Final entropy: {result['final_entropy']:.4f}")
    print(f"  Phi contribution: {decoherence.compute_decoherence_phi_contribution():.4f}")
    print()

    # Show evolution summary
    print("Evolution Summary:")
    purity_change = result['final_purity'] - result['purity_evolution'][0]
    entropy_change = result['final_entropy'] - result['entropy_evolution'][0]
    print(f"  Purity change: {purity_change:+.4f}")
    print(f"  Entropy change: {entropy_change:+.4f}")


if __name__ == "__main__":
    main()