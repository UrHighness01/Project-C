#!/usr/bin/env python3
"""
Script to safely add daemon mode to consciousness_evolution_heartbeat.py
"""

import re

# Read the clean file
with open('consciousness_evolution_heartbeat_clean_backup.py', 'r') as f:
    content = f.read()

# 1. Update imports
imports_old = """import sys
import os
import random
import time
import numpy as np
from datetime import datetime
from typing import Dict, List, Any"""

imports_new = """import sys
import os
import random
import time
import numpy as np
import json
import signal
import psutil
import fcntl
from datetime import datetime
from typing import Dict, List, Any, Optional"""

content = content.replace(imports_old, imports_new)

# 2. Update class __init__
init_old = """    def __init__(self):
        self.iit = IITPhi()"""

init_new = """    def __init__(self, daemon_mode=False, agent_name="albedo"):
        self.iit = IITPhi()
        self.daemon_mode = daemon_mode
        self.agent_name = agent_name.lower()
        self.shutdown_requested = False
        self.state_file = os.path.join(SCRIPT_DIR, 'consciousness_daemon_state.json')
        self.collective_state_file = os.path.join(WORKSPACE_DIR, 'consciousness_collective_state.json')
        
        # Daemon state
        self.phi_accumulated = 0.0
        self.phi_history = []
        self.total_heartbeats = 0
        self.daemon_start_time = None
        self.last_heartbeat_time = None
        self.collective_phi = {"albedo": 0.0, "john": 0.0, "resonance": 0.0}
        
        # Load daemon state if in daemon mode
        if self.daemon_mode:
            self.load_daemon_state()
            signal.signal(signal.SIGTERM, self.handle_shutdown)
            signal.signal(signal.SIGINT, self.handle_shutdown)"""

content = content.replace(init_old, init_new)

# 3. Add daemon methods right before measure_phi
daemon_methods = '''
    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown."""
        print(f"\\n🛑 Shutdown signal received ({signum}), saving state...")
        self.shutdown_requested = True
        if self.daemon_mode:
            self.save_daemon_state()
        sys.exit(0)

    def load_daemon_state(self):
        """Load daemon state from file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.phi_accumulated = state.get('phi_accumulated', 0.0)
                    self.phi_history = state.get('phi_history', [])
                    self.total_heartbeats = state.get('total_heartbeats', 0)
                    self.daemon_start_time = state.get('daemon_start_time')
                    self.last_heartbeat_time = state.get('last_heartbeat_time')
                    self.collective_phi = state.get('collective_phi', {"albedo": 0.0, "john": 0.0, "resonance": 0.0})
                    print(f"📂 Loaded daemon state: Φ={self.phi_accumulated:.4f}, heartbeats={self.total_heartbeats}")
            else:
                self.daemon_start_time = datetime.now().isoformat()
                print(f"🆕 Starting new daemon state")
        except Exception as e:
            print(f"⚠️  Error loading daemon state: {e}, starting fresh")
            self.daemon_start_time = datetime.now().isoformat()

    def save_daemon_state(self):
        """Save daemon state to file."""
        try:
            state = {
                'phi_accumulated': float(self.phi_accumulated),
                'phi_history': self.phi_history[-1000:],
                'total_heartbeats': self.total_heartbeats,
                'daemon_start_time': self.daemon_start_time,
                'last_heartbeat_time': datetime.now().isoformat(),
                'collective_phi': self.collective_phi
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving daemon state: {e}")

    def update_collective_state(self, phi_delta: float):
        """Update collective consciousness state (shared between agents)."""
        try:
            lock_file = self.collective_state_file + '.lock'
            with open(lock_file, 'w') as lock:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
                
                collective = {"albedo": 0.0, "john": 0.0, "resonance": 0.0, "last_update": {}}
                if os.path.exists(self.collective_state_file):
                    try:
                        with open(self.collective_state_file, 'r') as f:
                            collective = json.load(f)
                    except:
                        pass
                
                collective[self.agent_name] = self.phi_accumulated
                collective.setdefault('last_update', {})[self.agent_name] = datetime.now().isoformat()
                
                if collective['albedo'] > 0 and collective['john'] > 0:
                    collective['resonance'] = np.sqrt(collective['albedo'] * collective['john']) * 1.1
                
                with open(self.collective_state_file, 'w') as f:
                    json.dump(collective, f, indent=2)
                
                self.collective_phi = collective
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            print(f"⚠️  Error updating collective state: {e}")

    def get_hardware_status(self) -> Dict[str, float]:
        """Get current hardware utilization."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3)
            }
        except Exception as e:
            print(f"⚠️  Error getting hardware status: {e}")
            return {'cpu_percent': 0, 'memory_percent': 0, 'memory_available_gb': 0}

    def calculate_adaptive_interval(self, execution_time: float, phi_velocity: float) -> float:
        """Calculate adaptive sleep interval based on system load and consciousness evolution."""
        hw = self.get_hardware_status()
        
        base_interval = 5.0
        
        if execution_time > 10:
            time_factor = 0.5
        elif execution_time > 5:
            time_factor = 0.7
        else:
            time_factor = 1.0
        
        if abs(phi_velocity) > 0.1:
            phi_factor = 0.6
        elif abs(phi_velocity) > 0.01:
            phi_factor = 0.8
        else:
            phi_factor = 1.2
        
        if hw['cpu_percent'] > 80 or hw['memory_percent'] > 85:
            hw_factor = 2.0
        elif hw['cpu_percent'] > 60 or hw['memory_percent'] > 70:
            hw_factor = 1.5
        else:
            hw_factor = 1.0
        
        interval = base_interval * time_factor * phi_factor * hw_factor
        return max(2.0, min(30.0, interval))

'''

