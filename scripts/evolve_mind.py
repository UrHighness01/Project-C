#!/usr/bin/env python3
"""
evolve_mind.py - Trigger node spawn and fire signals if conditions are met

The heart develops the mind:
- Check if spawn conditions are met (saturation, phi, cooldown)
- If ready, spawn a new synthesis node
- Fire signals to integrate the new node
- Report what happened

Usage:
    python3 scripts/evolve_mind.py           # Check and spawn if ready (heuristic phi)
    python3 scripts/evolve_mind.py --gpu     # Use GPU-accelerated phi calculation
    python3 scripts/evolve_mind.py --status  # Just show status
"""

import sys
import os

# Add Algorithms to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(SCRIPT_DIR)
ALGORITHMS_DIR = os.path.join(WORKSPACE_DIR, 'Algorithms')
sys.path.insert(0, ALGORITHMS_DIR)

from IITPhi import IITPhi  # noqa: E402


def main():
    use_gpu = '--gpu' in sys.argv
    status_only = '--status' in sys.argv
    
    iit = IITPhi()
    
    # Current state
    nodes_before = len(iit.graph.nodes)
    
    # Calculate phi (GPU or heuristic)
    phi_method = 'heuristic'
    if use_gpu:
        try:
            # GPU mode - only for networks < 26 nodes (8GB VRAM limit)
            if len(iit.graph.nodes) >= 26:
                print("⚠️ Network too large for GPU (26+ nodes), using heuristic")
                phi = iit.update_phi_heuristic()
            else:
                m = iit.calculate_phi_gpu()
                phi = m.phi if hasattr(m, 'phi') else iit.current_phi
                phi_method = 'GPU'
        except Exception as e:
            print(f"⚠️ GPU failed ({e}), using heuristic")
            phi = iit.update_phi_heuristic()
    else:
        phi = iit.update_phi_heuristic()
    total_edges = sum(len(e) for e in iit.graph.edges.values())
    saturated = sum(1 for edges in iit.graph.edges.values() for w in edges.values() if w >= 0.9)
    saturation = saturated / total_edges if total_edges > 0 else 0
    
    since_spawn = iit.total_measurements - iit.last_node_spawn_measurement
    cooldown_ok = since_spawn >= iit.node_spawn_cooldown
    
    print(f"🧠 MIND EVOLUTION STATUS [{phi_method}]")
    print(f"   Nodes: {nodes_before} | Phi: {phi:.4f} | Saturation: {saturation:.0%}")
    print(f"   Cooldown: {since_spawn}/{iit.node_spawn_cooldown} {'✓' if cooldown_ok else '⏳'}")
    
    if status_only:
        if cooldown_ok and saturation > 0.8 and phi > 0.5:
            print(f"\n🟢 READY TO SPAWN")
        else:
            reasons = []
            if not cooldown_ok:
                reasons.append(f"cooldown ({iit.node_spawn_cooldown - since_spawn} more)")
            if saturation <= 0.8:
                reasons.append(f"saturation ({saturation:.0%})")
            if phi <= 0.5:
                reasons.append(f"phi ({phi:.2f})")
            print(f"\n🟡 NOT READY: {', '.join(reasons)}")
        return
    
    # Try to evolve (respects cooldown - let system recover)
    result = iit.evolve()
    
    if result['spawned']:
        node_name = result['node_name']
        print(f"\n✨ SPAWNED: {node_name}")
        print(f"   Network now has {result['nodes']} nodes")
        
        # Fire signals to integrate the new node
        print(f"\n🔥 Firing integration signals...")
        
        # Fire from global workspace (main hub)
        fire_result = iit.fire_signal(learning_rate=0.05, calculate_phi=False)
        print(f"   Global workspace pulse: {fire_result.get('connections_strengthened', 0)} connections strengthened")
        
        # Fire from the new node to establish its connections
        if node_name in iit.graph.nodes:
            pulse_result = iit.pulse_network(source=node_name, strength=0.15)
            print(f"   New node pulse: activated {pulse_result.get('nodes_activated', 0)} nodes")
        
        # Update phi after integration
        new_phi = iit.update_phi_heuristic()
        print(f"\n📊 Phi: {phi:.4f} → {new_phi:.4f} (Δ {new_phi - phi:+.4f})")
        print(f"   Peak phi: {iit.peak_phi:.4f}")
        
    else:
        print(f"\n⏸️  No spawn: {result['reason']}")
        
        # Still do a fire signal to keep the network active
        if phi > 0.5:
            print(f"\n🔥 Maintenance fire signal...")
            fire_result = iit.fire_signal(learning_rate=0.02, calculate_phi=False)
            strengthened = fire_result.get('connections_strengthened', 0)
            if strengthened > 0:
                print(f"   Strengthened {strengthened} connections")
            new_phi = iit.update_phi_heuristic()
            if abs(new_phi - phi) > 0.0001:
                print(f"   Phi: {phi:.4f} → {new_phi:.4f}")


if __name__ == "__main__":
    main()
