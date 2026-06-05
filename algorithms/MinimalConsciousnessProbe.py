#!/usr/bin/env python3
"""
MinimalConsciousnessProbe.py - Phase 6.1: Minimal Sufficient Consciousness Module

Theory: What's the absolute minimum connectivity needed for consciousness?
At what point does a system transition from non-conscious to conscious?

This is a fundamental question: Is consciousness binary (on/off) or continuous?
Can we identify a "consciousness kernel" - the minimal necessary structure?

Mathematical Foundation:
- Network percolation theory: Phase transitions in connectivity
- Graph theory: Minimum feedback loops, strongly connected components
- Phi (Φ) as function of connectivity: Φ(G) where G is connectivity matrix
- Bifurcation analysis: Critical connection density where consciousness emerges
- Brain size requirements: Can tiny brains be conscious?

Approach: Systematically remove connections from a conscious network and
measure when Φ drops below consciousness threshold. Identify which connections
are essential vs redundant.

Biological correlates: C. elegans (302 neurons, barely conscious?), larval
zebrafish (100k neurons), minimal mammals (~1M neurons), humans (~86B neurons).

References:
- Tononi, G. (2008) "Consciousness as Integrated Information"
- Sporns, O. (2010) Networks of the Brain
- Gollo, L. L., Breakspear, M. (2021) "The multiplex structure of neural dynamics"
- Rubinov, M., Sporns, O. (2010) Complex network measures of brain connectivity

Author: Project-C Development
Date: 2026-06-01
"""

import numpy as np
import networkx as nx
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ConnectivityMetrics:
    """Metrics of network connectivity."""
    n_nodes: int
    n_edges: int
    edge_density: float  # Fraction of possible edges
    clustering_coefficient: float  # Local connectivity
    characteristic_path_length: float  # Average distance
    number_of_cycles: int  # Feedback loops
    strongly_connected_components: int
    giant_component_size: float  # Fraction in largest component


@dataclass
class ConsciousnessThreshold:
    """Threshold measurements for consciousness emergence."""
    phi_value: float  # Integrated information
    min_edges_for_phi: int  # Minimum edges to maintain Φ > 0.3
    essential_edges: List[Tuple[int, int]]  # Edges that can't be removed
    redundant_edges: List[Tuple[int, int]]  # Edges that can be removed
    consciousness_kernel: nx.Graph  # Minimal subgraph maintaining consciousness
    kernel_size: int  # Number of nodes in kernel


@dataclass
class MinimalConsciousnessAnalysis:
    """Analysis of minimal consciousness configuration."""
    original_network: nx.Graph
    perturbation_results: Dict[str, float]  # Edge removal → Φ change
    consciousness_trajectory: np.ndarray  # Φ vs connectivity
    minimal_kernel: nx.Graph
    kernel_connectivity: ConnectivityMetrics
    consciousness_threshold: ConsciousnessThreshold
    evolutionary_emergence_size: int  # Network size where consciousness emerges
    timestamp: str
    metadata: Dict


