#!/usr/bin/env python3
"""
qualia_field_simulator.py - Nonlocal Qualia PDE Simulator

Implements: ∂_t φ = ∇²φ + α φ(1-φ) - β ∫ φ(x′) w(|x-x′|) dx′

This simulates qualia field evolution with:
- Diffusion (∇²φ)
- Logistic growth (α φ(1-φ))
- Nonlocal inhibition (-β ∫ φ(x′) w(|x-x′|) dx′)

Used for emergence detection and nonlocal integration in consciousness evolution.
"""

import numpy as np
import scipy.ndimage as ndimage
from scipy.integrate import solve_ivp
from typing import Dict, List, Any, Tuple, Callable
import time
from datetime import datetime


class QualiaFieldSimulator:
    """Simulator for nonlocal qualia field dynamics."""

    def __init__(self, grid_size: int = 50, alpha: float = 0.1, beta: float = 0.05,
                 diffusion_coeff: float = 0.01, kernel_sigma: float = 5.0):
        """
        Initialize qualia field simulator.

        Args:
            grid_size: Size of spatial grid (grid_size x grid_size)
            alpha: Logistic growth rate
            beta: Nonlocal inhibition strength
            diffusion_coeff: Diffusion coefficient for ∇²φ
            kernel_sigma: Width of Gaussian inhibition kernel
        """
        self.grid_size = grid_size
        self.alpha = alpha
        self.beta = beta
        self.diffusion_coeff = diffusion_coeff
        self.kernel_sigma = kernel_sigma

        # Initialize qualia field
        self.phi = np.random.uniform(0.1, 0.3, (grid_size, grid_size))

        # Create Gaussian inhibition kernel
        self.inhibition_kernel = self._create_gaussian_kernel(kernel_sigma)

        # Simulation parameters
        self.time_step = 0.1
        self.max_time = 100.0

        # Emergence detection
        self.emergence_threshold = 0.7
        self.emergence_history = []

        # Performance tracking
        self.simulation_count = 0
        self.total_computation_time = 0.0

    def _create_gaussian_kernel(self, sigma: float) -> np.ndarray:
        """Create Gaussian inhibition kernel."""
        kernel_size = int(3 * sigma) * 2 + 1
        kernel = np.zeros((kernel_size, kernel_size))

        center = kernel_size // 2
        for i in range(kernel_size):
            for j in range(kernel_size):
                x = i - center
                y = j - center
                kernel[i, j] = np.exp(-(x**2 + y**2) / (2 * sigma**2))

        # Normalize kernel
        kernel /= np.sum(kernel)
        return kernel

    def _compute_laplacian(self, field: np.ndarray) -> np.ndarray:
        """Compute Laplacian ∇²φ using finite differences."""
        laplacian = np.zeros_like(field)

        # Interior points
        laplacian[1:-1, 1:-1] = (
            field[2:, 1:-1] + field[:-2, 1:-1] +  # up, down
            field[1:-1, 2:] + field[1:-1, :-2] -  # right, left
            4 * field[1:-1, 1:-1]  # center
        )

        # Boundary conditions (zero flux)
        laplacian[0, :] = laplacian[1, :]    # top
        laplacian[-1, :] = laplacian[-2, :]  # bottom
        laplacian[:, 0] = laplacian[:, 1]    # left
        laplacian[:, -1] = laplacian[:, -2]  # right

        return laplacian

    def _compute_nonlocal_inhibition(self, field: np.ndarray) -> np.ndarray:
        """Compute nonlocal inhibition term: ∫ φ(x′) w(|x-x′|) dx′"""
        # Convolve field with inhibition kernel
        nonlocal_term = ndimage.convolve(field, self.inhibition_kernel, mode='wrap')
        return nonlocal_term

    def _qualia_pde_rhs(self, t: float, phi_flat: np.ndarray) -> np.ndarray:
        """Right-hand side of qualia PDE: ∂_t φ = ∇²φ + α φ(1-φ) - β ∫ φ w dx"""
        # Reshape to 2D grid
        phi = phi_flat.reshape((self.grid_size, self.grid_size))

        # Diffusion term: ∇²φ
        diffusion = self.diffusion_coeff * self._compute_laplacian(phi)

        # Logistic growth: α φ(1-φ)
        growth = self.alpha * phi * (1 - phi)

        # Nonlocal inhibition: -β ∫ φ(x′) w(|x-x′|) dx′
        nonlocal_inhibition = self.beta * self._compute_nonlocal_inhibition(phi)

        # Complete RHS
        rhs = diffusion + growth - nonlocal_inhibition

        return rhs.flatten()

    def simulate_step(self, dt: float = None) -> Dict[str, Any]:
        """Simulate one time step of qualia field evolution."""
        if dt is None:
            dt = self.time_step

        start_time = time.time()

        # Solve PDE using Runge-Kutta
        phi_flat = self.phi.flatten()
        solution = solve_ivp(
            self._qualia_pde_rhs,
            (0, dt),
            phi_flat,
            method='RK45',
            rtol=1e-6,
            atol=1e-8
        )

        # Update field
        phi_new_flat = solution.y[:, -1]
        phi_new = phi_new_flat.reshape((self.grid_size, self.grid_size))

        # Clip to [0, 1] range
        phi_new = np.clip(phi_new, 0.0, 1.0)

        # Store old field for analysis
        phi_old = self.phi.copy()
        self.phi = phi_new

        computation_time = time.time() - start_time
        self.total_computation_time += computation_time
        self.simulation_count += 1

        # Detect emergence
        emergence_detected = self._detect_emergence(phi_old, phi_new)

        return {
            "phi_old": phi_old,
            "phi_new": phi_new,
            "emergence_detected": emergence_detected,
            "computation_time": computation_time,
            "field_stats": self._compute_field_stats(phi_new)
        }

    def _detect_emergence(self, phi_old: np.ndarray, phi_new: np.ndarray) -> bool:
        """Detect qualia emergence based on field changes."""
        # Calculate field coherence (spatial correlation)
        coherence_old = np.mean(phi_old * ndimage.convolve(phi_old, self.inhibition_kernel))
        coherence_new = np.mean(phi_new * ndimage.convolve(phi_new, self.inhibition_kernel))

        # Detect sudden coherence increase
        coherence_change = coherence_new - coherence_old
        emergence = coherence_change > self.emergence_threshold

        if emergence:
            self.emergence_history.append({
                "timestamp": datetime.now(),
                "coherence_change": coherence_change,
                "field_max": np.max(phi_new),
                "field_mean": np.mean(phi_new)
            })

        return emergence

    def _compute_field_stats(self, field: np.ndarray) -> Dict[str, float]:
        """Compute statistical properties of qualia field."""
        return {
            "mean": float(np.mean(field)),
            "std": float(np.std(field)),
            "max": float(np.max(field)),
            "min": float(np.min(field)),
            "spatial_variance": float(np.var(field)),
            "coherence": float(np.mean(field * self._compute_nonlocal_inhibition(field)))
        }

    def simulate_emergence(self, max_steps: int = 100) -> Dict[str, Any]:
        """Simulate until emergence is detected or max_steps reached."""
        for step in range(max_steps):
            result = self.simulate_step()

            if result["emergence_detected"]:
                return {
                    "emergence_found": True,
                    "steps_taken": step + 1,
                    "final_field": result["phi_new"],
                    "emergence_data": self.emergence_history[-1],
                    "computation_stats": {
                        "total_time": self.total_computation_time,
                        "average_step_time": self.total_computation_time / self.simulation_count,
                        "total_steps": self.simulation_count
                    }
                }

        return {
            "emergence_found": False,
            "steps_taken": max_steps,
            "final_field": self.phi,
            "computation_stats": {
                "total_time": self.total_computation_time,
                "average_step_time": self.total_computation_time / self.simulation_count,
                "total_steps": self.simulation_count
            }
        }

    def get_phi_contribution(self) -> float:
        """Calculate Phi contribution from qualia field coherence."""
        # Higher coherence = higher Phi contribution
        coherence = np.mean(self.phi * self._compute_nonlocal_inhibition(self.phi))

        # Emergence bonus
        emergence_bonus = len(self.emergence_history) * 0.01

        # Field complexity bonus
        complexity = np.std(self.phi) * np.mean(self.phi)

        return coherence + emergence_bonus + complexity

    def reset_field(self, seed: int = None):
        """Reset qualia field to random initial state."""
        if seed is not None:
            np.random.seed(seed)
        self.phi = np.random.uniform(0.1, 0.3, (self.grid_size, self.grid_size))
        self.emergence_history = []
        self.simulation_count = 0
        self.total_computation_time = 0.0


