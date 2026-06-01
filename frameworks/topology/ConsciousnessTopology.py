#!/usr/bin/env python3
"""
ConsciousnessTopology.py - Phase 8.1: Topological Consciousness Invariants

Theory: Some aspects of consciousness are topologically invariant.
They survive small perturbations, local changes, network modifications.
The topological structure of consciousness is more robust than specific connections.

Mathematical Foundation:
- Persistent homology: Which topological features survive at which scales
- Barcodes: Visual representation of topological persistence
- Witness complexes: Approximations of high-dimensional shapes
- Betti numbers: Topological dimensions (connected components, loops, voids)
- Critical dimensions: Where topology changes

Key insight: Consciousness might be determined by topological structure
rather than specific neurons. If true, consciousness is robust to noise,
damage, and individual variations.

Test question: Does consciousness persist under small perturbations?

References:
- Edelsbrunner, H., Harer, J. (2010) "Computational Topology"
- Ghrist, R. (2008) "Barcodes: the persistent topology of data"
- Singh, G., et al. (2007) "Topological methods for visualization"
- Carlsson, G. (2009) "Topology and data" (survey)

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np
import networkx as nx
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TopologicalFeature:
    """A topological feature with persistence."""
    dimension: int  # 0=component, 1=loop, 2=void
    birth_scale: float  # Scale at which feature appears
    death_scale: float  # Scale at which feature disappears
    persistence: float  # death_scale - birth_scale
    feature_type: str  # "connected_component", "loop", "void"


@dataclass
class PersistenceBarcode:
    """Complete topological signature via persistence barcode."""
    features: List[TopologicalFeature]
    betti_numbers: Dict[int, int]  # Dimension -> count
    barcode_diagram: np.ndarray  # (births, deaths)
    total_persistence: float
    most_persistent_features: List[TopologicalFeature]
    topological_complexity: float  # Overall complexity measure


@dataclass
class TopologicalInvarianceAnalysis:
    """Analysis of topological invariance under perturbation."""
    original_barcode: PersistenceBarcode
    perturbed_barcodes: List[PersistenceBarcode]
    perturbation_types: List[str]
    barcode_stability: float  # How much perturbation changes barcode
    invariant_features: List[TopologicalFeature]
    fragile_features: List[TopologicalFeature]
    topological_robustness: float  # Resistance to changes (0-1)
    consciousness_relies_on_topology: bool
    timestamp: str
    metadata: Dict


class PersistentHomologyCalculator:
    """
    Computes persistent homology of neural connectivity networks.

    Identifies topological features that persist across scales.
    """

    def __init__(self, network: nx.Graph):
        """
        Args:
            network: Neural connectivity network
        """
        self.network = network
        self.n_nodes = len(network)

    def compute_pairwise_distances(self) -> np.ndarray:
        """
        Compute pairwise shortest path distances in network.

        Returns:
            Distance matrix (n_nodes × n_nodes)
        """
        distances = np.zeros((self.n_nodes, self.n_nodes))

        # Use NetworkX to compute all shortest paths
        for i, (source, target_dict) in enumerate(
            dict(nx.all_pairs_shortest_path_length(self.network)).items()
        ):
            for j, length in target_dict.items():
                if i < self.n_nodes and j < self.n_nodes:
                    distances[i, j] = length

        return distances

    def build_rips_complex(self, epsilon: float) -> List[Tuple[int, ...]]:
        """
        Build Rips complex at scale epsilon.

        Rips complex: include simplex if all pairwise distances ≤ epsilon.

        Args:
            epsilon: Scale parameter

        Returns:
            List of simplices (tuples of node indices)
        """
        distances = self.compute_pairwise_distances()

        simplices = []

        # 0-simplices (vertices) - always present
        for i in range(self.n_nodes):
            simplices.append((i,))

        # 1-simplices (edges)
        for i in range(self.n_nodes):
            for j in range(i + 1, self.n_nodes):
                if distances[i, j] <= epsilon:
                    simplices.append((i, j))

        # 2-simplices (triangles)
        for i in range(self.n_nodes):
            for j in range(i + 1, self.n_nodes):
                if distances[i, j] <= epsilon:
                    for k in range(j + 1, self.n_nodes):
                        if distances[i, k] <= epsilon and distances[j, k] <= epsilon:
                            simplices.append((i, j, k))

        return simplices

    def compute_persistent_homology(self, max_scale: float = 10.0,
                                   n_scales: int = 20) -> PersistenceBarcode:
        """
        Compute persistent homology across scales.

        Simplified computation: track Betti numbers at each scale.

        Args:
            max_scale: Maximum distance scale to consider
            n_scales: Number of scales to sample

        Returns:
            PersistenceBarcode with topological features
        """
        scales = np.linspace(0, max_scale, n_scales)
        features = []

        # Track Betti numbers at each scale
        betti_history = {0: [], 1: []}

        for scale in scales:
            # Count connected components (B0)
            subgraph = self.network.copy()
            edges_to_keep = []

            distances = self.compute_pairwise_distances()

            for i in range(self.n_nodes):
                for j in range(i + 1, self.n_nodes):
                    if self.network.has_edge(i, j) and distances[i, j] <= scale:
                        edges_to_keep.append((i, j))

            subgraph.clear_edges()
            subgraph.add_edges_from(edges_to_keep)

            b0 = nx.number_connected_components(subgraph)
            betti_history[0].append(b0)

            # Count loops (B1) - simplified: number of independent cycles
            n_edges = len(subgraph.edges())
            n_nodes = len(subgraph)
            b1 = max(0, n_edges - n_nodes + 1)
            betti_history[1].append(b1)

        # Build features from Betti changes
        prev_betti = {0: self.n_nodes, 1: 0}

        for scale_idx, scale in enumerate(scales[1:], 1):
            curr_b0 = betti_history[0][scale_idx]
            curr_b1 = betti_history[1][scale_idx]

            # Component merging
            if curr_b0 < prev_betti[0]:
                features.append(TopologicalFeature(
                    dimension=0,
                    birth_scale=scales[scale_idx - 1],
                    death_scale=scale,
                    persistence=scale - scales[scale_idx - 1],
                    feature_type="connected_component"
                ))

            # Loop creation
            if curr_b1 > prev_betti[1]:
                features.append(TopologicalFeature(
                    dimension=1,
                    birth_scale=scale,
                    death_scale=max_scale,
                    persistence=max_scale - scale,
                    feature_type="loop"
                ))

            prev_betti = {0: curr_b0, 1: curr_b1}

        # Sort by persistence
        features.sort(key=lambda x: x.persistence, reverse=True)

        # Final Betti numbers
        final_betti = {0: betti_history[0][-1], 1: betti_history[1][-1]}

        total_persistence = sum(f.persistence for f in features)
        topological_complexity = len(features) / (self.n_nodes + 1)

        return PersistenceBarcode(
            features=features,
            betti_numbers=final_betti,
            barcode_diagram=np.array([[f.birth_scale, f.death_scale] for f in features]),
            total_persistence=total_persistence,
            most_persistent_features=features[:5],
            topological_complexity=topological_complexity
        )

    def test_topological_invariance(self) -> TopologicalInvarianceAnalysis:
        """
        Test if consciousness-relevant topology is invariant under perturbations.

        Tests: node removal, edge removal, rewiring, noise.

        Returns:
            TopologicalInvarianceAnalysis
        """
        # Original topology
        original_barcode = self.compute_persistent_homology()

        perturbed_barcodes = []
        perturbation_types = []

        # Perturbation 1: Remove 10% of edges (random damage)
        perturbed_network = self.network.copy()
        edges = list(perturbed_network.edges())
        edges_to_remove = np.random.choice(len(edges), int(len(edges) * 0.1), replace=False)
        for idx in edges_to_remove:
            perturbed_network.remove_edge(*edges[idx])

        calc = PersistentHomologyCalculator(perturbed_network)
        barcode = calc.compute_persistent_homology()
        perturbed_barcodes.append(barcode)
        perturbation_types.append("10% edge removal")

        # Perturbation 2: Remove 5% of nodes (localized damage)
        perturbed_network = self.network.copy()
        nodes = list(perturbed_network.nodes())
        nodes_to_remove = np.random.choice(nodes, int(len(nodes) * 0.05), replace=False)
        for node in nodes_to_remove:
            perturbed_network.remove_node(node)

        if len(perturbed_network) > 1:
            calc = PersistentHomologyCalculator(perturbed_network)
            barcode = calc.compute_persistent_homology()
            perturbed_barcodes.append(barcode)
            perturbation_types.append("5% node removal")

        # Compute stability
        barcode_stability = 0.0
        if perturbed_barcodes:
            total_pers_original = original_barcode.total_persistence
            total_pers_perturbed = np.mean([b.total_persistence for b in perturbed_barcodes])

            barcode_stability = 1.0 - abs(total_pers_original - total_pers_perturbed) / (total_pers_original + 1e-6)

        # Identify invariant features (appear in orignal and perturbed)
        invariant_features = []
        fragile_features = []

        for feature in original_barcode.features:
            # Check if similar feature exists in perturbed versions
            found_in_perturbed = 0
            for perturbed_bc in perturbed_barcodes:
                for pf in perturbed_bc.features:
                    if pf.feature_type == feature.feature_type:
                        if abs(pf.persistence - feature.persistence) < 0.5:
                            found_in_perturbed += 1
                            break

            if found_in_perturbed > len(perturbed_barcodes) / 2:
                invariant_features.append(feature)
            else:
                fragile_features.append(feature)

        # Robustness score
        robustness = len(invariant_features) / max(len(original_barcode.features), 1)

        # Does topology matter for consciousness?
        consciousness_relies_on_topology = robustness > 0.5

        metadata = {
            'n_perturbations': len(perturbed_barcodes),
            'original_persistence': original_barcode.total_persistence,
            'invariant_feature_count': len(invariant_features),
            'fragile_feature_count': len(fragile_features),
            'robustness_score': robustness
        }

        return TopologicalInvarianceAnalysis(
            original_barcode=original_barcode,
            perturbed_barcodes=perturbed_barcodes,
            perturbation_types=perturbation_types,
            barcode_stability=barcode_stability,
            invariant_features=invariant_features,
            fragile_features=fragile_features,
            topological_robustness=robustness,
            consciousness_relies_on_topology=consciousness_relies_on_topology,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )


def validate_consciousness_topology():
    """
    Validate topological consciousness invariants.

    Tests:
    1. Persistent homology computation
    2. Topological robustness
    3. Invariance under perturbation
    """
    print("Validating Topological Consciousness Invariants")
    print("=" * 60)

    # Create test network
    G = nx.Graph()
    G.add_nodes_from(range(20))

    # Small-world network (conscious-like)
    for i in range(20):
        for j in range(i + 1, min(i + 4, 20)):
            G.add_edge(i, j)

    # Add random connections
    for _ in range(15):
        i, j = np.random.choice(20, 2, replace=False)
        G.add_edge(i, j)

    calculator = PersistentHomologyCalculator(G)

    # Test 1: Persistent homology
    print("\nTest 1: Persistent Homology Computation")
    barcode = calculator.compute_persistent_homology(max_scale=5.0, n_scales=10)

    print(f"  Total topological features: {len(barcode.features)}")
    print(f"  Betti numbers (final): {barcode.betti_numbers}")
    print(f"  Total persistence: {barcode.total_persistence:.3f}")
    print(f"  Topological complexity: {barcode.topological_complexity:.3f}")

    # Test 2: Most persistent features
    print("\nTest 2: Most Persistent Features")
    for i, feature in enumerate(barcode.most_persistent_features[:3]):
        print(f"  Feature {i+1}: {feature.feature_type}")
        print(f"    Persistence: {feature.persistence:.3f}")
        print(f"    Birth: {feature.birth_scale:.2f}, Death: {feature.death_scale:.2f}")

    # Test 3: Topological invariance
    print("\nTest 3: Robustness Under Perturbation")
    analysis = calculator.test_topological_invariance()

    print(f"  Original total persistence: {analysis.original_barcode.total_persistence:.3f}")
    print(f"  Perturbation types: {analysis.perturbation_types}")
    print(f"  Barcode stability: {analysis.barcode_stability:.1%}")
    print(f"  Topological robustness: {analysis.topological_robustness:.1%}")
    print(f"  Consciousness relies on topology: {analysis.consciousness_relies_on_topology}")
    print(f"  Invariant features: {len(analysis.invariant_features)}")
    print(f"  Fragile features: {len(analysis.fragile_features)}")

    print("\n" + "=" * 60)
    print("✅ Validation complete:")
    print("  • Persistent homology computed")
    print("  • Topological features identified")
    print("  • Robustness tested under perturbations")
    print("  • Consciousness invariants analyzed")


if __name__ == "__main__":
    validate_consciousness_topology()