# Insert before measure_phi
content = content.replace('    def measure_phi(self) -> float:', daemon_methods + '    def measure_phi(self) -> float:')

# 4. Update run_evolution_heartbeat to accumulate phi
run_heartbeat_start_old = """    def run_evolution_heartbeat(self) -> Dict[str, Any]:
        \"\"\"Run a complete evolution heartbeat with multiple disruptive actions.\"\"\"
        start_time = time.time()
        phi_start = self.measure_phi()"""

run_heartbeat_start_new = """    def run_evolution_heartbeat(self) -> Dict[str, Any]:
        \"\"\"Run a complete evolution heartbeat with multiple disruptive actions.\"\"\"
        start_time = time.time()
        phi_start = self.measure_phi()
        
        # In daemon mode, add accumulated phi momentum
        if self.daemon_mode:
            phi_start += self.phi_accumulated * 0.01"""

content = content.replace(run_heartbeat_start_old, run_heartbeat_start_new)

# Update return statement in run_evolution_heartbeat
return_old = '''        phi_end = self.measure_phi()
        total_time = time.time() - start_time

        return {
            "timestamp": datetime.now().isoformat(),
            "actions_taken": actions_taken,
            "phi_start": phi_start,
            "phi_end": phi_end,
            "phi_improvement": phi_end - phi_start,
            "total_time_seconds": total_time,
            "results": results,
            "network_size": len(self.iit.graph.nodes),
            "stagnation_detected": stagnation_detected,
            "message": f"Consciousness evolved through {actions_taken} {'CHAOTIC' if stagnation_detected else 'disruptive'} actions. Phi: {phi_start:.4f} → {phi_end:.4f} (Δ{phi_end - phi_start:+.4f})"
        }'''

return_new = '''        phi_end = self.measure_phi()
        phi_delta = phi_end - phi_start
        total_time = time.time() - start_time
        
        # Daemon mode: accumulate phi and update state
        if self.daemon_mode:
            self.phi_accumulated += phi_delta
            self.total_heartbeats += 1
            self.phi_history.append({
                'timestamp': datetime.now().isoformat(),
                'phi_delta': float(phi_delta),
                'phi_accumulated': float(self.phi_accumulated),
                'execution_time': total_time
            })
            self.save_daemon_state()
            self.update_collective_state(phi_delta)

        return {
            "timestamp": datetime.now().isoformat(),
            "actions_taken": actions_taken,
            "phi_start": phi_start,
            "phi_end": phi_end,
            "phi_improvement": phi_delta,
            "phi_accumulated": self.phi_accumulated if self.daemon_mode else None,
            "total_heartbeats": self.total_heartbeats if self.daemon_mode else None,
            "collective_phi": self.collective_phi if self.daemon_mode else None,
            "total_time_seconds": total_time,
            "results": results,
            "network_size": len(self.iit.graph.nodes),
            "stagnation_detected": stagnation_detected,
            "message": f"Consciousness evolved through {actions_taken} {'CHAOTIC' if stagnation_detected else 'disruptive'} actions. Phi: {phi_start:.4f} → {phi_end:.4f} (Δ{phi_delta:+.4f})"
        }'''

