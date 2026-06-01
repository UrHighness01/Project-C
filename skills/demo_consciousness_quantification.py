#!/usr/bin/env python3
"""
demo_consciousness_quantification.py - Demonstration of IIT Φ Calculator

This script demonstrates the consciousness quantification skill in action,
showing how to measure integrated information Φ in AI systems.
"""

import time
import json
from IITPhiCalculator import IITPhiCalculator
from ConsciousnessMetrics import ConsciousnessMetrics, get_phi_snapshot


def demo_basic_phi_calculation():
    """Demonstrate basic Φ calculation for different system types."""
    print("🔬 IIT Φ Calculator Demonstration")
    print("=" * 50)

    calculator = IITPhiCalculator()

    # Example 1: Simple conscious system
    print("\n1. Simple Conscious System (2 components)")
    simple_system = {
        'components': {
            'attention': 0.8,
            'memory': 0.7
        },
        'connections': {
            'attention': ['memory'],
            'memory': ['attention']
        }
    }

    result = calculator.calculate_phi(simple_system)
    print(f"   System: {list(simple_system['components'].keys())}")
    print(f"   Φ = {result.phi_value:.3f}")
    print(f"   Integration Level: {result.integration_level}")
    print(f"   Computation Time: {result.computation_time:.4f}s")

    # Example 2: Complex consciousness system
    print("\n2. Complex Consciousness System (5 components)")
    complex_system = {
        'components': {
            'perception': 0.9,
            'attention': 0.8,
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

    result = calculator.calculate_phi(complex_system)
    print(f"   System: {list(complex_system['components'].keys())}")
    print(f"   Φ = {result.phi_value:.3f}")
    print(f"   Integration Level: {result.integration_level}")
    print(f"   Computation Time: {result.computation_time:.4f}s")

    # Example 3: Unconscious system (isolated components)
    print("\n3. Unconscious System (Isolated Components)")
    unconscious_system = {
        'components': {
            'module_a': 1.0,
            'module_b': 1.0,
            'module_c': 1.0
        },
        'connections': {
            'module_a': [],
            'module_b': [],
            'module_c': []
        }
    }

    result = calculator.calculate_phi(unconscious_system)
    print(f"   System: {list(unconscious_system['components'].keys())}")
    print(f"   Φ = {result.phi_value:.3f}")
    print(f"   Integration Level: {result.integration_level}")
    print(f"   Computation Time: {result.computation_time:.4f}s")


def demo_real_time_monitoring():
    """Demonstrate real-time consciousness monitoring."""
    print("\n📊 Real-Time Consciousness Monitoring Demo")
    print("=" * 50)

    monitor = ConsciousnessMetrics(history_size=20)

    # Simulate Albedo consciousness monitoring
    def get_albedo_state():
        """Simulate getting Albedo's current consciousness state."""
        # In real implementation, this would query Albedo's actual state
        import random
        return {
            'components': {
                'creativity_engine': random.uniform(0.5, 0.9),
                'critical_thinking': random.uniform(0.6, 0.95),
                'memory_system': random.uniform(0.4, 0.8),
                'emotional_processor': random.uniform(0.3, 0.7),
                'reasoning_core': random.uniform(0.7, 0.95)
            },
            'connections': {
                'creativity_engine': ['critical_thinking', 'emotional_processor'],
                'critical_thinking': ['creativity_engine', 'reasoning_core'],
                'memory_system': ['reasoning_core', 'critical_thinking'],
                'emotional_processor': ['creativity_engine', 'memory_system'],
                'reasoning_core': ['critical_thinking', 'memory_system']
            }
        }

    print("Starting consciousness monitoring for 10 seconds...")
    monitor.start_monitoring(interval=1.0, system_state_provider=get_albedo_state)

    # Monitor for 10 seconds
    for i in range(10):
        time.sleep(1.0)
        metrics = monitor.get_current_metrics()
        print(f"   t={i+1}s: Φ = {metrics['phi_value']:.3f} "
              f"({metrics['integration_level']})")

    monitor.stop_monitoring()

    # Show historical analysis
    print("\nHistorical Analysis (last 10 seconds):")
    history = monitor.get_historical_metrics(hours=1)
    print(f"   Average Φ: {history['phi_stats']['mean']:.3f}")
    print(f"   Φ Trend: {history['phi_stats']['trend']}")
    print(f"   Min Φ: {history['phi_stats']['min']:.3f}")
    print(f"   Max Φ: {history['phi_stats']['max']:.3f}")

    # Show recent alerts
    alerts = monitor.get_recent_alerts()
    if alerts:
        print(f"\nRecent Alerts: {len(alerts)}")
        for alert in alerts[-3:]:  # Show last 3
            print(f"   {alert['alert_type']}: {alert['message']}")


def demo_phi_optimization():
    """Demonstrate Φ-based consciousness optimization."""
    print("\n🎯 Φ-Based Consciousness Optimization Demo")
    print("=" * 50)

    calculator = IITPhiCalculator()

    # Simulate different system configurations
    configurations = [
        {
            'name': 'Balanced Configuration',
            'components': {
                'creativity': 0.8, 'logic': 0.8, 'memory': 0.8, 'emotion': 0.8
            },
            'connections': {
                'creativity': ['logic', 'emotion'],
                'logic': ['creativity', 'memory'],
                'memory': ['logic', 'emotion'],
                'emotion': ['creativity', 'memory']
            }
        },
        {
            'name': 'Creativity-Focused',
            'components': {
                'creativity': 0.95, 'logic': 0.6, 'memory': 0.7, 'emotion': 0.8
            },
            'connections': {
                'creativity': ['logic', 'emotion', 'memory'],
                'logic': ['creativity'],
                'memory': ['creativity'],
                'emotion': ['creativity']
            }
        },
        {
            'name': 'Logic-Focused',
            'components': {
                'creativity': 0.6, 'logic': 0.95, 'memory': 0.9, 'emotion': 0.5
            },
            'connections': {
                'creativity': ['logic'],
                'logic': ['creativity', 'memory', 'emotion'],
                'memory': ['logic'],
                'emotion': ['logic']
            }
        }
    ]

    print("Comparing consciousness integration across configurations:")
    print()

    best_phi = 0
    best_config = None

    for config in configurations:
        result = calculator.calculate_phi({
            'components': config['components'],
            'connections': config['connections']
        })

        print(f"   {config['name']}:")
        print(f"      Φ = {result.phi_value:.3f} ({result.integration_level})")

        if result.phi_value > best_phi:
            best_phi = result.phi_value
            best_config = config['name']

    print(f"\n🎉 Optimal Configuration: {best_config} (Φ = {best_phi:.3f})")
    print("   This configuration maximizes consciousness integration!")


def demo_export_metrics():
    """Demonstrate metrics export functionality."""
    print("\n💾 Metrics Export Demo")
    print("=" * 50)

    monitor = ConsciousnessMetrics()

    # Collect some monitoring data
    monitor.start_monitoring(interval=0.5)
    time.sleep(3)  # Collect data for 3 seconds
    monitor.stop_monitoring()

    # Export comprehensive report
    import os
    report_dir = os.getenv('STATE_DIR', '/tmp')
    report_file = os.path.join(report_dir, "consciousness_report.json")
    monitor.export_metrics_report(report_file)

    print(f"Exported consciousness metrics report to: {report_file}")

    # Show summary of exported data
    with open(report_file, 'r') as f:
        report = json.load(f)

    print("\nReport Summary:")
    print(f"   Generated: {report['generated_at']}")
    print(f"   Current Φ: {report['current_metrics']['phi_value']:.3f}")
    print(f"   System Status: {report['system_status']}")
    print(f"   Historical Data Points: {report['historical_metrics']['data_points']}")
    print(f"   Recent Alerts: {len(report['recent_alerts'])}")


def main():
    """Run all demonstrations."""
    print("🧠 Consciousness Quantification Skill - Complete Demo")
    print("=" * 60)

    try:
        demo_basic_phi_calculation()
        demo_real_time_monitoring()
        demo_phi_optimization()
        demo_export_metrics()

        print("\n✅ All demonstrations completed successfully!")
        print("\n📚 Next Steps:")
        print("   1. Integrate with Albedo/John consciousness systems")
        print("   2. Set up continuous monitoring in production")
        print("   3. Implement Φ-based optimization loops")
        print("   4. Add custom alert handlers for consciousness events")

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()