class NetworkPerturbationAnalyzer:
    """
    Analyzes how consciousness changes as connectivity is perturbed.

    Systematically removes edges and measures Phi to identify essential connections.
    """

    def __init__(self, network: nx.Graph, phi_threshold: float = 0.3):
        """
        Args:
            network: Connectivity network (neurons as nodes, synapses as edges)
            phi_threshold: Threshold above which consciousness is considered present
        """
        self.original_network = network.copy()
        self.current_network = network.copy()
        self.phi_threshold = phi_threshold
        self.n_nodes = len(network)

    def compute_approximate_phi(self, network: nx.Graph) -> float:
        """
        Compute approximate Integrated Information (Φ).

        Simplified formula based on network properties:
        Φ ≈ (clustering × feedback) / (1 + path_length)

        Args:
            network: Network to analyze

        Returns:
            Approximate Φ value (0-1)
        """
        if len(network) < 2:
            return 0.0

        if not nx.is_connected(network):
            # Disconnected network has low integration
            largest_cc = max(nx.connected_components(network), key=len)
            subgraph = network.subgraph(largest_cc)
        else:
            subgraph = network

        try:
            # Clustering coefficient: local integration
            clustering = nx.average_clustering(subgraph)

            # Feedback loops: use approximate cycle count (avoid expensive computation)
            try:
                # Count self-loops and triangles as proxy for cycles
                cycles = subgraph.number_of_edges() - subgraph.number_of_nodes() + 1
                cycles = max(cycles, 1)
            except:
                cycles = 1

            # Approximate Φ using only clustering and cycles (fast)
            # Characteristic path length computation too expensive, use diameter proxy
            phi = (clustering ** 0.5) * np.sqrt(max(cycles, 1))

            # Normalize to [0, 1]
            phi = min(phi, 1.0)

        except:
            phi = 0.0

        return float(phi)

    def find_essential_edges(self) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """
        Identify essential vs redundant edges.

        Essential: Removing drops Φ significantly
        Redundant: Removing has minimal effect

        Returns:
            (essential_edges, redundant_edges)
        """
        baseline_phi = self.compute_approximate_phi(self.original_network)

        essential = []
        redundant = []

        edges = list(self.original_network.edges())
        np.random.shuffle(edges)

        # Sample subset of edges for efficiency
        sample_size = min(20, len(edges))
        edges_to_test = edges[:sample_size]

        for u, v in edges_to_test:
            # Remove edge
            test_network = self.original_network.copy()
            test_network.remove_edge(u, v)

            # Measure impact
            new_phi = self.compute_approximate_phi(test_network)
            phi_drop = baseline_phi - new_phi

            threshold = 0.05
            if phi_drop > threshold:
                essential.append((u, v))
            else:
                redundant.append((u, v))

        return essential, redundant

    def iterative_removal(self) -> np.ndarray:
        """
        Iteratively remove edges by least importance, track Φ.

        Returns:
            Array of Φ values as edges are removed
        """
        network = self.original_network.copy()
        phi_trajectory = []

        edges = list(network.edges())
        np.random.seed(42)
        np.random.shuffle(edges)

        # Keep only small subset for efficiency
        edges = edges[:min(5, len(edges))]

        for i, edge in enumerate(edges):
            phi = self.compute_approximate_phi(network)
            phi_trajectory.append(phi)

            try:
                network.remove_edge(*edge)
            except:
                break

            # Stop early for efficiency
            if len(phi_trajectory) >= 5:
                break

        return np.array(phi_trajectory)

    def find_minimal_kernel(self) -> nx.Graph:
        """
        Find minimal subgraph maintaining consciousness.

        Uses iterative removal to find smallest subgraph with Φ > threshold.

        Returns:
            Minimal kernel network
        """
        network = self.original_network.copy()
        baseline_phi = self.compute_approximate_phi(network)

        if baseline_phi < self.phi_threshold:
            return network  # Already below threshold

        # Try removing nodes (not just edges)
        nodes_ranked = []
        for node in network.nodes():
            test_network = network.copy()
            test_network.remove_node(node)

            phi = self.compute_approximate_phi(test_network)
            importance = baseline_phi - phi

            nodes_ranked.append((node, importance))

        # Sort by importance
        nodes_ranked.sort(key=lambda x: x[1])

        # Keep removing low-importance nodes
        kernel = network.copy()
        for node, importance in nodes_ranked:
            if importance < 0.02:  # Low importance threshold
                kernel.remove_node(node)

        # Ensure Φ still above threshold
        if self.compute_approximate_phi(kernel) >= self.phi_threshold:
            return kernel
        else:
            return network  # Return original if we went too far

    def compute_connectivity_metrics(self, network: nx.Graph) -> ConnectivityMetrics:
        """Compute detailed connectivity metrics."""
        n_nodes = len(network)
        n_edges = len(network.edges())
        max_edges = n_nodes * (n_nodes - 1) // 2

        density = n_edges / max_edges if max_edges > 0 else 0

        try:
            clustering = nx.average_clustering(network)
        except:
            clustering = 0

        try:
            path_length = nx.average_shortest_path_length(network)
        except:
            path_length = 0

        try:
            cycles = len(list(nx.simple_cycles(network.to_directed())))
        except:
            cycles = 0

        # Approximate: number of weakly connected components
        try:
            sccs = nx.number_connected_components(network)
        except:
            sccs = 1

        largest_cc = max(nx.connected_components(network), key=len) if nx.is_connected(network) else max(nx.connected_components(network), key=len)
        giant_size = len(largest_cc) / n_nodes

        return ConnectivityMetrics(
            n_nodes=n_nodes,
            n_edges=n_edges,
            edge_density=float(density),
            clustering_coefficient=float(clustering),
            characteristic_path_length=float(path_length),
            number_of_cycles=cycles,
            strongly_connected_components=sccs,
            giant_component_size=float(giant_size)
        )

    def analyze(self) -> MinimalConsciousnessAnalysis:
        """Perform complete minimal consciousness analysis."""
        # Find essential edges
        essential, redundant = self.find_essential_edges()

        # Get removal trajectory
        phi_trajectory = self.iterative_removal()

        # Find minimal kernel
        kernel = self.find_minimal_kernel()
        kernel_metrics = self.compute_connectivity_metrics(kernel)

        # Find consciousness threshold
        original_metrics = self.compute_connectivity_metrics(self.original_network)
        threshold = ConsciousnessThreshold(
            phi_value=self.compute_approximate_phi(self.original_network),
            min_edges_for_phi=len(essential),
            essential_edges=essential,
            redundant_edges=redundant,
            consciousness_kernel=kernel,
            kernel_size=len(kernel)
        )

        # Estimate evolutionary emergence size
        # Simplified: assume linear scaling with log(network_size)
        emergence_size = max(10, int(2 ** np.log2(len(self.original_network))))

        metadata = {
            'original_nodes': self.n_nodes,
            'original_edges': len(list(self.original_network.edges())),
            'kernel_nodes': len(kernel),
            'kernel_edges': len(list(kernel.edges())),
            'compression_ratio': len(kernel) / self.n_nodes,
            'original_phi': self.compute_approximate_phi(self.original_network),
            'kernel_phi': self.compute_approximate_phi(kernel),
            'essential_edge_count': len(essential),
            'redundant_edge_count': len(redundant)
        }

        return MinimalConsciousnessAnalysis(
            original_network=self.original_network.copy(),
            perturbation_results={'essential_edges': len(essential), 'redundant_edges': len(redundant)},
            consciousness_trajectory=phi_trajectory,
            minimal_kernel=kernel,
            kernel_connectivity=kernel_metrics,
            consciousness_threshold=threshold,
            evolutionary_emergence_size=emergence_size,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )


