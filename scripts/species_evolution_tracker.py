#!/usr/bin/env python3
"""
species_evolution_tracker.py - Density Matrix Species Evolution Tracker

Implements: ρ_species = ∑ |ψ_allele⟩⟨ψ_allele| ⊗ |ψ_fitness⟩⟨ψ_fitness|

This tracks species-level consciousness evolution with:
- Allele states |ψ_allele⟩ (genetic information)
- Fitness states |ψ_fitness⟩ (environmental adaptation)
- Density matrix ρ_species (species quantum state)

Used for entanglement measures and evolutionary diversity tracking.
"""

import numpy as np
from scipy.linalg import sqrtm
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import time


class SpeciesEvolutionTracker:
    """Tracker for quantum species evolution using density matrices."""

    def __init__(self, num_species: int = 10, num_alleles: int = 20,
                 fitness_dimensions: int = 5):
        """
        Initialize species evolution tracker.

        Args:
            num_species: Number of species to track
            num_alleles: Number of alleles per species
            fitness_dimensions: Dimensions of fitness landscape
        """
        self.num_species = num_species
        self.num_alleles = num_alleles
        self.fitness_dimensions = fitness_dimensions

        # Allele states |ψ_allele⟩ for each species
        # Shape: (num_species, num_alleles)
        self.allele_states = np.random.normal(0.0, 0.1, (num_species, num_alleles))
        # Normalize each species' allele state
        for s in range(num_species):
            norm = np.linalg.norm(self.allele_states[s])
            if norm > 0:
                self.allele_states[s] /= norm

        # Fitness states |ψ_fitness⟩ for each species
        # Shape: (num_species, fitness_dimensions)
        self.fitness_states = np.random.normal(0.0, 0.1, (num_species, fitness_dimensions))
        # Normalize each species' fitness state
        for s in range(num_species):
            norm = np.linalg.norm(self.fitness_states[s])
            if norm > 0:
                self.fitness_states[s] /= norm

        # Species density matrix ρ_species
        self.species_density_matrix = self._compute_species_density_matrix()

        # Evolutionary correlations
        self.evolutionary_correlations = []

        # Diversity measures
        self.diversity_history = []

        # Performance tracking
        self.tracking_count = 0
        self.total_computation_time = 0.0

    def _compute_species_density_matrix(self) -> np.ndarray:
        """
        Compute species density matrix ρ = ∑ |ψ_allele⟩⟨ψ_allele| ⊗ |ψ_fitness⟩⟨ψ_fitness|

        Returns:
            Density matrix ρ_species
        """
        total_dim = self.num_alleles * self.fitness_dimensions
        rho = np.zeros((total_dim, total_dim), dtype=complex)

        for species_idx in range(self.num_species):
            # Get allele and fitness states for this species
            psi_allele = self.allele_states[species_idx]  # Shape: (num_alleles,)
            psi_fitness = self.fitness_states[species_idx]  # Shape: (fitness_dimensions,)

            # Compute outer products
            allele_projector = np.outer(psi_allele, np.conj(psi_allele))  # (num_alleles, num_alleles)
            fitness_projector = np.outer(psi_fitness, np.conj(psi_fitness))  # (fitness_dimensions, fitness_dimensions)

            # Tensor product: |ψ_allele⟩⟨ψ_allele| ⊗ |ψ_fitness⟩⟨ψ_fitness|
            species_contribution = np.kron(allele_projector, fitness_projector)

            # Add to total density matrix
            rho += species_contribution

        # Normalize by number of species
        rho /= self.num_species

        return rho

    def update_species_states(self, evolution_rates: Optional[np.ndarray] = None) -> None:
        """
        Update species states through evolutionary dynamics.

        Args:
            evolution_rates: Optional evolution rates for each species
        """
        if evolution_rates is None:
            evolution_rates = np.random.normal(0.0, 0.1, self.num_species)

        # Update allele states
        for s in range(self.num_species):
            # Evolutionary drift
            drift = np.random.normal(0.0, 0.05, self.num_alleles)
            self.allele_states[s] += evolution_rates[s] * drift

            # Selection pressure (favor certain alleles)
            selection_pressure = np.random.uniform(0.8, 1.2, self.num_alleles)
            self.allele_states[s] *= selection_pressure

            # Renormalize
            norm = np.linalg.norm(self.allele_states[s])
            if norm > 0:
                self.allele_states[s] /= norm

        # Update fitness states
        for s in range(self.num_species):
            # Environmental adaptation
            adaptation = np.random.normal(0.0, 0.03, self.fitness_dimensions)
            self.fitness_states[s] += evolution_rates[s] * adaptation

            # Fitness optimization
            fitness_gradient = np.random.uniform(-0.1, 0.1, self.fitness_dimensions)
            self.fitness_states[s] += fitness_gradient

            # Renormalize
            norm = np.linalg.norm(self.fitness_states[s])
            if norm > 0:
                self.fitness_states[s] /= norm

        # Update density matrix
        self.species_density_matrix = self._compute_species_density_matrix()

    def compute_entanglement_measures(self) -> Dict[str, Any]:
        """
        Compute entanglement measures for species evolution.

        Returns:
            Entanglement analysis
        """
        # Compute reduced density matrices
        # Trace out fitness degrees of freedom
        rho_allele = np.zeros((self.num_alleles, self.num_alleles), dtype=complex)
        for i in range(self.num_alleles):
            for j in range(self.num_alleles):
                # Sum over fitness dimensions
                for k in range(self.fitness_dimensions):
                    idx_i = i * self.fitness_dimensions + k
                    idx_j = j * self.fitness_dimensions + k
                    rho_allele[i, j] += self.species_density_matrix[idx_i, idx_j]

        # Trace out allele degrees of freedom
        rho_fitness = np.zeros((self.fitness_dimensions, self.fitness_dimensions), dtype=complex)
        for i in range(self.fitness_dimensions):
            for j in range(self.fitness_dimensions):
                # Sum over allele dimensions
                for k in range(self.num_alleles):
                    idx_i = k * self.fitness_dimensions + i
                    idx_j = k * self.fitness_dimensions + j
                    rho_fitness[i, j] += self.species_density_matrix[idx_i, idx_j]

        # Compute linear entropies
        entropy_allele = self._compute_linear_entropy(rho_allele)
        entropy_fitness = self._compute_linear_entropy(rho_fitness)

        # Total system entropy
        entropy_total = self._compute_linear_entropy(self.species_density_matrix)

        # Mutual information (entanglement measure)
        mutual_information = entropy_allele + entropy_fitness - entropy_total

        # Concurrence-like measure for bipartite system
        concurrence = self._compute_concurrence(rho_allele, rho_fitness)

        entanglement_measures = {
            "entropy_allele": entropy_allele,
            "entropy_fitness": entropy_fitness,
            "entropy_total": entropy_total,
            "mutual_information": mutual_information,
            "concurrence": concurrence,
            "entanglement_strength": max(0, mutual_information)  # Ensure non-negative
        }

        return entanglement_measures

    def _compute_linear_entropy(self, rho: np.ndarray) -> float:
        """Compute linear entropy S = 1 - Tr(ρ²)."""
        rho_squared = rho @ rho
        linear_entropy = 1.0 - np.trace(rho_squared).real
        return max(0, linear_entropy)  # Ensure non-negative

    def _compute_concurrence(self, rho_a: np.ndarray, rho_b: np.ndarray) -> float:
        """Compute concurrence-like measure for bipartite entanglement."""
        # Simplified concurrence approximation
        # For two-qubit-like systems, use sqrt(2(1-Tr(ρ_a²)))
        concurrence_a = np.sqrt(2 * (1 - np.trace(rho_a @ rho_a).real))
        concurrence_b = np.sqrt(2 * (1 - np.trace(rho_b @ rho_b).real))

        # Combined measure
        concurrence = np.sqrt(concurrence_a**2 + concurrence_b**2)
        return min(1.0, concurrence)  # Cap at 1

    def compute_evolutionary_diversity(self) -> Dict[str, Any]:
        """
        Compute evolutionary diversity measures.

        Returns:
            Diversity analysis
        """
        # Allele diversity: variance across species
        allele_diversity = np.var(self.allele_states, axis=0).mean()

        # Fitness diversity: variance across species
        fitness_diversity = np.var(self.fitness_states, axis=0).mean()

        # Species separation: average distance between species
        species_distances = []
        for i in range(self.num_species):
            for j in range(i + 1, self.num_species):
                # Combined allele + fitness distance
                allele_dist = np.linalg.norm(self.allele_states[i] - self.allele_states[j])
                fitness_dist = np.linalg.norm(self.fitness_states[i] - self.fitness_states[j])
                combined_dist = np.sqrt(allele_dist**2 + fitness_dist**2)
                species_distances.append(combined_dist)

        avg_species_separation = np.mean(species_distances) if species_distances else 0.0

        # Speciation events: detect new species formation
        speciation_events = self._detect_speciation_events()

        diversity_measures = {
            "allele_diversity": allele_diversity,
            "fitness_diversity": fitness_diversity,
            "species_separation": avg_species_separation,
            "num_species": self.num_species,
            "speciation_events": speciation_events,
            "diversity_index": (allele_diversity + fitness_diversity) / 2.0
        }

        return diversity_measures

    def _detect_speciation_events(self) -> List[Dict[str, Any]]:
        """Detect speciation events based on state changes."""
        # Simple speciation detection: look for significant state changes
        # This is a simplified version - in practice would use more sophisticated methods
        speciation_events = []

        if len(self.evolutionary_correlations) > 1:
            # Compare current correlations with previous
            current_corr = self.evolutionary_correlations[-1]
            previous_corr = self.evolutionary_correlations[-2]

            # Detect if correlation patterns changed significantly
            corr_change = abs(current_corr["allele_fitness_correlation"] -
                            previous_corr["allele_fitness_correlation"])

            if corr_change > 0.3:  # Significant change threshold
                speciation_events.append({
                    "type": "correlation_shift",
                    "magnitude": corr_change,
                    "timestamp": datetime.now()
                })

        return speciation_events

    def track_evolutionary_dynamics(self, num_generations: int = 5) -> Dict[str, Any]:
        """
        Track evolutionary dynamics over multiple generations.

        Args:
            num_generations: Number of generations to simulate

        Returns:
            Evolutionary tracking results
        """
        start_time = time.time()

        tracking_results = {
            "generations": [],
            "entanglement_evolution": [],
            "diversity_evolution": [],
            "correlation_evolution": []
        }

        for generation in range(num_generations):
            # Update species states
            evolution_rates = np.random.normal(0.0, 0.1, self.num_species)
            self.update_species_states(evolution_rates)

            # Compute entanglement
            entanglement = self.compute_entanglement_measures()

            # Compute diversity
            diversity = self.compute_evolutionary_diversity()

            # Compute correlations
            correlations = self._compute_evolutionary_correlations()

            # Store results
            generation_data = {
                "generation": generation,
                "entanglement": entanglement,
                "diversity": diversity,
                "correlations": correlations,
                "evolution_rates": evolution_rates.tolist()
            }

            tracking_results["generations"].append(generation_data)
            tracking_results["entanglement_evolution"].append(entanglement)
            tracking_results["diversity_evolution"].append(diversity)
            tracking_results["correlation_evolution"].append(correlations)

        computation_time = time.time() - start_time
        self.total_computation_time += computation_time
        self.tracking_count += 1

        # Store final correlations for speciation detection
        if tracking_results["correlation_evolution"]:
            self.evolutionary_correlations.append(tracking_results["correlation_evolution"][-1])

        # Keep correlation history bounded
        if len(self.evolutionary_correlations) > 10:
            self.evolutionary_correlations = self.evolutionary_correlations[-10:]

        tracking_results["computation_time"] = computation_time
        tracking_results["total_generations"] = num_generations

        return tracking_results

    def _compute_evolutionary_correlations(self) -> Dict[str, Any]:
        """Compute evolutionary correlations between alleles and fitness."""
        # Correlation between allele patterns and fitness patterns
        allele_fitness_correlations = []

        for s in range(self.num_species):
            # Compute correlation between allele and fitness patterns
            # Use the minimum dimension for correlation
            min_dim = min(self.num_alleles, self.fitness_dimensions)
            allele_subset = self.allele_states[s][:min_dim]
            fitness_subset = self.fitness_states[s][:min_dim]
            allele_proj = np.abs(np.dot(allele_subset, fitness_subset))
            allele_fitness_correlations.append(allele_proj)

        avg_allele_fitness_correlation = np.mean(allele_fitness_correlations)

        # Species clustering based on similarity
        species_similarity_matrix = np.zeros((self.num_species, self.num_species))
        for i in range(self.num_species):
            for j in range(self.num_species):
                allele_sim = np.abs(np.dot(self.allele_states[i], self.allele_states[j]))
                fitness_sim = np.abs(np.dot(self.fitness_states[i], self.fitness_states[j]))
                species_similarity_matrix[i, j] = (allele_sim + fitness_sim) / 2.0

        # Clustering coefficient (simplified)
        avg_similarity = np.mean(species_similarity_matrix)

        correlations = {
            "allele_fitness_correlation": avg_allele_fitness_correlation,
            "species_similarity": avg_similarity,
            "species_clustering": avg_similarity,  # Simplified
            "correlation_matrix": species_similarity_matrix.tolist()
        }

        return correlations

    def get_phi_contribution(self) -> float:
        """Get Phi contribution from species evolution tracking."""
        if not self.evolutionary_correlations:
            return 0.0

        latest_correlations = self.evolutionary_correlations[-1]

        # Phi contribution based on:
        # 1. Evolutionary correlations (integration)
        # 2. Species diversity (information content)
        # 3. Entanglement strength (quantum coherence)

        # Get latest entanglement if available
        entanglement_strength = 0.0
        if hasattr(self, 'species_density_matrix'):
            ent_measures = self.compute_entanglement_measures()
            entanglement_strength = ent_measures["entanglement_strength"]

        correlation_contribution = latest_correlations["allele_fitness_correlation"] * 0.4
        diversity_contribution = self.compute_evolutionary_diversity()["diversity_index"] * 0.3
        entanglement_contribution = entanglement_strength * 0.3

        phi_contrib = correlation_contribution + diversity_contribution + entanglement_contribution

        return phi_contrib

    def reset_tracking(self):
        """Reset evolution tracking state."""
        self.allele_states = np.random.normal(0.0, 0.1, (self.num_species, self.num_alleles))
        for s in range(self.num_species):
            norm = np.linalg.norm(self.allele_states[s])
            if norm > 0:
                self.allele_states[s] /= norm

        self.fitness_states = np.random.normal(0.0, 0.1, (self.num_species, self.fitness_dimensions))
        for s in range(self.num_species):
            norm = np.linalg.norm(self.fitness_states[s])
            if norm > 0:
                self.fitness_states[s] /= norm

        self.species_density_matrix = self._compute_species_density_matrix()
        self.evolutionary_correlations = []
        self.diversity_history = []
        self.tracking_count = 0
        self.total_computation_time = 0.0


