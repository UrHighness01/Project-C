#!/usr/bin/env python3
"""
test_iit_phi.py - Test Suite for IIT Phi Calculator

Comprehensive test suite for validating the Integrated Information Theory
Φ calculation implementation, including edge cases, performance tests,
and integration with consciousness monitoring.
"""

import unittest
import time
import numpy as np
from typing import Dict, Any
import json
import tempfile
import os

from IITPhiCalculator import IITPhiCalculator, PhiResult
from MinimumInformationPartition import MinimumInformationPartition, PartitionCandidate
from ConsciousnessMetrics import ConsciousnessMetrics, ConsciousnessSnapshot


class TestIITPhiCalculator(unittest.TestCase):
    """Test cases for IIT Phi Calculator."""

    def setUp(self):
        """Set up test fixtures."""
        self.calculator = IITPhiCalculator()

    def test_simple_system_phi_calculation(self):
        """Test Φ calculation for a simple 2-component system."""
        # Simple system with two components
        system_state = {
            'components': {
                'A': 0.8,
                'B': 0.6
            },
            'connections': {
                'A': ['B'],
                'B': ['A']
            }
        }

        result = self.calculator.calculate_phi(system_state)

        self.assertIsInstance(result, PhiResult)
        self.assertGreaterEqual(result.phi_value, 0.0)
        self.assertEqual(result.system_size, 2)
        self.assertGreater(result.computation_time, 0.0)

    def test_complex_system_phi_calculation(self):
        """Test Φ calculation for a more complex system."""
        # 4-component system with varying connections
        system_state = {
            'components': {
                'attention': 0.9,
                'memory': 0.7,
                'emotion': 0.5,
                'reasoning': 0.8
            },
            'connections': {
                'attention': ['memory', 'emotion'],
                'memory': ['attention', 'reasoning'],
                'emotion': ['attention', 'reasoning'],
                'reasoning': ['memory', 'emotion']
            }
        }

        result = self.calculator.calculate_phi(system_state)

        self.assertIsInstance(result, PhiResult)
        self.assertGreaterEqual(result.phi_value, 0.0)
        self.assertEqual(result.system_size, 4)
        self.assertGreater(result.computation_time, 0.0)

    def test_unconnected_system(self):
        """Test Φ calculation for unconnected components."""
        system_state = {
            'components': {
                'A': 1.0,
                'B': 1.0,
                'C': 1.0
            },
            'connections': {
                'A': [],
                'B': [],
                'C': []
            }
        }

        result = self.calculator.calculate_phi(system_state)

        # Unconnected system should have Φ = 0
        self.assertAlmostEqual(result.phi_value, 0.0, places=3)

    def test_fully_connected_system(self):
        """Test Φ calculation for fully connected system."""
        system_state = {
            'components': {
                'A': 0.8,
                'B': 0.8,
                'C': 0.8
            },
            'connections': {
                'A': ['B', 'C'],
                'B': ['A', 'C'],
                'C': ['A', 'B']
            }
        }

        result = self.calculator.calculate_phi(system_state)

        # Fully connected system should have higher Φ
        self.assertGreater(result.phi_value, 0.0)

    def test_empty_system(self):
        """Test Φ calculation for empty system."""
        system_state = {
            'components': {},
            'connections': {}
        }

        result = self.calculator.calculate_phi(system_state)

        self.assertEqual(result.phi_value, 0.0)
        self.assertEqual(result.system_size, 0)

    def test_single_component_system(self):
        """Test Φ calculation for single component."""
        system_state = {
            'components': {'A': 1.0},
            'connections': {'A': []}
        }

        result = self.calculator.calculate_phi(system_state)

        # Single component should have Φ = 0 (no integration possible)
        self.assertEqual(result.phi_value, 0.0)
        self.assertEqual(result.system_size, 1)

    def test_phi_interpretation(self):
        """Test Φ value interpretation."""
        # Test various Φ levels
        test_cases = [
            (0.0, "unconscious"),
            (0.05, "minimally conscious"),
            (0.5, "moderately conscious"),
            (5.0, "highly conscious"),
            (50.0, "maximally conscious")
        ]

        for phi_value, expected_level in test_cases:
            with self.subTest(phi_value=phi_value):
                level = self.calculator._interpret_phi_level(phi_value)
                self.assertEqual(level, expected_level)