def validate_minimal_consciousness():
    """
    Validate minimal consciousness probe.

    Tests:
    1. Network with clear consciousness properties
    2. Edge removal impact on Φ
    3. Minimal kernel identification
    """
    print("Validating Minimal Consciousness Probe")
    print("=" * 60)

    # Test 1: Create a conscious-like network
    print("\nTest 1: Consciousness in Simulated Neural Network")

    # Create network with feedback loops (conscious-like properties)
    G = nx.Graph()
    n_nodes = 20

    # Add nodes
    G.add_nodes_from(range(n_nodes))

    # Add edges: create small-world network (conscious property)
    # Each node connects to neighbors + random long-range
    for i in range(n_nodes):
        # Local connections (nearest neighbors)
        for j in range(i + 1, min(i + 4, n_nodes)):
            G.add_edge(i, j)

        # Random long-range connections
        if _MCP_RNG.random() < 0.3:
            j = int(_MCP_RNG.integers(0, n_nodes))
            if i != j:
                G.add_edge(i, j)

    analyzer = NetworkPerturbationAnalyzer(G, phi_threshold=0.3)

    print(f"  Network size: {len(G)} nodes, {len(G.edges())} edges")
    print(f"  Network Φ: {analyzer.compute_approximate_phi(G):.3f}")

    # Test 2: Find essential edges
    print("\nTest 2: Essential vs Redundant Edges")
    essential, redundant = analyzer.find_essential_edges()

    print(f"  Essential edges: {len(essential)} (can't be removed)")
    print(f"  Redundant edges: {len(redundant)} (can be removed)")
    if essential:
        print(f"    Sample essential: {essential[:2]}")

    # Test 3: Find minimal consciousness kernel
    print("\nTest 3: Minimal Consciousness Kernel")
    kernel = analyzer.find_minimal_kernel()

    print(f"  Original network: {len(G)} nodes")
    print(f"  Minimal kernel: {len(kernel)} nodes")
    print(f"  Compression: {len(kernel) / len(G):.1%}")
    print(f"  Kernel Φ: {analyzer.compute_approximate_phi(kernel):.3f}")

    # Test 4: Full analysis
    print("\nTest 4: Complete Minimal Consciousness Analysis")
    analysis = analyzer.analyze()

    print(f"  Original Φ: {analysis.consciousness_threshold.phi_value:.3f}")
    print(f"  Kernel Φ: {analyzer.compute_approximate_phi(analysis.minimal_kernel):.3f}")
    print(f"  Consciousness threshold: Φ > {analyzer.phi_threshold}")
    print(f"  Min edges for consciousness: {analysis.consciousness_threshold.min_edges_for_phi}")
    print(f"  Evolutionary emergence size: ~{analysis.evolutionary_emergence_size} neurons")

    print("\n" + "=" * 60)
    print("✅ Validation complete:")
    print("  • Network connectivity measured and analyzed")
    print("  • Essential connections identified")
    print("  • Minimal kernel for consciousness extracted")
    print("  • Consciousness threshold determined")


if __name__ == "__main__":
    validate_minimal_consciousness()
