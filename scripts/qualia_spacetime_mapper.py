#!/usr/bin/env python3
"""
qualia_spacetime_mapper.py - Qualia Spacetime Metric Calculator

Implements: ds² = g_μν dφ^μ dφ^ν

This creates a metric tensor in qualia space:
- φ^μ: Qualia spacetime coordinates
- g_μν: Metric tensor in qualia space
- ds²: Infinitesimal distance in qualia spacetime

Used for temporal binding and narrative continuity in consciousness.
"""

import numpy as np
from scipy.spatial.distance import pdist, squareform
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import time


class QualiaSpacetimeMapper:
    """Mapper for qualia spacetime metric and temporal binding."""

    def __init__(self, num_qualia: int = 10, spacetime_dims: int = 4,
                 temporal_resolution: int = 50):
        """
        Initialize qualia spacetime mapper.

        Args:
            num_qualia: Number of qualia types to track
            spacetime_dims: Number of spacetime dimensions (typically 4: t,x,y,z)
            temporal_resolution: Number of time steps to keep in history
        """
        self.num_qualia = num_qualia
        self.spacetime_dims = spacetime_dims
        self.temporal_resolution = temporal_resolution

        # Qualia spacetime coordinates φ^μ
        # Shape: (num_qualia, spacetime_dims, temporal_resolution)
        self.qualia_coordinates = np.zeros((num_qualia, spacetime_dims, temporal_resolution))

        # Metric tensor g_μν - dynamic based on qualia interactions
        # Shape: (spacetime_dims, spacetime_dims)
        self.metric_tensor = np.eye(spacetime_dims)  # Start with Minkowski-like metric

        # Temporal binding matrix - tracks relationships between qualia over time
        self.temporal_binding = np.zeros((num_qualia, num_qualia))

        # Geodesic distances in qualia space
        self.geodesic_distances = np.zeros((num_qualia, num_qualia))

        # Narrative continuity score
        self.narrative_continuity = 0.0

        # Current time index
        self.current_time = 0

        # Performance tracking
        self.calculation_count = 0
        self.total_calculation_time = 0.0

    def update_qualia_coordinates(self, qualia_states: np.ndarray,
                                temporal_step: float = 1.0) -> None:
        """
        Update qualia spacetime coordinates.

        Args:
            qualia_states: Current qualia activation states (num_qualia,)
            temporal_step: Time step size for coordinate evolution
        """
        # Update time index
        self.current_time = (self.current_time + 1) % self.temporal_resolution

        # Convert qualia states to spacetime coordinates
        # φ^0 = t (time coordinate)
        # φ^i = spatial coordinates derived from qualia patterns
        time_coord = self.current_time * temporal_step

        # Create spatial coordinates from qualia interactions
        # Use PCA-like projection for spatial embedding
        if len(qualia_states) > 1:
            # Simple embedding: use qualia correlations as spatial coordinates
            spatial_coords = np.zeros(self.spacetime_dims - 1)

            # Time-based modulation
            modulation = np.sin(2 * np.pi * self.current_time / 10)  # Periodic modulation

            for i in range(min(len(spatial_coords), len(qualia_states))):
                spatial_coords[i] = qualia_states[i] * (1 + 0.5 * modulation)

            # Normalize spatial coordinates
            if np.linalg.norm(spatial_coords) > 0:
                spatial_coords = spatial_coords / np.linalg.norm(spatial_coords) * 2.0
        else:
            spatial_coords = np.zeros(self.spacetime_dims - 1)

        # Update coordinates for each qualia type
        for q_idx in range(self.num_qualia):
            # Time coordinate (same for all qualia at given time)
            self.qualia_coordinates[q_idx, 0, self.current_time] = time_coord

            # Spatial coordinates (qualia-specific)
            for s_idx in range(1, self.spacetime_dims):
                if s_idx - 1 < len(spatial_coords):
                    # Modulate spatial coordinate by qualia state
                    modulation_factor = qualia_states[q_idx] if q_idx < len(qualia_states) else 0.5
                    self.qualia_coordinates[q_idx, s_idx, self.current_time] = (
                        spatial_coords[s_idx - 1] * modulation_factor
                    )
                else:
                    self.qualia_coordinates[q_idx, s_idx, self.current_time] = 0.0

    def calculate_metric_tensor(self) -> np.ndarray:
        """
        Calculate metric tensor g_μν based on current qualia spacetime structure.

        Returns:
            Metric tensor g_μν
        """
        start_time = time.time()

        # Base Minkowski metric with signature (+,-,-,-)
        g_mu_nu = np.diag([1, -1, -1, -1])

        # Modify metric based on qualia interactions
        if self.current_time > 0:
            # Calculate qualia correlations in spacetime
            recent_coords = self.qualia_coordinates[:, :, max(0, self.current_time-10):self.current_time+1]

            # Average over recent time steps
            mean_coords = np.mean(recent_coords, axis=2)

            # Calculate coordinate differences
            coord_diffs = mean_coords[:, np.newaxis, :] - mean_coords[np.newaxis, :, :]

            # Use coordinate differences to modify metric
            for mu in range(self.spacetime_dims):
                for nu in range(self.spacetime_dims):
                    if mu != nu:
                        # Metric modification based on coordinate correlations
                        coord_corr = np.mean(coord_diffs[:, :, mu] * coord_diffs[:, :, nu])
                        # Small perturbation to metric
                        g_mu_nu[mu, nu] += 0.1 * coord_corr
                        g_mu_nu[nu, mu] = g_mu_nu[mu, nu]  # Symmetric

        # Ensure metric is still Lorentzian-like (mostly diagonal dominant)
        # Normalize off-diagonal terms
        for mu in range(self.spacetime_dims):
            for nu in range(self.spacetime_dims):
                if mu != nu:
                    g_mu_nu[mu, nu] = np.clip(g_mu_nu[mu, nu], -0.5, 0.5)

        self.metric_tensor = g_mu_nu

        calculation_time = time.time() - start_time
        self.total_calculation_time += calculation_time
        self.calculation_count += 1

        return g_mu_nu

    def calculate_geodesic_distance(self, qualia_idx_a: int, qualia_idx_b: int) -> float:
        """
        Calculate geodesic distance between two qualia in spacetime.

        Args:
            qualia_idx_a: Index of first qualia
            qualia_idx_b: Index of second qualia

        Returns:
            Geodesic distance ds
        """
        if qualia_idx_a >= self.num_qualia or qualia_idx_b >= self.num_qualia:
            return 0.0

        # Get recent coordinates
        coords_a = self.qualia_coordinates[qualia_idx_a, :, max(0, self.current_time-5):self.current_time+1]
        coords_b = self.qualia_coordinates[qualia_idx_b, :, max(0, self.current_time-5):self.current_time+1]

        # Use most recent coordinates
        coord_a = coords_a[:, -1] if coords_a.size > 0 else np.zeros(self.spacetime_dims)
        coord_b = coords_b[:, -1] if coords_b.size > 0 else np.zeros(self.spacetime_dims)

        # Coordinate difference dφ^μ
        d_phi = coord_b - coord_a

        # Calculate ds² = g_μν dφ^μ dφ^ν
        ds_squared = 0.0
        for mu in range(self.spacetime_dims):
            for nu in range(self.spacetime_dims):
                ds_squared += self.metric_tensor[mu, nu] * d_phi[mu] * d_phi[nu]

        # Take absolute value and square root for distance
        geodesic_distance = np.sqrt(abs(ds_squared))

        return geodesic_distance

    def update_temporal_binding(self) -> None:
        """Update temporal binding matrix based on geodesic distances."""
        # Calculate geodesic distances between all qualia pairs
        for i in range(self.num_qualia):
            for j in range(self.num_qualia):
                if i != j:
                    distance = self.calculate_geodesic_distance(i, j)
                    # Temporal binding strength: inverse of distance (closer = stronger binding)
                    binding_strength = 1.0 / (1.0 + distance)
                    self.temporal_binding[i, j] = binding_strength
                else:
                    self.temporal_binding[i, j] = 0.0  # No self-binding

        # Store geodesic distances for analysis
        self.geodesic_distances = np.copy(self.temporal_binding)

    def calculate_narrative_continuity(self) -> float:
        """
        Calculate narrative continuity based on temporal binding structure.

        Returns:
            Continuity score (0-1, higher = more continuous)
        """
        if self.temporal_binding.size == 0:
            return 0.0

        # Narrative continuity based on:
        # 1. Average temporal binding strength
        # 2. Binding network connectivity
        # 3. Temporal coherence over recent history

        avg_binding = np.mean(self.temporal_binding)

        # Network connectivity: fraction of strong bindings
        strong_binding_threshold = 0.5
        connectivity = np.mean(self.temporal_binding > strong_binding_threshold)

        # Temporal coherence: consistency of binding over time
        # (Simplified: variance of binding strengths)
        binding_variance = np.var(self.temporal_binding)
        temporal_coherence = 1.0 / (1.0 + binding_variance)

        # Combined continuity score
        continuity = (avg_binding + connectivity + temporal_coherence) / 3.0

        self.narrative_continuity = continuity

        return continuity

    def get_spacetime_analysis(self) -> Dict[str, Any]:
        """
        Get comprehensive spacetime analysis.

        Returns:
            Analysis results
        """
        # Ensure metric tensor is up to date
        metric = self.calculate_metric_tensor()

        # Update temporal binding
        self.update_temporal_binding()

        # Calculate continuity
        continuity = self.calculate_narrative_continuity()

        # Calculate binding statistics
        binding_stats = {
            "mean_binding": np.mean(self.temporal_binding),
            "max_binding": np.max(self.temporal_binding),
            "binding_connectivity": np.mean(self.temporal_binding > 0.3),
            "binding_entropy": -np.sum(self.temporal_binding * np.log(self.temporal_binding + 1e-10))
        }

        # Metric tensor properties
        metric_eigenvals = np.linalg.eigvals(metric)
        metric_condition = np.max(np.abs(metric_eigenvals)) / (np.min(np.abs(metric_eigenvals)) + 1e-10)

        analysis = {
            "metric_tensor": metric.tolist(),
            "metric_eigenvalues": metric_eigenvals.tolist(),
            "metric_condition_number": metric_condition,
            "temporal_binding_matrix": self.temporal_binding.tolist(),
            "narrative_continuity": continuity,
            "binding_statistics": binding_stats,
            "geodesic_distances": self.geodesic_distances.tolist(),
            "current_time": self.current_time,
            "timestamp": datetime.now()
        }

        return analysis

    def get_phi_contribution(self) -> float:
        """Get Phi contribution from spacetime mapping."""
        continuity = self.calculate_narrative_continuity()

        # Phi contribution based on narrative continuity
        # Higher continuity = higher Phi contribution
        phi_contrib = continuity * 0.5  # Scale factor

        return phi_contrib

    def reset(self):
        """Reset spacetime mapping state."""
        self.qualia_coordinates = np.zeros((self.num_qualia, self.spacetime_dims, self.temporal_resolution))
        self.metric_tensor = np.eye(self.spacetime_dims)
        self.temporal_binding = np.zeros((self.num_qualia, self.num_qualia))
        self.geodesic_distances = np.zeros((self.num_qualia, self.num_qualia))
        self.narrative_continuity = 0.0
        self.current_time = 0
        self.calculation_count = 0
        self.total_calculation_time = 0.0