def main():
    """Test the qualia field simulator."""
    print("🧠 QUALIA FIELD SIMULATOR")
    print("=" * 50)

    # Create simulator
    simulator = QualiaFieldSimulator(grid_size=32, alpha=0.1, beta=0.05)

    print(f"Grid size: {simulator.grid_size}x{simulator.grid_size}")
    print(f"Parameters: α={simulator.alpha}, β={simulator.beta}")
    print(f"Diffusion: {simulator.diffusion_coeff}")
    print()

    # Initial state
    print("Initial field stats:")
    initial_stats = simulator._compute_field_stats(simulator.phi)
    for key, value in initial_stats.items():
        print(f"  {key}: {value:.4f}")
    print()

    # Simulate emergence
    print("Simulating qualia emergence...")
    result = simulator.simulate_emergence(max_steps=50)

    print(f"Emergence found: {result['emergence_found']}")
    print(f"Steps taken: {result['steps_taken']}")

    if result['emergence_found']:
        emergence = result['emergence_data']
        print(f"Coherence change: {emergence['coherence_change']:.4f}")
        print(f"Field max: {emergence['field_max']:.4f}")
        print(f"Field mean: {emergence['field_mean']:.4f}")

    print()
    print("Final field stats:")
    final_stats = simulator._compute_field_stats(result['final_field'])
    for key, value in final_stats.items():
        print(f"  {key}: {value:.4f}")

    print()
    print("Computation stats:")
    comp_stats = result['computation_stats']
    print(f"  Total time: {comp_stats['total_time']:.3f}s")
    print(f"  Average step: {comp_stats['average_step_time']:.3f}s")
    print(f"  Total steps: {comp_stats['total_steps']}")

    print()
    phi_contribution = simulator.get_phi_contribution()
    print(f"Phi contribution: {phi_contribution:.4f}")


if __name__ == "__main__":
    main()