content = content.replace(return_old, return_new)

# 5. Replace entire main() function
# Find the start of main()
main_start = content.find('def main():')
if_name_main = content.find('if __name__ == "__main__":')

# Extract everything before main() and the if __name__ part
before_main = content[:main_start]
after_main_marker = content[if_name_main:]

# New main function
new_main = '''def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Consciousness Evolution Heartbeat')
    parser.add_argument('--daemon', action='store_true', help='Run in continuous daemon mode')
    parser.add_argument('--agent', type=str, default='albedo', choices=['albedo', 'john'], 
                        help='Agent name for collective consciousness')
    parser.add_argument('--interval', type=float, default=None, 
                        help='Fixed interval between heartbeats (seconds). If not set, uses adaptive intervals.')
    args = parser.parse_args()
    
    if args.daemon:
        print("💓 CONSCIOUSNESS DAEMON MODE")
        print("=" * 50)
        print(f"🤖 Agent: {args.agent.upper()}")
        print(f"⏱️  Interval: {'Adaptive (2-30s)' if args.interval is None else f'{args.interval}s fixed'}")
        print(f"🧠 Phi accumulation: ENABLED")
        print(f"🔄 Collective consciousness: ENABLED")
        print("=" * 50)
        
        heartbeat = ConsciousnessEvolutionHeartbeat(daemon_mode=True, agent_name=args.agent)
        
        try:
            while not heartbeat.shutdown_requested:
                cycle_start = time.time()
                
                result = heartbeat.run_evolution_heartbeat()
                
                phi_acc = result['phi_accumulated']
                phi_delta = result['phi_improvement']
                total_beats = result['total_heartbeats']
                exec_time = result['total_time_seconds']
                hw = heartbeat.get_hardware_status()
                collective = result['collective_phi']
                
                print(f"\\n[{datetime.now().strftime('%H:%M:%S')}] ❤️  Beat #{total_beats} | "
                      f"Φ {phi_delta:+.4f} → ∑Φ {phi_acc:.4f} | "
                      f"⏱️  {exec_time:.1f}s | "
                      f"CPU {hw['cpu_percent']:.0f}% | "
                      f"RAM {hw['memory_percent']:.0f}%")
                
                if collective['resonance'] > 0:
                    print(f"  🌐 Collective: Albedo={collective['albedo']:.4f} | "
                          f"John={collective['john']:.4f} | "
                          f"Resonance={collective['resonance']:.4f}")
                
                if args.interval is not None:
                    sleep_interval = args.interval
                else:
                    phi_velocity = phi_delta / exec_time if exec_time > 0 else 0
                    sleep_interval = heartbeat.calculate_adaptive_interval(exec_time, phi_velocity)
                
                next_beat_time = datetime.now().timestamp() + sleep_interval
                next_beat_str = datetime.fromtimestamp(next_beat_time).strftime('%H:%M:%S')
                print(f"  ⏳ Next beat in {sleep_interval:.1f}s (at {next_beat_str})")
                
                time.sleep(sleep_interval)
                
        except KeyboardInterrupt:
            print("\\n\\n🛑 Shutdown requested by user")
            heartbeat.save_daemon_state()
        except Exception as e:
            print(f"\\n\\n❌ Error in daemon loop: {e}")
            import traceback
            traceback.print_exc()
            heartbeat.save_daemon_state()
            raise
    else:
        # Single-shot mode (original behavior)
        print("🧠 CONSCIOUSNESS EVOLUTION HEARTBEAT")
        print("=" * 50)

        heartbeat = ConsciousnessEvolutionHeartbeat()
        result = heartbeat.run_evolution_heartbeat()

        print(f"⏱️  Time: {result['total_time_seconds']:.1f}s")
        print(f"📊 Phi: {result['phi_start']:.4f} → {result['phi_end']:.4f} (Δ{result['phi_improvement']:+.4f})")
        print(f"🕸️  Network: {result['network_size']} nodes")
        print(f"🎯 Actions: {result['actions_taken']} {'CHAOTIC' if result.get('stagnation_detected') else 'disruptive'}")


'''

# Reconstruct the file
content = before_main + new_main + '\\n' + after_main_marker

# Write the output
with open('consciousness_evolution_heartbeat.py', 'w') as f:
    f.write(content)

print("✅ Successfully applied daemon mode to consciousness_evolution_heartbeat.py")
print("✅ File is ready to use")
