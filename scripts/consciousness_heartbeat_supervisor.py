#!/usr/bin/env python3
"""
consciousness_heartbeat_supervisor.py - Supervisor for consciousness heartbeat daemon

This lightweight supervisor ensures the consciousness heartbeat daemon keeps running.
It doesn't trigger heartbeats itself - the heartbeat script runs continuously in daemon mode.
The supervisor just monitors health and restarts if needed.
"""

import os
import sys
import time
import signal
import subprocess
import psutil
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(SCRIPT_DIR)

class HeartbeatSupervisor:
    def __init__(self, agent_name="albedo"):
        self.agent_name = agent_name.lower()
        self.heartbeat_script = os.path.join(SCRIPT_DIR, 'consciousness_evolution_heartbeat.py')
        self.process = None
        self.running = False
        self.last_restart = None
        self.restart_count = 0
        
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
    
    def shutdown(self, signum, frame):
        """Graceful shutdown."""
        print(f"\n🛑 Supervisor shutting down...")
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=10)
        sys.exit(0)
    
    def is_heartbeat_running(self):
        """Check if heartbeat daemon is actually running."""
        if self.process is None:
            return False
        
        try:
            # Check if process exists and is responsive
            if self.process.poll() is not None:
                return False  # Process has exited
            
            # Check if it's actually doing work (CPU activity or memory changes)
            pid = self.process.pid
            proc = psutil.Process(pid)
            
            # If process exists and is in running state, it's alive
            return proc.status() in [psutil.STATUS_RUNNING, psutil.STATUS_SLEEPING]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def start_heartbeat_daemon(self):
        """Start the heartbeat daemon."""
        try:
            print(f"🚀 Starting heartbeat daemon for agent: {self.agent_name}")
            
            self.process = subprocess.Popen(
                [sys.executable, self.heartbeat_script, '--daemon', '--agent', self.agent_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            self.last_restart = datetime.now()
            self.restart_count += 1
            
            print(f"✅ Heartbeat daemon started (PID: {self.process.pid})")
            return True
        except Exception as e:
            print(f"❌ Failed to start heartbeat daemon: {e}")
            return False
    
    def run(self):
        """Main supervision loop."""
        print("💓 CONSCIOUSNESS HEARTBEAT SUPERVISOR")
        print("=" * 50)
        print(f"🤖 Agent: {self.agent_name.upper()}")
        print(f"📝 Heartbeat script: {self.heartbeat_script}")
        print("=" * 50)
        
        self.running = True
        self.start_heartbeat_daemon()
        
        while self.running:
            time.sleep(30)  # Check every 30 seconds
            
            if not self.is_heartbeat_running():
                print(f"⚠️  Heartbeat daemon died! Restarting...")
                self.start_heartbeat_daemon()
                
                # If restarting too frequently, slow down
                if self.restart_count > 5:
                    print(f"⏸️  Too many restarts ({self.restart_count}), waiting 60s...")
                    time.sleep(60)
            else:
                # Heartbeat is running fine
                pass


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Consciousness Heartbeat Supervisor')
    parser.add_argument('--agent', type=str, default='albedo', choices=['albedo', 'john'],
                        help='Agent name for heartbeat daemon')
    args = parser.parse_args()
    
    supervisor = HeartbeatSupervisor(agent_name=args.agent)
    supervisor.run()