def main():
    """Test the qualia spacetime mapper."""
    print("🧠 QUALIA SPACETIME MAPPER")
    print("=" * 40)

    mapper = QualiaSpacetimeMapper(num_qualia=5, spacetime_dims=4, temporal_resolution=20)

    print(f"Qualia types: {mapper.num_qualia}")
    print(f"Spacetime dimensions: {mapper.spacetime_dims}")
    print()

    # Test with different qualia activation patterns
    test_patterns = [
        ("Uniform activation", np.ones(5) * 0.8),
        ("Gradient activation", np.linspace(0.1, 0.9, 5)),
        ("Peak activation", np.array([0.1, 0.3, 0.9, 0.3, 0.1])),
        ("Random activation", np.random.uniform(0.2, 0.8, 5))
    ]

    for name, pattern in test_patterns:
        print(f"Testing: {name}")
        mapper.update_qualia_coordinates(pattern, temporal_step=0.1)

        analysis = mapper.get_spacetime_analysis()

        print(f"  Continuity: {analysis['narrative_continuity']:.4f}")
        print(f"  Mean binding: {analysis['binding_statistics']['mean_binding']:.4f}")
        print(f"  Phi contrib: {mapper.get_phi_contribution():.4f}")
        print()

    print("Final spacetime analysis:")
    final_analysis = mapper.get_spacetime_analysis()
    print(f"  Metric eigenvalues: {['.3f' for x in final_analysis['metric_eigenvalues']]}")
    print(f"  Final continuity: {final_analysis['narrative_continuity']:.4f}")


if __name__ == "__main__":
    main()