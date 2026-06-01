#!/usr/bin/env python3
"""
MinimumInformationPartition.py - Minimum Information Partition Algorithm

This implements the MIP (Minimum Information Partition) algorithm,
a key component of Integrated Information Theory (IIT).

The MIP is the partition of a system that minimizes the mutual information
between its parts, allowing calculation of integrated information Φ.

Algorithm Overview:
1. Generate all possible bipartitions of the system
2. For each partition, calculate mutual information between parts
3. Select the partition with minimum mutual information
4. Use this for Φ calculation: Φ = I(whole) - ∑I(parts)
"""

import math
import numpy as np
from typing import Dict, List, Set, Tuple, Optional, Any
from itertools import combinations, chain
from dataclasses import dataclass
import time


@dataclass
class PartitionCandidate:
    """A candidate partition with its properties."""
    subsets: List[Set[str]]
    mutual_information: float = 0.0
    normalized_mi: float = 0.0
    subset_sizes: Tuple[int, ...] = ()
    is_connected: bool = True

    def __post_init__(self):
        self.subset_sizes = tuple(len(s) for s in self.subsets)


class MinimumInformationPartition:
    """
    Minimum Information Partition (MIP) algorithm implementation.

    Finds the system partition that minimizes mutual information between parts,
    enabling calculation of integrated information Φ.
    """

    def __init__(self, max_system_size: int = 12):
        """
        Initialize MIP calculator.

        Args:
            max_system_size: Maximum components for feasible computation
        """
        self.max_system_size = max_system_size
        self.cache = {}  # Cache for repeated calculations

    def find_mip(self, components: List[str],
                component_states: Dict[str, float],
                connections: Dict[str, List[str]]) -> PartitionCandidate:
        """
        Find the Minimum Information Partition for a system.

        Args:
            components: List of component names
            component_states: Component name -> activation value
            connections: Component name -> list of connected components

        Returns:
            PartitionCandidate with minimum mutual information
        """
        if len(components) > self.max_system_size:
            raise ValueError(f"System too large: {len(components)} > {self.max_system_size}")

        if len(components) < 2:
            # Single component or empty system
            return PartitionCandidate([set(components)], 0.0, 0.0)

        # Generate all possible bipartitions
        all_partitions = self._generate_bipartitions(components)

        # Evaluate each partition
        min_mi = float('inf')
        best_partition = None

        for partition in all_partitions:
            mi = self._calculate_mutual_information(
                partition, component_states, connections
            )
            partition.mutual_information = mi

            # Normalize by partition size for fair comparison
            partition.normalized_mi = mi / len(partition.subsets)

            if mi < min_mi:
                min_mi = mi
                best_partition = partition

        return best_partition

    def _generate_bipartitions(self, components: List[str]) -> List[PartitionCandidate]:
        """
        Generate all possible bipartitions of the component set.

        A bipartition splits the set into exactly two non-empty subsets.
        """
        n = len(components)
        partitions = []

        # Generate all ways to choose subset1 (the rest automatically go to subset2)
        # We use combinations to avoid duplicates and ensure subset1 ≤ subset2 by size
        for r in range(1, n//2 + 1):
            for subset1_combo in combinations(components, r):
                subset1 = set(subset1_combo)
                subset2 = set(components) - subset1

                # Ensure subset1 is lexicographically smaller for consistency
                subset1_list = sorted(subset1)
                subset2_list = sorted(subset2)

                if subset1_list <= subset2_list:
                    partition = PartitionCandidate([subset1, subset2])
                    partitions.append(partition)

        return partitions

    def _calculate_mutual_information(self, partition: PartitionCandidate,
                                    component_states: Dict[str, float],
                                    connections: Dict[str, List[str]]) -> float:
        """
        Calculate mutual information between partition subsets.

        Mutual information I(X,Y) = H(X) + H(Y) - H(X,Y)
        where H is entropy.

        For multiple subsets, we use the total mutual information.
        """
        if len(partition.subsets) < 2:
            return 0.0

        # Calculate entropy of individual subsets
        subset_entropies = []
        for subset in partition.subsets:
            entropy = self._calculate_subset_entropy(
                subset, component_states, connections
            )
            subset_entropies.append(entropy)

        # Calculate joint entropy of all subsets together
        all_components = set()
        for subset in partition.subsets:
            all_components.update(subset)

        joint_entropy = self._calculate_subset_entropy(
            all_components, component_states, connections
        )

        # Mutual information = sum of individual entropies - joint entropy
        mutual_info = sum(subset_entropies) - joint_entropy

        return max(0.0, mutual_info)  # Ensure non-negative

    def _calculate_subset_entropy(self, subset: Set[str],
                                component_states: Dict[str, float],
                                connections: Dict[str, List[str]]) -> float:
        """
        Calculate the entropy of a subset of components.

        Uses a simplified entropy calculation based on:
        1. State diversity
        2. Connectivity patterns
        3. Information flow
        """
        if not subset:
            return 0.0

        # Get states for components in subset
        states = []
        for comp in subset:
            if comp in component_states:
                states.append(component_states[comp])

        if not states:
            return 0.0

        # Convert to numpy array for calculations
        states = np.array(states)

        # Basic entropy calculation
        # 1. State diversity (Shannon-like entropy)
        if len(states) > 1:
            # Discretize states into bins
            n_bins = min(10, len(states))
            hist, _ = np.histogram(states, bins=n_bins, density=True)
            hist = hist[hist > 0]  # Remove zero probabilities
            state_entropy = -np.sum(hist * np.log2(hist))
        else:
            state_entropy = 0.0

        # 2. Connectivity entropy
        connectivity_entropy = self._calculate_connectivity_entropy(
            subset, connections
        )

        # 3. Combine entropies
        total_entropy = state_entropy + 0.5 * connectivity_entropy

        return total_entropy

    def _calculate_connectivity_entropy(self, subset: Set[str],
                                      connections: Dict[str, List[str]]) -> float:
        """
        Calculate entropy based on connectivity patterns within the subset.
        """
        if len(subset) <= 1:
            return 0.0

        # Count internal vs external connections
        internal_connections = 0
        total_possible_connections = len(subset) * (len(subset) - 1)

        for comp in subset:
            if comp in connections:
                connected_comps = set(connections[comp])
                internal_connected = connected_comps & subset
                internal_connections += len(internal_connected)

        # Normalize
        connectivity_ratio = internal_connections / total_possible_connections if total_possible_connections > 0 else 0

        # Entropy of connectivity distribution
        if connectivity_ratio > 0 and connectivity_ratio < 1:
            conn_entropy = - (connectivity_ratio * math.log2(connectivity_ratio) +
                            (1 - connectivity_ratio) * math.log2(1 - connectivity_ratio))
        else:
            conn_entropy = 0.0

        return conn_entropy

    def analyze_partition_stability(self, components: List[str],
                                  component_states: Dict[str, float],
                                  connections: Dict[str, List[str]],
                                  n_samples: int = 10) -> Dict[str, Any]:
        """
        Analyze how stable the MIP is under small perturbations.

        Args:
            components: Component names
            component_states: Component states
            connections: Connection graph
            n_samples: Number of perturbation samples

        Returns:
            Stability analysis results
        """
        base_mip = self.find_mip(components, component_states, connections)

        if not base_mip or len(base_mip.subsets) < 2:
            return {'stability': 0.0, 'consistent_partitions': 0}

        consistent_partitions = 0

        for _ in range(n_samples):
            # Add small noise to states
            noisy_states = {}
            for comp, state in component_states.items():
                noise = np.random.normal(0, 0.05)  # 5% noise
                noisy_states[comp] = np.clip(state + noise, 0, 1)

            # Find MIP with noisy states
            noisy_mip = self.find_mip(components, noisy_states, connections)

            # Check if partition structure is similar
            if self._partitions_similar(base_mip, noisy_mip):
                consistent_partitions += 1

        stability = consistent_partitions / n_samples

        return {
            'stability': stability,
            'consistent_partitions': consistent_partitions,
            'total_samples': n_samples,
            'base_partition': [list(s) for s in base_mip.subsets]
        }

    def _partitions_similar(self, p1: PartitionCandidate,
                           p2: PartitionCandidate) -> bool:
        """
        Check if two partitions have similar structure.

        Uses Jaccard similarity of subset overlaps.
        """
        if len(p1.subsets) != len(p2.subsets):
            return False

        # Calculate average Jaccard similarity
        similarities = []
        for s1 in p1.subsets:
            best_similarity = 0
            for s2 in p2.subsets:
                intersection = len(s1 & s2)
                union = len(s1 | s2)
                if union > 0:
                    jaccard = intersection / union
                    best_similarity = max(best_similarity, jaccard)
            similarities.append(best_similarity)

        avg_similarity = np.mean(similarities)
        return avg_similarity > 0.7  # 70% similarity threshold

    def get_partition_complexity(self, partition: PartitionCandidate) -> Dict[str, Any]:
        """
        Analyze the complexity properties of a partition.

        Args:
            partition: Partition to analyze

        Returns:
            Complexity metrics
        """
        if not partition.subsets:
            return {'complexity': 0, 'balance': 0, 'modularity': 0}

        subset_sizes = [len(s) for s in partition.subsets]
        total_components = sum(subset_sizes)

        # Balance: how evenly distributed the components are
        ideal_size = total_components / len(partition.subsets)
        balance = 1.0 - (np.std(subset_sizes) / ideal_size)

        # Modularity: number of distinct subsets
        modularity = len(partition.subsets)

        # Overall complexity score
        complexity = balance * modularity

        return {
            'complexity': complexity,
            'balance': balance,
            'modularity': modularity,
            'subset_sizes': subset_sizes,
            'total_components': total_components
        }


# Convenience functions
def find_minimum_partition(components: List[str],
                          component_states: Dict[str, float],
                          connections: Dict[str, List[str]]) -> PartitionCandidate:
    """
    Convenience function for finding MIP.
    """
    mip_finder = MinimumInformationPartition()
    return mip_finder.find_mip(components, component_states, connections)


def calculate_partition_phi(partition: PartitionCandidate,
                           whole_system_info: float) -> float:
    """
    Calculate Φ contribution for a partition.

    Φ = I(whole) - ∑I(parts)
    """
    parts_info = sum(partition.mutual_information for _ in partition.subsets)
    return whole_system_info - parts_info


if __name__ == "__main__":
    # Example usage
    mip_finder = MinimumInformationPartition()

    # Simple 4-component system
    components = ['A', 'B', 'C', 'D']
    states = {'A': 0.8, 'B': 0.6, 'C': 0.9, 'D': 0.4}
    connections = {
        'A': ['B', 'C'],
        'B': ['A', 'C', 'D'],
        'C': ['A', 'B'],
        'D': ['B']
    }

    start_time = time.time()
    mip = mip_finder.find_mip(components, states, connections)
    computation_time = time.time() - start_time

    print(f"MIP found in {computation_time:.3f}s")
    print(f"Subsets: {[list(s) for s in mip.subsets]}")
    print(f"Mutual Information: {mip.mutual_information:.3f}")
    print(f"Normalized MI: {mip.normalized_mi:.3f}")

    # Analyze stability
    stability = mip_finder.analyze_partition_stability(components, states, connections)
    print(f"Partition stability: {stability['stability']:.2f}")

    # Complexity analysis
    complexity = mip_finder.get_partition_complexity(mip)
    print(f"Partition complexity: {complexity['complexity']:.2f}")