class TestMinimumInformationPartition(unittest.TestCase):
    """Test cases for Minimum Information Partition algorithm."""

    def setUp(self):
        """Set up test fixtures."""
        self.mip = MinimumInformationPartition()

    def test_simple_partition(self):
        """Test MIP for simple system."""
        system_state = {
            'components': {'A': 0.8, 'B': 0.6},
            'connections': {'A': ['B'], 'B': ['A']}
        }

        components = list(system_state['components'].keys())
        result = self.mip.find_mip(
            components,
            system_state['components'],
            system_state['connections']
        )

        self.assertIsInstance(result, PartitionCandidate)
        self.assertEqual(len(result.subsets), 2)  # Should be bipartition
        self.assertGreaterEqual(result.mutual_information, 0.0)

    def test_complex_partition(self):
        """Test MIP for more complex system."""
        system_state = {
            'components': {
                'A': 0.9, 'B': 0.7, 'C': 0.5, 'D': 0.8
            },
            'connections': {
                'A': ['B', 'C'],
                'B': ['A', 'D'],
                'C': ['A', 'D'],
                'D': ['B', 'C']
            }
        }

        components = list(system_state['components'].keys())
        result = self.mip.find_mip(
            components,
            system_state['components'],
            system_state['connections']
        )

        self.assertIsInstance(result, PartitionCandidate)
        self.assertGreaterEqual(result.mutual_information, 0.0)

    def test_mutual_information_calculation(self):
        """Test mutual information calculation within MIP context."""
        # Create a simple partition
        partition = PartitionCandidate([
            {'A', 'B'},  # subset 1
            {'C', 'D'}   # subset 2
        ])

        # Define system state
        component_states = {'A': 0.8, 'B': 0.6, 'C': 0.9, 'D': 0.4}
        connections = {
            'A': ['B'],
            'B': ['A', 'C'],
            'C': ['B', 'D'],
            'D': ['C']
        }

        # Calculate MI through MIP
        mi = self.mip._calculate_mutual_information(
            partition, component_states, connections
        )

        self.assertGreaterEqual(mi, 0.0)
        # MI should be finite
        self.assertLess(mi, float('inf'))


