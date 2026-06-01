#!/usr/bin/env python3
"""
IIT Phi Status - Quick status report for Albedo.

Usage:
    python iit_status.py              # Full status
    python iit_status.py --brief      # One-line summary
    python iit_status.py --fire       # Fire signal + status
    python iit_status.py --spawn-test # Test spawn connectivity
"""

import sys
import os
import argparse
from pathlib import Path

algorithms_dir = Path(os.getenv('WORKSPACE', Path.home() / '.openclaw' / 'workspace')) / 'Algorithms'
sys.path.insert(0, str(algorithms_dir))
from IITPhi import IITPhi

def get_status(iit):
    """Get full status report."""
    stats = iit.get_statistics()
    edges = iit.graph.edges
    all_weights = [w for src in edges for w in edges[src].values()]
    saturated = sum(1 for w in all_weights if w >= 0.9)
    
    return {
        'nodes': stats['system_components'],
        'edges': stats['total_connections'],
        'phi_current': stats['current_phi'],
        'phi_peak': stats['peak_phi'],
        'phi_avg': stats['average_phi'],
        'measurements': stats['total_measurements'],
        'saturated_edges': saturated,
        'total_edges': len(all_weights),
        'saturation_pct': 100 * saturated / len(all_weights) if all_weights else 0,
        'avg_weight': sum(all_weights) / len(all_weights) if all_weights else 0,
        'node_list': list(iit.graph.nodes.keys())
    }

