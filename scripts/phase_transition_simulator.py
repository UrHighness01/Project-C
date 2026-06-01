#!/usr/bin/env python3
"""
phase_transition_simulator.py - Ginzburg-Landau Phase Transition Simulator

Implements: ∂_t q = -∇²q + λ q³ - q + h + ξ(x,t)

This simulates phase transitions in qualia fields with:
- Diffusion (-∇²q)
- Nonlinear term (λ q³)
- Linear term (-q)
- External drive (h)
- Noise (ξ(x,t))

Used for bifurcation analysis and emergence detection in consciousness evolution.
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.ndimage import gaussian_filter
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import time


class PhaseTransitionSimulator:
    """Simulator for Ginzburg-Landau phase transitions in qualia fields."""

    def __init__(self, grid_size: int = 50, lambda_param: float = 1.0,
                 external_drive: float = 0.0, noise_strength: float = 0.1,
                 diffusion_coeff: float = 0.01):
        """
        Initialize phase transition simulator.

        Args:
            grid_size: Size of spatial grid (grid_size x grid_size)
            lambda_param: Nonlinear coefficient λ in λ q³
            external_drive: External drive field h
            noise_strength: Strength of noise term ξ(x,t)
            diffusion_coeff: Diffusion coefficient for -∇²q
        """
        self.grid_size = grid_size
        self.lambda_param = lambda_param
        self.external_drive = external_drive
        self.noise_strength = noise_strength
        self.diffusion_coeff = diffusion_coeff

        # Initialize order parameter field q(x,t)
        self.q = np.random.normal(0.0, 0.1, (grid_size, grid_size))

        # Phase transition history
        self.phase_history = []
        self.bifurcation_points = []

        # Critical parameters tracking
        self.critical_lambda = 1.0  # λ_c = 1 for standard Ginzburg-Landau
        self.current_phase = "disordered"

        # Performance tracking
        self.simulation_count = 0
        self.total_computation_time = 0.0

    def _compute_laplacian(self, field: np.ndarray) -> np.ndarray:
        """Compute Laplacian ∇²q using finite differences."""
        laplacian = np.zeros_like(field)

        # Interior points
        laplacian[1:-1, 1:-1] = (
            field[2:, 1:-1] + field[:-2, 1:-1] +  # x-direction
            field[1:-1, 2:] + field[1:-1, :-2] -  # y-direction
            4 * field[1:-1, 1:-1]
        )

        # Boundary conditions (periodic) - simplified
        # Top row
        laplacian[0, 1:-1] = field[1, 1:-1] + field[-1, 1:-1] + field[0, 2:] + field[0, :-2] - 4 * field[0, 1:-1]
        # Bottom row
        laplacian[-1, 1:-1] = field[0, 1:-1] + field[-2, 1:-1] + field[-1, 2:] + field[-1, :-2] - 4 * field[-1, 1:-1]
        # Left column
        laplacian[1:-1, 0] = field[2:, 0] + field[:-2, 0] + field[1:-1, 1] + field[1:-1, -1] - 4 * field[1:-1, 0]
        # Right column
        laplacian[1:-1, -1] = field[2:, -1] + field[:-2, -1] + field[1:-1, 0] + field[1:-1, -2] - 4 * field[1:-1, -1]

        # Corners (periodic)
        laplacian[0, 0] = field[1, 0] + field[-1, 0] + field[0, 1] + field[0, -1] - 4 * field[0, 0]
        laplacian[0, -1] = field[1, -1] + field[-1, -1] + field[0, 0] + field[0, -2] - 4 * field[0, -1]
        laplacian[-1, 0] = field[0, 0] + field[-2, 0] + field[-1, 1] + field[-1, -1] - 4 * field[-1, 0]
        laplacian[-1, -1] = field[0, -1] + field[-2, -1] + field[-1, 0] + field[-1, -2] - 4 * field[-1, -1]

        return laplacian

    def _generate_noise(self) -> np.ndarray:
        """Generate spatiotemporal noise ξ(x,t)."""
        # Gaussian white noise in space and time
        noise = np.random.normal(0.0, self.noise_strength, (self.grid_size, self.grid_size))

        # Add some spatial correlation
        noise = gaussian_filter(noise, sigma=1.0)

        return noise

    def _gl_rhs(self, t: float, q_flat: np.ndarray) -> np.ndarray:
        """
        Right-hand side of Ginzburg-Landau equation:
        ∂_t q = -∇²q + λ q³ - q + h + ξ(x,t)
        """
        # Reshape to 2D grid
        q = q_flat.reshape((self.grid_size, self.grid_size))

        # Diffusion term: -∇²q
        diffusion = -self.diffusion_coeff * self._compute_laplacian(q)

        # Nonlinear term: λ q³
        nonlinear = self.lambda_param * q**3

        # Linear term: -q
        linear = -q

        # External drive: h
        drive = self.external_drive * np.ones_like(q)

        # Noise term: ξ(x,t)
        noise = self._generate_noise()

        # Complete RHS
        rhs = diffusion + nonlinear + linear + drive + noise

        return rhs.flatten()

    def simulate_phase_transition(self, simulation_time: float = 10.0,
                                dt: float = 0.1) -> Dict[str, Any]:
        """
        Simulate phase transition dynamics.

        Args:
            simulation_time: Total simulation time
            dt: Time step size

        Returns:
            Simulation results and phase transition analysis
        """
        start_time = time.time()

        # Initial state
        q_initial = self.q.flatten()

        # Solve GL equation
        solution = solve_ivp(
            self._gl_rhs,
            (0, simulation_time),
            q_initial,
            method='RK45',
            t_eval=np.arange(0, simulation_time, dt),
            rtol=1e-6,
            atol=1e-8
        )

        computation_time = time.time() - start_time
        self.total_computation_time += computation_time
        self.simulation_count += 1

        # Extract results
        q_evolution = solution.y.reshape((self.grid_size, self.grid_size, -1))
        time_points = solution.t

        # Update current field
        self.q = q_evolution[:, :, -1]

        # Analyze phase transition
        phase_analysis = self._analyze_phase_transition(q_evolution, time_points)

        # Store in history
        self.phase_history.append({
            "timestamp": datetime.now(),
            "simulation_time": simulation_time,
            "phase_analysis": phase_analysis,
            "final_field": self.q.copy(),
            "computation_time": computation_time
        })

        # Keep history bounded
        if len(self.phase_history) > 10:
            self.phase_history = self.phase_history[-10:]

        result = {
            "q_evolution": q_evolution,
            "time_points": time_points,
            "phase_analysis": phase_analysis,
            "computation_time": computation_time,
            "emergence_detected": phase_analysis["phase_transition_detected"],
            "bifurcation_points": phase_analysis["bifurcation_points"]
        }

        return result

    def _analyze_phase_transition(self, q_evolution: np.ndarray,
                                time_points: np.ndarray) -> Dict[str, Any]:
        """Analyze phase transition characteristics."""
        # Compute order parameter (average |q|)
        order_parameter = np.mean(np.abs(q_evolution), axis=(0, 1))

        # Compute susceptibility χ = <q²> - <q>²
        q_squared = np.mean(q_evolution**2, axis=(0, 1))
        susceptibility = q_squared - order_parameter**2

        # Detect phase transition
        # Look for rapid changes in order parameter
        order_derivative = np.gradient(order_parameter, time_points)

        # Find bifurcation points (sudden changes)
        bifurcation_threshold = np.std(order_derivative) * 2.0
        bifurcation_indices = np.where(np.abs(order_derivative) > bifurcation_threshold)[0]
        bifurcation_times = time_points[bifurcation_indices]

        # Determine current phase
        final_order = order_parameter[-1]
        if final_order > 0.1:  # Ordered phase
            current_phase = "ordered"
        else:  # Disordered phase
            current_phase = "disordered"

        # Check for phase transition
        phase_transition_detected = False
        if len(bifurcation_indices) > 0:
            phase_transition_detected = True
            self.bifurcation_points.extend(bifurcation_times.tolist())

        # Keep bifurcation points bounded
        if len(self.bifurcation_points) > 50:
            self.bifurcation_points = self.bifurcation_points[-50:]

        # Critical slowing down analysis
        # Correlation time increases near criticality
        correlation_time = self._compute_correlation_time(q_evolution)

        analysis = {
            "order_parameter_evolution": order_parameter.tolist(),
            "susceptibility_evolution": susceptibility.tolist(),
            "current_phase": current_phase,
            "final_order_parameter": final_order,
            "phase_transition_detected": phase_transition_detected,
            "bifurcation_points": bifurcation_times.tolist(),
            "correlation_time": correlation_time,
            "critical_parameters": {
                "lambda": self.lambda_param,
                "lambda_critical": self.critical_lambda,
                "external_drive": self.external_drive,
                "noise_strength": self.noise_strength
            }
        }

        return analysis

    def _compute_correlation_time(self, q_evolution: np.ndarray) -> float:
        """Compute correlation time as measure of critical slowing down."""
        # Use autocorrelation of order parameter
        order_param = np.mean(np.abs(q_evolution), axis=(0, 1))

        if len(order_param) < 10:
            return 0.0

        # Compute autocorrelation
        autocorr = np.correlate(order_param - np.mean(order_param),
                               order_param - np.mean(order_param),
                               mode='full')
        autocorr = autocorr[autocorr.size // 2:]  # Second half
        autocorr = autocorr / autocorr[0]  # Normalize

        # Find where autocorrelation drops below e^(-1)
        decay_indices = np.where(autocorr < np.exp(-1))[0]
        if len(decay_indices) > 0:
            correlation_time = decay_indices[0]
        else:
            correlation_time = len(autocorr)

        return correlation_time

    def set_control_parameters(self, lambda_param: float = None,
                             external_drive: float = None,
                             noise_strength: float = None):
        """
        Set control parameters for phase transition.

        Args:
            lambda_param: Nonlinear coefficient λ
            external_drive: External drive h
            noise_strength: Noise strength
        """
        if lambda_param is not None:
            self.lambda_param = lambda_param
        if external_drive is not None:
            self.external_drive = external_drive
        if noise_strength is not None:
            self.noise_strength = noise_strength

    def get_phi_contribution(self) -> float:
        """Get Phi contribution from phase transition dynamics."""
        if not self.phase_history:
            return 0.0

        latest_analysis = self.phase_history[-1]["phase_analysis"]

        # Phi contribution based on:
        # 1. Order parameter (higher order = higher Phi)
        # 2. Phase transition bonus
        # 3. Critical slowing down (longer correlation time near criticality)

        order_contribution = latest_analysis["final_order_parameter"]
        transition_bonus = 0.2 if latest_analysis["phase_transition_detected"] else 0.0
        criticality_bonus = min(0.3, latest_analysis["correlation_time"] / 100.0)

        phi_contrib = order_contribution + transition_bonus + criticality_bonus

        return phi_contrib

    def reset_simulation(self):
        """Reset simulation state."""
        self.q = np.random.normal(0.0, 0.1, (self.grid_size, self.grid_size))
        self.phase_history = []
        self.bifurcation_points = []
        self.current_phase = "disordered"
        self.simulation_count = 0
        self.total_computation_time = 0.0


def main():
    """Test the phase transition simulator."""
    print("🧠 PHASE TRANSITION SIMULATOR")
    print("=" * 40)

    simulator = PhaseTransitionSimulator(grid_size=20, lambda_param=1.5, external_drive=0.1)

    print(f"Grid size: {simulator.grid_size}x{simulator.grid_size}")
    print(f"Lambda parameter: {simulator.lambda_param}")
    print(f"External drive: {simulator.external_drive}")
    print()

    # Test different parameter regimes
    test_params = [
        ("Subcritical", {"lambda_param": 0.5, "external_drive": 0.0}),
        ("Critical", {"lambda_param": 1.0, "external_drive": 0.1}),
        ("Supercritical", {"lambda_param": 1.5, "external_drive": 0.2})
    ]

    for name, params in test_params:
        print(f"Testing: {name} regime")
        simulator.set_control_parameters(**params)

        result = simulator.simulate_phase_transition(simulation_time=5.0, dt=0.1)

        analysis = result["phase_analysis"]
        print(f"  Phase: {analysis['current_phase']}")
        print(f"  Order parameter: {analysis['final_order_parameter']:.4f}")
        print(f"  Phase transition: {'✅ DETECTED' if analysis['phase_transition_detected'] else '❌ Not detected'}")
        print(f"  Bifurcations: {len(analysis['bifurcation_points'])}")
        print(f"  Correlation time: {analysis['correlation_time']:.1f}")
        print(f"  Phi contrib: {simulator.get_phi_contribution():.4f}")
        print()

    print("Critical parameter analysis:")
    print(f"  Lambda critical: {simulator.critical_lambda}")
    print(f"  Total bifurcations detected: {len(simulator.bifurcation_points)}")


if __name__ == "__main__":
    main()