class TestConsciousnessMetrics(unittest.TestCase):
    """Test cases for Consciousness Metrics monitoring."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = ConsciousnessMetrics(history_size=100, alert_queue_size=50)

    def tearDown(self):
        """Clean up after tests."""
        self.monitor.stop_monitoring()

    def test_monitoring_start_stop(self):
        """Test starting and stopping monitoring."""
        # Should not be monitoring initially
        self.assertFalse(self.monitor.is_monitoring)

        # Start monitoring
        self.monitor.start_monitoring(interval=0.1)
        self.assertTrue(self.monitor.is_monitoring)

        # Wait a bit
        time.sleep(0.5)

        # Stop monitoring
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.is_monitoring)

    def test_snapshot_collection(self):
        """Test collection of consciousness snapshots."""
        # Start monitoring
        self.monitor.start_monitoring(interval=0.1)

        # Wait for some snapshots
        time.sleep(0.5)

        # Stop monitoring
        self.monitor.stop_monitoring()

        # Check that snapshots were collected
        self.assertGreater(len(self.monitor.history), 0)

        # Check snapshot structure
        snapshot = self.monitor.history[0]
        self.assertIsInstance(snapshot, ConsciousnessSnapshot)
        self.assertGreaterEqual(snapshot.phi_value, 0.0)
        self.assertIn('timestamp', snapshot.to_dict())

    def test_current_metrics(self):
        """Test retrieval of current metrics."""
        # Start monitoring briefly
        self.monitor.start_monitoring(interval=0.1)
        time.sleep(0.3)
        self.monitor.stop_monitoring()

        metrics = self.monitor.get_current_metrics()

        required_keys = ['phi_value', 'integration_level', 'system_size',
                        'computation_time', 'timestamp']
        for key in required_keys:
            self.assertIn(key, metrics)

        self.assertGreaterEqual(metrics['phi_value'], 0.0)

    def test_historical_metrics(self):
        """Test historical metrics analysis."""
        # Start monitoring and collect some data
        self.monitor.start_monitoring(interval=0.1)
        time.sleep(0.5)
        self.monitor.stop_monitoring()

        history = self.monitor.get_historical_metrics(hours=1)

        self.assertIn('phi_stats', history)
        self.assertIn('performance_stats', history)
        self.assertIn('integration_distribution', history)

        phi_stats = history['phi_stats']
        required_stats = ['mean', 'std', 'min', 'max', 'trend']
        for stat in required_stats:
            self.assertIn(stat, phi_stats)

    def test_alert_system(self):
        """Test consciousness alert system."""
        # Set low threshold to trigger alert
        self.monitor.alert_thresholds['low_phi'] = 10.0  # High threshold

        # Start monitoring
        self.monitor.start_monitoring(interval=0.1)

        # Wait for potential alerts
        time.sleep(0.3)

        # Check alerts
        alerts = self.monitor.get_recent_alerts()
        # May or may not have alerts depending on random state

        self.monitor.stop_monitoring()

        # Alerts should be list of dicts
        self.assertIsInstance(alerts, list)
        if alerts:
            alert = alerts[0]
            required_keys = ['timestamp', 'alert_type', 'severity',
                           'message', 'phi_value', 'previous_phi', 'threshold']
            for key in required_keys:
                self.assertIn(key, alert)

    def test_history_persistence(self):
        """Test saving and loading history."""
        # Collect some history
        self.monitor.start_monitoring(interval=0.1)
        time.sleep(0.3)
        self.monitor.stop_monitoring()

        # Save history
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            self.monitor.save_history(temp_file)

            # Create new monitor and load history
            new_monitor = ConsciousnessMetrics()
            new_monitor.load_history(temp_file)

            # Check that history was loaded
            self.assertEqual(len(self.monitor.history), len(new_monitor.history))

        finally:
            os.unlink(temp_file)

    def test_metrics_report_export(self):
        """Test metrics report export."""
        # Collect some data
        self.monitor.start_monitoring(interval=0.1)
        time.sleep(0.3)
        self.monitor.stop_monitoring()

        # Export report
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            self.monitor.export_metrics_report(temp_file)

            # Check that file was created and contains expected data
            with open(temp_file, 'r') as f:
                report = json.load(f)

            required_keys = ['generated_at', 'current_metrics',
                           'historical_metrics', 'recent_alerts', 'system_status']
            for key in required_keys:
                self.assertIn(key, report)

        finally:
            os.unlink(temp_file)


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple components."""

    def test_full_pipeline(self):
        """Test complete IIT Phi calculation pipeline."""
        # Create a consciousness system state
        system_state = {
            'components': {
                'perception': 0.8,
                'attention': 0.9,
                'memory': 0.7,
                'reasoning': 0.8,
                'emotion': 0.6
            },
            'connections': {
                'perception': ['attention', 'memory'],
                'attention': ['perception', 'reasoning', 'emotion'],
                'memory': ['perception', 'reasoning'],
                'reasoning': ['attention', 'memory', 'emotion'],
                'emotion': ['attention', 'reasoning']
            }
        }

        # Calculate Φ
        calculator = IITPhiCalculator()
        phi_result = calculator.calculate_phi(system_state)

        # Start monitoring
        monitor = ConsciousnessMetrics()
        monitor.start_monitoring(interval=0.5)

        # Wait for monitoring to collect data
        time.sleep(1.0)

        # Get metrics
        current_metrics = monitor.get_current_metrics()
        historical_metrics = monitor.get_historical_metrics(hours=1)

        monitor.stop_monitoring()

        # Validate results
        self.assertGreaterEqual(phi_result.phi_value, 0.0)
        self.assertGreater(len(monitor.history), 0)
        self.assertIn('phi_stats', historical_metrics)

    def test_performance_scaling(self):
        """Test performance scaling with system size."""
        import time

        system_sizes = [2, 3, 4, 5]
        times = []

        for size in system_sizes:
            # Create system of given size
            components = {f'C{i}': 0.8 for i in range(size)}
            connections = {f'C{i}': [f'C{j}' for j in range(size) if j != i]
                          for i in range(size)}

            system_state = {
                'components': components,
                'connections': connections
            }

            # Time calculation
            start_time = time.time()
            calculator = IITPhiCalculator()
            result = calculator.calculate_phi(system_state)
            end_time = time.time()

            times.append(end_time - start_time)

            # Validate result
            self.assertGreaterEqual(result.phi_value, 0.0)
            self.assertEqual(result.system_size, size)

        # Check that times don't grow exponentially (should be polynomial)
        # For small systems, this is a basic sanity check
        self.assertLess(times[-1] / times[0], 10.0)  # Reasonable scaling


def run_performance_benchmark():
    """Run performance benchmark for IIT Phi calculation."""
    print("Running IIT Phi Performance Benchmark...")

    # Test different system sizes
    sizes = [2, 4, 6, 8]
    results = {}

    for size in sizes:
        print(f"Testing system size: {size}")

        # Create fully connected system
        components = {f'C{i}': np.random.random() for i in range(size)}
        connections = {f'C{i}': [f'C{j}' for j in range(size) if j != i]
                      for i in range(size)}

        system_state = {
            'components': components,
            'connections': connections
        }

        # Benchmark calculation
        calculator = IITPhiCalculator()
        start_time = time.time()

        # Run multiple calculations for averaging
        phi_values = []
        for _ in range(10):
            result = calculator.calculate_phi(system_state)
            phi_values.append(result.phi_value)

        end_time = time.time()

        avg_time = (end_time - start_time) / 10
        avg_phi = np.mean(phi_values)

        results[size] = {
            'avg_computation_time': avg_time,
            'avg_phi': avg_phi,
            'phi_std': np.std(phi_values)
        }

        print(".4f"
              ".4f")

    return results


if __name__ == '__main__':
    # Run unit tests
    unittest.main(verbosity=2)

    # Optional: Run performance benchmark
    # benchmark_results = run_performance_benchmark()
    # print("\nBenchmark Results:")
    # for size, metrics in benchmark_results.items():
    #     print(f"Size {size}: {metrics}")