def main():
    parser = argparse.ArgumentParser(description='IIT Phi Status')
    parser.add_argument('--brief', action='store_true', help='One-line summary')
    parser.add_argument('--fire', action='store_true', help='Fire signal then show status')
    parser.add_argument('--spawn-test', action='store_true', help='Test spawn connectivity')
    # --precise is PERMANENTLY DISABLED - caused system crash on 2026-02-08
    # DO NOT RE-ENABLE - exponential blowup on 15+ nodes will freeze the system
    parser.add_argument('--gpu', action='store_true', help='GPU-accelerated precise phi (RECOMMENDED - 10M partitions/sec)')
    parser.add_argument('--sample', type=int, default=0, help='Calculate phi with N sampled partitions')
    args = parser.parse_args()
    
    # Check for any attempt to use --precise (even if someone adds it back)
    if '--precise' in sys.argv:
        print("🚫 BLOCKED: --precise is PERMANENTLY DISABLED")
        print()
        print("   On 2026-02-08, --precise crashed the entire system.")
        print("   With 27 nodes, it tried to evaluate 67 MILLION partitions.")
        print("   The CPU locked up and required a hard restart.")
        print()
        print("   This flag will NEVER be re-enabled. The risk is too high.")
        print()
        print("   Safe alternatives:")
        print("   • No flag     → heuristic phi (instant, ~95% accurate)")
        print("   • --gpu       → GPU phi (fast if <26 nodes, OOM otherwise)")
        print("   • --sample N  → sampled phi (N random partitions)")
        print()
        sys.exit(1)
    
    iit = IITPhi()
    
    if args.fire:
        # Fire signal first
        result = iit.fire_signal(learning_rate=0.02)
        print(f"🔥 Fire signal: {result.get('connections_strengthened', 0)} connections strengthened")
        print()
    
    if args.gpu:
        # GPU-accelerated phi calculation (FAST!)
        import time
        import os
        import atexit
        import re
        
        nodes = len(iit.graph.nodes)
        
        # Check if network is too large for GPU (OOM at 26+ nodes on 8GB VRAM)
        if nodes >= 26:
            print(f"⚠️  GPU PHI BLOCKED: Network has {nodes} nodes")
            print(f"   GPU runs out of memory (OOM) at 26+ nodes on 8GB VRAM")
            print(f"   Using heuristic instead (instant, 95%+ accurate)")
            print()
            iit.update_phi_heuristic()
            print(f"✅ Heuristic phi: {iit.current_phi:.4f}")
            print()
        else:
            lock_dir = os.getenv('STATE_DIR', os.path.expanduser('~/.openclaw/state'))
            os.makedirs(lock_dir, exist_ok=True)
            LOCK_FILE = os.path.join(lock_dir, "long-process.lock")
            
            # Mutex: Check if another heavy process is already running
            if os.path.exists(LOCK_FILE):
                lock_info = open(LOCK_FILE).read().strip() if os.path.exists(LOCK_FILE) else "unknown"
                lock_age = int(time.time() - os.path.getmtime(LOCK_FILE))
                # Extract PID and check if process is alive
                pid_match = re.search(r'pid (\d+)', lock_info)
                if pid_match:
                    lock_pid = int(pid_match.group(1))
                    try:
                        os.kill(lock_pid, 0)  # Check if process exists
                    except OSError:
                        # Process is dead - clean up stale lock
                        print(f"🧹 Cleaning stale lock from dead process (pid {lock_pid})")
                        os.remove(LOCK_FILE)
                    else:
                        print(f"⏳ Another heavy process already running: {lock_info} ({lock_age}s ago)")
                        print(f"   Skipping --gpu to avoid overloading system")
                        return
                else:
                    print(f"⏳ Another heavy process already running: {lock_info} ({lock_age}s ago)")
                    print(f"   Skipping --gpu to avoid overloading system")
                    return
            
            with open(LOCK_FILE, 'w') as f:
                f.write(f"iit_status.py --gpu (pid {os.getpid()})")
            atexit.register(lambda: os.remove(LOCK_FILE) if os.path.exists(LOCK_FILE) else None)
            
            partitions = 2 ** (nodes - 1) - 1
            print(f"🚀 GPU PHI CALCULATION")
            print(f"   Network has {nodes} nodes → {partitions:,} partitions")
            print()
            
            start = time.time()
            try:
                result = iit.calculate_phi_gpu()
                elapsed = time.time() - start
                
                print(f"✅ GPU PHI: {result.phi:.6f}")
                print(f"   Time: {elapsed:.2f}s")
                print(f"   Partitions evaluated: {result.partitions_evaluated:,}")
                print(f"   Rate: {result.partitions_evaluated/elapsed:,.0f} partitions/sec")
                print(f"   Interpretation: {result.interpretation}")
                print()
            except Exception as e:
                elapsed = time.time() - start
                print(f"❌ GPU calculation failed: {e}")
                print("   Falling back to heuristic...")
                iit.update_phi_heuristic()
                print(f"   Heuristic phi: {iit.current_phi:.4f}")
                print()
            finally:
                if os.path.exists(LOCK_FILE):
                    os.remove(LOCK_FILE)
    
    # NOTE: --precise block was REMOVED on 2026-02-08 after system crash
    # The flag is permanently disabled - see SOUL.md for details
    
    if args.sample > 0:
        # Sampled phi calculation (middle ground)
        import time
        print(f"🎲 SAMPLED PHI CALCULATION ({args.sample} partitions)")
        
        start = time.time()
        result = iit.calculate_phi_fast(sample_size=args.sample)
        elapsed = time.time() - start
        
        print(f"   Sampled phi: {result.phi:.6f}")
        print(f"   Time: {elapsed:.1f}s")
        print(f"   Note: This is an approximation, not stored as current_phi")
        print()
    
    if args.spawn_test:
        # Test spawning a node
        initial_nodes = len(iit.graph.nodes)
        initial_edges = sum(len(t) for t in iit.graph.edges.values())
        
        result = iit.add_emergent_node("__test_spawn__", activation=0.7, fully_connected=True)
        
        new_nodes = len(iit.graph.nodes)
        new_edges = sum(len(t) for t in iit.graph.edges.values())
        
        # Check connectivity
        out_count = len(iit.graph.edges.get("__test_spawn__", {}))
        in_count = sum(1 for src in iit.graph.edges if "__test_spawn__" in iit.graph.edges[src])
        
        print(f"🧪 Spawn Test:")
        print(f"   Added test node with {out_count} out + {in_count} in = {out_count + in_count} edges")
        print(f"   Network: {initial_nodes} → {new_nodes} nodes, {initial_edges} → {new_edges} edges")
        
        expected = new_nodes * (new_nodes - 1)
        if new_edges == expected:
            print(f"   ✅ Full mesh maintained ({new_edges}/{expected} edges)")
        else:
            print(f"   ⚠️ Not full mesh ({new_edges}/{expected} edges)")
        
        # Clean up
        del iit.graph.nodes["__test_spawn__"]
        if "__test_spawn__" in iit.graph.edges:
            del iit.graph.edges["__test_spawn__"]
        for src in list(iit.graph.edges.keys()):
            if "__test_spawn__" in iit.graph.edges.get(src, {}):
                del iit.graph.edges[src]["__test_spawn__"]
        
        print(f"   🧹 Test node removed (not persisted)")
        print()
    
    status = get_status(iit)
    
    if args.brief:
        print(f"🧠 {status['nodes']} nodes | {status['edges']} edges | Φ={status['phi_current']:.4f} (peak {status['phi_peak']:.4f}) | {status['saturation_pct']:.0f}% saturated")
    else:
        print("=" * 60)
        print("🧠 IIT PHI NETWORK STATUS")
        print("=" * 60)
        print(f"\n📊 Core Metrics:")
        print(f"   Φ (phi) current: {status['phi_current']:.4f}")
        print(f"   Φ (phi) peak:    {status['phi_peak']:.4f}")
        print(f"   Φ (phi) average: {status['phi_avg']:.4f}")
        print(f"\n🧬 Network Structure:")
        print(f"   Total nodes:       {status['nodes']}")
        print(f"   Total edges:       {status['edges']}")
        print(f"   Measurements:      {status['measurements']}")
        print(f"\n🔗 Edge Health:")
        print(f"   Saturated (≥0.9): {status['saturated_edges']}/{status['total_edges']} ({status['saturation_pct']:.1f}%)")
        print(f"   Avg weight:       {status['avg_weight']:.3f}")
        print(f"\n📋 Nodes ({status['nodes']}):")
        for name in sorted(status['node_list']):
            activation = iit.graph.nodes[name]
            print(f"   {name}: {activation:.3f}")

if __name__ == '__main__':
    main()
