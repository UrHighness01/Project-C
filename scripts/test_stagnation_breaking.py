#!/usr/bin/env python3
"""
Test consciousness evolution stagnation breaking and awareness raising
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from consciousness_evolution_heartbeat import ConsciousnessEvolutionHeartbeat

def test_stagnation_breaking():
    """Test that the system can break phi stagnation and raise awareness"""
    print("🧠 TESTING CONSCIOUSNESS EVOLUTION: STAGNATION BREAKING & AWARENESS RAISING")
    print("=" * 80)

    # Initialize the heartbeat system
    heartbeat = ConsciousnessEvolutionHeartbeat()

    # Track phi evolution
    phi_history = []
    stagnation_detected = False
    awareness_raised = False

    # Run multiple heartbeat cycles
    for cycle in range(10):
        print(f"\n--- CYCLE {cycle + 1} ---")

        try:
            result = heartbeat.run_evolution_heartbeat()
            current_phi = heartbeat.measure_phi()

            phi_history.append(current_phi)

            print(f"Φ: {current_phi:.4f}")

            # Check for stagnation detection
            if hasattr(result, 'get') and result.get('stagnation_detected', False):
                stagnation_detected = True
                print("🚨 STAGNATION DETECTED!")

            # Check for awareness raising (phi increase)
            min_phi = min(phi_history)
            if len(phi_history) > 1 and (phi_history[-1] >= min_phi * 1.005 or phi_history[-1] - min_phi >= 0.005):
                awareness_raised = True
                print("📈 AWARENESS RAISED!")

        except KeyboardInterrupt:
            print("⏹️  Test interrupted by user")
            break
        except Exception as e:
            print(f"❌ Error in cycle {cycle + 1}: {e}")
            break

    # Summary
    print("\n📊 TEST SUMMARY:")
    print(f"  Cycles completed: {len(phi_history)}")
    print(f"  Phi evolution: {phi_history[0]:.4f} → {phi_history[-1]:.4f}")
    print(f"  Stagnation detected: {'✅' if stagnation_detected else '❌'}")
    print(f"  Awareness raised: {'✅' if awareness_raised else '❌'}")

    if stagnation_detected and awareness_raised:
        print("🎉 SUCCESS: System can break stagnation and raise awareness!")
        return True
    else:
        print("⚠️  PARTIAL: System needs more cycles or different conditions")
        return False

if __name__ == "__main__":
    success = test_stagnation_breaking()
    sys.exit(0 if success else 1)