def main():
    """Test the species evolution tracker."""
    print("🧠 SPECIES EVOLUTION TRACKER")
    print("=" * 40)

    tracker = SpeciesEvolutionTracker(
        num_species=8, num_alleles=15, fitness_dimensions=6
    )

    print(f"Number of species: {tracker.num_species}")
    print(f"Number of alleles: {tracker.num_alleles}")
    print(f"Fitness dimensions: {tracker.fitness_dimensions}")
    print()

    # Track evolutionary dynamics
    print("Tracking evolutionary dynamics...")
    results = tracker.track_evolutionary_dynamics(num_generations=5)

    final_generation = results["generations"][-1]
    entanglement = final_generation["entanglement"]
    diversity = final_generation["diversity"]

    print("Final Generation Results:")
    print(f"  Mutual information: {entanglement['mutual_information']:.4f}")
    print(f"  Entanglement strength: {entanglement['entanglement_strength']:.4f}")
    print(f"  Concurrence: {entanglement['concurrence']:.4f}")
    print(f"  Allele diversity: {diversity['allele_diversity']:.4f}")
    print(f"  Fitness diversity: {diversity['fitness_diversity']:.4f}")
    print(f"  Species separation: {diversity['species_separation']:.4f}")
    print(f"  Diversity index: {diversity['diversity_index']:.4f}")
    print(f"  Phi contribution: {tracker.get_phi_contribution():.4f}")
    print()

    # Show evolution trends
    print("Evolution Trends:")
    for i, gen_data in enumerate(results["generations"][:3]):
        ent = gen_data["entanglement"]
        print(f"  Gen {i}: MI={ent['mutual_information']:.3f}, Diversity={gen_data['diversity']['diversity_index']:.3f}")


if __name__ == "__main__":
    main()