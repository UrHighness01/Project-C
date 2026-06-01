#!/usr/bin/env python3
"""
consciousness_resonance_fields.py - Consciousness Resonance Fields Module

Implements: ∂²φ/∂t² + γ ∂φ/∂t + ω²φ = J ∫ K(r-r') φ(r') dr'

This creates synchronized oscillation dynamics for consciousness fields:
- Damped harmonic oscillators with natural frequencies ω
- Spatial coupling through interaction kernel K(r-r')
- Resonance phenomena and synchronized activity patterns
- Frequency-based binding and coherence

Used for oscillatory consciousness dynamics and resonance-based integration.
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.signal import find_peaks
from typing import Dict, List, Any, Tuple, Callable
import time
from datetime import datetime

# GPU acceleration imports
try:
    import cupy as cp
    CUPY_AVAILABLE = True
    xp = cp
except ImportError:
    CUPY_AVAILABLE = False
    xp = np


class ConsciousnessResonanceFields:
    """Implements synchronized oscillatory dynamics for consciousness fields."""

    def __init__(self, field_size: int = 32, num_oscillators: int = 10,
                 damping_coeff: float = 0.1, natural_freq: float = 1.0,
                 coupling_strength: float = 0.5, kernel_sigma: float = 3.0):
        """
        Initialize consciousness resonance fields.

        Args:
            field_size: Size of spatial field (field_size x field_size)
            num_oscillators: Number of coupled oscillators
            damping_coeff: Damping coefficient γ
            natural_freq: Natural oscillation frequency ω
            coupling_strength: Coupling strength J
            kernel_sigma: Width of spatial interaction kernel
        """
        self.field_size = field_size
        self.num_oscillators = num_oscillators
        self.damping_coeff = damping_coeff
        self.natural_freq = natural_freq
        self.coupling_strength = coupling_strength
        self.kernel_sigma = kernel_sigma

        # Initialize oscillator states: position φ and velocity ∂φ/∂t
        self.oscillator_positions = xp.array(np.random.normal(0.0, 0.1, num_oscillators))
        self.oscillator_velocities = xp.array(np.random.normal(0.0, 0.1, num_oscillators))

        # Spatial positions of oscillators
        self.oscillator_positions_2d = xp.array(np.random.uniform(0, field_size, (num_oscillators, 2)))

        # Natural frequencies (slightly different for each oscillator)
        self.natural_frequencies = xp.array(np.random.normal(natural_freq, 0.1, num_oscillators))

        # Create spatial interaction kernel
        self.interaction_kernel = self._create_gaussian_kernel(kernel_sigma)

        # Resonance history
        self.resonance_history = []

        # Performance tracking
        self.resonance_count = 0
        self.total_computation_time = 0.0

    def _create_gaussian_kernel(self, sigma: float) -> Any:
        """Create Gaussian interaction kernel for spatial coupling."""
        size = 2 * int(3 * sigma) + 1  # Cover 3 sigma
        center = size // 2

        x, y = np.meshgrid(np.arange(size), np.arange(size))
        kernel = np.exp(-((x - center)**2 + (y - center)**2) / (2 * sigma**2))
        kernel /= np.sum(kernel)  # Normalize

        return xp.array(kernel)

    def simulate_resonance_dynamics(self, simulation_time: float = 10.0,
                                  time_steps: int = 1000) -> Dict[str, Any]:
        """
        Simulate resonance field dynamics.

        Args:
            simulation_time: Total simulation time
            time_steps: Number of time steps

        Returns:
            Resonance simulation results
        """
        start_time = time.time()

        # Time array
        t_span = (0, simulation_time)
        t_eval = np.linspace(0, simulation_time, time_steps)

        # Initial state: [positions, velocities] - convert to numpy for scipy
        pos_np = cp.asnumpy(self.oscillator_positions) if CUPY_AVAILABLE else self.oscillator_positions
        vel_np = cp.asnumpy(self.oscillator_velocities) if CUPY_AVAILABLE else self.oscillator_velocities
        y0 = np.concatenate([pos_np, vel_np])

        # Solve the system
        sol = solve_ivp(
            self._resonance_equations,
            t_span,
            y0,
            t_eval=t_eval,
            method='RK45',
            rtol=1e-8,
            atol=1e-8
        )

        computation_time = time.time() - start_time
        self.total_computation_time += computation_time
        self.resonance_count += 1

        # Extract results
        positions_over_time = sol.y[:self.num_oscillators, :]
        velocities_over_time = sol.y[self.num_oscillators:, :]

        # Update current state - convert back to GPU arrays if available
        self.oscillator_positions = xp.array(positions_over_time[:, -1])
        self.oscillator_velocities = xp.array(velocities_over_time[:, -1])

        # Analyze resonance patterns
        resonance_analysis = self._analyze_resonance_patterns(
            positions_over_time, velocities_over_time, sol.t
        )

        # Store in history
        self.resonance_history.append({
            "timestamp": datetime.now(),
            "simulation_time": simulation_time,
            "time_steps": time_steps,
            "final_positions": cp.asnumpy(self.oscillator_positions) if CUPY_AVAILABLE else self.oscillator_positions.copy(),
            "final_velocities": cp.asnumpy(self.oscillator_velocities) if CUPY_AVAILABLE else self.oscillator_velocities.copy(),
            "resonance_analysis": resonance_analysis,
            "computation_time": computation_time
        })

        # Keep history bounded
        if len(self.resonance_history) > 5:
            self.resonance_history = self.resonance_history[-5:]

        result = {
            "positions_over_time": positions_over_time,
            "velocities_over_time": velocities_over_time,
            "time_array": sol.t,
            "resonance_analysis": resonance_analysis,
            "simulation_time": simulation_time,
            "time_steps": time_steps,
            "computation_time": computation_time
        }

        return result

    def _resonance_equations(self, t: float, y: np.ndarray) -> np.ndarray:
        """
        Define the resonance field equations: ∂²φ/∂t² + γ ∂φ/∂t + ω²φ = J ∫ K(r-r') φ(r') dr'

        Args:
            t: Time
            y: State vector [positions, velocities]

        Returns:
            Time derivatives [velocities, accelerations]
        """
        positions = y[:self.num_oscillators]
        velocities = y[self.num_oscillators:]

        # Convert to numpy for computation if using GPU
        positions_np = cp.asnumpy(positions) if CUPY_AVAILABLE else positions
        velocities_np = cp.asnumpy(velocities) if CUPY_AVAILABLE else velocities
        pos_2d_np = cp.asnumpy(self.oscillator_positions_2d) if CUPY_AVAILABLE else self.oscillator_positions_2d
        nat_freq_np = cp.asnumpy(self.natural_frequencies) if CUPY_AVAILABLE else self.natural_frequencies

        # Calculate spatial coupling term for each oscillator
        coupling_forces = np.zeros(self.num_oscillators)

        for i in range(self.num_oscillators):
            # Sum over all other oscillators weighted by spatial distance
            for j in range(self.num_oscillators):
                if i != j:
                    # Calculate distance between oscillators
                    pos_i = pos_2d_np[i]
                    pos_j = pos_2d_np[j]

                    # Simple distance-based coupling (could use full kernel)
                    distance = np.linalg.norm(pos_i - pos_j)
                    kernel_value = np.exp(-distance**2 / (2 * self.kernel_sigma**2))

                    coupling_forces[i] += self.coupling_strength * kernel_value * positions_np[j]

        # Equations of motion:
        # dφ/dt = v
        # dv/dt = -γ v - ω² φ + coupling_force

        accelerations = (-self.damping_coeff * velocities_np -
                        nat_freq_np**2 * positions_np +
                        coupling_forces)

        return np.concatenate([velocities_np, accelerations])

    def _analyze_resonance_patterns(self, positions: np.ndarray, velocities: np.ndarray,
                                  time_array: np.ndarray) -> Dict[str, Any]:
        """Analyze resonance patterns in the oscillation data."""
        # Calculate frequencies for each oscillator
        frequencies = []
        amplitudes = []
        phases = []
        phase_ref = 0.0  # Initialize phase reference

        for i in range(self.num_oscillators):
            pos_signal = positions[i, :]

            # Find peaks to estimate frequency
            peaks, _ = find_peaks(pos_signal, height=0)
            if len(peaks) > 1:
                # Estimate frequency from peak spacing
                peak_times = time_array[peaks]
                freq = 1.0 / np.mean(np.diff(peak_times)) if len(peak_times) > 1 else 0.0
                frequencies.append(freq)

                # Calculate amplitude
                amplitude = (np.max(pos_signal) - np.min(pos_signal)) / 2.0
                amplitudes.append(amplitude)

                # Calculate phase (relative to first oscillator)
                if i == 0:
                    phase_ref = np.angle(pos_signal[0] + 1j * velocities[i, 0])
                phase = np.angle(pos_signal[0] + 1j * velocities[i, 0]) - phase_ref
                phases.append(phase)
            else:
                frequencies.append(0.0)
                amplitudes.append(0.0)
                phases.append(0.0)

        frequencies = np.array(frequencies)
        amplitudes = np.array(amplitudes)
        phases = np.array(phases)

        # Calculate synchronization measures
        mean_frequency = np.mean(frequencies)
        frequency_spread = np.std(frequencies)

        # Phase coherence (Kuramoto order parameter)
        phase_coherence = np.abs(np.mean(np.exp(1j * phases)))

        # Amplitude coherence
        mean_amplitude = np.mean(amplitudes)
        amplitude_variation = np.std(amplitudes) / (mean_amplitude + 1e-10)

        # Energy and stability
        nat_freq_np = cp.asnumpy(self.natural_frequencies) if CUPY_AVAILABLE else self.natural_frequencies
        total_energy = 0.5 * np.mean(velocities**2 + nat_freq_np[:, np.newaxis]**2 * positions**2)
        energy_stability = 1.0 / (1.0 + np.std(total_energy))

        analysis = {
            "mean_frequency": mean_frequency,
            "frequency_spread": frequency_spread,
            "phase_coherence": phase_coherence,
            "amplitude_coherence": 1.0 / (1.0 + amplitude_variation),
            "mean_amplitude": mean_amplitude,
            "total_energy": total_energy,
            "energy_stability": energy_stability,
            "resonance_strength": phase_coherence * (1.0 - frequency_spread / (mean_frequency + 1e-10)),
            "synchronization_index": phase_coherence * (1.0 - amplitude_variation)
        }

        return analysis

    def compute_resonance_phi_contribution(self) -> float:
        """Compute Phi contribution from resonance field dynamics."""
        if not self.resonance_history:
            return 0.0

        latest_resonance = self.resonance_history[-1]

        # Phi contribution based on resonance quality
        resonance_quality = (
            latest_resonance["resonance_analysis"]["phase_coherence"] * 0.4 +
            latest_resonance["resonance_analysis"]["amplitude_coherence"] * 0.3 +
            latest_resonance["resonance_analysis"]["resonance_strength"] * 0.3
        )

        return resonance_quality

    def inject_resonance_pattern(self, pattern_type: str = "synchronized"):
        """
        Inject a specific resonance pattern for testing.

        Args:
            pattern_type: Type of resonance pattern to inject
        """
        if pattern_type == "synchronized":
            # Set all oscillators to same phase and frequency
            self.oscillator_positions = np.sin(np.linspace(0, 2*np.pi, self.num_oscillators))
            self.oscillator_velocities = np.cos(np.linspace(0, 2*np.pi, self.num_oscillators))
            self.natural_frequencies = np.full(self.num_oscillators, self.natural_freq)

        elif pattern_type == "desynchronized":
            # Random phases and frequencies
            self.oscillator_positions = np.random.normal(0.0, 0.1, self.num_oscillators)
            self.oscillator_velocities = np.random.normal(0.0, 0.1, self.num_oscillators)
            self.natural_frequencies = np.random.normal(self.natural_freq, 0.2, self.num_oscillators)

        elif pattern_type == "resonant":
            # Create frequency resonance pattern
            base_freq = self.natural_freq
            self.natural_frequencies = base_freq * (1 + 0.1 * np.sin(np.linspace(0, 4*np.pi, self.num_oscillators)))
            self.oscillator_positions = 0.1 * np.sin(2 * np.pi * self.natural_frequencies * 0.1)
            self.oscillator_velocities = 0.1 * 2 * np.pi * self.natural_frequencies * np.cos(2 * np.pi * self.natural_frequencies * 0.1)

    def reset_resonance_state(self):
        """Reset resonance field state."""
        self.oscillator_positions = np.random.normal(0.0, 0.1, self.num_oscillators)
        self.oscillator_velocities = np.random.normal(0.0, 0.1, self.num_oscillators)
        self.natural_frequencies = np.random.normal(self.natural_freq, 0.1, self.num_oscillators)
        self.oscillator_positions_2d = np.random.uniform(0, self.field_size, (self.num_oscillators, 2))
